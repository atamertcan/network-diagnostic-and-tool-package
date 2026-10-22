import socket

SEND_BUF_SIZE = 4096
RECV_BUF_SIZE = 2048


#Show the default socket timeout and change it
def test_socket_timeout(timeout=100):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Default socket timeout: %s" % s.gettimeout())
    s.settimeout(timeout)
    print("Current socket timeout: %s" % s.gettimeout())
    s.close()
    return s.gettimeout()


#Change the send/receive buffer sizes, returns the new sizes
def modify_buff_size(send_size=SEND_BUF_SIZE, recv_size=RECV_BUF_SIZE):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Get the size of the socket's send buffer
    sndbufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    print("Send Buffer size [Before]:%d" % sndbufsize)
    rcvbufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    print("Receive Buffer size [Before]:%d" % rcvbufsize)

    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_size)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_size)

    sndbufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    print("Send Buffer size [After]:%d" % sndbufsize)
    rcvbufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    print("Receive Buffer size [After]:%d" % rcvbufsize)
    sock.close()
    return sndbufsize, rcvbufsize


#Show the difference between blocking and non-blocking mode
def test_socket_modes():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(1)
    s.settimeout(0.5)
    s.bind(("127.0.0.1", 0))

    socket_address = s.getsockname()
    print("Trivial Server launched on socket: %s" % str(socket_address))
    s.listen(1)

    #Blocking mode: accept() waits for a client until the timeout runs out
    print("Blocking mode (timeout = %s s), calling accept()..." % s.gettimeout())
    try:
        s.accept()
    except socket.timeout:
        print("  accept() waited %s s, no client came -> socket.timeout" % s.gettimeout())

    #Non-blocking mode: accept() returns at once if no client is waiting
    s.setblocking(0)
    print("Non-blocking mode (timeout = %s), calling accept()..." % s.gettimeout())
    try:
        s.accept()
    except BlockingIOError:
        print("  accept() returned immediately, no client waiting -> BlockingIOError")
    s.close()


#Show the SO_REUSEADDR option before and after enabling it
def reuse_socket_addr():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Get the old state of the SO_REUSEADDR option
    old_state = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
    print("Old sock state: %s" % old_state)
    # Enable the SO_REUSEADDR option
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    new_state = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
    print("New sock state: %s" % new_state)
    sock.close()


#Run all settings tests, returns a short summary for the log
def run_socket_settings(timeout=100, send_size=SEND_BUF_SIZE, recv_size=RECV_BUF_SIZE):
    print("\n--- Socket timeout ---")
    new_timeout = test_socket_timeout(timeout)
    print("\n--- Buffer sizes ---")
    snd, rcv = modify_buff_size(send_size, recv_size)
    print("\n--- Blocking / non-blocking mode ---")
    test_socket_modes()
    print("\n--- SO_REUSEADDR ---")
    reuse_socket_addr()
    return "timeout=%s, send_buf=%d (asked %d), recv_buf=%d (asked %d)" % (
        new_timeout, snd, send_size, rcv, recv_size)


if __name__ == '__main__':
    print(run_socket_settings())
