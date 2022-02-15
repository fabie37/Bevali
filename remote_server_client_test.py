from networking.peer_router import PeerRouter
from time import sleep

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 1234

Router = PeerRouter(LOCAL_HOST, LOCAL_PORT)
Router.start()

Router.connect("139.162.220.116", 1234)
sleep(3)
if len(Router.socketList) > 1:
    print("Connected!")
    Router.getPeerList("139.162.220.116", 1234)

while (1):
    msg = input("Send something to server:")
    if msg.startswith("stop"):
        Router.stop()
        break
    Router.broadcast(msg)
    try:
        while not Router.databuffer.empty():
            msg = Router.databuffer.get()
            print(msg)
    except Exception:
        continue

print("Stopped")
