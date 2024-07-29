import socket
import os
import time
import threading
import signal
import sys
from tqdm import tqdm

# Configuration Constants

PORT = 65432
BUFFER_SIZE = 1024
INPUT_FILE = "input.txt"
OUTPUT_DIR = "output"
FORMAT = 'utf-8'

# Priority Mapping
priority_values = {
    "CRITICAL": 10,
    "HIGH": 4,
    "NORMAL": 1
}

# Global Variables
completed_files = []
file_progress = {}
stop_threads = False

# Signal Handling Class
class SignalHandler:
    def __init__(self):
        self.stop_threads = False
        signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        print("\nClient has pressed Ctrl+C. Closing connection...")
        self.stop_threads = True
        sys.exit(0)

# Initialize SignalHandler
signal_handler_instance = SignalHandler()

# Utility Functions
def list_files_to_download():
    files = []
    try:
        with open(INPUT_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.rsplit(' ', 1)
                filename = parts[0]
                priority = parts[1] if len(parts) > 1 else "NORMAL"
                files.append((filename, priority))
    except FileNotFoundError:
        print(f"File {INPUT_FILE} not found.")
    return files

def get_available_files():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(ADDR)
            files_info = client_socket.recv(BUFFER_SIZE).decode(FORMAT).split('\n')
            return {name: int(size) for name, size in (file.split(':') for file in files_info if ':' in file)}
    except Exception as e:
        print(f"Error getting available files: {e}")
        return {}

def download_file(file_name, file_size, chunks, priority):
    global stop_threads
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(ADDR)
            client_socket.sendall(file_name.encode(FORMAT))

            save_path = os.path.join(OUTPUT_DIR, file_name)
            total_received = 0
            client_socket.recv(BUFFER_SIZE).decode(FORMAT)  # To synchronize with the server
            with open(save_path, 'wb') as f, tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name, leave=False) as pbar:
                while total_received < file_size and not stop_threads:

                    file_data = client_socket.recv(min(BUFFER_SIZE * chunks, file_size - total_received))
                    if not file_data:
                        break
                    f.write(file_data)
                    total_received += len(file_data)

                    pbar.update(len(file_data))
                    file_progress[file_name] = (total_received / file_size) * 100

                    # Adjust the sleep time based on priority to simulate different download speeds
                    time.sleep(0.0000000001*chunks)

            if not stop_threads:
                file_progress[file_name] = 100
                completed_files.append(file_name)

    except Exception as e:
        print(f"Error downloading {file_name}: {e}")

def start_download_threads(files, files_to_download):
    threads = []
    for file_name, priority in files_to_download:
        if stop_threads or file_name in completed_files or file_name not in files:
            continue

        file_size = files[file_name]
        chunks = priority_values.get(priority.upper(), 1)
        thread = threading.Thread(target=download_file, args=(file_name, file_size, chunks, priority.upper()))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    HOST=input("please Enter the server IP for connection: ")
    ADDR = (HOST, PORT)
    print_lock = threading.Lock()

    try:
        files = get_available_files()
        if files:
            print("Priority values:", priority_values)
            print("Available files:")
            for file, size in files.items():
                print(f"{file} ({size} bytes)")
        while not signal_handler_instance.stop_threads:
            files_to_download = list_files_to_download()
            start_download_threads(files, files_to_download)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nClient has pressed Ctrl+C. Closing connection...")