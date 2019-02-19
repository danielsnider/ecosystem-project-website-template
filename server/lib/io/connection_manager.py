import logging
import socket

from lib.io.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, message_handler, closed_handler):
        self._connections = {}
        self._message_handler = message_handler
        self._closed_handler = closed_handler

    def register_connection(self, opened_socket, address):
        self._connections[address] = Connection(
            opened_socket,
            address,
            self._message_handler,
            self._closed_handler,
        )
        self._connections[address].start()

    def remove_connection(self, address):
        connection = self.get_connection(address)
        connection.stop()
        del self._connections[address]
        logger.debug("Removed connection to (%s:%d).", *address)

    def get_connection(self, address):
        if address not in self._connections:
            host, port = address
            raise ValueError(
                "Connection to ({}:{}) does not exist.".format(host, port))
        return self._connections[address]

    def broadcast(self, string_message):
        for _, connection in self._connections.items():
            connection.write_string_message(string_message)

    def connect_to(self, host, port):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.connect((host, port))
        self.register_connection(new_socket, (host, port))

    def stop(self):
        for _, connection in self._connections.items():
            connection.stop()
        self._connections.clear()
