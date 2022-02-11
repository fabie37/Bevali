"""
    This class will encapulate users.
    They will contain simply a private and public key.
"""
from random import randint


class User():
    def __init__(self):
        self.id = randint(1, 2**256)

    def getId(self):
        return self.id
