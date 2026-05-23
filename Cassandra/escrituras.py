from decimal import Decimal

from conexion import conectar_con_keyspace
from utilidades import convertir_fecha, convertir_hora, rango_fechas
from consultas import (
    consultar_promociones_por_restaurante,
    consultar_promociones_por_fecha_barrio,
    consultar_visitas_por_restaurante_dia,
    consultar_historial_visitas_usuario,
    consultar_plato_mas_vendido
)


def insertar_nueva_promocion():
    """
    Q6: Insertar nueva promoción.

    Una promoción se guarda en dos tablas:
    - promociones_por_restaurante
    - promociones_activas_por_fecha
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
    Q6: Insertar nueva visita.

    Una visita se guarda en:
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
    Ejecuta Q6 y luego consulta nuevamente para verificar los datos insertados.
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