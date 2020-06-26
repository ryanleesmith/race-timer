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

        self.mode = None

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsd
        while self.running:
            gpsd.next()
            self.mode = gpsd.fix.mode

class SpeedThreader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.startTime = 0
        self.started = False
        self.finished = False
        self.prev_speed = 0
        self.data = {}

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsPoller
        if not gpsPoller or not gpsPoller.running:
            try
                gpsPoller = GpsPoller()
                gpsPoller.start()
            except (KeyboardInterrupt, SystemExit):
                print("\nKilling GpsPoller...")
                gpsPoller.running = False
                gpsPoller.join()

        while True:
            speed = gpsd.fix.speed
            if math.isnan(speed):
                speed = 0
                red.publish('status', u'SPEED_UNKNOWN')
            speed = math.floor(speed * 2.237)
            
            dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': speed})
            red.publish('speed', u'{}'.format(dump))
            
            if speed == 0:
                red.publish('status', u'READY')
                self.startTime = time.time()
                self.started = True
                self.finished = False
                self.prev_speed = 0
                self.data = {}
            elif self.started:
                if speed > self.prev_speed:
                    red.publish('status', u'TIMING')
                    self.prev_speed = speed
                    if speed >= 30 and '30' not in self.data:
                        diff = time.time() - self.startTime
                        self.data['30'] = diff
                        dump = json.dumps({'30': diff})
                        red.publish('result', u'{}'.format(dump))
                    if speed >= 60 and '60' not in self.data:
                        self.finished = True
                        diff = time.time() - self.startTime
                        self.data['60'] = diff
                        dump = json.dumps({'60': diff})
                        red.publish('result', u'{}'.format(dump))
                else:
                    self.prev_speed = 0
                    self.started = False
                    #if '30' not in data:
                    #    data['30'] = 'N/A'
                    #if '60' not in data:
                    #    data['60'] = 'N/A'
                    #yield "data: 30: {}\t60: {}\n\n".format(data['30'], data['60'])
                if self.finished:
                    red.publish('status', u'FINISHED')
            elif not self.finished:
                red.publish('status', u'NOT_READY')
            
            #time.sleep(0.1)

class ModeThreader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.mode = None

        self.current_value = None
        self.running = True
 
    def run(self):
        global gpsPoller
        if not gpsPoller or not gpsPoller.running:
            try
                gpsPoller = GpsPoller()
                gpsPoller.start()
            except (KeyboardInterrupt, SystemExit):
                print("\nKilling GpsPoller...")
                gpsPoller.running = False
                gpsPoller.join()

        while True:
            if self.mode != gpsPoller.mode:
                self.mode = gpsPoller.mode
                red.publish('mode', self.mode)

            time.sleep(1)

def start():
    modeThreader = ModeThreader()
    speedThreader = speedThreader()
    try:
        modeThreader.start()
        speedThreader.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nKilling threads...")
        modeThreader.running = False
        modeThreader.join()
        speedThreader.running = False
        speedThreader.join()
