#!/usr/bin/env/python3
# File name   : LedServer.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import socket
import threading
from gpiozero import LED

# Function to set up the LED objects.
# Initializes three LED objects corresponding to different GPIO pins.
def switchSetup():
    global led1, led2, led3
    led1 = LED(9)
    led2 = LED(25)
    led3 = LED(11)

# Function to control the state of a specific LED.
# port: The number of the LED (1, 2, or 3).
# status: 1 to turn the LED on, 0 to turn it off.
def switch(port, status):
    if port == 1:
        if status == 1:
            led1.on()
        elif status == 0:
            led1.off()
    elif port == 2:
        if status == 1:
            led2.on()
        elif status == 0:
            led2.off()
    elif port == 3:
        if status == 1:
            led3.on()
        elif status == 0:
            led3.off()
    else:
        print('Wrong Command: Example--switch(3, 1)->to switch on port3')

# Function to handle client connections.
# client_socket: The socket object used for communication with the client.
# client_address: The address of the client.
def handle_client(client_socket, client_address):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            try:
                message = data.decode('utf-8')
                print(f"Received command: {message}")
                if message.startswith("LED"):
                    parts = message.split()
                    if message == "LEDALL ON":
                        switch(1, 1)
                        switch(2, 1)
                        switch(3, 1)
                        print("All LEDs are turned on")
                    elif message == "LEDALL OFF":
                        switch(1, 0)
                        switch(2, 0)
                        switch(3, 0)
                        print("All LEDs are turned off")
                    else:
                        led_num = int(parts[0][3:])
                        if len(parts) == 2:
                            if parts[1] == "ON":
                                switch(led_num, 1)
                                print(f"LED{led_num} is turned on")
                            elif parts[1] == "OFF":
                                switch(led_num, 0)
                                print(f"LED{led_num} is turned off")
                        else:
                            print(f"Invalid command: {message}")
                else:
                    print(f"Invalid command: {message}")
            except UnicodeDecodeError:
                print(f"Error decoding the received data: {data}")
    except socket.error as e:
        print(f"Socket error while communicating with {client_address}: {e}")
    except Exception as e:
        print(f"Error handling the client request: {e}")
    finally:
        client_socket.close()

# Create a TCP-based socket object.
# AF_INET indicates the IPv4 address family, and SOCK_STREAM indicates the TCP protocol.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to all available network interfaces and set the port number to 8000.
server_address = ('0.0.0.0', 8000)
server_socket.bind(server_address)

# Start listening for incoming connections.
# The maximum number of queued connections is set to 5.
server_socket.listen(5)
print("Server has started and is listening for connections...")

switchSetup()

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Accepted connection from {client_address}")
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()
