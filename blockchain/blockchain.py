from blockchain import Block
from time import time
from multithreading import ProtectedList


class Blockchain:
    """ Class used to contain the blockchain and associtated mining and integrity checks"""

    def __init__(self, target='0', miningWindow=60):
        self.chain = ProtectedList()
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
        with self.chain.lock:
            for block in self.chain[1:]:
                if not isinstance(block, Block):
                    return False
                previousHash = previousBlock.generate_hash()
                if previousHash != block.previousHash:
                    return False
                previousBlock = block
        return True

    def is_equal(self, bc):
        """ Checks if this blockchain is the same as another """
        if len(bc.chain) != len(self.chain):
            return False

        for index, block in enumerate(self.chain):
            thisHash = block.generate_hash()
            blockHash = bc.chain[index].generate_hash()
            if not thisHash == blockHash:
                return False

        return True

    def block_valid(self, block):
        """ Check if blocks hash is valid """
        # Check block is valid
        if not block.generate_hash().startswith(self.target):
            return False

        return True

    def is_block_in_chain(self, block):
        """ Checks if a block is in chain """
        for b in self.chain:
            if b.generate_hash() == block.generate_hash():
                return True
        return False

    def block_belongs(self, block):
        """ Checks if block belongs in blockchain"""
        # Check block is valid
        if not self.block_valid(block):
            return False

        # Check if previous hash matches last block's hash
        if self.chain[-1].generate_hash() != block.previousHash:
            return False

        return True

    def mine_block(self, data):
        """ Method to do PoW algorithm and return a valid block """

        target = self.target
        lastBlock = self.chain[-1]
        lastBlockHash = lastBlock.generate_hash()

        newBlock = Block(blockNumber=lastBlock.blockNumber + 1,
                         previousHash=lastBlockHash, data=data)
        timeInterval = time()

        while not newBlock.generate_hash().startswith(target):
            newBlock.nonce += 1
            if (time() - timeInterval) > self.miningWindow:
                timeInterval = time()
                newBlock.timestamp = timeInterval

        return newBlock
