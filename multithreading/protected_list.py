
from threading import RLock
from collections import UserList


class ProtectedList(UserList):
    def __init__(self, initlist=None):
        super().__init__(initlist=initlist)
        self.lock = RLock()

    def append(self, item):
        with self.lock:
            item = super().append(item)
        return item

    def remove(self, item):
        with self.lock:
            if super().__contains__(item):
                item = super().remove(item)
        return item

    def set_removal(self, lst):
        """
            Removes all elements in lst from this protected list
        """
        with self.lock:
            for item in lst:
                if super().__contains__(item):
                    super().remove(item)
        return

    def take(self, num=1):
        items = []
        with self.lock:
            for _ in range(num):
                if len(self) > 0:
                    items.append(super().pop(0))
                else:
                    break
        return items

    def __len__(self):
        length = 0
        with self.lock:
            length = super().__len__()
        return length
