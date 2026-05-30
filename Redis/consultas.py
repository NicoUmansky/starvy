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
    Devuelve el top N de restaurantes más visitados.

    Antes reconstruye el ranking desde Cassandra para asegurar que Redis
    tenga datos completos y nombres correctos.
    """
    top_n = int(top_n)

    reconstruir_desde_cassandra()

    resultados = r.zrevrange(
        "ranking:restaurante",
        0,
        top_n - 1,
        withscores=True
    )

    return [
        {
            "puesto": i,
            "nombre": nombre,
            "restaurante": nombre,
            "visitas": int(score),
            "score": int(score)
        }
        for i, (nombre, score) in enumerate(resultados, 1)
    ]
# ─── Funcionalidad 4: Ranking de tipos de comida ─────────────────────────────

def registrar_visita_tipo_comida(tipo_comida):
    """
    Incrementa en 1 el contador del tipo de comida en el Sorted Set.
    """
    r.zincrby("ranking:tipoComida", 1, tipo_comida)
    return tipo_comida


def ver_ranking_tipos_comida(top_n=10):
    """
    Devuelve el top N de tipos de comida más pedidos.
    """
    top_n = int(top_n)

    reconstruir_desde_cassandra()

    resultados = r.zrevrange(
        "ranking:tipoComida",
        0,
        top_n - 1,
        withscores=True
    )

    return [
        {
            "puesto": i,
            "tipo_comida": tipo,
            "nombre": tipo,
            "pedidos": int(score),
            "score": int(score)
        }
        for i, (tipo, score) in enumerate(resultados, 1)
    ]


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
    Reconstruye los rankings de Redis desde Cassandra.

    Cassandra aporta las visitas reales.
    DATASET/restaurantes.json aporta el nombre correcto del restaurante.
    Redis guarda el ranking ya preparado para responder rápido.
    """
    import json
    from pathlib import Path
    from collections import Counter
    from cassandra.cluster import Cluster

    base_dir = Path(__file__).resolve().parent.parent
    restaurantes_path = base_dir / "DATASET" / "restaurantes.json"

    with open(restaurantes_path, "r", encoding="utf-8") as f:
        restaurantes = json.load(f)

    mapa_restaurantes = {
        str(r.get("restaurante_id")): r.get("nombre", f"Restaurante {r.get('restaurante_id')}")
        for r in restaurantes
    }

    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect("starvy")

    filas = session.execute(
        "SELECT restaurante_id, tipo_comida FROM visitas_por_restaurante_dia"
    )

    contador_restaurante = Counter()
    contador_tipo = Counter()

    for fila in filas:
        restaurante_id = str(fila.restaurante_id)
        contador_restaurante[restaurante_id] += 1

        if fila.tipo_comida:
            contador_tipo[fila.tipo_comida] += 1

    session.shutdown()
    cluster.shutdown()

    pipe = r.pipeline()
    pipe.delete("ranking:restaurante")
    pipe.delete("ranking:tipoComida")

    for restaurante_id, cantidad in contador_restaurante.items():
        nombre = mapa_restaurantes.get(restaurante_id, f"Restaurante {restaurante_id}")
        pipe.zincrby("ranking:restaurante", cantidad, nombre)

    for tipo_comida, cantidad in contador_tipo.items():
        pipe.zincrby("ranking:tipoComida", cantidad, tipo_comida)

    pipe.execute()

    return {
        "restaurantes_cargados": len(contador_restaurante),
        "tipos_cargados": len(contador_tipo)
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
