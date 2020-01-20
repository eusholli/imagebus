from flask_socketio import SocketIO, emit
from flask import Flask, Response, render_template
from kafka import KafkaProducer
import jsonpickle
import sys
from base64 import b64decode


sys.path.append("../common")
from imagebusutil import FrameDetails, ImagebusTopic  # noqa

# Start up producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: jsonpickle.encode(v).encode("utf-8"),
)


def create_app():
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    return app


app = create_app()
socketio = SocketIO(app)

# for CORS
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,POST"
    )  # Put any other methods you need here
    return response


@app.route("/")
def index():
    return render_template("index.html")


# Handler for a message recieved over 'connect' channel
@socketio.on("connect")
def handle_connect():
    print("received connect")


@socketio.on("frame")
def process_frame(data):
    # print("getting frame: " + data["imageURI"])
    frameDetails = FrameDetails(
        name=data["name"],
        frameRate=int(data["frameRate"]),
        url="",
        topic=data["topic"],
    )

    # Where I am - convert dataURI to bytes
    header, encoded = data["imageURI"].split(",", 1)
    imageBytes = b64decode(encoded)
    frameDetails.setFrame(int(data["frameReference"]), imageBytes)
    producer.send(frameDetails.topic, frameDetails)
    emit("frame ack")


if __name__ == "__main__":
    # Set the consumer in a Flask App
    # app.run(host="0.0.0.0")

    # Start up producer
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: jsonpickle.encode(v).encode("utf-8"),
    )

    socketio.run(app, host="localhost", port=8080, debug=True)
