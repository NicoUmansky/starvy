try:
    from neo4j.exceptions import AuthError, ServiceUnavailable

    from carga_dataset import cargar_dataset, limpiar_grafo
    from conexion import probar_conexion
    from consultas import ejecutar_consultas
    from esquema import crear_constraints_e_indices, verificar_esquema
    from escrituras import ejecutar_escrituras
except ModuleNotFoundError as error:
    if error.name == "neo4j":
        print("Falta instalar la libreria oficial de Neo4j.")
        print("Ejecuta: pip install -r requirements.txt")
        raise SystemExit(1)

    raise


def main():
    print("Conectando Python con Neo4j...")

    probar_conexion()
    crear_constraints_e_indices()
    limpiar_grafo()
    cargar_dataset()
    verificar_esquema()

    ejecutar_consultas("VitoNava")
    ejecutar_escrituras("VitoNava")

    print("\nInicializacion, carga, consultas y escrituras de Neo4j finalizadas correctamente.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"\n{error}")
    except AuthError:
        print("\nNo se pudo autenticar con Neo4j Aura.")
        print("Verifica que NEO4J_USERNAME y NEO4J_PASSWORD sean los de la instancia StarvyNeo.")
    except ServiceUnavailable:
        print("\nNo se pudo conectar con Neo4j.")
        print("Verifica que la instancia Aura este activa y que NEO4J_URI, NEO4J_USERNAME y NEO4J_PASSWORD sean correctos.")
