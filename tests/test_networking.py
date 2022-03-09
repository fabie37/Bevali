"""
    This file contains tests for the class 'Server' contained within the 'Networking' module'
"""
from time import sleep
from math import log
from networking import PeerRouter

LOCAL_HOST = "127.0.0.1"
PORT_START = 1200


def connect_x_peers_together(x, delay=3):
    peer_list = []
    for i in range(x):
        peer_list.append(PeerRouter(LOCAL_HOST, PORT_START + i))
        peer_list[i].start()

    for z in range(x - 1):
        for peer in peer_list[z + 1:]:
            peer_list[z].connect(peer.hostname, peer.port)

    sleep(log(x) * delay)

    connected_peers_per_peer = []
    for peer in peer_list:
        connected_peers_per_peer.append(len(peer.peerAddressToSocket.items()))

    for i in range(x):
        peer_list[i].stop()

    return sum(connected_peers_per_peer)


def test_connect_2_peers():
    assert(connect_x_peers_together(2) == 2 * (2 - 1))


def test_connect_3_peers():
    assert(connect_x_peers_together(3) == 3 * (3 - 1))


def test_connect_10_peers():
    assert(connect_x_peers_together(10) == 10 * (10 - 1))


def test_connect_100_peers():
    assert(connect_x_peers_together(100, delay=5) == 100 * (100 - 1))


def get_x_peers_from_peer(x):
    peerList = []
    for i in range(0, x):
        peerList.append(PeerRouter(LOCAL_HOST, PORT_START + i))
        peerList[i].start()

    # Connect first peer to all other peers
    for i in range(1, x - 1):
        peerList[0].connect(peerList[i].hostname, peerList[i].port)

    # Wait for this to happen
    sleep(log(x) * 2)

    # Ask final peer to get the peer list from first peer
    peerList[-1].getPeers(peerList[0].hostname, peerList[0].port)

    # Wait for this to happen
    sleep(log(x) * 2)

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
    peer1 = PeerRouter(LOCAL_HOST, PORT_START + 0)
    peer2 = PeerRouter(LOCAL_HOST, PORT_START + 1)
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
    peer1 = PeerRouter(LOCAL_HOST, PORT_START + 0)
    peer2 = PeerRouter(LOCAL_HOST, PORT_START + 1)
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
        peer_list.append(PeerRouter(LOCAL_HOST, PORT_START + i))
        peer_list[i].start()

    # Let all peers connect to node peer
    for peer in peer_list[1:]:
        peer.getPeers(node.hostname, node.port)
        sleep(1)

    # Wait for this to happen
    sleep(log(x) * 2)

    # Get each node to broadcast a message
    for peer in peer_list:
        peer.broadcast("Test Message")

    # Wait for this to happen
    sleep(log(x) * 2)

    msgs = []

    for peer in peer_list:
        while peer.databuffer.qsize() != 0:
            msgs.append(peer.databuffer.get())
        peer.stop()

    return len(msgs)


def summation_i(i):
    return (i**2 + i) / 2


def test_connect_2_peers_and_send_1_msg():
    result = 2 * (2 - 1)
    assert(connect_x_peers_and_send_1_msg(2) == result)


def test_connect_3_peers_and_send_1_msg():
    result = 3 * (3 - 1)
    assert(connect_x_peers_and_send_1_msg(3) == result)


def test_connect_10_peers_and_send_1_msg():
    result = 10 * (10 - 1)
    assert(connect_x_peers_and_send_1_msg(10) == result)


def test_connect_100_peers_and_send_1_msg():
    result = 100 * (100 - 1)
    assert(connect_x_peers_and_send_1_msg(100) == result)


def test_blocking_on_connect():
    """
        This tests if the basic blocking function works when connecting between 2 peers
    """
    bob = PeerRouter(LOCAL_HOST, PORT_START)
    alice = PeerRouter(LOCAL_HOST, PORT_START + 1)

    bob.start()
    alice.start()

    bob.connect(alice.hostname, alice.port, True)

    tally = 0
    for i in range(0, 10):
        tally += 1

    bob.stop()
    alice.stop()
    assert(tally == 10)


def test_remote_code_execution():
    """
        Basic Test to see if remote peer will execute code as a string
    """
    def sub(a):
        return a - 1
    code = "def add(a,b):\n\treturn a+b\na = 5\nb = 5\nrtn = add(sub(a),b)"

    bob = PeerRouter(LOCAL_HOST, PORT_START)
    alice = PeerRouter(LOCAL_HOST, PORT_START + 1)

    bob.start()
    alice.start()

    bob.connect(alice.hostname, alice.port, block=True)
    bob.broadcast(code)
    sleep(1)
    data = alice.databuffer.get()

    code_locals = {}

    exec(data[1], {"sub": sub}, code_locals)

    # Globals: things we put into exec
    # Locals:  things we get from exec

    bob.stop()
    alice.stop()
    assert(code_locals['rtn'] == 9)


def test_message_routing():
    """
        Basic connect to 3 peers and see if they all get the same message
    """

    alice = PeerRouter(LOCAL_HOST, PORT_START, mesh=False)
    bob = PeerRouter(LOCAL_HOST, PORT_START + 1, mesh=False)
    carol = PeerRouter(LOCAL_HOST, PORT_START + 2, mesh=False)

    alice.start()
    bob.start()
    carol.start()

    sleep(1)

    alice.connect(bob.hostname, bob.port)
    bob.connect(carol.hostname, carol.port)
    sleep(1)

    alice.broadcast("Hello!")

    sleep(5)
    messages = 0
    messages += bob.databuffer.qsize()
    messages += carol.databuffer.qsize()
    alice.stop()
    bob.stop()
    carol.stop()
    assert(messages == 2)


def test_message_routing_3_cycle():
    """
        Tests that a cycle doesn't send data more than once to same peer
    """

    alice = PeerRouter(LOCAL_HOST, PORT_START, mesh=False)
    bob = PeerRouter(LOCAL_HOST, PORT_START + 1, mesh=False)
    carol = PeerRouter(LOCAL_HOST, PORT_START + 2, mesh=False)

    alice.start()
    bob.start()
    carol.start()

    sleep(3)
    alice.connect(bob.hostname, bob.port)
    sleep(0.5)
    bob.connect(carol.hostname, carol.port)
    sleep(0.5)
    carol.connect(alice.hostname, alice.port)
    sleep(3)

    alice.broadcast("Hello!")

    sleep(10)
    messages = 0
    messages += bob.databuffer.qsize()
    messages += carol.databuffer.qsize()
    messages += alice.databuffer.qsize()
    alice.stop()
    bob.stop()
    carol.stop()
    assert(messages == 2)


def connect_together(host, peerList, indexList):
    for peer in [peerList[i] for i in indexList]:
        host.connect(peer.hostname, peer.port)
        sleep(2)


def stop(peerList):
    for peer in peerList:
        peer.stop()


def test_message_routing_complex_cycle():
    """
        Tests a graph that is more involved
    """
    peers = []
    for i in range(9):
        router = PeerRouter(LOCAL_HOST, PORT_START + i, mesh=False)
        peers.append(router)
        router.start()

    sleep(3)

    connect_together(peers[0], peers, [1, 2])
    connect_together(peers[1], peers, [5, 4])
    connect_together(peers[2], peers, [6, 7, 3])
    connect_together(peers[3], peers, [5, 4])
    connect_together(peers[4], peers, [5])
    connect_together(peers[6], peers, [7])
    connect_together(peers[7], peers, [8])
    sleep(5)

    peers[0].broadcast("0")
    sleep(1)
    peers[5].broadcast("5")
    sleep(1)
    peers[8].broadcast("8")
    sleep(1)

    sleep(20)
    messages = {"0": 0, "5": 0, "8": 0}

    for peer in peers:
        while peer.databuffer.qsize() != 0:
            msg = peer.databuffer.get()[1]
            messages[msg] += 1

    stop(peers)
    assert(messages["0"] == 8 and messages["5"] == 8 and messages["8"] == 8)


def test_connect_x_no_mesh():
    x = 100
    peers = []
    for i in range(x):
        router = PeerRouter(LOCAL_HOST, PORT_START + i, mesh=False)
        peers.append(router)
        router.start()

    for index, peer in enumerate(peers[1:]):
        peers[index].connect(peer.hostname, peer.port)

    sleep(20)

    connections = []
    for peer in peers:
        connections.append(len(peer.peerAddressToSocket))

    stop(peers)

    assert(sum(connections) == ((x - 2) * 2) + 2)
