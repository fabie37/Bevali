import hashlib
import json


class Block:
    """ Class to encapsulate the blocks within the blockchain. """

    def __init__(self, blockNumber=0, previousHash=0):
        self.blockNumber = blockNumber
        self.previousHash = previousHash
        self.nonce = 0
        self.transactions = []

    def add_transaction(self, transcation):
        """ Adds a transaction to the block """
        self.transactions.append(transcation)

    def generate_hash(self):
        """ Generates a hash of the block containing: [blockNumber, previousHash, nonce, transactions] """

        blockObject = {
            "blockNumber": self.blockNumber,
            "previousHash": self.previousHash,
            "nonce": self.nonce,
            "transactions": self.transactions
        }
        blockJson = json.dumps(blockObject)
        hash = hashlib.sha256()
        hash.update(blockJson.encode('ascii'))
        return hash.hexdigest()
