from pymongo import MongoClient

mongo_uri = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"
client = MongoClient(mongo_uri)
db = client["starvy"]

usuarios_collection = db["usuarios"]
restaurantes_collection = db["restaurantes"]
resenas_collection = db["resenas"]
