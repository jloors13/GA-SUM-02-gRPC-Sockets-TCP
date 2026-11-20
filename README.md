# GA-SUM-02 — gRPC y Sockets TCP

Práctica experimental de comunicación entre procesos distribuidos mediante sockets TCP y gRPC con Protocol Buffers. El proyecto permite estudiar el intercambio de mensajes entre nodos, el uso de relojes lógicos de Lamport y el rendimiento de los mecanismos de comunicación.

## Descripción del proyecto

El proyecto desarrolla una aplicación distribuida con tres nodos que intercambian mensajes mediante sockets TCP. Cada nodo mantiene un reloj lógico de Lamport para registrar el orden de los eventos y utiliza un módulo de registro para almacenar la información de las comunicaciones.

También incorpora experimentos para medir latencia, rendimiento y concurrencia. Los resultados se guardan en archivos CSV y se procesan mediante herramientas de análisis estadístico y gráficos.

La estructura contempla una segunda implementación utilizando gRPC y Protocol Buffers, destinada a realizar posteriormente una comparación entre ambos mecanismos.

## Tecnologías utilizadas

- Python 3.12.
- Sockets TCP.
- gRPC y Protocol Buffers (componente previsto).
- Relojes lógicos de Lamport.
- Pandas.
- NumPy.
- Matplotlib.
- unittest.
- Git y GitHub.

## Estructura del repositorio

```text
GA-SUM-02-gRPC-Sockets-TCP/
│
├── analysis/
│   ├── figures/
│   │   ├── tcp_latency_comparison.png
│   │   └── tcp_latency_distribution.png
│   └── tcp_statistics.py
│
├── data/
│   ├── tcp_concurrency.csv
│   ├── tcp_events_nodo-A.csv
│   ├── tcp_events_nodo-B.csv
│   ├── tcp_events_nodo-C.csv
│   ├── tcp_exchanges.csv
│   ├── tcp_latency.csv
│   └── tcp_statistics.csv
│
├── docs/
│
├── proto/
│
├── src/
│   ├── common/
│   │   ├── event_logger.py
│   │   └── lamport.py
│   │
│   ├── grpc/
│   │
│   └── sockets/
│       ├── tcp_client.py
│       ├── tcp_experiment.py
│       ├── tcp_node.py
│       └── tcp_server.py
│
├── tests/
│   ├── test_event_logger.py
│   ├── test_lamport.py
│   └── test_tcp_statistics.py
│
├── requirements.txt
└── README.md
```

## Instalación y configuración

Se recomienda utilizar Python 3.12 y crear un entorno virtual para instalar las dependencias del proyecto.

Crear el entorno:

```bash
python -m venv .venv
```

Activarlo en Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Comprobar que las dependencias estén correctamente instaladas:

```bash
python -m pip check
```

## Implementación TCP

La implementación TCP utiliza tres nodos:

| Nodo | Dirección | Puerto |
|---|---|---:|
| nodo-A | 127.0.0.1 | 5000 |
| nodo-B | 127.0.0.1 | 5001 |
| nodo-C | 127.0.0.1 | 5002 |

Cada nodo dispone de un cliente y un servidor TCP. Los mensajes se intercambian mediante estructuras JSON y las respuestas permiten confirmar la recepción.

### Relojes lógicos de Lamport

El módulo `src/common/lamport.py` implementa el reloj lógico de cada nodo.

Sus operaciones principales son:

- `before_send()`: incrementa el reloj antes de enviar un mensaje.
- `after_receive(timestamp)`: actualiza el reloj al recibir un mensaje, considerando su timestamp.

### Registro de eventos

El módulo `src/common/event_logger.py` almacena los eventos de envío y recepción en archivos CSV.

Cada registro contiene:

- Nodo que genera el evento.
- Tipo de evento.
- Timestamp lógico de Lamport.
- Fecha y hora real del registro.

## Ejecución de los nodos

Para iniciar individualmente un nodo se utiliza:

```bash
python -m src.sockets.tcp_node nodo-A
```

También se puede utilizar `nodo-B` o `nodo-C`.

Para realizar una comunicación, se introduce el nombre del nodo de destino y posteriormente el mensaje.

Para detener el nodo se escribe:

```text
salir
```

## Ejecución de los experimentos TCP

El módulo de experimentación inicia automáticamente los tres servidores, realiza las pruebas y los detiene al finalizar.

Ejecutar:

```bash
python -m src.sockets.tcp_experiment
```

El experimento contempla:

- 20 intercambios de mensajes entre los nodos.
- Mediciones de latencia con mensajes de 100 y 10.240 bytes.
- 5 repeticiones por tamaño de mensaje.
- 100 muestras por repetición.
- Una prueba de concurrencia con tres comunicaciones simultáneas.

Los resultados se almacenan en la carpeta `data/`.

## Análisis estadístico

Para procesar las mediciones obtenidas mediante TCP:

```bash
python -m analysis.tcp_statistics
```

El módulo calcula:

- Media de latencia.
- Mediana.
- Latencia mínima y máxima.
- Desviación estándar.
- Percentil 95 (P95).
- Throughput promedio.

Los resultados se guardan en:

```text
data/tcp_statistics.csv
```

También se generan dos gráficos:

- `analysis/figures/tcp_latency_comparison.png`
- `analysis/figures/tcp_latency_distribution.png`

## Pruebas automatizadas

El proyecto utiliza `unittest` para verificar el funcionamiento de los módulos implementados.

Ejecutar todas las pruebas:

```bash
python -m unittest discover -s tests -v
```

Las pruebas disponibles comprueban el funcionamiento del reloj de Lamport, el registro de eventos y los cálculos estadísticos.

En la validación realizada durante el desarrollo se obtuvieron 22 pruebas superadas.

## Resultados experimentales TCP

En la ejecución experimental registrada se obtuvieron los siguientes resultados:

| Tamaño del mensaje | Bytes | Muestras | Latencia media |
|---|---:|---:|---:|
| Corto | 100 | 500 | 7,220525 ms |
| Largo | 10.240 | 500 | 4,850986 ms |

Estos valores corresponden al entorno donde se realizaron las pruebas. No representan resultados universales del protocolo TCP.

## Estado del proyecto

La implementación TCP, el registro de eventos, los relojes lógicos y el análisis estadístico se encuentran desarrollados y cuentan con pruebas automatizadas.

La implementación gRPC con Protocol Buffers y la comparación final entre ambos mecanismos forman parte del trabajo pendiente de integración.

## Trabajo colaborativo

El repositorio se utiliza para desarrollar e integrar las diferentes partes de la práctica. Cada integrante debe mantener sus cambios organizados, documentar sus aportes y verificar el funcionamiento de su implementación antes de integrarla a la rama principal.