from pymongo import ASCENDING

from conexion import obtener_coleccion


def crear_indices():
    """
    Crea indices para evitar duplicados y acelerar las consultas principales.
    """
    usuarios = obtener_coleccion("usuarios")
    restaurantes = obtener_coleccion("restaurantes")
    resenas = obtener_coleccion("resenas")

    usuarios.create_index([("dni_usuario", ASCENDING)], unique=True)
    usuarios.create_index([("username", ASCENDING)], unique=True)
    usuarios.create_index([("mail", ASCENDING)], unique=True)

    restaurantes.create_index([("restaurante_id", ASCENDING)], unique=True)
    restaurantes.create_index([("tipo_comida", ASCENDING)])
    restaurantes.create_index([("barrio", ASCENDING)])
    restaurantes.create_index([("calificacion_promedio", ASCENDING)])

    resenas.create_index([("resena_id", ASCENDING)], unique=True)
    resenas.create_index([("dni_usuario", ASCENDING)])
    resenas.create_index([("restaurante_id", ASCENDING)])
    resenas.create_index([("dni_usuario", ASCENDING), ("fecha", ASCENDING)])
    resenas.create_index([("restaurante_id", ASCENDING), ("fecha", ASCENDING)])

    print("Indices de MongoDB creados/verificados correctamente.")


def verificar_esquema():
    """
    Muestra cantidad de documentos e indices creados en cada coleccion.
    """
    print("\nColecciones MongoDB:")

    for nombre in ("usuarios", "restaurantes", "resenas"):
        coleccion = obtener_coleccion(nombre)
        indices = ", ".join(coleccion.index_information().keys())
        print(f"- {nombre}: {coleccion.count_documents({})} documentos | indices: {indices}")
