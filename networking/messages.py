class Message:
    """ Parent Class for sending messages """

    def __init__(self, peer):
        self.peer = peer

    def setSourceSocket(self, socket):
        self.sourceSocket = socket

    def open(self, peerRouter):
        pass


class SendPeerListMessage(Message):
    """ Message to send when given a GetPeersMessage """

    def __init__(self, peer, peerList):
        super().__init__(peer)
        self.peerList = peerList

    def open(self, peerRouter):
        peerRouter.updatePeerList(self.peerList)


class GetPeerListMessage(Message):
    """ Message to send if peers are wanted """

    def __init__(self, peer, sender):
        super().__init__(peer)
        self.sender = sender

    def open(self, peerRouter):
        peerList = []
        with peerRouter.peerLock:
            peerList = [peer.copy() for peer in self.peerList.values()]
        msg = SendPeerListMessage(self.sender, peerList)
        peerRouter.pushTxBuffer(msg)


class ConnectPeerMessage(Message):
    """ Message to send when you wish to connect to another peer """

    def __init__(self, peer, sender):
        super().__init__(peer)

    def open(self, peerRouter):
        # Make sure there is a known socket and the message came from same ip as socket.
        if (self.sourceSocket and self.sourceSocket.getpeername()[0] == self.sender[0]):
            with peerRouter.peerLock:
                self.peer.socket = self.sourceSocket
                peerRouter.peerList[self.peer.getAddressInfo()] = self.peer
        else:
            print("No source socket found!\n")


class
