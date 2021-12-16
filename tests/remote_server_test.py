from blockchain import Block
from networking import PeerRouter
from networking import Peer
from time import sleep

LOCAL_HOST = "139.162.220.116"
LOCAL_PORT = 1234

Router = PeerRouter(LOCAL_HOST, LOCAL_PORT)
Router.start()

while (1):
    data = Router.databuffer.get(block=True)
    print(data)
