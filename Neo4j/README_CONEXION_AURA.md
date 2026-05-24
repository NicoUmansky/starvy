# Conexion Neo4j Aura

La configuracion de Aura se lee desde `Neo4j/.env`.
Ese archivo no se sube a Git porque contiene credenciales.

## Archivo local

Crear `Neo4j/.env` con este formato:

```env
NEO4J_URI=neo4j+s://b7da37c0.databases.neo4j.io
NEO4J_USERNAME=b7da37c0
NEO4J_PASSWORD=tu_password_de_aura
NEO4J_DATABASE=b7da37c0
AURA_INSTANCEID=b7da37c0
AURA_INSTANCENAME=StarvyNeo
NEO4J_CONNECTION_TIMEOUT=10
```

## Instalar driver

Para trabajar solo con Neo4j:

```powershell
python -m pip install -r Neo4j/requirements-neo4j.txt
```

Si se usa otro interprete:

```powershell
py -3.13 -m pip install -r Neo4j/requirements-neo4j.txt
```

## Probar conexion sin cargar datos

Esta prueba solo ejecuta un `RETURN`, no modifica la base:

```powershell
python -c "import sys; sys.path.insert(0, 'Neo4j'); from conexion import probar_conexion; probar_conexion()"
```

## Cargar dataset

Cuando la instancia Aura este activa, ejecutar:

```powershell
python Neo4j/appNeo4j.py
```

Nota: `appNeo4j.py` limpia el grafo antes de cargar el dataset.
