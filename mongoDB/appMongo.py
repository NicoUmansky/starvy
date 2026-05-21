import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Redis'))
from appRedis import crear_sesion

from mongo_client import usuarios_collection, restaurantes_collection, resenas_collection


def registrarUsuario(dni, nombre, apellido, username, password, mail):
    usuarios_collection.insert_one({
        "dni_usuario": dni,
        "nombre": nombre,
        "apellido": apellido,
        "username": username,
        "password": password,
        "mail": mail
    })
    print("Usuario registrado correctamente.")


def loginUsuario(username, password):
    usuario = usuarios_collection.find_one({
        "username": username,
        "password": password
    })
    if usuario:
        user_id = str(usuario["_id"])
        crear_sesion(user_id)
        return user_id
    return None


def recalcularCalificacionPromedio(restaurante_id):
    resenas_restaurante = list(resenas_collection.find(
        {"restaurante_id": restaurante_id},
        {"_id": 0, "puntaje": 1}
    ))

    if len(resenas_restaurante) == 0:
        promedio = 0
    else:
        total_puntajes = sum(resena["puntaje"] for resena in resenas_restaurante)
        promedio = round(total_puntajes / len(resenas_restaurante), 1)

    restaurantes_collection.update_one(
        {"restaurante_id": restaurante_id},
        {"$set": {"calificacion_promedio": promedio}}
    )

    return promedio


def registrarRestaurante(restaurante_id, nombre, tipo_comida, barrio, direccion):
    restaurantes_collection.insert_one({
        "restaurante_id": restaurante_id,
        "nombre": nombre,
        "tipo_comida": tipo_comida,
        "barrio": barrio,
        "direccion": direccion,
        "calificacion_promedio": 0,
        "platos": []
    })
    print("Restaurante registrado correctamente.")


def registrarResena(resena_id, dni_usuario, restaurante_id, puntaje, comentario, fecha):
    resenas_collection.insert_one({
        "resena_id": resena_id,
        "dni_usuario": dni_usuario,
        "restaurante_id": restaurante_id,
        "puntaje": puntaje,
        "comentario": comentario,
        "fecha": fecha
    })

    promedio = recalcularCalificacionPromedio(restaurante_id)
    print(f"Resena registrada correctamente. Nueva calificacion promedio: {promedio}")
