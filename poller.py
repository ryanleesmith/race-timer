from gps import *
import math
import time
import json
import threading
import redis

gpsd = None
poller = None
mode = None

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

class Threader(threading.Thread):
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
        global poller, mode
        poller = Poller()
        speed = 0
        try:
            poller.start()
            while True:
                if gpsd.fix.mode != mode:
                    mode = gpsd.fix.mode
                    red.publish('mode', mode)

                #speed = gpsd.fix.speed
                if math.isnan(speed):
                    speed = 0
                    red.publish('status', u'SPEED_UNKNOWN')
                #speed = math.floor(speed * 2.237)
                
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

                speed = speed + 0.1
                if speed >= 62:
                    speed = 60
                
                time.sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            print("\nKilling Threader...")
            poller.running = False
            poller.join()

def start():
    threader = Threader()
    try:
        threader.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nKilling main...")
        threader.running = False
        threader.join()
