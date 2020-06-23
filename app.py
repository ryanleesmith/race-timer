from flask import Flask, render_template, Response
from gps import *
from timer import stream
import math
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/stream")
def stream():
    def eventStream():
        while True:
            yield "Hello"
    
    return Response(stream(), mimetype="text/event-stream")
