from esquema import crear_keyspace, crear_tablas, verificar_tablas
from carga_dataset import limpiar_tablas, cargar_dataset
from consultas import ejecutar_consultas
from escrituras import ejecutar_escrituras


def main():
    print("Conectando Python con Cassandra...")

    crear_keyspace()
    crear_tablas()
    verificar_tablas()

    limpiar_tablas()
    cargar_dataset()

    ejecutar_consultas()
    ejecutar_escrituras()

    print("\nInicialización, carga, consultas y escrituras de Cassandra finalizadas correctamente.")


if __name__ == "__main__":
    main()