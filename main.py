from modules.machine_info import print_machine_info, get_remote_machine_info
from modules.echo_test import run_echo_test
from modules.sntp_time import run_sntp_check, NTP_SERVER
from modules.socket_settings import run_socket_settings
from modules.error_management import check_connection, check_echo_result
from modules.chat import run_chat_server, run_chat_client
from modules.logger import log, sync_log_clock, LOG_FILE


def show_menu():
    print("\n" + "=" * 40)
    print(" NETWORK DIAGNOSTIC TOOL")
    print("=" * 40)
    print("1. Machine Information")
    print("2. Echo Test")
    print("3. SNTP Time Check")
    print("4. Socket Settings")
    print("5. Chat")
    print("6. Error Management")
    print("0. Exit")


#Ask for a whole number, use the default on Enter or on wrong input
def ask_number(text, default, low, high):
    answer = input("%s (Enter = %d): " % (text, default)).strip()
    if not answer:
        return default
    try:
        value = int(answer)
    except ValueError:
        print("'%s' is not a number, using %d." % (answer, default))
        return default
    if value < low or value > high:
        print("Value must be between %d and %d, using %d." % (low, high, default))
        return default
    return value


def main():
    sync_log_clock()
    log("Main", "Program started")
    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == "1":
            info = print_machine_info()
            host = input("\nRemote host to resolve (Enter = www.python.org): ").strip()
            get_remote_machine_info(host or "www.python.org")
            log("MachineInfo", "hostname=%s, ip=%s, %d interfaces"
                % (info["hostname"], info["ip"], len(info["interfaces"])))
        elif choice == "2":
            port = ask_number("Port", 9900, 1, 65535)
            server = input("Start the local echo server? (Enter = yes, n = no, to test errors): ").strip().lower()
            sent, received, error = run_echo_test(port, with_server=(server != "n"))
            ok, msg = check_echo_result(port, sent, received, error)
            log("EchoTest" if ok else "ErrorMgmt", msg)
        elif choice == "3":
            server = input("SNTP server (Enter = %s): " % NTP_SERVER).strip() or NTP_SERVER
            method = input("Method - 1) raw socket  2) ntplib (Enter = 1): ").strip()
            diff = run_sntp_check(server, use_ntplib=(method == "2"))
            if diff is None:
                log("SNTP", "%s: ERROR, no time received" % server)
            else:
                log("SNTP", "%s: local - server = %+.3f s" % (server, diff))
        elif choice == "4":
            timeout = ask_number("Socket timeout in seconds", 100, 1, 3600)
            send_size = ask_number("Send buffer size", 4096, 1024, 1048576)
            recv_size = ask_number("Receive buffer size", 2048, 1024, 1048576)
            summary = run_socket_settings(timeout, send_size, recv_size)
            log("Settings", summary)
        elif choice == "5":
            mode = input("Mode - s) server  c) client: ").strip().lower()
            if mode == "s":
                port = ask_number("Port", 5000, 1, 65535)
                log("Chat", "server started on port %d" % port)
                if run_chat_server(port):
                    log("Chat", "server on port %d stopped" % port)
                else:
                    log("Chat", "ERROR, server could not start on port %d" % port)
            elif mode == "c":
                name = input("Your name: ").strip() or "client"
                port = ask_number("Port", 5000, 1, 65535)
                if run_chat_client(name, port):
                    log("Chat", "%s left the chat on port %d" % (name, port))
                else:
                    log("Chat", "ERROR, %s could not connect to port %d" % (name, port))
            else:
                print("Invalid mode, choose 's' or 'c'.")
        elif choice == "6":
            host = input("Host to check (Enter = www.python.org): ").strip() or "www.python.org"
            port = ask_number("Port", 80, 1, 65535)
            ok, msg = check_connection(host, port)
            log("ErrorMgmt", msg)
        elif choice == "0":
            log("Main", "Program closed")
            print("Bye! Log file: %s" % LOG_FILE)
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Main", "Program closed with Ctrl+C")
        print("\nBye!")
