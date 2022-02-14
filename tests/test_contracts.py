from bevali import Bevali
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from transactions import Transaction, ContractUpdateTranscation, ContractInvokeTransaction, ContractCreateTransaction
from time import sleep
import os


def import_code(filename):
    code = ""
    cwd = os.getcwd() + "\\tests\\"
    with open(cwd + filename, "r") as f:
        code = ''.join(f.readlines())
    return code


def create_x_files(bevali, user_id, number_of_files):
    code = import_code("contract.py")
    for i in range(1, number_of_files+1):
        memory = {"id": i}
        state = {"permission_list": [
            "Bob", "Alice", "Carol"], "files_in_circulation": 1}
        fileContract = ContractCreateTransaction(
            user_id, i, code, memory, state)
        bevali.sendTransaction(fileContract)


def test_log_edit_file():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    bob.createNewChain()

    # Bob will be the miner
    bob.start_minning()
    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will create 1 files
    create_x_files(alice, "Alice", 1)
    sleep(1)

    # Alice will then invoke contract to upload a log
    editLog = ContractInvokeTransaction(
        "Alice", 1, {"action": "edit", "to": "Alice"})
    alice.sendTransaction(editLog)

    sleep(10)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["action"] == "edit" and bobT.data["action"]
           == "edit" and carolT.data["action"] == "edit")


def test_log_delete_file():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    bob.createNewChain()

    # Bob will be the miner
    bob.start_minning()
    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will create 1 files
    create_x_files(alice, "Alice", 1)
    sleep(1)

    # Alice will then invoke contract to upload a log
    deleteLog = ContractInvokeTransaction(
        "Alice", 1, {"action": "delete", "to": "Alice"})
    alice.sendTransaction(deleteLog)

    sleep(10)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["action"] == "delete" and bobT.data["action"]
           == "delete" and carolT.data["action"] == "delete")


def test_log_send_file():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    bob.createNewChain()

    # Bob will be the miner
    bob.start_minning()
    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will create 1 files
    create_x_files(alice, "Alice", 1)
    sleep(1)

    # Alice will then invoke contract to upload a log
    sendLog = ContractInvokeTransaction(
        "Alice", 1, {"action": "send", "to": "Bob"})
    alice.sendTransaction(sendLog)

    sleep(7)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[0]
    bobT = bob.blockchain.chain[-1].data[0]
    carolT = carol.blockchain.chain[-1].data[0]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["action"] == "send" and bobT.data["action"]
           == "send" and carolT.data["action"] == "send")
