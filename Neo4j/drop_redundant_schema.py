from conexion import obtener_driver

DROPS = [
    "DROP CONSTRAINT plato_id IF EXISTS",
    "DROP CONSTRAINT restaurante_id IF EXISTS",
    "DROP CONSTRAINT usuario_id IF EXISTS",
    "DROP INDEX index_1b9dcc97 IF EXISTS",
    "DROP INDEX index_460996c0 IF EXISTS",
    "DROP INDEX plato_id IF EXISTS",
    "DROP INDEX restaurante_id IF EXISTS",
    "DROP INDEX usuario_id IF EXISTS",
]

if __name__ == '__main__':
    d = obtener_driver()
    s = d.session()

    for stmt in DROPS:
        try:
            print('Ejecutando:', stmt)
            s.run(stmt)
            print('OK')
        except Exception as e:
            print('Error al ejecutar:', stmt, '|', e)

    s.close()
    d.close()
