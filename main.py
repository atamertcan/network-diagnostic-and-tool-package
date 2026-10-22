from modules.machine_info import print_machine_info, get_remote_machine_info
from modules.echo_test import run_echo_test
from modules.sntp_time import run_sntp_check, NTP_SERVER
from modules.socket_settings import run_socket_settings
from modules.error_management import check_connection
from modules.chat import run_chat_server, run_chat_client


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
    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == "1":
            print_machine_info()
            host = input("\nRemote host to resolve (Enter = www.python.org): ").strip()
            get_remote_machine_info(host or "www.python.org")
        elif choice == "2":
            port = ask_number("Port", 9900, 1, 65535)
            run_echo_test(port)
        elif choice == "3":
            server = input("SNTP server (Enter = %s): " % NTP_SERVER).strip()
            method = input("Method - 1) raw socket  2) ntplib (Enter = 1): ").strip()
            run_sntp_check(server or NTP_SERVER, use_ntplib=(method == "2"))
        elif choice == "4":
            timeout = ask_number("Socket timeout in seconds", 100, 1, 3600)
            send_size = ask_number("Send buffer size", 4096, 1024, 1048576)
            recv_size = ask_number("Receive buffer size", 2048, 1024, 1048576)
            run_socket_settings(timeout, send_size, recv_size)
        elif choice == "5":
            mode = input("Mode - s) server  c) client: ").strip().lower()
            if mode == "s":
                port = ask_number("Port", 5000, 1, 65535)
                run_chat_server(port)
            elif mode == "c":
                name = input("Your name: ").strip() or "client"
                port = ask_number("Port", 5000, 1, 65535)
                run_chat_client(name, port)
            else:
                print("Invalid mode, choose 's' or 'c'.")
        elif choice == "6":
            host = input("Host to check (Enter = www.python.org): ").strip() or "www.python.org"
            port = ask_number("Port", 80, 1, 65535)
            check_connection(host, port)
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
