from conexion import obtener_driver, obtener_session


def crear_constraints_e_indices():
    """
    Crea restricciones e indices para el grafo de Starvy.

    En defensa: las constraints garantizan identidad unica de nodos y los
    indices ayudan en busquedas frecuentes para recomendaciones por contenido.
    """
    consultas = [
        """
        CREATE CONSTRAINT usuario_dni_unico IF NOT EXISTS
        FOR (u:Usuario)
        REQUIRE u.dni_usuario IS UNIQUE
        """,
        """
        CREATE CONSTRAINT usuario_username_unico IF NOT EXISTS
        FOR (u:Usuario)
        REQUIRE u.username IS UNIQUE
        """,
        """
        CREATE CONSTRAINT restaurante_id_unico IF NOT EXISTS
        FOR (r:Restaurante)
        REQUIRE r.restaurante_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT plato_id_unico IF NOT EXISTS
        FOR (p:Plato)
        REQUIRE p.plato_id IS UNIQUE
        """,
        """
        CREATE INDEX restaurante_tipo_comida_idx IF NOT EXISTS
        FOR (r:Restaurante)
        ON (r.tipo_comida)
        """,
        """
        CREATE INDEX restaurante_barrio_idx IF NOT EXISTS
        FOR (r:Restaurante)
        ON (r.barrio)
        """
    ]

    driver = obtener_driver()

    with obtener_session(driver) as session:
        for consulta in consultas:
            session.run(consulta)

    driver.close()
    print("Constraints e indices de Neo4j creados o ya existentes.")


def verificar_esquema():
    """
    Muestra constraints e indices como evidencia de configuracion del motor.
    """
    driver = obtener_driver()

    with obtener_session(driver) as session:
        constraints = session.run("""
            SHOW CONSTRAINTS
            YIELD name, type
            RETURN name, type
            ORDER BY name
        """)

        print("\nConstraints en Neo4j:")
        for fila in constraints:
            print(f"- {fila['name']} | {fila['type']}")

        indices = session.run("""
            SHOW INDEXES
            YIELD name, type, entityType
            RETURN name, type, entityType
            ORDER BY name
        """)

        print("\nIndices en Neo4j:")
        for fila in indices:
            print(f"- {fila['name']} | {fila['type']} | {fila['entityType']}")

    driver.close()
