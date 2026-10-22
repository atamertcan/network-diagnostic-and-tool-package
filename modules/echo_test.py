import socket
import threading
import time

host = 'localhost'
data_payload = 2048
backlog = 5

#simple echo server.
#Echo test, so it must close after one client to free the port for the next test.
def echo_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (host, port)
    print("Starting up echo server on %s port %s" % server_address)
    try:
        sock.bind(server_address)
        sock.listen(backlog)
    except socket.error as e:
        print("Echo server could not start: %s" % e)
        sock.close()
        return
    print("Waiting to receive message from client")
    client, address = sock.accept()
    data = client.recv(data_payload)
    if data:
        print("Data: %s" % data)
        client.send(data)
        print("sent %s bytes back to %s" % (data, address))
    client.close()
    sock.close()

#simple echo client, returns the received text
def echo_client(port, message="Test message. This will be echoed"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    print("Connecting to %s port %s" % server_address)
    sock.settimeout(5)  # do not wait forever if the server never answers
    received = b""
    error = None  # the error is returned so the Error Management module can explain it
    try:
        sock.connect(server_address)
        print("Sending %s" % message)
        sock.sendall(message.encode('utf-8'))
        amount_received = 0
        amount_expected = len(message.encode('utf-8'))
        while amount_received < amount_expected:
            data = sock.recv(16)
            if not data:
                break
            amount_received += len(data)
            received += data
            print("Received: %s" % data)
    except socket.error as e:
        print("Socket error: %s" % str(e))
        error = e
    except Exception as e:
        print("Other exception: %s" % str(e))
        error = e
    finally:
        print("Closing connection to the server")
        sock.close()
    return received.decode('utf-8', errors='replace'), error


#Runs server + client together and compares the data
#with_server=False skips the local server, used to test the error handling
#Returns (sent, received, error) so the result can be checked by the Error Management module
def run_echo_test(port=9900, message="Test message. This will be echoed", with_server=True):
    if with_server:
        server_thread = threading.Thread(target=echo_server, args=(port,))
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.5)

    received, error = echo_client(port, message)

    if received == message:
        print("Connection successful, data matches")
    else:
        print("Echo test failed: sent %r, received %r" % (message, received))
    return message, received, error


if __name__ == '__main__':
    run_echo_test()
