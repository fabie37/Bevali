import imp
from bevali import Bevali
from multiprocessing import Process
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
from transactions import ContractCreateTransaction, ContractInvokeTransaction, findContract
from tests.test_contracts import import_code
from time import sleep
import json
import time

from transactions.transaction import Transaction

FILES = 1

BLOCKCHAIN_PORT = 1000
BLOCKCHAIN_IP = "127.0.0.1"

SLAVE_PORT = 6000
SLAVE_IP = "127.0.0.1"

WATCHERPORT = BLOCKCHAIN_PORT - 1

name_to_blockchain_port = {}
name_to_slave_port = {}
processes = []


def parseCommands(filename):
    with open(filename, 'r') as fp:
        lines = json.loads(fp.read().replace('\n', ''))
    return lines


def findevent(blockchain, id):
    # Method to spawn slave
    pass


def node(blockchain_port, slave_port):
    node = Bevali(BLOCKCHAIN_IP, blockchain_port)
    node.start()
    node.connectToNode(BLOCKCHAIN_IP, WATCHERPORT)

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
            # while findContract(node.blockchain, contract_id) is None:
            #     sleep(5)
            edit = ContractInvokeTransaction(creator, contract_id, action)
            node.sendTransaction(edit)

        elif cmd == "delete_file":
            delete = ContractInvokeTransaction()
        elif cmd == "send_file":
            send = ContractInvokeTransaction()
        elif cmd == 'close':
            conn.close()
            break
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


def evaluation_violation_detection(num_peers, num_blocks):

    # 0) Generate x peers
    sleep(3)
    watcher_node = Bevali(BLOCKCHAIN_IP, WATCHERPORT)
    watcher_node.start()
    watcher_node.createNewChain()
    watcher_node.start_minning()

    for peer_id in range(1, num_peers):  # Exclude 1 peer because of watcher
        bport = BLOCKCHAIN_PORT + peer_id
        sport = SLAVE_PORT + peer_id
        name_to_blockchain_port[peer_id] = bport
        name_to_slave_port[peer_id] = sport
        p = Process(target=node, args=(bport, sport))
        processes.append(p)
        p.start()

    # Gives the processes a chance to start up
    sleep(3)

    # 1) Generate x blocks
    code = import_code("contract.py")
    for block in range(1, num_blocks):
        memory = {"id": block}
        state = {"permission_list": [1, 2], "files_in_circulation": 1}
        file = ContractCreateTransaction(
            "Watcher Node", block, code, memory, state)
        watcher_node.sendTransaction(file)

    sleep(3)

    # 2) Tell a peer to violate contract & record time taken
    bport = name_to_blockchain_port[num_peers - 1]
    sport = name_to_slave_port[num_peers - 1]
    address = (SLAVE_IP, sport)
    cmd = "edit_file"
    data = {"creator": "Violator", "contract_id": num_blocks - 1, "data":
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
    print("Done!")


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


if __name__ == '__main__':
    # evaluation_violation_detection(3, 10)
    evaluation_violation_detection(3, 100)
    # evaluation_violation_detection(3, 1000)
    # evaluation_violation_detection(3, 10000)
