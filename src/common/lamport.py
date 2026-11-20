
from threading import Lock


class LamportClock:

    def __init__(self, node_name: str):
        self.node_name = node_name
        self._time = 0
        self._lock = Lock()

    @property
    def time(self) -> int:
        with self._lock:
            return self._time

    def before_send(self) -> int:
        with self._lock:
            self._time += 1
            return self._time

    def after_receive(self, received_timestamp: int) -> int:
        if received_timestamp < 0:
            raise ValueError("El timestamp no puede ser negativo")

        with self._lock:
            self._time = max(self._time, received_timestamp) + 1
            return self._time
