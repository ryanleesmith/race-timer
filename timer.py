from gps import *
import math
import time
import json

def timer():
    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

    start = 0
    started = False
    finished = False
    prev_speed = 0
    data = {}

    speed = 0

    try:
        while True:
            report = gpsd.next()
            if report['class'] == 'TPV':
                #speed = float(getattr(report, 'speed', 'nan'))
                
                if math.isnan(speed):
                    speed = 0
                    yield 'event: STATUS\ndata: SPEED_UNKNOWN\n\n'

                #speed = math.floor(speed * 2.237)
                dump = json.dumps({'x': int(round(time.time() * 1000)), 'y': speed})
                yield 'event: SPEED\ndata: {}\n\n'.format(dump)

                if speed == 0:
                    yield 'event: STATUS\ndata: READY\n\n'
                    start = time.time()
                    started = True
                    finished = False
                    prev_speed = 0
                    data = {}
                elif started:
                    if speed > prev_speed:
                        yield 'event: STATUS\ndata: TIMING\n\n'
                        prev_speed = speed
                        if speed >= 30 and '30' not in data:
                            diff = time.time() - start
                            data['30'] = diff
                            dump = json.dumps({'30': diff})
                            yield 'event: RESULT\ndata: {}\n\n'.format(dump)
                        if speed >= 60 and '60' not in data:
                            finished = True
                            diff = time.time() - start
                            data['60'] = diff
                            dump = json.dumps({'60': diff})
                            yield 'event: RESULT\ndata: {}\n\n'.format(dump)
                    else:
                        prev_speed = 0
                        started = False
                        #if '30' not in data:
                        #    data['30'] = 'N/A'
                        #if '60' not in data:
                        #    data['60'] = 'N/A'
                        #yield "data: 30: {}\t60: {}\n\n".format(data['30'], data['60'])
                    if finished:
                        yield 'event: STATUS\ndata: FINISHED\n\n'
                elif not finished:
                    yield 'event: STATUS\ndata: NOT_READY\n\n'

                speed = speed + 0.75
                if speed >= 62:
                    speed = 60
            time.sleep(.5)
    except (KeyboardInterrupt, SystemExit):
        print("Done.\nExiting.")