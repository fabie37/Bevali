from blockchain.blockchain import Blockchain
from multithreading.managed_thread import ManagedThread
from networking import PeerRouter
from multithreading import ThreadManager, ThreadStatus
from blockchain import Block
from queue import Queue


class DataHandler:

    def __init__(self, dataSource):
        # Define the queue to take data from
        self.dataSource = dataSource

        # Thread manager to manage handling of thread
        self.threadManager = ThreadManager()

        # handler thread
        dataThread = ManagedThread(target=self.dataThread, name=f"Data Thread")
        self.threadManager.addThread(dataThread)

        self.dataSink = {}

    def addDataSink(self, dataSink):
        """ Defines a data sink to send data from source to sink """
        self.dataSink[dataSink.dataType] = dataSink

    def dataThread(self, _thread):
        """ This Thread handles where to send data from source to sink """
        while _thread["status"] != ThreadStatus.STOPPING:
            try:
                data = self.dataSource.get(block=True, timeout=3)
                dataType = type(data)
                self.dataSink[dataType].append(data)
            except Exception as e:
                print(e)

    def start(self):
        self.threadManager.startThreads()

    def stop(self):
        self.threadManager.stopThreads()
