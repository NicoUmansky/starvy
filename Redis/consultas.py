import sys
from collections import Counter
from pathlib import Path

from redis_client import get_client

r = get_client()

_MAX_BUSQUEDAS = 5
_MONGO_DIR = str(Path(__file__).resolve().parent.parent / "mongoDB")


def _restaurantes_collection():
    """
    Agrega el módulo MongoDB al path en tiempo de ejecución y devuelve
    la colección de restaurantes. Se usa solo en reconstruir_desde_cassandra()
    para obtener el nombre del restaurante a partir de su ID.
    """
    if _MONGO_DIR not in sys.path:
        sys.path.insert(0, _MONGO_DIR)
    from mongo_client import restaurantes_collection
    return restaurantes_collection


# ─── Funcionalidad 1: Crear y cerrar sesiones ─────────────────────────────────
#
# Cuando un usuario hace login en MongoDB, se genera un token UUID que se guarda
# en Redis con SETEX. El TTL (por defecto 1 hora) hace que la sesión expire
# automáticamente sin que ningún otro motor tenga que intervenir.
# Redis ES fuente de verdad para sesiones: si se pierde, el usuario vuelve a loguearse.

def crear_sesion(user_id, ttl=3600):
    """
    Crea una sesión activa para el usuario.
    Guarda el token en la key 'sesion:{user_id}' con expiración automática.
    Retorna el token generado.
    """
    import uuid
    token = str(uuid.uuid4())
    r.setex(f"sesion:{user_id}", ttl, token)
    print(f"Sesión creada para {user_id} | Token: {token} | Expira en: {ttl}s")
    return token


def cerrar_sesion(user_id):
    """
    Elimina la sesión del usuario borrando su key en Redis.
    Equivale a un logout explícito antes de que expire el TTL.
    """
    r.delete(f"sesion:{user_id}")
    print(f"Sesión cerrada para {user_id}")


# ─── Funcionalidad 2: Consultar sesiones activas ──────────────────────────────
#
# Permite ver qué usuarios tienen sesión vigente en este momento.
# En producción se usaría SCAN en lugar de KEYS para no bloquear el servidor.

def verificar_sesion(user_id):
    """
    Verifica si el usuario tiene una sesión activa en Redis.
    Retorna True si existe la key, False si expiró o nunca se creó.
    """
    token = r.get(f"sesion:{user_id}")
    if token:
        print(f"Sesión activa | Usuario: {user_id} | Token: {token}")
        return True
    print(f"Sin sesión activa para {user_id}")
    return False


def ver_sesiones_activas():
    """
    Lista todos los usuarios con sesión activa junto con su token y TTL restante.
    """
    claves = r.keys("sesion:*")
    if not claves:
        print("No hay sesiones activas.")
        return
    print(f"{len(claves)} sesión(es) activa(s):")
    for clave in claves:
        token = r.get(clave)
        ttl = r.ttl(clave)
        user_id = clave.split(":")[1]
        print(f"  Usuario: {user_id} | Token: {token} | Expira en: {ttl}s")


# ─── Funcionalidad 3: Ranking de restaurantes más visitados ───────────────────
#
# Usa un Sorted Set donde cada miembro es el nombre del restaurante y el score
# es la cantidad de visitas. ZINCRBY incrementa el score en O(log N).
# La fuente de verdad es Cassandra (visitas_por_restaurante_dia).
# Redis NO es fuente de verdad: si se pierde, se reconstruye con reconstruir_desde_cassandra().

def registrar_visita_restaurante(nombre_restaurante):
    """
    Incrementa en 1 el contador de visitas del restaurante en el Sorted Set.
    Llamar junto con el INSERT de visita en Cassandra.
    """
    r.zincrby("ranking:restaurante", 1, nombre_restaurante)


def ver_ranking_restaurantes(top_n=10):
    """
    Muestra el top N de restaurantes ordenados por cantidad de visitas (mayor a menor).
    ZREVRANGE devuelve los elementos en orden descendente por score.
    """
    resultados = r.zrevrange("ranking:restaurante", 0, top_n - 1, withscores=True)
    print(f"\nTop {top_n} restaurantes más visitados:")
    if not resultados:
        print("  Sin datos. Ejecutá reconstruir_desde_cassandra() primero.")
        return
    for i, (nombre, visitas) in enumerate(resultados, 1):
        print(f"  {i}. {nombre} — {int(visitas)} visitas")


# ─── Funcionalidad 4: Ranking de tipos de comida ─────────────────────────────
#
# Mismo mecanismo que el ranking de restaurantes pero por tipo de cocina.
# La fuente de verdad es Cassandra (metricas_restaurante_por_dia, campo tipo_comida).

def registrar_visita_tipo_comida(tipo_comida):
    """
    Incrementa en 1 el contador del tipo de comida en el Sorted Set.
    Llamar junto con el INSERT de visita en Cassandra.
    """
    r.zincrby("ranking:tipoComida", 1, tipo_comida)


def ver_ranking_tipos_comida(top_n=10):
    """
    Muestra el top N de tipos de comida ordenados por popularidad (mayor a menor).
    """
    resultados = r.zrevrange("ranking:tipoComida", 0, top_n - 1, withscores=True)
    print(f"\nTop {top_n} tipos de comida más pedidos:")
    if not resultados:
        print("  Sin datos. Ejecutá reconstruir_desde_cassandra() primero.")
        return
    for i, (tipo, cantidad) in enumerate(resultados, 1):
        print(f"  {i}. {tipo} — {int(cantidad)} pedidos")


def registrar_visita(nombre_restaurante, tipo_comida):
    """
    Atajo que actualiza ambos rankings en una sola llamada.
    Es la función que debe llamarse cada vez que se registra una visita en Cassandra.
    """
    registrar_visita_restaurante(nombre_restaurante)
    registrar_visita_tipo_comida(tipo_comida)


def reconstruir_desde_cassandra():
    """
    Reconstruye los rankings desde cero cuando Redis pierde su estado.
    Lee todas las visitas de Cassandra, cuenta en Python, y consulta MongoDB
    para obtener el nombre del restaurante a partir del restaurante_id.
    Usa ALLOW FILTERING porque la tabla está particionada por (restaurante_id, fecha)
    y necesitamos recorrer todas las particiones.
    """
    from cassandra.cluster import Cluster

    restaurantes = _restaurantes_collection()

    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect("starvy")

    filas = session.execute(
        "SELECT restaurante_id, tipo_comida FROM visitas_por_restaurante_dia ALLOW FILTERING"
    )

    contador_restaurante = Counter()
    contador_tipo = Counter()

    for fila in filas:
        contador_restaurante[fila.restaurante_id] += 1
        if fila.tipo_comida:
            contador_tipo[fila.tipo_comida] += 1

    session.shutdown()
    cluster.shutdown()

    # Limpiar los sorted sets antes de recargar
    r.delete("ranking:restaurante")
    r.delete("ranking:tipoComida")

    for tipo, cantidad in contador_tipo.items():
        r.zincrby("ranking:tipoComida", cantidad, tipo)

    for restaurante_id, visitas in contador_restaurante.items():
        doc = restaurantes.find_one({"restaurante_id": restaurante_id}, {"nombre": 1})
        nombre = doc["nombre"] if doc else f"restaurante_{restaurante_id}"
        r.zincrby("ranking:restaurante", visitas, nombre)

    print("Rankings reconstruidos desde Cassandra y MongoDB.")
    ver_ranking_restaurantes()
    ver_ranking_tipos_comida()


# ─── Funcionalidad 5: Últimas búsquedas de un usuario ────────────────────────
#
# Usa una List por usuario. LPUSH inserta al principio, por lo que el elemento
# más reciente siempre queda en el índice 0. LTRIM recorta la lista para que
# no crezca más allá de _MAX_BUSQUEDAS entradas.
# Redis ES fuente de verdad: este dato no existe en ningún otro motor.
# Si se pierde, está bien: las búsquedas recientes son efímeras por naturaleza.

def registrar_busqueda(user_id, termino):
    """
    Agrega el término al inicio del historial del usuario y descarta los más viejos
    si superan el límite de _MAX_BUSQUEDAS.
    """
    r.lpush(f"busqueda:{user_id}", termino)
    r.ltrim(f"busqueda:{user_id}", 0, _MAX_BUSQUEDAS - 1)
    print(f"Búsqueda registrada para {user_id}: '{termino}'")


def ver_ultimas_busquedas(user_id):
    """
    Devuelve las últimas búsquedas del usuario en orden cronológico inverso
    (la más reciente primero).
    """
    busquedas = r.lrange(f"busqueda:{user_id}", 0, _MAX_BUSQUEDAS - 1)
    print(f"\nÚltimas búsquedas de {user_id}:")
    if not busquedas:
        print("  Sin búsquedas registradas.")
        return
    for i, termino in enumerate(busquedas, 1):
        print(f"  {i}. {termino}")
