import sys
import datetime
import time
import cv2
import json
import pickle
import umsgpack
from kafka import KafkaProducer
import traceback

topic = "distributed-video1"
# Start up producer
producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: umsgpack.packb(v))


def getCurrentTime():
    now = datetime.datetime.now()
    return now
    # return now.strftime("%A, %d %B, %Y at %X")


def publish_video(video_file):
    """
    Publish given video file to a specified Kafka topic.
    Kafka Server is expected to be running on the localhost. Not partitioned.

    :param video_file: path to video file <string>
    """
    # Open file
    video = cv2.VideoCapture(video_file)

    print('publishing video...')

    frame_sample = 30

    while (video.isOpened()):
        count = 0
        while count < frame_sample:
            count += 1
            success, frame = video.read()

        imageTime = getCurrentTime()

        # Ensure file was read successfully
        if not success:
            print("bad read!")
            break

        # Convert image to png
        ret, buffer = cv2.imencode('.jpg', frame)

        # Convert to bytes and send to kafka
        producer.send(topic, {'image': buffer.tobytes(),
                              'time': imageTime})

        time.sleep(0.2)

    video.release()
    print('publish complete')


def publish_camera():
    """
    Publish camera video stream to specified Kafka topic.
    Kafka Server is expected to be running on the localhost. Not partitioned.
    """

    camera = cv2.VideoCapture(0)
    try:
        while(True):
            success, frame = camera.read()
            imageTime = getCurrentTime()

            ret, buffer = cv2.imencode('.jpg', frame)
            producer.send(topic, {'image': buffer.tobytes(),
                                  'time': imageTime})

            # Choppier stream, reduced load on processor
            time.sleep(3)

    except Exception as e:
        traceback.print_exc()
        print("\nExiting.")
        sys.exit(1)

    camera.release()


if __name__ == '__main__':
    """
    Producer will publish to Kafka Server a video file given as a system arg. 
    Otherwise it will default by streaming webcam feed.
    """
    if(len(sys.argv) > 1):
        video_path = sys.argv[1]
        publish_video(video_path)
    else:
        print("publishing feed!")
        publish_camera()
