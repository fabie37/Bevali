from threading import Lock
from threading import Condition


class ThreadManager:
    """ Class to encapsulate handling threads """

    def __init__(self):
        self.threads = []
        self.activeThreads = 0
        self.lock = Lock()
        self.closeSignal = Condition(self.lock)

    def incrementActiveThreads(self):
        """ Increments number of active threads """
        self.activeThreads += 1

    def decrementActiveThreads(self):
        """ Decrements number of active threads and notifies any thread waiting on closeSignal """
        if self.activeThreads > 0:
            self.activeThreads -= 1

    def addThread(self, thread):
        """ Adds a thread to be managed by the manager """
        with self.lock:
            thread.closeSignal = self.closeSignal
            self.threads.append(thread)

    def getThreadByName(self, name):
        """ Returns thread based on thread name """
        for thread in self.threads:
            if thread._name == name:
                return thread
        return None

    def getThreadLock(self, name):
        """ Returns thread lock based on thread name """
        for thread in self.threads:
            if thread._name == name:
                return thread._management["lock"]

    def getThreadSignal(self, name):
        """ Returns thread signal based on thread name """
        for thread in self.threads:
            if thread._name == name:
                return thread._management["signal"]

    def startThreads(self):
        """ Starts all threads in manager """
        with self.lock:
            for thread in self.threads:
                thread.start()
                self.incrementActiveThreads()

    def stopThreads(self):
        """ Attempts to kill threads in manager """
        with self.closeSignal:
            for thread in self.threads:
                thread.stop()
                self.closeSignal.wait()
                self.decrementActiveThreads()

        self.threads = []

        if (self.activeThreads == 0):
            return True
        else:
            return False
