from conexion import obtener_driver, obtener_session


USERNAME_DEMO = "VitoNava"


def _formatear_valor(valor):
    if isinstance(valor, list):
        return ", ".join(str(item) for item in valor)

    if isinstance(valor, float):
        return f"{valor:.2f}"

    return str(valor)


def _imprimir_resultados(titulo, registros):
    print(f"\n{titulo}")

    if not registros:
        print("No se encontraron resultados.")
        return

    for registro in registros:
        texto = " | ".join(
            f"{clave}: {_formatear_valor(valor)}"
            for clave, valor in registro.items()
        )
        print(f"- {texto}")


def ejecutar_consulta(titulo, consulta, parametros=None):
    driver = obtener_driver()

    with obtener_session(driver) as session:
        resultado = session.run(consulta, parametros or {})
        registros = [fila.data() for fila in resultado]

    driver.close()
    _imprimir_resultados(titulo, registros)
    return registros


def consultar_perfil_usuario(username):
    consulta = """
        MATCH (u:Usuario {username: $username})
        OPTIONAL MATCH (u)-[s:SIGUE]->()
        WITH u, count(s) AS siguiendo
        OPTIONAL MATCH (u)<-[seguidor:SIGUE]-()
        WITH u, siguiendo, count(seguidor) AS seguidores
        OPTIONAL MATCH (u)-[v:VISITO]->()
        WITH u, siguiendo, seguidores, count(v) AS visitas
        OPTIONAL MATCH (u)-[c:CALIFICO]->()
        RETURN u.username AS username,
               u.nombre + ' ' + u.apellido AS nombre,
               siguiendo,
               seguidores,
               visitas,
               count(c) AS resenas
    """

    return ejecutar_consulta(
        f"Perfil social y gastronomico de {username}",
        consulta,
        {"username": username}
    )


def consultar_usuarios_que_sigue(username):
    consulta = """
        MATCH (:Usuario {username: $username})-[:SIGUE]->(seguido:Usuario)
        RETURN seguido.username AS username,
               seguido.nombre + ' ' + seguido.apellido AS nombre
        ORDER BY username
    """

    return ejecutar_consulta(
        f"Usuarios que sigue {username}",
        consulta,
        {"username": username}
    )


def consultar_seguidores(username):
    consulta = """
        MATCH (seguidor:Usuario)-[:SIGUE]->(:Usuario {username: $username})
        RETURN seguidor.username AS username,
               seguidor.nombre + ' ' + seguidor.apellido AS nombre
        ORDER BY username
    """

    return ejecutar_consulta(
        f"Seguidores de {username}",
        consulta,
        {"username": username}
    )


def buscar_usuarios(termino_busqueda, limite=10):
    consulta = """
        MATCH (u:Usuario)
        WHERE u.username CONTAINS $termino 
           OR toLower(u.nombre) CONTAINS toLower($termino)
           OR toLower(u.apellido) CONTAINS toLower($termino)
        RETURN u.username AS username, 
               u.nombre AS nombre, 
               u.apellido AS apellido
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Buscar usuario (termino: {termino_busqueda})",
        consulta,
        {"termino": termino_busqueda, "limite": limite}
    )


def consultar_visitas_amigos(username, limite=10):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)-[v:VISITO]->(r:Restaurante)
        RETURN amigo.username AS amigo,
               r.nombre AS restaurante,
               v.fecha AS fecha
        ORDER BY v.fecha DESC, amigo
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Restaurantes que visitaron los amigos de {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def consultar_calificaciones_amigos(username, limite=10):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)-[c:CALIFICO]->(r:Restaurante)
        RETURN amigo.username AS amigo,
               r.nombre AS restaurante,
               c.puntaje AS puntaje,
               c.comentario AS comentario
        ORDER BY c.fecha DESC, c.puntaje DESC
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Calificaciones hechas por los amigos de {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def sugerir_usuarios_para_seguir(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(:Usuario)-[:SIGUE]->(sugerido:Usuario)
        WHERE sugerido <> yo
          AND NOT (yo)-[:SIGUE]->(sugerido)
        RETURN sugerido.username AS usuario_sugerido,
               count(*) AS conexiones_en_comun
        ORDER BY conexiones_en_comun DESC, usuario_sugerido
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Sugerencias sociales para {username} por amigos de amigos",
        consulta,
        {"username": username, "limite": limite}
    )


def recomendar_visitados_por_amigos(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)-[v:VISITO]->(r:Restaurante)
        WHERE NOT (yo)-[:VISITO]->(r)
        RETURN r.restaurante_id AS restaurante_id,
               r.nombre AS restaurante,
               r.tipo_comida AS tipo_comida,
               r.barrio AS barrio,
               count(DISTINCT amigo) AS amigos_que_fueron,
               count(v) AS visitas_de_amigos,
               collect(DISTINCT amigo.username)[0..4] AS amigos
        ORDER BY amigos_que_fueron DESC, visitas_de_amigos DESC, restaurante
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Recomendacion colaborativa: restaurantes visitados por amigos de {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def recomendar_bien_calificados_por_amigos(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)-[c:CALIFICO]->(r:Restaurante)
        WHERE c.puntaje >= 4
          AND NOT (yo)-[:VISITO]->(r)
        RETURN r.restaurante_id AS restaurante_id,
               r.nombre AS restaurante,
               r.tipo_comida AS tipo_comida,
               r.barrio AS barrio,
               round(avg(c.puntaje) * 100) / 100 AS puntaje_promedio_amigos,
               count(c) AS calificaciones_altas,
               collect(DISTINCT amigo.username)[0..4] AS amigos
        ORDER BY puntaje_promedio_amigos DESC, calificaciones_altas DESC, restaurante
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Recomendacion colaborativa: restaurantes bien calificados por amigos de {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def recomendar_por_usuarios_similares(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:VISITO|CALIFICO]->(r:Restaurante)<-[:VISITO|CALIFICO]-(similar:Usuario)
        WHERE similar <> yo
        WITH yo, similar, count(DISTINCT r) AS gustos_en_comun
        ORDER BY gustos_en_comun DESC
        LIMIT 10
        MATCH (similar)-[rel:VISITO|CALIFICO]->(rec:Restaurante)
        WHERE NOT (yo)-[:VISITO]->(rec)
          AND NOT (yo)-[:CALIFICO]->(rec)
          AND (type(rel) = 'VISITO' OR rel.puntaje >= 4)
        OPTIONAL MATCH (similar)-[cal:CALIFICO]->(rec)
        WITH rec,
             sum(gustos_en_comun) AS score_colaborativo,
             count(DISTINCT similar) AS usuarios_similares,
             avg(cal.puntaje) AS puntaje_promedio_similares
        RETURN rec.restaurante_id AS restaurante_id,
               rec.nombre AS restaurante,
               rec.tipo_comida AS tipo_comida,
               rec.barrio AS barrio,
               score_colaborativo,
               usuarios_similares,
               round(coalesce(puntaje_promedio_similares, 0.0) * 100) / 100 AS puntaje_promedio_similares
        ORDER BY score_colaborativo DESC, usuarios_similares DESC, puntaje_promedio_similares DESC
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Filtrado colaborativo: restaurantes sugeridos por usuarios similares a {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def recomendar_por_contenido(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[c:CALIFICO]->(gustado:Restaurante)
        WHERE c.puntaje >= 4
        MATCH (rec:Restaurante)
        WHERE rec <> gustado
          AND NOT (yo)-[:VISITO]->(rec)
          AND NOT (yo)-[:CALIFICO]->(rec)
          AND (rec.tipo_comida = gustado.tipo_comida OR rec.barrio = gustado.barrio)
        WITH rec,
             count(DISTINCT gustado) AS coincidencias,
             sum(CASE WHEN rec.tipo_comida = gustado.tipo_comida THEN 1 ELSE 0 END) AS coincidencias_tipo,
             sum(CASE WHEN rec.barrio = gustado.barrio THEN 1 ELSE 0 END) AS coincidencias_barrio,
             collect(DISTINCT gustado.nombre)[0..4] AS basado_en
        RETURN rec.restaurante_id AS restaurante_id,
               rec.nombre AS restaurante,
               rec.tipo_comida AS tipo_comida,
               rec.barrio AS barrio,
               rec.calificacion_promedio AS calificacion_promedio,
               coincidencias,
               coincidencias_tipo,
               coincidencias_barrio,
               basado_en
        ORDER BY calificacion_promedio DESC, coincidencias DESC, restaurante
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Recomendacion basada en contenido para {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def explicar_camino_de_recomendacion(username, limite=5):
    consulta = """
        MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)-[c:CALIFICO]->(r:Restaurante)
        WHERE c.puntaje >= 4
          AND NOT (yo)-[:VISITO]->(r)
        RETURN yo.username AS usuario,
               amigo.username AS recomendado_por,
               r.nombre AS restaurante,
               c.puntaje AS puntaje,
               'Usuario -> SIGUE -> Amigo -> CALIFICO -> Restaurante' AS camino
        ORDER BY c.puntaje DESC, restaurante
        LIMIT $limite
    """

    return ejecutar_consulta(
        f"Caminos que explican recomendaciones para {username}",
        consulta,
        {"username": username, "limite": limite}
    )


def ejecutar_consultas(username=USERNAME_DEMO):
    """
    Ejecuta consultas de red social y recomendaciones.
    """
    print("\n==============================")
    print("EJECUCION DE CONSULTAS NEO4J")
    print("==============================")

    consultar_perfil_usuario(username)
    consultar_usuarios_que_sigue(username)
    consultar_seguidores(username)
    
    # Nuevas funciones de busqueda e interacciones
    buscar_usuarios("val", 5)
    consultar_visitas_amigos(username)
    consultar_calificaciones_amigos(username)

    sugerir_usuarios_para_seguir(username)
    recomendar_visitados_por_amigos(username)
    recomendar_bien_calificados_por_amigos(username)
    recomendar_por_usuarios_similares(username)
    recomendar_por_contenido(username)
    explicar_camino_de_recomendacion(username)


def consultar_detalle_perfil_usuario(username):
    """
    Consulta ampliada para el frontend.
    Devuelve el perfil con listas reales de usuarios/restaurantes para poder dibujar grafo.
    """
    consulta = """
        MATCH (u:Usuario {username: $username})
        CALL {
          WITH u
          OPTIONAL MATCH (u)-[:SIGUE]->(s:Usuario)
          RETURN count(s) AS siguiendo,
                 collect(DISTINCT {
                   username: s.username,
                   nombre: trim(coalesce(s.nombre,'') + ' ' + coalesce(s.apellido,''))
                 })[0..15] AS siguiendo_usuarios
        }
        CALL {
          WITH u
          OPTIONAL MATCH (f:Usuario)-[:SIGUE]->(u)
          RETURN count(f) AS seguidores,
                 collect(DISTINCT {
                   username: f.username,
                   nombre: trim(coalesce(f.nombre,'') + ' ' + coalesce(f.apellido,''))
                 })[0..15] AS seguidores_usuarios
        }
        CALL {
          WITH u
          OPTIONAL MATCH (u)-[v:VISITO]->(r:Restaurante)
          RETURN count(v) AS visitas,
                 collect(DISTINCT {
                   restaurante: r.nombre,
                   barrio: r.barrio,
                   tipo_comida: r.tipo_comida,
                   fecha: toString(v.fecha)
                 })[0..15] AS visitas_restaurantes
        }
        CALL {
          WITH u
          OPTIONAL MATCH (u)-[c:CALIFICO]->(r:Restaurante)
          RETURN count(c) AS resenas,
                 collect(DISTINCT {
                   restaurante: r.nombre,
                   puntaje: c.puntaje,
                   comentario: c.comentario,
                   fecha: toString(c.fecha)
                 })[0..15] AS resenas_restaurantes
        }
        RETURN u.username AS username,
               trim(coalesce(u.nombre,'') + ' ' + coalesce(u.apellido,'')) AS nombre,
               siguiendo, seguidores, visitas, resenas,
               siguiendo_usuarios, seguidores_usuarios,
               visitas_restaurantes, resenas_restaurantes
    """

    return ejecutar_consulta(
        f"Perfil social ampliado de {username}",
        consulta,
        {"username": username}
    )
