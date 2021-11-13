import socket
import pickle
import logging
from typing import Type

from config import HEADERSIZE
from config import peerLogger

from server import Server


class Peer:
    """ Class to encapsulate sending data to peers"""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.headersize = HEADERSIZE
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, data):
        """Sends data to a specific peer"""
        try:
            pickleData = pickle.dumps(data)
            msg = bytes(f'{len(pickleData):<{self.headersize}}',
                        'utf-8') + pickleData
            self.socket.connect((self.ip, self.port))
            self.socket.send(msg)
            self.socket.close()
            return True
        except TypeError:
            peerLogger.exception("Cannot pickle message!")
            raise TypeError
        except Exception:
            peerLogger.exception("Cannot connect to peer!")
            raise ConnectionError


# peer = Peer(socket.gethostname(), 1234)
# peer.send({"1": 1})
