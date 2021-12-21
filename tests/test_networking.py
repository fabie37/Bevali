"""
    This file contains tests for the class 'Server' contained within the 'Networking' module'
"""
from time import sleep
from math import log
from networking import PeerRouter

LOCAL_HOST = "127.0.0.1"
PORT_START = 1200


def connect_x_peers_together(x):
    peer_list = []
    for i in range(x):
        peer_list.append(PeerRouter(LOCAL_HOST, PORT_START+i))
        peer_list[i].start()

    for z in range(x-1):
        for peer in peer_list[z+1:]:
            peer_list[z].connect(peer.hostname, peer.port)

    sleep(log(x)*2)

    connected_peers_per_peer = []
    for peer in peer_list:
        connected_peers_per_peer.append(len(peer.peerAddressToSocket.items()))

    for i in range(x):
        peer_list[i].stop()

    return sum(connected_peers_per_peer)


def test_connect_2_peers():
    assert(connect_x_peers_together(2) == 2*(2-1))


def test_connect_3_peers():
    assert(connect_x_peers_together(3) == 3*(3-1))


def test_connect_10_peers():
    assert(connect_x_peers_together(10) == 10*(10-1))


def test_connect_100_peers():
    assert(connect_x_peers_together(100) == 100*(100-1))


def get_x_peers_from_peer(x):
    peerList = []
    for i in range(0, x):
        peerList.append(PeerRouter(LOCAL_HOST, PORT_START+i))
        peerList[i].start()

    # Connect first peer to all other peers
    for i in range(1, x-1):
        peerList[0].connect(peerList[i].hostname, peerList[i].port)

    # Wait for this to happen
    sleep(log(x)*2)

    # Ask final peer to get the peer list from first peer
    peerList[-1].getPeers(peerList[0].hostname, peerList[0].port)

    # Wait for this to happen
    sleep(log(x)*2)

    totalPeers = len(peerList[-1].peerAddressToSocket.items())

    # Stop all peers
    for i in range(0, x):
        peerList[i].stop()

    # Now the final peer should be connected to every other peer
    return totalPeers


def test_get_10_peers_from_peer():
    assert(get_x_peers_from_peer(10) == 9)


def test_get_50_peers_from_peer():
    assert(get_x_peers_from_peer(50) == 49)


def x_msg_sent_to_another_peer(x):
    peer1 = PeerRouter(LOCAL_HOST, PORT_START+0)
    peer2 = PeerRouter(LOCAL_HOST, PORT_START+1)
    peer1.start()
    peer2.start()
    for i in range(x):
        peer1.send(peer2.hostname, peer2.port, f"Test Message {i}", )
    with peer2.threadManager.getThreadSignal("Message Thread"):
        while peer2.databuffer.qsize() < x:
            peer2.threadManager.getThreadSignal("Message Thread").wait()
    data = []
    while peer2.databuffer.qsize() != 0:
        data.append(peer2.databuffer.get())
    peer1.stop()
    peer2.stop()

    return len(data)


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


def x_msg_to_broadcast_to_another_peer(x):
    peer1 = PeerRouter(LOCAL_HOST, PORT_START+0)
    peer2 = PeerRouter(LOCAL_HOST, PORT_START+1)
    peer1.start()
    peer2.start()
    peer2.connect(peer1.hostname, peer1.port)
    sleep(1)
    for i in range(x):
        peer1.broadcast(f"Test Message {i}")
    with peer2.threadManager.getThreadSignal("Message Thread"):
        while peer2.databuffer.qsize() < x:
            peer2.threadManager.getThreadSignal("Message Thread").wait()
    data = []
    while peer2.databuffer.qsize() != 0:
        data.append(peer2.databuffer.get())
    peer1.stop()
    peer2.stop()
    return len(data)


def test_1_msg_to_broadcast_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 1x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_to_another_peer(1) == 1)


def test_10_msg_to_broadcast_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 10x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_to_another_peer(10) == 10)


def test_100_msg_to_broadcast_to_another_peer():
    """
        This test is between 2 peers. 1 Peer will try to send a test to another 100x times via broacast to his client list
    """
    assert(x_msg_to_broadcast_to_another_peer(100) == 100)


def connect_x_peers_and_send_1_msg(x):
    peer_list = []
    node = PeerRouter(LOCAL_HOST, PORT_START)
    node.start()
    peer_list.append(node)
    for i in range(1, x):
        peer_list.append(PeerRouter(LOCAL_HOST, PORT_START+i))
        peer_list[i].start()

    # Let all peers connect to node peer
    for peer in peer_list[1:]:
        peer.getPeers(node.hostname, node.port)
        sleep(1)

    # Wait for this to happen
    sleep(log(x)*2)

    # Get each node to broadcast a message
    for peer in peer_list:
        peer.broadcast("Test Message")

    # Wait for this to happen
    sleep(log(x)*2)

    msgs = []

    for peer in peer_list:
        while peer.databuffer.qsize() != 0:
            msgs.append(peer.databuffer.get())
        peer.stop()

    return len(msgs)


def test_connect_2_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(2) == 2*(2-1))


def test_connect_3_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(3) == 3*(3-1))


def test_connect_10_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(10) == 10*(10-1))


def test_connect_100_peers_and_send_1_msg():
    assert(connect_x_peers_and_send_1_msg(100) == 100*(100-1))


def test_blocking_on_connect():
    """
        This tests if the basic blocking function works when connecting between 2 peers
    """
    bob = PeerRouter(LOCAL_HOST, PORT_START)
    alice = PeerRouter(LOCAL_HOST, PORT_START+1)

    bob.start()
    alice.start()

    bob.connect(alice.hostname, alice.port, True)

    tally = 0
    for i in range(0, 10):
        tally += 1

    bob.stop()
    alice.stop()
    assert(tally == 10)
