
import csv
import tempfile
import unittest
from pathlib import Path

from analysis.validate_experiment_data import (
    load_csv,
    validate_latency,
    validate_exchanges,
    validate_concurrency,
    validate_statistics,
)


class TestValidateExperimentData(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "prueba.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def crear_csv(self, columnas, filas):
        with self.path.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=columnas)
            writer.writeheader()
            writer.writerows(filas)

    def crear_latencia(self, **cambios):
        fila = {
            "mechanism": "TCP",
            "message_size": "corto",
            "message_bytes": "100",
            "repetition": "1",
            "sample": "1",
            "latency_ms": "5.2",
            "run_duration_s": "0.5",
            "throughput_msg_s": "200",
            "timestamp": "2026-11-20T13:00:00"
        }
        fila.update(cambios)
        return [fila]

    def test_rechaza_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            load_csv(
                self.path.parent / "archivo_inexistente.csv",
                "latency"
            )

    def test_rechaza_columnas_faltantes(self):
        self.crear_csv(
            ["mechanism", "latency_ms"],
            [{"mechanism": "TCP", "latency_ms": "5.2"}]
        )

        with self.assertRaises(ValueError):
            load_csv(self.path, "latency")

    def test_rechaza_csv_sin_registros(self):
        columnas = [
            "mechanism",
            "message_size",
            "message_bytes",
            "repetition",
            "sample",
            "latency_ms",
            "run_duration_s",
            "throughput_msg_s",
            "timestamp"
        ]

        self.crear_csv(columnas, [])

        with self.assertRaises(ValueError):
            load_csv(self.path, "latency")

    def test_acepta_latencia_valida(self):
        filas = self.crear_latencia()
        validate_latency(filas)

    def test_rechaza_latencia_negativa(self):
        filas = self.crear_latencia(latency_ms="-5")

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_latencia_nan(self):
        filas = self.crear_latencia(latency_ms="NaN")

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_latencia_infinita(self):
        filas = self.crear_latencia(latency_ms="Infinity")

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_throughput_infinito(self):
        filas = self.crear_latencia(
            throughput_msg_s="Infinity"
        )

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_repeticion_cero(self):
        filas = self.crear_latencia(repetition="0")

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_tamano_mensaje_cero(self):
        filas = self.crear_latencia(message_bytes="0")

        with self.assertRaises(ValueError):
            validate_latency(filas)

    def test_rechaza_orden_lamport_incorrecto(self):
        filas = [{
            "exchange": "1",
            "sender": "nodo-A",
            "destination": "nodo-B",
            "message": "Hola",
            "sender_timestamp": "5",
            "receiver_timestamp": "3",
            "response_timestamp": "6",
            "client_receive_timestamp": "7",
            "response": "ACK",
            "timestamp": "2026-11-20T13:00:00"
        }]

        with self.assertRaises(ValueError):
            validate_exchanges(filas)

    def test_rechaza_nodo_desconocido(self):
        filas = [{
            "sender": "nodo-X",
            "destination": "nodo-B",
            "latency_ms": "5.2",
            "response": "ACK",
            "timestamp": "2026-11-20T13:00:00"
        }]

        with self.assertRaises(ValueError):
            validate_concurrency(filas)

    def test_rechaza_estadisticas_incoherentes(self):
        filas = [{
            "mechanism": "TCP",
            "message_size": "corto",
            "message_bytes": "100",
            "samples": "500",
            "mean_ms": "5",
            "median_ms": "4",
            "minimum_ms": "10",
            "maximum_ms": "2",
            "std_ms": "1",
            "p95_ms": "6",
            "mean_throughput_msg_s": "100"
        }]

        with self.assertRaises(ValueError):
            validate_statistics(filas)


if __name__ == "__main__":
    unittest.main()
