import redis

_pool = None

def get_client() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool(
            host='redis-10212.c14.us-east-1-2.ec2.cloud.redislabs.com',
            port=10212,
            db=0,
            password='cRWgta2gV5bWacRM2zr5AfVUxUtP5LKE',
            decode_responses=True
        )
    return redis.Redis(connection_pool=_pool)
