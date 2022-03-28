from queue import Empty, Queue
from multithreading.managed_thread import ManagedThread
from networking import PeerRouter
from datahandler import DataHandler
from datahandler import BlockChainSink, BlockSink, PoolSink, RequestsSink
from datahandler import BlockchainRequestMessage
from multithreading import ThreadManager, ProtectedList, ThreadStatus
from threading import Lock, RLock
from blockchain import Blockchain, Block
from transactions import Transaction, signHash
from encryption import get_public_key, generate_private_key, serialize_public_key
from time import sleep

TRANSACTIONS_TO_MINE = 10
RELEASE_TRANSACTIONS_AFTER = 2


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
        self.router = PeerRouter(ip, port, mesh=False)

        # Ground Truth blockchain
        self.blockchainLock = RLock()
        self.blockchain = Blockchain()

        # Secondary Chains
        self.secondaryChainsLock = Lock()
        self.secondaryChains = []

        # Orphan Blocks
        self.orphanBlocksLock = Lock()
        self.orphanBlocks = []

        # Public/Private Key Crypto
        self.privateKey = generate_private_key()
        self.publicKey = get_public_key(self.privateKey)

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

        # Handles If this client wishes to mine blocks
        minningThread = ManagedThread(
            target=self.minningThread, name="Minning Thread"
        )
        self.minningManager = ThreadManager()
        self.minningManager.addThread(minningThread)
        self.isMinning = False

        # Defines where to tell the data handler to send incoming data to
        poolSink = PoolSink(self.pool)
        blockSink = BlockSink(self.blocks)
        blockchainSink = BlockChainSink(self.blockchains)
        requestSink = RequestsSink(self.requests)
        self.handler.addDataSink(poolSink)
        self.handler.addDataSink(blockSink)
        self.handler.addDataSink(blockchainSink)
        self.handler.addDataSink(requestSink)

        # Thread Queue to signal custom actions
        self.signal = Queue()

        # Disable checks, for testing purposes
        self.disableChecks = False

        # Throttles minning for testing
        self.throttle_minning = False

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
        self.stop_minning()
        self.router.stop()
        self.handler.stop()
        self.threadManager.stopThreads()

    def start_minning(self):
        """
        Start this client minning
        """
        self.isMinning = True
        self.minningManager.startThreads()

    def stop_minning(self):
        """
            Stops all threads associated with minning
        """
        if self.isMinning:
            self.minningManager.stopThreads()
            self.isMinning = False
            self.minningManager.addThread(ManagedThread(
                target=self.minningThread, name="Minning Thread"
            ))

    def getSerialPublicKey(self):
        """
            Returns a string format of public key
        """
        return serialize_public_key(self.publicKey).decode("utf-8")

    def createNewChain(self, target='0'):
        """ Method to created a new chain """
        firstBlock = Block()
        self.blockchain = Blockchain(target=target)
        self.blockchain.add_block(firstBlock)

    def sendTransaction(self, transaction):
        # First sign transactions hash
        signHash(transaction, self.privateKey)
        self.pool.append(transaction)
        self.router.broadcast(transaction)

    def _mine(self, data):
        """ Method to mine a block """

        # Record Current length of chain
        mainCopy = None
        with self.blockchainLock:
            mainCopy = self.blockchain.copy()

        # Mine a new block
        block = mainCopy.mine_block(data, self.port)

        # If minning successful, broadcast to peers new block
        with self.blockchainLock:
            if len(mainCopy.chain) == len(self.blockchain.chain):
                if not self.disableChecks:
                    self.processBlock(block)
                else:
                    self.blockchain.chain.append(block)
                self.router.broadcast(block)
                return True

        return False

    def connectToNode(self, ip, port, blocking=True):
        """ Connects to an existing node in blockchain """
        # 1. Connect to node in peer
        self.router.connect(ip, port, block=blocking, duration=60)

        # 2. Get blockchain from peer
        blockchainReq = BlockchainRequestMessage(self.ip, self.port)
        self.router.send(ip, port, blockchainReq)

        # 3. Wait for a blockchain object to come from our peer
        self.handler.waitOnData((ip, port), Blockchain, 60)

    def findCommonBlock(self, mainChain, sndChain):
        """
            Returns a common block between two chains
        """
        common_head = len(mainChain) - len(sndChain)
        mainPointer = len(mainChain) - common_head - 1
        sndChainPointer = len(sndChain) - 1
        while mainChain[mainPointer].generate_hash() != sndChain[sndChainPointer].generate_hash():
            mainPointer -= 1
            sndChainPointer -= 1
        if mainChain[mainPointer].generate_hash() == sndChain[sndChainPointer].generate_hash():
            return (mainPointer, sndChainPointer)
        else:
            return None

    def getListOfTransactionsInChain(self, chain, fromIndex=None):
        """
            Returns a list which contains the transactions in a blockchain list
        """
        transactions = []
        if fromIndex:
            for block in chain.chain[fromIndex:]:
                if isinstance(block.data, list):
                    for tx in block.data:
                        if isinstance(tx, Transaction):
                            transactions.append(tx)
                else:
                    break
        return transactions

    def releaseTransactions(self):
        """
            If main chain is beating secondary chains,
            release old transactions back to network
        """
        lengths = []
        with self.blockchainLock:
            with self.secondaryChainsLock:
                # Get the length of all secondary chains
                for sndChain in self.secondaryChains:
                    lengths.append(len(sndChain.chain))

                # If no secondary chains, return
                if not lengths:
                    return

                # if the main chain is definitely ahead, release mined transactioned
                if len(self.blockchain.chain) >= max(lengths) + RELEASE_TRANSACTIONS_AFTER:
                    for sndChain in self.secondaryChains:
                        commonBlocks = self.findCommonBlock(
                            self.blockchain.chain, sndChain.chain)
                        if commonBlocks:
                            # add all transactions in old chain back into tx pool
                            sndChainPointer = commonBlocks[1]
                            sndChainTxs = self.getListOfTransactionsInChain(
                                sndChain, sndChainPointer)
                            mainChainPointer = commonBlocks[0]
                            mainChainTxs = self.getListOfTransactionsInChain(
                                self.blockchain, mainChainPointer)
                            # Take away the transactions that already exist in main chain
                            toRelease = list(
                                set(sndChainTxs) - set(mainChainTxs))
                            # Add lost transactions back in pool
                            for tx in toRelease:
                                self.pool.append(tx)

                    # Clear secondary chains
                    self.secondaryChains = []

    def releaseTransactionsFromNewBlock(self, block):
        """
            When a new block comes to the blockchain,
            remove any transactions that are in the pool
        """
        if isinstance(block.data, list):
            for tx in block.data:
                if isinstance(tx, Transaction):
                    self.pool.remove(tx)

    def newBlockHashValid(self, block):
        """
            Checks if a new block's hash is valid
        """
        with self.blockchainLock:
            if not self.blockchain.block_valid(block):
                return False
        return True

    def newBlockTransactionsValid(self, block):
        """
            Checks if the transactions in a block are valid
        """
        with self.blockchainLock:
            for tx in block.data:
                if isinstance(tx, Transaction) or issubclass(type(tx), Transaction):
                    if not tx.validate(self.blockchain, block):
                        return False
        return True

    def newBlockBelongsOnMainChain(self, block):
        """
            Checks if new block should be on main chain.
        """
        with self.blockchainLock:
            if self.blockchain.block_belongs(block):
                self.releaseTransactionsFromNewBlock(block)
                self.blockchain.add_block(block)

                # For evaluation purposes
                self.signal.put("New Block")
                return True
        return False

    def newBlockBelongsOnSecondaryChains(self, block):
        """
            Checks if new block should be added to a
            secondary chain.
        """
        blockchainContender = False
        with self.secondaryChainsLock:
            for blockchain in self.secondaryChains:
                if blockchain.block_belongs(block):
                    blockchain.add_block(block)
                    blockchainContender = blockchain
        return blockchainContender

    def challengeMainChain(self, contenderChain, block):
        """
            Checks if a contending chain is longer 
            than the main chain.
            If so, swap and release added block's
            transactions.
        """
        with self.blockchainLock:
            mainChain = None
            if len(contenderChain.chain) > len(self.blockchain.chain):
                self.releaseTransactionsFromNewBlock(block)
                mainChain = self.blockchain
                self.blockchain = contenderChain
                with self.secondaryChainsLock:
                    self.secondaryChains.remove(contenderChain)
                    self.secondaryChains.append(mainChain)
        return True

    def newBlockCausedAFork(self, block):
        """
            Checks if a block causes a fork,
            thus creates a new secondary chain
        """
        with self.blockchainLock:
            if blockNumber := self.blockchain.is_prev_hash_in_chain(block):

                newChain = self.blockchain.copy(blockNumber)
                newChain.add_block(block)

                # For evaluation purposes
                self.signal.put("New Block")

                # Release blocks
                # self.releaseTransactionsFromNewBlock(block)

                # Put main back into secondary chains
                with self.secondaryChainsLock:
                    self.secondaryChains.append(newChain)
                return True

        return False

    def addOrphanBlock(self, block):
        """
            Block passed in becomes an orphan.
        """
        with self.orphanBlocksLock:
            self.orphanBlocks.append(block)
            return True

    def processBlock(self, block):
        """ Processes a new block incomming """
        # 1) Check hash is valid
        if not self.newBlockHashValid(block):
            return False

        # 2) Check to see if transactions are valid
        if not self.newBlockTransactionsValid(block):
            return False

        # 3) See if block belongs on main chain
        if self.newBlockBelongsOnMainChain(block):
            return True

        # 4) If not here then it might be in a secondary chain
        if contender := self.newBlockBelongsOnSecondaryChains(block):
            # 5) Check if main chain needs replaced
            return self.challengeMainChain(contender, block)

        # 6) Check if block's prev hash is a part of main chain,
        #    if so, create a secondary chain, with new block as head
        if self.newBlockCausedAFork(block):
            return True

        # 7) Since there is not place for block to go, call it an orphan.
        return self.addOrphanBlock(block)

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
        """
            As the name implies, this thread
            processes any request, sent from
            filtered by the data handler.
        """
        try:
            while _thread["status"] != ThreadStatus.STOPPING:

                # 1. Process a requests
                try:
                    request = self.requests.get(block=True, timeout=0.1)
                    request.open(self)
                    self.requests.task_done()
                except Empty:
                    # No requests available
                    pass
                except Exception:
                    print("Exception raised processing request!")

                # 2. Process a blockchain
                try:
                    # Get blockchain
                    blockchain = self.blockchains.get(block=True, timeout=0.1)
                    self.processBlockchain(blockchain)
                    self.blockchains.task_done()
                except Empty:
                    # No blockchain available
                    pass
                except Exception:
                    print("Exception Raised processing blockchain!")

                # 3. Process a incoming blocks
                try:
                    block = self.blocks.get(block=True, timeout=0.1)
                    self.blocks.task_done()
                    self.processBlock(block)
                    # self.releaseTransactions()
                except Empty:
                    # No blocks available
                    pass
                except Exception:
                    print("Exception raised processing block!")

        except Exception:
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def minningThread(self, _thread):
        """
            This thread starts the minning process.
        """
        print("Starting to mine...")
        try:
            while _thread["status"] != ThreadStatus.STOPPING:

                if self.throttle_minning:
                    sleep(0.3)

                try:
                    # Before minning, get the transactions from transaction pool
                    poolTxs = self.pool.take(TRANSACTIONS_TO_MINE)

                    if poolTxs:
                        transactions = []
                        # Then make sure to run any contract code
                        with self.blockchainLock:
                            for transaction in poolTxs:
                                returnedTxs = transaction.exec(self.blockchain)
                                if isinstance(returnedTxs, list):
                                    transactions = [
                                        *transactions, *returnedTxs]
                                else:
                                    transactions = [*transactions, returnedTxs]

                        # Once any contract code has been ran, mine the data and remove transactions from pool
                        isMined = self._mine(transactions)
                        if isMined:
                            for tx in poolTxs:
                                self.pool.remove(tx)

                    sleep(0.1)
                except (Exception):
                    # Something went wrong in minning, just try again
                    pass
        except Exception:
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR

    def peerWatcherThread(self, _thread):
        """
            This thread watches out for new threads.
            If one if found, it sends a request for 
            their blockchain.
        """
        try:
            while _thread["status"] != ThreadStatus.STOPPING:
                try:
                    newPeer = self.router.newPeerQueue.get(
                        block=True, timeout=5)
                    blockchainReq = BlockchainRequestMessage(
                        self.ip, self.port)
                    self.router.send(newPeer[0], newPeer[1], blockchainReq)

                except Exception as e:
                    # No new peers
                    pass

        except Exception:
            with _thread["lock"]:
                _thread["status"] = ThreadStatus.ERROR
