## Sesión 9 — Implementación inicial de los componentes TCP y módulos comunes

- **Fecha:** 19 de noviembre de 2026
- **Horario:** Tarde y noche
- **Integrante:** Jordan Loor

### Lo realizado

- Se creó la estructura inicial del repositorio para organizar los componentes TCP y gRPC.
- Se configuraron las dependencias del proyecto.
- Se implementó el reloj lógico de Lamport en `src/common/lamport.py`.
- Se desarrolló `src/common/event_logger.py` para registrar los eventos de comunicación en archivos CSV.
- Se implementaron el cliente, servidor y nodo TCP, junto con el módulo de experimentación.

## Sesión 10 — Consolidación de experimentos TCP y documentación de integración

- **Fecha:** 20 de noviembre de 2026
- **Horario:** Tarde
- **Integrante:** Jordan Loor

### Lo realizado

- Se consolidaron los experimentos TCP y se desarrolló `analysis/tcp_statistics.py` para calcular estadísticas y generar gráficos.
- Se incorporaron los resultados experimentales y las pruebas de los módulos comunes.
- Se desarrolló `analysis/verify_lamport.py` junto con sus pruebas automatizadas.
- Se implementó `analysis/validate_experiment_data.py` para comprobar la integridad de los registros experimentales.
- Se agregó la documentación de integración TCP-gRPC en `docs/integracion_tcp_grpc.md`.

## Sesión 1 — Configuración inicial del repositorio y entorno local
- **Fecha:** 19 de noviembre de 2026  
- **Hora:** 23:00 – 23:45  
- **Integrante:** César Macías  

### Lo realizado
- Acceso al repositorio del equipo en GitHub y clonado local del proyecto.
- Creación y verificación de la rama de trabajo personal (`cesar`) para evitar conflictos directos en `main`.
- Revisión de la estructura base de carpetas (`/src/sockets`, `/src/grpc`, `/proto`, `/data`, `/analysis`, `/docs`) y validación de la versión de Python disponible en el equipo.

### Problemas encontrados y soluciones
- **Problema:** Ninguno durante el acceso inicial y clonado del repositorio.
- **Solución:** N/A.


## Sesión 2 — Definición del contrato gRPC (`servicio.proto`)
- **Fecha:** 20 de noviembre de 2026  
- **Hora:** 18:15 - 19:20 
- **Integrante:** Washington Apunte 

### Lo realizado
- Revisión del esqueleto de `servicio.proto` en la carpeta `/proto` y comparación con el formato JSON de la versión TCP (`tcp_server.py`), para mantener los mismos campos: `sender`, `timestamp` y `message`.
- Definición del paquete `mensajeria` y del servicio `ComunicacionNodos` con el método remoto `rpc EnviarMensaje(Mensaje) returns (Acuse);`.
- Definición del mensaje `Mensaje` (lo que envía el cliente) y del mensaje `Acuse` (lo que responde el servidor, con `received_timestamp` y `timestamp`).
- Elección de `int64` para los tres campos de reloj de Lamport. Motivo: es compatible con lenguajes que no tienen enteros sin signo (por ejemplo, Java) y permite detectar un valor negativo como error, y rechazarlo con `INVALID_ARGUMENT` en el servidor.
- Comando para generar el código de Python: `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/servicio.proto`, que crea `servicio_pb2.py` y `servicio_pb2_grpc.py`.

### Problemas encontrados y soluciones
- **Problema:** Hubo que decidir entre `int64` y `uint64` para los timestamps, porque el reloj de Lamport nunca es negativo y los dos tipos parecían válidos.
- **Solución:** Se usó `int64` en los tres campos para que sean consistentes, por las razones de compatibilidad y detección de errores que se explican arriba. En Python no cambia nada, porque ambos tipos se leen como `int`.


## Sesión 3 — Pruebas del servidor, documentación e informe
- **Fecha:** 20 de noviembre de 2026  
- **Hora:** 19:30 – 20:54  
- **Integrante:** Washington Apunte  

### Lo realizado
- Se escribieron 6 pruebas del servidor gRPC en `tests/test_grpc_server.py`, entre ellas `test_timestamp_negativo` y una prueba de concurrencia de 30 llamadas en la que no se repitió ningún timestamp. Con ellas, la suite completa pasó de 47 a 53 pruebas.
- Se comprobó que una solicitud rechazada (emisor vacío o timestamp negativo) no deja eventos registrados.
- Se comentó `proto/servicio.proto` y se justificó el uso de `int64` por compatibilidad con lenguajes sin enteros sin signo nativos (como Java) y porque el servidor puede recibir un valor negativo y rechazarlo de forma controlada con `INVALID_ARGUMENT`.
- Se agregó al `README.md` una sección nueva con tres partes: generar el código del contrato con `grpc_tools.protoc`, iniciar un nodo gRPC y ejecutar las pruebas del servidor. También se actualizó el conteo de pruebas a 53.
- PR #6: incluyó `tests/test_grpc_server.py`, los comentarios del `.proto` y la sección nueva del README. Se fusionó con merge commit.
- Se redactó la sección del informe «El contrato `.proto` y Protocol Buffers» (`seccion_proto.tex`) y se dejó en borrador la de «Servidor gRPC» (`seccion_servidor.tex`); falta completar la lista de pruebas.
- Referencias: se recibió una lista de candidatos, de los cuales dos artículos de revista se contrastaron con Crossref. Falta abrir cada DOI en doi.org, verificar los demás candidatos y escribir el .bib.

### Problemas encontrados y soluciones
- **Problema:** Al ejecutar las pruebas apareció el error `LamportClock() missing 'node_name'`.
- **Solución:** Se cambió `LamportClock()` por `LamportClock("nodo-X")` en el `setUp` de las pruebas, porque el constructor exige el nombre del nodo.
- **Problema:** La bitácora tenía texto de plantilla y una afirmación imprecisa sobre `uint64`: decía que un negativo se convertiría en un número gigante, pero en Python la librería lanza un error al construir el mensaje.
- **Solución:** Se reemplazó el texto de plantilla por el contenido real y se reescribió la razón de `int64` con lo que se puede demostrar: el servidor rechaza el negativo con `INVALID_ARGUMENT`, como comprueba `test_timestamp_negativo`.


## Sesión 4 — Informe del servidor, referencias y capturas
- **Fecha:** 20 de noviembre de 2026  
- **Hora:** 20:55 – 22:28  
- **Integrante:** Washington Apunte  

### Lo realizado
- Se completó la sección del informe «Servidor gRPC» (`seccion_servidor.tex`): se terminó la lista de las 6 pruebas y se corrigió `<nodo>` en el nombre del CSV para que se vea bien en el PDF.
- Se probó el servidor con el cliente gRPC de César (`python -m src.grpc.grpc_client nodo-A nodo-B "Hola"`): el servidor respondió `ACK: Hola`. El reloj de `nodo-A` terminó en 4 en la primera llamada y en 6 en la segunda, porque el servidor conserva su reloj entre llamadas.
- Se tomaron 6 capturas con el usuario, el equipo y la fecha visibles: cliente, servidor, las 53 pruebas, emisor vacío, `timestamp` negativo y el CSV de eventos de `nodo-B`.
- Se escribió `informe/referencias.bib` con 7 entradas: Niswar 2024, Ain 2025, Maltsev y Amin 2024, Iwanowski et al. 2024 (JCSI), Lamport 1978, RFC 9293 y RFC 9113. Los datos de cada una se comprobaron en Crossref y en las páginas de las revistas.
- Se agregaron citas en `seccion_proto.tex` (Niswar, Ain, Iwanowski et al., Maltsev y Amin, RFC 9113 y RFC 9293) y en `seccion_servidor.tex` (Lamport).
- Se fusionaron el PR #8 y el PR #9 con merge commit.

### Problemas encontrados y soluciones
- **Problema:** Sangwai 2023 y Ghosh 2023 eran de pago.
- **Solución:** Se citan solo fuentes de libre acceso, así que ambas quedaron fuera del `.bib` y se reemplazaron por Maltsev y Amin 2024 e Iwanowski et al. 2024.
- **Problema:** En el artículo de JCSI 2024, la página de la revista y Crossref listan primero a Jarmoszewicz, pero el PDF imprime primero a Iwanowski.
- **Solución:** Se usó el orden del PDF, porque es el del propio artículo, y se dejó anotada la diferencia.
- **Problema:** Se subió `seccion_servidor.tex` sin guardar el archivo en VS Code (faltó Ctrl+S) y quedó una versión a medias en `main`.
- **Solución:** Se detectó con `git diff`, se guardó y se subió la corrección. Desde entonces se revisa con `git diff` antes de cada commit y se activó el guardado automático.
- **Problema:** Al añadir las citas, `git diff` mostró que una cita ya subida (Niswar) había vuelto a un `% TODO`.
- **Solución:** Se volvió a poner la cita antes de hacer el commit.


## Sesión 5 — Implementación del cliente gRPC y script de experimentos
- **Fecha:** 20 de noviembre de 2026  
- **Hora:** 20:00 – 21:30  
- **Integrante:** César Macías  

### Lo realizado
- Sincronización de la rama `cesar` con `main` para integrar el contrato `proto/servicio.proto`, `src/grpc/grpc_server.py` y los módulos comunes (`lamport.py`, `event_logger.py`).
- Implementación del cliente gRPC (`src/grpc/grpc_client.py`) con actualización del reloj de Lamport antes de enviar y al recibir el `Acuse`, registro de eventos y manejo de `grpc.RpcError`.
- Implementación del script de experimentos automatizados (`src/grpc/grpc_experiment.py`) replicando las mismas condiciones que TCP: 20 intercambios con verificación causal, calentamiento descartado, 5 repeticiones de 100 muestras para mensajes cortos (100 B) y largos (10 KB), y prueba de concurrencia con tres clientes simultáneos.
- Apertura de Pull Request hacia `main` con ambos módulos.

### Problemas encontrados y soluciones
- **Problema:** Al ejecutar `python -m src.grpc.grpc_experiment` apareció `ModuleNotFoundError: No module named 'grpc'`.
- **Solución:** Se instalaron las dependencias desde `requirements.txt` (`pip install -r requirements.txt`) y se verificó la ejecución completa de los experimentos.
- **Problema:** Git bloqueó el commit por no tener configurada la identidad local (`user.name` y `user.email`).
- **Solución:** Se configuraron `user.name` y `user.email` vinculados a la cuenta de GitHub y se subió la rama `cesar`.


## Sesión 6 — Ejecución de experimentos gRPC, pruebas del cliente y documentación
- **Fecha:** 21 de noviembre de 2026  
- **Hora:** 20:15 – 20:45  
- **Integrante:** César Macías  

### Lo realizado
- Ejecución completa de `src/grpc/grpc_experiment.py` en equipo local y respaldo de los CSV crudos en `data/` (`grpc_events_nodo-A.csv`, `grpc_events_nodo-B.csv`, `grpc_events_nodo-C.csv`, `grpc_exchanges.csv`, `grpc_latency.csv` y `grpc_concurrency.csv`).
- Implementación y ejecución de 3 pruebas unitarias para el cliente gRPC en `tests/test_grpc_client.py` (envío válido con reloj de Lamport, rechazo de emisor vacío y manejo de servidor inaccesible), todas superadas (`OK` en 1.721 s).
- Documentación del cliente gRPC, el script de experimentos y las pruebas unitarias en `README.md`.
- Limpieza del texto de plantilla pendiente en la Sesión 1 de `BITACORA.md` y registro de las sesiones de trabajo.

### Problemas encontrados y soluciones
- **Problema:** La primera captura de la ejecución de experimentos cortaba el prompt con el usuario arriba y el bloque de mensajes largos abajo.
- **Solución:** Se verificó la salida completa en la terminal para respaldar evidencias con el usuario, nombre del equipo, fecha y hora visibles.


## Sesión 7 — README, declaración de uso de IA y conclusión individual
* **Fecha:** 22 de noviembre de 2026  
* **Hora:** 14:30 – 16:10  
* **Integrante:** Washington Apunte  

### Lo realizado
* Se sincronizó la rama de trabajo con `main` mediante un fast-forward, sin commit de fusión.
* Se ejecutó la suite completa de pruebas y pasaron las 56.
* Se reescribió el segundo párrafo de «Estado del proyecto» en el `README.md`. Ahora indica que el contrato `proto/servicio.proto`, el servidor y el cliente gRPC y sus experimentos están desarrollados, y que quedan pendientes el análisis comparativo de TCP frente a gRPC y el informe final. También menciona las pruebas de cada uno en `tests/test_grpc_server.py` y `tests/test_grpc_client.py`.
* Se redactó la declaración de uso de IA.
* Se escribió la conclusión individual en `informe/seccion_conclusion_washington.tex`, de unas 180 palabras. Resume el contrato y el servidor, justifica el uso de `int64` y da las cifras de las pruebas: 6 del servidor, 56 en total y la prueba de concurrencia de 30 llamadas desde 10 hilos.
* Se revisaron la guía de la práctica y los criterios de evaluación del docente.

### Problemas encontrados y soluciones
* **Problema:** «Estado del proyecto» seguía diciendo que la implementación gRPC estaba pendiente, aunque el contrato, el servidor y el cliente ya estaban en el repositorio.
* **Solución:** Se reescribió el párrafo separando lo hecho de lo pendiente.


## Sesión 8 — Sección del informe del cliente gRPC, entorno experimental, declaración de IA y conclusión
* **Fecha:** 22 de noviembre de 2026  
* **Hora:** 19:20 – 19:50  
* **Integrante:** César Macías  

### Lo realizado
* Se sincronizó la rama `cesar` con los últimos cambios de `main` (fast-forward incluyendo aportes de Washington y suite completa de 56 pruebas).
* Se corrigieron las líneas 103 y 108 de `BITACORA.md` eliminando los marcadores residuales `[cite: 12]` y `[cite: 11]`.
* Se redactó la sección del informe sobre el cliente gRPC (`informe/seccion_cliente.tex`), detallando la estructura de `grpc_client.py`, la gestión del reloj de Lamport, el control de excepciones con `grpc.RpcError`, la suite de pruebas unitarias y la automatización experimental.
* Se documentó detalladamente el entorno experimental de las corridas (Python, arquitectura AMD64 con 16 núcleos lógicos, Windows 11, y nodos simulados como procesos/hilos independientes en `localhost`).
* Se redactó la declaración individual de uso de IA en `informe/seccion_declaracion_ia.tex`.
* Se redactó la conclusión individual en `informe/seccion_conclusion_cesar.tex` y en la sección del cliente.
* Se verificó la ejecución exitosa de la suite completa de 56 pruebas automatizadas (`OK`).

### Problemas encontrados y soluciones
* **Problema:** En la Sesión 6 de `BITACORA.md` habían quedado marcadores residuales `[cite: 12]` y `[cite: 11]`.
* **Solución:** Se removieron ambos marcadores dejando la redacción limpia y uniforme.
* **Problema:** El entorno de corrida de los experimentos no estaba formalmente caracterizado en el informe para garantizar la validez metodológica frente a TCP.
* **Solución:** Se añadió una subsección específica con las especificaciones de hardware, versión de Python y el esquema de aislamiento de procesos en `localhost`.
## Sesión 11 — Análisis comparativo TCP y gRPC e informe individual

- **Fecha:** 22 de noviembre de 2026
- **Horario:** Tarde
- **Integrante:** Jordan Loor

### Lo realizado

- Se desarrolló `analysis/compare_tcp_grpc.py` para comparar los resultados experimentales de TCP y gRPC.
- Se calcularon estadísticas de latencia, throughput e intervalos de confianza.
- Se generaron tres gráficos comparativos.
- Se implementaron pruebas unitarias para el análisis comparativo.
- Se elaboró la sección comparativa, la conclusión individual y la declaración de uso de IA.
- Se organizaron los resultados en archivos CSV dentro de `data/`.

### Resultados

- gRPC registró una reducción de latencia media del 49,66 % en mensajes cortos y del 32,55 % en mensajes largos.
- El throughput promedio de gRPC fue superior en ambos tamaños de mensaje.
- La suite completa alcanzó 63 pruebas superadas, según la ejecución registrada.