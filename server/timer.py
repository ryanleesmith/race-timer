from gps import *
import math
import time

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

speed = 0
start = 0
started = False
curr_speed = 0
prev_speed = 0
data = {}

try:
    while True:
        report = gpsd.next()
        if report['class'] == 'TPV':
            #speed = float(getattr(report, 'speed', 'nan'))
            speed += .3
            if not math.isnan(speed):
                curr_speed = speed * 2.237
                #print('%.2f' % (curr_speed))
                if math.floor(curr_speed) == 0:
                    print("Starting")
                    start = time.time()
                    started = True
                    prev_speed = 0
                    data = {}
                elif started:
                    #print('%.2f %.2f' % (curr_speed, prev_speed))
                    if curr_speed > 61:
                        curr_speed = 0
                    if curr_speed > prev_speed:
                        prev_speed = curr_speed
                        if curr_speed >= 30 and '30' not in data:
                            diff = time.time() - start
                            data['30'] = diff
                        if curr_speed >= 60 and '60' not in data:
                            diff = time.time() - start
                            data['60'] = diff
                    else:
                        speed = 0
                        curr_speed = 0
                        prev_speed = 0
                        started = False
                        for key in data:
                            print('%s: %.2f' % (key, data[key]))


        time.sleep(.1)
except (KeyboardInterrupt, SystemExit):
    print("Done.\nExiting.")