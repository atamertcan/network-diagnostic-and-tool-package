import socket


#Connect to host:port, send an HTTP request and catch every possible error.
#Returns (True/False, message) instead of calling sys.exit() so the menu keeps running.
def check_connection(host, port, path="/", timeout=5):
    #create socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
    except socket.error as e:
        msg = "Error creating socket: %s" % e
        print(msg)
        return False, msg

    #connect to given host/port
    try:
        s.connect((host, port))
    except socket.gaierror as e:
        msg = "Address-related error connecting to server: %s" % e
        print(msg)
        s.close()
        return False, msg
    except socket.timeout:
        msg = "Connection timed out after %s seconds" % timeout
        print(msg)
        s.close()
        return False, msg
    except socket.error as e:
        msg = "Connection error: %s" % e
        print(msg)
        s.close()
        return False, msg

    #sending data
    try:
        s.sendall(("GET %s HTTP/1.0\r\n\r\n" % path).encode('utf-8'))
    except socket.error as e:
        msg = "Error sending data: %s" % e
        print(msg)
        s.close()
        return False, msg

    #waiting to receive data from remote host
    response = b""
    while True:
        try:
            buf = s.recv(2048)
        except socket.error as e:
            msg = "Error receiving data: %s" % e
            print(msg)
            s.close()
            return False, msg
        if not buf:
            break
        response += buf
    s.close()

    # Only the first line of the answer is shown
    first_line = response.decode('utf-8', errors='replace').split('\r\n')[0]
    msg = "Connected to %s:%s, server answered: %s" % (host, port, first_line)
    print(msg)
    return True, msg


if __name__ == '__main__':
    check_connection('www.python.org', 80)
