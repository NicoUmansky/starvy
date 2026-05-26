from pymongo.errors import ServerSelectionTimeoutError

from carga_dataset import cargar_dataset, limpiar_colecciones
from conexion import cerrar_conexion, probar_conexion
from consultas import (
    buscar_restaurantes_por_filtros,
    ejecutar_consultas,
    validar_credenciales,
    ver_mis_calificaciones,
    ver_mis_resenas
)
from esquema import crear_indices, verificar_esquema
from escrituras import (
    ejecutar_escrituras,
    insertar_calificacion,
    insertar_resena,
    login_usuario,
    recalcular_calificacion_promedio,
    registrar_restaurante,
    registrar_usuario
)


def main():
    """
    Orquesta la demo completa de MongoDB: conexion, carga, consultas y escrituras.
    """
    print("Conectando Python con MongoDB...")

    probar_conexion()
    limpiar_colecciones()
    crear_indices()
    cargar_dataset()
    verificar_esquema()

    validar_credenciales("VitoNava", "starvy123")
    buscar_restaurantes_por_filtros(tipo_comida="Mexicana", calificacion_minima=3, barrio="Flores")
    ejecutar_consultas(dni_usuario=44000009, restaurante_id=1)
    ejecutar_escrituras()

    print("\nInicializacion, carga, consultas y escrituras de MongoDB finalizadas correctamente.")


if __name__ == "__main__":
    try:
        main()
    except ServerSelectionTimeoutError:
        print("\nNo se pudo conectar con MongoDB.")
        print("Verifica MONGO_URI, la conexion a internet y el acceso permitido en MongoDB Atlas.")
    finally:
        cerrar_conexion()
