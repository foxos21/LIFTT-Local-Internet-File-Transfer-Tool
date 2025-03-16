import os
import socket
import sys
import time
import getpass
from wakepy import keep


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def receive_file(host, port):
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}...")

    # Accept incoming connection from the client
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")

    # Receive the file name and size
    file_name = client_socket.recv(100).decode().strip()
    file_size = int(client_socket.recv(1024).decode())

    # Send acknowledgment back to the client to start file transfer
    client_socket.send(b"ACK")

    # Open the file to save the incoming content
    with open(file_name, 'wb') as file:
        bytes_received = 0
        start_time = time.time()
        with keep.presenting():
            while bytes_received < file_size:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                file.write(chunk)
                bytes_received += len(chunk)

                # Update the progress bar
                percent_received = (bytes_received / file_size) * 100
                elapsed_time = time.time() - start_time
                speed = bytes_received / elapsed_time if elapsed_time > 0 else 0
                to_print = f"{bcolors.WARNING}Sending {bcolors.ENDC}{file_name}{bcolors.ENDC}: {bcolors.WARNING}{percent_received:.2f}% {bcolors.ENDC}| {bcolors.OKGREEN}{bytes_received / 1024:.2f} KB / {file_size / 1024:.2f} KB {bcolors.ENDC}| {bcolors.FAIL}Speed: {speed / 1024:.2f} KB/s{bcolors.ENDC}"
                refresh(to_print, bcolors.OKGREEN)

        print(f"\nFile '{file_name}' received successfully.")

    client_socket.close()
    server_socket.close()


def server_side():
    print(f"{bcolors.WARNING}Running As Server{bcolors.ENDC}")
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    print(f"Your IP Address Is {bcolors.BOLD}'{IPAddr}'{bcolors.ENDC}")
    host = "0.0.0.0"  # Listen on all available interfaces
    port = input(
        f"{bcolors.OKCYAN}Port to connect to (default 12345){bcolors.ENDC}\n:: ")  # Port to connect to (must be the same on both sides)
    if port == "" or port == " ":
        port = 12345

    receive_file(host, port)


def send_file(filename, host, port):
    print(f"Connecting to {host}:{port}")

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((host, port))
    print(f"Connected to {host}:{port}")

    # Open the file in binary mode
    with open(filename, 'rb') as file:
        # Send the file name and size
        file_name = os.path.basename(filename)
        file_size = os.path.getsize(filename)

        # Send file name and size first
        client_socket.send(f"{file_name}{' ' * (100 - len(file_name))}".encode())  # Ensure fixed length for filename
        client_socket.send(str(file_size).encode())

        # Wait for receiver to acknowledge file size
        client_socket.recv(1024)

        # Initialize progress bar variables
        bytes_sent = 0
        start_time = time.time()

        # Send file in chunks
        with keep.presenting():
            while chunk := file.read(1024):
                client_socket.send(chunk)
                bytes_sent += len(chunk)

                # Update the progress bar
                percent_sent = (bytes_sent / file_size) * 100
                elapsed_time = time.time() - start_time
                speed = bytes_sent / elapsed_time if elapsed_time > 0 else 0
                to_print = f"{bcolors.WARNING}Receiving {bcolors.ENDC}{file_name}{bcolors.ENDC}: {bcolors.WARNING}{percent_sent:.2f}% {bcolors.ENDC}| {bcolors.OKGREEN}{bytes_sent / 1024:.2f} KB / {file_size / 1024:.2f} KB {bcolors.ENDC}| {bcolors.FAIL}Speed: {speed / 1024:.2f} KB/s{bcolors.ENDC}"
                refresh(to_print, bcolors.OKGREEN)

        print(f"\nFile '{filename}' sent successfully.")
    client_socket.close()


def client_side():
    print(f"{bcolors.WARNING}Running As Client{bcolors.ENDC}")
    # File to send
    print(f"{bcolors.OKBLUE}{search_for_videos()}{bcolors.ENDC}")
    filename = input(f"{bcolors.OKCYAN}where your file at?{bcolors.ENDC}\n:: ")  # Replace with your file's path

    if os.path.exists(os.path.join("./", "ip")):
        with open(os.path.join("./", "ip"), 'r') as file:
            host = file.read()
        print(f"{bcolors.WARNING}Using IP from File.{bcolors.ENDC}")
    else:
        host = input(
            f"{bcolors.OKCYAN}IP address of the receiving device\n(Only the last digits. Press enter for custom){bcolors.ENDC}\n:: ")  # Replace with the IP address of the receiving device

        if host == "":
            host = input(
                f"{bcolors.OKCYAN}FULL IP address of the receiving device{bcolors.ENDC}\n:: ")
        else:
            host = "192.168.1." + host

        with open(os.path.join("./", "ip"), 'w') as file:
            file.write(host)

    port = input(
        f"{bcolors.OKCYAN}Port to connect to (default 12345){bcolors.ENDC}\n:: ")  # Port to connect to (must be the same on both sides)
    if port == "" or port == " ":
        port = 12345

    send_file(filename, host, port)


def search_for_videos(folder_path="./"):
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    result_list = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(tuple(video_extensions)):
                result_list.append(os.path.join(root, file))
    return result_list


def refresh(text, color):
    sys.stdout.write("\033[H")
    text = f" {text} "
    todo = []
    roof_length = len(text) - 40
    roof = f"{color}─{bcolors.ENDC}" * roof_length
    top = f"{color}┌{bcolors.ENDC}" + roof + f"{color}┐{bcolors.ENDC}"
    todo.append(top)
    todo.append(f"{color}│{bcolors.ENDC}{text}{color}│{bcolors.ENDC}")
    bottom = f"{color}└{bcolors.ENDC}" + roof + f"{color}┘{bcolors.ENDC}"
    todo.append(bottom)
    for n in todo:
        sys.stdout.write(f"\033[{n}\n")
    sys.stdout.flush()



def print_text(text, color):
    text = f" {text} "
    todo = []
    top = f"{color}┌{bcolors.ENDC}" + f"{color}─{bcolors.ENDC}" * len(text) + f"{color}┐{bcolors.ENDC}"
    todo.append(top)
    todo.append(f"{color}│{bcolors.ENDC}{text}{color}│{bcolors.ENDC}")
    bottom = f"{color}└{bcolors.ENDC}" + f"{color}─{bcolors.ENDC}" * len(text) + f"{color}┘{bcolors.ENDC}"
    todo.append(bottom)
    for n in todo:
        print(f"{n}")


def scrub():
    try:
        os.system('cls')
    except:
        os.system('clear')


print_text(f"Hello {getpass.getuser()}!", bcolors.HEADER)
print_text("What will be this device?", bcolors.OKBLUE)
system = input("s) Server\nc) Client\n:: ")
scrub()
if system == "s":
    server_side()
else:
    client_side()
scrub()
input(f"{bcolors.FAIL}PROCESS FINISHED{bcolors.ENDC}")
