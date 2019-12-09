import io
import numpy as np
import sys
import time
import cv2
import umsgpack
import datetime

from imageai.Detection import ObjectDetection
from kafka import KafkaProducer
from kafka import KafkaConsumer

import traceback

in_topic = "distributed-video1"
out_topic = "imageai-video1"

detector = ObjectDetection()

detector.setModelTypeAsYOLOv3()
detector.setModelPath("yolo.h5")
detector.loadModel()


def analyzeImages():
    """
    Start analyzing images
    """
    print('Start analyzing images...')

    # Start up consumer
    consumer = KafkaConsumer(in_topic, bootstrap_servers=['localhost:9092'],
                             value_deserializer=lambda m: umsgpack.unpackb(m))

    # Start up producer
    producer = KafkaProducer(bootstrap_servers='localhost:9092',
                             value_serializer=lambda v: umsgpack.packb(v))

    try:
        while(True):
            for msg in consumer:
                byteStream = io.BytesIO(msg.value['image'])
                originalTime = msg.value['time']
                image = np.asarray(bytearray(byteStream.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

                imageai_frame, detection = detector.detectObjectsFromImage(
                    input_image=image, input_type='array', output_image_path="./result.jpg", output_type='array')
                imageTime = datetime.datetime.now()

                print("--------------------------------")
                identified_objects = []
                print(imageTime)
                for eachObject in detection:
                    print(eachObject["name"], " : ", eachObject["percentage_probability"],
                          " : ", eachObject["box_points"])
                    identified_objects.append(
                        {'name': eachObject["name"],
                         'percentage_probability': eachObject["percentage_probability"],
                         'position': [int(eachObject["box_points"][0]),
                                      int(eachObject["box_points"][1]),
                                      int(eachObject["box_points"][2]),
                                      int(eachObject["box_points"][3])]})
                print("--------------------------------\n\r")

                # Convert image to png
                ret, buffer = cv2.imencode('.jpg', imageai_frame)
                # Convert to bytes and send to kafka
                producer.send(out_topic, {'image': buffer.tobytes(),
                                          'time': imageTime,
                                          'original_time': originalTime,
                                          'details': identified_objects})

    except Exception as e:
        traceback.print_exc()
        print("\nExiting.")
        sys.exit(1)


if __name__ == '__main__':

    analyzeImages()
