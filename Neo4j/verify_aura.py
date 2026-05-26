from conexion import obtener_driver

if __name__ == '__main__':
    d = obtener_driver()
    s = d.session()

    def run(q):
        return s.run(q)

    print('Nodos:', run('MATCH (n) RETURN count(n) AS c').single()['c'])
    print('Usuarios:', run("MATCH (u:Usuario) RETURN count(u) AS c").single()['c'])
    print('Restaurantes:', run("MATCH (r:Restaurante) RETURN count(r) AS c").single()['c'])
    print('Platos:', run("MATCH (p:Plato) RETURN count(p) AS c").single()['c'])
    print('SIGUE:', run("MATCH ()-[x:SIGUE]->() RETURN count(x) AS c").single()['c'])
    print('VISITO:', run("MATCH ()-[x:VISITO]->() RETURN count(x) AS c").single()['c'])
    print('PIDIO:', run("MATCH ()-[x:PIDIO]->() RETURN count(x) AS c").single()['c'])
    print('CALIFICO:', run("MATCH ()-[x:CALIFICO]->() RETURN count(x) AS c").single()['c'])
    print('OFRECE:', run("MATCH ()-[x:OFRECE]->() RETURN count(x) AS c").single()['c'])

    print('\n5 usuarios:')
    for r in run("MATCH (u:Usuario) RETURN u.username AS username, u.nombre AS nombre, u.apellido AS apellido LIMIT 5"):
        print('-', r['username'], r['nombre'], r['apellido'])

    print('\n5 restaurantes:')
    for r in run("MATCH (r:Restaurante) RETURN r.restaurante_id AS id, r.nombre AS nombre, r.tipo_comida AS tipo LIMIT 5"):
        print('-', r['id'], r['nombre'], r['tipo'])

    print('\nVitoNava sigue:')
    for r in run("MATCH (u:Usuario {username:'VitoNava'})-[:SIGUE]->(v:Usuario) RETURN v.username AS username LIMIT 10"):
        print('-', r['username'])

    print('\nVitoNava visitas:')
    for r in run("MATCH (u:Usuario {username:'VitoNava'})-[:VISITO]->(r:Restaurante) RETURN r.nombre AS nombre LIMIT 10"):
        print('-', r['nombre'])

    s.close()
    d.close()
