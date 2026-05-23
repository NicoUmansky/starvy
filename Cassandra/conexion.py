from cassandra.cluster import Cluster
from config import CASSANDRA_HOST, CASSANDRA_PORT, KEYSPACE


def conectar_sin_keyspace():
    """
    Conexión inicial a Cassandra.
    Se usa para crear el keyspace si todavía no existe.
    """
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()
    return cluster, session


def conectar_con_keyspace():
    """
    Conexión a Cassandra usando el keyspace starvy.
    Se usa para crear tablas, cargar datos y ejecutar consultas.
    """
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect(KEYSPACE)
    return cluster, session