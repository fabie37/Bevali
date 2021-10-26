from blockchain import Block


class Blockchain:
    """ Class used to contain the blockchain and associtated mining and integrity checks"""

    def __init__(self):
        self.chain = []

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
