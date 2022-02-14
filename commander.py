from bevali import Bevali
from multiprocessing import Process
from multiprocessing.connection import Listener
from multiprocessing.connection import Client
from transactions import ContractCreateTransaction, ContractInvokeTransaction
from time import sleep
import json

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
            edit = ContractInvokeTransaction()
        elif cmd == "delete_file":
            delete = ContractInvokeTransaction()
        elif cmd == "send_file":
            send = ContractInvokeTransaction()
        elif cmd == 'close':
            conn.close()
            break
    listener.close()
    node.stop()


if __name__ == '__main__':
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
