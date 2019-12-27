from flask_socketio import SocketIO, emit
from flask import Flask, Response, render_template, flash
from kafka import KafkaConsumer
import umsgpack
import time
import datetime
import base64


def create_app(configfile=None):
    app = Flask(__name__)
    return app


app = create_app()
# socketio = SocketIO(app, logger=True, engineio_logger=True)
socketio = SocketIO(app)


@app.template_filter()
def datetimefilter(value, format='%Y/%m/%d %H:%M:%S.%f'):
    """convert a datetime to a different format."""
    return value.strftime(format)


app.jinja_env.filters['datetimefilter'] = datetimefilter

app.jinja_env.auto_reload = True

# Fire up the Kafka Consumer
original_topic = "distributed-video1"
imageai_topic = "imageai-video1"
redacted_topic = "redacted-video1"

consumer = KafkaConsumer(
    original_topic,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: umsgpack.unpackb(m),
)

imageaiConsumer = KafkaConsumer(
    imageai_topic,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: umsgpack.unpackb(m),
)

redactedConsumer = KafkaConsumer(
    redacted_topic,
    consumer_timeout_ms=500,
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: umsgpack.unpackb(m),
)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/home")
def home():
    return render_template('index.html')


@app.route("/details")
def details():
    return render_template('details.html')


@app.route("/redaction")
def redaction():
    return render_template('redaction.html')


# Handler for a message recieved over 'connect' channel
@socketio.on('connect')
def handle_connect():
    print('received connect')


original_msg = None
@socketio.on('get original')
def process_original():
    print("getting original...")
    global original_msg
    try:
        for msg in consumer:
            original_msg = msg
            break
    except Exception as e:
        print("Exception fetching imageai")

    if original_msg is not None:
        encoded_image = base64.b64encode(
            original_msg.value["image"]).decode('utf8')
        emit('original', {'image': "data:image/jpg;base64," +
                          encoded_image, 'time': datetimefilter(original_msg.value["time"])})
    else:
        emit('original')

    return


imageai_msg = None
@socketio.on('get imageai')
def process_imageai():
    print("getting imageai...")
    global imageai_msg
    try:
        for msg in imageaiConsumer:
            imageai_msg = msg
            break

    except Exception as e:
        print("Exception fetching imageai")

    if imageai_msg is not None:
        encoded_image = base64.b64encode(
            imageai_msg.value["image"]).decode('utf8')
        emit('imageai', {'image': "data:image/jpg;base64," +
                         encoded_image, 'time': datetimefilter(imageai_msg.value["time"]),
                         'original_time': datetimefilter(imageai_msg.value["original_time"]),
                         'details': imageai_msg.value["details"]})
    else:
        emit('imageai')

    return


imageai_msg = None
@socketio.on('get redacted')
def process_redacted():
    print("getting redacted...")
    global redacted_msg
    try:
        for msg in redactedConsumer:
            redacted_msg = msg
            break

    except Exception as e:
        print("Exception fetching redacted")

    if redacted_msg is not None:
        encoded_image = base64.b64encode(
            redacted_msg.value["image"]).decode('utf8')
        emit('redacted', {'image': "data:image/jpg;base64," +
                          encoded_image, 'time': datetimefilter(redacted_msg.value["time"]),
                          'original_time': datetimefilter(redacted_msg.value["original_time"]),
                          'details': redacted_msg.value["details"]})
    else:
        emit('redacted')

    return


if __name__ == "__main__":
    # Set the consumer in a Flask App
    # app.run(host="0.0.0.0")
    socketio.run(app, debug=True)
