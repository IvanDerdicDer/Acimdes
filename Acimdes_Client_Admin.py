# Vesion 1.0

# Gives admin privelages to the server.
# Commands:
#   -!Stop -- Stops the server safely.
# More to be added.

# run with "python Acimdes_Client.py"

# Copyright 2020 Ivan Derdić

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket as soc
import sys
import threading as thrd
import errno
import time

HEADER_LENGTH = 10
IP = soc.gethostbyname(soc.gethostname())
# IP = soc.gethostbyname('raspberrypi')
# IP = soc.gethostbyname('ivangeneral.ddns.net')
# IP = '192.168.5.2'
PORT = 7777
ADDR = (IP, PORT)
FORMAT = 'utf-8'
END_SESSION = "!disconnect"
STOP = '!Stop'
usrname = 'Admin'


def send_msg(msg_in: str):
    msg_coded: bytes = msg_in.encode(FORMAT)
    msg_head = f"{len(msg_coded):<{HEADER_LENGTH}}".encode(FORMAT)
    msg_send = msg_head + msg_coded
    client_soc.send(msg_send)


def receive_msg():
    head = client_soc.recv(HEADER_LENGTH)
    if not len(head):
        print("[CON_CLOSED]Connection closed by server")
        kill.set()
        sys.exit()
    length = int(head.decode(FORMAT))
    return client_soc.recv(length).decode(FORMAT)


def continuous_recv(kill):
    while not kill.is_set():
        time.sleep(0.01)
        try:
            msg = receive_msg()
            print(msg)
        except:
            pass


client_soc = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
client_soc.connect(ADDR)
client_soc.setblocking(False)

kill = thrd.Event()
t = thrd.Thread(target=continuous_recv, args=[kill])
t.start()


send_msg(usrname)

while True:
    try:
        msg = input()
        if msg == END_SESSION:
            kill.set()
            client_soc.close()
            print("[END_SESSION]Ending session...")
            sys.exit()
        if msg:
            send_msg(msg)


    except IOError as e:

        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print(f"Reading error: {e}")

            sys.exit()

        continue


    except Exception as e:

        print(f"General error: {e}")

        sys.exit()
