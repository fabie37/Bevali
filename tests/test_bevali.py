
from bevali import Bevali
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from time import sleep


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

    for i in range(0, 10):
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

    for x in range(0, 11):
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
    sleep(2)

    # 3. Carol connects to bob and gets alice's blockchain too
    carol.connectToNode(bob.ip, bob.port)
    sleep(2)

    # 4. We then check if carol got alice's blockchain
    bothChainsThere = True

    if len(carol.blockchain.chain) != 11 or len(carol.secondaryChains[0].chain) != 11:
        bothChainsThere = False

    alice.stop()
    bob.stop()
    carol.stop()

    assert(bothChainsThere)
