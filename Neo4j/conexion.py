from neo4j import GraphDatabase

from config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER


def obtener_driver():
    """
    Crea el driver oficial de Neo4j.
    El driver mantiene el pool de conexiones hacia el motor.
    """
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )


def obtener_session(driver):
    """
    Crea una sesion. Si NEO4J_DATABASE esta vacio usa la base por defecto.
    """
    if NEO4J_DATABASE:
        return driver.session(database=NEO4J_DATABASE)

    return driver.session()


def probar_conexion():
    """
    Verifica que Python pueda conectarse con Neo4j.
    """
    driver = obtener_driver()

    with obtener_session(driver) as session:
        resultado = session.run("""
            RETURN 'Conexion exitosa con Neo4j' AS mensaje
        """)
        print(resultado.single()["mensaje"])

    driver.close()
