
import csv
import tempfile
import unittest
from unittest.mock import call, patch

from pathlib import Path

from analysis.verify_lamport import (
    main,
    verify_events,
    verify_exchanges,
)


class TestVerifyLamport(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_events_file(self, rows):
        path = self.directory / "events.csv"

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "node",
                "event_type",
                "lamport_time",
                "real_time"
            ])
            writer.writerows(rows)

        return path

    def create_exchanges_file(self, rows):
        path = self.directory / "exchanges.csv"

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "exchange",
                "sender",
                "destination",
                "sender_timestamp",
                "receiver_timestamp",
                "response_timestamp",
                "client_receive_timestamp"
            ])
            writer.writerows(rows)

        return path

    def test_accepts_valid_events(self):
        path = self.create_events_file([
            ["nodo-A", "send", 1, "2026-11-20T10:00:00"],
            ["nodo-A", "receive", 4, "2026-11-20T10:00:01"],
            ["nodo-A", "send", 5, "2026-11-20T10:00:02"],
        ])

        self.assertEqual(verify_events(path, "nodo-A"), 3)

    def test_rejects_missing_file(self):
        path = self.directory / "missing.csv"

        with self.assertRaises(FileNotFoundError):
            verify_events(path, "nodo-A")

    def test_rejects_incomplete_columns(self):
        path = self.directory / "invalid.csv"
        path.write_text("node,event_type\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            verify_events(path, "nodo-A")

    def test_rejects_invalid_timestamp(self):
        path = self.create_events_file([
            ["nodo-A", "send", "abc", "2026-11-20T10:00:00"],
        ])

        with self.assertRaises(ValueError):
            verify_events(path, "nodo-A")

    def test_rejects_invalid_event_type(self):
        path = self.create_events_file([
            ["nodo-A", "unknown", 1, "2026-11-20T10:00:00"],
        ])

        with self.assertRaises(ValueError):
            verify_events(path, "nodo-A")

    def test_rejects_wrong_node(self):
        path = self.create_events_file([
            ["nodo-B", "send", 1, "2026-11-20T10:00:00"],
        ])

        with self.assertRaises(ValueError):
            verify_events(path, "nodo-A")

    def test_accepts_new_session(self):
        path = self.create_events_file([
            ["nodo-A", "send", 100, "2026-11-20T10:00:00"],
            ["nodo-A", "send", 1, "2026-11-20T10:02:00"],
        ])

        self.assertEqual(verify_events(path, "nodo-A"), 2)

    def test_rejects_unexpected_regression(self):
        path = self.create_events_file([
            ["nodo-A", "send", 10, "2026-11-20T10:00:00"],
            ["nodo-A", "receive", 5, "2026-11-20T10:00:01"],
        ])

        with self.assertRaises(ValueError):
            verify_events(path, "nodo-A")

    def test_accepts_valid_exchange(self):
        path = self.create_exchanges_file([
            [1, "nodo-A", "nodo-B", 1, 2, 3, 4],
        ])

        self.assertEqual(verify_exchanges(path), 1)

    def test_rejects_invalid_exchange_order(self):
        path = self.create_exchanges_file([
            [1, "nodo-A", "nodo-B", 1, 3, 2, 4],
        ])

        with self.assertRaises(ValueError):
            verify_exchanges(path)

    def test_rejects_same_sender_and_destination(self):
        path = self.create_exchanges_file([
            [1, "nodo-A", "nodo-A", 1, 2, 3, 4],
        ])

        with self.assertRaises(ValueError):
            verify_exchanges(path)

    def test_rejects_empty_exchanges(self):
        path = self.create_exchanges_file([])

        with self.assertRaises(ValueError):
            verify_exchanges(path)

    def test_grpc_events_valid_for_each_node(self):
        for node in ("nodo-A", "nodo-B", "nodo-C"):
            with self.subTest(node=node):
                path = self.create_events_file([
                    [node, "send", 1, "2026-11-20T10:00:00"],
                    [node, "receive", 4, "2026-11-20T10:00:01"],
                ])
                self.assertEqual(verify_events(path, node), 2)

    def test_grpc_events_reject_bad_timestamp(self):
        path = self.create_events_file([
            ["nodo-A", "send", "bad", "2026-11-20T10:00:00"],
        ])
        with self.assertRaisesRegex(ValueError, "timestamp inválido"):
            verify_events(path, "nodo-A")

    def test_grpc_events_reject_wrong_node(self):
        path = self.create_events_file([
            ["nodo-B", "send", 1, "2026-11-20T10:00:00"],
        ])
        with self.assertRaisesRegex(ValueError, "nodo incorrecto"):
            verify_events(path, "nodo-A")

    def test_grpc_exchanges_reject_invalid_causal_order(self):
        path = self.create_exchanges_file([
            [1, "nodo-A", "nodo-B", 1, 3, 2, 4],
        ])
        with self.assertRaisesRegex(ValueError, "orden causal incorrecto"):
            verify_exchanges(path)

    def test_grpc_files_report_missing_and_malformed_data(self):
        missing = self.directory / "grpc_events_nodo-C.csv"
        with self.assertRaisesRegex(FileNotFoundError, "No existe el archivo"):
            verify_events(missing, "nodo-C")

        malformed = self.directory / "grpc_exchanges.csv"
        malformed.write_text("exchange,sender\n1,nodo-A\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Faltan columnas"):
            verify_exchanges(malformed)

    def test_main_checks_tcp_and_grpc_files(self):
        with patch("analysis.verify_lamport.verify_events") as events, patch(
            "analysis.verify_lamport.verify_exchanges", return_value=1
        ) as exchanges:
            main()

        self.assertEqual(events.call_args_list, [
            call(f"data/tcp_events_{node}.csv", node)
            for node in ("nodo-A", "nodo-B", "nodo-C")
        ] + [
            call(f"data/grpc_events_{node}.csv", node)
            for node in ("nodo-A", "nodo-B", "nodo-C")
        ])
        self.assertEqual(exchanges.call_args_list, [
            call("data/tcp_exchanges.csv"),
            call("data/grpc_exchanges.csv"),
        ])


if __name__ == "__main__":
    unittest.main()
