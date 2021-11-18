"""
    This file contains tests for the class 'Server' contained within the 'Networking' module'
"""
from time import sleep
from math import log
from networking import Server

LOCAL_HOST = "127.0.0.1"
PORT_START = 1200

test_data = [
    "Test Message",
    {"Test": 0, "Test": 2}
]


def x_msg_sent_to_another_peer(x):
    peer1 = Server(LOCAL_HOST, PORT_START+0)
    peer2 = Server(LOCAL_HOST, PORT_START+1)
    peer1.start()
    peer2.start()
    for i in range(x):
        peer1.send(f"Test Message {i}", peer2.hostname, peer2.port)
    with peer2.rxSignal:
        while len(peer2.rxbuffer) < x:
            peer2.rxSignal.wait()
    msgs = peer2.rxbuffer
    peer1.stop()
    peer2.stop()

    return len(msgs)


def test_1_msg_sent_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 1x times
    """
    assert(x_msg_sent_to_another_peer(1) == 1)


def test_10_msg_sent_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 10x times
    """
    assert(x_msg_sent_to_another_peer(10) == 10)


def test_100_msg_sent_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 100x times
    """
    assert(x_msg_sent_to_another_peer(100) == 100)


def x_msg_to_broadcast_another_peer(x):
    peer1 = Server(LOCAL_HOST, PORT_START+0)
    peer2 = Server(LOCAL_HOST, PORT_START+1)
    peer1.start()
    peer2.start()
    peer2.send(f"Let's connect!", peer1.hostname, peer1.port)
    sleep(1)
    for i in range(x):
        peer1.send(f"Test Message {i}")
    with peer2.rxSignal:
        while len(peer2.rxbuffer) < x:
            peer2.rxSignal.wait()
    msgs = peer2.rxbuffer
    peer1.stop()
    peer2.stop()

    return len(msgs)


def test_1_msg_to_broadcast_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 1x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_another_peer(1) == 1)


def test_10_msg_to_broadcast_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 10x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_another_peer(10) == 10)


def test_100_msg_to_broadcast_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 100x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_another_peer(100) == 100)


def connect_x_peers_and_send_1_msg(x):
    peer_list = []
    for i in range(x):
        peer_list.append(Server(LOCAL_HOST, PORT_START+i))
        peer_list[i].start()

    for z in range(len(peer_list)-1):
        for peer in peer_list[z+1:]:
            peer_list[z].send("Let's connect", peer.hostname, peer.port)

    sleep(log(x)*2)

    for peer in peer_list:
        peer.clearRxBuffer()

    for peer in peer_list:
        peer.send("Message")

    sleep(log(x)*2)

    msgs = []
    for peer in peer_list:
        msgs = msgs + peer.rxbuffer

    for i in range(x):
        peer_list[i].stop()

    return len(msgs)


def test_connect_2_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(2) == 2*(2-1))


def test_connect_10_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(10) == 10*(10-1))


def test_connect_100_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(100) == 100*(100-1))
