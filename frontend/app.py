"""
STARVY — API Flask del Frontend

IMPORTANTE:
Este archivo NO vuelve a implementar la lógica de cada base de datos.
Funciona como capa HTTP/presentación: recibe requests del frontend, llama a las
funciones ya creadas en mongoDB/, Neo4j/, Cassandra/ y Redis/, y devuelve JSON
para la pantalla del panel.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import io
import json
import sys
from contextlib import contextmanager, redirect_stdout
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIRS = {
    "mongo": BASE_DIR / "mongoDB",
    "neo4j": BASE_DIR / "Neo4j",
    "cassandra": BASE_DIR / "Cassandra",
    "redis": BASE_DIR / "Redis",
}

# Los módulos de cada motor se llaman igual (consultas.py, conexion.py, config.py).
# Para evitar que Python mezcle dependencias entre carpetas, cada llamada se hace
# en un contexto aislado de imports.
_SHARED_MODULE_NAMES = [
    "config",
    "conexion",
    "consultas",
    "escrituras",
    "utilidades",
    "carga_dataset",
    "esquema",
    "mongo_client",
]


def _json_default(obj: Any) -> Any:
    """Convierte tipos de Mongo/Neo4j/Cassandra a JSON."""
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    if isinstance(obj, _dt.time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    # ObjectId, Neo4j Date/Time, Cassandra Time, etc.
    return str(obj)


def limpiar_docs(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=_json_default, ensure_ascii=False))


@contextmanager
def _engine_import_context(engine: str):
    """Carga imports desde la carpeta del motor pedido y restaura el entorno."""
    engine_dir = ENGINE_DIRS[engine]
    old_path = list(sys.path)
    saved_modules = {name: sys.modules.get(name) for name in _SHARED_MODULE_NAMES}

    for name in _SHARED_MODULE_NAMES:
        sys.modules.pop(name, None)

    sys.path.insert(0, str(engine_dir))
    try:
        yield
    finally:
        # Limpieza de imports con nombres genéricos para que no contaminen otro motor.
        for name in _SHARED_MODULE_NAMES:
            sys.modules.pop(name, None)
            if saved_modules[name] is not None:
                sys.modules[name] = saved_modules[name]
        sys.path = old_path


_module_cache: Dict[str, Any] = {}


def motor_call(engine: str, module_name: str, function_name: str, *args, **kwargs):
    """Llama una función existente de un motor, capturando prints de consola."""
    cache_key = f"{engine}:{module_name}"
    if cache_key in _module_cache:
        module = _module_cache[cache_key]
    else:
        with _engine_import_context(engine):
            module = importlib.import_module(module_name)
        if engine == "redis":
            _module_cache[cache_key] = module
    function = getattr(module, function_name)
    with redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


def ok_response(query: str, lenguaje: str, resultado: Any, **extra):
    payload = {
        "query": query,
        "lenguaje": lenguaje,
        "resultado": limpiar_docs(resultado or []),
    }
    payload.update(extra)
    return jsonify(payload)


def error_response(query: str, mensaje: str, status: int = 500, lenguaje: str = "plaintext"):
    return jsonify({"query": query, "lenguaje": lenguaje, "error": mensaje, "resultado": []}), status


@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────
# MONGODB — endpoints finos que llaman mongoDB/consultas.py y mongoDB/escrituras.py
# ─────────────────────────────────────────────────────────────


@app.route("/api/mongo/login", methods=["POST"])
def mongo_login():
    data = request.json or {}
    username = data.get("username", "VitoNava")
    password = data.get("password", "starvy123")
    query = f'db.usuarios.findOne(\n  {{ username: "{username}", password: "***" }},\n  {{ password: 0 }}\n)'
    try:
        # Función existente: valida credenciales y crea sesión Redis si está disponible.
        user_id = motor_call("mongo", "escrituras", "login_usuario", username, password)
        if not user_id:
            return ok_response(query, "javascript", [], exito=False)

        usuario = motor_call("mongo", "consultas", "buscar_usuario_por_username", username)
        if usuario:
            usuario.pop("password", None)
            usuario["login_ok"] = True
            usuario["sesion_redis_intentada"] = True
        return ok_response(query, "javascript", [usuario] if usuario else [], exito=True)
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


@app.route("/api/mongo/mis-resenas")
def mongo_mis_resenas():
    dni = int(request.args.get("dni", 44000009))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ dni_usuario: {dni}, comentario: {{ $exists: true, $nin: [null, ""] }} }} }},
  {{ $sort: {{ fecha: -1, resena_id: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from: "restaurantes", localField: "restaurante_id", foreignField: "restaurante_id", as: "restaurante" }} }},
  {{ $unwind: "$restaurante" }},
  {{ $project: {{
      _id: 0,
      resena_id: 1,
      restaurante_id: 1,
      restaurante: "$restaurante.nombre",
      comentario: 1,
      puntaje: 1,
      fecha: 1
  }} }}
])"""
    try:
        rows = motor_call("mongo", "consultas", "ver_mis_resenas", dni, limit)
        return ok_response(query, "javascript", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


@app.route("/api/mongo/mis-calificaciones")
def mongo_mis_calificaciones():
    dni = int(request.args.get("dni", 44000009))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ dni_usuario: {dni} }} }},
  {{ $sort: {{ fecha: -1, resena_id: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from: "restaurantes", localField: "restaurante_id", foreignField: "restaurante_id", as: "restaurante" }} }},
  {{ $unwind: "$restaurante" }},
  {{ $project: {{
      _id: 0,
      resena_id: 1,
      restaurante_id: 1,
      restaurante: "$restaurante.nombre",
      puntaje: 1,
      fecha: 1
  }} }}
])"""
    try:
        rows = motor_call("mongo", "consultas", "ver_mis_calificaciones", dni, limit)
        return ok_response(query, "javascript", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


@app.route("/api/mongo/buscar-restaurantes")
def mongo_buscar_restaurantes():
    tipo = request.args.get("tipo", "").strip() or None
    barrio = request.args.get("barrio", "").strip() or None
    min_cal_raw = request.args.get("min_calificacion", "0")
    min_cal = float(min_cal_raw or 0)
    dni = request.args.get("dni", "").strip() or None
    filtro_mql = {}
    if tipo:
        filtro_mql["tipo_comida"] = {"$regex": tipo, "$options": "i"}
    if barrio:
        filtro_mql["barrio"] = {"$regex": barrio, "$options": "i"}
    if min_cal > 0:
        filtro_mql["calificacion_promedio"] = {"$gte": 4.95 if min_cal >= 5 else min_cal}
    query = f"""db.restaurantes.find(
{json.dumps(filtro_mql, ensure_ascii=False, indent=2)}
).sort({{ calificacion_promedio: -1 }}).limit(20)"""
    try:
        if dni:
            termino_busqueda = " ".join(filter(None, [tipo, barrio]))
            if termino_busqueda:
                try:
                    if motor_call("redis", "consultas", "verificar_sesion", dni):
                        motor_call("redis", "consultas", "registrar_busqueda", dni, termino_busqueda)
                except Exception:
                    pass
        rows = motor_call(
            "mongo",
            "consultas",
            "buscar_restaurantes_por_filtros",
            tipo_comida=tipo,
            calificacion_minima=min_cal if min_cal > 0 else None,
            barrio=barrio,
            limite=20,
        )
        return ok_response(query, "javascript", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


@app.route("/api/mongo/platos-restaurante")
def mongo_platos_restaurante():
    rid = int(request.args.get("restaurante_id", 1))
    query = f"""db.restaurantes.findOne(
  {{ restaurante_id: {rid} }},
  {{ _id: 0, restaurante_id: 1, nombre: 1, barrio: 1, platos: 1 }}
)
// En Python se filtran los platos disponibles para armar el dropdown."""
    try:
        rows = motor_call("mongo", "consultas", "listar_platos_restaurante", rid, True)
        return ok_response(query, "mql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="mql")


@app.route("/api/mongo/resenas-restaurante")
def mongo_resenas_restaurante():
    rid = int(request.args.get("restaurante_id", 1))
    limit = int(request.args.get("limit", 10))
    query = f"""db.resenas.aggregate([
  {{ $match: {{ restaurante_id: {rid} }} }},
  {{ $sort: {{ fecha: -1, resena_id: -1 }} }},
  {{ $limit: {limit} }},
  {{ $lookup: {{ from: "usuarios", localField: "dni_usuario", foreignField: "dni_usuario", as: "usuario" }} }},
  {{ $unwind: "$usuario" }},
  {{ $project: {{
      _id: 0,
      resena_id: 1,
      usuario: "$usuario.username",
      puntaje: 1,
      comentario: 1,
      fecha: 1
  }} }}
])"""
    try:
        rows = motor_call("mongo", "consultas", "ver_resenas_de_restaurante", rid, limit)
        return ok_response(query, "javascript", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


@app.route("/api/mongo/insertar-resena", methods=["POST"])
def mongo_insertar_resena():
    data = request.json or {}
    dni = int(data.get("dni_usuario", 44000001))
    restaurante_id = int(data.get("restaurante_id", 1))
    puntaje = int(data.get("puntaje", 5))
    comentario = data.get("comentario", "Excelente!")
    fecha = _dt.date.today().isoformat()

    query = f"""db.resenas.insertOne({{\n  dni_usuario: {dni},\n  restaurante_id: {restaurante_id},\n  puntaje: {puntaje},\n  comentario: "{comentario}",\n  fecha: "{fecha}"\n}})\n// Luego se sincroniza CALIFICO en Neo4j"""
    try:
        # 1) Función existente de MongoDB: inserta reseña y recalcula promedio.
        resena = motor_call(
            "mongo",
            "escrituras",
            "insertar_resena",
            dni_usuario=dni,
            restaurante_id=restaurante_id,
            puntaje=puntaje,
            comentario=comentario,
            fecha=fecha,
        )
        if not resena:
            raise ValueError("MongoDB no pudo insertar la reseña. Revisá usuario, restaurante o duplicados.")

        # 2) Consistencia: misma reseña visible en Neo4j como relación CALIFICO.
        # Si Neo4j falla, compensamos eliminando la reseña de Mongo para no dejar
        # datos visibles en un motor y ausentes en el otro.
        try:
            sync_neo4j = motor_call(
                "neo4j",
                "escrituras",
                "sincronizar_resena_desde_mongo",
                dni_usuario=dni,
                restaurante_id=restaurante_id,
                resena_id=resena["resena_id"],
                puntaje=puntaje,
                comentario=comentario,
                fecha=fecha,
            )
        except Exception as sync_error:
            motor_call("mongo", "escrituras", "eliminar_resena_por_id", resena["resena_id"])
            raise RuntimeError(
                "La reseña se insertó en MongoDB, pero falló la sincronización con Neo4j. "
                "Se revirtió MongoDB para mantener consistencia. Error Neo4j: "
                f"{sync_error}"
            )

        promedio = motor_call("mongo", "escrituras", "recalcular_calificacion_promedio", restaurante_id)
        return ok_response(
            query,
            "javascript",
            [{
                **limpiar_docs(resena),
                "promedio_restaurante_actualizado": promedio,
                "sincronizado_neo4j": bool(sync_neo4j),
                "consistencia": "MongoDB + Neo4j OK",
            }],
            exito=True,
        )
    except Exception as e:
        return error_response(query, str(e), lenguaje="javascript")


# ─────────────────────────────────────────────────────────────
# NEO4J — endpoints que llaman Neo4j/consultas.py y Neo4j/escrituras.py
# ─────────────────────────────────────────────────────────────


def construir_grafo_perfil(row: Dict[str, Any], username: str) -> Dict[str, List[Dict[str, Any]]]:
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen_nodes = set()
    seen_links = set()

    def node(node_id, label, tipo="user", sub=""):
        node_id = str(node_id)
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({"id": node_id, "label": str(label), "type": tipo, "sub": str(sub or "")})

    def link(source, target, label):
        source, target, label = str(source), str(target), str(label)
        key = (source, target, label)
        if source != target and key not in seen_links:
            seen_links.add(key)
            links.append({"source": source, "target": target, "label": label})

    center = f"user:{username}"
    node(center, username, "user", row.get("nombre", "usuario actual"))

    for u in row.get("siguiendo_usuarios", []) or []:
        uname = u.get("username") or u.get("nombre")
        if uname:
            uid = f"user:{uname}"
            node(uid, uname, "user", u.get("nombre", "seguido"))
            link(center, uid, "SIGUE")

    for u in row.get("seguidores_usuarios", []) or []:
        uname = u.get("username") or u.get("nombre")
        if uname:
            uid = f"user:{uname}"
            node(uid, uname, "user", u.get("nombre", "seguidor"))
            link(uid, center, "SIGUE")

    for v in row.get("visitas_restaurantes", []) or []:
        rest = v.get("restaurante") or v.get("nombre")
        if rest:
            rid = f"rest:{rest}"
            detalle = " · ".join([x for x in [v.get("tipo_comida"), v.get("barrio")] if x])
            node(rid, rest, "restaurant", detalle or "visitado")
            link(center, rid, f"VISITÓ {v.get('fecha')}" if v.get("fecha") else "VISITÓ")

    for c in row.get("resenas_restaurantes", []) or []:
        rest = c.get("restaurante") or c.get("nombre")
        if rest:
            rid = f"rest:{rest}"
            node(rid, rest, "restaurant", f"★ {c.get('puntaje')}" if c.get("puntaje") else "calificado")
            link(center, rid, f"CALIFICÓ {c.get('puntaje')}★" if c.get("puntaje") else "CALIFICÓ")

    return {"nodes": nodes[:45], "links": links[:80]}


@app.route("/api/neo4j/perfil")
def neo4j_perfil():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (u:Usuario {{username: "{username}"}})
OPTIONAL MATCH (u)-[:SIGUE]->(seguido:Usuario)
OPTIONAL MATCH (seguidor:Usuario)-[:SIGUE]->(u)
OPTIONAL MATCH (u)-[v:VISITO]->(rest_visitado:Restaurante)
OPTIONAL MATCH (u)-[c:CALIFICO]->(rest_calificado:Restaurante)
RETURN u.username, u.nombre + " " + u.apellido AS nombre,
       count(DISTINCT seguido) AS siguiendo,
       count(DISTINCT seguidor) AS seguidores,
       count(DISTINCT v) AS visitas,
       count(DISTINCT c) AS resenas"""
    try:
        rows = motor_call("neo4j", "consultas", "consultar_detalle_perfil_usuario", username)
        rows = limpiar_docs(rows)
        grafo = construir_grafo_perfil(rows[0], username) if rows else {"nodes": [], "links": []}
        tabla = []
        if rows:
            r = rows[0]
            tabla = [{
                "username": r.get("username"),
                "nombre": r.get("nombre"),
                "siguiendo": r.get("siguiendo", 0),
                "seguidores": r.get("seguidores", 0),
                "visitas": r.get("visitas", 0),
                "resenas": r.get("resenas", 0),
            }]
        return ok_response(query, "cypher", tabla, grafo=grafo)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/siguiendo")
def neo4j_siguiendo():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (:Usuario {{username: "{username}"}})-[:SIGUE]->(seguido:Usuario)
RETURN seguido.username AS username,
       seguido.nombre + " " + seguido.apellido AS nombre
ORDER BY username"""
    try:
        rows = motor_call("neo4j", "consultas", "consultar_usuarios_que_sigue", username)
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/seguidores")
def neo4j_seguidores():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (seguidor:Usuario)-[:SIGUE]->(:Usuario {{username: "{username}"}})
RETURN seguidor.username AS username,
       seguidor.nombre + " " + seguidor.apellido AS nombre
ORDER BY username"""
    try:
        rows = motor_call("neo4j", "consultas", "consultar_seguidores", username)
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/buscar-usuarios")
def neo4j_buscar_usuarios():
    termino = request.args.get("termino", "val")
    dni = request.args.get("dni", "").strip() or None
    query = f"""MATCH (u:Usuario)
WHERE toLower(u.username) CONTAINS toLower("{termino}")
   OR toLower(u.nombre) CONTAINS toLower("{termino}")
   OR toLower(u.apellido) CONTAINS toLower("{termino}")
RETURN u.dni_usuario AS dni_usuario,
       u.username AS username,
       u.nombre + " " + u.apellido AS nombre
ORDER BY username
LIMIT 20"""
    try:
        if dni and termino:
            try:
                if motor_call("redis", "consultas", "verificar_sesion", dni):
                    motor_call("redis", "consultas", "registrar_busqueda", dni, termino)
            except Exception:
                pass
        rows = motor_call("neo4j", "consultas", "buscar_usuarios", termino, 20)
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/visitas-amigos")
def neo4j_visitas_amigos():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (:Usuario {{username: "{username}"}})-[:SIGUE]->(amigo:Usuario)-[v:VISITO]->(r:Restaurante)
RETURN amigo.username AS amigo,
       r.nombre AS restaurante,
       r.barrio AS barrio,
       r.tipo_comida AS tipo_comida,
       v.fecha AS fecha
ORDER BY v.fecha DESC
LIMIT 15"""
    try:
        rows = motor_call("neo4j", "consultas", "consultar_visitas_amigos", username, 15)
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/recomendacion-colaborativa")
def neo4j_recom_colaborativa():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (yo:Usuario {{username: "{username}"}})-[:SIGUE]->(amigo:Usuario)-[c:CALIFICO]->(r:Restaurante)
WHERE c.puntaje >= 4
  AND NOT (yo)-[:VISITO]->(r)
RETURN r.restaurante_id AS restaurante_id,
       r.nombre AS restaurante,
       r.tipo_comida AS tipo_comida,
       r.barrio AS barrio,
       round(avg(c.puntaje) * 100) / 100 AS puntaje_promedio_amigos,
       count(c) AS calificaciones_altas,
       collect(DISTINCT amigo.username)[0..4] AS amigos
ORDER BY puntaje_promedio_amigos DESC, calificaciones_altas DESC
LIMIT 8"""
    try:
        rows = motor_call("neo4j", "consultas", "recomendar_bien_calificados_por_amigos", username, 8)
        # Alias para que el HTML actual siga mostrando el grafo/puntaje esperado.
        for r in rows or []:
            if "puntaje_promedio_amigos" in r:
                r["puntaje_amigos"] = r["puntaje_promedio_amigos"]
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/recomendacion-contenido")
def neo4j_recom_contenido():
    username = request.args.get("username", "VitoNava")
    query = f"""MATCH (yo:Usuario {{username: "{username}"}})-[c:CALIFICO]->(gustado:Restaurante)
WHERE c.puntaje >= 4
MATCH (rec:Restaurante)
WHERE rec <> gustado
  AND NOT (yo)-[:VISITO]->(rec)
  AND NOT (yo)-[:CALIFICO]->(rec)
  AND (rec.tipo_comida = gustado.tipo_comida OR rec.barrio = gustado.barrio)
RETURN rec.restaurante_id AS restaurante_id,
       rec.nombre AS restaurante,
       rec.tipo_comida AS tipo_comida,
       rec.barrio AS barrio,
       rec.calificacion_promedio AS calificacion_promedio
ORDER BY calificacion_promedio DESC
LIMIT 8"""
    try:
        rows = motor_call("neo4j", "consultas", "recomendar_por_contenido", username, 8)
        for r in rows or []:
            if "calificacion_promedio" in r:
                r["calificacion"] = r["calificacion_promedio"]
        return ok_response(query, "cypher", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


@app.route("/api/neo4j/seguir", methods=["POST"])
def neo4j_seguir():
    data = request.json or {}
    follower = data.get("follower", "VitoNava")
    followed = data.get("followed", "LuisRam")
    query = f"""MATCH (origen:Usuario {{username: "{follower}"}})
MATCH (destino:Usuario {{username: "{followed}"}})
WHERE origen <> destino
MERGE (origen)-[:SIGUE]->(destino)
RETURN origen.username AS usuario,
       destino.username AS sigue_a"""
    try:
        row = motor_call("neo4j", "escrituras", "seguir_usuario", follower, followed)
        return ok_response(query, "cypher", [row] if row else [], exito=bool(row))
    except Exception as e:
        return error_response(query, str(e), lenguaje="cypher")


# ─────────────────────────────────────────────────────────────
# CASSANDRA — endpoints que llaman Cassandra/consultas.py y Cassandra/escrituras.py
# ─────────────────────────────────────────────────────────────


@app.route("/api/cassandra/promociones-restaurante")
def cass_promociones_restaurante():
    rid = int(request.args.get("restaurante_id", 1))
    query = f"""SELECT restaurante_id, estado, fecha_fin, promocion_id, titulo,
       descripcion, descuento, fecha_inicio, barrio
FROM promociones_por_restaurante
WHERE restaurante_id = {rid}
AND estado = 'activa';"""
    try:
        rows = motor_call("cassandra", "consultas", "consultar_promociones_por_restaurante", rid)
        return ok_response(query, "sql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")


@app.route("/api/cassandra/promociones-fecha-barrio")
def cass_promociones_fecha_barrio():
    dia = request.args.get("dia", "2026-05-15")
    barrio = request.args.get("barrio", "Palermo")
    query = f"""SELECT dia_vigencia, barrio, restaurante_id, promocion_id,
       titulo, descuento, fecha_inicio, fecha_fin, estado
FROM promociones_activas_por_fecha
WHERE dia_vigencia = '{dia}'
AND barrio = '{barrio}';"""
    try:
        rows = motor_call("cassandra", "consultas", "consultar_promociones_por_fecha_barrio", dia, barrio)
        return ok_response(query, "sql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")


@app.route("/api/cassandra/visitas-restaurante-dia")
def cass_visitas_dia():
    rid = int(request.args.get("restaurante_id", 1))
    fecha = request.args.get("fecha", "2026-05-15")
    query = f"""SELECT restaurante_id, fecha, hora, visita_id, dni_usuario,
       plato_id, plato_nombre, tipo_comida, barrio, monto
FROM visitas_por_restaurante_dia
WHERE restaurante_id = {rid}
AND fecha = '{fecha}';"""
    try:
        rows = motor_call("cassandra", "consultas", "consultar_visitas_por_restaurante_dia", rid, fecha)
        return ok_response(query, "sql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")

@app.route("/api/cassandra/historial-usuario")
def cass_historial_usuario():
    dni = int(request.args.get("dni_usuario", 44000014))
    query = f"""SELECT dni_usuario, fecha, hora, visita_id, restaurante_id,
       plato_id, plato_nombre, tipo_comida, monto
FROM visitas_por_usuario_fecha
WHERE dni_usuario = {dni}
LIMIT 10;"""
    try:
        rows = motor_call("cassandra", "consultas", "consultar_historial_visitas_usuario", dni)
        return ok_response(query, "sql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")

@app.route("/api/cassandra/insertar-visita", methods=["POST"])
def cass_insertar_visita():
    data = request.json or {}
    visita = {
        "dni_usuario": int(data.get("dni_usuario", 44000001)),
        "restaurante_id": int(data.get("restaurante_id", 1)),
        "plato_id": int(data.get("plato_id", 9001)),
        "plato_nombre": data.get("plato_nombre", "Milanesa napolitana"),
        "tipo_comida": data.get("tipo_comida", "Milanesas"),
        "barrio": data.get("barrio", "Palermo"),
        "monto": float(data.get("monto", 1500)),
        "fecha": _dt.date.today().isoformat(),
        "hora": _dt.datetime.now().strftime("%H:%M:%S"),
    }
    query = f"""INSERT INTO visitas_por_restaurante_dia (
  restaurante_id, fecha, hora, visita_id, dni_usuario,
  plato_id, plato_nombre, tipo_comida, barrio, monto
) VALUES (
  {visita["restaurante_id"]}, '{visita["fecha"]}', '{visita["hora"]}', <nuevo_id>, {visita["dni_usuario"]},
  {visita["plato_id"]}, '{visita["plato_nombre"]}', '{visita["tipo_comida"]}', '{visita["barrio"]}', {visita["monto"]}
);

INSERT INTO visitas_por_usuario_fecha (...) VALUES (...);
INSERT INTO metricas_restaurante_por_dia (...) VALUES (...);

// Luego se sincroniza VISITO y PIDIO en Neo4j"""
    try:
        resultado_cassandra = motor_call("cassandra", "escrituras", "registrar_visita", visita)

        # Consistencia: la visita también queda disponible en el grafo para recomendaciones sociales.
        sync_neo4j = motor_call("neo4j", "escrituras", "sincronizar_visita_desde_cassandra", **resultado_cassandra)

        # Si el módulo de Cassandra no pudo actualizar Redis, lo hacemos desde acá.
        # Esto actualiza ranking:restaurante y ranking:tipoComida en una sola llamada.
        sync_redis = resultado_cassandra.get("sincronizado_redis", False)
        if not sync_redis:
            try:
                docs = motor_call("mongo", "consultas", "ver_calificacion_restaurante", visita["restaurante_id"])
                nombre = docs[0]["nombre"] if docs else f"restaurante_{visita['restaurante_id']}"
                motor_call("redis", "consultas", "registrar_visita", nombre, visita["tipo_comida"])
                sync_redis = True
            except Exception:
                sync_redis = False

        resultado = [{**limpiar_docs(resultado_cassandra), "sincronizado_neo4j": bool(sync_neo4j), "sincronizado_redis": sync_redis}]
        return ok_response(query, "sql", resultado, exito=True)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")


@app.route("/api/cassandra/metricas-dia")
def cass_metricas_dia():
    rid = int(request.args.get("restaurante_id", 1))
    fecha = request.args.get("fecha", "2026-05-15")
    query = f"""SELECT restaurante_id, fecha, cantidad_vendida, plato_id,
       plato_nombre, tipo_comida, total_ingresos
FROM metricas_restaurante_por_dia
WHERE restaurante_id = {rid}
AND fecha = '{fecha}'
LIMIT 1;"""
    try:
        rows = motor_call("cassandra", "consultas", "consultar_plato_mas_vendido", rid, fecha)
        return ok_response(query, "sql", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="sql")


# ─────────────────────────────────────────────────────────────
# REDIS — endpoints que llaman Redis/consultas.py
# ─────────────────────────────────────────────────────────────


@app.route("/api/redis/sesiones-activas")
def redis_sesiones():
    query = """KEYS sesion:*
GET sesion:{user_id}
TTL sesion:{user_id}"""
    try:
        rows = motor_call("redis", "consultas", "ver_sesiones_activas")
        return ok_response(query, "redis", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


@app.route("/api/redis/verificar-sesion")
def redis_verificar_sesion():
    user_id = request.args.get("user_id", "44000009")
    query = f"""GET sesion:{user_id}
TTL sesion:{user_id}"""
    try:
        row = motor_call("redis", "consultas", "verificar_sesion", user_id)
        return ok_response(query, "redis", [row] if isinstance(row, dict) else [{"usuario": user_id, "sesion_activa": bool(row)}])
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


@app.route("/api/redis/ranking-restaurantes")
def redis_ranking_restaurantes():
    top_n = int(request.args.get("top", 10))
    query = f"ZREVRANGE ranking:restaurante 0 {top_n - 1} WITHSCORES"
    try:
        rows = motor_call("redis", "consultas", "ver_ranking_restaurantes", top_n)
        return ok_response(query, "redis", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


@app.route("/api/redis/ranking-tipos-comida")
def redis_ranking_tipos():
    top_n = int(request.args.get("top", 10))
    query = f"ZREVRANGE ranking:tipoComida 0 {top_n - 1} WITHSCORES"
    try:
        rows = motor_call("redis", "consultas", "ver_ranking_tipos_comida", top_n)
        return ok_response(query, "redis", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


@app.route("/api/redis/ultimas-busquedas")
def redis_ultimas_busquedas():
    user_id = request.args.get("user_id", "44000009")
    query = f"LRANGE busqueda:{user_id} 0 4"
    try:
        rows = motor_call("redis", "consultas", "ver_ultimas_busquedas", user_id)
        return ok_response(query, "redis", rows)
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


@app.route("/api/redis/registrar-busqueda", methods=["POST"])
def redis_registrar_busqueda():
    data = request.json or {}
    user_id = data.get("user_id", "").strip()
    termino = data.get("termino", "").strip()
    query = f"""LPUSH busqueda:{user_id or "<user_id>"} "{termino or "<termino>"}"
LTRIM busqueda:{user_id or "<user_id>"} 0 4"""
    if not user_id:
        return error_response(query, "Se requiere user_id para registrar una búsqueda.", 400, lenguaje="redis")
    if not termino:
        return error_response(query, "Se requiere un término de búsqueda.", 400, lenguaje="redis")
    try:
        sesion_activa = motor_call("redis", "consultas", "verificar_sesion", user_id)
        if not sesion_activa:
            return error_response(query, f"No hay sesión activa para el usuario {user_id}. Iniciá sesión primero.", 401, lenguaje="redis")
        rows = motor_call("redis", "consultas", "registrar_busqueda", user_id, termino)
        return ok_response(query, "redis", rows, exito=True)
    except Exception as e:
        return error_response(query, str(e), lenguaje="redis")


if __name__ == "__main__":
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        try:
            print("Reconstruyendo rankings Redis desde Cassandra...")
            motor_call("redis", "consultas", "reconstruir_desde_cassandra")
            print("Rankings Redis listos.")
        except Exception as e:
            print(f"No se pudo reconstruir Redis desde Cassandra: {e}")
    app.run(debug=True, port=5000)
