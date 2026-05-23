**INGENIERÍA DE DATOS II**  
**Trabajo Práctico Integrador**  
**STARVY**

## **Integrantes:** 

* Lan Franco \- LU1188365  
* Gimenez Santiago \- LU1162528  
* Giordano Nicolás Luca \- LU1188062  
* Nava Vito  \- LU1187177  
* **Mannino Valentina \- LU1190321 (PM)**   
* Umansky Nicolás \- LU1188098

**Profesora:** Dra. Ing. Martínez Roxana 

**Universidad:** Universidad Argentina de la Empresa

**Facultad de Ingeniería**: Ingeniería en Informática

**Número de grupo:** 07 

**Año:** 2026  
![][image1]

**MongoDB**

1. Login y Signup  
   1. Insert para registrar (mail- contraseña- username)  
   2. *find* para validar la coincidencia del usuario  
        
2. Catálogo de restaurantes y platos  
   1. Agregar platos a un restaurant (no se ve en el front, todo por motor)  
   2. Buscar restaurantes por filtros:    
      1. TIPO DE COMIDA  
      2. CALIFICACIÓN  
      3. BARRIO / ZONA

3. Reseñas y calificación (stars)   
   1. Ver mis reseñas  
   2. Ver mis calificaciones  
   3. Insertar una calificación de 1 al 5 estrellas al restaurante  
   4. Insertar una reseña escrita sobre ese restaurante

Para la implementación en MongoDB se utilizó la base de datos starvy, conectada desde Python mediante la librería PyMongo. Además, se usó Pandas para leer los archivos JSON del dataset y convertirlos en documentos listos para insertar en las colecciones.

Se trabajó con tres colecciones principales:

\- usuarios  
\- restaurantes  
\- resenas

La colección usuarios almacena la información básica de cada usuario de la aplicación, incluyendo dni\_usuario, nombre, apellido, username, password y mail. Estos datos se cargan desde el archivo usuarios.json.

La colección restaurantes almacena los datos principales de cada restaurante, como restaurante\_id, nombre, tipo\_comida, barrio, direccion y calificacion\_promedio. Además, en esta colección se decidió anidar los platos dentro de cada restaurante. Para eso, se leen los archivos restaurantes.json y platos.json, y luego se relacionan los platos con su restaurante correspondiente mediante el campo restaurante\_id. De esta forma, cada documento de restaurante contiene un arreglo llamado platos, donde se guardan todos los platos asociados a ese restaurante.

Ejemplo de estructura de restaurante:

{  
  "restaurante\_id": 1,  
  "nombre": "Qnekt",  
  "tipo\_comida": "Mexicana",  
  "barrio": "Flores",  
  "direccion": "848 Reed Street",  
  "calificacion\_promedio": 3.1,  
  "platos": \[  
    {  
      "plato\_id": 1,  
      "restaurante\_id": 1,  
      "plato\_nombre": "Milanesa completa",  
      "tipo\_comida": "Pastas",  
      "precio": 3500,  
      "disponible": true  
    }  
  \]  
}

La colección resenas almacena las reseñas y calificaciones realizadas por los usuarios sobre los restaurantes. Cada reseña contiene resena\_id, dni\_usuario, restaurante\_id, puntaje, comentario y fecha. Esta colección se mantiene separada porque relaciona a usuarios con restaurantes y permite consultar las opiniones o calificaciones de forma independiente.

También se implementó una función llamada recalcularCalificacionPromedio(restaurante\_id), que busca todas las reseñas asociadas a un restaurante, calcula el promedio de los puntajes y actualiza el campo calificacion\_promedio dentro del documento correspondiente en la colección restaurantes.

Además, se agregaron funciones para registrar nuevos usuarios, restaurantes y reseñas. En el caso de registrar una reseña, luego de insertar el documento en la colección resenas, se recalcula automáticamente la calificación promedio del restaurante afectado.

Esta estructura aprovecha el modelo documental de MongoDB: los platos se guardan anidados dentro del restaurante porque pertenecen directamente a él, mientras que las reseñas se guardan en una colección separada porque dependen tanto del usuario como del restaurante.

**Neo4j**  
**Entidades y relaciones:**  
Podemos observar en este grafico de prueba en Neo4j como existen usuarios y restaurantes. Los restaurantes pueden ofrecer platos que pueden consumir o pedir los usuarios. Estos también pueden seguirse entre sí y calificar a los restaurantes.   
La estructura quedaría así:  
(Usuario)-\[:SIGUE\]-\>(Usuario)  
(Usuario)-\[:VISITO\]-\>(Restaurante)  
(Usuario)-\[:CALIFICO\]-\>(Restaurante)  
(Restaurante)-\[:OFRECE\]-\>(Plato)  
(Usuario)-\[:PIDIO\]-\>(Plato)

**![][image2]**

4. Red social de usuarios que se siguen   
   1. Seguir a un usuario

MATCH (yo:Usuario {username: "valen"})  
MATCH (otro:Usuario {username: "sofi"})  
WHERE yo \<\> otro  
MERGE (yo)-\[s:SIGUE\]-\>(otro)  
ON CREATE SET s.desde \= date()  
RETURN yo.username, otro.username, s.desde;

2. Dejar de seguir a un usuario

MATCH (yo:Usuario {username: "valen"})-\[s:SIGUE\]-\>(otro:Usuario {username: "mica"})  
DELETE s  
RETURN yo.username AS usuario, otro.username AS dejo\_de\_seguir\_a;

3. Buscar usuarios por nombre de usuario 

MATCH (u:Usuario)  
WHERE toLower(u.username) CONTAINS toLower("so")  
RETURN u.id, u.nombre, u.username  
ORDER BY u.username;

5. Recomendaciones tipo “tus amigos fueron acá”   
   1. Ver las reseñas de tus amigos 

MATCH (yo:Usuario {username: "valen"})-\[:SIGUE\]-\>(amigo:Usuario)  
MATCH (amigo)-\[c:CALIFICO\]-\>(r:Restaurante)  
WHERE c.comentario IS NOT NULL  
RETURN amigo.username, r.nombre, c.puntaje, c.comentario, c.fecha  
ORDER BY c.fecha DESC;

2. Ver las calificaciones de tus amigos

MATCH (yo:Usuario {username: "valen"})-\[:SIGUE\]-\>(amigo:Usuario)  
MATCH (amigo)-\[c:CALIFICO\]-\>(r:Restaurante)  
RETURN amigo.username, r.nombre, c.puntaje, c.fecha  
ORDER BY c.fecha DESC, c.puntaje DESC;

3. Ver a dónde fueron tus amigos

MATCH (yo:Usuario {username: "valen"})-\[:SIGUE\]-\>(amigo:Usuario)  
MATCH (amigo)-\[v:VISITO\]-\>(r:Restaurante)  
RETURN amigo.username, r.nombre, r.barrio, r.tipo\_comida, v.fecha  
ORDER BY v.fecha DESC;

4. Recomendaciones de restaurante basadas en lo que les gusto a tus amigos (filtrado colaborativo)

MATCH (yo:Usuario {username: "valen"})-\[:SIGUE\]-\>(amigo:Usuario)  
MATCH (amigo)-\[c:CALIFICO\]-\>(r:Restaurante)  
WHERE c.puntaje \>= 4  
AND NOT EXISTS {  
MATCH (yo)-\[:VISITO\]-\>(r)  
}  
RETURN  
r.nombre AS restaurante\_recomendado,  
r.barrio AS barrio,  
r.tipo\_comida AS tipo\_comida,  
count(DISTINCT amigo) AS cantidad\_amigos\_que\_lo\_recomiendan,  
collect(DISTINCT amigo.username) AS recomendado\_por,  
round(avg(c.puntaje), 2) AS promedio\_calificacion\_amigos  
ORDER BY cantidad\_amigos\_que\_lo\_recomiendan DESC, promedio\_calificacion\_amigos DESC;

5. Recomendaciones de restaurante basadas en tus calificaciones previas (filtrado basado en contenido). Agregamos un restaurante y una calificación al usuario “valen” para ejecutar esta consulta.

MATCH (yo:Usuario {username: "valen"})-\[c:CALIFICO\]-\>(rGustado:Restaurante)  
WHERE c.puntaje \>= 4

MATCH (recomendado:Restaurante)  
WHERE recomendado \<\> rGustado  
AND NOT EXISTS {  
MATCH (yo)-\[:VISITO\]-\>(recomendado)  
}  
AND (  
recomendado.tipo\_comida \= rGustado.tipo\_comida  
OR recomendado.barrio \= rGustado.barrio  
)

WITH  
recomendado,  
collect(DISTINCT rGustado.nombre) AS basado\_en,  
count(DISTINCT rGustado) AS coincidencias

RETURN  
recomendado.nombre AS restaurante\_recomendado,  
recomendado.barrio AS barrio,  
recomendado.tipo\_comida AS tipo\_comida,  
recomendado.rating\_promedio AS rating\_promedio,  
basado\_en,  
coincidencias

ORDER BY coincidencias DESC, rating\_promedio DESC;

**Cassandra**

6. Promociones activas y visitas registradas

USO:   
Utilizamos Cassandra para guardar cosas que pasan todo el tiempo (visitas, promociones, fechas, métricas, comida vendida, etc). El modelado se diseña por consulta, primero pensamos qué queremos preguntar y luego creamos una tabla preparada para responder rápidamente a esa pregunta.  
K: clave principal de la búsqueda.  
C: ordenar dentro de la carpeta. Flecha arriba: ascendente (menor a mayor) / Flecha abajo: descendente, mayor a menor.  
En Cassandra no conviene hacer JOINs ni buscar por cualquier campo para que las consultas sean rápidas, por eso Starvy duplica datos de forma controlada: una promoción se guarda en dos tablas de lectura y una visita alimenta tablas por restaurante, por usuario y una métrica diaria.  
Para eso, fue necesario realizar el MODELADO FÍSICO.

- Q1:  Ver promociones activas por restaurante / TABLA: promociones\_por\_restaurante / CLAVE: restaurante\_id (busca por restaurante).  
- Q2: Ver promociones activas por fecha y barrio / TABLA: promociones\_activas\_por\_fecha / CLAVE: dia\_vigencia \- barrio (puede buscar por dia y barrio).  
- Q3: Ver visitas registradas en un día de un restaurante / TABLA: visitas\_por\_restaurante\_dia / CLAVE:  restaurante\_id \- fecha (encuentra las visitas de un restaurante en una fecha).  
- Q4: Ver historial de visitas por usuario / TABLA: visitas\_por\_usuario\_fecha / CLAVE: dni\_usuario \- fecha (ver el historial del usuario por día).  
- Q5: Ver comida/plato más vendido hoy / TABLA: metricas\_restaurante\_por\_dia / ORDENA POR: cantidad\_vendida DESC (plato mas vendido aparece primero).  
- Q6: Insertar nueva visita / insertar nueva promoción / CREAR NUEVA PROMOCION: promociones\_por\_restaurante \- promociones\_activas\_por\_fecha // REGISTRAR NUEVA VISITA: visitas\_por\_restaurante\_dia \- visitas\_por\_usuario\_fecha \- metricas\_restaurante\_por\_dia

MODELO FÍSICO:  
![][image3]

	Además, realizamos el Modelo Genérico, que muestra el flujo general de consultas y escrituras en Cassandra para responder la parte de promociones activas y visitas registradas dentro de Starvy.  
Arriba están las queries de lectura, es decir, las preguntas que la app necesita responder.   
	En el medio están las tablas Cassandra. Cada query baja directamente a una tabla (ya que modelamos pensando en qué consulta queremos resolver).   
	Abajo está Q6 \- Escrituras, representa cuando se inserta una nueva promoción o visita. Una misma escritura puede guardarse en varias tablas para que después las lecturas sean más rápidas. Es así, porque Cassandra se usa para escenarios de alto volumen y escalabilidad, como logs, visitas, promociones y métricas. 

MODELO GENÉRICO:  
![][image4]

Implementación en Cassandra:

* CREAMOS EL KEYSPACE: 

![][image5]

* CREAMOS LAS TABLAS: 

Q1 TABLA promociones\_por\_restaurante  
![][image6]  
Q2 TABLA promociones\_activas\_por\_fecha  
![][image7]  
Q3 TABLA visitas\_por\_restaurante\_dia

Q4 TABLA visitas\_por\_usuario\_fecha  
![][image8]  
Q5 TABLA metricas\_restaurante\_por\_dia  
![][image9]

* VERIFICAMOS QUE SE HAYAN CREADO:

![][image10]

* INSERTAMOS DATOS DE PRUEBA: 

![][image11]![][image12]![][image13]

* EJECUTAMOS LAS QUERIES:  
  1. Ver promociones activas por restaurante (promociones\_por\_restaurante) Q1

![][image14]

2. *Ver promociones activas por fecha y barrio (promociones\_activas\_por\_fecha) Q2*

*![][image15]*

3. Ver visitas registradas en un día de un restaurante (visitas\_por\_restaurante\_dia) Q3

![][image16]

4. *Ver historial de visitas por usuario (visitas\_por\_usuario\_fecha) Q4*

*![][image17]*

5. Ver que comida fue la más vendida hoy (metricas\_restaurante\_por\_dia) Q5

![][image18]

6. ESCRITURAS: 

Insertar una nueva visita (nueva visita → visitas\_por\_restaurante\_dia \+ visitas\_por\_usuario\_fecha \+ metricas\_restaurante\_por\_dia ) // Insertar una nueva promoción (nueva promocion → promociones\_por\_restaurante \+ promociones\_activas\_por\_fecha) Q6  
![][image19]  
Para validar el modelo físico propuesto, se implementó el keyspace starvy en Cassandra y se crearon cinco tablas orientadas a consultas. Luego se insertaron datos de prueba y se ejecutaron consultas de lectura para verificar que cada tabla respondiera a la query para la cual fue diseñada. Además, se realizó la operación de escritura mediante la inserción de una nueva promoción y una nueva visita.

Conexión con Python:  
Para continuar con la implementación, se desarrolló un script en Python dentro de la carpeta Cassandra del proyecto. Este script permite conectar la aplicación con Apache Cassandra, crear el keyspace `starvy`, crear las tablas definidas en el modelado físico y cargar los datos provenientes de los archivos `promociones.json` y `visitas.json`.  
![][image20]  
Verificamos que Python esté instalado, activamos el entorno virtual e instalamos Cassandra Driver.  
![][image21]  
Creamos/actualizamos el archivo requirements con el comando pip freeze \> requirements.txt  
Conexión entre Python y Cassandra:   
![][image22]

Evidencia de conexión e inicialización de Cassandra desde Python  
Se implementó un script en Python dentro de la carpeta Cassandra del proyecto Starvy. El script permite conectarse a Apache Cassandra ejecutándose en Docker, crear el keyspace `starvy`, crear las tablas definidas en el modelado físico y verificar desde Python que dichas tablas existen. Así se confirma la conexión entre la aplicación y Cassandra.  
![][image23]

Carga del dataset de promociones y visitas en Cassandra desde Python:  
![][image24]

Ejecución de consultas Cassandra desde Python:  
![][image25]  
Una vez cargado el dataset en Cassandra, se ejecutaron desde Python las consultas definidas en el modelado físico. Cada consulta accede directamente a una tabla diseñada para responder una necesidad específica de lectura: promociones por restaurante, promociones por fecha y barrio, visitas por restaurante y día, historial de visitas por usuario y plato más vendido por restaurante y fecha. De esta manera se evidencia el modelado por consulta propio de Cassandra y la interacción entre la aplicación Python y la base de datos.

Escrituras en Cassandra:  
![][image26]

CÓMO SE DIVIDEN LOS ARCHIVOS EN CASSANDRA:   
Dividimos el archivo principal de Cassandra en módulos para separar responsabilidades: conexión, configuración, creación del esquema, carga del dataset, consultas y escrituras. Esto permite que el código sea más legible, mantenible y fácil de explicar, sin modificar la lógica de base de datos ya implementada.

* [app.p](http://app.py)y			→ archivo principal  
* config.py           	→ configuración: host, puerto, keyspace, ruta dataset  
* conexion.py       	→ conexión con Cassandra  
* utilidades.py       	→ funciones auxiliares: fechas, horas, JSON  
* esquema.py          	→ keyspace, tablas, verificar tablas  
* carga\_dataset.py    	→ carga promociones, visitas y métricas  
* consultas.py        	→ Q1, Q2, Q3, Q4, Q5  
* escrituras.py      	→ Q6: nueva promo y nueva visita

Buenas prácticas aplicadas en Cassandra:   
Para evitar duplicación accidental durante las pruebas, el script limpia las tablas antes de volver a cargar el dataset. También se utilizaron consultas preparadas desde Python para insertar los datos de manera ordenada y consistente. El entorno virtual `.venv` no se sube al repositorio, mientras que las dependencias se documentan en `requirements.txt`, donde queda registrada la librería `cassandra-driver`.  
En el modelado se mantuvo el criterio de Cassandra: no se realizan JOINs ni búsquedas por campos arbitrarios. Cada tabla fue diseñada para responder una consulta específica, aceptando duplicación controlada de datos a cambio de lecturas más rápidas.

**Redis**

7. Caché de restaurantes populares y sesiones activas   
   1. Almacenar en memoria sesiones activas de usuarios  
   2. Ver sesiones activas   
   3. GET Ranking de restaurantes más visitados (SORTED SET)  
   4. GET Ranking de tipos de comida (tipo top de las hamburguesas más pedidas)   
   5. Últimas búsquedas de un usuario (LPUSH)
