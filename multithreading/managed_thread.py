"""
This class extends the python thread class.
It enables a signaling system for the thread manager class
so that it is able to detect if a thread has successful returned.
"""


import threading
from enum import Enum
from time import sleep


class ThreadStatus(Enum):
    INIT = 0
    RUNNING = 1
    STOPPING = 2
    STOPPED = 3
    ERROR = 4


class ManagedThread(threading.Thread):
    def __init__(self, closeSignal=None, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name, args=args,
                         kwargs=kwargs, daemon=daemon)

        lock = threading.Lock()
        signal = threading.Condition(lock)
        self._management = {
            "status": ThreadStatus.INIT,
            "lock": lock,
            "signal": signal,
        }
        self._args += (self._management,)
        self.closeSignal = closeSignal

    def stop(self):
        with self._management["lock"]:
            self._management["status"] = ThreadStatus.STOPPING
        with self._management["signal"]:
            self._management["signal"].notify_all()

    def run(self):
        try:
            with self._management["lock"]:
                self._management["status"] = ThreadStatus.RUNNING
            if self._target is not None:
                self._target(*self._args, **self._kwargs)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs
            self._thread = ThreadStatus.STOPPED
            with self.closeSignal:
                self.closeSignal.notify()
