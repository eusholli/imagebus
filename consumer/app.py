from flask_socketio import SocketIO, emit
from flask import Flask, Response, render_template, flash
from kafka import KafkaConsumer
import time
import datetime
import base64
import jsonpickle
import sys

sys.path.append("../common")
from imagebusutil import FrameDetails, ImagebusTopic  # noqa


def create_app(configfile=None):
    app = Flask(__name__)
    return app


app = create_app()
# socketio = SocketIO(app, logger=True, engineio_logger=True)
socketio = SocketIO(app)


app.jinja_env.auto_reload = True

consumer = KafkaConsumer(
    ImagebusTopic.SOURCE_FRAME.name,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: jsonpickle.decode(m.decode("utf-8")),
)

imageaiConsumer = KafkaConsumer(
    ImagebusTopic.IMAGEAI_FRAME.name,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: jsonpickle.decode(m.decode("utf-8")),
)

redactedConsumer = KafkaConsumer(
    ImagebusTopic.REDACTION_FRAME.name,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: jsonpickle.decode(m.decode("utf-8")),
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/imageai")
def imageai():
    return render_template("imageai.html")


@app.route("/redaction")
def redaction():
    return render_template("redaction.html")


# Handler for a message recieved over 'connect' channel
@socketio.on("connect")
def handle_connect():
    print("received connect")


original_frameDetails = None


@socketio.on("get original")
def process_original():
    print("getting original...")
    global original_frameDetails
    try:
        for msg in consumer:
            original_frameDetails = msg.value
            break
    except Exception as e:
        print("Exception fetching original")

    if original_frameDetails is not None:
        emit("original", {"from": original_frameDetails.createResponse()})
    else:
        emit("original")

    return


imageai_frameDetails = None


@socketio.on("get imageai")
def process_imageai():
    print("getting imageai...")
    global imageai_frameDetails
    try:
        for msg in imageaiConsumer:
            imageai_frameDetails = msg.value
            break

    except Exception as e:
        print("Exception fetching imageai")

    if imageai_frameDetails is not None:
        emit(
            "imageai",
            {
                "from": imageai_frameDetails.parent.createResponse(),
                "to": imageai_frameDetails.createResponse(),
            },
        )
    else:
        emit("imageai")

    return


redacted_FrameDetails = None


@socketio.on("get redacted")
def process_redacted():
    print("getting redacted...")
    global redacted_FrameDetails
    try:
        for msg in redactedConsumer:
            redacted_FrameDetails = msg.value
            break

    except Exception as e:
        print("Exception fetching redacted")

    if redacted_FrameDetails is not None:
        emit(
            "redacted",
            {
                "from": redacted_FrameDetails.parent.createResponse(),
                "to": redacted_FrameDetails.createResponse(),
            },
        )
    else:
        emit("redacted")

    return


if __name__ == "__main__":
    # Set the consumer in a Flask App
    # app.run(host="0.0.0.0")
    socketio.run(app, debug=True)
