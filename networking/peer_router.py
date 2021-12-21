import socket
import select
import pickle
from queue import Empty, Queue
from networking import HEADERSIZE
from networking import ServerStatus
from networking import serverLogger
from multithreading import ThreadManager
from multithreading import ManagedThread
from multithreading import ThreadStatus
from threading import Lock
from threading import Condition

from networking.messages import ConnectMessage, DataMessage, GetPeerListMessage, Message, PeerRequestMessage


class PeerRouter:
    """ Class to encapsulate handling """

    def __init__(self, hostname, port, id=None):

        # Server Configuration Settings
        self.hostname = hostname
        self.port = port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Define Peers in sever
        self.peerLock = Lock()
        self.socketList = [self.serverSocket]
        self.socketAddressToPeerAddress = {}
        self.peerAddressToSocket = {}  # (Peer List)

        # Define Thread Manager
        self.threadManager = ThreadManager()

        # Status of server
        self.status = ServerStatus.INIT

        # TX Buffer handler
        self.txbuffer = Queue()
        txThread = ManagedThread(
            target=self.txThread, name="TX Thread")
        self.threadManager.addThread(txThread)

        # Message Handler
        msgThread = ManagedThread(
            target=self.msgThread, name="Message Thread")
        self.threadManager.addThread(msgThread)

        # RX Buffer handler
        self.rxbuffer = Queue()
        rxThread = ManagedThread(
            target=self.rxThread, name="RX Thread")
        self.threadManager.addThread(rxThread)

        # Signal List
        # This is used for any methods that need to be blocking
        # These are indexed by the IP and port number you are wanting on
        self.signalListLock = Lock()
        self.signalList = {}

        # Data Buffer
        # This is different from rx as the RX handler only accepts messages
        # The message thread then handles the messages and adds any sent data to the databuffer
        # for another thread to accept and use.
        self.databuffer = Queue()

    def start(self):
        """ Starts all threads associated with Server Class """
        self.status = ServerStatus.INIT
        self.threadManager.startThreads()
        self.status = ServerStatus.RUNNING

    def stop(self):
        """ Stops all thread associated with Thread Class """
        self.status = ServerStatus.CLOSING
        self.threadManager.stopThreads()

        for sock in self.socketList:
            sock.close()
        self.serverSocket.close()
        self.socketAddressToPeerAddress = {}
        self.peerAddressToSocket = {}
        self.txbuffer = Queue()
        self.rxbuffer = Queue()
        return

    def connect(self, ip, port, block=False):
        """ Connects to a peer.
            This process involves both the peer adding this router to thier peer list,
            and this router adding the peer to the peer list. 
        """
        fromPeer = (self.hostname, self.port)
        toPeer = (ip, port)

        # Check that you aren't already connected to peer
        with self.peerLock:
            if (toPeer not in self.peerAddressToSocket):
                msg = ConnectMessage(toPeer, fromPeer)
                self.txbuffer.put(msg)

        # If blocking, wait for signal
        if block:
            self.addSignal(ip, port)
            with self.signalList[(ip, port)]:
                self.signalList[(ip, port)].wait()
            self.removeSignal(ip, port)

    def getPeers(self, ip, port):
        """
            Connects to a peer and tells that peer to tell all his peers to connect to me.
            This should hopefully solve the issue of two peers trying to connect to eachother at the same time.
            As there is no new, you only even need to connect to one peer. 
        """
        fromPeer = (self.hostname, self.port)
        toPeer = (ip, port)

        # First connect
        self.connect(ip, port)

        # Then send peer request
        requestMsg = PeerRequestMessage(toPeer, fromPeer)
        self.txbuffer.put(requestMsg)

    def getPeerList(self, ip, port):
        """
            Connects to a peer and asks them for their peers.
            This is non blocking, so the thread calling this might need to wait.
            Ie there is no way of knowing if the peer will even reply!
            Easy check to implement would be to add signal for when the msg thread gets
            the reply to this message (SendPeerListMessage), 
            it signals this thread. But thats not important rightnow
        """
        fromPeer = (self.hostname, self.port)
        toPeer = (ip, port)

        # First we will connect with the peer
        with self.peerLock:
            if (toPeer not in self.peerAddressToSocket):
                connectMsg = ConnectMessage(toPeer, fromPeer)
                self.txbuffer.put(connectMsg)

        # Right after, we will send them a message to send us their peer list
        getPeersMsg = GetPeerListMessage(toPeer, fromPeer)
        self.txbuffer.put(getPeersMsg)

    def addSignal(self, ip, port):
        """
            Created a signal for blocking threads to wait on
        """
        with self.signalListLock:
            self.signalList[(ip, port)] = Condition()

    def removeSignal(self, ip, port):
        """
            Removes a signal for blocking threads to wait on
        """
        with self.signalListLock:
            del self.signalList[(ip, port)]

    def send(self, ip, port, data):
        """
            Will send any data to a peer, can be any python object (that does not use file handles)
            If peer not in peerlist it will connect to peer.
        """
        fromPeer = (self.hostname, self.port)
        toPeer = (ip, port)

        # Check if we are connected to peer, if not connect to peer
        with self.peerLock:
            if (toPeer not in self.peerAddressToSocket):
                connectMsg = ConnectMessage(toPeer, fromPeer)
                self.txbuffer.put(connectMsg)

        dataMsg = DataMessage(toPeer, fromPeer, data)
        self.txbuffer.put(dataMsg)

    def broadcast(self, data):
        """
            Broadcasts data to all other peers in network some data
        """
        fromPeer = (self.hostname, self.port)

        for peerAddress in self.peerAddressToSocket.keys():
            toPeer = peerAddress
            dataMsg = DataMessage(toPeer, fromPeer, data)
            self.txbuffer.put(dataMsg)

    def recv(self, peer_socket):
        """ Recieve data from a peer socket """
        try:
            message_header = peer_socket.recv(HEADERSIZE)

            if not len(message_header):
                return False

            message_length = int(message_header.decode("utf-8").strip())
            client_msg = peer_socket.recv(message_length)
            rx_data = pickle.loads(client_msg)
            return rx_data
        except Exception:
            serverLogger.exception("Failed to read from peer socket!")
            return False

    def serializeMessage(self, msg):
        """ serializeMessage: Pickles message for sending. """
        try:
            pickleData = pickle.dumps(msg)
            serializedMsg = bytes(f'{len(pickleData):<{HEADERSIZE}}',
                                  'utf-8') + pickleData

            return serializedMsg
        except Exception:
            serverLogger.exception("Could not serialize message!")
            return None

    def deserializeMessage(self, serializedMsg):
        """ deserializedMessage: Depickles message for receveing. """
        try:
            msg = pickle.dumps(serializedMsg)
            return msg
        except Exception:
            serverLogger.exception("Could not deserialize message!")
            return None

    def txThread(self, _thread):
        """ txThread: Thread that sends data when asked to """
        try:
            # Continue Loop until thread is signaled to stop
            while _thread["status"] != ThreadStatus.STOPPING:
                try:
                    # Wait for buffer to have a message
                    msg = self.txbuffer.get(block=True, timeout=1)
                    # Lock peer & socket list in case another thread is using them
                    with self.peerLock:
                        if isinstance(msg, Message):
                            try:
                                # Serialize message to be sent
                                serializedMsg = self.serializeMessage(msg)

                                # Send message if connected to a peer
                                if msg.toPeer in self.peerAddressToSocket:
                                    self.peerAddressToSocket[msg.toPeer].send(
                                        serializedMsg)
                                else:
                                    # Else create a new socket for peer
                                    sock = socket.socket(
                                        socket.AF_INET, socket.SOCK_STREAM)
                                    sock.setsockopt(
                                        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                    sock.connect(msg.toPeer)

                                    # Socket List [... sock]
                                    self.socketList.append(sock)

                                    # Msg.toPeer -> toPeer
                                    self.socketAddressToPeerAddress[msg.toPeer] = msg.toPeer

                                    # toPeer -> sock
                                    self.peerAddressToSocket[msg.toPeer] = sock
                                    sock.send(serializedMsg)
                            except Exception:
                                serverLogger.exception(
                                    "Could not send message in txBuffer!")
                        else:
                            serverLogger.info(
                                f"Message put in txBuffer was not of type message but of type {type(msg)}")
                except Empty:
                    serverLogger.info("TX Buffer is empty.")
        except Exception:
            serverLogger.exception("Exception raised in TX thread.")
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def rxThread(self, _thread):
        """ rxThread: Thread that listens for connections and data. """
        try:
            self.serverSocket.bind((self.hostname, self.port))
            self.serverSocket.listen()

            while _thread["status"] != ThreadStatus.STOPPING:
                # Wake when something has happened to any of the sockets.
                try:
                    read_sockets, _, exception_sockets = select.select(
                        self.socketList, [], self.socketList, 0.5)

                    for triggered_socket in read_sockets:
                        # if a new peer connects to server's socket, get thier incoming message and push to rx buffer.
                        if triggered_socket == self.serverSocket:
                            peer_socket, peer_address = self.serverSocket.accept()
                            serverLogger.info(
                                f"Connection from {peer_address} has been establised!")
                            msg = self.recv(peer_socket)
                            if msg is False or not isinstance(msg, Message):
                                continue
                            msg.setSourceSocket(peer_socket, peer_address)
                            self.rxbuffer.put(msg)
                        # Else connected peer sent us a new message
                        else:
                            msg = self.recv(triggered_socket)
                            # If connection closed, remove socket
                            if msg is False:
                                try:
                                    serverLogger.info(
                                        f"Closed connection from {triggered_socket.getpeername()}")
                                except Exception:
                                    serverLogger.info(
                                        "A socket closed expectedly!")
                                finally:
                                    self.removeSocket(triggered_socket)
                                    continue

                            # Else check message is type message
                            if isinstance(msg, Message):
                                msg.setSourceSocket(
                                    triggered_socket, triggered_socket.getpeername())
                                self.rxbuffer.put(msg)
                                serverLogger.info(
                                    f"Recevied message from {msg.fromPeer}")
                            else:
                                serverLogger.error(
                                    "Message received was not of type message!")

                    # If any sockets throw an exception, remove them as a peer
                    for bad_socket in exception_sockets:
                        self.removeSocket(bad_socket)
                except Exception:
                    serverLogger.error("Connection stopped suddenly.")
        except Exception:
            serverLogger.exception("Exception raised in RX thread.")
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def msgThread(self, _thread):
        """ msgThread: Opens messages in rx buffer """
        try:
            while _thread["status"] != ThreadStatus.STOPPING:
                try:
                    msg = self.rxbuffer.get(block=True, timeout=1)
                    msg.open(self)
                except Empty:
                    serverLogger.info("No messages to open.")
        except Exception:
            serverLogger.exception("Exception raised in message thread.")
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def removeSocket(self, socket):
        """ Removes a socket from the router """
        try:
            with self.peerLock:
                self.socketList.remove(socket)
                socketAddress = socket.getpeername()
                peerAddress = self.socketAddressToPeerAddress[socketAddress]
                del self.peerAddressToSocket[peerAddress]
                del self.socketAddressToPeerAddress[socketAddress]
        except Exception:
            serverLogger.info(
                "Tried to remove a socket but failed!")
        finally:
            socket.close()
