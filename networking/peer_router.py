import socket
import select
import pickle
from networking import HEADERSIZE
from networking import ServerStatus
from networking import serverLogger
from multithreading import ThreadManager
from multithreading import ManagedThread
from multithreading import ThreadStatus
from threading import Lock
from threading import Condition
from time import sleep


class PeerRouter:
    """ Class to encapsulate handling """

    def __init__(self, hostname, port, id=None):

        # Server Configuration Settings
        self.id = id
        self.hostname = hostname
        self.port = port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Define Peers in sever
        self.peerLock = Lock()
        self.socketList = [self.serverSocket]
        self.peerList = {}

        # Define Thread Manager
        self.threadManager = ThreadManager()

        # Status of server
        self.status = ServerStatus.INIT

        # TX Buffer handler
        self.txbuffer = []
        txThread = ManagedThread(
            target=self.txThread, name=f"TX Thread")
        self.threadManager.addThread(txThread)

        # RX Buffer handler
        self.rxbuffer = []
        rxThread = ManagedThread(
            target=self.rxThread, name=f"RX Thread")
        self.threadManager.addThread(rxThread)

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
        self.peerList = {}
        self.txbuffer = []
        self.rxbuffer = []

        return

    def pushTxBuffer(self, tx_data):
        """ Pushes data into tx buffer """
        try:
            with self.threadManager.getThreadSignal("TX Thread"):
                self.txbuffer.append(tx_data)
                self.threadManager.getThreadSignal("TX Thread").notify()
            return True
        except:
            serverLogger.error("Failed to push to TX Buffer")
            return False

    def clearTxBuffer(self):
        """ Clears data in rxBuffer """
        try:
            with self.threadManager.getThreadLock("TX Thread"):
                self.txbuffer = []
            return True
        except:
            serverLogger.error("Failed to clear TX Buffer")
            return False

    def pushRxBuffer(self, rx_data):
        """ Pushes data into rx buffer """
        try:
            with self.threadManager.getThreadSignal("RX Thread"):
                self.rxbuffer.append(rx_data)
                self.threadManager.getThreadSignal("RX Thread").notify()
            return True
        except:
            serverLogger.error("Failed to push to RX Buffer")
            return False

    def clearRxBuffer(self):
        """ Clears data in rxBuffer """
        try:
            with self.threadManager.getThreadLock("RX Thread"):
                self.rxbuffer = []
            return True
        except:
            serverLogger.error("Failed to clear RX Buffer")
            return False

    @staticmethod
    def recv(peer_socket):
        """ Recieve data from a peer socket """
        try:
            message_header = peer_socket.recv(HEADERSIZE)

            if not len(message_header):
                return False

            message_length = int(message_header.decode("utf-8").strip())
            client_msg = peer_socket.recv(message_length)
            rx_data = pickle.loads(client_msg)
            return {"header": message_header, "data": rx_data}
        except Exception:
            serverLogger.exception("Failed to read from peer socket!")
            return False

    def send(self, data, ip=None, port=None):
        """ send: Sends data to peers. If port and IP are not specified, broadcast to all """
        try:
            pickleData = pickle.dumps(data)
            msg = bytes(f'{len(pickleData):<{HEADERSIZE}}',
                        'utf-8') + pickleData

            # Format msg if wanted to send to specific client
            if (ip is not None and port is not None):
                address = (ip, port)
                msg = {"address": address, "data": msg}

            with self.threadManager.getThreadLock("TX Thread"):
                self.txbuffer.append(msg)
                self.threadManager.getThreadSignal("TX Thread").notify()
            return True
        except Exception:
            serverLogger.exception("Cannot send data!")
            raise False

    def txThread(self, _thread):
        """ txThread: Thread that sends data when asked to """
        try:
            # Continue Loop until thread is signaled to stop
            while _thread["status"] != ThreadStatus.STOPPING:

                # Wait for a signal to transmit data
                msgs = []
                with _thread["signal"]:
                    while len(self.txbuffer) == 0 and _thread["status"] != ThreadStatus.STOPPING:
                        _thread["signal"].wait()
                    msgs = self.txbuffer
                    self.txbuffer = []

                # Iterate through messages in buffer to send
                for msg in msgs:
                    # If msg is for a specific client
                    with self.peerLock:
                        if type(msg) is dict and "address" in msg:
                            try:
                                # If peer is in our list sent them the data
                                if msg['address'] in self.peerList:
                                    self.peerList[msg["address"]].send(
                                        msg["data"])
                                else:
                                    # Else directly send data to peer
                                    sock = socket.socket(
                                        socket.AF_INET, socket.SOCK_STREAM)
                                    sock.setsockopt(
                                        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                    sock.connect(msg["address"])
                                    sock.send(msg["data"])
                                    self.socketList.append(sock)
                                    self.peerList[msg["address"]] = sock
                            except Exception:
                                serverLogger.exception(
                                    "Couldn't send to message to peer!")
                                pass
                        else:
                            # Else, if no peer selected in msg, broadcast to everyone.
                            for peer in self.socketList:
                                try:
                                    if peer != self.serverSocket:
                                        peer.send(msg)
                                except Exception:
                                    serverLogger.exception(
                                        "Couldn't broadcast message to a peer!")
                                    pass
        except Exception:
            serverLogger.exception("Exception raised in TX thread.")
            with self.statusLock:
                self.status = ServerStatus.ERROR

    def rxThread(self, _thread):
        """ rxThread: Thread that listens for connections and data. """
        try:
            self.serverSocket.bind((self.hostname, self.port))
            self.serverSocket.listen()

            while _thread["status"] != ThreadStatus.STOPPING:
                # Wake when something has happened to any of the sockets.
                read_sockets, _, exception_sockets = select.select(
                    self.socketList, [], self.socketList, 0.5)

                for triggered_socket in read_sockets:
                    # if a new peer connects to server's socket, add to list and store the incomming message.
                    if triggered_socket == self.serverSocket:
                        peer_socket, peer_address = self.serverSocket.accept()
                        serverLogger.info(
                            f"Connection from {peer_address} has been establised!")

                        msg = self.recv(peer_socket)
                        if msg == False:
                            continue
                        self.peerLock.acquire()
                        self.socketList.append(peer_socket)
                        self.peerList[peer_address] = peer_socket
                        self.peerLock.release()
                        msg["address"] = peer_address
                        self.pushRxBuffer(msg)
                    # Else Already connected peer sent us a new message
                    else:
                        msg = self.recv(triggered_socket)
                        if msg is False:
                            serverLogger.info(
                                f"Closed connection from {triggered_socket.getpeername()}")
                            with self.peerLock:
                                self.socketList.remove(triggered_socket)
                                del self.peerList[triggered_socket.getpeername()]
                            continue
                        msg["address"] = triggered_socket.getpeername()
                        self.pushRxBuffer(msg)
                        serverLogger.info(
                            f"Recevied message from {msg['address']}")

                # If any sockets throw an exception, remove them as a peer
                for bad_socket in exception_sockets:
                    with self.peerLock:
                        self.socketList.remove(bad_socket)
                        del self.peerList[bad_socket.getpeername()]

        except Exception:
            serverLogger.exception("Exception raised in RX thread.")
            with self.statusLock:
                self.status = ServerStatus.ERROR
