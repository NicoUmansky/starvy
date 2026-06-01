"""Sincroniza resenas de MongoDB hacia Neo4j usando resena_id como referencia.

Usar: python frontend/neo4j_sync.py
"""
import time

from neo4j import GraphDatabase
from pymongo import MongoClient


# Config (coincide con frontend/app.py)
MONGO_URI = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"
MONGO_DB = "starvy"
NEO4J_URI = "neo4j+s://b7da37c0.databases.neo4j.io"
NEO4J_USER = "b7da37c0"
NEO4J_PASSWORD = "UNbTrBV5hF57i8MaXJSB7Q34hhZAuPqUJTycZtbK-KM"
NEO4J_DB = "b7da37c0"


def get_mongo():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=6000)
    return client[MONGO_DB]


def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def normalizar_fecha(fecha):
    if hasattr(fecha, "date"):
        return fecha.date().isoformat()
    return str(fecha)


def obtener_resenas_mongo(db):
    return list(db.resenas.find({}, {
        "_id": 0,
        "resena_id": 1,
        "dni_usuario": 1,
        "restaurante_id": 1,
        "puntaje": 1,
        "comentario": 1,
        "fecha": 1,
    }).sort("resena_id", 1))


def obtener_resenas_neo4j(driver):
    consulta = """
        MATCH (u:Usuario)-[c:CALIFICO]->(r:Restaurante)
        WHERE c.resena_id IS NOT NULL
        RETURN toInteger(c.resena_id) AS resena_id,
               u.dni_usuario AS dni_usuario,
               r.restaurante_id AS restaurante_id,
               c.puntaje AS puntaje,
               c.comentario AS comentario,
               toString(c.fecha) AS fecha
        ORDER BY resena_id
    """

    with driver.session(database=NEO4J_DB) as session:
        return [dict(row) for row in session.run(consulta)]


def comparar_resenas(mongo_resenas, neo_resenas):
    mongo_por_id = {int(r["resena_id"]): r for r in mongo_resenas}
    neo_por_id = {int(r["resena_id"]): r for r in neo_resenas}

    mongo_ids = set(mongo_por_id)
    neo_ids = set(neo_por_id)

    faltan_en_neo = sorted(mongo_ids - neo_ids)
    sobran_en_neo = sorted(neo_ids - mongo_ids)
    distintas = []

    for resena_id in sorted(mongo_ids & neo_ids):
        mongo = mongo_por_id[resena_id]
        neo = neo_por_id[resena_id]

        campos = {
            "dni_usuario": int(mongo["dni_usuario"]),
            "restaurante_id": int(mongo["restaurante_id"]),
            "puntaje": int(mongo["puntaje"]),
            "comentario": mongo.get("comentario", ""),
            "fecha": normalizar_fecha(mongo.get("fecha")),
        }

        if any(str(campos[campo]) != str(neo.get(campo)) for campo in campos):
            distintas.append(resena_id)

    return mongo_por_id, neo_por_id, faltan_en_neo, sobran_en_neo, distintas


def sync_one(session, resena):
    cypher = """
        OPTIONAL MATCH ()-[vieja:CALIFICO {resena_id: $id}]->()
        DELETE vieja
        WITH 1 AS _
        MERGE (u:Usuario {dni_usuario: $dni})
        MERGE (r:Restaurante {restaurante_id: $rid})
        CREATE (u)-[c:CALIFICO {resena_id: $id}]->(r)
        SET c.puntaje = $puntaje,
            c.comentario = $comentario,
            c.fecha = date($fecha)
    """
    try:
        session.run(cypher, {
            "dni": int(resena["dni_usuario"]),
            "rid": int(resena["restaurante_id"]),
            "id": int(resena["resena_id"]),
            "puntaje": int(resena["puntaje"]),
            "comentario": resena.get("comentario", ""),
            "fecha": normalizar_fecha(resena.get("fecha")),
        })
        return True, None
    except Exception as error:
        return False, str(error)


def main():
    db = get_mongo()
    driver = get_neo4j_driver()

    try:
        mongo_resenas = obtener_resenas_mongo(db)
        neo_resenas = obtener_resenas_neo4j(driver)
    finally:
        driver.close()

    mongo_por_id, _, faltan_en_neo, sobran_en_neo, distintas = comparar_resenas(
        mongo_resenas,
        neo_resenas
    )

    print(f"MongoDB resenas: {len(mongo_resenas)}")
    print(f"Neo4j CALIFICO con resena_id: {len(neo_resenas)}")
    print(f"Faltan en Neo4j: {len(faltan_en_neo)} -> {faltan_en_neo}")
    print(f"Sobran en Neo4j: {len(sobran_en_neo)} -> {sobran_en_neo}")
    print(f"Distintas entre Mongo y Neo4j: {len(distintas)} -> {distintas}")

    pending_ids = sorted(set(faltan_en_neo) | set(distintas))
    pending = [mongo_por_id[resena_id] for resena_id in pending_ids]

    if not pending:
        print("No hay resenas pendientes de sincronizacion.")
        return

    print(f"Sincronizando {len(pending)} resenas usando MongoDB como fuente de verdad...")
    synced = 0

    driver = get_neo4j_driver()
    try:
        with driver.session(database=NEO4J_DB) as session:
            for resena in pending:
                for attempt in range(3):
                    ok, err = sync_one(session, resena)
                    if ok:
                        db.resenas.update_one(
                            {"resena_id": resena["resena_id"]},
                            {"$set": {"synced_neo4j": True}, "$unset": {"sync_error": ""}}
                        )
                        synced += 1
                        break

                    print(f"Intento {attempt + 1} fallo para resena {resena['resena_id']}: {err}")
                    time.sleep(1)
                else:
                    db.resenas.update_one(
                        {"resena_id": resena["resena_id"]},
                        {"$set": {"sync_error": err}}
                    )
    finally:
        driver.close()

    print(f"Sincronizacion finalizada. Sincronizadas: {synced}/{len(pending)}.")


if __name__ == "__main__":
    main()
