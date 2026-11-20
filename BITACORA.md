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
* **Hora:** [Ej. 18:15 – 18:30]  
* **Integrante:** [Tu nombre]  

### Lo realizado
* Revisión del esqueleto de `servicio.proto` en la carpeta `/proto` y comparación con el formato JSON de la versión TCP (`tcp_server.py`), para mantener los mismos campos: `sender`, `timestamp` y `message`.
* Definición del paquete `mensajeria` y del servicio `ComunicacionNodos` con el método remoto `rpc EnviarMensaje(Mensaje) returns (Acuse);`.
* Definición del mensaje `Mensaje` (lo que envía el cliente) y del mensaje `Acuse` (lo que responde el servidor, con `received_timestamp` y `timestamp`).
* Elección de `int64` para los tres campos de reloj de Lamport. Motivo: es compatible con lenguajes que no tienen enteros sin signo (por ejemplo, Java) y permite detectar un valor negativo como error, en vez de que se convierta en un número gigante como pasaría con `uint64`.
* Eliminación de los comentarios del esqueleto.
* Comando para generar el código de Python: `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. servicio.proto`, que crea `servicio_pb2.py` y `servicio_pb2_grpc.py`.

### Problemas encontrados y soluciones
* **Problema:** Hubo que decidir entre `int64` y `uint64` para los timestamps, porque el reloj de Lamport nunca es negativo y los dos tipos parecían válidos.
* **Solución:** Se usó `int64` en los tres campos para que sean consistentes, por las razones de compatibilidad y detección de errores que se explican arriba. En Python no cambia nada, porque ambos tipos se leen como `int`.