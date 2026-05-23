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
