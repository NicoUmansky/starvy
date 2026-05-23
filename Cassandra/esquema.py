from conexion import conectar_sin_keyspace, conectar_con_keyspace


def crear_keyspace():
    """
    Crea el keyspace starvy.
    En entorno local con Docker usamos SimpleStrategy y replication_factor 1.
    """
    cluster, session = conectar_sin_keyspace()

    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS starvy
        WITH replication = {
            'class': 'SimpleStrategy',
            'replication_factor': 1
        };
    """)

    print("Keyspace 'starvy' creado o ya existente.")

    session.shutdown()
    cluster.shutdown()


def crear_tablas():
    """
    Crea las tablas de Cassandra según el modelado por consulta.
    No usamos metodo_pago porque no existe en el dataset real.
    """
    cluster, session = conectar_con_keyspace()

    session.execute("""
        CREATE TABLE IF NOT EXISTS promociones_por_restaurante (
            restaurante_id int,
            estado text,
            fecha_fin date,
            promocion_id int,
            titulo text,
            descripcion text,
            descuento int,
            fecha_inicio date,
            barrio text,
            PRIMARY KEY ((restaurante_id), estado, fecha_fin, promocion_id)
        ) WITH CLUSTERING ORDER BY (estado ASC, fecha_fin ASC, promocion_id ASC);
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS promociones_activas_por_fecha (
            dia_vigencia date,
            barrio text,
            restaurante_id int,
            promocion_id int,
            titulo text,
            descuento int,
            fecha_inicio date,
            fecha_fin date,
            estado text,
            PRIMARY KEY ((dia_vigencia, barrio), restaurante_id, promocion_id)
        ) WITH CLUSTERING ORDER BY (restaurante_id ASC, promocion_id ASC);
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS visitas_por_restaurante_dia (
            restaurante_id int,
            fecha date,
            hora time,
            visita_id int,
            dni_usuario int,
            plato_id int,
            plato_nombre text,
            tipo_comida text,
            barrio text,
            monto decimal,
            PRIMARY KEY ((restaurante_id, fecha), hora, visita_id)
        ) WITH CLUSTERING ORDER BY (hora DESC, visita_id ASC);
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS visitas_por_usuario_fecha (
            dni_usuario int,
            fecha date,
            hora time,
            visita_id int,
            restaurante_id int,
            plato_id int,
            plato_nombre text,
            tipo_comida text,
            monto decimal,
            PRIMARY KEY ((dni_usuario), fecha, hora, visita_id)
        ) WITH CLUSTERING ORDER BY (fecha DESC, hora DESC, visita_id ASC);
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS metricas_restaurante_por_dia (
            restaurante_id int,
            fecha date,
            cantidad_vendida int,
            plato_id int,
            plato_nombre text,
            tipo_comida text,
            total_ingresos decimal,
            PRIMARY KEY ((restaurante_id, fecha), cantidad_vendida, plato_id)
        ) WITH CLUSTERING ORDER BY (cantidad_vendida DESC, plato_id ASC);
    """)

    print("Tablas creadas o ya existentes.")

    session.shutdown()
    cluster.shutdown()


def verificar_tablas():
    """
    Lista las tablas existentes en el keyspace starvy.
    Sirve como evidencia de conexión entre Python y Cassandra.
    """
    cluster, session = conectar_con_keyspace()

    filas = session.execute("""
        SELECT table_name
        FROM system_schema.tables
        WHERE keyspace_name = 'starvy';
    """)

    print("\nTablas existentes en Cassandra:")
    for fila in filas:
        print("-", fila.table_name)

    session.shutdown()
    cluster.shutdown()