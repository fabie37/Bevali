from blockchain import Block
from time import time
from multithreading import ProtectedList
import random
from random import randint
from sys import maxsize


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
            thisBlock = block
            otherBlock = bc.chain[index]
            if thisBlock != otherBlock:
                return False

        return True

    def block_valid(self, block):
        """ Check if blocks hash is valid """
        # Check block is valid
        if not block.generate_hash().startswith(self.target):
            return False

        return True

    def is_prev_hash_in_chain(self, block):
        """ Checks is block's prev hash is in chain """
        for b in reversed(self.chain):
            if b.generate_hash() == block.previousHash:
                return b.blockNumber
        return False

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

    def copy(self, blockNumber=None):
        """ 
            Creates a copy of the blockchain object
            If blockNumber supplied, copy chain up to a point
        """

        newChain = Blockchain(target=self.target,
                              miningWindow=self.miningWindow)
        chain = self.chain.__deepcopy__()
        if blockNumber:
            newChain.chain.extend(chain[:blockNumber + 1])
        else:
            newChain.chain = chain
        return newChain

    def mine_block(self, data, miner=""):
        """ Method to do PoW algorithm and return a valid block """
        # random.seed()
        target = self.target
        lastBlock = self.chain[-1]
        lastBlockHash = lastBlock.generate_hash()

        newBlock = Block(blockNumber=lastBlock.blockNumber + 1,
                         previousHash=lastBlockHash, data=data, miner=miner)
        timeInterval = time()

        while not newBlock.generate_hash().startswith(target):
            # newBlock.nonce += 1
            # newBlock.nonce = random.randint(0, maxsize - 1)
            newBlock.nonce = randint(0, maxsize - 1)
            if (time() - timeInterval) > self.miningWindow:
                timeInterval = time()
                newBlock.timestamp = timeInterval

        return newBlock
