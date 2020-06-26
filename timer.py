from gps import *
import math
import time
import json
import threading

gpsd = None
poller = None

class Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        global gpsd
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsd, poller
        while poller.running:
            gpsd.next()

def timer():
    global gpsd, poller
    poller = Poller()
    try:
        poller.start()
        while True:
            speed = gpsd.fix.speed
            if math.isnan(speed):
                speed = 0
            print(speed)
            dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': speed})
            yield 'event: SPEED\ndata: {}\n\n'.format(dump)
            
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        print("\nKilling Thread...")
        poller.running = False
        poller.join()
