# Arquitectura de comunicación mediante sockets TCP

## 1. Descripción

La implementación TCP utiliza tres nodos que se comunican mediante sockets. Cada nodo puede enviar y recibir mensajes, lo que permite observar cómo se realiza la comunicación entre procesos distribuidos.

Los mensajes se representan mediante estructuras JSON. Además, se utilizan relojes lógicos de Lamport para registrar el orden de los eventos.

## 2. Organización de los nodos

| Nodo | Dirección IP | Puerto |
|---|---|---|
| nodo-A | 127.0.0.1 | 5000 |
| nodo-B | 127.0.0.1 | 5001 |
| nodo-C | 127.0.0.1 | 5002 |

Los tres nodos se ejecutan en el mismo equipo utilizando puertos diferentes. Esta configuración permite simular la comunicación entre procesos independientes sin necesitar varias computadoras.

## 3. Componentes principales

### Cliente TCP

Archivo: `src/sockets/tcp_client.py`

Se encarga de establecer la conexión con el nodo de destino, enviar el mensaje y recibir la respuesta.

### Servidor TCP

Archivo: `src/sockets/tcp_server.py`

Escucha las solicitudes entrantes, procesa los mensajes recibidos y devuelve una respuesta al cliente.

### Nodo TCP

Archivo: `src/sockets/tcp_node.py`

Permite ejecutar individualmente los nodos y realizar intercambios de mensajes desde la terminal.

### Experimentos TCP

Archivo: `src/sockets/tcp_experiment.py`

Automatiza la ejecución de los tres servidores y realiza las pruebas de intercambio, latencia y concurrencia.

### Reloj lógico de Lamport

Archivo: `src/common/lamport.py`

Cada nodo mantiene un contador lógico que se actualiza durante los eventos de envío y recepción.

### Registro de eventos

Archivo: `src/common/event_logger.py`

Almacena los eventos registrados durante la comunicación en archivos CSV, incluyendo el nodo, el tipo de evento, el timestamp lógico y la hora real.

## 4. Funcionamiento de la comunicación

Cuando un nodo envía un mensaje, incrementa su reloj lógico e incorpora el timestamp correspondiente.

El servidor receptor recibe el mensaje, actualiza su reloj considerando el timestamp recibido y prepara una respuesta.

Al recibir la respuesta, el nodo que inició la comunicación vuelve a actualizar su reloj lógico.

Este procedimiento permite comprobar el orden causal de los eventos de comunicación.

## 5. Experimentos realizados

Se realizaron pruebas de intercambio de mensajes entre los tres nodos.

También se midió la latencia utilizando mensajes de 100 y 10.240 bytes, con cinco repeticiones y cien muestras por repetición para cada tamaño.

Además, se ejecutó una prueba con tres comunicaciones concurrentes para comprobar el comportamiento de la implementación ante solicitudes simultáneas.

## 6. Resultados

Los experimentos generan archivos CSV dentro de `data/`, que posteriormente se procesan mediante `analysis/tcp_statistics.py`.

En la ejecución registrada se obtuvieron 500 muestras para cada tamaño de mensaje.

| Mensaje | Latencia media |
|---|---:|
| Corto, 100 bytes | 7,220525 ms |
| Largo, 10.240 bytes | 4,850986 ms |

Estos resultados corresponden a las condiciones específicas de la ejecución realizada en el equipo local.

## 7. Limitaciones

Aunque los nodos funcionan como procesos de comunicación independientes, las pruebas se realizan utilizando la dirección local `127.0.0.1`.

Por esta razón, los resultados no representan el comportamiento de una red distribuida entre diferentes equipos físicos.

Para obtener conclusiones más amplias sería necesario realizar pruebas adicionales en otros entornos de red.

## 8. Trabajo pendiente

La implementación TCP servirá como referencia para desarrollar la comunicación mediante gRPC y Protocol Buffers.

Una vez implementado el segundo mecanismo, se podrán comparar los resultados de latencia, throughput y concurrencia utilizando condiciones experimentales equivalentes.