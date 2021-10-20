import hashlib
import json


class Block:
    def __init__(self):
        self.blockNumber = 0
        self.previousHash = 0
        self.nonce = 0
        self.transactions = []

    def add_transaction(self, transcation):
        self.transactions.append(transcation)

    def generate_hash(self):
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
