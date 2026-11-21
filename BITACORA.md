## Sesión 1 — Configuración inicial del repositorio y entorno local
* **Fecha:** 19 de noviembre de 2026  
* **Hora:** [Ej. 23:00 – 23:45]  
* **Integrante:** César Macías  

### Lo realizado
* Acceso al repositorio del equipo en GitHub y clonado local del proyecto.
* Creación/verificación de la rama de trabajo personal (`cesar-macias`) para evitar conflictos directos en `main`.
* Revisión de la estructura base de carpetas (`/src/sockets`, `/src/grpc`, `/proto`, `/data`, `/analysis`, `/docs`) y validación de la versión de Python disponible en el equipo.

### Problemas encontrados y soluciones
* **Problema:** Ninguno durante el acceso inicial y clonado del repositorio. (Si te salió algún error de credenciales, `git pull` o rama, anótalo aquí).
* **Solución:** N/A.


## Sesión 2 — Definición del contrato gRPC (`servicio.proto`)
* **Fecha:** 20 de noviembre de 2026  
* **Hora:** 18:15 - 19:20 
* **Integrante:** Washington Apunte 

### Lo realizado
* Revisión del esqueleto de `servicio.proto` en la carpeta `/proto` y comparación con el formato JSON de la versión TCP (`tcp_server.py`), para mantener los mismos campos: `sender`, `timestamp` y `message`.
* Definición del paquete `mensajeria` y del servicio `ComunicacionNodos` con el método remoto `rpc EnviarMensaje(Mensaje) returns (Acuse);`.
* Definición del mensaje `Mensaje` (lo que envía el cliente) y del mensaje `Acuse` (lo que responde el servidor, con `received_timestamp` y `timestamp`).
* Elección de `int64` para los tres campos de reloj de Lamport. Motivo: es compatible con lenguajes que no tienen enteros sin signo (por ejemplo, Java) y permite detectar un valor negativo como error, y rechazarlo con `INVALID_ARGUMENT` en el servidor.
* Comando para generar el código de Python: `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/servicio.proto`, que crea `servicio_pb2.py` y `servicio_pb2_grpc.py`.

### Problemas encontrados y soluciones
* **Problema:** Hubo que decidir entre `int64` y `uint64` para los timestamps, porque el reloj de Lamport nunca es negativo y los dos tipos parecían válidos.
* **Solución:** Se usó `int64` en los tres campos para que sean consistentes, por las razones de compatibilidad y detección de errores que se explican arriba. En Python no cambia nada, porque ambos tipos se leen como `int`.


## Sesión 3 — Pruebas del servidor, documentación e informe
* **Fecha:** 20 de noviembre de 2026  
* **Hora:** 19:30 – 20:54  
* **Integrante:** Washington Apunte  

### Lo realizado
* Se escribieron 6 pruebas del servidor gRPC en `tests/test_grpc_server.py`, entre ellas `test_timestamp_negativo` y una prueba de concurrencia de 30 llamadas en la que no se repitió ningún timestamp. Con ellas, la suite completa pasó de 47 a 53 pruebas.
* Se comprobó que una solicitud rechazada (emisor vacío o timestamp negativo) no deja eventos registrados.
* Se comentó `proto/servicio.proto` y se justificó el uso de `int64` por compatibilidad con lenguajes sin enteros sin signo nativos (como Java) y porque el servidor puede recibir un valor negativo y rechazarlo de forma controlada con `INVALID_ARGUMENT`.
* Se agregó al `README.md` una sección nueva con tres partes: generar el código del contrato con `grpc_tools.protoc`, iniciar un nodo gRPC y ejecutar las pruebas del servidor. También se actualizó el conteo de pruebas a 53.
* PR #6: incluyó `tests/test_grpc_server.py`, los comentarios del `.proto` y la sección nueva del README. Se fusionó con merge commit.
* Se redactó la sección del informe «El contrato `.proto` y Protocol Buffers» (`seccion_proto.tex`) y se dejó en borrador la de «Servidor gRPC» (`seccion_servidor.tex`); falta completar la lista de pruebas.
* Referencias: se recibió una lista de candidatos, de los cuales dos artículos de revista se contrastaron con Crossref. Falta abrir cada DOI en doi.org, verificar los demás candidatos y escribir el .bib.

### Problemas encontrados y soluciones
* **Problema:** Al ejecutar las pruebas apareció el error `LamportClock() missing 'node_name'`.
* **Solución:** Se cambió `LamportClock()` por `LamportClock("nodo-X")` en el `setUp` de las pruebas, porque el constructor exige el nombre del nodo.
* **Problema:** La bitácora tenía texto de plantilla y una afirmación imprecisa sobre `uint64`: decía que un negativo se convertiría en un número gigante, pero en Python la librería lanza un error al construir el mensaje.
* **Solución:** Se reemplazó el texto de plantilla por el contenido real y se reescribió la razón de `int64` con lo que se puede demostrar: el servidor rechaza el negativo con `INVALID_ARGUMENT`, como comprueba `test_timestamp_negativo`.