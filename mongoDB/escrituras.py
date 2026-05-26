import importlib.util
import sys
from pathlib import Path

from pymongo.errors import DuplicateKeyError

from conexion import obtener_coleccion
from consultas import (
    validar_credenciales,
    ver_calificacion_restaurante,
    ver_mis_calificaciones,
    ver_mis_resenas
)
from utilidades import fecha_hoy_texto, obtener_siguiente_id, validar_puntaje


def crear_sesion_si_redis_esta_disponible(user_id):
    """
    Intenta crear sesion en Redis despues del login, sin cortar Mongo si Redis falla.
    """
    redis_dir = Path(__file__).resolve().parent.parent / "Redis"
    redis_consultas = redis_dir / "consultas.py"

    if not redis_consultas.exists():
        print("No se creo sesion Redis porque no se encontro Redis/consultas.py.")
        return None

    try:
        if str(redis_dir) not in sys.path:
            sys.path.insert(0, str(redis_dir))

        spec = importlib.util.spec_from_file_location("redis_consultas", redis_consultas)
        redis_modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(redis_modulo)

        return redis_modulo.crear_sesion(user_id)
    except Exception as error:
        print(f"No se pudo crear sesion en Redis: {error}")
        return None


def registrar_usuario(mail, password, username, dni_usuario, nombre, apellido):
    """
    Signup MongoDB: usa insert_one para registrar mail, password y username.
    Tambien guarda dni, nombre y apellido para mantener la estructura del dataset.
    """
    usuarios = obtener_coleccion("usuarios")
    usuario = {
        "dni_usuario": int(dni_usuario),
        "nombre": nombre,
        "apellido": apellido,
        "username": username,
        "password": password,
        "mail": mail
    }

    try:
        usuarios.insert_one(usuario)
    except DuplicateKeyError:
        print(f"\nNo se pudo registrar {username}: mail, username o DNI ya existente.")
        return None

    print(f"\nUsuario registrado correctamente: {username}")
    return usuario


def login_usuario(username, password):
    """
    Valida credenciales con MongoDB y, si son correctas, intenta crear sesion Redis.
    """
    usuario = validar_credenciales(username, password)

    if usuario is None:
        return None

    user_id = str(usuario["_id"])
    crear_sesion_si_redis_esta_disponible(user_id)
    return user_id


def recalcular_calificacion_promedio(restaurante_id):
    """
    Calcula el promedio de puntajes de resenas y actualiza el restaurante.
    """
    restaurante_id = int(restaurante_id)
    pipeline = [
        {"$match": {"restaurante_id": restaurante_id}},
        {"$group": {"_id": "$restaurante_id", "promedio": {"$avg": "$puntaje"}}}
    ]

    resultado = list(obtener_coleccion("resenas").aggregate(pipeline))
    promedio = round(resultado[0]["promedio"], 1) if resultado else 0

    obtener_coleccion("restaurantes").update_one(
        {"restaurante_id": restaurante_id},
        {"$set": {"calificacion_promedio": promedio}}
    )

    return promedio


def registrar_restaurante(restaurante_id, nombre, tipo_comida, barrio, direccion):
    """
    Inserta un restaurante nuevo con promedio inicial 0 y arreglo de platos vacio.
    """
    restaurante = {
        "restaurante_id": int(restaurante_id),
        "nombre": nombre,
        "tipo_comida": tipo_comida,
        "barrio": barrio,
        "direccion": direccion,
        "calificacion_promedio": 0,
        "platos": []
    }

    try:
        obtener_coleccion("restaurantes").insert_one(restaurante)
    except DuplicateKeyError:
        print(f"\nNo se pudo registrar el restaurante {restaurante_id}: id ya existente.")
        return None

    print(f"\nRestaurante registrado correctamente: {nombre}")
    return restaurante


def insertar_calificacion(dni_usuario, restaurante_id, puntaje, comentario="", fecha=None, resena_id=None):
    """
    Inserta una calificacion de 1 a 5 estrellas.
    Si comentario viene informado, tambien queda registrada la resena escrita.
    """
    usuarios = obtener_coleccion("usuarios")
    restaurantes = obtener_coleccion("restaurantes")
    resenas = obtener_coleccion("resenas")

    dni_usuario = int(dni_usuario)
    restaurante_id = int(restaurante_id)
    puntaje = validar_puntaje(puntaje)

    # Validamos que el usuario y restaurante existan antes de insertar
    if usuarios.find_one({"dni_usuario": dni_usuario}, {"_id": 1}) is None:
        print(f"\nNo existe el usuario con DNI {dni_usuario}.")
        return None

    if restaurantes.find_one({"restaurante_id": restaurante_id}, {"_id": 1}) is None:
        print(f"\nNo existe el restaurante {restaurante_id}.")
        return None

    resena = {
        "resena_id": int(resena_id) if resena_id else obtener_siguiente_id(resenas, "resena_id"),
        "dni_usuario": dni_usuario,
        "restaurante_id": restaurante_id,
        "puntaje": puntaje,
        "comentario": comentario,
        "fecha": fecha or fecha_hoy_texto()
    }

    try:
        resenas.insert_one(resena)
    except DuplicateKeyError:
        print(f"\nNo se pudo insertar la resena {resena['resena_id']}: id ya existente.")
        return None

    promedio = recalcular_calificacion_promedio(restaurante_id)
    
    print(
        f"\nCalificacion insertada correctamente. "
        f"Nuevo promedio del restaurante {restaurante_id}: {promedio}"
    )
    
    return resena


def insertar_resena(dni_usuario, restaurante_id, puntaje, comentario, fecha=None, resena_id=None):
    """
    Inserta una resena escrita sobre un restaurante con su puntaje de estrellas.
    """
    return insertar_calificacion(
        dni_usuario=dni_usuario,
        restaurante_id=restaurante_id,
        puntaje=puntaje,
        comentario=comentario,
        fecha=fecha,
        resena_id=resena_id
    )


def ejecutar_escrituras():
    """
    Ejecuta una demo de signup, login e insercion de resena/calificacion.
    """
    print("\n==============================")
    print("ESCRITURAS EN MONGODB")
    print("==============================")

    usuario = registrar_usuario(
        mail="demo.mongo@starvy.com",
        password="starvy123",
        username="DemoMongo",
        dni_usuario=44999999,
        nombre="Demo",
        apellido="Mongo"
    )

    login_usuario("DemoMongo", "starvy123")

    dni_usuario = usuario["dni_usuario"] if usuario else 44999999
    insertar_resena(
        dni_usuario=dni_usuario,
        restaurante_id=1,
        puntaje=5,
        comentario="Muy buena experiencia, volveria."
    )

    print("\nVerificacion despues de las escrituras:")
    ver_mis_resenas(dni_usuario)
    ver_mis_calificaciones(dni_usuario)
    ver_calificacion_restaurante(1)
