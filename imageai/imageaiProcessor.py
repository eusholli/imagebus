import traceback
import io
import numpy as np
import sys
import time
import cv2
import datetime
import jsonpickle
import argparse

from imageai.Detection import ObjectDetection
from kafka import KafkaProducer
from kafka import KafkaConsumer

sys.path.append("../common")
from imagebusutil import FrameDetails, ImagebusTopic  # noqa


def analyzeImages(consumer, producer, frameDetails):
    """
    Start analyzing images
    """
    print("Start analyzing images...")

    detector = ObjectDetection()
    detector.setModelTypeAsYOLOv3()
    detector.setModelPath("yolo.h5")
    detector.loadModel()

    try:
        frameReference = 0
        totalAnalysisTime = 0
        while True:
            for msg in consumer:
                parent = msg.value
                frameReference += 1
                byteStream = io.BytesIO(parent.image)
                originalTime = parent.dateTime
                image = np.asarray(bytearray(byteStream.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

                beforeDetection = time.process_time()
                imageai_frame, detection = detector.detectObjectsFromImage(
                    input_image=image, input_type="array", output_type="array"
                )
                detectionTime = time.process_time() - beforeDetection
                totalAnalysisTime += detectionTime
                imageTime = datetime.datetime.now()

                print("--------------------------------")
                identified_objects = []
                print(imageTime)
                for eachObject in detection:
                    print(
                        eachObject["name"],
                        " : ",
                        eachObject["percentage_probability"],
                        " : ",
                        eachObject["box_points"],
                    )
                    identified_objects.append(
                        {
                            "name": eachObject["name"],
                            "percentage_probability": round(
                                eachObject["percentage_probability"], 2
                            ),
                            "position": [
                                int(eachObject["box_points"][0]),
                                int(eachObject["box_points"][1]),
                                int(eachObject["box_points"][2]),
                                int(eachObject["box_points"][3]),
                            ],
                        }
                    )
                print("--------------------------------\n\r")

                # Convert image to png
                ret, buffer = cv2.imencode(".jpg", imageai_frame)
                # Convert to bytes and send to kafka
                frameDetails.setChildFrame(
                    frameReference,
                    buffer.tobytes(),
                    identified_objects,
                    parent,
                    round(detectionTime, 2),
                    round(totalAnalysisTime / frameReference, 2),
                )
                producer.send(frameDetails.topic, frameDetails)

    except Exception as e:
        traceback.print_exc()
        print("\nExiting.")
        sys.exit(1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="imageaiProcessor",
        description="start image recognition on incoming frames",
    )
    parser.add_argument(
        "-t",
        "--topic",
        default=ImagebusTopic.IMAGEAI_FRAME.name,
        help="set the topic name for publishing the feed, defaults to "
        + ImagebusTopic.IMAGEAI_FRAME.name,
    )

    parser.add_argument(
        "-i",
        "--input",
        default=ImagebusTopic.SOURCE_FRAME.name,
        help="set the topic name for reading the incoming feed, defaults to "
        + ImagebusTopic.SOURCE_FRAME.name,
    )

    args = parser.parse_args()

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

    frameDetails = FrameDetails(name="imageaiProcessor", topic=args.topic)
    analyzeImages(consumer, producer, frameDetails)
