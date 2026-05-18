# pip install pandas pymongo

from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"

df = pd.read_json("./DATASET/usuarios.json")
records = df.to_dict(orient="records")
print(records)

with MongoClient(mongo_uri) as client:
    db = client["starvy"]
    collection = db["usuarios"]
    # collection.insert_many(records)
    # print("Datos insertados correctamente en MongoDB.")


    def registrarUsuario(dni,nombre,apellido,username,password,mail):
        collection.insert_one({
            "dni_usuario": dni,
            "nombre": nombre,
            "apellido": apellido,
            "username": username,
            "password": password,
            "mail": mail
        })
        print("Usuario registrado correctamente.")
                    