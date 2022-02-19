# Correct Module Referencing
from random import randrange
import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Imports
from transactions import ContractCreateTransaction, ContractInvokeTransaction, findContract, Transaction
from blockchain.blockchain import Blockchain, Block
from multiprocessing.connection import Listener, Client
from multiprocessing import Process, JoinableQueue as MQ, Manager
from multiprocessing.managers import SyncManager
from threading import Lock
from time import time, sleep
from tests.test_contracts import import_code
from bevali import Bevali
import pandas as pd

# Constants
BLOCKCHAIN_IP = '127.0.0.1'
WATCHERPORT = 1234
COMMANDER_PORT = 5000

# Demo chain for starting blockchain off
demochain = None


def create_demo_chain(diff):
    """
        Replicates 100 contracts with the same persimissions
    """
    demochain = Blockchain(target=diff)
    demochain.add_block(Block())
    code = import_code("contract.py")
    for x in range(0, 100):
        memory = {"id": x}
        state = {"permission_list": [1, 2], "files_in_circulation": 1}
        file = ContractCreateTransaction(
            "Watcher Node", x, code, memory, state)
        demochain.add_block(demochain.mine_block([file]))
    return demochain


def create_demo_log(logger, contract_id):
    """
        Creates a log to send to peers
    """
    contract_id = contract_id
    action = {
        "action": "edit",
        "to": logger
    }
    return ContractInvokeTransaction(logger, contract_id, action)


def setup_watcher_node():
    """
        Setups up basic peer with pre-implemented blockchain
    """
    watcher = Bevali(BLOCKCHAIN_IP, WATCHERPORT)
    watcher.blockchain = demochain
    return watcher


def launch_processes(proc, numb, argus):
    """
        Returns a list of processess
    """
    processes = []
    for x in range(numb):
        p = Process(target=proc, args=argus[x])
        processes.append(p)
        p.start()
        sleep(2)
    return processes


def wait_for_x_connections(node, conns):
    prs = 0
    while prs < conns:
        with node.router.peerLock:
            if prs != len(node.router.peerAddressToSocket):
                print(
                    f"Node {node.port} connections:{len(node.router.peerAddressToSocket)}")
            prs = len(node.router.peerAddressToSocket)


def sendAlert(address, alert):
    conn = Client(address, authkey=b'123')
    conn.send(alert)
    conn.close()


def listenForAlert(listener):
    conn = listener.accept()
    alert = conn.recv()
    conn.close()


def listenForNumAlerts(listener, num_alerts):
    recv_alerts = 0
    while recv_alerts < num_alerts:
        conn = listener.accept()
        alert = conn.recv()
        recv_alerts += 1
        conn.close()


def getFromQueue(queue, item):
    qItem = queue.get()
    if qItem == item:
        queue.task_done()
        return True
    queue.put(qItem)
    return False


def run_node(ip, port, miner, peers, txs, queue, callbackQ):
    """
        Runs an instance of Bevali Blockchain
    """
    # Blockchain
    node = Bevali(ip, port)
    node.start()
    node.connectToNode(BLOCKCHAIN_IP, WATCHERPORT)
    wait_for_x_connections(node, peers - 1)

    # Tell main process, all peers found
    callbackQ.put("found")

    # Wait for main process to tell you to begin
    while not getFromQueue(callbackQ, "begin"):
        pass

    # Begin experiment
    if miner:
        node.start_minning()

    # Once all peers connected start experiment
    throughput_experiment(node, txs, queue)

    # Tell main process you are done
    callbackQ.put("done")

    # Wait for main process to tell you to stop
    while not getFromQueue(callbackQ, "close"):
        pass

    node.stop()


def connection_experiment(node):
    while True:
        sleep(5)


def throughput_experiment(node, txs, queue):
    """
        Will return when main blockchain has #txs in chain
    """
    start_time = time()
    if isinstance(node, Bevali):
        total = 0
        while total < txs:
            block = None
            node.signal.get()
            with node.blockchainLock:
                if node.blockchain.chain:
                    block = node.blockchain.chain[-1]
            if block:
                for tx in block.data:
                    total += 1
    stop_time = time()
    total_time = stop_time - start_time
    queue.put(total_time)


def experiment_start(num_peers, num_miners, num_tx, difficulty):
    """
        Sets up params for experiement & recording
    """
    qq = MQ()
    manager = Manager()
    callbackQ = manager.Queue()
    argus = []
    miners = num_miners

    # Set up arguments for nodes
    for p in range(1, num_peers):
        # Set miners
        miner = False
        if miners > 0:
            miner = True
            miners -= 1

        arg = [
            BLOCKCHAIN_IP,
            WATCHERPORT + p,
            miner,
            num_peers,
            num_tx,
            qq,
            callbackQ
        ]

        argus.append(arg)

    # Launch watcher
    watcher = setup_watcher_node()
    watcher.start()
    sleep(5)

    # Launch command listener
    # listener = Listener((BLOCKCHAIN_IP, COMMANDER_PORT), authkey=b'123')

    # Launch nodes
    procs = launch_processes(run_node, num_peers - 1, argus)
    sleep(num_peers)

    # Wait for all processes to be connected
    found = 0
    while found < num_peers - 1:
        if getFromQueue(callbackQ, "found"):
            found += 1

    # Once all peers connected tell all peers to start
    for peer in range(1, num_peers):
        callbackQ.put("begin")

    # Start sending transactions
    for tx in range(num_tx, num_tx * 2):
        watcher.sendTransaction(create_demo_log(1, randrange(1, 99)))

    # Wait for all peers to finish collecting new blocks
    finished = 0
    while finished < num_peers - 1:
        if getFromQueue(callbackQ, "done"):
            finished += 1

    # Tell all peers to close
    for peer in range(1, num_peers):
        callbackQ.put("close")

    # Wait for them to finish
    for proc in procs:
        proc.join()

    watcher.stop()
    manager.shutdown()

    # Record results
    times = []
    while not qq.empty():
        times.append(qq.get())

    cols = ["Peers", "Miners", "Transactions", "Time", "Difficulty"]
    data = []
    for t in times:
        data.append([
            num_peers,
            num_miners,
            num_tx,
            t,
            len(difficulty)
        ])

    results = pd.DataFrame(data, columns=cols)
    return results


if __name__ == '__main__':

    # Difficulty Level 1
    diff = '0'
    demochain = create_demo_chain(diff)
    results = experiment_start(2, 1, 100, diff)
    results = pd.concat([results, experiment_start(4, 1, 100, diff)])
    results = pd.concat([results, experiment_start(8, 1, 100, diff)])
    results = pd.concat([results, experiment_start(16, 1, 100, diff)])
    results = pd.concat([results, experiment_start(20, 1, 100, diff)])
    results = pd.concat([results, experiment_start(3, 2, 100, diff)])
    results = pd.concat([results, experiment_start(4, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 2, 100, diff)])
    results = pd.concat([results, experiment_start(16, 2, 100, diff)])
    results = pd.concat([results, experiment_start(20, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 4, 100, diff)])
    results = pd.concat([results, experiment_start(16, 4, 100, diff)])
    results = pd.concat([results, experiment_start(20, 4, 100, diff)])

    # Difficulty Level 2
    diff = '00'
    demochain = create_demo_chain(diff)
    results = pd.concat([results, experiment_start(2, 1, 100, diff)])
    results = pd.concat([results, experiment_start(4, 1, 100, diff)])
    results = pd.concat([results, experiment_start(8, 1, 100, diff)])
    results = pd.concat([results, experiment_start(16, 1, 100, diff)])
    results = pd.concat([results, experiment_start(20, 1, 100, diff)])
    results = pd.concat([results, experiment_start(3, 2, 100, diff)])
    results = pd.concat([results, experiment_start(4, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 2, 100, diff)])
    results = pd.concat([results, experiment_start(16, 2, 100, diff)])
    results = pd.concat([results, experiment_start(20, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 4, 100, diff)])
    results = pd.concat([results, experiment_start(16, 4, 100, diff)])
    results = pd.concat([results, experiment_start(20, 4, 100, diff)])

    # Difficulty Level 3
    diff = '000'
    demochain = create_demo_chain(diff)
    results = pd.concat([results, experiment_start(2, 1, 100, diff)])
    results = pd.concat([results, experiment_start(4, 1, 100, diff)])
    results = pd.concat([results, experiment_start(8, 1, 100, diff)])
    results = pd.concat([results, experiment_start(16, 1, 100, diff)])
    results = pd.concat([results, experiment_start(20, 1, 100, diff)])
    results = pd.concat([results, experiment_start(3, 2, 100, diff)])
    results = pd.concat([results, experiment_start(4, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 2, 100, diff)])
    results = pd.concat([results, experiment_start(16, 2, 100, diff)])
    results = pd.concat([results, experiment_start(20, 2, 100, diff)])
    results = pd.concat([results, experiment_start(8, 4, 100, diff)])
    results = pd.concat([results, experiment_start(16, 4, 100, diff)])
    results = pd.concat([results, experiment_start(20, 4, 100, diff)])

    # Record Results
    results.to_csv("eval_throughput.csv")
