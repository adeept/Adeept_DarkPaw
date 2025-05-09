#!/usr/bin/env/python3
# File name   : Server.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import socket
import threading

should_exit = False

def handle_client(client_socket, client_address):
    global should_exit
    while not should_exit:
        try:
            client_socket.settimeout(1)
            data = client_socket.recv(1024)
            if data:
                message = data.decode('utf-8')
                print(f"Received from {client_address}: {message}")
            else:
                break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error communicating with {client_address}: {e}")
            break
    client_socket.close()

def send_message(client_socket):
    global should_exit
    while not should_exit:
        try:
            message = input("Enter message to send to client (type 'exit' to quit): ")
            if message.lower() == 'exit':
                should_exit = True
                break
            client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")
            break

# Create a TCP - based socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to all available network interfaces, port number set to 8000
server_address = ('0.0.0.0', 8000)
server_socket.bind(server_address)

# Start listening, maximum number of connections is 5
server_socket.listen(5)
server_socket.settimeout(1)
print("Server has started and is listening for connections...")

connected_threads = []

while not should_exit:
    try:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        # Start the thread that receives client messages
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
        connected_threads.append(client_thread)
        # Start the thread that sends messages to the client
        send_thread = threading.Thread(target=send_message, args=(client_socket,))
        send_thread.start()
        connected_threads.append(send_thread)
    except socket.timeout:
        continue
    except Exception as e:
        if should_exit:
            break
        print(f"Error accepting connection: {e}")


server_socket.close()

for thread in connected_threads:
    thread.join()
print("Server has stopped.")