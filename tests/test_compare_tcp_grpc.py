
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analysis.compare_tcp_grpc import (
    load_latency_file,
    load_concurrency_file,
    calculate_statistics,
    compare_mechanisms,
    calculate_concurrency,
)


class TestCompareTCPGrpc(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "latency.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_carga_archivo_tcp_valido(self):
        data = pd.DataFrame([{
            "mechanism": "TCP",
            "message_size": "corto",
            "message_bytes": 100,
            "repetition": 1,
            "sample": 1,
            "latency_ms": 5.0,
            "run_duration_s": 0.5,
            "throughput_msg_s": 200.0,
            "timestamp": "2026-11-20T13:00:00"
        }])

        data.to_csv(self.path, index=False)

        result = load_latency_file(self.path, "TCP")

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["mechanism"], "TCP")

    def test_rechaza_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            load_latency_file(
                Path(self.temp_dir.name) / "inexistente.csv",
                "TCP"
            )

    def test_rechaza_mecanismo_incorrecto(self):
        data = pd.DataFrame([{
            "mechanism": "gRPC",
            "message_size": "corto",
            "message_bytes": 100,
            "repetition": 1,
            "sample": 1,
            "latency_ms": 5.0,
            "run_duration_s": 0.5,
            "throughput_msg_s": 200.0,
            "timestamp": "2026-11-20T13:00:00"
        }])

        data.to_csv(self.path, index=False)

        with self.assertRaises(ValueError):
            load_latency_file(self.path, "TCP")

    def test_calcula_estadisticas(self):
        data = pd.DataFrame([
            {
                "mechanism": "TCP",
                "message_size": "corto",
                "message_bytes": 100,
                "latency_ms": 4.0,
                "throughput_msg_s": 200.0
            },
            {
                "mechanism": "TCP",
                "message_size": "corto",
                "message_bytes": 100,
                "latency_ms": 6.0,
                "throughput_msg_s": 180.0
            }
        ])

        result = calculate_statistics(data)

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0]["mean_ms"], 5.0)
        self.assertAlmostEqual(result.iloc[0]["median_ms"], 5.0)
        self.assertEqual(result.iloc[0]["samples"], 2)

    def test_compara_tcp_y_grpc(self):
        data = pd.DataFrame([
            {
                "mechanism": "TCP",
                "message_size": "corto",
                "samples": 100,
                "mean_ms": 8.0,
                "std_ms": 2.0,
                "mean_throughput_msg_s": 100.0
            },
            {
                "mechanism": "gRPC",
                "message_size": "corto",
                "samples": 100,
                "mean_ms": 4.0,
                "std_ms": 1.0,
                "mean_throughput_msg_s": 200.0
            }
        ])

        result = compare_mechanisms(data)

        self.assertAlmostEqual(
            result.iloc[0]["grpc_latency_reduction_percent"],
            50.0
        )

        self.assertAlmostEqual(
            result.iloc[0]["grpc_throughput_change_percent"],
            100.0
        )

    def test_calcula_concurrencia(self):
        tcp = pd.DataFrame({
            "latency_ms": [5.0, 6.0, 7.0],
            "response": ["ACK", "ACK", "ACK"]
        })

        grpc = pd.DataFrame({
            "latency_ms": [10.0, 12.0, 14.0],
            "response": ["ACK", "ACK", "ACK"]
        })

        result = calculate_concurrency(tcp, grpc)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result.iloc[0]["successful_responses"], 3
        )
        self.assertAlmostEqual(
            result.iloc[0]["mean_ms"], 6.0
        )
        self.assertAlmostEqual(
            result.iloc[1]["mean_ms"], 12.0
        )

    def test_rechaza_rutas_concurrentes_incompletas(self):
        data = pd.DataFrame([{
            "sender": "nodo-A",
            "destination": "nodo-B",
            "latency_ms": 5.0,
            "response": "ACK",
            "timestamp": "2026-11-20T13:00:00"
        }])

        expected = {
            ("nodo-A", "nodo-B"),
            ("nodo-B", "nodo-C"),
            ("nodo-C", "nodo-A")
        }

        data.to_csv(self.path, index=False)

        with self.assertRaises(ValueError):
            load_concurrency_file(self.path, expected)


if __name__ == "__main__":
    unittest.main()
