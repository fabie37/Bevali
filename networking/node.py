from p2pnetwork.node import Node
from time import sleep


class MyOwnPeer2PeerNode (Node):

    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(MyOwnPeer2PeerNode, self).__init__(
            host, port, id, callback, max_connections)
        print("MyPeer2PeerNode: Started")

    # all the methods below are called when things happen in the network.
    # implement your network node behavior to create the required functionality.

    def outbound_node_connected(self, node):
        print("outbound_node_connected (" + self.id + "): " + node.id)

    def inbound_node_connected(self, node):
        print("inbound_node_connected: (" + self.id + "): " + node.id)

    def inbound_node_disconnected(self, node):
        print("inbound_node_disconnected: (" + self.id + "): " + node.id)

    def outbound_node_disconnected(self, node):
        print("outbound_node_disconnected: (" + self.id + "): " + node.id)

    def node_message(self, node, data):
        print("node_message (" + self.id + ") from " + node.id + ": " + str(data))

    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" +
              self.id + "): " + node.id)

    def node_request_to_stop(self):
        print("node is requested to stop (" + self.id + "): ")


node1 = MyOwnPeer2PeerNode("127.0.0.1", 2001, 1)
node2 = MyOwnPeer2PeerNode("127.0.0.1", 2002, 2)
node3 = MyOwnPeer2PeerNode("127.0.0.1", 2003, 3)

sleep(1)

node1.start()
node2.start()
node3.start()

sleep(1)

node1.connect_with_node('127.0.0.1', 2002)
node2.connect_with_node('127.0.0.1', 2003)
# node3.connect_with_node('127.0.0.1', 2002)

sleep(1)

node1.send_to_nodes("Hello world!")

sleep(1)
print("Node 1 stopping")
node1.stop()

sleep(2)
print("Rest stopping")
node2.stop()
node3.stop()
