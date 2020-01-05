import traceback
import io
import sys
import time
import numpy as np
import cv2
import datetime
import jsonpickle
import argparse

from kafka import KafkaProducer
from kafka import KafkaConsumer

sys.path.append("../common")
from imagebusutil import FrameDetails, ImagebusTopic  # noqa


def redactImages(consumer, producer, frameDetails, redactedObjects):
    """
    Start redacting images
    """
    print("Start redacting images...")

    try:
        frameReference = 0
        totalAnalysisTime = 0
        # Black color in BGR
        color = (0, 0, 0)
        # Line thickness of 2 px
        thickness = -1

        while True:
            for msg in consumer:
                parent = msg.value
                frameReference += 1
                byteStream = io.BytesIO(parent.image)
                image = np.asarray(bytearray(byteStream.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

                beforeDetection = time.process_time()

                print("--------------------------------")

                details = parent.details
                for eachObject in details:
                    object_type = eachObject["name"]

                    if object_type in redactedObjects:
                        eachObject["redacted"] = True
                        print(object_type + " to be redacted...")
                        start_point = (
                            eachObject["position"][0],
                            eachObject["position"][1],
                        )
                        end_point = (
                            eachObject["position"][2],
                            eachObject["position"][3],
                        )
                        image = cv2.rectangle(
                            image, start_point, end_point, color, thickness
                        )

                print("--------------------------------\n\r")

                detectionTime = time.process_time() - beforeDetection
                totalAnalysisTime += detectionTime

                # Convert image to jpg
                ret, buffer = cv2.imencode(".jpg", image)
                # Convert to bytes and send to kafka
                frameDetails.setChildFrame(
                    frameReference,
                    buffer.tobytes(),
                    details,
                    parent,
                    round(detectionTime, 4),
                    round(totalAnalysisTime / frameReference, 4),
                )
                producer.send(frameDetails.topic, frameDetails)

    except Exception as e:
        traceback.print_exc()
        print("\nExiting.")
        sys.exit(1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="redaction", description="start redacting incoming frames"
    )

    parser.add_argument(
        "redactedObjects",
        nargs="*",
        help="list of objects to be redacted ex. person cup",
        default=["person"],
    )

    parser.add_argument(
        "-t",
        "--topic",
        default=ImagebusTopic.REDACTION_FRAME.name,
        help="set the topic name for publishing the feed, defaults to "
        + ImagebusTopic.REDACTION_FRAME.name,
    )

    parser.add_argument(
        "-i",
        "--input",
        default=ImagebusTopic.IMAGEAI_FRAME.name,
        help="set the topic name for reading the incoming feed, defaults to "
        + ImagebusTopic.IMAGEAI_FRAME.name,
    )

    parser.add_argument(
        "-n",
        "--name",
        help='set the display name of this redaction process, defaults to "redactionProcessor" if missing',
        default="redactionProcessor",
    )

    args = parser.parse_args()
    print(args.redactedObjects)

    # Start up consumer
    consumer = KafkaConsumer(
        args.input,
        bootstrap_servers=["localhost:9092"],
        value_deserializer=lambda m: jsonpickle.decode(m.decode("utf-8")),
    )

    # Start up producer
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: jsonpickle.encode(v).encode("utf-8"),
    )

    frameDetails = FrameDetails(name=args.name, topic=args.topic)
    redactImages(consumer, producer, frameDetails, args.redactedObjects)
