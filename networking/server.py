import socket
import select
import pickle
import threading
import logging

from config import HEADERSIZE
from config import ServerStatus
from config import serverLogger


class Server:
    """ Class to encapsulate handling """

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.statusLock = threading.Lock()
        self.status = ServerStatus.INIT
        self.rxLock = threading.Lock()
        self.rxSignal = threading.Condition(self.rxLock)
        self.rxbuffer = []
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rxThread = threading.Thread(
            target=self.run, name=f"RX Thread")
        self.loggerThread = threading.Thread(
            target=self.logger, name=f"Logger Thread")
        self.socketList = [self.serverSocket]
        self.activeThreads = 0
        self.activeThreadsLock = threading.Lock()
        self.closeSignal = threading.Condition(self.activeThreadsLock)

    def start(self):
        """ Starts all threads associated with Server Class """
        self.rxThread.start()
        self.loggerThread.start()

    def stop(self):
        """ Stops all thread associated with Thread Class """
        with self.statusLock:
            self.status = ServerStatus.CLOSING
            with self.rxSignal:
                self.rxSignal.notify_all()

        with self.closeSignal:
            while self.activeThreads != 0:
                self.closeSignal.wait()
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
        except:
            serverLogger.error("Failed to read from peer socket!")
            return False

    def run(self):
        """ Run: Starts the server listening for connections. """
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
                        self.socketList.append(peer_socket)
                        msg["address"] = peer_address
                        self.pushRxBuffer(msg)
                    # Else Already connected peer sent us a new message
                    else:
                        msg = self.recv(triggered_socket)
                        if msg is False:
                            serverLogger.info(
                                f"Closed connection from {triggered_socket.getsockname()}")
                            self.socketList.remove(triggered_socket)
                            continue
                        msg["address"] = triggered_socket.getsocketname()
                        self.pushRxBuffer(msg)
                        serverLogger.info(
                            f"Recevied message from {msg['address']}")

                # If any sockets throw an exception, remove them as a peer
                for bad_socket in exception_sockets:
                    self.socketList.remove(bad_socket)
        except Exception as err:
            serverLogger.exception("Exception raised in RX thread.")
            self.decrementActiveThreads()


server = Server(socket.gethostname(), 1234)
server.start()
some_random_input = input("Press Enter to stop threads")
server.stop()
some_random_input = input("Check threads")
