import socket
import psutil


#Listing network interfaces. Return {interface_name: [IPv4 addresses]}.
def get_interfaces():
    interfaces = {}
    for name, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family == socket.AF_INET]
        interfaces[name] = ips
    return interfaces


#Get IP address of a remote host
def get_remote_machine_info(remote_host='www.python.org'):
    try:
        print("IP address of %s: %s" % (remote_host, socket.gethostbyname(remote_host)))
    except socket.error as err_msg:
        print("%s: %s" % (remote_host, err_msg))


#Print local machine info and return it as a dict.
def print_machine_info():
    host_name = socket.gethostname()
    try:
        ip_address = socket.gethostbyname(host_name)
    except socket.gaierror as e:
        print("Address related error: %s" % e)
        ip_address = "unknown"
    interfaces = get_interfaces()

    print("Host name: %s" % host_name)
    print("IP address: %s" % ip_address)
    print("Network interfaces:")
    for name, ips in interfaces.items():
        print("  %-25s %s" % (name, ", ".join(ips) or "(no IPv4)"))

    return {"hostname": host_name, "ip": ip_address, "interfaces": interfaces}


if __name__ == '__main__':
    print_machine_info()
    get_remote_machine_info()
