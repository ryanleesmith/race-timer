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

        self.start = 0
        self.started = False
        self.finished = False
        self.prev_speed = 0
        self.data = {}

        self.current_value = None
        self.running = True
 
    def run(self):
        global poller, mode
        poller = Poller()
        try:
            poller.start()
            while True:
                if gpsd.fix.mode != mode:
                    mode = gpsd.fix.mode
                    red.publish('mode', mode)

                speed = gpsd.fix.speed
                if math.isnan(speed):
                    speed = 0
                    red.publish('status', u'SPEED_UNKNOWN')
                speed = math.floor(speed * 2.237)
                
                dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': speed})
                red.publish('speed', u'{}'.format(dump))
                
                if speed == 0:
                    red.publish('status', u'READY')
                    start = time.time()
                    started = True
                    finished = False
                    prev_speed = 0
                    data = {}
                elif started:
                    if speed > prev_speed:
                        red.publish('status', u'TIMING')
                        prev_speed = speed
                        if speed >= 30 and '30' not in data:
                            diff = time.time() - start
                            data['30'] = diff
                            dump = json.dumps({'30': diff})
                            #yield 'event: RESULT\ndata: {}\n\n'.format(dump)
                        if speed >= 60 and '60' not in data:
                            finished = True
                            diff = time.time() - start
                            data['60'] = diff
                            dump = json.dumps({'60': diff})
                            #yield 'event: RESULT\ndata: {}\n\n'.format(dump)
                    else:
                        prev_speed = 0
                        started = False
                        #if '30' not in data:
                        #    data['30'] = 'N/A'
                        #if '60' not in data:
                        #    data['60'] = 'N/A'
                        #yield "data: 30: {}\t60: {}\n\n".format(data['30'], data['60'])
                    if finished:
                        red.publish('status', u'FINISHED')
                elif not finished:
                    red.publish('status', u'NOT_READY')
                
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
