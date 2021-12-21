
from bevali import Bevali
from blockchain import Block
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


def test_get_peer_blockchain():

    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START+1)
    alice.start()
    bob.start()

    # 1. bob creates a blockchain and mines a few blocks
    bob.createNewChain()

    for i in range(0, 10):
        block = bob.blockchain.mine_block("somedata")
        bob.blockchain.add_block(block)

    # 2. Alice then joins the network
    alice.connectToNode(bob.ip, bob.port)
    sleep(2)

    # 3. We then check if alice blockchain is same as bobs
    isEqual = True

    for x in range(0, 11):
        if alice.blockchain.chain[x] != bob.blockchain.chain[x]:
            isEqual = False

    alice.stop()
    bob.stop()

    assert(isEqual)
