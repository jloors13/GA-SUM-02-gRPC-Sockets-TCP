
import unittest
from concurrent.futures import ThreadPoolExecutor

from src.common.lamport import LamportClock


class TestLamportClock(unittest.TestCase):

    def setUp(self):
        self.clock = LamportClock("nodo-A")

    def test_initial_time(self):
        self.assertEqual(self.clock.time, 0)

    def test_before_send_increments_clock(self):
        self.assertEqual(self.clock.before_send(), 1)
        self.assertEqual(self.clock.before_send(), 2)
        self.assertEqual(self.clock.before_send(), 3)

    def test_after_receive_updates_clock(self):
        received_time = self.clock.after_receive(5)

        self.assertEqual(received_time, 6)
        self.assertEqual(self.clock.time, 6)

    def test_after_receive_preserves_logical_order(self):
        self.clock.before_send()

        received_time = self.clock.after_receive(0)

        self.assertEqual(received_time, 2)

    def test_negative_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.clock.after_receive(-1)

    def test_concurrent_access(self):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(
                executor.map(
                    lambda _: self.clock.before_send(),
                    range(1000)
                )
            )

        self.assertEqual(len(set(results)), 1000)
        self.assertEqual(sorted(results), list(range(1, 1001)))
        self.assertEqual(self.clock.time, 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
