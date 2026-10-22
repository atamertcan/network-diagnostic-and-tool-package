import socket
import struct
import time
from time import ctime
import ntplib

NTP_SERVER = "0.uk.pool.ntp.org"
TIME1970 = 2208988800

#Get the time from an SNTP server with a raw UDP socket.
def sntp_client(server=NTP_SERVER):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5)
    data = b'\x1b' + 47 * b'\0'
        # 0x1b: (Single Byte)
        # LI (Leap Indicator): 2 bits, usually set to 0 indicating no warning.
        # VN (Version Number): 3 bits, here indicating NTP version 3.
        # Mode: 3 bits, with the value 3 representing a client mode.
        # SNTP Request is total 48-bytes
    try:
        client.sendto(data, (server, 123)) #NTP server port is 123
        data, address = client.recvfrom(1024)
    except socket.gaierror as e:
        print("Could not resolve SNTP server %s: %s" % (server, e))
        return None
    except socket.timeout:
        print("No response from %s (timeout)" % server)
        return None
    except socket.error as e:
        print("Socket error: %s" % e)
        return None
    finally:
        client.close()
    if data:
        print('Response received from:', address)
    unpacked = struct.unpack('!12I', data) #'!' = network byte order, '12I' = 12 unsigned 4-byte ints
    t = unpacked[10] + unpacked[11] / 2**32 	#index 10 = transmit time, index 11 = fraction of a second
    t -= TIME1970
    print('\tTime=%s' % time.ctime(t))
    return t

#Get the time from an NTP server with the ntplib library.
def print_time(server=NTP_SERVER):
    ntp_client = ntplib.NTPClient()
    try:
        response = ntp_client.request(server)
    except (ntplib.NTPException, socket.error) as e:
        print("ntplib request failed: %s" % e)
        return None
    print(ctime(response.tx_time))
    return response.tx_time


#Compare the server time with the local system time
def compare_with_local(server_time):
    local_time = time.time()
    diff = local_time - server_time
    print("Server time : %s" % ctime(server_time))
    print("Local time  : %s" % ctime(local_time))
    print("Difference  : %+.3f seconds (local - server)" % diff)
    if abs(diff) < 1:
        print("Local clock is synchronized.")
    elif diff > 0:
        print("Local clock is %.3f seconds AHEAD." % diff)
    else:
        print("Local clock is %.3f seconds BEHIND." % -diff)
    return diff


#Entry point used by the main menu
def run_sntp_check(server=NTP_SERVER, use_ntplib=False):
    if use_ntplib:
        server_time = print_time(server)
    else:
        server_time = sntp_client(server)
    if server_time is None:
        print("SNTP check failed.")
        return None
    return compare_with_local(server_time)


if __name__ == '__main__':
    run_sntp_check()
