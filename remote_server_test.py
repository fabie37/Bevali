from networking import PeerRouter

LOCAL_HOST = "139.162.220.116"
LOCAL_PORT = 1234

Router = PeerRouter(LOCAL_HOST, LOCAL_PORT)
Router.start()

while (1):
    data = Router.databuffer.get(block=True)
    Router.broadcast("Got your message!")
    print(data)
