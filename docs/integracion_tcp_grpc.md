# Integración de Sockets TCP y gRPC

## 1. Objetivo

En esta parte del proyecto se busca que las implementaciones de Sockets TCP y gRPC puedan trabajar bajo las mismas condiciones de prueba. Esto permitirá revisar cómo se comporta cada mecanismo al enviar mensajes entre nodos y comparar sus tiempos de respuesta.

También se comprobará que los relojes de Lamport funcionen correctamente y que los eventos registrados mantengan el orden lógico de las comunicaciones.

## 2. Componentes que se van a integrar

El proyecto trabaja con tres nodos: nodo-A, nodo-B y nodo-C.

La parte de Sockets TCP ya está desarrollada. Los nodos pueden intercambiar mensajes mediante conexiones TCP y utilizar JSON para enviar la información.

En el caso de gRPC, los mensajes y servicios se definirán mediante Protocol Buffers. Esta implementación todavía está pendiente de incorporarse al proyecto.

La idea es que ambos mecanismos utilicen los mismos criterios para registrar los eventos, de manera que después sea posible comparar los resultados sin tener que procesarlos de formas completamente distintas.

## 3. Uso de los relojes de Lamport

Los relojes de Lamport permiten llevar un orden lógico de los eventos que ocurren durante la comunicación entre nodos.

Para utilizarlos correctamente, se seguirán estas reglas:

- Cada vez que un nodo envía un mensaje, aumenta su reloj lógico en una unidad.
- El mensaje debe incluir el valor del reloj del emisor.
- Cuando otro nodo recibe ese mensaje, compara el valor recibido con su propio reloj, toma el mayor y le suma uno.
- Los eventos de envío y recepción se guardan en archivos CSV para revisarlos posteriormente.

En la implementación TCP ya se utilizan los archivos `src/common/lamport.py` y `src/common/event_logger.py`.

Cuando se incorpore gRPC, se revisará cómo reutilizar estos módulos para evitar desarrollar nuevamente la misma lógica.

## 4. Condiciones de las pruebas

Para que la comparación tenga sentido, las pruebas de TCP y gRPC deben realizarse con parámetros similares.

| Parámetro | Sockets TCP | gRPC |
|---|---|---|
| Número de nodos | 3 | 3 |
| Intercambios de mensajes | 20 | 20 |
| Mensajes pequeños | 100 bytes | 100 bytes |
| Mensajes grandes | 10.240 bytes | 10.240 bytes |
| Repeticiones por tamaño | 5 | 5 |
| Muestras por repetición | 100 | 100 |
| Clientes concurrentes | 3 | 3 |

Estos valores ya se utilizaron en los experimentos TCP y servirán como referencia para preparar las pruebas de gRPC.

Además, se procurará ejecutar ambos experimentos en el mismo equipo y sin programas que generen una carga excesiva, ya que esto podría afectar las mediciones.

## 5. Datos que se van a comparar

Una vez que tengamos los resultados de ambos mecanismos, revisaremos:

- **Latencia media:** cuánto tarda, en promedio, una comunicación.
- **Mediana:** el valor central de los tiempos registrados.
- **Desviación estándar:** cuánto varían los tiempos entre una prueba y otra.
- **Percentil 95 (P95):** el tiempo por debajo del cual se encuentra el 95 % de las mediciones.
- **Throughput:** cuántos datos o solicitudes se procesan por unidad de tiempo, según la medida utilizada.
- **Concurrencia:** cómo responde cada mecanismo cuando varios clientes se comunican al mismo tiempo.

También se comprobará que los timestamps de Lamport respeten el orden de los mensajes enviados y recibidos.

## 6. Cómo comprobaremos que la integración funciona

No será suficiente con que los programas se ejecuten sin mostrar errores. También tendremos que revisar que los mensajes lleguen correctamente y que los resultados puedan utilizarse para el análisis.

Para eso, comprobaremos lo siguiente:

- Que los nodos puedan comunicarse mediante gRPC.
- Que cada mensaje incluya el timestamp lógico correspondiente.
- Que los eventos de envío y recepción queden registrados en archivos CSV.
- Que el verificador de Lamport pueda revisar el orden de los eventos.
- Que las pruebas de gRPC generen datos con los mismos criterios utilizados en TCP.
- Que las pruebas automatizadas terminen sin errores.

Si alguna de estas comprobaciones falla, habrá que corregirla antes de realizar la comparación final.

## 7. Avance del proyecto

Hasta el momento, la implementación de Sockets TCP está terminada. Se realizaron pruebas de comunicación entre los tres nodos, se registraron los eventos y se obtuvieron mediciones de latencia y concurrencia.

También se desarrolló un programa para verificar los relojes de Lamport a partir de los archivos CSV.

Por otro lado, la implementación gRPC todavía no se ha incorporado a la rama principal. Cuando los compañeros terminen y publiquen sus avances, se revisará que funcione junto con los módulos que ya tenemos.

Después de esa integración podremos ejecutar los experimentos pendientes y elaborar la comparación final entre Sockets TCP y gRPC.