import socket
import pickle

from constants import HEADERSIZE


class Peer:
    """ Class to encapsulate sending data to peers"""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.headersize = HEADERSIZE
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, data):
        """Sends data to a specific peer"""
        jsonData = pickle.dumps(data)
        msg = bytes(f'{len(jsonData):<{self.headersize}}', 'utf-8') + jsonData
        self.socket.connect((self.ip, self.port))
        self.socket.send(msg)


peer = Peer(socket.gethostname(), 1234)
peer.send({"BlockSize": 3000})
