import tempfile
import time
import unittest
from pathlib import Path

from src.common.event_logger import EventLogger
from src.common.lamport import LamportClock
from src.grpc.grpc_client import send_message
from src.grpc.grpc_server import create_server


class TestGrpcClient(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.host = "127.0.0.1"
        self.port = 5055

        self.server_clock = LamportClock("nodo-B")
        self.server_logger = EventLogger(
            str(Path(self.temp_dir.name) / "server_events.csv")
        )
        self.server = create_server(
            "nodo-B",
            self.host,
            self.port,
            self.server_clock,
            self.server_logger,
        )
        self.server.start()
        time.sleep(0.2)

        self.client_clock = LamportClock("nodo-A")
        self.client_logger = EventLogger(
            str(Path(self.temp_dir.name) / "client_events.csv")
        )

    def tearDown(self):
        self.server.stop(1)
        self.temp_dir.cleanup()

    def test_envio_valido_y_reloj_lamport(self):
        response = send_message(
            self.host,
            self.port,
            "nodo-A",
            self.client_clock,
            self.client_logger,
            "Mensaje de prueba",
        )

        self.assertEqual(response["sender"], "nodo-B")
        self.assertEqual(response["message"], "ACK: Mensaje de prueba")
        self.assertGreater(response["received_timestamp"], 1)
        self.assertGreater(response["timestamp"], response["received_timestamp"])
        self.assertGreater(self.client_clock.time, response["timestamp"])

    def test_error_emisor_vacio(self):
        with self.assertRaises(RuntimeError):
            send_message(
                self.host,
                self.port,
                "",
                self.client_clock,
                self.client_logger,
                "Sin emisor",
            )

    def test_error_servidor_inaccesible(self):
        with self.assertRaises(RuntimeError):
            send_message(
                self.host,
                5099,
                "nodo-A",
                self.client_clock,
                self.client_logger,
                "Puerto cerrado",
                timeout=1.0,
            )


if __name__ == "__main__":
    unittest.main()