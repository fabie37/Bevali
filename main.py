from blockchain import Block
from networking import PeerRouter
from time import sleep

firstBlock = Block()
hash = firstBlock.generate_hash()
print(hash)

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 1234

# Start two routers
Peer_Bob = PeerRouter(LOCAL_HOST, LOCAL_PORT)
Peer_Alice = PeerRouter(LOCAL_HOST, LOCAL_PORT + 1)
Peer_Carol = PeerRouter(LOCAL_HOST, LOCAL_PORT + 2)

Peer_Bob.start()
Peer_Alice.start()
Peer_Carol.start()

# Connect bob to alice
Peer_Bob.connect(Peer_Alice.hostname, Peer_Alice.port)

# Make sure the connection happens
sleep(2)

# Carol asks bob for her client list
Peer_Carol.getPeers(Peer_Bob.hostname, Peer_Bob.port)

sleep(2)

# See if bob successfully connected to alice
if (len(Peer_Carol.peerAddressToSocket.items()) == 2):
    print("Carol got correct number of peers! :)")
else:
    print("Carol didn't get correct number of peers! :(")

# Stop both servers
some_random_input = input("Press Enter to stop threads")
Peer_Bob.stop()
Peer_Alice.stop()
Peer_Carol.stop()
some_random_input = input("Press Enter to check threads")
