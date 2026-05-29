from conexion import conectar_con_keyspace
from utilidades import convertir_fecha


def _fila_a_dict(fila):
    return dict(fila._asdict())


def consultar_promociones_por_restaurante(restaurante_id):
    """
    Q1: Ver promociones activas por restaurante.
    Retorna filas para que el frontend pueda mostrarlas sin volver a escribir la query.
    """
    cluster, session = conectar_con_keyspace()
    try:
        filas = list(session.execute("""
            SELECT restaurante_id, estado, fecha_fin, promocion_id, titulo,
                   descripcion, descuento, fecha_inicio, barrio
            FROM promociones_por_restaurante
            WHERE restaurante_id = %s
            AND estado = %s;
        """, (int(restaurante_id), "activa")))

        print(f"\nQ1 - Promociones activas del restaurante {restaurante_id}:")
        if not filas:
            print("No se encontraron promociones activas para ese restaurante.")
        for fila in filas:
            print(
                f"- Promo ID {fila.promocion_id} | {fila.titulo} | "
                f"{fila.descuento}% OFF | Barrio: {fila.barrio} | "
                f"Vigencia: {fila.fecha_inicio} a {fila.fecha_fin}"
            )
        return [_fila_a_dict(fila) for fila in filas]
    finally:
        session.shutdown()
        cluster.shutdown()


def consultar_promociones_por_fecha_barrio(dia_vigencia, barrio):
    """
    Q2: Ver promociones activas por fecha y barrio.
    """
    cluster, session = conectar_con_keyspace()
    try:
        fecha = convertir_fecha(dia_vigencia)
        filas = list(session.execute("""
            SELECT dia_vigencia, barrio, restaurante_id, promocion_id,
                   titulo, descuento, fecha_inicio, fecha_fin, estado
            FROM promociones_activas_por_fecha
            WHERE dia_vigencia = %s
            AND barrio = %s;
        """, (fecha, barrio)))

        print(f"\nQ2 - Promociones activas el día {dia_vigencia} en {barrio}:")
        if not filas:
            print("No se encontraron promociones activas para esa fecha y barrio.")
        for fila in filas:
            print(
                f"- Restaurante {fila.restaurante_id} | Promo ID {fila.promocion_id} | "
                f"{fila.titulo} | {fila.descuento}% OFF | "
                f"Vigencia: {fila.fecha_inicio} a {fila.fecha_fin}"
            )
        return [_fila_a_dict(fila) for fila in filas]
    finally:
        session.shutdown()
        cluster.shutdown()


def consultar_visitas_por_restaurante_dia(restaurante_id, fecha_texto):
    """
    Q3: Ver visitas registradas en un día de un restaurante.
    """
    cluster, session = conectar_con_keyspace()
    try:
        fecha = convertir_fecha(fecha_texto)
        filas = list(session.execute("""
            SELECT restaurante_id, fecha, hora, visita_id, dni_usuario,
                   plato_id, plato_nombre, tipo_comida, barrio, monto
            FROM visitas_por_restaurante_dia
            WHERE restaurante_id = %s
            AND fecha = %s;
        """, (int(restaurante_id), fecha)))

        print(f"\nQ3 - Visitas del restaurante {restaurante_id} el día {fecha_texto}:")
        if not filas:
            print("No se encontraron visitas para ese restaurante y fecha.")
        for fila in filas:
            print(
                f"- Visita {fila.visita_id} | Usuario: {fila.dni_usuario} | "
                f"Hora: {fila.hora} | Plato: {fila.plato_nombre} | "
                f"Tipo: {fila.tipo_comida} | Barrio: {fila.barrio} | Monto: ${fila.monto}"
            )
        return [_fila_a_dict(fila) for fila in filas]
    finally:
        session.shutdown()
        cluster.shutdown()


def consultar_historial_visitas_usuario(dni_usuario):
    """
    Q4: Ver historial de visitas por usuario.
    """
    cluster, session = conectar_con_keyspace()
    try:
        filas = list(session.execute("""
            SELECT dni_usuario, fecha, hora, visita_id, restaurante_id,
                   plato_id, plato_nombre, tipo_comida, monto
            FROM visitas_por_usuario_fecha
            WHERE dni_usuario = %s
            LIMIT 10;
        """, (int(dni_usuario),)))

        print(f"\nQ4 - Historial de visitas del usuario {dni_usuario}:")
        if not filas:
            print("No se encontraron visitas para ese usuario.")
        for fila in filas:
            print(
                f"- Fecha: {fila.fecha} | Hora: {fila.hora} | "
                f"Restaurante: {fila.restaurante_id} | Plato: {fila.plato_nombre} | "
                f"Tipo: {fila.tipo_comida} | Monto: ${fila.monto}"
            )
        return [_fila_a_dict(fila) for fila in filas]
    finally:
        session.shutdown()
        cluster.shutdown()


def consultar_plato_mas_vendido(restaurante_id, fecha_texto):
    """
    Q5: Ver plato/comida más vendida por restaurante y día.
    """
    cluster, session = conectar_con_keyspace()
    try:
        fecha = convertir_fecha(fecha_texto)
        filas = list(session.execute("""
            SELECT restaurante_id, fecha, cantidad_vendida, plato_id,
                   plato_nombre, tipo_comida, total_ingresos
            FROM metricas_restaurante_por_dia
            WHERE restaurante_id = %s
            AND fecha = %s
            LIMIT 10;
        """, (int(restaurante_id), fecha)))

        print(f"\nQ5 - Plato más vendido del restaurante {restaurante_id} el día {fecha_texto}:")
        if not filas:
            print("No se encontraron métricas para ese restaurante y fecha.")
        for fila in filas:
            print(
                f"- Plato: {fila.plato_nombre} | Tipo: {fila.tipo_comida} | "
                f"Cantidad vendida: {fila.cantidad_vendida} | "
                f"Total ingresos: ${fila.total_ingresos}"
            )
        return [_fila_a_dict(fila) for fila in filas]
    finally:
        session.shutdown()
        cluster.shutdown()


def ejecutar_consultas():
    """
    Ejecuta Q1, Q2, Q3, Q4 y Q5.
    """
    print("\n==============================")
    print("EJECUCIÓN DE CONSULTAS CASSANDRA")
    print("==============================")

    consultar_promociones_por_restaurante(14)
    consultar_promociones_por_fecha_barrio("2026-05-12", "Almagro")
    consultar_visitas_por_restaurante_dia(8, "2026-05-12")
    consultar_historial_visitas_usuario(44000014)
    consultar_plato_mas_vendido(8, "2026-05-12")
