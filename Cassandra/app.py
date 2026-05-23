from cassandra.cluster import Cluster
from cassandra.util import Time
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import json


CASSANDRA_HOST = "127.0.0.1"
CASSANDRA_PORT = 9042
KEYSPACE = "starvy"

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "DATASET"


def conectar_sin_keyspace():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()
    return cluster, session


def conectar_con_keyspace():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect(KEYSPACE)
    return cluster, session


def crear_keyspace():
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
    cluster, session = conectar_con_keyspace()

    # Q1: Ver promociones activas por restaurante
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

    # Q2: Ver promociones activas por fecha y barrio
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

    # Q3: Ver visitas registradas en un día de un restaurante
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

    # Q4: Ver historial de visitas por usuario
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

    # Q5: Ver plato/comida más vendida por restaurante y día
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


def leer_json(nombre_archivo):
    ruta = DATASET_DIR / nombre_archivo

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def convertir_fecha(fecha_texto):
    return datetime.strptime(fecha_texto, "%Y-%m-%d").date()


def convertir_hora(hora_texto):
    """
    El dataset trae horas como HH:MM.
    Cassandra usa tipo time, por eso agregamos los segundos.
    """
    if len(hora_texto.split(":")) == 2:
        hora_texto = hora_texto + ":00"

    return Time(hora_texto)


def rango_fechas(fecha_inicio, fecha_fin):
    """
    Genera todos los días entre fecha_inicio y fecha_fin.
    Esto sirve para la tabla promociones_activas_por_fecha.
    """
    dia_actual = fecha_inicio

    while dia_actual <= fecha_fin:
        yield dia_actual
        dia_actual = dia_actual + timedelta(days=1)


def limpiar_tablas():
    """
    Limpia las tablas antes de volver a cargar el dataset.
    Esto evita mezclar datos de prueba manuales con los datos reales del JSON.
    """
    cluster, session = conectar_con_keyspace()

    tablas = [
        "promociones_por_restaurante",
        "promociones_activas_por_fecha",
        "visitas_por_restaurante_dia",
        "visitas_por_usuario_fecha",
        "metricas_restaurante_por_dia"
    ]

    for tabla in tablas:
        session.execute(f"TRUNCATE {tabla};")

    print("Tablas limpiadas correctamente.")

    session.shutdown()
    cluster.shutdown()


def cargar_promociones():
    """
    Carga promociones.json en dos tablas:
    - promociones_por_restaurante
    - promociones_activas_por_fecha

    En promociones_activas_por_fecha solo guardamos promociones con estado activa.
    """
    promociones = leer_json("promociones.json")

    cluster, session = conectar_con_keyspace()

    insert_por_restaurante = session.prepare("""
        INSERT INTO promociones_por_restaurante (
            restaurante_id, estado, fecha_fin, promocion_id,
            titulo, descripcion, descuento, fecha_inicio, barrio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_por_fecha = session.prepare("""
        INSERT INTO promociones_activas_por_fecha (
            dia_vigencia, barrio, restaurante_id, promocion_id,
            titulo, descuento, fecha_inicio, fecha_fin, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    cantidad_promociones_restaurante = 0
    cantidad_promociones_fecha = 0

    for promo in promociones:
        restaurante_id = int(promo["restaurante_id"])
        estado = promo["estado"].lower()
        fecha_inicio = convertir_fecha(promo["fecha_inicio"])
        fecha_fin = convertir_fecha(promo["fecha_fin"])
        promocion_id = int(promo["promocion_id"])
        titulo = promo["titulo"]
        descripcion = promo["descripcion"]
        descuento = int(promo["descuento"])
        barrio = promo["barrio"]

        session.execute(insert_por_restaurante, (
            restaurante_id,
            estado,
            fecha_fin,
            promocion_id,
            titulo,
            descripcion,
            descuento,
            fecha_inicio,
            barrio
        ))

        cantidad_promociones_restaurante += 1

        if estado == "activa":
            for dia in rango_fechas(fecha_inicio, fecha_fin):
                session.execute(insert_por_fecha, (
                    dia,
                    barrio,
                    restaurante_id,
                    promocion_id,
                    titulo,
                    descuento,
                    fecha_inicio,
                    fecha_fin,
                    estado
                ))

                cantidad_promociones_fecha += 1

    print(f"Promociones cargadas en promociones_por_restaurante: {cantidad_promociones_restaurante}")
    print(f"Registros cargados en promociones_activas_por_fecha: {cantidad_promociones_fecha}")

    session.shutdown()
    cluster.shutdown()


def cargar_visitas_y_metricas():
    """
    Carga visitas.json en:
    - visitas_por_restaurante_dia
    - visitas_por_usuario_fecha

    Además calcula la métrica de platos vendidos por restaurante y día:
    - metricas_restaurante_por_dia

    """
    visitas = leer_json("visitas.json")

    cluster, session = conectar_con_keyspace()

    insert_visita_restaurante = session.prepare("""
        INSERT INTO visitas_por_restaurante_dia (
            restaurante_id, fecha, hora, visita_id, dni_usuario,
            plato_id, plato_nombre, tipo_comida, barrio, monto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_visita_usuario = session.prepare("""
        INSERT INTO visitas_por_usuario_fecha (
            dni_usuario, fecha, hora, visita_id, restaurante_id,
            plato_id, plato_nombre, tipo_comida, monto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_metrica = session.prepare("""
        INSERT INTO metricas_restaurante_por_dia (
            restaurante_id, fecha, cantidad_vendida, plato_id,
            plato_nombre, tipo_comida, total_ingresos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """)

    metricas = defaultdict(lambda: {
        "cantidad_vendida": 0,
        "total_ingresos": Decimal("0"),
        "plato_nombre": "",
        "tipo_comida": ""
    })

    for visita in visitas:
        restaurante_id = int(visita["restaurante_id"])
        fecha = convertir_fecha(visita["fecha"])
        hora = convertir_hora(visita["hora"])
        visita_id = int(visita["visita_id"])
        dni_usuario = int(visita["dni_usuario"])
        plato_id = int(visita["plato_id"])
        plato_nombre = visita["plato_nombre"]
        tipo_comida = visita["tipo_comida"]
        barrio = visita["barrio"]
        monto = Decimal(str(visita["monto"]))

        session.execute(insert_visita_restaurante, (
            restaurante_id,
            fecha,
            hora,
            visita_id,
            dni_usuario,
            plato_id,
            plato_nombre,
            tipo_comida,
            barrio,
            monto
        ))

        session.execute(insert_visita_usuario, (
            dni_usuario,
            fecha,
            hora,
            visita_id,
            restaurante_id,
            plato_id,
            plato_nombre,
            tipo_comida,
            monto
        ))

        clave_metrica = (restaurante_id, fecha, plato_id)

        metricas[clave_metrica]["cantidad_vendida"] += 1
        metricas[clave_metrica]["total_ingresos"] += monto
        metricas[clave_metrica]["plato_nombre"] = plato_nombre
        metricas[clave_metrica]["tipo_comida"] = tipo_comida

    for (restaurante_id, fecha, plato_id), datos in metricas.items():
        session.execute(insert_metrica, (
            restaurante_id,
            fecha,
            datos["cantidad_vendida"],
            plato_id,
            datos["plato_nombre"],
            datos["tipo_comida"],
            datos["total_ingresos"]
        ))

    print(f"Visitas cargadas: {len(visitas)}")
    print(f"Métricas generadas: {len(metricas)}")

    session.shutdown()
    cluster.shutdown()


def cargar_dataset():
    print("\nCargando dataset en Cassandra...")

    cargar_promociones()
    cargar_visitas_y_metricas()

    print("Carga del dataset finalizada correctamente.")

def consultar_promociones_por_restaurante(restaurante_id):
    """
    Q1: Ver promociones activas por restaurante.
    Tabla utilizada: promociones_por_restaurante.
    """
    cluster, session = conectar_con_keyspace()

    filas = session.execute("""
        SELECT restaurante_id, estado, fecha_fin, promocion_id, titulo,
               descripcion, descuento, fecha_inicio, barrio
        FROM promociones_por_restaurante
        WHERE restaurante_id = %s
        AND estado = %s;
    """, (restaurante_id, "activa"))

    print(f"\nQ1 - Promociones activas del restaurante {restaurante_id}:")
    cantidad = 0

    for fila in filas:
        cantidad += 1
        print(
            f"- Promo ID {fila.promocion_id} | {fila.titulo} | "
            f"{fila.descuento}% OFF | Barrio: {fila.barrio} | "
            f"Vigencia: {fila.fecha_inicio} a {fila.fecha_fin}"
        )

    if cantidad == 0:
        print("No se encontraron promociones activas para ese restaurante.")

    session.shutdown()
    cluster.shutdown()


def consultar_promociones_por_fecha_barrio(dia_vigencia, barrio):
    """
    Q2: Ver promociones activas por fecha y barrio.
    Tabla utilizada: promociones_activas_por_fecha.
    """
    cluster, session = conectar_con_keyspace()

    fecha = convertir_fecha(dia_vigencia)

    filas = session.execute("""
        SELECT dia_vigencia, barrio, restaurante_id, promocion_id,
               titulo, descuento, fecha_inicio, fecha_fin, estado
        FROM promociones_activas_por_fecha
        WHERE dia_vigencia = %s
        AND barrio = %s;
    """, (fecha, barrio))

    print(f"\nQ2 - Promociones activas el día {dia_vigencia} en {barrio}:")
    cantidad = 0

    for fila in filas:
        cantidad += 1
        print(
            f"- Restaurante {fila.restaurante_id} | Promo ID {fila.promocion_id} | "
            f"{fila.titulo} | {fila.descuento}% OFF | "
            f"Vigencia: {fila.fecha_inicio} a {fila.fecha_fin}"
        )

    if cantidad == 0:
        print("No se encontraron promociones activas para esa fecha y barrio.")

    session.shutdown()
    cluster.shutdown()


def consultar_visitas_por_restaurante_dia(restaurante_id, fecha_texto):
    """
    Q3: Ver visitas registradas en un día de un restaurante.
    Tabla utilizada: visitas_por_restaurante_dia.
    """
    cluster, session = conectar_con_keyspace()

    fecha = convertir_fecha(fecha_texto)

    filas = session.execute("""
        SELECT restaurante_id, fecha, hora, visita_id, dni_usuario,
               plato_id, plato_nombre, tipo_comida, barrio, monto
        FROM visitas_por_restaurante_dia
        WHERE restaurante_id = %s
        AND fecha = %s;
    """, (restaurante_id, fecha))

    print(f"\nQ3 - Visitas del restaurante {restaurante_id} el día {fecha_texto}:")
    cantidad = 0

    for fila in filas:
        cantidad += 1
        print(
            f"- Visita {fila.visita_id} | Usuario: {fila.dni_usuario} | "
            f"Hora: {fila.hora} | Plato: {fila.plato_nombre} | "
            f"Tipo: {fila.tipo_comida} | Barrio: {fila.barrio} | Monto: ${fila.monto}"
        )

    if cantidad == 0:
        print("No se encontraron visitas para ese restaurante y fecha.")

    session.shutdown()
    cluster.shutdown()


def consultar_historial_visitas_usuario(dni_usuario):
    """
    Q4: Ver historial de visitas por usuario.
    Tabla utilizada: visitas_por_usuario_fecha.
    """
    cluster, session = conectar_con_keyspace()

    filas = session.execute("""
        SELECT dni_usuario, fecha, hora, visita_id, restaurante_id,
               plato_id, plato_nombre, tipo_comida, monto
        FROM visitas_por_usuario_fecha
        WHERE dni_usuario = %s
        LIMIT 10;
    """, (dni_usuario,))

    print(f"\nQ4 - Historial de visitas del usuario {dni_usuario}:")
    cantidad = 0

    for fila in filas:
        cantidad += 1
        print(
            f"- Fecha: {fila.fecha} | Hora: {fila.hora} | "
            f"Restaurante: {fila.restaurante_id} | Plato: {fila.plato_nombre} | "
            f"Tipo: {fila.tipo_comida} | Monto: ${fila.monto}"
        )

    if cantidad == 0:
        print("No se encontraron visitas para ese usuario.")

    session.shutdown()
    cluster.shutdown()


def consultar_plato_mas_vendido(restaurante_id, fecha_texto):
    """
    Q5: Ver plato/comida más vendida por restaurante y día.
    Tabla utilizada: metricas_restaurante_por_dia.
    """
    cluster, session = conectar_con_keyspace()

    fecha = convertir_fecha(fecha_texto)

    filas = session.execute("""
        SELECT restaurante_id, fecha, cantidad_vendida, plato_id,
               plato_nombre, tipo_comida, total_ingresos
        FROM metricas_restaurante_por_dia
        WHERE restaurante_id = %s
        AND fecha = %s
        LIMIT 1;
    """, (restaurante_id, fecha))

    print(f"\nQ5 - Plato más vendido del restaurante {restaurante_id} el día {fecha_texto}:")
    cantidad = 0

    for fila in filas:
        cantidad += 1
        print(
            f"- Plato: {fila.plato_nombre} | Tipo: {fila.tipo_comida} | "
            f"Cantidad vendida: {fila.cantidad_vendida} | "
            f"Total ingresos: ${fila.total_ingresos}"
        )

    if cantidad == 0:
        print("No se encontraron métricas para ese restaurante y fecha.")

    session.shutdown()
    cluster.shutdown()


def ejecutar_consultas():
    """
    Ejecuta las consultas principales del punto 6:
    promociones activas y visitas registradas.
    """

    print("\n==============================")
    print("EJECUCIÓN DE CONSULTAS CASSANDRA")
    print("==============================")

    consultar_promociones_por_restaurante(14)
    consultar_promociones_por_fecha_barrio("2026-05-12", "Almagro")
    consultar_visitas_por_restaurante_dia(8, "2026-05-12")
    consultar_historial_visitas_usuario(44000014)
    consultar_plato_mas_vendido(8, "2026-05-12")


def insertar_nueva_promocion():
    """
    Q6: Insertar una nueva promoción.

    En Cassandra una misma promoción se guarda en dos tablas:
    - promociones_por_restaurante
    - promociones_activas_por_fecha

    Esto se hace porque cada tabla responde a una consulta distinta.
    """

    cluster, session = conectar_con_keyspace()

    nueva_promocion = {
        "restaurante_id": 14,
        "estado": "activa",
        "fecha_inicio": "2026-05-12",
        "fecha_fin": "2026-05-20",
        "promocion_id": 999,
        "titulo": "Promo Python - 2x1 en platos seleccionados",
        "descripcion": "Promoción insertada desde Python para evidenciar escritura en Cassandra.",
        "descuento": 35,
        "barrio": "Puerto Madero"
    }

    fecha_inicio = convertir_fecha(nueva_promocion["fecha_inicio"])
    fecha_fin = convertir_fecha(nueva_promocion["fecha_fin"])

    insert_por_restaurante = session.prepare("""
        INSERT INTO promociones_por_restaurante (
            restaurante_id, estado, fecha_fin, promocion_id,
            titulo, descripcion, descuento, fecha_inicio, barrio
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_por_fecha = session.prepare("""
        INSERT INTO promociones_activas_por_fecha (
            dia_vigencia, barrio, restaurante_id, promocion_id,
            titulo, descuento, fecha_inicio, fecha_fin, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    session.execute(insert_por_restaurante, (
        nueva_promocion["restaurante_id"],
        nueva_promocion["estado"],
        fecha_fin,
        nueva_promocion["promocion_id"],
        nueva_promocion["titulo"],
        nueva_promocion["descripcion"],
        nueva_promocion["descuento"],
        fecha_inicio,
        nueva_promocion["barrio"]
    ))

    if nueva_promocion["estado"] == "activa":
        for dia in rango_fechas(fecha_inicio, fecha_fin):
            session.execute(insert_por_fecha, (
                dia,
                nueva_promocion["barrio"],
                nueva_promocion["restaurante_id"],
                nueva_promocion["promocion_id"],
                nueva_promocion["titulo"],
                nueva_promocion["descuento"],
                fecha_inicio,
                fecha_fin,
                nueva_promocion["estado"]
            ))

    print("\nQ6 - Nueva promoción insertada correctamente.")
    print(
        f"- Promo ID {nueva_promocion['promocion_id']} | "
        f"Restaurante {nueva_promocion['restaurante_id']} | "
        f"{nueva_promocion['titulo']} | "
        f"{nueva_promocion['descuento']}% OFF"
    )

    session.shutdown()
    cluster.shutdown()


def insertar_nueva_visita():
    """
    Q6: Insertar una nueva visita.

    En Cassandra una visita se guarda en varias tablas:
    - visitas_por_restaurante_dia
    - visitas_por_usuario_fecha
    - metricas_restaurante_por_dia

    """

    cluster, session = conectar_con_keyspace()

    nueva_visita = {
        "visita_id": 999,
        "dni_usuario": 44000014,
        "restaurante_id": 8,
        "plato_id": 999,
        "plato_nombre": "Plato especial Python",
        "tipo_comida": "Mexicana",
        "barrio": "Almagro",
        "fecha": "2026-05-12",
        "hora": "23:30",
        "monto": 4200
    }

    fecha = convertir_fecha(nueva_visita["fecha"])
    hora = convertir_hora(nueva_visita["hora"])
    monto = Decimal(str(nueva_visita["monto"]))

    insert_visita_restaurante = session.prepare("""
        INSERT INTO visitas_por_restaurante_dia (
            restaurante_id, fecha, hora, visita_id, dni_usuario,
            plato_id, plato_nombre, tipo_comida, barrio, monto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_visita_usuario = session.prepare("""
        INSERT INTO visitas_por_usuario_fecha (
            dni_usuario, fecha, hora, visita_id, restaurante_id,
            plato_id, plato_nombre, tipo_comida, monto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    insert_metrica = session.prepare("""
        INSERT INTO metricas_restaurante_por_dia (
            restaurante_id, fecha, cantidad_vendida, plato_id,
            plato_nombre, tipo_comida, total_ingresos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """)

    session.execute(insert_visita_restaurante, (
        nueva_visita["restaurante_id"],
        fecha,
        hora,
        nueva_visita["visita_id"],
        nueva_visita["dni_usuario"],
        nueva_visita["plato_id"],
        nueva_visita["plato_nombre"],
        nueva_visita["tipo_comida"],
        nueva_visita["barrio"],
        monto
    ))

    session.execute(insert_visita_usuario, (
        nueva_visita["dni_usuario"],
        fecha,
        hora,
        nueva_visita["visita_id"],
        nueva_visita["restaurante_id"],
        nueva_visita["plato_id"],
        nueva_visita["plato_nombre"],
        nueva_visita["tipo_comida"],
        monto
    ))

    session.execute(insert_metrica, (
        nueva_visita["restaurante_id"],
        fecha,
        1,
        nueva_visita["plato_id"],
        nueva_visita["plato_nombre"],
        nueva_visita["tipo_comida"],
        monto
    ))

    print("\nQ6 - Nueva visita insertada correctamente.")
    print(
        f"- Visita {nueva_visita['visita_id']} | "
        f"Usuario {nueva_visita['dni_usuario']} | "
        f"Restaurante {nueva_visita['restaurante_id']} | "
        f"Plato: {nueva_visita['plato_nombre']} | "
        f"Monto: ${monto}"
    )

    session.shutdown()
    cluster.shutdown()


def ejecutar_escrituras():
    """
    Ejecuta Q6: inserción de nueva promoción y nueva visita.
    Luego vuelve a consultar para evidenciar que los datos quedaron guardados.
    """

    print("\n==============================")
    print("Q6 - ESCRITURAS EN CASSANDRA")
    print("==============================")

    insertar_nueva_promocion()
    insertar_nueva_visita()

    print("\nVerificación después de las escrituras:")

    consultar_promociones_por_restaurante(14)
    consultar_promociones_por_fecha_barrio("2026-05-12", "Puerto Madero")
    consultar_visitas_por_restaurante_dia(8, "2026-05-12")
    consultar_historial_visitas_usuario(44000014)
    consultar_plato_mas_vendido(8, "2026-05-12")


def main():
    print("Conectando Python con Cassandra...")

    crear_keyspace()
    crear_tablas()
    verificar_tablas()

    limpiar_tablas()
    cargar_dataset()

    ejecutar_consultas()
    ejecutar_escrituras()

    print("\nInicialización, carga, consultas y escrituras de Cassandra finalizadas correctamente.")


if __name__ == "__main__":
    main()