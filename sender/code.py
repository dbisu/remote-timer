# License : GPLv2.0
# copyright (c) 2022  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
# FeatherS2 board support


import time
import digitalio
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
import board
from board import *
import wifi
import socketpool
import adafruit_requests
import ssl
import ipaddress
import random



def startWiFi():
    # Get wifi details and more from a secrets.py file
    try:
        from secrets import secrets
    except ImportError:
        print("WiFi secrets are kept in secrets.py, please add them there!")
        raise

    print("Connect wifi")
    #wifi.radio.connect(secrets['ssid'],secrets['password'])
    wifi.radio.start_ap(secrets['ssid'],secrets['password'])
    HOST = repr(wifi.radio.ipv4_address_ap)
    PORT = 555        # Port to listen on
    print(HOST,PORT)

# data format
# byte 0: cmd byte
# byte 1-3: timer value in seconds

# commands:
# 0x42 - start timer
# 0xAA = stop timer
# 0X55 = client heartbeat
# 0x33 = server heartbeat

# example - start 30s timer
# msg = b'\x42\x00\x00\x1E'

# example - start 5min timer
# msg = b'\x42\x00\x01\x2c'

# example - start 1 hour timer
# msg = b'\x42\x00\x0E\x10'

# example - stop timer
# msg = b'\xAA\xFF\xFF\xFF'

def startService(s):
    try:
        client, remote_addr = s.accept()
        print("Connection from ", remote_addr)
        return client

    except OSError as e:
        print("Timed Out")
        return()


def sendStop(client):
    cmd = b'\xAA'
    timer_bytes = b'\xFF\xFF\xFF'
    msg = cmd + timer_bytes
    print("Sending: ", msg)
    client.send(msg)

def sendTimer(client, buttonNum):
    seconds = random.randint(1,300)
    if(buttonNum == 1):
        seconds = 30
    elif(buttonNum == 2):
        seconds = 60
    elif(buttonNum == 3):
        seconds = 90
    elif(buttonNum == 4):
        seconds = 5
    timer_bytes = seconds.to_bytes(3,'big')
    cmd = b'\x42'
    msg = cmd + timer_bytes
    print("Sending: ", msg)
    client.send(msg)

def sendHeartbeat(client):
    cmd = b'\x33'
    timer_bytes = b'\xFF\xFF\xFF'
    msg = cmd + timer_bytes
    print("Sending: ", msg)
    client.send(msg)

def readButtons():
    buttonNum = -1
    for i in range(len(buttons)):
        buttons[i].update()
        if buttons[i].fell:
            print("button",i,"pressed!")
        if buttons[i].rose:
            print("button",i,"released!")
            buttonNum = i
    return(buttonNum)

def mainLoop(client):
    try:
        recvBuffer = bytearray(100)
        datalen = client.recv_into(recvBuffer)
        print("Received: ", recvBuffer[:datalen])
        command = int(recvBuffer[0])
        cmd_bytes = command.to_bytes(1,'big')
        print("Command: ", cmd_bytes)
        if(cmd_bytes == b'\x55'):
            randcmd = random.randint(0,15)
            buttonNum = readButtons()
            print(buttonNum)
            if(buttonNum == 0):
                sendStop(client)
            elif(buttonNum > 0):
                sendTimer(client, buttonNum)
            else:
                sendHeartbeat(client)
        else:
            print("unknown command: ", cmd_bytes)
    except OSError as e:
        print("Timed Out, continuing ", e)
        return()

pins = (board.IO18,board.IO14,board.IO12,board.IO6,board.IO5)
buttons = []   # will hold list of Debouncer objects
for pin in pins:   # set up each pin
    tmp_pin = DigitalInOut(pin) # defaults to input
    tmp_pin.pull = Pull.UP      # turn on internal pull-up resistor
    buttons.append( Debouncer(tmp_pin) )

stopButton = buttons[0]

print("Starting Wifi")
startWiFi()

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
s = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
s.settimeout(None)
s.bind(['0.0.0.0', 555])
s.listen(1)

print("Listening on port 555")

notConnected = True
while (notConnected == True):
    client = startService(s)
    if(client != None):
        notConnected = False

while True:
    mainLoop(client)
    time.sleep(1)
