from networking import PeerRouter
from networking import Peer
from time import sleep


client_list = [
    {"id": 1, "ip": "127.0.0.1", "port": 1200},
    {"id": 2, "ip": "127.0.0.1", "port": 1201},
]

peer_list = []
for client in client_list:
    peer = Peer(client["id"], client["ip"], client["port"])


server = PeerRouter("192.168.1.122", 1231)
server2 = PeerRouter("127.0.0.1", 1231)
server.start()
server2.start()
some_random_input = 0
while some_random_input != "stop":
    some_random_input = input("Press Enter to send data to connected client")
    server2.send("From Server 2", "192.168.1.122", 1231)
    sleep(1)
    print(f"Server 1: {server.rxbuffer}")
    print(f"Server 2: {server2.rxbuffer}")
    server.send("From Server 1")
    sleep(1)
    print(f"Server 1: {server.rxbuffer}")
    print(f"Server 2: {server2.rxbuffer}")
some_random_input = input("Press Enter to stop threads")
server.stop()
some_random_input = input("Press Enter to check threads")
