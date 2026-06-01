import importlib.util
import sys
from pathlib import Path


def _cargar_consultas_redis():
    """
    Carga consultas.py desde la carpeta Redis.
    Evita conflictos con otros modulos llamados consultas.py.
    """
    redis_dir = Path(__file__).resolve().parent
    ruta_consultas = redis_dir / "consultas.py"

    if str(redis_dir) not in sys.path:
        sys.path.insert(0, str(redis_dir))

    spec = importlib.util.spec_from_file_location("redis_consultas_app", ruta_consultas)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_consultas = _cargar_consultas_redis()

crear_sesion = _consultas.crear_sesion
cerrar_sesion = _consultas.cerrar_sesion
verificar_sesion = _consultas.verificar_sesion
ver_sesiones_activas = _consultas.ver_sesiones_activas
registrar_visita = _consultas.registrar_visita
ver_ranking_restaurantes = _consultas.ver_ranking_restaurantes
ver_ranking_tipos_comida = _consultas.ver_ranking_tipos_comida
registrar_busqueda = _consultas.registrar_busqueda
ver_ultimas_busquedas = _consultas.ver_ultimas_busquedas


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
