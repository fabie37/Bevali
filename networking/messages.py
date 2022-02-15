
class Message:
    """ Parent Class for sending messages """

    def __init__(self, toPeer, fromPeer):
        self.toPeer = toPeer
        self.fromPeer = fromPeer

    def setSourceSocket(self, socket, address):
        self.sourceSocket = socket
        self.sourceAddress = address

    def open(self, peerRouter):
        if self.fromPeer not in peerRouter.peerAddressToSocket:
            self.sourceSocket.close()


class ConnectMessage(Message):
    """ Message to send when you wish to connect to another peer """

    def __init__(self, toPeer, fromPeer):
        super().__init__(toPeer, fromPeer)

    def open(self, peerRouter):
        socketAddress = self.sourceAddress

        # Make sure there is a known socket
        if (self.sourceSocket):
            with peerRouter.peerLock:
                if (self.fromPeer not in peerRouter.peerAddressToSocket or peerRouter.peerAddressToSocket[self.fromPeer].fileno() == -1):
                    # Add person who sent the message to socket mapping
                    # Socket Specific Address -> fromPeer
                    peerRouter.socketAddressToPeerAddress[socketAddress] = self.fromPeer

                    # Peer Address -> Socket
                    peerRouter.peerAddressToSocket[self.fromPeer] = self.sourceSocket

                    # For Socket Listener
                    peerRouter.socketList.append(self.sourceSocket)

                    # Alert Application new peer connected
                    peerRouter.newPeerQueue.put(self.fromPeer)
                else:
                    print("Socket already here!")

            # Accept the connection
            toPeer = self.fromPeer
            fromPeer = (peerRouter.hostname, peerRouter.port)
            acceptMsg = AcceptedConnectMessage(toPeer, fromPeer)
            peerRouter.txbuffer.put(acceptMsg)
        else:
            print("No source socket found!\n")


class AcceptedConnectMessage(Message):
    def __init__(self, toPeer, fromPeer):
        super().__init__(toPeer, fromPeer)

    def open(self, peerRouter):
        address = (self.fromPeer[0], self.fromPeer[1])
        try:
            with peerRouter.signalList[address]:
                peerRouter.signalList[address].notify()
        except Exception:
            # No signal exists! Ignore
            print("No such signal exists!")


class PeerRequestMessage(Message):
    """ Message to send if you want a peer to tell their peers to conenct to you"""

    def __init__(self, toPeer, fromPeer):
        super().__init__(toPeer, fromPeer)

    def open(self, peerRouter):
        for peerAddress in peerRouter.peerAddressToSocket.keys():
            if (peerAddress != self.fromPeer):
                toPeer = peerAddress
                fromPeer = (peerRouter.hostname, peerRouter.port)
                newPeer = self.fromPeer

                # Tell my peers to connect to new peer
                updateMsg = NewPeerUpdateMessage(toPeer, fromPeer, newPeer)
                peerRouter.txbuffer.put(updateMsg)


class NewPeerUpdateMessage(Message):
    """ Message to send to peers to tell them to connect to a new peer"""

    def __init__(self, toPeer, fromPeer, newPeer):
        super().__init__(toPeer, fromPeer)
        self.newPeer = newPeer

    def open(self, peerRouter):
        peerRouter.connect(self.newPeer[0], self.newPeer[1])


class GetPeerListMessage(Message):
    """ Message to send if peer list is wanted """

    def __init__(self, toPeer, fromPeer):
        super().__init__(toPeer, fromPeer)

    def open(self, peerRouter):
        peerList = []
        with peerRouter.peerLock:
            peerList = [peerAddress for peerAddress in peerRouter.peerAddressToSocket.keys(
            ) if peerAddress != self.fromPeer]

        # fromPeer is a tuple (ip,port)
        # From the person opening the message
        fromPeer = (peerRouter.hostname, peerRouter.port)

        # To peer is the person who sent the request
        toPeer = self.fromPeer
        msg = SendPeerListMessage(toPeer, fromPeer, peerList)
        peerRouter.txbuffer.put(msg)


class SendPeerListMessage(Message):
    """ Message to send when given a GetPeersMessage """

    def __init__(self, toPeer, fromPeer, peerList):
        super().__init__(toPeer, fromPeer)
        self.peerList = peerList

    def open(self, peerRouter):
        # If you get a reply from a peer about their client list, connect to those peers
        for peerAddress in self.peerList:
            peerRouter.connect(peerAddress[0], peerAddress[1])


class DataMessage(Message):
    """ Message to send when wanting to give peer data """

    def __init__(self, toPeer, fromPeer, data):
        super().__init__(toPeer, fromPeer)
        self.data = data

    def open(self, peerRouter):
        # If open, push to data buffer
        if (self.data):
            peerRouter.databuffer.put((self.fromPeer, self.data))

        # Notify signal for testing
        with peerRouter.threadManager.getThreadSignal("Message Thread"):
            peerRouter.threadManager.getThreadSignal("Message Thread").notify()
