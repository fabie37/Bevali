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

    def dataThread(self, _thread):
        while _thread["status"] != ThreadStatus.STOPPING:
            try:
                data = self.dataSource.get(block=True, timeout=3)
                if isinstance(data, Block):
                    print("Got block")

                if isinstance(data, Blockchain):
                    print("Got blockchain")
            except:
                pass
