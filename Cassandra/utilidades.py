from cassandra.util import Time
from datetime import datetime, timedelta
from config import DATASET_DIR
import json


def leer_json(nombre_archivo):
    """
    Lee un archivo JSON desde la carpeta DATASET.
    """
    ruta = DATASET_DIR / nombre_archivo

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def convertir_fecha(fecha_texto):
    """
    Convierte una fecha en texto al tipo date que espera Cassandra.
    Formato esperado: YYYY-MM-DD.
    """
    return datetime.strptime(fecha_texto, "%Y-%m-%d").date()


def convertir_hora(hora_texto):
    """
    Convierte una hora del dataset al tipo time de Cassandra.
    El dataset puede traer horas como HH:MM, por eso agregamos segundos.
    """
    if len(hora_texto.split(":")) == 2:
        hora_texto = hora_texto + ":00"

    return Time(hora_texto)


def rango_fechas(fecha_inicio, fecha_fin):
    """
    Genera todos los días entre fecha_inicio y fecha_fin.
    Sirve para cargar promociones activas por cada día de vigencia.
    """
    dia_actual = fecha_inicio

    while dia_actual <= fecha_fin:
        yield dia_actual
        dia_actual = dia_actual + timedelta(days=1)