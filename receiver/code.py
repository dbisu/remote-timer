# License : GPLv2.0
# copyright (c) 2022  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)


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
from webapp import *

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
    PORT = 80        # Port to listen on
    print(HOST,PORT)

def initDisplay():
    WIDTH = 130 # Change these to the right size for your display!
    HEIGHT = 64
    i2c = busio.I2C(SCL, SDA) # Create the I2C interface.
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
    display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT) # Create the SH1106 OLED class.
    return display

## Screen setup and function to change image on the screen
displayio.release_displays()
WIDTH = 130 # Change these to the right size for your display!
HEIGHT = 64
BORDER = 1

print("Starting Wifi")
startWiFi()
print("Init Display")
display = initDisplay()
print("Starting Web Service")
startWebService(display)
