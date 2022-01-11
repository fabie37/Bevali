
from queue import Queue
from multithreading.managed_thread import ManagedThread
from networking import PeerRouter
from datahandler import DataHandler
from datahandler import BlockChainSink, BlockSink, PoolSink, RequestsSink
from datahandler import BlockchainRequestMessage
from multithreading import ThreadManager, ProtectedList, ThreadStatus
from threading import Lock
from blockchain import Blockchain, Block


class Bevali():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        # Holds unprocessed transactions
        self.pool = ProtectedList()

        # Holds unprocessed blocks
        self.blocks = Queue()

        # Holds unprocessed blockchains
        self.blockchains = Queue()

        # Hold unprocessed requests from other peers
        self.requests = Queue()

        # Handles all networking
        self.router = PeerRouter(ip, port)

        # Ground Truth blockchain
        self.blockchainLock = Lock()
        self.blockchain = Blockchain()

        # Secondary Chains
        self.secondaryChainsLock = Lock()
        self.secondaryChains = []

        # Orphan Blocks
        self.orphanBlocksLock = Lock()
        self.orphanBlocks = []

        # Handles incoming data send from other peers from the router
        self.handler = DataHandler(self.router.databuffer)

        # Handles all threads concerning this class
        self.threadManager = ThreadManager()

        # Handles Incomming Data Messages
        procThread = ManagedThread(
            target=self.processingThread, name="Processing Thread")
        self.threadManager.addThread(procThread)

        # Handles When new peers connect
        peerWatcherThread = ManagedThread(
            target=self.peerWatcherThread, name="Peer Watcher"
        )
        self.threadManager.addThread(peerWatcherThread)

        # Defines where to tell the data handler to send incoming data to
        poolSink = PoolSink(self.pool)
        blockSink = BlockSink(self.blocks)
        blockchainSink = BlockChainSink(self.blockchains)
        requestSink = RequestsSink(self.requests)
        self.handler.addDataSink(poolSink)
        self.handler.addDataSink(blockSink)
        self.handler.addDataSink(blockchainSink)
        self.handler.addDataSink(requestSink)

    def start(self):
        """
        Starts all related threads:
            Networking,
            Data handling,
            Blockchain updates,
            New Blocks,
            Incoming transactions
        """
        self.router.start()
        self.handler.start()
        self.threadManager.startThreads()

    def stop(self):
        """
        Stops all related threads
        """
        self.router.stop()
        self.handler.stop()
        self.threadManager.stopThreads()

    def createNewChain(self):
        """ Method to created a new chain """
        firstBlock = Block()
        self.blockchain = Blockchain()
        self.blockchain.add_block(firstBlock)

    def _mine(self, data):
        """ Method to mine a block """

        # Record Current length of chain
        currentLength = 0
        with self.blockchainLock:
            currentLength = len(self.blockchain.chain)

        # Mine a new block
        block = self.blockchain.mine_block(data)

        # If minning successful, broadcast to peers new block
        with self.blockchainLock:
            if currentLength == len(self.blockchain.chain):
                self.blockchain.add_block(block)
                self.router.broadcast(block)
                return True

        return False

    def connectToNode(self, ip, port):
        """ Connects to an existing node in blockchain """
        # 1. Connect to node in peer
        self.router.getPeers(ip, port)

        # 2. Get blockchain from peer
        blockchainReq = BlockchainRequestMessage(self.ip, self.port)
        self.router.send(ip, port, blockchainReq)

        # 3. Wait for a blockchain object to come from our peer
        self.handler.waitOnData((ip, port), Blockchain, 60)

    def processBlock(self, block):
        """ Processes a new block incomming """
        # 1) Check hash is valid
        with self.blockchainLock:
            if not self.blockchain.block_valid(block):
                return False

        # 2) See if block belongs on main chain
        with self.blockchainLock:
            if self.blockchain.block_belongs(block):
                self.blockchain.add_block(block)
                return False

        # 3) If not here then it might be in a secondary chain
        checkReplacement = False
        blockchainContender = None
        with self.secondaryChainsLock:
            for blockchain in self.secondaryChains:
                if blockchain.block_belongs(block):
                    blockchain.add_block(block)
                    checkReplacement = True
                    blockchainContender = blockchain

        # 4) Check if main chain needs replaced
        # It shouldn't matter that it's not protected here,
        # This is the only time we ever edit a secondary chain directly
        if checkReplacement:
            with self.blockchainLock:
                if len(blockchainContender) > len(self.blockchain):
                    self.blockchain = blockchainContender

            with self.secondaryChainsLock:
                self.secondaryChains.remove(blockchainContender)

        # 5) Since there is not place for block to go, call it an orphan.
        with self.orphanBlocksLock:
            self.orphanBlocks.append(block)

    def processBlockchain(self, blockchain):
        """ Processes a new blockchain incomming """
        # if blockchain is empty, reject it
        if len(blockchain.chain) == 0:
            return

        # Create a copy
        newChain = Blockchain(blockchain.target, blockchain.miningWindow)
        for block in blockchain.chain:
            newChain.add_block(block)

        # Check incoming chain is valid
        if newChain.check_integrity():
            # Check if any orphan blocks belong to the chain
            with self.orphanBlocksLock:
                removalList = []
                for orphanBlock in self.orphanBlocks:
                    if newChain.is_block_in_chain(orphanBlock):
                        removalList.append(orphanBlock)
                    elif newChain.block_belongs(orphanBlock):
                        newChain.add_block(orphanBlock)

                for oldOrphan in removalList:
                    self.orphanBlocks.remove(oldOrphan)

            with self.blockchainLock:
                # if new chain is longer than old chain, make it the new chain
                if len(self.blockchain.chain) < len(newChain.chain):
                    oldChain = self.blockchain
                    self.blockchain = newChain
                    # Make sure our old chain isn't empty
                    if len(oldChain.chain) != 0:
                        with self.secondaryChainsLock:              # Potential For dead lock - watch out
                            self.secondaryChains.append(oldChain)
                # Make sure new chain isn't already here
                elif self.blockchain.is_equal(newChain):
                    pass
                else:
                    with self.secondaryChainsLock:
                        self.secondaryChains.append(newChain)

    def processingThread(self, _thread):
        try:
            while _thread["status"] != ThreadStatus.STOPPING:

                # 1. Process a requests
                try:
                    request = self.requests.get(block=True, timeout=1)
                    request.open(self)
                except Exception:
                    # No requests available
                    pass

                # 2. Process a incoming blocks
                try:
                    block = self.blocks.get(block=True, timeout=1)
                    self.processBlock(block)
                except Exception:
                    # No blocks available
                    pass

                # 3. Process a blockchain
                try:
                    # Get blockchain
                    blockchain = self.blockchains.get(block=True, timeout=1)
                    self.processBlockchain(blockchain)

                except Exception:
                    # No blockchain available
                    pass

        except Exception:
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def peerWatcherThread(self, _thread):
        try:
            while _thread["status"] != ThreadStatus.STOPPING:
                try:
                    newPeer = self.router.newPeerQueue.get(
                        block=True, timeout=5)
                    blockchainReq = BlockchainRequestMessage(
                        self.ip, self.port)
                    self.router.send(newPeer[0], newPeer[1], blockchainReq)

                except Exception:
                    # No new peers
                    pass

        except Exception:
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR
