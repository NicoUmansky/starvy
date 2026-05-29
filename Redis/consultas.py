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
    """
    r.delete(f"sesion:{user_id}")
    print(f"Sesión cerrada para {user_id}")
    return {"usuario": user_id, "sesion_cerrada": True}


# ─── Funcionalidad 2: Consultar sesiones activas ──────────────────────────────

def verificar_sesion(user_id):
    """
    Verifica si el usuario tiene una sesión activa en Redis.
    """
    token = r.get(f"sesion:{user_id}")
    ttl = r.ttl(f"sesion:{user_id}")
    activa = token is not None
    if activa:
        print(f"Sesión activa | Usuario: {user_id} | Token: {token}")
    else:
        print(f"Sin sesión activa para {user_id}")
    return {
        "usuario": user_id,
        "sesion_activa": activa,
        "token": token or "sin sesion",
        "ttl_segundos": ttl
    }


def ver_sesiones_activas():
    """
    Lista todos los usuarios con sesión activa junto con su token y TTL restante.
    """
    claves = r.keys("sesion:*")
    if not claves:
        print("No hay sesiones activas.")
        return []

    filas = []
    print(f"{len(claves)} sesión(es) activa(s):")
    for clave in claves:
        token = r.get(clave)
        ttl = r.ttl(clave)
        user_id = clave.split(":", 1)[1]
        print(f"  Usuario: {user_id} | Token: {token} | Expira en: {ttl}s")
        filas.append({"usuario": user_id, "token": token, "ttl_segundos": ttl, "sesion_activa": True})
    return filas


# ─── Funcionalidad 3: Ranking de restaurantes más visitados ───────────────────

def registrar_visita_restaurante(nombre_restaurante):
    """
    Incrementa en 1 el contador de visitas del restaurante en el Sorted Set.
    """
    r.zincrby("ranking:restaurante", 1, nombre_restaurante)
    return nombre_restaurante


def ver_ranking_restaurantes(top_n=10):
    """
    Muestra el top N de restaurantes ordenados por cantidad de visitas.
    """
    resultados = r.zrevrange("ranking:restaurante", 0, int(top_n) - 1, withscores=True)
    print(f"\nTop {top_n} restaurantes más visitados:")
    filas = []
    if not resultados:
        print("  Sin datos. Ejecutá reconstruir_desde_cassandra() primero.")
        return filas
    for i, (nombre, visitas) in enumerate(resultados, 1):
        print(f"  {i}. {nombre} — {int(visitas)} visitas")
        filas.append({"posicion": i, "restaurante": nombre, "visitas": int(visitas)})
    return filas


# ─── Funcionalidad 4: Ranking de tipos de comida ─────────────────────────────

def registrar_visita_tipo_comida(tipo_comida):
    """
    Incrementa en 1 el contador del tipo de comida en el Sorted Set.
    """
    r.zincrby("ranking:tipoComida", 1, tipo_comida)
    return tipo_comida


def ver_ranking_tipos_comida(top_n=10):
    """
    Muestra el top N de tipos de comida ordenados por popularidad.
    """
    resultados = r.zrevrange("ranking:tipoComida", 0, int(top_n) - 1, withscores=True)
    print(f"\nTop {top_n} tipos de comida más pedidos:")
    filas = []
    if not resultados:
        print("  Sin datos. Ejecutá reconstruir_desde_cassandra() primero.")
        return filas
    for i, (tipo, cantidad) in enumerate(resultados, 1):
        print(f"  {i}. {tipo} — {int(cantidad)} pedidos")
        filas.append({"posicion": i, "tipo_comida": tipo, "pedidos": int(cantidad)})
    return filas


def registrar_visita(nombre_restaurante, tipo_comida):
    """
    Atajo que actualiza ambos rankings en una sola llamada.
    Es la función que debe llamarse cada vez que se registra una visita en Cassandra.
    """
    registrar_visita_restaurante(nombre_restaurante)
    registrar_visita_tipo_comida(tipo_comida)
    return {"restaurante": nombre_restaurante, "tipo_comida": tipo_comida, "rankings_actualizados": True}


def reconstruir_desde_cassandra():
    """
    Reconstruye los rankings desde cero cuando Redis pierde su estado.
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

    r.delete("ranking:restaurante")
    r.delete("ranking:tipoComida")

    for tipo, cantidad in contador_tipo.items():
        r.zincrby("ranking:tipoComida", cantidad, tipo)

    for restaurante_id, visitas in contador_restaurante.items():
        doc = restaurantes.find_one({"restaurante_id": restaurante_id}, {"nombre": 1})
        nombre = doc["nombre"] if doc else f"restaurante_{restaurante_id}"
        r.zincrby("ranking:restaurante", visitas, nombre)

    print("Rankings reconstruidos desde Cassandra y MongoDB.")
    return {
        "restaurantes": ver_ranking_restaurantes(),
        "tipos_comida": ver_ranking_tipos_comida()
    }


# ─── Funcionalidad 5: Últimas búsquedas de un usuario ────────────────────────

def registrar_busqueda(user_id, termino):
    """
    Agrega el término al inicio del historial del usuario y descarta los más viejos.
    """
    r.lpush(f"busqueda:{user_id}", termino)
    r.ltrim(f"busqueda:{user_id}", 0, _MAX_BUSQUEDAS - 1)
    print(f"Búsqueda registrada para {user_id}: '{termino}'")
    return ver_ultimas_busquedas(user_id)


def ver_ultimas_busquedas(user_id):
    """
    Devuelve las últimas búsquedas del usuario en orden cronológico inverso.
    """
    busquedas = r.lrange(f"busqueda:{user_id}", 0, _MAX_BUSQUEDAS - 1)
    print(f"\nÚltimas búsquedas de {user_id}:")
    filas = []
    if not busquedas:
        print("  Sin búsquedas registradas.")
        return filas
    for i, termino in enumerate(busquedas, 1):
        print(f"  {i}. {termino}")
        filas.append({"posicion": i, "termino": termino})
    return filas
