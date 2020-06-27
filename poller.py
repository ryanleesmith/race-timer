from gps import *
import math
import time
import json
import threading
import redis

gpsd = None
gpsPoller = None

red = redis.StrictRedis()

class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        global gpsd
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

        self.startTime = 0
        self.started = False
        self.finished = False
        self.speed = 0 #math.nan
        self.prev_speed = 0
        self.data = {}

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsd
        while self.running:
            gpsd.next()
            #self.speed = gpsd.fix.speed
            if not math.isnan(self.speed):
                #self.speed = math.floor(self.speed * 2.237)

                if self.speed == 0:
                    self.startTime = time.time()
                    self.started = True
                    self.finished = False
                    self.prev_speed = 0
                    self.data = {}
                elif self.started:
                    if self.speed > self.prev_speed:
                        self.prev_speed = self.speed
                        if self.speed >= 30 and '30' not in self.data:
                            diff = time.time() - self.startTime
                            self.data['30'] = diff
                        if self.speed >= 60 and '60' not in self.data:
                            self.finished = True
                            diff = time.time() - self.startTime
                            self.data['60'] = diff
                    else:
                        self.prev_speed = 0
                        self.started = False
            self.speed += 1

class SpeedThreader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsPoller
        if not gpsPoller or not gpsPoller.running:
            try:
                gpsPoller = GpsPoller()
                gpsPoller.start()
            except (KeyboardInterrupt, SystemExit):
                print("\nKilling GpsPoller...")
                gpsPoller.running = False
                gpsPoller.join()

        while True:
            if math.isnan(gpsPoller.speed):
                red.publish('status', u'SPEED_UNKNOWN')
                continue
            
            dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': gpsPoller.speed})
            red.publish('speed', u'{}'.format(dump))
            
            if gpsPoller.speed == 0:
                red.publish('status', u'READY')
            elif gpsPoller.started:
                if gpsPoller.speed > gpsPoller.prev_speed:
                    red.publish('status', u'TIMING')
                    if '30' in gpsPoller.data:
                        dump = json.dumps({'30': gpsPoller.data['30']})
                        red.publish('result', u'{}'.format(dump))
                    if '60' in gpsPoller.data:
                        dump = json.dumps({'60': gpsPoller.data['30']})
                        red.publish('result', u'{}'.format(dump))
                #else:
                    ## ?
                if gpsPoller.finished:
                    red.publish('status', u'FINISHED')
            elif not gpsPoller.finished:
                red.publish('status', u'NOT_READY')
            
            time.sleep(0.1)

class ModeThreader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsPoller
        if not gpsPoller or not gpsPoller.running:
            try:
                gpsPoller = GpsPoller()
                gpsPoller.start()
            except (KeyboardInterrupt, SystemExit):
                print("\nKilling GpsPoller...")
                gpsPoller.running = False
                gpsPoller.join()

        while True:
            red.publish('mode', gpsd.fix.mode)
            time.sleep(1)

def start():
    modeThreader = ModeThreader()
    speedThreader = SpeedThreader()
    try:
        modeThreader.start()
        speedThreader.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nKilling threads...")
        modeThreader.running = False
        modeThreader.join()
        speedThreader.running = False
        speedThreader.join()
