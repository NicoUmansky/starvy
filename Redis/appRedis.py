from consultas import (
    crear_sesion,
    cerrar_sesion,
    verificar_sesion,
    ver_sesiones_activas,
    registrar_visita,
    ver_ranking_restaurantes,
    ver_ranking_tipos_comida,
    registrar_busqueda,
    ver_ultimas_busquedas,
)


def main():
    print("Conectando Python con Redis...\n")

    print("=== SESIONES ===")
    token = crear_sesion("user_001")
    verificar_sesion("user_001")
    ver_sesiones_activas()
    cerrar_sesion("user_001")
    verificar_sesion("user_001")

    print("\n=== RANKINGS ===")
    registrar_visita("Burger House", "Americana")
    registrar_visita("Sushi Palermo", "Japonesa")
    registrar_visita("Burger House", "Americana")
    ver_ranking_restaurantes()
    ver_ranking_tipos_comida()

    print("\n=== BÚSQUEDAS ===")
    registrar_busqueda("user_001", "sushi palermo")
    registrar_busqueda("user_001", "burger cerca")
    registrar_busqueda("user_001", "pizza vegetariana")
    ver_ultimas_busquedas("user_001")


if __name__ == "__main__":
    main()
