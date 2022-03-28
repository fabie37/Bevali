
from bevali import Bevali
import blockchain
from blockchain.block import Block
from tests.test_networking import LOCAL_HOST
from tests.test_networking import PORT_START
from transactions import Transaction, ContractUpdateTranscation, ContractInvokeTransaction, ContractCreateTransaction, signHash, findState
from time import sleep
from math import log
import os

from transactions.transaction import findState


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
    " Creates a sample blockchain for test"
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
    alice._mine("block")
    sleep(3)
    # 3. Carol connects to bob and gets alice's blockchain too
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # 4. We then check if carol got alice's blockchain
    carolgotBlockchain = True

    if len(carol.blockchain.chain) != BLOCKCHAIN_SIZE + 2:
        carolgotBlockchain = False

    alice.stop()
    bob.stop()
    carol.stop()

    assert(carolgotBlockchain)


def with_x_peers_check_blockchain_on_connect(x):

    # Create x peers
    peers = []
    for i in range(0, x):
        peer = Bevali(LOCAL_HOST, PORT_START + i)
        peers.append(peer)
        peer.start()

    sleep(15)
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


def test_send_transaction():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()

    transaction = Transaction("123", data={"hello": 1234})
    contract = ContractCreateTransaction("123", "234", "code", {1: 123}, {
                                         1: 123}, data={"hello": 1234})
    invoke = ContractInvokeTransaction("123", "123", data="Hello")
    update = ContractUpdateTranscation("123", "234", {1: 123})

    sleep(2)

    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)

    sleep(2)

    bob.sendTransaction(transaction)
    bob.sendTransaction(contract)
    bob.sendTransaction(invoke)
    bob.sendTransaction(update)

    sleep(2)

    size_of_alice_pool = len(alice.pool)
    size_of_carol_pool = len(carol.pool)

    alice.stop()
    bob.stop()
    carol.stop()

    assert(size_of_alice_pool == 4 and size_of_carol_pool == 4)


def test_transaction_mined():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    sleep(3)
    sample_blockchain(bob)

    # Bob will be a minner
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will send the transaction to her peers
    transaction = Transaction("123", data={"hello": 1234})
    alice.sendTransaction(transaction)
    sleep(6)

    # By this point bob should have mined the block and sent it to his peers
    alice_chain_len = len(alice.blockchain.chain)
    bob_chain_len = len(bob.blockchain.chain)
    carol_chain_len = len(carol.blockchain.chain)

    alice.stop()
    bob.stop()
    carol.stop()

    assert(alice_chain_len == BLOCKCHAIN_SIZE + 2 and bob_chain_len ==
           BLOCKCHAIN_SIZE + 2 and carol_chain_len == BLOCKCHAIN_SIZE + 2)


def test_contract_executed():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    bob.createNewChain()

    # Bob will be a minner
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will send the transaction to her peers
    code = ""
    cwd = os.getcwd() + "/tests/"
    with open(cwd + "contract_1.py", "r") as f:
        code = ''.join(f.readlines())
    memory = {}
    state = {}
    transaction = ContractCreateTransaction("123", "246", code, memory, state)
    alice.sendTransaction(transaction)
    sleep(5)
    invoke = ContractInvokeTransaction("123", "246")
    alice.sendTransaction(invoke)
    sleep(9)

    # By this point bob should have mined the block and sent it to his peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(isinstance(aliceT, Transaction) and isinstance(
        bobT, Transaction) and isinstance(carolT, Transaction))


def test_contract_state_updated():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()
    bob.createNewChain()

    # Bob will be a minner
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)
    carol.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will send the transaction to her peers
    code = ""
    cwd = os.getcwd() + "/tests/"
    with open(cwd + "contract_2.py", "r") as f:
        code = ''.join(f.readlines())
    memory = {}
    state = {"updated": False}
    transaction = ContractCreateTransaction("123", "246", code, memory, state)
    alice.sendTransaction(transaction)
    sleep(5)
    update = ContractUpdateTranscation("123", "246", {"updated": True})
    carol.sendTransaction(update)
    sleep(5)
    invoke = ContractInvokeTransaction("123", "246")
    alice.sendTransaction(invoke)
    sleep(9)

    # By this point bob should have mined the block and sent it to his peers
    aliceT = alice.blockchain.chain[-1].data[1]
    bobT = bob.blockchain.chain[-1].data[1]
    carolT = carol.blockchain.chain[-1].data[1]

    alice.stop()
    bob.stop()
    carol.stop()

    assert(isinstance(aliceT, Transaction) and isinstance(
        bobT, Transaction) and isinstance(carolT, Transaction))


def test_permission_list_updated():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)

    alice.start()
    bob.start()
    bob.createNewChain()

    # Bob will be a minner
    bob.start_minning()

    alice.connectToNode(bob.ip, bob.port)
    sleep(3)

    # Alice will send the transaction to her peers
    code = ""
    cwd = os.getcwd() + "/tests/"
    with open(cwd + "contract.py", "r") as f:
        code = ''.join(f.readlines())
    memory = {"id": "246"}
    state = {"permission_list": ["Alice"], "files_in_circulation": 1}
    transaction = ContractCreateTransaction(
        "Alice", "246", code, memory, state)
    alice.sendTransaction(transaction)
    sleep(5)
    update = ContractInvokeTransaction(
        "Alice", "246", data={"action": "addUser", "user": "Bob"})
    alice.sendTransaction(update)
    sleep(10)
    # By this point bob should have mined the block and sent it to his peers
    newState = findState(alice.blockchain, "246", state.keys())

    alice.stop()
    bob.stop()

    assert ("Bob" in newState["permission_list"])


def test_blockchain_2_blocks_ahead():
    alice = Bevali(LOCAL_HOST, PORT_START)

    longchain = blockchain.Blockchain()
    shortchain = blockchain.Blockchain()
    longchain.add_block(Block())
    shortchain.add_block(Block())
    for i in range(4):
        tx = ContractCreateTransaction("alice", i, "", {}, {})
        mined_block = longchain.mine_block([tx])
        longchain.add_block(mined_block)
        shortchain.add_block(mined_block)

    tx_5 = ContractCreateTransaction("alice", 5, "", {}, {})
    tx_6 = ContractCreateTransaction("alice", 6, "", {}, {})
    tx_7 = ContractCreateTransaction("alice", 7, "", {}, {})
    tx_9 = ContractCreateTransaction("alice", 9, "", {}, {})

    shortchain.add_block(shortchain.mine_block([tx_5, tx_6, tx_9]))

    longchain.add_block(longchain.mine_block([tx_5]))
    longchain.add_block(longchain.mine_block([tx_6]))
    longchain.add_block(longchain.mine_block([tx_7]))

    alice.blockchain = longchain
    alice.secondaryChains.append(shortchain)

    alice.releaseTransactions()

    # This should be []
    secondaryChains = alice.secondaryChains

    # This should shoudld contract a contract with contract_id 7
    releasedtx = alice.pool.pop()
    assert(not secondaryChains and releasedtx == tx_9)


def test_new_block_removes_old_transactions():

    tx_5 = ContractCreateTransaction("alice", 5, "", {}, {})
    tx_6 = ContractCreateTransaction("alice", 6, "", {}, {})
    tx_7 = ContractCreateTransaction("alice", 7, "", {}, {})
    tx_9 = ContractCreateTransaction("alice", 9, "", {}, {})

    alice = Bevali(LOCAL_HOST, PORT_START)
    longchain = blockchain.Blockchain()
    longchain.add_block(Block())
    longchain.add_block(longchain.mine_block([tx_5]))
    longchain.add_block(longchain.mine_block([tx_6]))
    longchain.add_block(longchain.mine_block([tx_7]))
    alice.pool.append(tx_9)

    alice.blockchain = longchain
    alice.releaseTransactionsFromNewBlock(longchain.mine_block([tx_9]))
    releasedtx = alice.pool
    assert(not releasedtx)


def test_main_blockchain_switches_with_longer_secondary():
    alice = Bevali(LOCAL_HOST, PORT_START)

    main = blockchain.Blockchain()
    secondary = blockchain.Blockchain()
    main.add_block(Block())
    secondary.add_block(Block())
    for i in range(4):
        tx = ContractCreateTransaction("alice", i, "", {}, {})
        mined_block = main.mine_block([tx])
        main.add_block(mined_block)
        secondary.add_block(mined_block)

    tx_5 = ContractCreateTransaction("alice", 5, "", {}, {})
    tx_6 = ContractCreateTransaction("alice", 6, "", {}, {})
    tx_9 = ContractCreateTransaction("alice", 9, "", {}, {})

    main.add_block(main.mine_block([tx_5]))
    secondary.add_block(main.mine_block([tx_6]))

    alice.blockchain = main
    alice.secondaryChains.append(secondary)
    alice.processBlock(secondary.mine_block([tx_6, tx_9]))

    # This should be []
    mainChain = alice.blockchain
    secondaryChain = alice.secondaryChains[0]

    assert(mainChain == secondary and secondaryChain == main)


def test_new_secondary_chain_created_on_competing_block():
    alice = Bevali(LOCAL_HOST, PORT_START)

    main = blockchain.Blockchain()
    main.add_block(Block())
    for i in range(4):
        tx = ContractCreateTransaction("alice", i, "", {}, {})
        mined_block = main.mine_block([tx])
        main.add_block(mined_block)

    competingChain = main.copy(2)
    tx = ContractCreateTransaction("alice", i, "", {}, {})
    competingBlock = competingChain.mine_block([tx])

    alice.blockchain = main
    alice.processBlock(competingBlock)
    secondaryChain = alice.secondaryChains[0]

    assert(len(secondaryChain.chain) == 4)


def test_connect():
    alice = Bevali(LOCAL_HOST, PORT_START)
    alice.createNewChain()
    alice.start()
    sleep(3)
    peers = []
    for i in range(1, 10):
        peer = Bevali(LOCAL_HOST, PORT_START + i)
        peer.start()
        sleep(0.5)
        peer.connectToNode(LOCAL_HOST, PORT_START)
        peers.append(peer)

    sleep(20)

    connections = []
    for peer in peers:
        connections.append(len(peer.router.socketAddressToPeerAddress))

    connections.append(len(alice.router.socketAddressToPeerAddress))
    for peer in peers:
        peer.stop()
    alice.stop()
    assert(sum(connections) == 9 + 9)


def test_encrypted_transaction():
    alice = Bevali(LOCAL_HOST, PORT_START)

    main = blockchain.Blockchain()
    main.add_block(Block())
    for i in range(1, 4):
        tx = ContractCreateTransaction(
            alice.getSerialPublicKey(), i, "", {}, {}, None, alice.getSerialPublicKey())
        signHash(tx, alice.privateKey)
        mined_block = main.mine_block([tx])
        main.add_block(mined_block)

    valid = True
    for block in main.chain:
        valid = alice.newBlockTransactionsValid(block)

    return valid


def test_tampered_encrypted_transaction():
    alice = Bevali(LOCAL_HOST, PORT_START)

    main = blockchain.Blockchain()
    main.add_block(Block())
    for i in range(1, 4):
        tx = ContractCreateTransaction(
            alice.getSerialPublicKey(), i, "", {}, {}, None, alice.getSerialPublicKey())
        signHash(tx, alice.privateKey)
        tx.data = [1, 2, 3]
        mined_block = main.mine_block([tx])
        main.add_block(mined_block)

    valid = True
    for block in main.chain:
        valid = alice.newBlockTransactionsValid(block)

    return not valid


def test_consensus_is_reached():
    alice = Bevali(LOCAL_HOST, PORT_START)
    bob = Bevali(LOCAL_HOST, PORT_START + 1)
    carol = Bevali(LOCAL_HOST, PORT_START + 2)

    alice.start()
    bob.start()
    carol.start()

    alice.start_minning()
    alice.createNewChain(target='00')

    for i in range(1, 100):
        tx = ContractCreateTransaction("", i, {}, {}, None, None, None)
        alice.sendTransaction(tx)

    sleep(5)
    alice.stop_minning()

    # Connect three peers
    bob.connectToNode(alice.ip, alice.port)
    carol.connectToNode(alice.ip, alice.port)
    bob.connectToNode(carol.ip, carol.port)
    sleep(3)

    # Start two competeing agents
    bob.throttle_minning = True
    bob.start_minning()
    carol.start_minning()

    # Let alice start broadcasting transactions
    for i in range(101, 400):
        tx = ContractCreateTransaction("", i, {}, {}, None, None, None)
        alice.sendTransaction(tx)

    sleep(30)

    lengths = []
    lengths.append(len(alice.blockchain.chain))
    lengths.append(len(bob.blockchain.chain))
    lengths.append(len(carol.blockchain.chain))

    # Check blockchain are same length
    sameLength = True
    for i in range(len(lengths) - 1):
        if lengths[i] != lengths[i + 1]:
            sameLength = False
            break

    # Check blockchains are actually the same
    sameBlocks = True
    if sameLength:
        for block in range(0, lengths[0]):
            alice_block = alice.blockchain.chain[block]
            bob_block = bob.blockchain.chain[block]
            carol_block = carol.blockchain.chain[block]

            if alice_block != bob_block or bob_block != carol_block:
                sameBlocks = False

    alice.stop()
    bob.stop()
    carol.stop()
    assert(sameLength and sameBlocks)
