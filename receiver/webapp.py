# License : GPLv2.0
# copyright (c) 2021  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
# FeatherS2 board support

import socketpool
import time
import os
import storage

import wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp
import wifi

import displayio
import adafruit_framebuf
import adafruit_displayio_sh1106
from adafruit_display_text import label
import terminalio

class Timer():
    def __init__(self):
        self.is_running = False
        self.time_remaining = 0

def showMessage(msg):
    global display
    text = "Hello world"
    text_area = label.Label(terminalio.FONT, text=msg)
    text_area.x = 10
    text_area.y = 10
    #group = displayio.Group()
    #text = msg
    #text_area = label.Label(
    #    terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1
    #)
    #group.append(text_area)
    display.show(text_area)




web_app = WSGIApp()




@web_app.route("/")
def index(request):
    response = "Display Timer"
    return("200 OK", [('Content-Type', 'text/html')], response)

@web_app.route("/api/stop", methods=["POST"])
def stop(request):
    global timer
    timer.is_running = False
    timer.time_remaining = 0
    msg = "Timer stopped"
    showMessage(msg)
    response = "Timer Stopped"
    return("200 OK", [('Content-Type', 'text/html')], response)

@web_app.route("/api/timer/<seconds>", methods=["POST"])
def run_timer(request,seconds):
    timer.is_running = True
    timer.time_remaining = int(seconds)
    response = "Timer started"
    return("200 OK", [('Content-Type', 'text/html')], response)

def update_timer():
    global timer
    if(timer.is_running == True):
        if(timer.time_remaining > 0):
            timer.time_remaining -= 1
        msg = "Time remaining " + str(timer.time_remaining)
        showMessage(msg)
    else:
        msg = "Timer stopped"
        showMessage(msg)


def startWebService(display_param):

    #web_app = WSGIApp()

    HOST = repr(wifi.radio.ipv4_address_ap)
    PORT = 80        # Port to listen on
    print(HOST,PORT)

    global timer
    timer = Timer()

    global display
    display = display_param

    poll_time = time.time()

    wsgiServer = server.WSGIServer(80, application=web_app)

    print(f"open this IP in your browser: http://{HOST}:{PORT}/")

    # Start the server
    wsgiServer.start()
    while True:
        wsgiServer.update_poll()
        currentTime = time.time()
        if(currentTime > poll_time):
            update_timer()
            poll_time = currentTime

        time.sleep(0.01)
