import redis
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Variable global que guarda el pool una vez creado
_pool = None

def get_client() -> redis.Redis:
    global _pool
    # Solo crea el pool la primera vez (patrón singleton)
    if _pool is None:
        _pool = redis.ConnectionPool(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True  # Las respuestas vienen como str en vez de bytes
        )
    # Devuelve un cliente Redis usando el pool compartido
    return redis.Redis(connection_pool=_pool)
