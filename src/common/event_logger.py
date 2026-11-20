
import csv
from datetime import datetime
from pathlib import Path
from threading import Lock


class EventLogger:

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            with self.file_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "node",
                    "event_type",
                    "lamport_time",
                    "real_time"
                ])

    def log_event(self, node: str, event_type: str, lamport_time: int):
        if event_type not in ("send", "receive"):
            raise ValueError("El tipo de evento debe ser send o receive")

        event = [
            node,
            event_type,
            lamport_time,
            datetime.now().astimezone().isoformat(timespec="microseconds")
        ]

        with self._lock:
            with self.file_path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(event)
