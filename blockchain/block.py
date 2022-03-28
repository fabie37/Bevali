import hashlib
import json
import time

from transactions.transaction import Transaction


class Block:
    """ Class to encapsulate the blocks within the blockchain. """

    def __init__(self, blockNumber=0, previousHash=0, data=[],
                 nonce=0, timestamp=time.time(), miner=""):
        self.blockNumber = blockNumber
        self.previousHash = previousHash
        self.nonce = nonce
        self.data = data
        self.timestamp = timestamp
        self.miner = miner

    def add_data(self, data):
        """ Adds a data element to the block """
        self.data.append(data)

    def generate_hash(self):
        """ Generates a hash of the block containing:
            [blockNumber, previousHash, nonce, data, timestamp]
        """
        datajson = []
        if isinstance(self.data, list):
            for elem in self.data:
                if isinstance(elem, Transaction) or issubclass(type(elem), Transaction):
                    datajson.append(elem.jsonize())
                else:
                    datajson.append(elem)
        elif isinstance(self.data, Transaction) or issubclass(type(self.data), Transaction):
            datajson.append(self.data.jsonize())
        else:
            datajson.append(self.data)

        blockObject = {
            "blockNumber": self.blockNumber,
            "previousHash": self.previousHash,
            "nonce": self.nonce,
            "data": datajson,
            "timestamp": self.timestamp,
            "miner": self.miner
        }
        blockJson = json.dumps(blockObject)
        hash = hashlib.sha256()
        hash.update(blockJson.encode('UTF-8'))
        return hash.hexdigest()

    def __eq__(self, other):
        if (isinstance(other, Block)):
            return self.generate_hash() == other.generate_hash()
        return False
