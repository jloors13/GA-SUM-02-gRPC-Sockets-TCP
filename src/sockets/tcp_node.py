
import sys
import threading

from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger
from src.sockets.tcp_server import TCPNodeServer
from src.sockets.tcp_client import send_message


NODES = {
    "nodo-A": ("127.0.0.1", 5000),
    "nodo-B": ("127.0.0.1", 5001),
    "nodo-C": ("127.0.0.1", 5002)
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in NODES:
        print("Uso: python -m src.sockets.tcp_node nodo-A")
        return

    node_name = sys.argv[1]
    host, port = NODES[node_name]

    clock = LamportClock(node_name)
    logger = EventLogger(f"data/tcp_events_{node_name}.csv")

    server = TCPNodeServer(
        (host, port),
        node_name,
        clock,
        logger
    )

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    server_thread.start()

    print(f"{node_name} iniciado en {host}:{port}")
    print("Nodos disponibles: nodo-A, nodo-B, nodo-C")
    print("Escribe salir para detener el nodo.")

    try:
        while True:
            destination = input("\nEnviar a: ").strip()

            if destination.lower() == "salir":
                break

            if destination not in NODES or destination == node_name:
                print("Destino no valido.")
                continue

            message = input("Mensaje: ")

            if not message.strip():
                print("El mensaje no puede estar vacio.")
                continue

            destination_host, destination_port = NODES[destination]

            try:
                response = send_message(
                    destination_host,
                    destination_port,
                    node_name,
                    clock,
                    logger,
                    message
                )

                print(f"Respuesta de {response['sender']}: {response['message']}")
                print(f"Reloj de Lamport: {clock.time}")

            except (OSError, ValueError, ConnectionError) as error:
                print(f"Error de comunicacion: {error}")

    except KeyboardInterrupt:
        print("\nDeteniendo nodo...")

    finally:
        server.shutdown()
        server.server_close()
        print(f"{node_name} detenido.")


if __name__ == "__main__":
    main()
