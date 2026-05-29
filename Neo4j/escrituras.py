from conexion import obtener_driver, obtener_session
from consultas import (
    consultar_perfil_usuario,
    consultar_usuarios_que_sigue,
    recomendar_bien_calificados_por_amigos
)
from utilidades import normalizar_hora


def _imprimir_registro(titulo, registro):
    print(f"\n{titulo}")

    if registro is None:
        print("No se pudo realizar la operacion.")
        return

    texto = " | ".join(
        f"{clave}: {valor}"
        for clave, valor in registro.items()
    )
    print(f"- {texto}")


def seguir_usuario(username_origen, username_destino):
    consulta = """
        MATCH (origen:Usuario {username: $username_origen})
        MATCH (destino:Usuario {username: $username_destino})
        WHERE origen <> destino
        MERGE (origen)-[:SIGUE]->(destino)
        RETURN origen.username AS usuario,
               destino.username AS sigue_a
    """

    driver = obtener_driver()

    with obtener_session(driver) as session:
        fila = session.run(
            consulta,
            {
                "username_origen": username_origen,
                "username_destino": username_destino
            }
        ).single()

    driver.close()
    registro = fila.data() if fila else None
    _imprimir_registro("Escritura: seguir usuario", registro)
    return registro


def dejar_de_seguir_usuario(username_origen, username_destino):
    consulta = """
        MATCH (origen:Usuario {username: $username_origen})-[s:SIGUE]->(destino:Usuario {username: $username_destino})
        WITH origen, destino, s
        DELETE s
        RETURN origen.username AS usuario,
               destino.username AS dejo_de_seguir
    """

    driver = obtener_driver()

    with obtener_session(driver) as session:
        fila = session.run(
            consulta,
            {
                "username_origen": username_origen,
                "username_destino": username_destino
            }
        ).single()

    driver.close()
    registro = fila.data() if fila else None
    _imprimir_registro("Escritura: dejar de seguir usuario", registro)
    return registro


def registrar_visita_y_calificacion(username, restaurante_id, puntaje, comentario):
    """
    Inserta una nueva visita, el plato pedido y una calificacion.
    Se usa para mostrar que las recomendaciones tambien actualizan el grafo.
    """
    consulta = """
        MATCH (u:Usuario {username: $username})
        MATCH (r:Restaurante {restaurante_id: toInteger($restaurante_id)})
        MATCH (r)-[:OFRECE]->(p:Plato)
        WITH u, r, p
        ORDER BY p.disponible DESC, p.precio ASC
        WITH u, r, collect(p)[0] AS p
        OPTIONAL MATCH ()-[vis:VISITO]->()
        WITH u, r, p, coalesce(max(vis.visita_id), 0) + 1 AS nuevo_visita_id
        OPTIONAL MATCH ()-[cal:CALIFICO]->()
        WITH u, r, p, nuevo_visita_id, coalesce(max(cal.resena_id), 0) + 1 AS nuevo_resena_id
        CREATE (u)-[v:VISITO {
            visita_id: nuevo_visita_id,
            fecha: date($fecha),
            hora: localtime($hora),
            monto: p.precio,
            barrio: r.barrio,
            origen: 'escritura_python'
        }]->(r)
        CREATE (u)-[pedido:PIDIO {
            visita_id: nuevo_visita_id,
            fecha: date($fecha),
            hora: localtime($hora),
            monto: p.precio,
            plato_nombre: p.nombre,
            tipo_comida: p.tipo_comida,
            origen: 'escritura_python'
        }]->(p)
        CREATE (u)-[c:CALIFICO {
            resena_id: nuevo_resena_id,
            puntaje: toInteger($puntaje),
            comentario: $comentario,
            fecha: date($fecha),
            origen: 'escritura_python'
        }]->(r)
        RETURN u.username AS usuario,
               r.nombre AS restaurante,
               p.nombre AS plato,
               nuevo_visita_id AS visita_id,
               nuevo_resena_id AS resena_id,
               c.puntaje AS puntaje
    """

    parametros = {
        "username": username,
        "restaurante_id": restaurante_id,
        "puntaje": puntaje,
        "comentario": comentario,
        "fecha": "2026-05-23",
        "hora": normalizar_hora("21:30")
    }

    driver = obtener_driver()

    with obtener_session(driver) as session:
        fila = session.run(consulta, parametros).single()

    driver.close()
    registro = fila.data() if fila else None
    _imprimir_registro("Escritura: registrar visita y calificacion", registro)
    return registro


def ejecutar_escrituras(username="VitoNava"):
    """
    Ejecuta escrituras y consultas de verificacion.
    """
    print("\n==============================")
    print("ESCRITURAS EN NEO4J")
    print("==============================")

    seguir_usuario(username, "MiaDiaz")
    dejar_de_seguir_usuario(username, "MiaDiaz")
    seguir_usuario(username, "MiaDiaz")

    registrar_visita_y_calificacion(
        username=username,
        restaurante_id=15,
        puntaje=5,
        comentario="Visita registrada desde Python luego de una recomendacion."
    )

    print("\nVerificacion despues de escrituras:")
    consultar_perfil_usuario(username)
    consultar_usuarios_que_sigue(username)
    recomendar_bien_calificados_por_amigos(username)


def sincronizar_resena_desde_mongo(dni_usuario, restaurante_id, resena_id, puntaje, comentario, fecha):
    """
    Mantiene consistencia MongoDB -> Neo4j.
    Cuando MongoDB inserta una reseña/calificación, Neo4j crea o actualiza
    la relación (:Usuario)-[:CALIFICO]->(:Restaurante) con el mismo resena_id.
    """
    consulta = """
        MATCH (u:Usuario {dni_usuario: toInteger($dni_usuario)})
        MATCH (r:Restaurante {restaurante_id: toInteger($restaurante_id)})
        MERGE (u)-[c:CALIFICO {resena_id: toInteger($resena_id)}]->(r)
        SET c.puntaje = toInteger($puntaje),
            c.comentario = $comentario,
            c.fecha = date($fecha),
            c.origen = 'sync_mongodb_frontend'
        RETURN u.username AS usuario,
               r.nombre AS restaurante,
               c.resena_id AS resena_id,
               c.puntaje AS puntaje,
               c.fecha AS fecha
    """
    driver = obtener_driver()
    try:
        with obtener_session(driver) as session:
            fila = session.run(consulta, {
                "dni_usuario": dni_usuario,
                "restaurante_id": restaurante_id,
                "resena_id": resena_id,
                "puntaje": puntaje,
                "comentario": comentario,
                "fecha": fecha,
            }).single()
    finally:
        driver.close()

    registro = fila.data() if fila else None
    _imprimir_registro("Sync MongoDB -> Neo4j: reseña/calificación", registro)
    return registro


def sincronizar_visita_desde_cassandra(**visita):
    """
    Mantiene consistencia Cassandra -> Neo4j.
    Cuando Cassandra registra una visita, Neo4j crea/actualiza VISITO y PIDIO
    para que las recomendaciones sociales vean la misma interacción.
    """
    consulta = """
        MATCH (u:Usuario {dni_usuario: toInteger($dni_usuario)})
        MATCH (r:Restaurante {restaurante_id: toInteger($restaurante_id)})
        MERGE (p:Plato {plato_id: toInteger($plato_id)})
        SET p.nombre = $plato_nombre,
            p.plato_nombre = $plato_nombre,
            p.tipo_comida = $tipo_comida
        MERGE (r)-[:OFRECE]->(p)
        MERGE (u)-[v:VISITO {visita_id: toInteger($visita_id)}]->(r)
        SET v.fecha = date($fecha),
            v.hora = localtime($hora),
            v.monto = toFloat($monto),
            v.barrio = $barrio,
            v.origen = 'sync_cassandra_frontend'
        MERGE (u)-[pedido:PIDIO {visita_id: toInteger($visita_id)}]->(p)
        SET pedido.fecha = date($fecha),
            pedido.hora = localtime($hora),
            pedido.monto = toFloat($monto),
            pedido.plato_nombre = $plato_nombre,
            pedido.tipo_comida = $tipo_comida,
            pedido.origen = 'sync_cassandra_frontend'
        RETURN u.username AS usuario,
               r.nombre AS restaurante,
               p.nombre AS plato,
               v.visita_id AS visita_id,
               v.fecha AS fecha
    """
    driver = obtener_driver()
    try:
        with obtener_session(driver) as session:
            fila = session.run(consulta, {
                "dni_usuario": int(visita["dni_usuario"]),
                "restaurante_id": int(visita["restaurante_id"]),
                "visita_id": int(visita["visita_id"]),
                "plato_id": int(visita.get("plato_id", 0)),
                "plato_nombre": visita.get("plato_nombre", "Plato registrado"),
                "tipo_comida": visita.get("tipo_comida", "Sin tipo"),
                "barrio": visita.get("barrio", ""),
                "monto": float(visita.get("monto", 0)),
                "fecha": str(visita["fecha"]),
                "hora": str(visita.get("hora", "12:00:00"))[:8],
            }).single()
    finally:
        driver.close()

    registro = fila.data() if fila else None
    _imprimir_registro("Sync Cassandra -> Neo4j: visita/pedido", registro)
    return registro
