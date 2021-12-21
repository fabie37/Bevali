
from threading import Lock, Condition


class ProtectedList(list):
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
