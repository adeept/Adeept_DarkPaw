#!/usr/bin/env/python3
# File name   : Client.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import socket
import sys
import threading

should_exit = False

def receive_message(client_socket):
    global should_exit
    while not should_exit:
        try:
            client_socket.settimeout(1)
            data = client_socket.recv(1024)
            if data:
                message = data.decode('utf-8')
                print(f"Received from server: {message}")
            else:
                break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

if len(sys.argv) != 2:
    print("Please enter the server's IP address when running, for example: python3 client.py 192.168.1.100")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = 8000

# Create a TCP - based socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    client_socket.connect((server_ip, server_port))
    print(f"Connected to server {server_ip}:{server_port}")
    # Start the thread that receives server messages
    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    receive_thread.start()

    while True:
        # Get input from the keyboard
        message = input("Please enter the message to send (type 'exit' to quit): ")
        if message.lower() == 'exit':
            should_exit = True
            break
        # Send the message to the server
        client_socket.send(message.encode('utf-8'))
except socket.error as e:
    print(f"Error connecting to the server: {e}")
finally:
    client_socket.close()
    if 'receive_thread' in locals():
        receive_thread.join()
        
        
        