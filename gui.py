"""
Simple Tkinter GUI for the Network Diagnostic Tool.
Runs the same modules as main.py; everything they print is shown in the output box.
Run with: python gui.py
"""
import os
import sys
import queue
import subprocess
import threading
import tkinter as tk
import ttkbootstrap as ttk  # modern themes for ttk widgets (pip install ttkbootstrap)

from modules.machine_info import print_machine_info, get_remote_machine_info
from modules.echo_test import run_echo_test
from modules.sntp_time import run_sntp_check, NTP_SERVER
from modules.socket_settings import run_socket_settings
from modules.error_management import check_connection, check_echo_result
from modules.logger import log, sync_log_clock, LOG_DIR

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


#Sends everything written with print() to a queue, the GUI shows it in the output box
class QueueWriter:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        self.q.put(text)

    def flush(self):
        pass


class NetworkToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Diagnostic Tool")
        self.root.geometry("820x700")
        self.root.minsize(760, 600)
        self.busy = False
        self.output_queue = queue.Queue()
        sys.stdout = QueueWriter(self.output_queue)

        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

        ttk.Label(root, text="Network Diagnostic Tool", style="Title.TLabel", bootstyle="info").pack(anchor="w", padx=12, pady=(10, 4))

        form = ttk.Frame(root, padding=(12, 4))
        form.pack(fill="x")

        # 1 - Machine Information
        box = self.section(form, "1. Machine Information", 0)
        self.remote_host = self.field(box, "Remote host", "www.python.org", 0, 22)
        ttk.Button(box, text="Run", bootstyle="success", command=lambda: self.start(self.do_machine_info)).grid(row=0, column=2, padx=6)

        # 2 - Echo Test
        box = self.section(form, "2. Echo Test", 1)
        self.echo_port = self.field(box, "Port", "9900", 0, 8)
        self.echo_no_server = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="No server (test errors)", variable=self.echo_no_server,
                        bootstyle="warning-round-toggle").grid(row=0, column=2, padx=(10, 4))
        ttk.Button(box, text="Run", bootstyle="success", command=lambda: self.start(self.do_echo)).grid(row=0, column=3, padx=6)

        # 3 - SNTP
        box = self.section(form, "3. SNTP Time Check", 2)
        self.sntp_server = self.field(box, "Server", NTP_SERVER, 0, 22)
        ttk.Label(box, text="Method").grid(row=0, column=2, padx=(10, 4))
        self.sntp_method = ttk.Combobox(box, values=["raw socket", "ntplib"], width=10, state="readonly")
        self.sntp_method.current(0)
        self.sntp_method.grid(row=0, column=3)
        ttk.Button(box, text="Run", bootstyle="success", command=lambda: self.start(self.do_sntp)).grid(row=0, column=4, padx=6)

        # 4 - Socket Settings
        box = self.section(form, "4. Socket Settings", 3)
        self.timeout = self.field(box, "Timeout (s)", "100", 0, 6)
        ttk.Label(box, text="Send buf").grid(row=0, column=2, padx=(10, 4))
        self.send_buf = ttk.Entry(box, width=8)
        self.send_buf.insert(0, "4096")
        self.send_buf.grid(row=0, column=3)
        ttk.Label(box, text="Recv buf").grid(row=0, column=4, padx=(10, 4))
        self.recv_buf = ttk.Entry(box, width=8)
        self.recv_buf.insert(0, "2048")
        self.recv_buf.grid(row=0, column=5)
        ttk.Button(box, text="Run", bootstyle="success", command=lambda: self.start(self.do_settings)).grid(row=0, column=6, padx=6)

        # 5 - Chat (opens console windows, chat needs keyboard input)
        box = self.section(form, "5. Chat", 4)
        self.chat_name = self.field(box, "Name", "alice", 0, 10)
        ttk.Label(box, text="Port").grid(row=0, column=2, padx=(10, 4))
        self.chat_port = ttk.Entry(box, width=8)
        self.chat_port.insert(0, "5000")
        self.chat_port.grid(row=0, column=3)
        ttk.Button(box, text="Start server", bootstyle="info", command=self.do_chat_server).grid(row=0, column=4, padx=6)
        ttk.Button(box, text="Open client", bootstyle="info-outline", command=self.do_chat_client).grid(row=0, column=5)

        # 6 - Error Management
        box = self.section(form, "6. Error Management", 5)
        self.err_host = self.field(box, "Host", "www.python.org", 0, 22)
        ttk.Label(box, text="Port").grid(row=0, column=2, padx=(10, 4))
        self.err_port = ttk.Entry(box, width=8)
        self.err_port.insert(0, "80")
        self.err_port.grid(row=0, column=3)
        ttk.Button(box, text="Check", bootstyle="warning", command=lambda: self.start(self.do_error_check)).grid(row=0, column=4, padx=6)

        form.columnconfigure(0, weight=1)

        # Bottom bar (packed before the output box so it is never cut off)
        bottom = ttk.Frame(root, padding=12)
        bottom.pack(side="bottom", fill="x")
        self.status = ttk.Label(bottom, text="Ready")
        self.status.pack(side="left")
        ttk.Button(bottom, text="Open log folder", bootstyle="secondary", command=self.open_logs).pack(side="right")
        ttk.Button(bottom, text="Clear output", bootstyle="secondary", command=lambda: self.output.delete("1.0", "end")).pack(side="right", padx=6)

        # Output box
        out = ttk.Frame(root, padding=(12, 6, 12, 0))
        out.pack(fill="both", expand=True)
        self.output = tk.Text(out, wrap="word", font=("Consolas", 10), bg="#1b1f24", fg="#d4d4d4",
                              insertbackground="#d4d4d4", relief="flat", borderwidth=0, highlightthickness=0, padx=8, pady=6)
        scroll = ttk.Scrollbar(out, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_output()
        self.start(self.do_startup)

    #A labelled box for one module
    def section(self, parent, title, row):
        box = ttk.LabelFrame(parent, text=title, padding=(8, 2))
        box.grid(row=row, column=0, sticky="ew", pady=1)
        return box

    #A label + entry pair, returns the entry
    def field(self, parent, label, default, column, width):
        ttk.Label(parent, text=label).grid(row=0, column=column, padx=(0, 4))
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, default)
        entry.grid(row=0, column=column + 1)
        return entry

    #Read a whole number from an entry, use the default on wrong input
    def number(self, entry, default, low, high):
        text = entry.get().strip()
        try:
            value = int(text)
        except ValueError:
            print("'%s' is not a number, using %d." % (text, default))
            return default
        if value < low or value > high:
            print("Value must be between %d and %d, using %d." % (low, high, default))
            return default
        return value

    #Run a task in a background thread so the window does not freeze
    def start(self, task):
        if self.busy:
            print("\nPlease wait, another test is still running...")
            return
        self.busy = True
        self.status.config(text="Running...")

        def worker():
            try:
                task()
            except Exception as e:
                print("Unexpected error: %s" % e)
            finally:
                self.busy = False
                self.root.after(0, lambda: self.status.config(text="Ready"))

        threading.Thread(target=worker, daemon=True).start()

    #Move printed text from the queue to the output box (runs every 100 ms)
    def poll_output(self):
        while not self.output_queue.empty():
            self.output.insert("end", self.output_queue.get())
            self.output.see("end")
        self.root.after(100, self.poll_output)

    def header(self, title):
        print("\n" + "=" * 50 + "\n " + title + "\n" + "=" * 50)

    # ---- tasks (same steps as main.py) ----
    def do_startup(self):
        sync_log_clock()
        log("Main", "GUI started")

    def do_machine_info(self):
        self.header("MACHINE INFORMATION")
        info = print_machine_info()
        get_remote_machine_info(self.remote_host.get().strip() or "www.python.org")
        log("MachineInfo", "hostname=%s, ip=%s, %d interfaces"
            % (info["hostname"], info["ip"], len(info["interfaces"])))

    def do_echo(self):
        self.header("ECHO TEST")
        port = self.number(self.echo_port, 9900, 1, 65535)
        sent, received, error = run_echo_test(port, with_server=not self.echo_no_server.get())
        ok, msg = check_echo_result(port, sent, received, error)
        log("EchoTest" if ok else "ErrorMgmt", msg)

    def do_sntp(self):
        self.header("SNTP TIME CHECK")
        server = self.sntp_server.get().strip() or NTP_SERVER
        diff = run_sntp_check(server, use_ntplib=(self.sntp_method.get() == "ntplib"))
        if diff is None:
            log("SNTP", "%s: ERROR, no time received" % server)
        else:
            log("SNTP", "%s: local - server = %+.3f s" % (server, diff))

    def do_settings(self):
        self.header("SOCKET SETTINGS")
        timeout = self.number(self.timeout, 100, 1, 3600)
        send_size = self.number(self.send_buf, 4096, 1024, 1048576)
        recv_size = self.number(self.recv_buf, 2048, 1024, 1048576)
        log("Settings", run_socket_settings(timeout, send_size, recv_size))

    def do_error_check(self):
        self.header("ERROR MANAGEMENT")
        host = self.err_host.get().strip() or "www.python.org"
        port = self.number(self.err_port, 80, 1, 65535)
        ok, msg = check_connection(host, port)
        log("ErrorMgmt", msg)

    #Chat needs keyboard input, so it opens in its own console window
    def open_console(self, code, title):
        if os.name != "nt":
            print("\nChat windows open automatically only on Windows. Use: python main.py -> 5")
            return
        code += "; input('\\nPress Enter to close this window...')"
        subprocess.Popen([sys.executable, "-c", code], cwd=PROJECT_DIR,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("\n%s opened in a new window." % title)

    def do_chat_server(self):
        port = self.number(self.chat_port, 5000, 1, 65535)
        self.open_console("from modules.chat import run_chat_server; run_chat_server(%d)" % port,
                          "Chat server (port %d)" % port)
        log("Chat", "server window opened on port %d" % port)

    def do_chat_client(self):
        port = self.number(self.chat_port, 5000, 1, 65535)
        name = self.chat_name.get().strip() or "client"
        self.open_console("from modules.chat import run_chat_client; run_chat_client(%r, %d)" % (name, port),
                          "Chat client '%s'" % name)
        log("Chat", "client window opened for %s on port %d" % (name, port))

    def open_logs(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        if os.name == "nt":
            os.startfile(LOG_DIR)
        else:
            print("\nLog folder: %s" % LOG_DIR)

    def on_close(self):
        log("Main", "GUI closed")
        sys.stdout = sys.__stdout__
        self.root.destroy()


if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    NetworkToolGUI(root)
    root.mainloop()
