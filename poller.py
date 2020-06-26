from gps import *
import math
import time
import json
import threading
import redis

gpsd = None
poller = None

red = redis.StrictRedis()

class Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        global gpsd
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsd
        while self.running:
            gpsd.next()

def start():
    global gpsd, poller
    poller = Poller()
    mode = None

    try:
        poller.start()
        while True:
            speed = gpsd.fix.speed
            if math.isnan(speed):
                speed = 0
            #print(speed)
            #print(gpsd.fix.mode)
            if gpsd.fix.mode != mode:
                mode = gpsd.fix.mode
                red.publish('mode', mode)
            red.publish('speed', speed)
            #print(gpsd.satellites)
            #dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': speed})
            #yield 'event: SPEED\ndata: {}\n\n'.format(dump)
            
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        print("\nKilling Thread...")
        poller.running = False
        poller.join()
