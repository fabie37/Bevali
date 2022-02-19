from enum import Enum
from http import server
import logging

""" Networking constants """


HEADERSIZE = 40

""" Networking enumations """


class ServerStatus(Enum):
    INIT = 1
    RUNNING = 2
    STOPPED = 3
    CLOSING = 4
    ERROR = 5


""" Logging Handles"""
logFormat = logging.Formatter(" %(levelname)s - %(name)s - %(message)s")
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
streamHandler.setFormatter(logFormat)
serverLogger = logging.getLogger("Server")
serverLogger.setLevel(logging.CRITICAL)
serverLogger.addHandler(streamHandler)
peerLogger = logging.getLogger("Peer")
peerLogger.setLevel(logging.INFO)
