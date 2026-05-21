import uuid
from redis_client import get_client

r = get_client()

# primera funcionalidad = crea sesison + funciones de verificado y cerrado( no se que tan utikes son estas ultimas para lo que hacemos, pero bueno)
def crear_sesion(user_id, ttl=3600):
    token = str(uuid.uuid4())
    r.setex(f"sesion:{user_id}", ttl, token)
    print(f"Sesión creada para {user_id} | Token: {token} | Expira en: {ttl}s")
    return token


def verificar_sesion(user_id):
    token = r.get(f"sesion:{user_id}")
    if token:
        print(f"Sesión activa | Usuario: {user_id} | Token: {token}")
        return True
    print(f"Sin sesión activa para {user_id}")
    return False


def cerrar_sesion(user_id):
    r.delete(f"sesion:{user_id}")
    print(f"Sesión cerrada para {user_id}")

# segunda funcionalidad, ver sesiones activas.
def ver_sesiones_activas():
    claves = r.keys("sesion:*")
    if not claves:
        print("No hay sesiones activas")
        return
    print(f"{len(claves)} sesión(es) activa(s):")
    for clave in claves:
        token = r.get(clave)
        ttl = r.ttl(clave)
        user_id = clave.split(":")[1]
        print(f"  Usuario: {user_id} | Token: {token} | Expira en: {ttl}s")
        
