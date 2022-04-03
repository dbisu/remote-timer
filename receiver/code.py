# License : GPLv2.0
# copyright (c) 2022  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
# FeatherS2 board support


import time
import digitalio
from board import *
import wifi
import busio
import displayio
import adafruit_framebuf
import adafruit_displayio_sh1106
from adafruit_display_text import label
import terminalio
import socketpool
import adafruit_requests
import ssl

def startWiFi():
    # Get wifi details and more from a secrets.py file
    try:
        from secrets import secrets
    except ImportError:
        print("WiFi secrets are kept in secrets.py, please add them there!")
        raise

    notConnected = True
    while(notConnected == True):
        try:
            print("Connect wifi")
            wifi.radio.connect(secrets['ssid'],secrets['password'], timeout=30)
            notConnected = False
            #wifi.radio.start_ap(secrets['ssid'],secrets['password'])
            HOST = repr(wifi.radio.ipv4_address)
            PORT = 555        # Port to listen on
            print(HOST,PORT)
        except ConnectionError:
            print("No Wifi Network found, retrying in 5 sec")
            time.sleep(5)

def startConnection(conn):
    try:
        host = repr(wifi.radio.ipv4_gateway)
        print("Connecting to ", host, " 555")
        conn.connect((host,555))
        return conn
    except OSError as e:
        print("Timed Out, continuing")
        return()


class TimerRunner:
    def __init__(self,conn):
        self.connection = conn
        self.currentTimer = 0
        self.timerRunning = False
        self.display = None

    def initDisplay(self):
        WIDTH = 130 # Change these to the right size for your display!
        HEIGHT = 64
        i2c = busio.I2C(SCL, SDA) # Create the I2C interface.
        display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
        self.display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT) # Create the SH1106 OLED class.


    def NugEyes(self, IMAGE): ## Make a function to put eyes on the screen
        bitmap = displayio.OnDiskBitmap(IMAGE) # Setup the file as the bitmap data source
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader) # Create a TileGrid to hold the bitmap
        group = displayio.Group() # Create a Group to hold the TileGrid
        group.append(tile_grid) # Add the TileGrid to the Group
        self.display.show(group) # Add the Group to the Display


    def sendHeartbeat(self):
        cmd = b'\x55'
        timer_bytes = b'\xff\xff\xff'
        msg = cmd + timer_bytes
        #print("Sending: ", msg)
        self.connection.send(msg)

    def stepTimer(self):
        if(self.currentTimer > 0) and (self.timerRunning == True):
            self.currentTimer = self.currentTimer - 1
            print("Time remaining ", self.currentTimer)
            msg = "Time remaining\n" + str(self.currentTimer) + " seconds"
            #self.NugEyes("/faces/boingo.bmp")
        else:
            print("We're live")
            msg = "We're live"
            #self.NugEyes("/faces/menu.bmp")

    def receiveTimers(self):
        try:
            recvBuffer = bytearray(100)
            datalen = self.connection.recv_into(recvBuffer)
            #print("Received: ", recvBuffer[:datalen])
            cmd = recvBuffer[0].to_bytes(1,'big')
            timer_bytes = recvBuffer[1:4]
            if(cmd == b'\x42'):
                timer = int.from_bytes(timer_bytes,'big')
                msg = self.runTimer(timer)
            elif(cmd == b'\xAA'):
                msg = self.stopTimer()
            elif(cmd == b'\x33'):
                # server heartbeat
                msg = self.stepTimer()
        except OSError as e:
            #print("Timed Out, continuing")
            return(None)

    def showMessage(self, msg):
        text = "Hello world"
        text_area = label.Label(terminalio.FONT, text=text)
        text_area.x = 10
        text_area.y = 10
        #group = displayio.Group()
        #text = msg
        #text_area = label.Label(
        #    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
        #)
        #group.append(text_area)
        self.display.show(text_area)

    def runTimer(self, timer):
        print("Starting ", timer, " second timer")
        msg = "Starting " + str(timer) + " second\n timer"
        self.currentTimer = timer
        self.timerRunning = True
        return(msg)

    def stopTimer(self):
        print("Stopping timer")
        msg = "Stopping timer"
        self.timerRunning = False
        return(msg)

    def mainLoop(self):
        while True:
            # run thread loop
            # send heartbeat
            self.sendHeartbeat()
            # update timers
            msg = self.receiveTimers()
            # update display
            if (msg != None):
                self.showMessage(msg)
            time.sleep(1)

    def start(self):
        self.initDisplay()
        #self.NugEyes("/faces/menu.bmp")
        self.mainLoop()


## Screen setup and function to change image on the screen
displayio.release_displays()
WIDTH = 130 # Change these to the right size for your display!
HEIGHT = 64
BORDER = 1


pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
conn = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
conn.settimeout(1)


print("Starting Wifi")
startWiFi()

server = startConnection(conn)

timer = TimerRunner(server)
timer.start()
