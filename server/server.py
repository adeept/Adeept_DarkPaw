#!/usr/bin/env/python
# File name   : server.py
# Description : main programe for DarkPaw
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22
# Refactored  : Jules

import socket
import time
import threading
import move
import Adafruit_PCA9685
from rpi_ws281x import Color
import os
import FPV
import psutil
import switch
import LED
import logging
import subprocess

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Server:
    def __init__(self, host='', port=10223):
        # Constants
        self.HOST = host
        self.PORT = port
        self.BUFSIZ = 1024
        self.ADDR = (self.HOST, self.PORT)
        self.INFO_PORT = 2256

        # Hardware and state variables
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.led = LED.LED()
        self.fpv = FPV.FPV(led_instance=self.led)

        # State
        self.step_set = 1
        self.speed_set = 150
        self.direction_command = 'no'
        self.turn_command = 'no'
        self.smooth_mode = 0
        self.steady_mode = 0

        # Sockets
        self.tcp_ser_sock = None
        self.tcp_cli_sock = None
        self.client_addr = None

        # Threads
        self.threads = []
        self.state_lock = threading.Lock()

    def _start_thread(self, target, args=()):
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)

    @staticmethod
    def _ap_thread():
        logging.info("Starting Wi-Fi access point...")
        try:
            subprocess.run(
                ["sudo", "create_ap", "wlan0", "eth0", "AdeeptCar", "12345678"],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to start access point: {e}\n{e.stderr}")
        except FileNotFoundError:
            logging.error("`create_ap` command not found. Please install it.")

    @staticmethod
    def _get_cpu_temp():
        """ Returns CPU temperature as a string. """
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as mytmpfile:
                result = float(mytmpfile.read()) / 1000
                return f"{result:.1f}"
        except FileNotFoundError:
            logging.warning("Cannot read CPU temperature.")
            return "N/A"

    @staticmethod
    def _get_cpu_use():
        """ Returns CPU usage as a string. """
        return str(psutil.cpu_percent())

    @staticmethod
    def _get_ram_info():
        """ Returns RAM usage as a string. """
        return str(psutil.virtual_memory()[2])

    def _move_thread(self):
        stand_stu = 1
        while True:
            with self.state_lock:
                steady = self.steady_mode
                direction = self.direction_command
                turn = self.turn_command
                step = self.step_set

            if not steady:
                if direction == 'forward' and turn == 'no':
                    stand_stu = 0
                    move.dove_move_tripod(step, 150, 'forward')
                    with self.state_lock:
                        self.step_set = (self.step_set % 8) + 1
                elif direction == 'backward' and turn == 'no':
                    stand_stu = 0
                    move.dove_move_tripod(step, 150, 'backward')
                    with self.state_lock:
                        self.step_set = (self.step_set % 8) + 1
                elif turn != 'no':
                    stand_stu = 0
                    move.dove_move_diagonal(step, 150, turn)
                    with self.state_lock:
                        self.step_set = (self.step_set % 8) + 1
                elif direction == 'stand' and turn == 'no':
                    if not stand_stu:
                        move.robot_stand(150)
                        with self.state_lock:
                            self.step_set = 1
                        stand_stu = 1
                    time.sleep(0.01)
            else:
                move.robot_X(150, 100)
                move.steady()
            time.sleep(0.01) # Avoid busy-waiting

    def _info_send_client_thread(self):
        server_ip = self.client_addr[0]
        server_addr = (server_ip, self.INFO_PORT)

        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as info_socket:
                    info_socket.connect(server_addr)
                    logging.info(f"Info stream connected to {server_addr}")
                    while True:
                        info_payload = f"{self._get_cpu_temp()} {self._get_cpu_use()} {self._get_ram_info()}"
                        info_socket.send(info_payload.encode())
                        time.sleep(1)
            except socket.error as e:
                logging.error(f"Info stream connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def _fpv_thread(self):
        self.fpv.capture_thread(self.client_addr[0])

    def _handle_client_commands(self):
        ws_R = 0
        ws_G = 0
        ws_B = 0

        while True:
            try:
                data = self.tcp_cli_sock.recv(self.BUFSIZ).decode().strip()
                if not data:
                    logging.warning("Client disconnected.")
                    break

                logging.info(f"Received command: {data}")

                with self.state_lock:
                    if 'forward' == data: self.direction_command = 'forward'
                    elif 'backward' == data: self.direction_command = 'backward'
                    elif 'DS' in data: self.direction_command = 'stand'
                    elif 'left' == data: self.turn_command = 'left'
                    elif 'right' == data: self.turn_command = 'right'
                    elif 'leftside' == data: self.turn_command = 'left'
                    elif 'rightside' == data: self.turn_command = 'right'
                    elif 'TS' in data: self.turn_command = 'no'

                if 'headup' == data: move.ctrl_pitch_roll(150, -100, 0)
                elif 'headdown' == data: move.ctrl_pitch_roll(150, 100, 0)
                elif 'headhome' == data: move.ctrl_pitch_roll(150, 0, 0)
                elif 'low' == data: move.robot_stand(-150)
                elif 'hight' == data: move.robot_stand(150)
                elif 'wsR' in data:
                    try:
                        ws_R = int(data.split()[1])
                        self.led.colorWipe(Color(ws_R, ws_G, ws_B))
                    except (ValueError, IndexError) as e:
                        logging.error(f"Invalid wsR command: {data}, error: {e}")
                elif 'wsG' in data:
                    try:
                        ws_G = int(data.split()[1])
                        self.led.colorWipe(Color(ws_R, ws_G, ws_B))
                    except (ValueError, IndexError) as e:
                        logging.error(f"Invalid wsG command: {data}, error: {e}")
                elif 'wsB' in data:
                    try:
                        ws_B = int(data.split()[1])
                        self.led.colorWipe(Color(ws_R, ws_G, ws_B))
                    except (ValueError, IndexError) as e:
                        logging.error(f"Invalid wsB command: {data}, error: {e}")
                elif 'FindColor' in data:
                    self.led.breath_status_set(1)
                    self.fpv.FindColor(1)
                    self.tcp_cli_sock.send('FindColor'.encode())
                elif 'WatchDog' in data:
                    self.led.breath_status_set(1)
                    self.fpv.WatchDog(1)
                    self.tcp_cli_sock.send('WatchDog'.encode())
                elif 'steady' in data:
                    with self.state_lock:
                        self.steady_mode = 1
                    self.led.breath_status_set(1)
                    self.led.breath_color_set('blue')
                    self.tcp_cli_sock.send('steady'.encode())
                elif 'funEnd' in data:
                    with self.state_lock:
                        self.steady_mode = 0
                    self.led.breath_status_set(0)
                    self.fpv.FindColor(0)
                    self.fpv.WatchDog(0)
                    self.tcp_cli_sock.send('FunEnd'.encode())
                elif 'Smooth_on' in data:
                    with self.state_lock:
                        self.smooth_mode = 1
                    self.tcp_cli_sock.send('Smooth_on'.encode())
                elif 'Smooth_off' in data:
                    with self.state_lock:
                        self.smooth_mode = 0
                    self.tcp_cli_sock.send('Smooth_off'.encode())
                elif 'Switch_1_on' in data: switch.switch(1, 1); self.tcp_cli_sock.send('Switch_1_on'.encode())
                elif 'Switch_1_off' in data: switch.switch(1, 0); self.tcp_cli_sock.send('Switch_1_off'.encode())
                elif 'Switch_2_on' in data: switch.switch(2, 1); self.tcp_cli_sock.send('Switch_2_on'.encode())
                elif 'Switch_2_off' in data: switch.switch(2, 0); self.tcp_cli_sock.send('Switch_2_off'.encode())
                elif 'Switch_3_on' in data: switch.switch(3, 1); self.tcp_cli_sock.send('Switch_3_on'.encode())
                elif 'Switch_3_off' in data: switch.switch(3, 0); self.tcp_cli_sock.send('Switch_3_off'.encode())
            except socket.error as e:
                logging.error(f"Socket error in command loop: {e}")
                break
            except Exception as e:
                logging.error(f"An unexpected error occurred in command loop: {e}")
                break
    
    def setup(self):
        logging.info("Setting up hardware...")
        switch.switchSetup()
        switch.set_all_switch_off()
        self.pwm.set_pwm_freq(50)
        move.init_servos()
        
        try:
            self._start_thread(target=self.led.breath, args=(255,))
            self.led.breath_color_set('blue')
        except Exception as e:
            logging.error(f"Failed to start LED thread. Is rpi_ws281x installed? Error: {e}")

    def wait_for_connection(self):
        # Check for existing network connection, otherwise start AP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("1.1.1.1", 80))
                ipaddr_check = s.getsockname()[0]
                logging.info(f"Connected to network with IP: {ipaddr_check}")
        except OSError:
            logging.info("No network connection. Starting access point thread.")
            self._start_thread(target=self._ap_thread)
            # Visual indicator for AP mode
            colors = [Color(0,16,50), Color(0,16,100), Color(0,16,150), Color(0,16,200), Color(0,16,255), Color(35,255,35)]
            for color in colors:
                self.led.colorWipe(color)
                time.sleep(1)

        # Main server loop to accept client connection
        while True:
            try:
                self.tcp_ser_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.tcp_ser_sock.bind(self.ADDR)
                self.tcp_ser_sock.listen(5)
                logging.info(f"Server listening on {self.ADDR}")

                self.tcp_cli_sock, self.client_addr = self.tcp_ser_sock.accept()
                logging.info(f"Connection from: {self.client_addr}")
                move.robot_stand(150)
                return True # Connection successful
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")
                self.led.colorWipe(Color(0,0,0)) # Signal error
                time.sleep(1) # Wait before retrying

    def start(self):
        self.setup()
        if self.wait_for_connection():
            try:
                self.led.breath_status_set(0)
                self.led.colorWipe(Color(64, 128, 255))
            except Exception as e:
                logging.error(f"Error setting LED after connection: {e}")

            # Start all threads that depend on a client connection
            self._start_thread(target=self._fpv_thread)
            self._start_thread(target=self._move_thread)
            self._start_thread(target=self._info_send_client_thread)

            # Start blocking command handling
            self._handle_client_commands()

    def destroy(self):
        logging.info("Shutting down server and cleaning up...")
        if self.tcp_cli_sock:
            try:
                self.tcp_cli_sock.close()
            except socket.error as e:
                logging.error(f"Error closing client socket: {e}")
        if self.tcp_ser_sock:
            try:
                self.tcp_ser_sock.close()
            except socket.error as e:
                logging.error(f"Error closing server socket: {e}")
        move.clean_all()
        switch.set_all_switch_off()
        self.led.colorWipe(Color(0,0,0))


if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received.")
    except Exception as e:
        logging.critical(f"Unhandled exception in server: {e}")
    finally:
        server.destroy()
