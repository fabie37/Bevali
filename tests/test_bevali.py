
from bevali import Bevali
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from time import sleep
from math import log

BLOCKCHAIN_SIZE = 10


def test_create_new_blockchain():
    bevali = Bevali(LOCAL_HOST, PORT_START)
    bevali.start()
    bevali.createNewChain()

    isCreated = False
    if bevali.blockchain and bevali.blockchain.check_integrity():
        isCreated = True

    bevali.stop()
    assert(isCreated)


def sample_blockchain(bevali):
    " Creates a sample blockchain for testr"
    bevali.createNewChain()

    for i in range(0, BLOCKCHAIN_SIZE):
        block = bevali.blockchain.mine_block("somedata")
        bevali.blockchain.add_block(block)


def test_get_peer_blockchain():

    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    alice.start()
    bob.start()

    # 1. bob creates a blockchain and mines a few blocks
    sample_blockchain(bob)

    # 2. Alice then joins the network
    alice.connectToNode(bob.ip, bob.port)
    sleep(5)

    # 3. We then check if alice blockchain is same as bobs
    isEqual = True

    for x in range(0, BLOCKCHAIN_SIZE):
        if alice.blockchain.chain[x] != bob.blockchain.chain[x]:
            isEqual = False

    alice.stop()
    bob.stop()

    assert(isEqual)


def test_peer_watch_get_blockchain_on_connect():

    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()

    # 1. Bob has an existing blockchain
    sample_blockchain(bob)

    # 2. Bob and alice connect
    alice.connectToNode(bob.ip, bob.port)
    sleep(3)
    block = alice.blockchain.mine_block("hello")
    alice.blockchain.add_block(block)
    sleep(3)
    # 3. Carol connects to bob and gets alice's blockchain too
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # 4. We then check if carol got alice's blockchain
    bothChainsThere = True

    if len(carol.blockchain.chain) != BLOCKCHAIN_SIZE + 2 or len(carol.secondaryChains[0].chain) != BLOCKCHAIN_SIZE + 1:
        bothChainsThere = False

    alice.stop()
    bob.stop()
    carol.stop()

    assert(bothChainsThere)


def with_x_peers_check_blockchain_on_connect(x):

    # Create x peers
    peers = []
    for i in range(0, x):
        peer = Bevali(LOCAL_HOST, PORT_START + i)
        peers.append(peer)
        peer.start()

    # Make first peer have a blockchain
    sample_blockchain(peers[0])

    # Make each connect each peer
    for index, peer in enumerate(peers[1:]):
        peer.connectToNode(peers[index].ip, peers[index].port)
        sleep(log(x))

    # Check each peer has blockchain of size BLOCKCHAIN_SIZE + genisus block
    allSameBlockchains = True
    for peer in peers:
        if len(peer.blockchain.chain) != BLOCKCHAIN_SIZE + 1:
            allSameBlockchains = False
            break

    # Stop all peers
    for peer in peers:
        peer.stop()

    return allSameBlockchains


def test_10_peers_have_same_blockchain_on_connect():
    assert (with_x_peers_check_blockchain_on_connect(10))


def test_20_peers_have_same_blockchain_on_connect():
    assert (with_x_peers_check_blockchain_on_connect(20))


def test_mined_block_propogation():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()

    # 1. Bob has an existing blockchain
    sample_blockchain(bob)

    # 2. Bob and alice connect
    alice.connectToNode(bob.ip, bob.port)
    sleep(3)

    # 3. Carol connects to bob and gets alice's blockchain too
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # 4. Carol mines a block
    carol._mine("Hello")
    sleep(3)

    # 5. Check all blockchains have the same length
    aliceLength = len(alice.blockchain.chain)
    bobLength = len(bob.blockchain.chain)
    carolLength = len(carol.blockchain.chain)

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceLength == 12 and bobLength == 12 and carolLength == 12)
