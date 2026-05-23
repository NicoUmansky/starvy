from collections import defaultdict
from decimal import Decimal

from conexion import conectar_con_keyspace
from utilidades import leer_json, convertir_fecha, convertir_hora, rango_fechas


def limpiar_tablas():
    """
    Limpia las tablas antes de volver a cargar el dataset.
    Esto evita mezclar datos de prueba manuales con datos reales del JSON.
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
    Carga promociones.json en:
    - promociones_por_restaurante
    - promociones_activas_por_fecha
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

    Además genera:
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