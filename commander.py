from bevali import Bevali
from multiprocessing import Process
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
from blockchain.blockchain import Blockchain, Block
from transactions import ContractCreateTransaction, ContractInvokeTransaction, findContract, Transaction
from tests.test_contracts import import_code
from time import sleep
import json
import time
import yappi


FILES = 1

BLOCKCHAIN_PORT = 1000
BLOCKCHAIN_IP = "127.0.0.1"

SLAVE_PORT = 6000
SLAVE_IP = "127.0.0.1"

WATCHERPORT = BLOCKCHAIN_PORT - 1

name_to_blockchain_port = {}
name_to_slave_port = {}
processes = []


def custom_commander():
    # 0) Get test details
    test_data = parseCommands("commandlist.dat")
    client_names = test_data["clients"]
    commands = test_data["commands"]

    # 1) Create a blockchain on this thread for monitoring
    watcher_node = Bevali(BLOCKCHAIN_IP, WATCHERPORT)
    watcher_node.start()
    watcher_node.createNewChain()

    # 2) Start processes
    for index, client in enumerate(client_names):
        bport = BLOCKCHAIN_PORT + index
        sport = SLAVE_PORT + index
        name_to_blockchain_port[client] = bport
        name_to_slave_port[client] = sport
        p = Process(target=node, args=(bport, sport))
        processes.append(p)
        p.start()

    for command in commands:
        name = command["name"]
        cmd = command["cmd"]
        data = command["data"]

        if cmd != "wait":
            bport = name_to_blockchain_port[name]
            sport = name_to_slave_port[name]
            address = (SLAVE_IP, sport)
            conn = Client(address, authkey=b'secret password')
            conn.send([cmd, data])
            conn.close()
        else:
            sleep(data)
            for socket in watcher_node.router.peerAddressToSocket:
                print(socket)

    # 3) Once all commands sent, close connection
    for client in client_names:
        bport = name_to_blockchain_port[client]
        sport = name_to_slave_port[client]
        address = (SLAVE_IP, sport)
        conn = Client(address, authkey=b'secret password')
        conn.send(["close", {}])
        conn.close()

    # 4) Ask all processes to join main thread
    for p in processes:
        p.join()

    watcher_node.stop()
    print("Done!")


def parseCommands(filename):
    with open(filename, 'r') as fp:
        lines = json.loads(fp.read().replace('\n', ''))
    return lines


def findevent(blockchain, id):
    # Method to spawn slave
    pass


def node(blockchain_port, slave_port, miner):
    node = Bevali(BLOCKCHAIN_IP, blockchain_port)
    node.start()
    node.connectToNode(BLOCKCHAIN_IP, WATCHERPORT)

    if miner:
        node.start_minning()

    address = (SLAVE_IP, slave_port)
    listener = Listener(address, authkey=b'secret password')
    while True:
        conn = listener.accept()
        msg = conn.recv()
        cmd = msg[0]
        data = msg[1]
        if cmd == 'mine':
            node.start_minning()
        elif cmd == 'stop_mine':
            node.stop_minning()
        elif cmd == "create_new_chain":
            node.createNewChain()
        elif cmd == "sendTransaction":
            node.sendTransaction(None)
        elif cmd == "connectToNode":
            ip = BLOCKCHAIN_IP if data["ip"] == "BLOCKCHAIN_IP" else data["ip"]
            port = WATCHERPORT if data["port"] == "WATCHERPORT" else data["port"]
            node.connectToNode(ip, port)
        elif cmd == "create_file":
            contract = ContractCreateTransaction()
        elif cmd == "edit_file":
            creator = data["creator"]
            contract_id = data["contract_id"]
            action = {
                "action": "edit",
                "to": creator
            }
            edit = ContractInvokeTransaction(creator, contract_id, action)
            node.sendTransaction(edit)

        elif cmd == "delete_file":
            delete = ContractInvokeTransaction()
        elif cmd == "send_file":
            send = ContractInvokeTransaction()
        elif cmd == 'close':
            conn.close()
            break
        sleep(10)
    listener.close()
    node.stop()


def violation_in_chain(chain):
    # Check last 5 blocks for a violation
    for block in reversed(chain[-1:]):
        data = block.data
        for transaction in data:
            if type(transaction) is Transaction and transaction.data["type"] == "violation log":
                return True
    return False


def create_demo_chain():
    demochain = Blockchain()
    demochain.add_block(Block())
    code = import_code("contract.py")
    for x in range(0, 5):
        memory = {"id": x}
        state = {"permission_list": [1, 2], "files_in_circulation": 1}
        file = ContractCreateTransaction(
            "Watcher Node", x, code, memory, state)
        demochain.add_block(demochain.mine_block([file]))

    return demochain


def evaluation_violation_detection(num_peers, num_miners, num_blocks):

    # 0) Generate x peers
    sleep(3)
    watcher_node = Bevali(BLOCKCHAIN_IP, WATCHERPORT)
    watcher_node.blockchain = create_demo_chain()
    watcher_node.blockchain.target = '00'
    watcher_node.start()
    # watcher_node.start_minning()

    for peer_id in range(1, num_peers):  # Exclude 1 peer because of watcher
        bport = BLOCKCHAIN_PORT + peer_id
        sport = SLAVE_PORT + peer_id
        name_to_blockchain_port[peer_id] = bport
        name_to_slave_port[peer_id] = sport
        miner = False
        if num_miners > 0:
            miner = True
            num_miners -= 1
        p = Process(target=node, args=(bport, sport, miner))
        processes.append(p)
        p.start()

    sleep(20)

    # 1) Generate x blocks
    code = import_code("contract.py")
    for block in range(5, num_blocks):
        memory = {"id": block}
        state = {"permission_list": [1, 2], "files_in_circulation": 1}
        file = ContractCreateTransaction(
            "Watcher Node", block, code, memory, state)
        watcher_node.sendTransaction(file)

    sleep(200)

    # 2) Tell a peer to violate contract & record time taken
    bport = name_to_blockchain_port[num_peers - 1]
    sport = name_to_slave_port[num_peers - 1]
    address = (SLAVE_IP, sport)
    cmd = "edit_file"
    data = {"creator": "Violator", "contract_id": num_blocks - 20, "data":
            ["edit", num_peers - 1]
            }

    conn = Client(address, authkey=b'secret password')
    # 3) Record time taken to detect violation
    start_time = time.time()
    conn.send([cmd, data])
    conn.close()
    while not violation_in_chain(watcher_node.blockchain.chain):
        pass
    stop_time = time.time() - start_time

    # 4) Write Results
    with open("results.dat", "a+") as f:
        f.write(
            f"Blocks: {num_blocks}. Peers: {num_peers}. Time: {stop_time}\n")

    # 5) Close connections
    for peer_id in range(1, num_peers):
        bport = name_to_blockchain_port[peer_id]
        sport = name_to_slave_port[peer_id]
        address = (SLAVE_IP, sport)
        conn = Client(address, authkey=b'secret password')
        conn.send(["close", {}])
        conn.close()

    # 4) Ask all processes to join main thread
    for p in processes:
        p.join()

    watcher_node.stop()
    print(f"Main Chain:\n")
    print(f"Length: {len(watcher_node.blockchain.chain)}")
    print("Transactions:\n")
    for block in watcher_node.blockchain.chain:
        for tx in block.data:
            if isinstance(tx, ContractCreateTransaction) or isinstance(tx, ContractInvokeTransaction):
                print(f"Main Tx: {tx.contract_id}")
            else:
                print(f"Main Tx: {tx.data}")

    for snd in watcher_node.secondaryChains:
        print(f"Secondary Chain Lengths: {len(snd.chain)}\n")

    print("\n Orphan Blocks:\n")
    for block in watcher_node.orphanBlocks:
        for tx in block.data:
            if isinstance(tx, ContractCreateTransaction) or isinstance(tx, ContractInvokeTransaction):
                print(f"Orphan Tx: {tx.contract_id}")
            else:
                print(f"Orphan Tx:{tx.data}")

    print(f"\n Number of transactions in pool: {len(watcher_node.pool)}")


if __name__ == '__main__':
    yappi.start()
    yappi.set_clock_type("cpu")  # Use set_clock_type("wall") for wall time
    evaluation_violation_detection(5, 2, 100)
    yappi.get_func_stats().print_all()
    yappi.get_thread_stats().print_all()
