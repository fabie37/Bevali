from blockchain import Block
from networking import PeerRouter
from networking import Peer
from time import sleep

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 1234

Router = PeerRouter(LOCAL_HOST, LOCAL_PORT)
Router.start()

Router.connect("139.162.220.116", 1234)
sleep(2)
if Router.socketList > 1:
    print("Connected!")

while (1):
    msg = input("Send something to server:")
    Router.broadcast(msg)
