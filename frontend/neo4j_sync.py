"""Script simple para reconciliar reseñas en Mongo que no pudieron sincronizarse con Neo4j.
Usar: python frontend/neo4j_sync.py
"""
from pymongo import MongoClient
from neo4j import GraphDatabase
import time

# Config (coincide con frontend/app.py)
MONGO_URI      = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"
MONGO_DB       = "starvy"
NEO4J_URI      = "neo4j+s://b7da37c0.databases.neo4j.io"
NEO4J_USER     = "b7da37c0"
NEO4J_PASSWORD = "UNbTrBV5hF57i8MaXJSB7Q34hhZAuPqUJTycZtbK-KM"
NEO4J_DB       = "b7da37c0"


def get_mongo():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=6000)
    return client[MONGO_DB]


def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def sync_one(resena):
    cypher = """
MERGE (u:Usuario {dni_usuario: $dni})
MERGE (r:Restaurante {restaurante_id: $rid})
MERGE (u)-[c:CALIFICO {resena_id: $id}]->(r)
SET c.puntaje = $puntaje, c.comentario = $comentario, c.fecha = date($fecha)
"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=NEO4J_DB) as s:
            s.run(cypher, {
                "dni": int(resena["dni_usuario"]),
                "rid": int(resena["restaurante_id"]),
                "id": int(resena["resena_id"]),
                "puntaje": int(resena["puntaje"]),
                "comentario": resena.get("comentario", ""),
                "fecha": resena.get("fecha"),
            })
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        driver.close()


def main():
    db = get_mongo()
    pending = list(db.resenas.find({"synced_neo4j": False}))
    total = len(pending)
    if total == 0:
        print("No hay reseñas pendientes de sincronización.")
        return

    print(f"Encontradas {total} reseñas pendientes. Intentando sincronizar...")
    synced = 0
    for r in pending:
        for attempt in range(3):
            ok, err = sync_one(r)
            if ok:
                db.resenas.update_one({"resena_id": r["resena_id"]}, {"$set": {"synced_neo4j": True}, "$unset": {"sync_error": ""}})
                synced += 1
                break
            else:
                print(f"Intento {attempt+1} falló para resena {r['resena_id']}: {err}")
                time.sleep(1)
        else:
            db.resenas.update_one({"resena_id": r["resena_id"]}, {"$set": {"sync_error": err}})

    print(f"Sincronización finalizada. Sincronizadas: {synced}/{total}.")


if __name__ == "__main__":
    main()
