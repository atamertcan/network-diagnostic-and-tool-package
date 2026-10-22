import os
import time
from modules.sntp_time import sntp_client

# logs/ folder next to main.py (created if missing, git does not keep empty folders)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "network_tool.log")

# difference between SNTP time and local time, stays 0 if SNTP is not reachable
time_offset = 0.0


#Get the time once from the SNTP module and use it for all log timestamps
def sync_log_clock():
    global time_offset
    print("Synchronizing log clock with SNTP server...")
    server_time = sntp_client()
    if server_time is None:
        print("SNTP not reachable, logs will use the local clock.")
    else:
        time_offset = server_time - time.time()
        print("Log clock synchronized (offset %+.3f s)." % time_offset)


#Current time as text, corrected with the SNTP offset
def now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + time_offset))


#Append one line to the main log file
def log(module, message):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("[%s] [%s] %s\n" % (now_str(), module, message))
