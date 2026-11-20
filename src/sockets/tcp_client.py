
import json
import socket

from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger


def send_message(host: str, port: int, sender: str,
                 clock: LamportClock, logger: EventLogger,
                 message: str) -> dict:

    timestamp = clock.before_send()
    logger.log_event(sender, "send", timestamp)

    request = {
        "sender": sender,
        "timestamp": timestamp,
        "message": message
    }

    with socket.create_connection((host, port), timeout=5) as connection:
        with connection.makefile("rwb") as stream:
            stream.write(
                (json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8")
            )
            stream.flush()

            response_line = stream.readline()

    if not response_line:
        raise ConnectionError("El servidor no envio respuesta")

    response = json.loads(response_line.decode("utf-8"))

    if "error" in response:
        raise ValueError(response["error"])

    received_timestamp = response["timestamp"]
    clock.after_receive(received_timestamp)

    logger.log_event(sender, "receive", clock.time)

    return response
