
from blockchain import Blockchain


class DataRequestMessages():
    """
        In the context of networking this falls under
        as a data message.

        This allows peers to request data from other peers
        current context.

        This is useful for getting a peer's current blockchain status
        or other information.
    """

    def __init__(self, fromIp, fromPort):
        self.fromIp = fromIp
        self.fromPort = fromPort

    def open(self, bevali):
        pass


class BlockchainRequestMessage(DataRequestMessages):
    """
        This is a request that gets sent to a peer.

        The person who got sent this request, copies their blockchain and
        sends it to the sender
    """

    def __init__(self, fromIp, fromPort):
        super().__init__(fromIp, fromPort)

    def open(self, bevali):
        # Create an instance of a blockchain without any locks
        sendableBlockChain = Blockchain(
            bevali.blockchain.target, bevali.blockchain.miningWindow)
        sendableBlockChain.chain = []

        # Iterate over our curretly accepted blockchain
        with bevali.blockchain.chain.lock:
            for block in bevali.blockchain.chain:
                sendableBlockChain.add_block(block)

        # Send the blockchain to the person who wanted it.
        bevali.router.send(self.fromIp, self.fromPort, sendableBlockChain)
