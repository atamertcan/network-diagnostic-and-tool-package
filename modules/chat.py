import select
import socket
import sys
import pickle
import struct
import threading
import os
import time

SERVER_HOST = 'localhost'

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


#Append one chat line with the time to txt
def save_chat(owner, text):
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "chat_%s.txt" % owner)
    with open(path, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), text))


#Send a message: first its size, then the pickled data
def send(channel, *args):
    buffer = pickle.dumps(args)
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)


#Receive one message sent with send()
def receive(channel):
    size_data = channel.recv(struct.calcsize("L"))
    try:
        size = socket.ntohl(struct.unpack("L", size_data)[0])
    except struct.error as e:
        return ''
    buf = b""
    while len(buf) < size:
        chunk = channel.recv(size - len(buf))
        if not chunk:  # connection closed in the middle of a message
            return ''
        buf += chunk
    return pickle.loads(buf)[0]

#chat server using select.
class ChatServer:
    def __init__(self, port, backlog=5):
        self.clients = 0
        self.clientmap = {}
        self.outputs = []  #list of output sockets
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Enable re-using socket address
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((SERVER_HOST, port))
        print("Server listening to port: {} ...".format(port))
        self.server.listen(backlog)

    #Close all sockets (called when the server stops)
    def close_all(self):
        print("Shutting down server...")
        for output in self.outputs:
            output.close()
        self.server.close()

    #Return the name of the client.
    def get_client_name(self, client):
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))

    #Show a message on the server screen and save it
    def show(self, msg):
        print(msg.strip())
        save_chat("server", msg.strip())

    def run(self):
        inputs = [self.server]
        self.outputs = []
        print("Press Ctrl+C to stop the server and return to the menu.")
        try:
            while True:
                #Only readable sockets are watched (client sockets are almost always writable,
                #watching them made select() return at once and use 100% CPU).
                #Timeout of 1 s so that Ctrl+C is noticed on Windows.
                try:
                    readable, writeable, exceptional = select.select(inputs, [], [], 1)
                except select.error as e:
                    break

                for sock in readable:
                    if sock == self.server:
                        #handle the server socket: new connection
                        client, address = self.server.accept()
                        print("Chat server: got connection {} from {}".format(client.fileno(), address))
                        #Read the login name
                        cname = receive(client).split('NAME: ')[1]
                        #Compute client name and send back
                        self.clients += 1
                        send(client, 'CLIENT: ' + str(address[0]))
                        inputs.append(client)
                        self.clientmap[client] = (address, cname)
                        #Send joining information to other clients
                        msg = "\n(Connected: New client ({}) from {})".format(self.clients, self.get_client_name(client))
                        self.show(msg)
                        for output in self.outputs:
                            send(output, msg)
                        self.outputs.append(client)
                    else:
                        #handle client sockets: incoming messages
                        try:
                            data = receive(sock)
                            if data:
                                # Broadcast the message to all other clients
                                msg = "\n#[{}]>>{}".format(self.get_client_name(sock), data)
                                self.show(msg)
                                for output in self.outputs:
                                    if output != sock:
                                        send(output, msg)
                            else:
                                # Client disconnected
                                print("Chat server: {} hung up".format(sock.fileno()))
                                self.clients -= 1
                                sock.close()
                                inputs.remove(sock)
                                if sock in self.outputs:
                                    self.outputs.remove(sock)
                                # Inform others of client departure
                                msg = "\n(Now hung up: Client from {})".format(self.get_client_name(sock))
                                self.show(msg)
                                for output in self.outputs:
                                    send(output, msg)
                        except socket.error as e:
                            # Remove socket on error
                            if sock in inputs:
                                inputs.remove(sock)
                            if sock in self.outputs:
                                self.outputs.remove(sock)
                            sock.close()
                            print("Socket error: {}".format(e))
        except KeyboardInterrupt:
            pass
        finally:
            self.close_all()


#command line chat client using a separate input thread.
class ChatClient:
    def __init__(self, name, port, host=SERVER_HOST):
        self.name = name
        self.connected = False
        self.host = host
        self.port = port
        self.prompt = '[' + '@'.join((name, socket.gethostname().split('.')[0])) + ']> '
        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, self.port))
            print("Now connected to chat server @ port {}".format(self.port))
            self.connected = True
            send(self.sock, 'NAME: ' + self.name)
            data = receive(self.sock)
            addr = data.split('CLIENT: ')[1]
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> '
        except socket.error as e:
            print("Failed to connect to chat server @ port {}: {}".format(self.port, e))

    #Chat client main loop using a separate input thread.
    def run(self):
        if not self.connected:
            return
        print("Type a message and press Enter. Type /quit to leave the chat.")

        def input_thread():
            # This thread handles user input from the console.
            while self.connected:
                line = sys.stdin.readline().strip()
                if not self.connected:  # server closed while we were waiting
                    break
                if line == '/quit':
                    self.connected = False
                    # wakes up recv() in the main thread so it can stop
                    self.sock.shutdown(socket.SHUT_RDWR)
                    break
                if line:
                    try:
                        send(self.sock, line)
                        save_chat(self.name, "[me]>>" + line)
                    except socket.error as e:
                        print("Could not send message: %s" % e)
                        break
                    sys.stdout.write(self.prompt)
                    sys.stdout.flush()

        # Start the input thread
        t = threading.Thread(target=input_thread, daemon=True)
        t.start()
        sys.stdout.write(self.prompt)
        sys.stdout.flush()

        try:
            # Main thread: receive messages from the server.
            while self.connected:
                data = receive(self.sock)
                if not data:
                    break
                # Print and save received messages
                print("\n" + data.strip())
                save_chat(self.name, data.strip())
                sys.stdout.write(self.prompt)
                sys.stdout.flush()
        except socket.error:
            pass  # recv() can fail after /quit closed the socket
        except KeyboardInterrupt:
            print("Client interrupted.")
        finally:
            if self.connected:
                # the server closed the connection, the input thread still waits for a line
                self.connected = False
                print("\nConnection closed by the server. Press Enter to return to the menu.")
            else:
                print("Leaving the chat.")
            self.sock.close()
            t.join()  # wait for the input thread so it does not steal the next menu input


#Start the chat in server mode
def run_chat_server(port=5000):
    try:
        server = ChatServer(port)
    except socket.error as e:
        print("Could not start chat server: %s" % e)
        return False
    server.run()
    return True


#Start the chat in client mode
def run_chat_client(name, port=5000, host=SERVER_HOST):
    client = ChatClient(name=name, port=port, host=host)
    if not client.connected:
        return False
    client.run()
    return True
