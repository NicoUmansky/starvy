import json

from config import DATASET_DIR
from conexion import obtener_coleccion
from mongoDB.escrituras import recalcular_calificacion_promedio


def _leer_json(nombre_archivo):
    """
    Lee un archivo JSON del dataset y lo devuelve como lista de diccionarios.
    """
    ruta = DATASET_DIR / nombre_archivo

    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def limpiar_colecciones():
    """
    Borra usuarios, restaurantes y resenas para evitar duplicados en la demo.
    """
    for nombre in ("usuarios", "restaurantes", "resenas"):
        obtener_coleccion(nombre).delete_many({})

    print("Colecciones de MongoDB limpiadas correctamente.")


def cargar_dataset():
    """
    Carga usuarios, restaurantes y resenas; anida los platos dentro de cada restaurante.
    """
    usuarios = _leer_json("usuarios.json")
    restaurantes = _leer_json("restaurantes.json")
    platos = _leer_json("platos.json")
    resenas = _leer_json("resenas.json")

    for restaurante in restaurantes:
        restaurante["platos"] = [
            plato for plato in platos
            if plato["restaurante_id"] == restaurante["restaurante_id"]
        ]

    usuarios_col = obtener_coleccion("usuarios")
    restaurantes_col = obtener_coleccion("restaurantes")
    resenas_col = obtener_coleccion("resenas")


    # Usamos replace_one con upsert para evitar duplicados si se corre varias veces el script. Tambien recalculamos el promedio de cada restaurante despues de cargar las resenas.
    for usuario in usuarios:
        usuarios_col.replace_one(
            {"dni_usuario": usuario["dni_usuario"]},
            usuario,
            upsert=True
        )

    for restaurante in restaurantes:
        restaurantes_col.replace_one(
            {"restaurante_id": restaurante["restaurante_id"]},
            restaurante,
            upsert=True
        )

    for resena in resenas:
        resenas_col.replace_one(
            {"resena_id": resena["resena_id"]},
            resena,
            upsert=True
        )

    for restaurante in restaurantes:
        recalcular_calificacion_promedio(restaurante["restaurante_id"])

    print("Dataset cargado correctamente en MongoDB.")
