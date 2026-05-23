from pymongo import MongoClient

from config import DB_NAME, MONGO_URI


_client = None


def obtener_cliente():
    """
    Crea y reutiliza un unico cliente MongoClient para toda la ejecucion.
    """
    global _client

    if _client is None:
        _client = MongoClient(MONGO_URI)

    return _client


def obtener_db():
    """
    Devuelve la base de datos starvy configurada en config.py.
    """
    return obtener_cliente()[DB_NAME]


def obtener_coleccion(nombre):
    """
    Devuelve una coleccion de MongoDB por nombre: usuarios, restaurantes o resenas.
    """
    return obtener_db()[nombre]


def probar_conexion():
    """
    Ejecuta ping contra MongoDB Atlas para validar que la conexion funciona.
    """
    obtener_cliente().admin.command("ping")
    print("Conexion con MongoDB verificada correctamente.")


def cerrar_conexion():
    """
    Cierra el cliente MongoDB al finalizar el script.
    """
    global _client

    if _client is not None:
        _client.close()
        _client = None
