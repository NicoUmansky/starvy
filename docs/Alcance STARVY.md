**Starvy es una red social gastronómica para descubrir restaurantes, platos, precios, promociones y recomendaciones basadas en amigos.**  
Starvy no recomienda solo por popularidad general, sino por confianza social: te muestra dónde comieron tus amigos, qué platos calificaron bien y qué promociones están activas cerca tuyo. 

**MVP de Starvy:**

1. Login de usuarios (mail, contraseña, nombre de usuario) \- **MongoDB**  
2. Catálogo de restaurantes y platos \- **MongoDB**  
   LUPA DE BÚSQUEDA- filtros por   
* tipo de comida  
* calificación   
* barrio / zona

Reseñas y calificación (stars) \-  **MongoDB**

3. Red social de usuarios que se siguen \- **Neo4j**   
4. Recomendaciones tipo “tus amigos fueron acá” (filtrado colaborativo y basado en contenido) \- **Neo4j**   
5. Promociones activas y visitas registradas **\- Cassandra**  
6. Rankings ordenados, sesiones activas y búsquedas recientes**\- Redis**

**EJEMPLOS DE QUERIES PARA CADA PUNTO:**  
FRONT END → UN SOLO PERFIL \- VISTA DE ADMINISTRADOR\!\!  
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

**Neo4j**

4. Red social de usuarios que se siguen   
   1. Seguir a un usuario  
   2. Dejar de seguir a un usuario  
   3. Buscar usuarios por nombre de usuario 

5. Recomendaciones tipo “tus amigos fueron acá”   
   1. Ver las reseñas de tus amigos   
   2. Ver las calificaciones de tus amigos  
   3. Ver a dónde fueron tus amigos  
   4. Recomendaciones de restaurante basadas en lo que les gusto a tus amigos (filtrado colaborativo)  
   5. Recomendaciones de restaurante basadas en tus calificaciones previas (filtrado basado en contenido)  
      

**Cassandra**

6. Promociones activas y visitas registradas  
   1. Ver promociones activas por restaurante   
   2. Ver que comida fue la más vendida hoy  
   3. Ver visitas registradas en un día de un restaurante  
   4. Insertar una nueva visita   
   5. Insertar una nueva promoción 

**Redis**

7. Caché de restaurantes populares y sesiones activas   
   1. Almacenar en memoria sesiones activas de usuarios  
   2. Ver sesiones activas   
   3. GET Ranking de restaurantes más visitados (SORTED SET)  
   4. GET Ranking de tipos de comida (tipo top de las hamburguesas más pedidas)   
   5. Últimas búsquedas de un usuario (LPUSH)  
      

**LENGUAJES:**   
Python → MongoDB \+ Neo4j \+ Redis \+ Cassandra  
Power BI → Dashboard conectado a datos de MongoDB vía API Flask  
\- Un script por motor.  
\- Menú simple por consola para ejecutar operaciones.

**MONGODB- Colecciones que necesitamos:**

* Usuarios   
  * dni  
  * mail  
  * password  
  * username


* Restaurantes (Tienen los platos anidados)  
* Reseñas y calificaciones

**Neo4j- Nodos y relaciones que necesitamos:**  
**NODOS:**

- **Usuario**  
- **Restaurante**  
- **Plato**

**RELACIONES:**

* **(USUARIO) \- \[SIGUE\] \-\> (USUARIO) →** PROPIEDAD: Desde  
* **(USUARIO) \- \[VISITÓ\] \-\> (RESTAURANTE) →** PROPIEDAD: Cuando  
* **(USUARIO) \- \[CALIFICÓ\] \-\> (RESTAURANTE)  →** PROPIEDAD: Puntaje  
* **(RESTAURANTE) \- \[OFRECE\] \-\> (PLATO)**  
* **(USUARIO) \- \[PIDIÓ\] \-\> (PLATO)**

**Cassandra- Tablas que necesitamos (modelado por consulta):** 

* **visitas\_por\_restaurante**  
* **visitas\_por\_usuario**  
* **promociones\_por\_restaurante**  
* **promociones\_activas\_por\_fecha**  
* **metricas\_restaurante\_por\_dia** 

**Redis- Datos que necesitamos:**

* **sesion:userId**  
* **busqueda:userId**  
* **visitas: restauranteId**  
* **ranking:restaurante**  
* **ranking:tipoComida**

DATASET: 1000 registros

| Tipo de dato | Cantidad | Motor principal | Para qué sirve |
| :---- | :---- | :---- | :---- |
| Usuarios | 80 | MongoDB / Neo4j / Redis | Login, perfiles, sesiones activas y red social |
| Restaurantes | 40 | MongoDB / Neo4j / Cassandra / Redis | Catálogo, rankings, promociones y visitas |
| Platos | 160 | MongoDB / Neo4j | Menú de cada restaurante |
| Reseñas y calificaciones | 250 | MongoDB / Neo4j | Reviews, puntajes y recomendaciones |
| Visitas registradas | 390 | Cassandra / Neo4j / Redis | Historial de visitas, métricas, rankings y comidas más vendidas |
| Promociones | 80 | Cassandra / MongoDB opcional | Promociones activas por restaurante, fecha y barrio |

| Archivo | Registros | ID principal | Rango |
| :---- | :---- | :---- | :---- |
| `usuarios.json` | 80 | `dni_usuario` | 44000001 a 44000080 |
| `restaurantes.json` | 40 | `restaurante_id` | 1 a 40 |
| `platos.json` | 160 | `plato_id` | 1 a 160 |
| `resenas.json` | 250 | `resena_id` | 1 a 250 |
| `visitas.json` | 390 | `visita_id` | 1 a 390 |
| `promociones.json` | 80 | `promocion_id` | 1 a 80 |

DATOS:  
usuarios.json

- dni\_usuario  
- nombre  
- apellido  
- username  
- password  
- mail

restaurantes.json

- restaurante\_id  
- nombre  
- tipo\_comida  
- barrio  
- direccion  
- calificacion\_promedio

platos.json

- plato\_id  
- restaurante\_id  
- plato\_nombre  
- tipo\_comida  
- precio  
- calificacion\_promedio  
- disponible

resenas.json

- resena\_id  
- dni\_usuario  
- restaurante\_id  
- puntaje  
- comentario  
- fecha

visitas.json

- visita\_id  
- dni\_usuario  
- restaurante\_id  
- plato\_id  
- plato\_nombre  
- tipo\_comida  
- barrio  
- fecha  
- hora  
- monto

promociones.json

- promocion\_id  
- restaurante\_id  
- titulo  
- descripcion  
- descuento  
- fecha\_inicio  
- fecha\_fin  
- estado  
- barrio

redis\_eventos.json

- evento\_id  
- tipo\_evento  
- usuario\_id  
- valor  
- timestamp

////////////////////////////////////////////////////////////////////////////////////////

**LO QUE LE MOSTRAMOS A LA PROFE:**  
Starvy es una app móvil que permite descubrir restaurantes, consultar menús, precios, promociones exclusivas y hacer pedidos para consumir en el lugar o retirar sin delivery. 

Es una red social orientada a experiencias gastronómicas. Los usuarios pueden seguir a amigos, descubrir restaurantes y platos, dejar reseñas y calificaciones, y acceder a promociones exclusivas de los locales. La plataforma combina el componente social (seguir personas, ver qué comen tus amigos, recibir recomendaciones personalizadas) con el componente de descubrimiento (explorar menús, precios, horarios, platos destacados).  
La propuesta de valor central es que las recomendaciones no vienen de un algoritmo genérico sino de tu red: si tres amigos califican bien una milanesa en un bar de Palermo, Starvy te lo muestra.

**MongoDB \- Documental**: guarda el catálogo de restaurantes, los perfiles de usuarios y las reviews. Se justifica por su esquema flexible, ya que cada restaurante tiene campos distintos (un bar tiene "happy hour", una hamburguesería tiene "punto de cocción") y no podés forzar esa variedad en una estructura rígida.  
**Cassandra \- Columnar:** entra para todo lo que es volumen masivo con timestamps: el log de cada descuento activado, cada visita registrada, cada métrica del restaurante. Con millones de eventos por día se necesita un motor de altísima velocidad de escritura y escalabilidad horizontal. Hacer 5 o 6 QUERIES   
**Redis \- Clave-Valor:** es la capa de velocidad que hace que la app se sienta rápida: maneja las sesiones activas de usuarios con TTL, cachea los restaurantes más buscados para no ir a MongoDB en cada request.  
**Neo4j \- Grafos:** modela la red social gastronómica: las relaciones usuario→ visitó→ restaurante, usuario→ sigue→ usuario y las recomendaciones del tipo "3 amigos tuyos fueron acá". Ese tipo de consulta en una base relacional sería una cadena de JOINs inmanejable; en Neo4j es un simple recorrido del grafo con Cypher.  
Python→ MongoDB \+ Neo4j  
pymongo para el catálogo y reviews · py2neo / neo4j-driver para el grafo social y recomendaciones.