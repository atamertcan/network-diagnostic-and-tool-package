# Network Diagnostic and Tool Package

CEN322 – Network Programming, Project 01
Çukurova University, Computer Engineering

- **Student:** Atamert Can
- **Student ID:** _________

A Python tool that combines socket programming, network diagnostics, time
synchronization, chat and error handling. It can be used from a terminal menu
(`main.py`) or from a simple graphical interface (`gui.py`).

## Features

| # | Module | What it does |
|---|---|---|
| 1 | Machine Information | Hostname, primary IP address, all network interfaces with their IPv4 addresses, IP lookup of a remote host |
| 2 | Echo Test | Starts a TCP echo server in a background thread, connects a client, compares sent and received data |
| 3 | SNTP Time Check | Gets the time from an SNTP server (raw UDP socket or `ntplib`) and compares it with the local clock |
| 4 | Socket Settings | Changes the socket timeout and send/receive buffer sizes, shows blocking vs non-blocking mode and `SO_REUSEADDR` |
| 5 | Chat | Multi-client chat in server or client mode, messages are saved to files |
| 6 | Error Management | Connects to a host and catches socket, address, connection, timeout, send and receive errors with clear messages |

**Integration**
- At start-up the SNTP module is used once to get the correct time; every log timestamp (main log and chat logs) is corrected with it.
- Every module writes its result or its error to `logs/network_tool.log`, so the log also works as a test report.
- Wrong user input (letters instead of numbers, ports outside 1–65535) is caught and the default value is used.

## Project Structure

```
cen322_project/
├── main.py                    # terminal menu
├── gui.py                     # graphical interface (Tkinter + ttkbootstrap)
├── requirements.txt
├── README.md
├── modules/
│   ├── machine_info.py        # A - Machine Information
│   ├── echo_test.py           # B - Echo Test
│   ├── sntp_time.py           # C - SNTP Time Synchronization
│   ├── chat.py                # D - Chat
│   ├── socket_settings.py     # E - Socket Settings
│   ├── error_management.py    # E - Error Management
│   └── logger.py              # log file with SNTP based timestamps
├── logs/                      # created automatically
│   ├── network_tool.log
│   └── chat_<name>.txt
└── test_outputs/              # screenshots / outputs of the tests
```

## Requirements

- Python 3.8 or newer (developed and tested with Python 3.13 on Windows 11)
- Libraries:
  - `psutil` – listing network interfaces
  - `ntplib` – second SNTP method
  - `ttkbootstrap` – theme of the graphical interface (only needed for `gui.py`)
- Internet connection for the SNTP, remote host and `www.python.org` checks
  (Echo Test, Socket Settings and Chat also work offline)

## Installation

Open a terminal in the project folder and run:

```
pip install -r requirements.txt
```

## Running

Terminal menu:

```
python main.py
```

Graphical interface:

```
python gui.py
```

At start-up both versions synchronize the log clock with the SNTP server:

```
Synchronizing log clock with SNTP server...
Response received from: ('45.138.55.60', 123)
        Time=Thu Oct 22 21:51:03 2026
Log clock synchronized (offset +0.331 s).
```

## Usage (terminal menu)

```
========================================
 NETWORK DIAGNOSTIC TOOL
========================================
1. Machine Information
2. Echo Test
3. SNTP Time Check
4. Socket Settings
5. Chat
6. Error Management
0. Exit
```

Press **Enter** at any question to use the default value shown in brackets.

**1 – Machine Information**: prints hostname, IP address and all interfaces,
then asks for a remote host to resolve (default `www.python.org`).

**2 – Echo Test**: asks for a port (default 9900). Expected result:
`Connection successful, data matches`

**3 – SNTP Time Check**: asks for a server (default `0.uk.pool.ntp.org`) and a
method (1 = raw socket, 2 = ntplib). Prints the server time, the local time and
the difference between them.

**4 – Socket Settings**: asks for a timeout and buffer sizes (defaults 100 s,
4096, 2048) and prints the values before and after the change. The operating
system may round the buffer sizes, so the "After" value can differ from the request.

**5 – Chat** – needs three terminals on the same computer:
1. Terminal 1: `python main.py` → `5` → `s` → port `5000`
2. Terminal 2: `python main.py` → `5` → `c` → name `alice` → port `5000`
3. Terminal 3: `python main.py` → `5` → `c` → name `bob` → port `5000`

Type a message and press Enter; it appears at the other clients and on the server.
Type `/quit` to leave the chat, stop the server with `Ctrl+C`.
Messages are saved in `logs/chat_server.txt`, `logs/chat_alice.txt`, `logs/chat_bob.txt`.

In the GUI, "Start server" and "Open client" open the chat in separate console windows.

**6 – Error Management**: asks for a host and a port. Example inputs and the
error each one produces:

| Host | Port | Result |
|---|---|---|
| `www.python.org` | 80 | connected, server answers `HTTP/1.1 301 Moved Permanently` |
| `nonexistent.invalid` | 80 | address-related error (`gaierror`) |
| `localhost` | 1 | connection refused |
| `www.python.org` | 8080 | connection timed out |

## Log File

`logs/network_tool.log` example:

```
[2026-10-22 21:51:03] [Main] Program started
[2026-10-22 21:51:10] [MachineInfo] hostname=Atamert, ip=192.168.0.13, 8 interfaces
[2026-10-22 21:51:15] [EchoTest] port 9900: connection successful, data matches
[2026-10-22 21:51:22] [SNTP] 0.uk.pool.ntp.org: local - server = -0.331 s
[2026-10-22 21:51:30] [ErrorMgmt] Connection error: [WinError 10061] No connection could be made ...
[2026-10-22 21:51:40] [Main] Program closed
```

## Notes and Problems Found

- `socket.gethostbyname(hostname)` returns only one IP address. On a computer
  with VPN or virtual adapters (Radmin VPN, VirtualBox, Hyper-V) it may return
  the address of a virtual adapter instead of the real LAN address. The
  interface list shows every address together with its adapter.
- While testing, `pip` and the SNTP check failed with `getaddrinfo failed`
  although the browser worked: Radmin VPN added a second default gateway and
  DNS queries to 8.8.8.8 were lost. Disabling the VPN adapter fixed it.
- The chat server listens on `localhost`, so all chat clients must run on the same computer.
- The SNTP comparison does not correct for network delay, so a few
  milliseconds of difference are normal.
