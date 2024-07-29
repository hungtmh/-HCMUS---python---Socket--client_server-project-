import os
import socket
import threading

# Define server address and port
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
DICTIONARY = "files"
BUFFER_SIZE = 1024
FORMAT = 'utf-8'

def list_files():
    # Specify the directory containing the files
    directory = DICTIONARY

    # Initialize an empty list to store the file names and sizes
    files_with_sizes = []

    # Loop through each file in the directory
    for filename in os.listdir(directory):
        # Get the full path of the file
        file_path = os.path.join(directory, filename)

        # Get the size of the file
        file_size = os.path.getsize(file_path)

        # Append a tuple (filename, file_size) to the list
        files_with_sizes.append((filename, file_size))

    # Return the list of tuples
    return files_with_sizes

def handle_client(client_socket):
    # Get the list of files and their sizes
    files = list_files()

    # Create a string of file names and sizes
    file_list = ""
    for file, size in files:
        file_list += f"{file}:{size}\n"

    # Encode the file list string to UTF-8 format
    encoded_file_list = file_list.encode(FORMAT)

    # Send the encoded file list to the client
    client_socket.sendall(encoded_file_list)

    while True:
        try:
            # Receive the file name requested by the client, the data received will be in bytes
            requested_file_bytes = client_socket.recv(BUFFER_SIZE)

            # Decode the byte data to a string in UTF-8 format
            requested_file = requested_file_bytes.decode(FORMAT)

            # If nothing is received (connection is closed), exit the loop
            if not requested_file:
                break

            # Check if the requested file is in the list of files
            file_names = [f[0] for f in files]
            if requested_file in file_names:
                # Create the full path to the requested file
                file_path = os.path.join(DICTIONARY, requested_file)

                # Open the file for reading in binary mode
                with open(file_path, 'rb') as file:
                    while True:
                        # Read a chunk of data from the file
                        data = file.read(BUFFER_SIZE)

                        # If no more data to read (end of file), exit the loop
                        if not data:
                            break

                        # Send the chunk of data to the client
                        client_socket.sendall(data)
        except Exception as e:
            # If an error occurs, print the error message and exit the loop
            print(f"Error: {e}")
            break

    # Close the connection with the client after processing is complete
    client_socket.close()

# Create the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)
server_socket.listen()
print("Server is listening...")
print(f"Server is running on {HOST}, {PORT}")

while True:
    # Accept a connection from the client
    client_socket, client_addr = server_socket.accept()
    print(f"Connected by {client_addr}")

    # Create a new thread to handle the client
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()