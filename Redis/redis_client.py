import redis

# Pool de conexiones compartido entre todos los módulos.
# Se crea una sola vez (patrón singleton) para reutilizar conexiones TCP
# en lugar de abrir y cerrar una nueva conexión en cada operación.
_pool = None

def get_client() -> redis.Redis:
    """
    Devuelve un cliente Redis conectado a la instancia compartida en Redis Cloud.
    decode_responses=True hace que las respuestas lleguen como str en vez de bytes.
    """
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool(
            host='redis-10212.c14.us-east-1-2.ec2.cloud.redislabs.com',
            port=10212,
            db=0,
            password='cRWgta2gV5bWacRM2zr5AfVUxUtP5LKE',
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            health_check_interval=30,
        )
    return redis.Redis(connection_pool=_pool)
