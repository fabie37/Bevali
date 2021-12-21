import pickle


from networking import HEADERSIZE
from networking import peerLogger


class Peer:
    """ Class to encapsulate sending data to peers"""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.headersize = HEADERSIZE
        self.socket = None

    def getAddressInfo(self):
        """ Return socket format for address """
        return (self.ip, self.port)

    def copy(self):
        """ Returns a copy of this peer (without socket reference)"""
        return Peer(self.ip, self.port)

    def send(self, data):
        """Sends data to a specific peer"""
        try:
            pickleData = pickle.dumps(data)
            msg = bytes(f'{len(pickleData):<{self.headersize}}',
                        'utf-8') + pickleData
            self.socket.send(msg)
            return True
        except TypeError:
            peerLogger.exception("Cannot pickle message!")
            raise TypeError
        except Exception:
            peerLogger.exception("Cannot connect to peer!")
            raise ConnectionError


# peer = Peer("127.0.0.1", 1234)
# peer.send("Give mme something?")
# inputsome = 0
# while inputsome != "stop":
#     inputsome = input("Type stop to stop")
#     if inputsome == "stop":
#         exit()
#     msg_len = peer.socket.recv(HEADERSIZE)
#     msg = peer.socket.recv(int(msg_len.decode("utf-8").strip()))
#     print(pickle.loads(msg))
#     peer.socket.send(HEADERSIZE)
#     peer.socket.send("hello world".encode("utf-8"))
