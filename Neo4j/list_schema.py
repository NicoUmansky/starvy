from conexion import obtener_driver

if __name__ == '__main__':
    d = obtener_driver()
    s = d.session()

    print('Constraints:')
    try:
        result = s.run("SHOW CONSTRAINTS YIELD name, type RETURN name, type ORDER BY name")
        for r in result:
            print('-', r['name'], '|', r['type'])
    except Exception:
        # Fallback a una forma más simple
        result = s.run("SHOW CONSTRAINTS")
        for r in result:
            print('-', r['name'])

    print('\nIndexes:')
    try:
        result = s.run("SHOW INDEXES YIELD name, type, entityType RETURN name, type, entityType ORDER BY name")
        for r in result:
            print('-', r['name'], '|', r['type'], '|', r['entityType'])
    except Exception:
        result = s.run("SHOW INDEXES")
        for r in result:
            print('-', r['name'])

    s.close()
    d.close()
