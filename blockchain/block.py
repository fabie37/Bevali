import hashlib
import json
import time


class Block:
    """ Class to encapsulate the blocks within the blockchain. """

    def __init__(self, blockNumber=0, previousHash=0, data=[], nonce=0, timestamp=time.time()):
        self.blockNumber = blockNumber
        self.previousHash = previousHash
        self.nonce = nonce
        self.data = data
        self.timestamp = timestamp

    def add_data(self, data):
        """ Adds a data element to the block """
        self.data.append(data)

    def generate_hash(self):
        """ Generates a hash of the block containing: [blockNumber, previousHash, nonce, data, timestampe] """

        blockObject = {
            "blockNumber": self.blockNumber,
            "previousHash": self.previousHash,
            "nonce": self.nonce,
            "data": self.data,
            "timestamp": self.timestamp
        }
        blockJson = json.dumps(blockObject)
        hash = hashlib.sha256()
        hash.update(blockJson.encode('ascii'))
        return hash.hexdigest()

    def __eq__(self, other):
        if (isinstance(other, Block)):
            return self.__dict__ == other.__dict__
        return False
