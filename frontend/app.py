"""
STARVY — Frontend Backend API
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MONGO_URI      = "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"
MONGO_DB       = "starvy"

NEO4J_URI      = "neo4j+s://b7da37c0.databases.neo4j.io"
NEO4J_USER     = "b7da37c0"
NEO4J_PASSWORD = "UNbTrBV5hF57i8MaXJSB7Q34hhZAuPqUJTycZtbK-KM"
NEO4J_DB       = "b7da37c0"

CASS_HOST      = "127.0.0.1"
CASS_PORT      = 9042
CASS_KEYSPACE  = "starvy"

REDIS_HOST     = "redis-10212.c14.us-east-1-2.ec2.cloud.redislabs.com"
REDIS_PORT     = 10212
REDIS_PASS     = "cRWgta2gV5bWacRM2zr5AfVUxUtP5LKE"

def get_mongo():
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=6000)
    return client[MONGO_DB]

def get_neo4j_session():
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver

def get_redis():
    import redis
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT,
                       password=REDIS_PASS, decode_responses=True,
                       socket_connect_timeout=5)

def get_cassandra():
    from cassandra.cluster import Cluster
    cluster = Cluster([CASS_HOST], port=CASS_PORT)
    session = cluster.connect(CASS_KEYSPACE)
    return cluster, session

def serializar(obj):
    import datetime
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return str(obj)

def limpiar_docs(docs):
    import json
    return json.loads(json.dumps(docs, default=serializar))

@app.route("/")
def index():
    return render_template("index.html")

# ── MONGODB ──────────────────────────────────────────────────

@app.route("/api/mongo/login", methods=["POST"])
def mongo_login():
    data     = request.json or {}
    username = data.get("username", "VitoNava")
    password = data.get("password", "starvy123")
    query = f'db.usuarios.findOne(\n  {{ username: "{username}", password: "***" }},\n  {{ password: 0 }}\n)'
    try:
        db  = get_mongo()
        doc = db.usuarios.find_one({"username": username, "password": password}, {"password": 0})
        if doc:
            doc["_id"] = str(doc["_id"])
        return jsonify({"query": query, "lenguaje": "javascript",
                        "resultado": [doc] if doc else [], "exito": doc is not None})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

@app.route("/api/mongo/mis-resenas")
def mongo_mis_resenas():
    dni   = int(request.args.get("dni", 44000009))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ dni_usuario: {dni} }} }},
  {{ $sort: {{ fecha: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from: "restaurantes", localField: "restaurante_id",
                 foreignField: "restaurante_id", as: "restaurante" }} }},
  {{ $unwind: "$restaurante" }},
  {{ $project: {{ _id:0, restaurante:"$restaurante.nombre",
                  puntaje:1, comentario:1, fecha:1 }} }}
])"""
    try:
        db = get_mongo()
        pipeline = [
            {"$match": {"dni_usuario": dni}},
            {"$sort": {"fecha": -1, "resena_id": -1}},
            {"$limit": limit},
            {"$lookup": {"from": "restaurantes", "localField": "restaurante_id",
                         "foreignField": "restaurante_id", "as": "restaurante"}},
            {"$unwind": "$restaurante"},
            {"$project": {"_id": 0, "resena_id": 1,
                          "restaurante": "$restaurante.nombre",
                          "puntaje": 1, "comentario": 1, "fecha": 1}}
        ]
        return jsonify({"query": query, "lenguaje": "javascript",
                        "resultado": limpiar_docs(list(db.resenas.aggregate(pipeline)))})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

@app.route("/api/mongo/mis-calificaciones")
def mongo_mis_calificaciones():
    dni   = int(request.args.get("dni", 44000009))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ dni_usuario: {dni} }} }},
  {{ $sort: {{ fecha: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from: "restaurantes", localField: "restaurante_id",
                 foreignField: "restaurante_id", as: "restaurante" }} }},
  {{ $unwind: "$restaurante" }},
  {{ $project: {{ _id:0, restaurante:"$restaurante.nombre", puntaje:1, fecha:1 }} }}
])"""
    try:
        db = get_mongo()
        pipeline = [
            {"$match": {"dni_usuario": dni}},
            {"$sort": {"fecha": -1}},
            {"$limit": limit},
            {"$lookup": {"from": "restaurantes", "localField": "restaurante_id",
                         "foreignField": "restaurante_id", "as": "restaurante"}},
            {"$unwind": "$restaurante"},
            {"$project": {"_id": 0, "resena_id": 1,
                          "restaurante": "$restaurante.nombre",
                          "puntaje": 1, "fecha": 1}}
        ]
        return jsonify({"query": query, "lenguaje": "javascript",
                        "resultado": limpiar_docs(list(db.resenas.aggregate(pipeline)))})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

@app.route("/api/mongo/buscar-restaurantes")
def mongo_buscar_restaurantes():
    tipo    = request.args.get("tipo", "")
    barrio  = request.args.get("barrio", "")
    min_cal = float(request.args.get("min_calificacion", 0))
    filtro = {}
    if tipo:    filtro["tipo_comida"] = {"$regex": tipo, "$options": "i"}
    if barrio:  filtro["barrio"]      = {"$regex": barrio, "$options": "i"}
    if min_cal > 0: filtro["calificacion_promedio"] = {"$gte": min_cal}
    query = f"""db.restaurantes.find({filtro},
  {{ _id:0, nombre:1, tipo_comida:1, barrio:1, calificacion_promedio:1 }}
).sort({{ calificacion_promedio: -1 }}).limit(20)"""
    try:
        db = get_mongo()
        resultado = limpiar_docs(list(
            db.restaurantes.find(
                filtro,
                {"_id": 0, "restaurante_id": 1, "nombre": 1,
                 "tipo_comida": 1, "barrio": 1, "calificacion_promedio": 1}
            ).sort("calificacion_promedio", -1).limit(20)
        ))
        return jsonify({"query": query, "lenguaje": "javascript", "resultado": resultado})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

@app.route("/api/mongo/resenas-restaurante")
def mongo_resenas_restaurante():
    rid   = int(request.args.get("restaurante_id", 1))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ restaurante_id: {rid} }} }},
  {{ $sort: {{ fecha: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from:"usuarios", localField:"dni_usuario",
                 foreignField:"dni_usuario", as:"usuario" }} }},
  {{ $unwind: "$usuario" }},
  {{ $project: {{ _id:0, usuario:"$usuario.username",
                  puntaje:1, comentario:1, fecha:1 }} }}
])"""
    try:
        db = get_mongo()
        pipeline = [
            {"$match": {"restaurante_id": rid}},
            {"$sort": {"fecha": -1}},
            {"$limit": limit},
            {"$lookup": {"from": "usuarios", "localField": "dni_usuario",
                         "foreignField": "dni_usuario", "as": "usuario"}},
            {"$unwind": "$usuario"},
            {"$project": {"_id": 0, "resena_id": 1,
                          "usuario": "$usuario.username",
                          "puntaje": 1, "comentario": 1, "fecha": 1}}
        ]
        return jsonify({"query": query, "lenguaje": "javascript",
                        "resultado": limpiar_docs(list(db.resenas.aggregate(pipeline)))})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

@app.route("/api/mongo/insertar-resena", methods=["POST"])
def mongo_insertar_resena():
    import datetime
    data           = request.json or {}
    dni            = data.get("dni_usuario", 44000001)
    restaurante_id = data.get("restaurante_id", 1)
    puntaje        = data.get("puntaje", 5)
    comentario     = data.get("comentario", "Excelente!")
    query = f"""db.resenas.insertOne({{
  dni_usuario: {dni}, restaurante_id: {restaurante_id},
  puntaje: {puntaje}, comentario: "{comentario}",
  fecha: new Date()
}})"""
    try:
        db     = get_mongo()
        max_id = db.resenas.find_one(sort=[("resena_id", -1)]) or {}
        nid    = (max_id.get("resena_id") or 0) + 1
        doc    = {"resena_id": nid, "dni_usuario": int(dni),
                  "restaurante_id": int(restaurante_id), "puntaje": int(puntaje),
                  "comentario": comentario, "fecha": datetime.datetime.utcnow()}
        res = db.resenas.insert_one(doc)
        return jsonify({"query": query, "lenguaje": "javascript",
                        "resultado": [{"inserted_id": str(res.inserted_id), "resena_id": nid}],
                        "exito": True})
    except Exception as e:
        return jsonify({"query": query, "error": str(e), "resultado": []}), 500

# ── NEO4J ────────────────────────────────────────────────────

def neo4j_run(cypher, params=None):
    driver = get_neo4j_session()
    with driver.session(database=NEO4J_DB) as session:
        result = session.run(cypher, params or {})
        rows   = [r.data() for r in result]
    driver.close()
    return rows

@app.route("/api/neo4j/perfil")
def neo4j_perfil():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (u:Usuario {username: $username})
OPTIONAL MATCH (u)-[:SIGUE]->()
WITH u, count(*) AS siguiendo
OPTIONAL MATCH (u)<-[:SIGUE]-()
WITH u, siguiendo, count(*) AS seguidores
OPTIONAL MATCH (u)-[:VISITO]->()
WITH u, siguiendo, seguidores, count(*) AS visitas
OPTIONAL MATCH (u)-[:CALIFICO]->()
RETURN u.username AS username,
       u.nombre + ' ' + u.apellido AS nombre,
       siguiendo, seguidores, visitas, count(*) AS resenas"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/siguiendo")
def neo4j_siguiendo():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (:Usuario {username: $username})-[:SIGUE]->(seguido:Usuario)
RETURN seguido.username AS username,
       seguido.nombre + ' ' + seguido.apellido AS nombre
ORDER BY username"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/seguidores")
def neo4j_seguidores():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (seguidor:Usuario)-[:SIGUE]->(:Usuario {username: $username})
RETURN seguidor.username AS username,
       seguidor.nombre + ' ' + seguidor.apellido AS nombre
ORDER BY username"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/buscar-usuarios")
def neo4j_buscar_usuarios():
    termino = request.args.get("termino", "val")
    cypher = """MATCH (u:Usuario)
WHERE u.username CONTAINS $termino
   OR toLower(u.nombre)   CONTAINS toLower($termino)
   OR toLower(u.apellido) CONTAINS toLower($termino)
RETURN u.username AS username, u.nombre AS nombre, u.apellido AS apellido
LIMIT 20"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"termino": termino}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/visitas-amigos")
def neo4j_visitas_amigos():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)
      -[v:VISITO]->(r:Restaurante)
RETURN amigo.username AS amigo, r.nombre AS restaurante, v.fecha AS fecha
ORDER BY v.fecha DESC
LIMIT 15"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/recomendacion-colaborativa")
def neo4j_recom_colaborativa():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (yo:Usuario {username: $username})-[:SIGUE]->(amigo:Usuario)
      -[c:CALIFICO]->(r:Restaurante)
WHERE c.puntaje >= 4
  AND NOT (yo)-[:VISITO]->(r)
RETURN r.nombre AS restaurante, r.tipo_comida AS tipo_comida,
       r.barrio AS barrio,
       round(avg(c.puntaje)*100)/100 AS puntaje_amigos,
       count(c) AS calificaciones_altas,
       collect(DISTINCT amigo.username)[0..4] AS amigos
ORDER BY puntaje_amigos DESC, calificaciones_altas DESC
LIMIT 8"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/recomendacion-contenido")
def neo4j_recom_contenido():
    username = request.args.get("username", "VitoNava")
    cypher = """MATCH (yo:Usuario {username: $username})-[c:CALIFICO]->(gustado:Restaurante)
WHERE c.puntaje >= 4
MATCH (rec:Restaurante)
WHERE rec <> gustado
  AND NOT (yo)-[:VISITO]->(rec)
  AND NOT (yo)-[:CALIFICO]->(rec)
  AND (rec.tipo_comida = gustado.tipo_comida OR rec.barrio = gustado.barrio)
WITH rec, count(DISTINCT gustado) AS coincidencias,
     collect(DISTINCT gustado.nombre)[0..3] AS basado_en
RETURN rec.nombre AS restaurante, rec.tipo_comida AS tipo_comida,
       rec.barrio AS barrio, rec.calificacion_promedio AS calificacion,
       coincidencias, basado_en
ORDER BY coincidencias DESC, calificacion DESC
LIMIT 8"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"username": username}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

@app.route("/api/neo4j/seguir", methods=["POST"])
def neo4j_seguir():
    data     = request.json or {}
    follower = data.get("follower", "VitoNava")
    followed = data.get("followed", "LuisRam")
    cypher = """MATCH (a:Usuario {username: $follower}),
      (b:Usuario {username: $followed})
MERGE (a)-[r:SIGUE]->(b)
ON CREATE SET r.desde = date()
RETURN a.username AS de, b.username AS a, r.desde AS desde"""
    try:
        rows = limpiar_docs(neo4j_run(cypher, {"follower": follower, "followed": followed}))
        return jsonify({"query": cypher, "lenguaje": "cypher", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cypher, "error": str(e), "resultado": []}), 500

# ── CASSANDRA ────────────────────────────────────────────────

def cass_run(cql, params=()):
    cluster, session = get_cassandra()
    try:
        rows = list(session.execute(cql, params))
        return [dict(r._asdict()) for r in rows]
    finally:
        session.shutdown()
        cluster.shutdown()

@app.route("/api/cassandra/promociones-restaurante")
def cass_promociones_restaurante():
    rid = int(request.args.get("restaurante_id", 1))
    cql = """SELECT restaurante_id, estado, fecha_fin, promocion_id,
       titulo, descripcion, descuento, fecha_inicio, barrio
FROM promociones_por_restaurante
WHERE restaurante_id = %s AND estado = 'activa';"""
    try:
        rows = limpiar_docs(cass_run(cql, (rid,)))
        return jsonify({"query": cql, "lenguaje": "sql", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cql, "error": str(e), "resultado": []}), 500

@app.route("/api/cassandra/promociones-fecha-barrio")
def cass_promociones_fecha_barrio():
    dia    = request.args.get("dia", "2025-06-01")
    barrio = request.args.get("barrio", "Palermo")
    cql = """SELECT dia_vigencia, barrio, restaurante_id, promocion_id,
       titulo, descuento, fecha_inicio, fecha_fin, estado
FROM promociones_activas_por_fecha
WHERE dia_vigencia = %s AND barrio = %s;"""
    try:
        import datetime
        fecha = datetime.date.fromisoformat(dia)
        rows  = limpiar_docs(cass_run(cql, (fecha, barrio)))
        return jsonify({"query": cql, "lenguaje": "sql", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cql, "error": str(e), "resultado": []}), 500

@app.route("/api/cassandra/visitas-restaurante-dia")
def cass_visitas_dia():
    rid   = int(request.args.get("restaurante_id", 1))
    fecha = request.args.get("fecha", "2025-06-01")
    cql = """SELECT restaurante_id, fecha, hora, visita_id,
       dni_usuario, plato_nombre, monto
FROM visitas_por_restaurante_dia
WHERE restaurante_id = %s AND fecha = %s;"""
    try:
        import datetime
        fecha_d = datetime.date.fromisoformat(fecha)
        rows    = limpiar_docs(cass_run(cql, (rid, fecha_d)))
        return jsonify({"query": cql, "lenguaje": "sql", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cql, "error": str(e), "resultado": []}), 500

@app.route("/api/cassandra/insertar-visita", methods=["POST"])
def cass_insertar_visita():
    import uuid, datetime
    data           = request.json or {}
    dni            = data.get("dni_usuario", 44000001)
    restaurante_id = data.get("restaurante_id", 1)
    plato_nombre   = data.get("plato_nombre", "Milanesa napolitana")
    tipo_comida    = data.get("tipo_comida", "Argentina")
    barrio         = data.get("barrio", "Palermo")
    monto          = data.get("monto", 1500)
    cql = """INSERT INTO visitas_por_restaurante_dia
  (restaurante_id, fecha, hora, visita_id,
   dni_usuario, plato_nombre, tipo_comida, barrio, monto)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    try:
        now    = datetime.datetime.utcnow()
        params = (int(restaurante_id), now.date(), now.time(),
                  uuid.uuid4(), int(dni), plato_nombre,
                  tipo_comida, barrio, float(monto))
        cass_run(cql, params)
        return jsonify({"query": cql, "lenguaje": "sql",
                        "resultado": [{"status": "Visita insertada correctamente"}],
                        "exito": True})
    except Exception as e:
        return jsonify({"query": cql, "error": str(e), "resultado": []}), 500

@app.route("/api/cassandra/metricas-dia")
def cass_metricas_dia():
    rid   = int(request.args.get("restaurante_id", 1))
    fecha = request.args.get("fecha", "2025-06-01")
    cql = """SELECT restaurante_id, fecha, tipo_comida,
       total_visitas, total_ingresos, plato_mas_pedido
FROM metricas_restaurante_por_dia
WHERE restaurante_id = %s AND fecha = %s;"""
    try:
        import datetime
        fecha_d = datetime.date.fromisoformat(fecha)
        rows    = limpiar_docs(cass_run(cql, (rid, fecha_d)))
        return jsonify({"query": cql, "lenguaje": "sql", "resultado": rows})
    except Exception as e:
        return jsonify({"query": cql, "error": str(e), "resultado": []}), 500

# ── REDIS ────────────────────────────────────────────────────

@app.route("/api/redis/sesiones-activas")
def redis_sesiones():
    comando = "KEYS sesion:*\nGET sesion:{user_id}\nTTL sesion:{user_id}"
    try:
        r      = get_redis()
        claves = r.keys("sesion:*")
        rows   = []
        for clave in claves:
            token   = r.get(clave)
            ttl     = r.ttl(clave)
            user_id = clave.split(":")[1]
            rows.append({"usuario": user_id, "token": token, "ttl_segundos": ttl})
        return jsonify({"query": comando, "lenguaje": "redis", "resultado": rows})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

@app.route("/api/redis/ranking-restaurantes")
def redis_ranking_restaurantes():
    top_n   = int(request.args.get("top", 10))
    comando = f"ZREVRANGE ranking:restaurante 0 {top_n-1} WITHSCORES"
    try:
        r   = get_redis()
        res = r.zrevrange("ranking:restaurante", 0, top_n - 1, withscores=True)
        rows = [{"posicion": i+1, "restaurante": nombre, "visitas": int(score)}
                for i, (nombre, score) in enumerate(res)]
        return jsonify({"query": comando, "lenguaje": "redis", "resultado": rows})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

@app.route("/api/redis/ranking-tipos-comida")
def redis_ranking_tipos():
    top_n   = int(request.args.get("top", 10))
    comando = f"ZREVRANGE ranking:tipoComida 0 {top_n-1} WITHSCORES"
    try:
        r   = get_redis()
        res = r.zrevrange("ranking:tipoComida", 0, top_n - 1, withscores=True)
        rows = [{"posicion": i+1, "tipo_comida": nombre, "pedidos": int(score)}
                for i, (nombre, score) in enumerate(res)]
        return jsonify({"query": comando, "lenguaje": "redis", "resultado": rows})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

@app.route("/api/redis/ultimas-busquedas")
def redis_ultimas_busquedas():
    user_id = request.args.get("user_id", "44000009")
    comando = f"LRANGE busqueda:{user_id} 0 4"
    try:
        r         = get_redis()
        busquedas = r.lrange(f"busqueda:{user_id}", 0, 4)
        rows      = [{"posicion": i+1, "termino": t} for i, t in enumerate(busquedas)]
        return jsonify({"query": comando, "lenguaje": "redis", "resultado": rows})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

@app.route("/api/redis/verificar-sesion")
def redis_verificar_sesion():
    user_id = request.args.get("user_id", "44000009")
    comando = f"EXISTS sesion:{user_id}\nGET sesion:{user_id}"
    try:
        r     = get_redis()
        token = r.get(f"sesion:{user_id}")
        ttl   = r.ttl(f"sesion:{user_id}")
        rows  = [{"usuario": user_id, "sesion_activa": token is not None,
                  "token": token or "sin sesion", "ttl_segundos": ttl}]
        return jsonify({"query": comando, "lenguaje": "redis", "resultado": rows})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

@app.route("/api/redis/registrar-busqueda", methods=["POST"])
def redis_registrar_busqueda():
    data    = request.json or {}
    user_id = data.get("user_id", "44000009")
    termino = data.get("termino", "pizza")
    comando = f'LPUSH busqueda:{user_id} "{termino}"\nLTRIM busqueda:{user_id} 0 4'
    try:
        r = get_redis()
        r.lpush(f"busqueda:{user_id}", termino)
        r.ltrim(f"busqueda:{user_id}", 0, 4)
        busquedas = r.lrange(f"busqueda:{user_id}", 0, 4)
        rows = [{"posicion": i+1, "termino": t} for i, t in enumerate(busquedas)]
        return jsonify({"query": comando, "lenguaje": "redis",
                        "resultado": rows, "exito": True})
    except Exception as e:
        return jsonify({"query": comando, "error": str(e), "resultado": []}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)