from flask import Flask, render_template, Response
from gps import *
from timer import timer
import poller
import math
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(timer(), mimetype='text/event-stream')

if __name__ == '__main__':
    poller.start()
