from concurrent import futures
import sys

import grpc

from proto import servicio_pb2, servicio_pb2_grpc
from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger


NODES = {
    "nodo-A": ("127.0.0.1", 5000),
    "nodo-B": ("127.0.0.1", 5001),
    "nodo-C": ("127.0.0.1", 5002)
}


class ComunicacionNodosServicer(servicio_pb2_grpc.ComunicacionNodosServicer):

    def __init__(self, node_name, clock, logger):
        self.node_name = node_name
        self.clock = clock
        self.logger = logger

    def EnviarMensaje(self, request, context):
        if not request.sender:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Emisor invalido")

        if request.timestamp < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Timestamp invalido")

        received_timestamp = self.clock.after_receive(request.timestamp)
        self.logger.log_event(self.node_name, "receive", received_timestamp)

        response_timestamp = self.clock.before_send()
        self.logger.log_event(self.node_name, "send", response_timestamp)

        return servicio_pb2.Acuse(
            sender=self.node_name,
            received_timestamp=received_timestamp,
            timestamp=response_timestamp,
            message=f"ACK: {request.message}"
        )


def create_server(node_name, host, port, clock, logger):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ComunicacionNodosServicer(node_name, clock, logger)
    servicio_pb2_grpc.add_ComunicacionNodosServicer_to_server(servicer, server)
    server.add_insecure_port(f"{host}:{port}")
    return server


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in NODES:
        print("Uso: python -m src.grpc.grpc_server nodo-A")
        return

    node_name = sys.argv[1]
    host, port = NODES[node_name]

    clock = LamportClock(node_name)
    logger = EventLogger(f"data/grpc_events_{node_name}.csv")

    server = create_server(node_name, host, port, clock, logger)
    server.start()
    print(f"{node_name} gRPC iniciado en {host}:{port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nDeteniendo nodo...")
    finally:
        server.stop(2)
        print(f"{node_name} detenido.")


if __name__ == "__main__":
    main()