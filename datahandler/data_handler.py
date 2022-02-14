from threading import Condition, Lock
from multithreading import ManagedThread, ThreadManager, ThreadStatus


class DataHandler:
    def __init__(self, dataSource):
        # Define the queue to take data from
        self.dataSource = dataSource

        # Thread manager to manage handling of thread
        self.threadManager = ThreadManager()

        # handler thread
        dataThread = ManagedThread(target=self.dataThread, name="Data Thread")
        self.threadManager.addThread(dataThread)

        # A dictionary that specifies (type) -> list or queue to organise data to
        self.dataSink = {}

        # A signal list to notify when a particular resource comes in
        self.signalListLock = Lock()
        self.signalList = {}

    def addDataSink(self, dataSink):
        """ Defines a data sink to send data from source to sink """
        self.dataSink[dataSink.dataType] = dataSink

    def addSignal(self, fromPeer, datatype):
        """ Creates a condition variable to wait for date of a type and from a certain address. """
        key = (fromPeer, datatype)
        with self.signalListLock:
            self.signalList[key] = Condition()

    def removeSignal(self, fromPeer, datatype):
        """ Removes a condition variable that a thread was waiting on """
        key = (fromPeer, datatype)
        with self.signalListLock:
            del self.signalList[key]

    def waitOnData(self, fromPeer, datatype, timeout=None):
        """ Method to wait on a datatype arriving from a specific peer """
        self.addSignal(fromPeer, datatype)
        key = (fromPeer, datatype)
        with self.signalList[key]:
            if timeout:
                self.signalList[key].wait(timeout)
            else:
                self.signalList[key].wait()
        self.removeSignal(fromPeer, datatype)

    def dataThread(self, _thread):
        """ This Thread handles where to send data from source to sink """
        while _thread["status"] != ThreadStatus.STOPPING:
            try:
                letter = self.dataSource.get(block=True, timeout=3)
                fromAddress = letter[0]
                data = letter[1]

                # Check class or parent class
                dataType = type(data)
                if dataType in self.dataSink:
                    self.dataSink[dataType].append(data)
                else:
                    for parent in data.__class__.__bases__:
                        if parent in self.dataSink:
                            self.dataSink[parent].append(data)

                # If we have any threads waiting for this data, alert them
                try:
                    key = (fromAddress, dataType)
                    with self.signalList[key]:
                        self.signalList[key].notify()
                except Exception:
                    # No threads waiting for this data,
                    # print("No such signal exists!")
                    pass
            except Exception as e:
                print(e)

    def start(self):
        self.threadManager.startThreads()

    def stop(self):
        self.threadManager.stopThreads()
