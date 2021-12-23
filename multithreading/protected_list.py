
from threading import Lock
from collections import UserList


class ProtectedList(UserList):
    def __init__(self, initlist=None):
        super().__init__(initlist=initlist)
        self.lock = Lock()

    def append(self, item):
        with self.lock:
            item = super().append(item)
        return item

    def remove(self, item):
        with self.lock:
            item = super().remove(item)
        return item

    def __len__(self):
        length = 0
        with self.lock:
            length = super().__len__()
        return length
