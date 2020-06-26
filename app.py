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
    for message in pubsub.listen():
        print(message)
        yield message

if __name__ == 'app':
    poller.start()
