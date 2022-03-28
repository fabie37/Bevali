from bevali import Bevali
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from transactions import ContractInvokeTransaction, ContractCreateTransaction, Transaction
from time import sleep
import os


def import_code(filename):
    code = ""
    cwd = os.getcwd() + "/tests/"
    with open(cwd + filename, "r") as f:
        code = ''.join(f.readlines())
    return code


def create_x_files(bevali, user_id, number_of_files, permissionList=None):
    code = import_code("contract.py")
    for i in range(1, number_of_files + 1):
        memory = {"id": i}
        if not permissionList:
            state = {"permission_list": [
                "Bob", "Alice"], "files_in_circulation": 1}
        else:
            state = {"permission_list": [], "files_in_circulation": 1}
            for id in permissionList:
                state["permission_list"].append(id)
        fileContract = ContractCreateTransaction(
            user_id, i, code, memory, state)
        bevali.sendTransaction(fileContract)


def test_contract_stored_on_blockchain():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)

    alice.start()
    bob.start()
    bob.createNewChain()
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)
    sleep(2)

    create_x_files(alice, "Alice", 1)
    sleep(2)

    hasContract = False
    for i in range(len(alice.blockchain.chain)):
        alice_block = alice.blockchain.chain[i]
        bob_block = bob.blockchain.chain[i]

        if alice_block.data and bob_block.data:
            for tx in range(len(alice_block.data)):
                alice_tx = alice_block.data[tx]
                bob_tx = bob_block.data[tx]

                if isinstance(alice_tx, ContractCreateTransaction) and isinstance(bob_tx, ContractCreateTransaction):
                    hasContract = True

    alice.stop()
    bob.stop()

    return hasContract


def test_invocation_to_sum_contract():
    sumContract = import_code("sum_contract.py")

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

    # Alice sends a contract on the blockchain to sum two values
    sumC = ContractCreateTransaction(
        "Alice", 99, sumContract, None, None, None, None)
    alice.sendTransaction(sumC)
    sleep(3)

    # Then alice sends a invocation to the add contract to add various numbers
    add45 = ContractInvokeTransaction("Alice", 99, data={
        "var_1": 4,
        "var_2": 5
    })

    add98 = ContractInvokeTransaction("Alice", 99, data={
        "var_1": 9,
        "var_2": 8
    })

    alice.sendTransaction(add45)
    alice.sendTransaction(add98)

    # Wait for execution and minning
    sleep(10)

    alice_chain = alice.blockchain.chain
    bob_chain = bob.blockchain.chain
    carol_chain = carol.blockchain.chain

    targets = {
        9: False,
        17: False
    }
    for block in range(len(alice_chain)):
        if alice_chain[block].data:
            for tx in range(len(alice_chain[block].data)):
                a_tx = alice_chain[block].data[tx]
                b_tx = bob_chain[block].data[tx]
                c_tx = carol_chain[block].data[tx]

                if isinstance(a_tx, Transaction) and isinstance(b_tx, Transaction) and isinstance(c_tx, Transaction):
                    if a_tx.data and b_tx.data and c_tx.data:
                        if "result" in a_tx.data:
                            if a_tx.data["result"] in targets and b_tx.data["result"] in targets and c_tx.data["result"] in targets:
                                targets[a_tx.data["result"]] = True

    alice.stop()
    bob.stop()
    carol.stop()
    assert(targets[9] and targets[17])


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

    sleep(4)

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

    sleep(4)

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

    sleep(4)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[0]
    bobT = bob.blockchain.chain[-1].data[0]
    carolT = carol.blockchain.chain[-1].data[0]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["action"] == "send" and bobT.data["action"]
           == "send" and carolT.data["action"] == "send")


def test_log_violation_edit_file():
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
        "Carol", 1, {"action": "edit", "to": "Carol"})
    carol.sendTransaction(sendLog)

    sleep(4)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["type"] == "violation log" and bobT.data["type"]
           == "violation log" and carolT.data["type"] == "violation log")


def test_log_violation_delete_file():
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
        "Carol", 1, {"action": "delete", "to": "Carol"})
    carol.sendTransaction(sendLog)

    sleep(4)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["type"] == "violation log" and bobT.data["type"]
           == "violation log" and carolT.data["type"] == "violation log")


def test_log_violation_send_file():
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
        "Carol", 1, {"action": "send", "to": "Billy Joe"})
    carol.sendTransaction(sendLog)

    sleep(4)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["type"] == "violation log" and bobT.data["type"]
           == "violation log" and carolT.data["type"] == "violation log")


def test_log_violation_send_file_from_authenticated_user():
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
        "Alice", 1, {"action": "send", "to": "Carol"})
    alice.sendTransaction(sendLog)

    sleep(4)

    # Check that the log is on the blockchain for each of the peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(aliceT.data["type"] == "violation log" and bobT.data["type"]
           == "violation log" and carolT.data["type"] == "violation log")
