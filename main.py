"""
CEN322 - Network Programming, Project 01
Network Diagnostic and Tool Package - main menu

[EKLENDI] The whole file is new: the project asks for one menu
that calls each module.
"""
from modules.machine_info import print_machine_info, get_remote_machine_info
from modules.echo_test import run_echo_test


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


def main():
    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == "1":
            print_machine_info()
            host = input("\nRemote host to resolve (Enter = www.python.org): ").strip()
            get_remote_machine_info(host or "www.python.org")
        elif choice == "2":
            port = input("Port (Enter = 9900): ").strip()
            run_echo_test(int(port) if port else 9900)
        elif choice in ("3", "4", "5", "6"):
            print("Not implemented yet.")
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
