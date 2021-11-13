import socket
import select
import pickle
import threading
from config import HEADERSIZE
from config import ServerStatus
from config import serverLogger
from time import sleep


class Server:
    """ Class to encapsulate handling """

    def __init__(self, hostname, port):

        # Server Configuration Settings
        self.hostname = hostname
        self.port = port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Define Peers in sever
        self.peerLock = threading.Lock()
        self.socketList = [self.serverSocket]
        self.peerList = {}

        # Status of server
        self.statusLock = threading.Lock()
        self.status = ServerStatus.INIT

        # TX Buffer handler
        self.txLock = threading.Lock()
        self.txSignal = threading.Condition(self.txLock)
        self.txbuffer = []
        self.txThread = threading.Thread(
            target=self.txThread, name=f"TX Thread")

        # RX Buffer handler
        self.rxLock = threading.Lock()
        self.rxSignal = threading.Condition(self.rxLock)
        self.rxbuffer = []
        self.rxThread = threading.Thread(
            target=self.rxThread, name=f"RX Thread")

        # Thread Management
        self.activeThreads = 0
        self.activeThreadsLock = threading.Lock()
        self.closeSignal = threading.Condition(self.activeThreadsLock)

        # Buffer Logger
        self.loggerThread = threading.Thread(
            target=self.logger, name=f"Logger Thread")

    def start(self):
        """ Starts all threads associated with Server Class """
        with self.statusLock:
            self.status = ServerStatus.INIT
        self.rxThread.start()
        self.txThread.start()
        self.loggerThread.start()
        with self.statusLock:
            self.status = ServerStatus.RUNNING

    def stop(self):
        """ Stops all thread associated with Thread Class """
        with self.statusLock:
            self.status = ServerStatus.CLOSING
            with self.rxSignal:
                self.rxSignal.notify_all()
            with self.txSignal:
                self.txSignal.notify_all()

        with self.closeSignal:
            while self.activeThreads != 0:
                self.closeSignal.wait()

        for sock in self.socketList:
            sock.close()
        self.serverSocket.close()
        self.peerList = {}
        self.txbuffer = []
        self.rxbuffer = []
        self.activeThreads = 0
        return

    def incrementActiveThreads(self):
        """ Increments number of active threads """
        with self.activeThreadsLock:
            self.activeThreads += 1

    def decrementActiveThreads(self):
        """ Decrements number of active threads and notifies any thread waiting on closeSignal """
        with self.closeSignal:
            self.activeThreads -= 1
            self.closeSignal.notify()

    def shouldThreadClose(self, threadname):
        """ Method to check if thread should close. """
        if self.status == ServerStatus.CLOSING:
            serverLogger.info(f"{threadname} is closing...")
            self.decrementActiveThreads()
            return True
        else:
            return False

    def logger(self):
        """ Logs data in RX Buffer """
        try:
            self.incrementActiveThreads()
            while True:
                if (self.shouldThreadClose("Logger Thread")):
                    return

                with self.rxSignal:
                    self.rxSignal.wait()
                    for item in self.rxbuffer:
                        print(f"{item}\n")
                    self.rxbuffer = []
        except:
            serverLogger.error("Logger thread closed unexpectedly!")
            self.decrementActiveThreads()

    def pushRxBuffer(self, rx_data):
        """ Pushes data into rx buffer """
        with self.rxSignal:
            self.rxbuffer.append(rx_data)
            self.rxSignal.notify()

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

            with self.txSignal:
                self.txbuffer.append(msg)
                self.txSignal.notify()
            return True
        except Exception:
            serverLogger.exception("Cannot send data!")
            raise False

    def txThread(self):
        """ txThread: Thread that sends data when asked to """
        try:
            self.incrementActiveThreads()

            while True:

                # If asked to close server, close this thread
                if (self.shouldThreadClose("TX Thread")):
                    return

                # Wait for a signal to transmit data
                msgs = []
                with self.txSignal:
                    while len(self.txbuffer) == 0 and self.status != ServerStatus.CLOSING:
                        self.txSignal.wait()
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
                                    self.clientSocket = socket.socket(
                                        socket.AF_INET, socket.SOCK_STREAM)
                                    self.clientSocket.connect(msg["address"])
                                    self.clientSocket.send(msg["data"])
                                    self.clientSocket.close()
                            except Exception:
                                serverLogger.exception(
                                    "Couldn't send to message to peer!")
                                pass
                        else:
                            # Else, if no peer selected in msg, broadcast to everyone.
                            for peer in self.socketList:
                                try:
                                    peer.send(msg)
                                except Exception:
                                    serverLogger.exception(
                                        "Couldn't broadcast message to a peer!")
                                    pass
        except Exception:
            serverLogger.exception("Exception raised in TX thread.")
            self.decrementActiveThreads()
            self.stop()
            with self.statusLock:
                self.status = ServerStatus.ERROR

    def rxThread(self):
        """ rxThread: Thread that listens for connections and data. """
        try:
            self.incrementActiveThreads()
            self.serverSocket.bind((self.hostname, self.port))
            self.serverSocket.listen()

            while True:
                # If asked to stop, stop thread
                if (self.shouldThreadClose("RX Thread")):
                    return

                # Wake when something has happened to any of the sockets.
                read_sockets, _, exception_sockets = select.select(
                    self.socketList, [], self.socketList, 10)

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
                            self.peerLock.acquire()
                            self.socketList.remove(triggered_socket)
                            del self.peerList[triggered_socket.getpeername()]
                            self.peerLock.release()
                            continue
                        msg["address"] = triggered_socket.getpeername()
                        self.pushRxBuffer(msg)
                        serverLogger.info(
                            f"Recevied message from {msg['address']}")

                # If any sockets throw an exception, remove them as a peer
                for bad_socket in exception_sockets:
                    self.peerLock.acquire()
                    self.socketList.remove(bad_socket)
                    del self.peerList[bad_socket.getpeername()]
                    self.peerLock.release()
        except Exception:
            serverLogger.exception("Exception raised in RX thread.")
            self.decrementActiveThreads()
            self.stop()
            with self.statusLock:
                self.status = ServerStatus.ERROR


server = Server("127.0.0.1", 1234)
server.start()

p2p = Server("127.0.0.1", 1235)
p2p.start()

for i in range(0, 100):
    p2p.send("hello world!", "127.0.0.1", 1234)
    sleep(0.1)
    server.send("how you been?", "127.0.0.1", 1235)

some_random_input = input("Press Enter to stop threads")
server.stop()
p2p.stop()
some_random_input = input("Check threads")
