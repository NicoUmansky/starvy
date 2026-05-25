import argparse

try:
    from neo4j.exceptions import AuthError, ServiceUnavailable

    from carga_dataset import cargar_dataset, limpiar_grafo
    from conexion import probar_conexion
    from esquema import crear_constraints_e_indices, verificar_esquema
except ModuleNotFoundError as error:
    if error.name == "neo4j":
        print("Falta instalar la libreria oficial de Neo4j.")
        print("Ejecuta: pip install -r requirements.txt")
        raise SystemExit(1)

    raise


def inicializar_grafo():
    """
    Recorre el flujo destructivo de bootstrap para reconstruir el grafo desde cero.
    """
    crear_constraints_e_indices()
    limpiar_grafo()
    cargar_dataset()
    verificar_esquema()
    print("\nInicializacion y carga de Neo4j finalizadas correctamente.")


def main(bootstrap=False):
    print("Conectando Python con Neo4j...")

    probar_conexion()
    crear_constraints_e_indices()

    if bootstrap:
        inicializar_grafo()
        return

    verificar_esquema()
    print("\nNeo4j quedo listo. Para reconstruir la base desde cero, ejecuta inicializar_grafo() manualmente.")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Inicializacion y verificacion de Neo4j para STARVY")
        parser.add_argument(
            "--bootstrap",
            action="store_true",
            help="Borra el grafo y vuelve a cargar todo el dataset",
        )
        args = parser.parse_args()

        main(bootstrap=args.bootstrap)
    except RuntimeError as error:
        print(f"\n{error}")
    except AuthError:
        print("\nNo se pudo autenticar con Neo4j Aura.")
        print("Verifica que NEO4J_USERNAME y NEO4J_PASSWORD sean los de la instancia StarvyNeo.")
    except ServiceUnavailable:
        print("\nNo se pudo conectar con Neo4j.")
        print("Verifica que la instancia Aura este activa y que NEO4J_URI, NEO4J_USERNAME y NEO4J_PASSWORD sean correctos.")
