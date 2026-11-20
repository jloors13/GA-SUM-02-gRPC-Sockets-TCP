# Metodología experimental de comunicación TCP

## 1. Objetivo

Evaluar el funcionamiento de la comunicación mediante sockets TCP entre tres nodos, registrando los intercambios de mensajes, los tiempos de respuesta y el comportamiento ante solicitudes concurrentes.

Los resultados obtenidos servirán como referencia para una comparación posterior con gRPC.

## 2. Entorno de pruebas

Los experimentos se realizaron con Python 3.12 y tres nodos ejecutados en un entorno local.

| Nodo | Dirección IP | Puerto |
|---|---|---|
| nodo-A | 127.0.0.1 | 5000 |
| nodo-B | 127.0.0.1 | 5001 |
| nodo-C | 127.0.0.1 | 5002 |

La comunicación utiliza sockets TCP y mensajes representados mediante JSON. Los eventos se registran utilizando relojes lógicos de Lamport.

## 3. Procedimiento experimental

### 3.1. Intercambio de mensajes

Se realizaron 20 intercambios entre los nodos para comprobar el envío, la recepción y las respuestas del sistema.

Los eventos generados se almacenan en `data/tcp_exchanges.csv` y en los archivos de eventos correspondientes a cada nodo.

### 3.2. Medición de latencia

Se utilizaron dos tamaños de mensaje:

- Mensaje corto: 100 bytes.
- Mensaje largo: 10.240 bytes.

Para cada tamaño se realizaron cinco repeticiones de cien muestras, obteniendo 500 mediciones por categoría.

La latencia se expresa en milisegundos y representa el tiempo medido durante la comunicación de solicitud y respuesta.

Los datos se almacenan en `data/tcp_latency.csv`.

### 3.3. Prueba de concurrencia

Se realizaron tres comunicaciones concurrentes:

| Emisor | Receptor | Latencia registrada |
|---|---|---:|
| nodo-A | nodo-B | 6,1154 ms |
| nodo-B | nodo-C | 6,2118 ms |
| nodo-C | nodo-A | 6,6787 ms |

Los resultados se almacenan en `data/tcp_concurrency.csv`.

Esta prueba permite observar el comportamiento de la implementación ante varias solicitudes, pero no constituye una evaluación completa de escalabilidad.

## 4. Procesamiento estadístico

Los datos de latencia se procesan mediante el módulo `analysis/tcp_statistics.py`.

Se calculan las siguientes métricas:

- Media: promedio de las latencias registradas.
- Mediana: valor central de las mediciones.
- Mínimo y máximo: valores extremos registrados.
- Desviación estándar: dispersión de los resultados.
- Percentil 95 (P95): valor por debajo del cual se encuentra aproximadamente el 95 % de las mediciones.
- Throughput promedio: cantidad promedio de mensajes procesados por segundo, según el cálculo utilizado en el análisis.

Los resultados se guardan en `data/tcp_statistics.csv`.

## 5. Resultados obtenidos

| Tamaño | Muestras | Latencia media |
|---|---:|---:|
| 100 bytes | 500 | 7,220525 ms |
| 10.240 bytes | 500 | 4,850986 ms |

En esta ejecución, los mensajes de mayor tamaño presentaron una latencia media menor.

Este comportamiento puede depender de las condiciones del equipo, la planificación de procesos, las variaciones temporales de ejecución y otros factores que no se controlaron de forma independiente.

Por tanto, los resultados no permiten establecer una relación general entre el tamaño del mensaje y la latencia de TCP.

## 6. Visualización de resultados

El módulo de análisis genera dos gráficos:

- `analysis/figures/tcp_latency_comparison.png`: comparación de latencias.
- `analysis/figures/tcp_latency_distribution.png`: distribución de las mediciones.

Los gráficos complementan el resumen estadístico y permiten observar las diferencias entre ambos tamaños de mensaje.

## 7. Reproducción de los experimentos

Desde la raíz del repositorio, con el entorno virtual activado, ejecutar:

```bash
python -m src.sockets.tcp_experiment
```

Después, procesar las mediciones:

```bash
python -m analysis.tcp_statistics
```

Finalmente, ejecutar las pruebas automatizadas:

```bash
python -m unittest discover -s tests -v
```

Los resultados pueden variar entre ejecuciones y equipos.

## 8. Limitaciones

Las pruebas se realizaron utilizando la interfaz local `127.0.0.1`, sin comunicación entre computadoras físicamente separadas.

No se evaluaron condiciones de red como pérdida de paquetes, congestión, latencia externa o diferentes ubicaciones geográficas.

La prueba de concurrencia incluyó solamente tres comunicaciones, por lo que sus resultados no deben interpretarse como una medición exhaustiva de capacidad.

## 9. Comparación pendiente con gRPC

Una vez implementado gRPC, se deberán ejecutar experimentos bajo condiciones equivalentes, documentando el tamaño de los mensajes, el número de repeticiones, las muestras y las métricas utilizadas.

Esto permitirá realizar una comparación fundamentada entre ambos mecanismos de comunicación.