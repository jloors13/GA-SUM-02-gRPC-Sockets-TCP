
import csv
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from src.common.event_logger import EventLogger


class TestEventLogger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "events.csv"
        self.logger = EventLogger(str(self.file_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_events(self):
        with self.file_path.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            return list(csv.DictReader(file))

    def test_creates_csv_with_header(self):
        with self.file_path.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            reader = csv.reader(file)
            header = next(reader)

        self.assertEqual(
            header,
            ["node", "event_type", "lamport_time", "real_time"]
        )

    def test_registers_send_event(self):
        self.logger.log_event("nodo-A", "send", 1)

        events = self.read_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["node"], "nodo-A")
        self.assertEqual(events[0]["event_type"], "send")
        self.assertEqual(events[0]["lamport_time"], "1")
        self.assertTrue(events[0]["real_time"])

    def test_registers_receive_event(self):
        self.logger.log_event("nodo-B", "receive", 2)

        events = self.read_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["node"], "nodo-B")
        self.assertEqual(events[0]["event_type"], "receive")
        self.assertEqual(events[0]["lamport_time"], "2")

    def test_rejects_invalid_event_type(self):
        with self.assertRaises(ValueError):
            self.logger.log_event("nodo-A", "invalid", 3)

        self.assertEqual(len(self.read_events()), 0)

    def test_registers_multiple_events(self):
        self.logger.log_event("nodo-A", "send", 1)
        self.logger.log_event("nodo-B", "receive", 2)
        self.logger.log_event("nodo-A", "send", 3)

        self.assertEqual(len(self.read_events()), 3)

    def test_concurrent_event_registration(self):
        total_events = 200

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(
                lambda index: self.logger.log_event(
                    "nodo-A",
                    "send" if index % 2 == 0 else "receive",
                    index + 1
                ),
                range(total_events)
            ))

        events = self.read_events()

        self.assertEqual(len(events), total_events)
        self.assertEqual(
            sum(event["event_type"] == "send" for event in events),
            100
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)