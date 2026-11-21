import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

import grpc

from proto import servicio_pb2, servicio_pb2_grpc
from src.common.lamport import LamportClock
from src.grpc.grpc_server import create_server


class FakeLogger:
    """Guarda los eventos en memoria en vez de escribir un CSV."""
    def __init__(self):
        self.events = []

    def log_event(self, node, event_type, lamport_time):
        self.events.append((node, event_type, lamport_time))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestGrpcServer(unittest.TestCase):
    def setUp(self):
        self.port = free_port()
        self.logger = FakeLogger()
        self.server = create_server("nodo-X", "127.0.0.1", self.port,
                                    LamportClock("nodo-X"), self.logger)
        self.server.start()
        self.channel = grpc.insecure_channel(f"127.0.0.1:{self.port}")
        self.stub = servicio_pb2_grpc.ComunicacionNodosStub(self.channel)

    def tearDown(self):
        self.channel.close()
        self.server.stop(0)

    def test_llamada_valida(self):
        r = self.stub.EnviarMensaje(
            servicio_pb2.Mensaje(sender="nodo-A", timestamp=5, message="hola"))
        self.assertEqual(r.sender, "nodo-X")
        self.assertEqual(r.received_timestamp, 6)   # max(0,5)+1
        self.assertEqual(r.timestamp, 7)            # before_send
        self.assertEqual(r.message, "ACK: hola")

    def test_emisor_vacio(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.EnviarMensaje(
                servicio_pb2.Mensaje(sender="", timestamp=1, message="x"))
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEqual(self.logger.events, [])



    def test_timestamp_negativo(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.EnviarMensaje(
                servicio_pb2.Mensaje(sender="nodo-A", timestamp=-1, message="x"))
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEqual(self.logger.events, [])

    def test_reloj_crece_entre_llamadas(self):
        r1 = self.stub.EnviarMensaje(
            servicio_pb2.Mensaje(sender="nodo-A", timestamp=0, message="1"))
        r2 = self.stub.EnviarMensaje(
            servicio_pb2.Mensaje(sender="nodo-A", timestamp=0, message="2"))
        self.assertGreater(r2.received_timestamp, r1.timestamp)

    def test_registra_receive_y_send(self):
        self.stub.EnviarMensaje(
            servicio_pb2.Mensaje(sender="nodo-A", timestamp=5, message="hola"))
        self.assertEqual(self.logger.events,
                         [("nodo-X", "receive", 6), ("nodo-X", "send", 7)])

    def test_concurrencia(self):
        def llamar(i):
            return self.stub.EnviarMensaje(
                servicio_pb2.Mensaje(sender="nodo-A", timestamp=0, message=str(i)))
        with ThreadPoolExecutor(max_workers=10) as ex:
            respuestas = list(ex.map(llamar, range(30)))
        self.assertEqual(len(respuestas), 30)
        tiempos = [r.timestamp for r in respuestas]
        self.assertEqual(len(set(tiempos)), 30)  # ningún timestamp repetido


if __name__ == "__main__":
    unittest.main()