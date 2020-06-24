from gps import *
import math
import time
import json

def timer():
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

    start = 0
    started = False
    curr_speed = 0
    prev_speed = 0
    data = {}

    try:
        while True:
            report = gpsd.next()
            if report['class'] == 'TPV':
                speed = float(getattr(report, 'speed', 'nan'))
                if math.isnan(speed):
                    speed = 0
                    yield 'event: STATUS\ndata: SPEED_UNKNOWN\n\n'

                curr_speed = math.floor(speed * 2.237)
                dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': curr_speed})
                yield 'event: SPEED\ndata: {}\n\n'.format(dump)

                if curr_speed == 0:
                    yield 'event: STATUS\ndata: READY\n\n'
                    start = time.time()
                    started = True
                    prev_speed = 0
                    data = {}
                elif started:
                    #yield "data: Timing...\n\n"
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
                        if '30' not in data:
                            data['30'] = 'N/A'
                        if '60' not in data:
                            data['60'] = 'N/A'
                        #yield "data: 30: {}\t60: {}\n\n".format(data['30'], data['60'])
                #else:
                    #yield "data: Come to stop\n\n"
            time.sleep(.1)
    except (KeyboardInterrupt, SystemExit):
        print("Done.\nExiting.")