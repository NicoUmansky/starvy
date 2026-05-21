# pip install pandas pymongo

from pymongo import MongoClient
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Redis'))
from app import crear_sesion

mongo_uri = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"

df_usuarios = pd.read_json("./DATASET/usuarios.json")
usuarios = df_usuarios.to_dict(orient="records")

df_restaurantes = pd.read_json("./DATASET/restaurantes.json")
df_platos = pd.read_json("./DATASET/platos.json")
df_resenas = pd.read_json("./DATASET/resenas.json")

restaurantes = df_restaurantes.to_dict(orient="records")
platos = df_platos.to_dict(orient="records")
resenas = df_resenas.to_dict(orient="records")

for restaurante in restaurantes:
    restaurante["platos"] = [
        plato for plato in platos
        if plato["restaurante_id"] == restaurante["restaurante_id"]
    ]

with MongoClient(mongo_uri) as client:
    db = client["starvy"]
    usuarios_collection = db["usuarios"]
    restaurantes_collection = db["restaurantes"]
    resenas_collection = db["resenas"]

    #usuarios_collection.insert_many(usuarios)
    restaurantes_collection.insert_many(restaurantes)
    resenas_collection.insert_many(resenas)
    print("Datos insertados correctamente en MongoDB.")


    def registrarUsuario(dni,nombre,apellido,username,password,mail):
        usuarios_collection.insert_one({
            "dni_usuario": dni,
            "nombre": nombre,
            "apellido": apellido,
            "username": username,
            "password": password,
            "mail": mail
        })
        print("Usuario registrado correctamente.")


    def loginUsuario(username, password):         #una vez que el usuario se loguea, se crea una sesion para ese usuario (si el login es exitoso)
        usuario = usuarios_collection.find_one({  #esto se hace en redis, pero desde el modulo de mongo, porque es el que tiene la info de los usuarios. Si el login es exitoso, se crea una sesion para ese usuario en redis.
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


    def registrarRestaurante(restaurante_id,nombre,tipo_comida,barrio,direccion): 
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


    def registrarResena(resena_id,dni_usuario,restaurante_id,puntaje,comentario,fecha):
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
