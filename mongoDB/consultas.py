import re

from conexion import obtener_coleccion
from utilidades import imprimir_documentos


def buscar_usuario_por_username(username):
    """
    Busca un usuario puntual por username dentro de la coleccion usuarios.
    """
    return obtener_coleccion("usuarios").find_one({"username": username})


def validar_credenciales(username, password):
    """
    Login MongoDB: usa find_one para validar coincidencia de username y password.
    """
    usuario = obtener_coleccion("usuarios").find_one(
        {"username": username, "password": password},
        {"password": 0}
    )

    if usuario:
        print(f"\nLogin valido para {username}.")
        return usuario

    print(f"\nLogin invalido para {username}.")
    return None


def buscar_restaurantes_por_filtros(tipo_comida=None, calificacion_minima=None, barrio=None, limite=10):
    """
    Busca restaurantes aplicando filtros opcionales por tipo de comida,
    calificacion minima y barrio/zona.
    """
    filtro = {}

    if tipo_comida:
        filtro["tipo_comida"] = {"$regex": f"^{re.escape(tipo_comida)}$", "$options": "i"}

    if calificacion_minima is not None:
        filtro["calificacion_promedio"] = {"$gte": float(calificacion_minima)}

    if barrio:
        filtro["barrio"] = {"$regex": f"^{re.escape(barrio)}$", "$options": "i"}

    restaurantes = obtener_coleccion("restaurantes").find(
        filtro,
        {
            "_id": 0,
            "restaurante_id": 1,
            "nombre": 1,
            "tipo_comida": 1,
            "barrio": 1,
            "direccion": 1,
            "calificacion_promedio": 1,
            "platos": 1
        }
    ).sort("calificacion_promedio", -1).limit(limite)

    return imprimir_documentos("Restaurantes encontrados por filtros", restaurantes)


def ver_mis_resenas(dni_usuario, limite=10):
    """
    Muestra las reseñas escritas por un usuario, con nombre del restaurante.
    """
    pipeline = [
        {"$match": {"dni_usuario": int(dni_usuario), "comentario": {"$ne": ""}}},
        {"$sort": {"fecha": -1, "resena_id": -1}},
        {"$limit": limite},
        {
            "$lookup": {
                "from": "restaurantes",
                "localField": "restaurante_id",
                "foreignField": "restaurante_id",
                "as": "restaurante"
            }
        },
        {"$unwind": "$restaurante"},
        {
            "$project": {
                "_id": 0,
                "resena_id": 1,
                "restaurante_id": 1,
                "restaurante": "$restaurante.nombre",
                "comentario": 1,
                "puntaje": 1,
                "fecha": 1
            }
        }
    ]

    documentos = obtener_coleccion("resenas").aggregate(pipeline)
    return imprimir_documentos(f"Mis resenas - usuario {dni_usuario}", documentos)


def ver_mis_calificaciones(dni_usuario, limite=10):
    """
    Muestra las calificaciones de 1 a 5 estrellas hechas por un usuario.
    """
    pipeline = [
        {"$match": {"dni_usuario": int(dni_usuario)}},
        {"$sort": {"fecha": -1, "resena_id": -1}},
        {"$limit": limite},
        {
            "$lookup": {
                "from": "restaurantes",
                "localField": "restaurante_id",
                "foreignField": "restaurante_id",
                "as": "restaurante"
            }
        },
        {"$unwind": "$restaurante"},
        {
            "$project": {
                "_id": 0,
                "resena_id": 1,
                "restaurante_id": 1,
                "restaurante": "$restaurante.nombre",
                "puntaje": 1,
                "fecha": 1
            }
        }
    ]

    documentos = obtener_coleccion("resenas").aggregate(pipeline)
    return imprimir_documentos(f"Mis calificaciones - usuario {dni_usuario}", documentos)


def ver_resenas_de_restaurante(restaurante_id, limite=10):
    """
    Lista las resenas de un restaurante y trae el username del autor con $lookup.
    """
    pipeline = [
        {"$match": {"restaurante_id": int(restaurante_id)}},
        {"$sort": {"fecha": -1, "resena_id": -1}},
        {"$limit": limite},
        {
            "$lookup": {
                "from": "usuarios",
                "localField": "dni_usuario",
                "foreignField": "dni_usuario",
                "as": "usuario"
            }
        },
        {"$unwind": "$usuario"},
        {
            "$project": {
                "_id": 0,
                "resena_id": 1,
                "usuario": "$usuario.username",
                "puntaje": 1,
                "comentario": 1,
                "fecha": 1
            }
        }
    ]

    documentos = obtener_coleccion("resenas").aggregate(pipeline)
    return imprimir_documentos(f"Resenas del restaurante {restaurante_id}", documentos)


def ver_calificacion_restaurante(restaurante_id):
    """
    Consulta el promedio de estrellas guardado en el documento del restaurante.
    """
    restaurante = obtener_coleccion("restaurantes").find_one(
        {"restaurante_id": int(restaurante_id)},
        {
            "_id": 0,
            "restaurante_id": 1,
            "nombre": 1,
            "tipo_comida": 1,
            "barrio": 1,
            "calificacion_promedio": 1
        }
    )

    documentos = [restaurante] if restaurante else []
    return imprimir_documentos(f"Calificacion del restaurante {restaurante_id}", documentos)


def ejecutar_consultas(dni_usuario=44000001, restaurante_id=1):
    """
    Ejecuta las consultas MongoDB que cubren resenas y calificaciones del TPO.
    """
    print("\n==============================")
    print("EJECUCION DE CONSULTAS MONGODB")
    print("==============================")

    buscar_restaurantes_por_filtros(
        tipo_comida="Mexicana",
        calificacion_minima=3,
        barrio="Flores"
    )
    ver_mis_resenas(dni_usuario)
    ver_mis_calificaciones(dni_usuario)
    ver_calificacion_restaurante(restaurante_id)
    ver_resenas_de_restaurante(restaurante_id)

def main():
    ver_mis_resenas(dni_usuario=44000001)
