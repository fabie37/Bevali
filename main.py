from networking import Server

server = Server("127.0.0.1", 1231)
server.start()
some_random_input = 0
while some_random_input != "stop":
    some_random_input = input("Press Enter to send data to connected client")
    server.send("From Test", "127.0.0.1", 1234)
some_random_input = input("Press Enter to stop threads")
server.stop()
some_random_input = input("Press Enter to check threads")
