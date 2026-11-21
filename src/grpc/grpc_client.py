import sys
import grpc

from proto import servicio_pb2, servicio_pb2_grpc
from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger


NODES = {
    "nodo-A": ("127.0.0.1", 5000),
    "nodo-B": ("127.0.0.1", 5001),
    "nodo-C": ("127.0.0.1", 5002),
}


def send_message(host, port, sender, clock, logger, message, timeout=5.0):
    send_timestamp = clock.before_send()
    logger.log_event(sender, "send", send_timestamp)

    request = servicio_pb2.Mensaje(
        sender=sender,
        timestamp=send_timestamp,
        message=message,
    )

    try:
        with grpc.insecure_channel(f"{host}:{port}") as channel:
            stub = servicio_pb2_grpc.ComunicacionNodosStub(channel)
            response = stub.EnviarMensaje(request, timeout=timeout)
    except grpc.RpcError as error:
        raise RuntimeError(
            f"Error gRPC al enviar de {sender} a {host}:{port}: "
            f"{error.code().name} - {error.details()}"
        ) from error

    receive_timestamp = clock.after_receive(response.timestamp)
    logger.log_event(sender, "receive", receive_timestamp)

    return {
        "sender": response.sender,
        "received_timestamp": response.received_timestamp,
        "timestamp": response.timestamp,
        "message": response.message,
    }


def main():
    if len(sys.argv) < 4:
        print('Uso: python -m src.grpc.grpc_client nodo-A nodo-B "Hola"')
        return

    sender = sys.argv[1]
    destination = sys.argv[2]
    message = " ".join(sys.argv[3:])

    if sender not in NODES or destination not in NODES:
        print("Nodos validos: nodo-A, nodo-B, nodo-C")
        return

    host, port = NODES[destination]
    clock = LamportClock(sender)
    logger = EventLogger(f"data/grpc_events_{sender}.csv")

    response = send_message(host, port, sender, clock, logger, message)
    print(f"Respuesta de {response['sender']}: {response['message']}")
    print(f"Reloj local final de {sender}: {clock.time}")


if __name__ == "__main__":
    main()