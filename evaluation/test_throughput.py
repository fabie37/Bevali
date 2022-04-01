# Correct Module Referencing
import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from random import randrange
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


def create_demo_chain(diff='0', contracts=100):
    """
        Replicates 100 contracts with the same persimissions
    """
    demochain = Blockchain(target=diff)
    demochain.add_block(Block())
    code = import_code("contract.py")
    for x in range(0, contracts):
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
        sleep(8)
    return processes


def wait_for_x_connections(node, conns):
    prs = 0
    while prs < conns:
        with node.router.peerLock:
            # if prs != len(node.router.peerAddressToSocket):
            #     # print(
            #     # f"Node {node.port} connections:{len(node.router.peerAddressToSocket)}")
            prs = len(node.router.peerAddressToSocket)


def wait_for_chainlen(node, chainlength):
    length = 0
    while length < chainlength:
        length = len(node.blockchain.chain)
        sleep(0.1)


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


def run_node(ip, port, miner, peers, txs, queue, callbackQ, neighbours, chainlength):
    """
        Runs an instance of Bevali Blockchain
    """
    # Blockchain
    node = Bevali(ip, port)
    node.start()
    for neighbour in neighbours:
        node.connectToNode(BLOCKCHAIN_IP, neighbour)
    wait_for_x_connections(node, len(neighbours))
    wait_for_chainlen(node, chainlength)
    print(f"[Node {node.port}]  [connections:{len(node.router.peerAddressToSocket)}] [bc: {len(node.blockchain.chain)}]")
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
    print(f"Node {port} finished")

    # Wait for main process to tell you to stop
    while not getFromQueue(callbackQ, "close"):
        pass

    node.stop()


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


def experiment_start(num_peers, num_miners, num_contracts, num_tx, difficulty):
    """
        Sets up params for experiement & recording
    """
    print("Starting experiment...")
    qq = MQ()
    manager = Manager()
    callbackQ = manager.Queue()
    argus = []
    miners = num_miners

    # Set up arguments for nodes
    for p in range(1, num_peers):
        # Set miners
        miner = False
        mod = int(num_peers / miners)
        if (p - 1) % mod == 0:
            miner = True
        # if miners > 0:
        #     miner = True
        #     miners -= 1

        # Set neighbours
        if p > 1:
            neighbours = [WATCHERPORT + p - 1, WATCHERPORT + p - 2]
        if p <= 1:
            neighbours = [WATCHERPORT]

        arg = [
            BLOCKCHAIN_IP,
            WATCHERPORT + p,
            miner,
            num_peers,
            num_tx,
            qq,
            callbackQ,
            neighbours,
            len(demochain.chain)
        ]

        argus.append(arg)

    # Launch watcher
    watcher = setup_watcher_node()
    watcher.start()
    sleep(3)

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

    sleep(10)
    # Once all peers connected tell all peers to start
    for peer in range(1, num_peers):
        callbackQ.put("begin")

    # Start sending transactions
    for tx in range(num_tx, num_tx * 2):
        watcher.sendTransaction(create_demo_log(1, randrange(1, num_contracts- 1)))

    # Wait for all peers to finish collecting new blocks
    finished = 0
    while finished < num_peers - 1:
        if getFromQueue(callbackQ, "done"):
            finished += 1

    print("Experiment Finished...")

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

    cols = ["Peers", "Miners", "Contracts",
            "Transactions", "Time", "Difficulty"]
    data = []
    for t in times:
        data.append([
            num_peers,
            num_miners,
            num_contracts,
            num_tx,
            t,
            len(difficulty)
        ])

    results = pd.DataFrame(data, columns=cols)
    return results


if __name__ == '__main__':
    for i in range(0, 3):
        print("Experiment 5:")
        txs = 100
        # contracts_list = [500, 1000, 1500, 2000, 2500]
        contracts_list = [1500]
        diff_list = ['0']
        miner_list = [1, 2, 3, 4, 5, 6]
        peer_list = [6]
        output = "evaluation/experiment_5.csv"

        results = pd.DataFrame(
            columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
        for diff in diff_list:
            for contracts in contracts_list:
                for miners in miner_list:
                    for peers in peer_list:
                        demochain = create_demo_chain(diff, contracts)
                        results = pd.concat(
                            [results, experiment_start(peers, miners, contracts, txs, diff)])
                        results.to_csv(output, mode='a',
                                       header=not os.path.exists(output))
                        results = pd.DataFrame(
                            columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
                        sleep(1)

    # for i in range(0, 1):
    #     print("Experiment 3:")
    #     txs = 100
    #     contracts_list = [5000, 10000, 15000, 20000, 25000, 30000]
    #     diff_list = ['0']
    #     miner_list = [1]
    #     peer_list = [16]
    #     output = "evaluation/experiment_3.csv"

    #     results = pd.DataFrame(
    #         columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
    #     for diff in diff_list:
    #         for contracts in contracts_list:
    #             for miners in miner_list:
    #                 for peers in peer_list:
    #                     demochain = create_demo_chain(diff, contracts)
    #                     results = pd.concat(
    #                         [results, experiment_start(peers, miners, contracts, txs, diff)])
    #                     results.to_csv(output, mode='a',
    #                                    header=not os.path.exists(output))
    #                     results = pd.DataFrame(
    #                         columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])

        # print("Experiment 1:")
        # txs = 100
        # contracts_list = [100]
        # diff_list = ['0']
        # miner_list = [1]
        # peer_list = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        # output = "evaluation/experiment_1.csv"

        # results = pd.DataFrame(
        #     columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
        # for diff in diff_list:
        #     for contracts in contracts_list:
        #         for miners in miner_list:
        #             for peers in peer_list:
        #                 demochain = create_demo_chain(diff, contracts)
        #                 results = pd.concat(
        #                     [results, experiment_start(peers, miners, contracts, txs, diff)])
        #                 results.to_csv(output, mode='a',
        #                                header=not os.path.exists(output))
        #                 results = pd.DataFrame(
        #                     columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])

        # print("Experiment 2:")
        # txs = 100
        # contracts_list = [100]
        # diff_list = ['0']
        # miner_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        # peer_list = [16]
        # output = "evaluation/experiment_2.csv"

        # results = pd.DataFrame(
        #     columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
        # for diff in diff_list:
        #     for contracts in contracts_list:
        #         for miners in miner_list:
        #             for peers in peer_list:
        #                 demochain = create_demo_chain(diff, contracts)
        #                 results = pd.concat(
        #                     [results, experiment_start(peers, miners, contracts, txs, diff)])
        #                 results.to_csv(output, mode='a',
        #                                header=not os.path.exists(output))
        #                 results = pd.DataFrame(
        #                     columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])

    # txs = 100
    # contracts = 100
    # results = pd.DataFrame(
    #     columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
    # for diff in ['0']:
    #     demochain = create_demo_chain(diff, contracts)
    #     for miners in [1]:
    #         for peers in [2,4,6, 8, 10, 12, 14, 16, 18, 20]:
    #             results = pd.concat(
    #                 [results, experiment_start(peers, miners, contracts, txs, diff)])
    #             results.to_csv("evaluation/eval_throughput_new.csv", mode='a',
    #                            header=not os.path.exists("evaluation/eval_throughput_new.csv"))
    #             results = pd.DataFrame(
    #                 columns=["Peers", "Miners", "Contracts", "Transactions", "Time", "Difficulty"])
