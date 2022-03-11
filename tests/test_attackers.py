from bevali import Bevali
from time import sleep
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from tests.test_bevali import sample_blockchain
from tests.test_contracts import import_code, create_x_files
from transactions import ContractInvokeTransaction


def test_agent_does_not_accept_blockchain_that_malicious_peer_edits():
    """
        Test to check alice doesn't accept bobs blockchain if he
        modifies data on the chain
    """

    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    sample_blockchain(bob)

    bob.start()
    alice.start()

    bob.blockchain.chain[1].data = "wrong data"

    alice.connectToNode(bob.ip, bob.port)

    sleep(1)

    # Check alice did not accept the blockchain
    bc = alice.blockchain.chain

    bob.stop()
    alice.stop()

    assert(not bc)


def test_agent_does_not_accept_modified_mined_transaction():
    """
        Test to check alice doesn't accept bobs blockchain if he
        modifies data on the chain
    """

    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    sample_blockchain(bob)

    bob.start()
    alice.start()
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)

    sleep(1)

    # Alice creates a contract to edit file called "1"
    create_x_files(alice, alice.getSerialPublicKey(), 1, permissionList=[
                   alice.getSerialPublicKey(), bob.getSerialPublicKey()])

    # Wait for bob to mine next block
    sleep(3)

    # Tell bob to stop minning
    bob.stop_minning()
    sleep(3)

    # Alice now says she is editing file
    editTx = ContractInvokeTransaction(alice.getSerialPublicKey(
    ), 1, {"action": "edit", "to": "Alice"}, alice.getSerialPublicKey())

    # Alice broadcasts trasaction
    alice.sendTransaction(editTx)

    # Wait for bob to get tx
    sleep(2)

    # Bob gets transaction and edits the data
    bob.pool[0].data["action"] = "delete"

    # Bob then mines the data
    bob.disableChecks = True
    bob.start_minning()
    sleep(3)

    # Check alice did not accept the corrupt block
    alicechain_length = len(alice.blockchain.chain)

    bob.stop()
    alice.stop()

    assert(alicechain_length != 13)
