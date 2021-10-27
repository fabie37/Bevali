from blockchain import Block
from time import time


class Blockchain:
    """ Class used to contain the blockchain and associtated mining and integrity checks"""

    def __init__(self, target='0', miningWindow=60):
        self.chain = []
        self.target = target
        self.miningWindow = 60  # In seconds

    def add_block(self, block):
        """ Adds a new block to the chain """

        if isinstance(block, Block):
            self.chain.append(block)
            return True
        else:
            return False

    def check_integrity(self):
        """ Checks the integrity of the blockchain. In other words, that the blocks have not been modified."""

        # 1) Empty Block Chain is valid
        if len(self.chain) == 0:
            return True

        # 2) Check type of first block is valid
        if not isinstance(self.chain[0], Block):
            return False

        # 3) Check chain integrity of full chain
        previousBlock = self.chain[0]
        for block in self.chain[1:]:
            if not isinstance(block, Block):
                return False
            previousHash = previousBlock.generate_hash()
            if previousHash != block.previousHash:
                return False
            previousBlock = block

        return True

    def mine_block(self, data):
        """ Method to do PoW algorithm and return a valid block """

        target = self.target
        lastBlock = self.chain[-1]
        lastBlockHash = lastBlock.generate_hash()

        newBlock = Block(blockNumber=lastBlock.blockNumber+1,
                         previousHash=lastBlockHash, data=data)
        timeInterval = time()

        while not newBlock.generate_hash().startswith(target):
            newBlock.nonce += 1
            if (time() - timeInterval) > self.miningWindow:
                timeInterval = time()
                newBlock.timestamp = timeInterval

        return newBlock
