from conexion import obtener_driver, obtener_session
from utilidades import leer_json, normalizar_hora


RELACIONES_SIGUE = [
    ("VitoNava", "ValentinaMannino"),
    ("VitoNava", "SofiaGarcia"),
    ("VitoNava", "FrancoLan"),
    ("VitoNava", "NicolasGiordano"),
    ("ValentinaMannino", "SofiaGarcia"),
    ("ValentinaMannino", "CamilaRodriguez"),
    ("ValentinaMannino", "MiaDiaz"),
    ("SofiaGarcia", "VitoNava"),
    ("SofiaGarcia", "ValentinaMannino"),
    ("SofiaGarcia", "MartinaLopez"),
    ("FrancoLan", "VitoNava"),
    ("FrancoLan", "LucasFernandez"),
    ("FrancoLan", "JuanMorales"),
    ("NicolasGiordano", "VitoNava"),
    ("NicolasGiordano", "FrancoLan"),
    ("NicolasGiordano", "AgustinRuiz"),
    ("LucasFernandez", "MiaDiaz"),
    ("LucasFernandez", "DiegoVillalba"),
    ("MiaDiaz", "VitoNava"),
    ("MiaDiaz", "SofiaGarcia"),
    ("JuanMorales", "LolaLeiva"),
    ("JuanMorales", "MilagrosGodoy"),
    ("DiegoVillalba", "SolBravo"),
    ("DiegoVillalba", "ArianaFerreyra"),
    ("MilagrosGodoy", "MaiteFunes"),
    ("MilagrosGodoy", "AndresLedesma")
]


def limpiar_grafo():
    """
    Borra nodos y relaciones, pero conserva constraints e indices.
    """
    driver = obtener_driver()

    with obtener_session(driver) as session:
        session.run("MATCH (n) DETACH DELETE n")

    driver.close()
    print("Grafo de Neo4j limpiado correctamente.")


def cargar_usuarios(session):
    usuarios = leer_json("usuarios.json")

    session.run("""
        UNWIND $usuarios AS fila
        MERGE (u:Usuario {dni_usuario: toInteger(fila.dni_usuario)})
        SET u.nombre = fila.nombre,
            u.apellido = fila.apellido,
            u.username = fila.username,
            u.mail = fila.mail
    """, usuarios=usuarios)

    print(f"Usuarios cargados: {len(usuarios)}")


def cargar_restaurantes(session):
    restaurantes = leer_json("restaurantes.json")

    session.run("""
        UNWIND $restaurantes AS fila
        MERGE (r:Restaurante {restaurante_id: toInteger(fila.restaurante_id)})
        SET r.nombre = fila.nombre,
            r.tipo_comida = fila.tipo_comida,
            r.barrio = fila.barrio,
            r.direccion = fila.direccion,
            r.calificacion_promedio = toFloat(fila.calificacion_promedio)
    """, restaurantes=restaurantes)

    print(f"Restaurantes cargados: {len(restaurantes)}")


def cargar_platos(session):
    platos = leer_json("platos.json")

    session.run("""
        UNWIND $platos AS fila
        MATCH (r:Restaurante {restaurante_id: toInteger(fila.restaurante_id)})
        MERGE (p:Plato {plato_id: toInteger(fila.plato_id)})
        SET p.nombre = fila.plato_nombre,
            p.tipo_comida = fila.tipo_comida,
            p.precio = toFloat(fila.precio),
            p.disponible = fila.disponible
        MERGE (r)-[:OFRECE]->(p)
    """, platos=platos)

    print(f"Platos cargados y vinculados con restaurantes: {len(platos)}")


def cargar_visitas(session):
    visitas = leer_json("visitas.json")

    for visita in visitas:
        visita["hora"] = normalizar_hora(visita["hora"])

    session.run("""
        UNWIND $visitas AS fila
        MATCH (u:Usuario {dni_usuario: toInteger(fila.dni_usuario)})
        MATCH (r:Restaurante {restaurante_id: toInteger(fila.restaurante_id)})
        MATCH (p:Plato {plato_id: toInteger(fila.plato_id)})
        MERGE (u)-[v:VISITO {visita_id: toInteger(fila.visita_id)}]->(r)
        SET v.fecha = date(fila.fecha),
            v.hora = localtime(fila.hora),
            v.monto = toFloat(fila.monto),
            v.barrio = fila.barrio
        MERGE (u)-[pedido:PIDIO {visita_id: toInteger(fila.visita_id)}]->(p)
        SET pedido.fecha = date(fila.fecha),
            pedido.hora = localtime(fila.hora),
            pedido.monto = toFloat(fila.monto),
            pedido.plato_nombre = fila.plato_nombre,
            pedido.tipo_comida = fila.tipo_comida
    """, visitas=visitas)

    print(f"Visitas cargadas: {len(visitas)}")
    print(f"Relaciones PIDIO cargadas: {len(visitas)}")


def cargar_resenas(session):
    resenas = leer_json("resenas.json")

    session.run("""
        UNWIND $resenas AS fila
        MATCH (u:Usuario {dni_usuario: toInteger(fila.dni_usuario)})
        MATCH (r:Restaurante {restaurante_id: toInteger(fila.restaurante_id)})
        MERGE (u)-[c:CALIFICO {resena_id: toInteger(fila.resena_id)}]->(r)
        SET c.puntaje = toInteger(fila.puntaje),
            c.comentario = fila.comentario,
            c.fecha = date(fila.fecha)
    """, resenas=resenas)

    print(f"Resenas cargadas como relaciones CALIFICO: {len(resenas)}")


def cargar_red_social(session):
    relaciones = [
        {"origen": origen, "destino": destino}
        for origen, destino in RELACIONES_SIGUE
    ]

    session.run("""
        UNWIND $relaciones AS fila
        MATCH (origen:Usuario {username: fila.origen})
        MATCH (destino:Usuario {username: fila.destino})
        MERGE (origen)-[:SIGUE]->(destino)
    """, relaciones=relaciones)

    print(f"Relaciones SIGUE cargadas: {len(relaciones)}")


def cargar_dataset():
    """
    Carga todos los nodos y relaciones del grafo.
    """
    print("\nCargando dataset en Neo4j...")

    driver = obtener_driver()

    with obtener_session(driver) as session:
        cargar_usuarios(session)
        cargar_restaurantes(session)
        cargar_platos(session)
        cargar_visitas(session)
        cargar_resenas(session)
        cargar_red_social(session)

    driver.close()
    print("Carga del dataset de Neo4j finalizada correctamente.")
