
import csv
import tempfile
import unittest

from pathlib import Path

from analysis.verify_lamport import (
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


if __name__ == "__main__":
    unittest.main()
