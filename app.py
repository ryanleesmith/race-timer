from flask import Flask, render_template, Response
from gps import *
#from timer import timer
import poller
import math
import time
import redis

app = Flask(__name__)
red = redis.StrictRedis()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(streamer(), mimetype='text/event-stream')
    #return Response(timer(), mimetype='text/event-stream')

def streamer():
    pubsub = red.pubsub()
    pubsub.subscribe('mode', 'speed')
    while True:
        message = pubsub.get_message()
        if message['channel'].decode('utf-8') == 'speed':
            print(message)
            yield 'event: SPEED\ndata: {}\n\n'.format(message['data'].decode('utf-8'))

if __name__ == 'app':
    poller.start()
