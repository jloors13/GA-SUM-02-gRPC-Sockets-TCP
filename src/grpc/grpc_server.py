from concurrent import futures
import sys

import grpc

from proto import servicio_pb2, servicio_pb2_grpc
from src.common.lamport import LamportClock
from src.common.event_logger import EventLogger


class ComunicacionNodosServicer(servicio_pb2_grpc.ComunicacionNodosServicer):

    def __init__(self, node_name, clock, logger):
        self.node_name = node_name
        self.clock = clock
        self.logger = logger

    def EnviarMensaje(self, request, context):
        if not request.sender:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Emisor invalido")

        if request.timestamp < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Timestamp invalido")

        received_timestamp = self.clock.after_receive(request.timestamp)
        self.logger.log_event(self.node_name, "receive", received_timestamp)

        response_timestamp = self.clock.before_send()
        self.logger.log_event(self.node_name, "send", response_timestamp)

        return servicio_pb2.Acuse(
            sender=self.node_name,
            received_timestamp=received_timestamp,
            timestamp=response_timestamp,
            message=f"ACK: {request.message}"
        )