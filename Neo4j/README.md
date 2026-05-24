# Modulo Neo4j - STARVY

Este modulo implementa el grafo social y gastronomico de STARVY usando Neo4j.
El objetivo es modelar usuarios, restaurantes, platos, visitas, resenas y relaciones sociales para poder ejecutar consultas de perfil, recomendaciones y escrituras sobre el grafo.

## Modelo del grafo

### Nodos principales

- `Usuario`: representa a cada usuario de la aplicacion. Usa `dni_usuario` como identificador principal y `username` como identificador social.
- `Restaurante`: representa los restaurantes disponibles. Usa `restaurante_id` como identificador.
- `Plato`: representa los platos ofrecidos por cada restaurante. Usa `plato_id` como identificador.

### Relaciones principales

- `(:Usuario)-[:SIGUE]->(:Usuario)`: modela la red social entre usuarios.
- `(:Usuario)-[:VISITO]->(:Restaurante)`: registra una visita de un usuario a un restaurante.
- `(:Usuario)-[:PIDIO]->(:Plato)`: registra el plato pedido en una visita.
- `(:Usuario)-[:CALIFICO]->(:Restaurante)`: registra una resena/calificacion hecha por un usuario.
- `(:Restaurante)-[:OFRECE]->(:Plato)`: vincula cada restaurante con sus platos.

## Archivos del modulo

### `config.py`

Centraliza la configuracion del modulo.

Responsabilidades:

- Define la ruta base del proyecto y la carpeta `DATASET`.
- Carga variables de entorno desde `.env` del proyecto o desde `Neo4j/.env`.
- Configura los datos de conexion a Neo4j Aura:
  - `NEO4J_URI`
  - `NEO4J_USERNAME` o `NEO4J_USER`
  - `NEO4J_PASSWORD`
  - `NEO4J_DATABASE`
  - `NEO4J_CONNECTION_TIMEOUT`
- Guarda metadatos de la instancia Aura, como `AURA_INSTANCEID` y `AURA_INSTANCENAME`.

El archivo `Neo4j/.env` contiene credenciales reales y no debe subirse al repositorio.

### `conexion.py`

Contiene la capa de conexion con Neo4j usando el driver oficial `neo4j`.

Funciones principales:

- `obtener_driver()`: crea el driver de Neo4j con URI, usuario, password y timeout.
- `obtener_session(driver)`: abre una sesion contra la base configurada.
- `probar_conexion()`: ejecuta una consulta minima `RETURN` para validar conectividad.

Tambien valida que existan usuario y password antes de intentar conectarse, para evitar errores poco claros.

### `utilidades.py`

Agrupa funciones auxiliares usadas por la carga.

Funciones principales:

- `leer_json(nombre_archivo)`: lee archivos JSON desde la carpeta `DATASET`.
- `normalizar_hora(hora_texto)`: convierte horas con formato `HH:MM` al formato `HH:MM:SS`, requerido por `localtime()` en Neo4j.

### `esquema.py`

Define restricciones e indices del grafo.

Funciones principales:

- `crear_constraints_e_indices()`: crea constraints e indices si todavia no existen.
- `verificar_esquema()`: muestra constraints e indices existentes como evidencia de configuracion.

Constraints creadas:

- `usuario_dni_unico`: evita usuarios duplicados por `dni_usuario`.
- `usuario_username_unico`: evita usuarios duplicados por `username`.
- `restaurante_id_unico`: evita restaurantes duplicados por `restaurante_id`.
- `plato_id_unico`: evita platos duplicados por `plato_id`.

Indices creados:

- `restaurante_tipo_comida_idx`: acelera busquedas por tipo de comida.
- `restaurante_barrio_idx`: acelera busquedas por barrio.

### `carga_dataset.py`

Carga el dataset JSON en Neo4j.

Funciones principales:

- `limpiar_grafo()`: borra nodos y relaciones existentes, conservando constraints e indices.
- `cargar_usuarios(session)`: carga nodos `Usuario`.
- `cargar_restaurantes(session)`: carga nodos `Restaurante`.
- `cargar_platos(session)`: carga nodos `Plato` y relaciones `OFRECE`.
- `cargar_visitas(session)`: carga relaciones `VISITO` y `PIDIO`.
- `cargar_resenas(session)`: carga relaciones `CALIFICO`.
- `cargar_red_social(session)`: carga relaciones `SIGUE` definidas en `RELACIONES_SIGUE`.
- `cargar_dataset()`: ejecuta la carga completa en orden.

Orden de carga:

1. Usuarios.
2. Restaurantes.
3. Platos y relaciones `OFRECE`.
4. Visitas y relaciones `PIDIO`.
5. Resenas como relaciones `CALIFICO`.
6. Red social con relaciones `SIGUE`.

Conteos esperados despues de una carga completa:

- `Usuario`: 80
- `Restaurante`: 40
- `Plato`: 180
- `OFRECE`: 180
- `VISITO`: 390
- `PIDIO`: 390
- `CALIFICO`: 250
- `SIGUE`: 26

Nota: `promociones.json` existe en el dataset general, pero este modulo Neo4j no lo carga actualmente en el grafo.

### `consultas.py`

Implementa consultas de lectura sobre el grafo.

Responsabilidades:

- Mostrar perfil social y gastronomico de un usuario.
- Listar usuarios seguidos y seguidores.
- Sugerir usuarios para seguir mediante amigos de amigos.
- Recomendar restaurantes visitados por amigos.
- Recomendar restaurantes bien calificados por amigos.
- Recomendar restaurantes por usuarios similares.
- Recomendar restaurantes por contenido, usando tipo de comida y barrio.
- Explicar caminos de recomendacion.

Funciones destacadas:

- `consultar_perfil_usuario(username)`
- `consultar_usuarios_que_sigue(username)`
- `consultar_seguidores(username)`
- `sugerir_usuarios_para_seguir(username, limite=5)`
- `recomendar_visitados_por_amigos(username, limite=5)`
- `recomendar_bien_calificados_por_amigos(username, limite=5)`
- `recomendar_por_usuarios_similares(username, limite=5)`
- `recomendar_por_contenido(username, limite=5)`
- `explicar_camino_de_recomendacion(username, limite=5)`
- `ejecutar_consultas(username)`

### `escrituras.py`

Implementa operaciones que modifican el grafo.

Funciones principales:

- `seguir_usuario(username_origen, username_destino)`: crea una relacion `SIGUE`.
- `dejar_de_seguir_usuario(username_origen, username_destino)`: elimina una relacion `SIGUE`.
- `registrar_visita_y_calificacion(username, restaurante_id, puntaje, comentario)`: registra una visita nueva, el plato pedido y una calificacion.
- `ejecutar_escrituras(username)`: ejecuta una secuencia de escrituras de demostracion y luego consulta el estado actualizado.

Las escrituras agregan propiedades `origen: 'escritura_python'` en las relaciones creadas desde Python para diferenciarlas del dataset inicial.

### `appNeo4j.py`

Es el punto de entrada principal para ejecutar el flujo completo de Neo4j.

Flujo de ejecucion:

1. Prueba la conexion con Neo4j.
2. Crea constraints e indices.
3. Limpia el grafo.
4. Carga el dataset.
5. Verifica el esquema.
6. Ejecuta consultas de demostracion.
7. Ejecuta escrituras de demostracion.

Importante: este script llama a `limpiar_grafo()`, por lo que borra todos los nodos y relaciones antes de cargar nuevamente el dataset.

### `requirements-neo4j.txt`

Lista la dependencia minima para trabajar con Neo4j:

```txt
neo4j==5.28.1
```

Se separo del `requirements.txt` general para poder instalar solo el driver de Neo4j sin depender de otros motores del proyecto.

### `README_CONEXION_AURA.md`

Documenta especificamente como configurar y probar la conexion con Neo4j Aura.

Incluye:

- Formato esperado para `Neo4j/.env`.
- Comando para instalar el driver.
- Comando para probar conexion sin modificar datos.
- Comando para ejecutar la carga completa.

## Variables de entorno esperadas

El archivo local `Neo4j/.env` debe tener este formato:

```env
NEO4J_URI=neo4j+s://b7da37c0.databases.neo4j.io
NEO4J_USERNAME=b7da37c0
NEO4J_PASSWORD=tu_password_de_aura
NEO4J_DATABASE=b7da37c0
NEO4J_CONNECTION_TIMEOUT=10
AURA_INSTANCEID=b7da37c0
AURA_INSTANCENAME=StarvyNeo
```

No incluir credenciales reales en archivos versionados.

## Como ejecutar

Instalar solo las dependencias de Neo4j:

```powershell
python -m pip install -r Neo4j/requirements-neo4j.txt
```

Probar conexion sin modificar datos:

```powershell
python -c "import sys; sys.path.insert(0, 'Neo4j'); from conexion import probar_conexion; probar_conexion()"
```

Ejecutar flujo completo:

```powershell
python Neo4j/appNeo4j.py
```

## Consideraciones

- La instancia Aura debe estar activa antes de ejecutar consultas.
- Si Aura esta pausada o la URI no resuelve por DNS, la conexion fallara.
- `appNeo4j.py` limpia el grafo antes de cargar el dataset.
- Las consultas y escrituras usan el usuario demo `VitoNava` por defecto.
- Las constraints usan `IF NOT EXISTS`, por lo que se pueden ejecutar varias veces sin duplicarse.
- La carga usa `MERGE` para nodos y relaciones principales, lo que ayuda a mantener identidad unica segun los campos definidos.
