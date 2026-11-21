import csv
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger
from src.grpc.grpc_client import send_message
from src.grpc.grpc_server import create_server


NODES = {
    "nodo-A": ("127.0.0.1", 5000),
    "nodo-B": ("127.0.0.1", 5001),
    "nodo-C": ("127.0.0.1", 5002),
}

EXCHANGES = [
    ("nodo-A", "nodo-B"),
    ("nodo-B", "nodo-C"),
    ("nodo-C", "nodo-A"),
]

MESSAGE_SIZES = {
    "corto": 100,
    "largo": 10 * 1024,
}

REPETITIONS = 5
SAMPLES = 100
EXCHANGE_COUNT = 20


def prepare_data():
    Path("data").mkdir(parents=True, exist_ok=True)

    for node in NODES:
        event_file = Path(f"data/grpc_events_{node}.csv")
        if event_file.exists():
            event_file.unlink()


def create_clients():
    clocks = {node: LamportClock(node) for node in NODES}
    loggers = {
        node: EventLogger(f"data/grpc_events_{node}.csv")
        for node in NODES
    }
    return clocks, loggers


def start_servers(clocks, loggers):
    servers = []

    try:
        for node, (host, port) in NODES.items():
            server = create_server(
                node,
                host,
                port,
                clocks[node],
                loggers[node],
            )
            server.start()
            servers.append(server)
            print(f"{node} gRPC iniciado en {host}:{port}")

        time.sleep(0.5)
        return servers

    except Exception:
        stop_servers(servers)
        raise


def stop_servers(servers):
    for server in servers:
        server.stop(2)

    print("Servidores gRPC detenidos")


def send_request(sender, destination, message, clocks, loggers):
    host, port = NODES[destination]
    return send_message(
        host,
        port,
        sender,
        clocks[sender],
        loggers[sender],
        message,
    )


def run_exchanges(clocks, loggers):
    output = "data/grpc_exchanges.csv"

    with open(output, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "exchange",
            "sender",
            "destination",
            "message",
            "sender_timestamp",
            "receiver_timestamp",
            "response_timestamp",
            "client_receive_timestamp",
            "response",
            "timestamp",
        ])

        for index in range(EXCHANGE_COUNT):
            sender, destination = EXCHANGES[index % len(EXCHANGES)]
            message = f"Intercambio experimental numero {index + 1}"

            sender_timestamp = clocks[sender].time + 1

            response = send_request(
                sender,
                destination,
                message,
                clocks,
                loggers,
            )

            receiver_timestamp = response["received_timestamp"]
            response_timestamp = response["timestamp"]
            client_receive_timestamp = clocks[sender].time

            if receiver_timestamp <= sender_timestamp:
                raise RuntimeError(
                    f"Error causal: {sender} -> {destination}"
                )

            if client_receive_timestamp <= response_timestamp:
                raise RuntimeError(
                    f"Error en la respuesta: {destination} -> {sender}"
                )

            if response["sender"] != destination:
                raise RuntimeError("El emisor de la respuesta no coincide")

            writer.writerow([
                index + 1,
                sender,
                destination,
                message,
                sender_timestamp,
                receiver_timestamp,
                response_timestamp,
                client_receive_timestamp,
                response["message"],
                datetime.now().astimezone().isoformat(),
            ])

            file.flush()

            print(
                f"Intercambio {index + 1}/{EXCHANGE_COUNT}: "
                f"{sender} -> {destination} | OK"
            )


def measure_batch(sender, destination, payload, clocks, loggers):
    latencies = []
    start = time.perf_counter()

    for _ in range(SAMPLES):
        begin = time.perf_counter()

        send_request(
            sender,
            destination,
            payload,
            clocks,
            loggers,
        )

        end = time.perf_counter()

        latencies.append((
            (end - begin) * 1000,
            datetime.now().astimezone().isoformat(),
        ))

    duration = time.perf_counter() - start
    return latencies, duration


def run_latency_tests(clocks, loggers):
    output = "data/grpc_latency.csv"

    with open(output, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "mechanism",
            "message_size",
            "message_bytes",
            "repetition",
            "sample",
            "latency_ms",
            "run_duration_s",
            "throughput_msg_s",
            "timestamp",
        ])

        for size_name, size in MESSAGE_SIZES.items():
            payload = "x" * size

            print(f"\nCalentamiento gRPC: mensajes {size_name}")
            measure_batch(
                "nodo-A",
                "nodo-B",
                payload,
                clocks,
                loggers,
            )

            for repetition in range(1, REPETITIONS + 1):
                latencies, duration = measure_batch(
                    "nodo-A",
                    "nodo-B",
                    payload,
                    clocks,
                    loggers,
                )

                throughput = SAMPLES / duration

                for sample, (latency, timestamp) in enumerate(latencies, 1):
                    writer.writerow([
                        "gRPC",
                        size_name,
                        size,
                        repetition,
                        sample,
                        latency,
                        duration,
                        throughput,
                        timestamp,
                    ])

                file.flush()

                average = sum(
                    latency for latency, _ in latencies
                ) / len(latencies)

                print(
                    f"gRPC {size_name} | "
                    f"Repeticion {repetition}/{REPETITIONS} | "
                    f"Media: {average:.4f} ms"
                )


def concurrent_send(node, destination, barrier, clocks, loggers):
    barrier.wait()

    start = time.perf_counter()

    response = send_request(
        node,
        destination,
        f"Mensaje concurrente de {node}",
        clocks,
        loggers,
    )

    latency = (time.perf_counter() - start) * 1000

    return (
        node,
        destination,
        latency,
        response["message"],
        datetime.now().astimezone().isoformat(),
    )


def run_concurrency_test(clocks, loggers):
    routes = [
        ("nodo-A", "nodo-B"),
        ("nodo-B", "nodo-C"),
        ("nodo-C", "nodo-A"),
    ]

    barrier = threading.Barrier(3)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(
                concurrent_send,
                sender,
                destination,
                barrier,
                clocks,
                loggers,
            )
            for sender, destination in routes
        ]

        results = [future.result() for future in futures]

    with open(
        "data/grpc_concurrency.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "sender",
            "destination",
            "latency_ms",
            "response",
            "timestamp",
        ])

        for sender, destination, latency, response, timestamp in results:
            writer.writerow([
                sender,
                destination,
                latency,
                response,
                timestamp,
            ])

            print(
                f"Concurrencia gRPC: {sender} -> {destination} | "
                f"{latency:.4f} ms"
            )


def main():
    prepare_data()
    clocks, loggers = create_clients()
    servers = []

    try:
        servers = start_servers(clocks, loggers)

        print("\nIniciando experimentos gRPC")
        run_exchanges(clocks, loggers)

        print("\nIniciando mediciones de latencia gRPC")
        run_latency_tests(clocks, loggers)

        print("\nIniciando prueba de concurrencia gRPC")
        run_concurrency_test(clocks, loggers)

        print("\nExperimentos gRPC finalizados")
        print("Archivos generados en data/")

    finally:
        if servers:
            stop_servers(servers)


if __name__ == "__main__":
    main()