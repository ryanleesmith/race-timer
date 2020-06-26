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
    pubsub.subscribe('mode', 'status', 'speed', 'result')
    while True:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            #print(message)
            #print(message['channel'])
            #print(message['channel'].decode('utf-8'))
            #print(message['data'])
            #print(message['data'].decode('utf-8'))
            if message['channel'].decode('utf-8') == 'mode':
                yield 'event: MODE\ndata: {}\n\n'.format(message['data'].decode('utf-8'))
            if message['channel'].decode('utf-8') == 'status':
                yield 'event: STATUS\ndata: {}\n\n'.format(message['data'].decode('utf-8'))
            if message['channel'].decode('utf-8') == 'speed':
                yield 'event: SPEED\ndata: {}\n\n'.format(message['data'].decode('utf-8'))
            if message['channel'].decode('utf-8') == 'result':
                yield 'event: RESULT\ndata: {}\n\n'.format(message['data'].decode('utf-8'))

if __name__ == 'app':
    poller.start()
