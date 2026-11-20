
import json
import socketserver

from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger


class TCPRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        node = self.server.node_name
        clock = self.server.clock
        logger = self.server.logger

        line = self.rfile.readline()

        if not line:
            return

        try:
            request = json.loads(line.decode("utf-8"))

            sender = request["sender"]
            timestamp = request["timestamp"]
            message = request["message"]

            if not isinstance(sender, str) or not sender:
                raise ValueError("Emisor invalido")

            if type(timestamp) is not int or timestamp < 0:
                raise ValueError("Timestamp invalido")

            if not isinstance(message, str):
                raise ValueError("Mensaje invalido")

            received_timestamp = clock.after_receive(timestamp)
            logger.log_event(node, "receive", received_timestamp)

            response_timestamp = clock.before_send()
            logger.log_event(node, "send", response_timestamp)

            response = {
                "sender": node,
                "received_timestamp": received_timestamp,
                "timestamp": response_timestamp,
                "message": f"ACK: {message}"
            }

            self.wfile.write(
                (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
            )

        except (ValueError, KeyError, json.JSONDecodeError) as error:
            response = {"error": str(error)}
            self.wfile.write(
                (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
            )


class TCPNodeServer(socketserver.ThreadingTCPServer):

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, node_name, clock, logger):
        self.node_name = node_name
        self.clock = clock
        self.logger = logger
        super().__init__(address, TCPRequestHandler)
