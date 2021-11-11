import socket
import pickle
import threading

from constants import HEADERSIZE
from constants import ServerStatus


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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.thread = threading.Thread(
            target=self.run, name=f"Thread-{hostname}")
        self.loggerThread = threading.Thread(target=self.logger)

    def start(self):
        """ Starts all threads associated with Server Class """
        self.thread.start()
        self.loggerThread.start()

    def stop(self):
        """ Stops all thread associated with Thread Class """
        self.statusLock.acquire()
        self.status = ServerStatus.STOPPED
        self.statusLock.release()

    def logger(self):
        while True:
            if self.status == ServerStatus.STOPPED:
                print("Logger Thread Closing")
                return

            while len(self.rxbuffer) == 0:
                self.rxSignal.acquire()
                self.rxSignal.wait()

            for item in self.rxbuffer:
                print(item)
            self.rxbuffer = []
            self.rxSignal.release()

    def run(self):
        """ Run: Starts the server listening for connections. """
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(5)

        while True:
            # If asked to stop, stop thread
            if self.status == ServerStatus.STOPPED:
                print("Run Thread Closing")
                return

            # Create a new client socket
            clientsocket, address = self.socket.accept()
            print(f"Connection from {address} has been establised!")

            full_msg = b''
            new_msg = True

            while True:
                msg = clientsocket.recv(2*HEADERSIZE)
                if new_msg:
                    print(f"new message length: {msg[:HEADERSIZE]}")
                    msglen = int(msg[:HEADERSIZE])
                    new_msg = False

                full_msg += msg

                if len(full_msg) - HEADERSIZE == msglen:
                    print("Full Message Recieved")
                    rx_data = pickle.loads(full_msg[HEADERSIZE:])
                    self.rxLock.acquire()
                    self.rxbuffer.append(rx_data)
                    self.rxSignal.notify()
                    self.rxLock.release()

                    break


server = Server(socket.gethostname(), 1234)
server.start()
some_random_input = input("Press Enter to stop threads")
server.stop()
some_random_input = input("Check threads")
