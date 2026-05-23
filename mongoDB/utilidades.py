from datetime import date


def fecha_hoy_texto():
    """
    Devuelve la fecha actual en formato texto YYYY-MM-DD para guardar en resenas.
    """
    return date.today().isoformat()


def validar_puntaje(puntaje):
    """
    Valida que una calificacion este dentro del rango permitido: 1 a 5 estrellas.
    """
    puntaje = int(puntaje)

    if puntaje < 1 or puntaje > 5:
        raise ValueError("El puntaje debe estar entre 1 y 5 estrellas.")

    return puntaje


def obtener_siguiente_id(coleccion, campo_id):
    """
    Busca el mayor id existente en una coleccion y devuelve el siguiente.
    """
    ultimo = coleccion.find_one({}, {campo_id: 1}, sort=[(campo_id, -1)])

    if ultimo is None:
        return 1

    return int(ultimo[campo_id]) + 1


def imprimir_documentos(titulo, documentos):
    """
    Imprime una lista de documentos MongoDB sin mostrar el campo interno _id.
    """
    print(f"\n{titulo}")

    documentos = list(documentos)
    if not documentos:
        print("No se encontraron resultados.")
        return documentos

    for documento in documentos:
        texto = " | ".join(
            f"{clave}: {valor}"
            for clave, valor in documento.items()
            if clave != "_id"
        )
        print(f"- {texto}")

    return documentos
