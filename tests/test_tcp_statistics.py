
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from analysis import tcp_statistics


class TestTCPStatistics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.csv_path = Path(self.temp_dir.name) / "latency.csv"

        self.data = pd.DataFrame({
            "mechanism": ["TCP"] * 5,
            "message_size": ["corto"] * 5,
            "message_bytes": [100] * 5,
            "repetition": [1] * 5,
            "sample": [1, 2, 3, 4, 5],
            "latency_ms": [2.0, 4.0, 6.0, 8.0, 10.0],
            "run_duration_s": [0.1] * 5,
            "throughput_msg_s": [50.0] * 5,
            "timestamp": ["2026-11-20T10:00:00-05:00"] * 5
        })

        self.data.to_csv(self.csv_path, index=False)

    def load_test_data(self):
        with patch.object(
            tcp_statistics, "INPUT_FILE", self.csv_path
        ):
            return tcp_statistics.load_data()

    def test_loads_valid_csv(self):
        data = self.load_test_data()
        self.assertEqual(len(data), 5)

    def test_calculates_mean(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertAlmostEqual(result.iloc[0]["mean_ms"], 6.0)

    def test_calculates_median(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertAlmostEqual(result.iloc[0]["median_ms"], 6.0)

    def test_calculates_minimum_and_maximum(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertEqual(result.iloc[0]["minimum_ms"], 2.0)
        self.assertEqual(result.iloc[0]["maximum_ms"], 10.0)

    def test_calculates_standard_deviation(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertAlmostEqual(
            result.iloc[0]["std_ms"],
            3.1622776601683795
        )

    def test_calculates_p95(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertAlmostEqual(result.iloc[0]["p95_ms"], 9.6)

    def test_calculates_throughput(self):
        result = tcp_statistics.calculate_statistics(self.data)
        self.assertEqual(
            result.iloc[0]["mean_throughput_msg_s"],
            50.0
        )

    def test_rejects_missing_columns(self):
        invalid = self.data.drop(columns=["latency_ms"])
        invalid.to_csv(self.csv_path, index=False)

        with self.assertRaises(ValueError):
            self.load_test_data()

    def test_rejects_negative_latency(self):
        invalid = self.data.copy()
        invalid.loc[0, "latency_ms"] = -1
        invalid.to_csv(self.csv_path, index=False)

        with self.assertRaises(ValueError):
            self.load_test_data()

    def test_rejects_invalid_numeric_values(self):
        invalid = self.data.copy()
        invalid["latency_ms"] = ["error"] * 5
        invalid.to_csv(self.csv_path, index=False)

        with self.assertRaises(ValueError):
            self.load_test_data()


if __name__ == "__main__":
    unittest.main(verbosity=2)
