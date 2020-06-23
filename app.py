from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/stream")
def stream():
    def eventStream():
        while True:
            yield "Hello"
    
    return Response(eventStream(), mimetype="text/event-stream")