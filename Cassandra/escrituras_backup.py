import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

from conexion import conectar_con_keyspace
from utilidades import convertir_fecha, convertir_hora, rango_fechas
from consultas import (
    consultar_promociones_por_restaurante,
    consultar_promociones_por_fecha_barrio,
    consultar_visitas_por_restaurante_dia,
    consultar_historial_visitas_usuario,
    consultar_plato_mas_vendido
)


def actualizar_rankings_redis_si_disponible(restaurante_id, tipo_comida):
    """
    Intenta actualizar los rankings de Redis tras insertar una visita en Cassandra.
    Si Redis no está disponible, lo informa y continúa sin interrumpir el flujo.
    Usa restaurante_id como identificador porque Cassandra no almacena el nombre.
    """
    redis_dir = Path(__file__).resolve().parent.parent / "Redis"
    redis_consultas = redis_dir / "consultas.py"

    if not redis_consultas.exists():
        print("No se actualizó Redis: no se encontró Redis/consultas.py.")
        return

    try:
        if str(redis_dir) not in sys.path:
            sys.path.insert(0, str(redis_dir))

        spec = importlib.util.spec_from_file_location("consultas_redis", redis_consultas)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        mod.registrar_visita(f"restaurante_{restaurante_id}", tipo_comida)
    except Exception as error:
        print(f"No se pudo actualizar Redis: {error}")


def existe_promocion(session, restaurante_id, estado, fecha_fin, promocion_id):
    """
    Verifica si la promoción ya existe en la tabla principal de promociones.

    Se consulta usando la clave primaria de promociones_por_restaurante:
    restaurante_id + estado + fecha_fin + promocion_id.
    Esto evita sobrescribir una promoción de prueba si el script se ejecuta varias veces.
    """
    consulta = session.prepare("""
        SELECT promocion_id
        FROM promociones_por_restaurante
        WHERE restaurante_id = ?
        AND estado = ?
        AND fecha_fin = ?
        AND promocion_id = ?
        LIMIT 1;
    """)

    fila = session.execute(consulta, (
        restaurante_id,
        estado,
        fecha_fin,
        promocion_id
    )).one()

    return fila is not None


def existe_visita(session, restaurante_id, fecha, hora, visita_id):
    """
    Verifica si la visita ya existe en la tabla principal de visitas.

    Se consulta usando la clave primaria de visitas_por_restaurante_dia:
    restaurante_id + fecha + hora + visita_id.
    Esto evita sobrescribir una visita de prueba si el script se ejecuta varias veces.
    """
    consulta = session.prepare("""
        SELECT visita_id
        FROM visitas_por_restaurante_dia
        WHERE restaurante_id = ?
        AND fecha = ?
        AND hora = ?
        AND visita_id = ?
        LIMIT 1;
    """)

    fila = session.execute(consulta, (
        restaurante_id,
        fecha,
        hora,
        visita_id
    )).one()

    return fila is not None


def insertar_nueva_promocion():
    """
    Q6: Insertar nueva promoción.

    Una promoción se guarda en dos tablas:
    - promociones_por_restaurante
    - promociones_activas_por_fecha

    Antes de insertar, se verifica si la clave ya existe para evitar sobrescrituras
    accidentales durante las pruebas.
    """
    cluster, session = conectar_con_keyspace()

    try:
        nueva_promocion = {
            "restaurante_id": 14,
            "estado": "activa",
            "fecha_inicio": "2026-05-12",
            "fecha_fin": "2026-05-20",
            "promocion_id": 999,
            "titulo": "Promo Python - 2x1 en platos veganos",
            "descripcion": "Promoción insertada desde Python para evidenciar escritura en Cassandra.",
            "descuento": 35,
            "barrio": "Almagro"
        }

        fecha_inicio = convertir_fecha(nueva_promocion["fecha_inicio"])
        fecha_fin = convertir_fecha(nueva_promocion["fecha_fin"])

        if existe_promocion(
            session,
            nueva_promocion["restaurante_id"],
            nueva_promocion["estado"],
            fecha_fin,
            nueva_promocion["promocion_id"]
        ):
            print("\nQ6 - La promoción ya existe. No se vuelve a insertar para evitar sobrescrituras.")
            print(
                f"- Promo ID {nueva_promocion['promocion_id']} | "
                f"Restaurante {nueva_promocion['restaurante_id']} | "
                f"Clave ya registrada en promociones_por_restaurante."
            )
            return

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

    finally:
        session.shutdown()
        cluster.shutdown()


def insertar_nueva_visita():
    """
    Q6: Insertar nueva visita.

    Una visita se guarda en:
    - visitas_por_restaurante_dia
    - visitas_por_usuario_fecha
    - metricas_restaurante_por_dia

    Antes de insertar, se verifica si la clave ya existe para evitar sobrescrituras
    accidentales durante las pruebas.
    """
    cluster, session = conectar_con_keyspace()

    try:
        nueva_visita = {
            "visita_id": 999,
            "dni_usuario": 44000014,
            "restaurante_id": 14,
            "plato_id": 59,
            "plato_nombre": "Bowl veggie",
            "tipo_comida": "Vegano",
            "barrio": "Almagro",
            "fecha": "2026-05-12",
            "hora": "23:30",
            "monto": 7800
        }

        fecha = convertir_fecha(nueva_visita["fecha"])
        hora = convertir_hora(nueva_visita["hora"])
        monto = Decimal(str(nueva_visita["monto"]))

        if existe_visita(
            session,
            nueva_visita["restaurante_id"],
            fecha,
            hora,
            nueva_visita["visita_id"]
        ):
            print("\nQ6 - La visita ya existe. No se vuelve a insertar para evitar sobrescrituras.")
            print(
                f"- Visita {nueva_visita['visita_id']} | "
                f"Restaurante {nueva_visita['restaurante_id']} | "
                f"Fecha {fecha} | Hora {hora} | "
                f"Clave ya registrada en visitas_por_restaurante_dia."
            )
            return

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

        actualizar_rankings_redis_si_disponible(
            nueva_visita["restaurante_id"],
            nueva_visita["tipo_comida"]
        )

    finally:
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
    consultar_promociones_por_fecha_barrio("2026-05-12", "Almagro")
    consultar_visitas_por_restaurante_dia(14, "2026-05-12")
    consultar_historial_visitas_usuario(44000014)
    consultar_plato_mas_vendido(14, "2026-05-12")