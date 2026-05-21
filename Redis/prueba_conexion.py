from redis_client import get_client

r = get_client()

if r.ping():
    print("Conexión exitosa a Redis")
else:
    print("Error de conexión")
