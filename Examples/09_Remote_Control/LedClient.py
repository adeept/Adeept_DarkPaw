#!/usr/bin/env/python3
# File name   : LedClient.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import socket
import sys

if len(sys.argv)!= 2:
    print("Please enter the server's IP address when running, for example: python3 client.py 192.168.3.31")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = 8000

# Create a TCP - based socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    client_socket.connect((server_ip, server_port))
    while True:
        # Get input from the keyboard
        message = input("Please enter the message to send (type 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        # Send the message to the server
        client_socket.send(message.encode('utf-8'))
except socket.error as e:
    print(f"Error connecting to the server: {e}")
finally:
    # Close the client socket
    client_socket.close()
    
    
