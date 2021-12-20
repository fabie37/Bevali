
from pickle import FALSE
from datahandler import DataHandler, BlockSink, BlockChainSink
from networking import PeerRouter
from blockchain import Block
from blockchain import Blockchain
from time import sleep
from math import log

LOCAL_HOST = "127.0.0.1"
PORT_START = 1200

data_sinks = {
    Block: BlockSink,
    Blockchain: BlockChainSink
}


def get_data_from_a_peer(data):

    bob_router = PeerRouter(LOCAL_HOST, PORT_START)
    carol_router = PeerRouter(LOCAL_HOST, PORT_START+1)
    carol_handler = DataHandler(carol_router.databuffer)

    carol_data_sink = []
    dataSink = data_sinks[type(data)](carol_data_sink)

    carol_handler.addDataSink(dataSink)

    bob_router.start()
    carol_router.start()
    carol_handler.start()

    bob_router.connect(carol_router.hostname, carol_router.port)
    sleep(1)
    bob_router.broadcast(data)
    sleep(1)

    result = False
    if len(carol_data_sink) > 0:
        result = True

    bob_router.stop()
    carol_router.stop()
    carol_handler.stop()

    return result


def test_get_block_from_a_peer():
    data = Block()
    assert(get_data_from_a_peer(data))


def test_get_blockchain_from_a_peer():
    data = Blockchain()
    assert(get_data_from_a_peer(data))
