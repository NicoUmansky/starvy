import json

from config import DATASET_DIR


def leer_json(nombre_archivo):
    """
    Lee archivos JSON desde la carpeta DATASET.
    """
    ruta = DATASET_DIR / nombre_archivo

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def normalizar_hora(hora_texto):
    """
    Neo4j espera HH:MM:SS para localtime.
    El dataset trae HH:MM, por eso agregamos segundos cuando hace falta.
    """
    if len(hora_texto.split(":")) == 2:
        return hora_texto + ":00"

    return hora_texto
