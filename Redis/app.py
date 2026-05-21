from redis_client import get_client

r = get_client()


def crear_sesion(user_id, token, ttl=3600):
    # Guarda el token de sesión con expiración automática (default 1 hora)
    r.setex(f"sesion:{user_id}", ttl, token)
    print(f"Sesión creada para usuario {user_id} (expira en {ttl}s)")


def ver_sesiones_activas():
    # Busca todas las claves que siguen el patrón sesion:*
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


if __name__ == "__main__":
    # Datos hardcodeados para probar
    crear_sesion("user_001", "token_abc123")
    crear_sesion("user_002", "token_xyz789")

    ver_sesiones_activas()
