# imagebus

Microservice Message Bus Design for edge analysis of video streams

## Introduction

A distributed design pattern is required to cope with the requirements of scale video analysis. There can be many other reasons for needing to keep video analytics at the edge beyond bandwidth, including privacy, control access, device simplification, and so on. This is the first design pattern being published as a result of the [Seamster](https://seamster.io) initiative - "Our purpose is to provide a clear, comprehensive understanding of the edge market and to support industry-wide adoption of edge-enabled technologies and innovations." Seamster defines the basic DNA behind every edge use case being discovered.
![Seamster edge use case DNA](dna.png "Seamster edge use case DNA")

This repo implements a simple example of a video processing toolchain that enables flexible deployment using a message bus for distribution. Find below the overall architecture of the solution.
![imagebus architecture](architecture.png "imagebus Design Architecture")

All implementation is in Python 3 but due to the neutrality of Kafka, all languages can be used and can all interwork. Objects are passed using [msgpack](https://msgpack.org) formatting.

## Prerequisites

```
# Python 3.6
$ python3 --version
Python 3.6.5

# Docker
$ docker --version
Docker version 19.03.2, build 6a30dfc

# Docker Compose
$ docker-compose --version
docker-compose version 1.24.1, build 4667896b

# java
$ java -version
openjdk version "12.0.2" 2019-07-16
OpenJDK Runtime Environment (build 12.0.2+10)
OpenJDK 64-Bit Server VM (build 12.0.2+10, mixed mode, sharing)

$ pip3 --version
pip 19.1.1

$ virtualenv --version
16.7.2

```

## Tested Environment

Operating system:

- macOS Mojave 10.14.6

## Installing

To get your code up and running, first let's clone the repo locally then compose the project:

```
$ cd <PATH_OF_CHOICE>
$ git clone https://github.com/eusholli/imagebus
$ cd imagebus/
```

There are 5 main processes in the repo

### Consumer

Consumer is a python flask/socketio app, app.py, that pulls the messages from the Kafka bus and makes them available via a webserver on localhost:5000. To install execute the following

```
$ cd consumer
$ chmod 755 install.sh
$ ./install.sh
$ cd ..
```

### Producer

Producer is a python executable, producer.py, that grabs images from a video stream, either from a local video file if passed as an argument, or the embedded camera if no argument passed, and publishes the frame to the kafka bus. It is set to pass every 30th frame to the Kafka bus from the video feed. To install execute the following

```
$ cd producer
$ chmod 755 install.sh
$ ./install.sh
$ cd ..
```

### ImageAI

ImageAI contains the executables that take the source frames from the producer, analyses them for any inclusion of identifiable features and publishes the wanted result back onto the kafka message bus based on the wanted function of the processing. The object identification uses the open source [imageAI](https://imageai.com) library that can identify up to 1000 objects from 80 different types in any one frame. OpenCV is used to manipulate the images for redaction implementation. There are two examples. imageaiProcessor.py takes the original captured frame, identifies objects and creates a new image with boxes around the identified objects and also outputs the details of the indentified objects. redactionProcessor.py takes the identified objects, looks for people and publishes a new image that blacks them out. To install execute the following

```
$ cd imageai
$ chmod 755 install.sh
$ ./install.sh
$ cd ..
```

### kafka

Kafka runs in a docker container. No additional execution should be required.

## Running

All processes need to run in parallel and are best started in individual terminals since the consumer, producer and imageai processes run inside their own individual virtual environments. The order in which the processes are started is important. The Kafka bus must be initialised first.

### Kafka Bus

Kafka runs in its own docker container and does not need any additional config. To run, stay in the root directory of the project and execute

```
$ docker-compose up
```

### Producer Shell

```
$ cd producer
$ . venv/bin/activate
$ python producer.py
```

### Imageai Shell

```
$ cd imageai
$ . venv/bin/activate
$ python imageaiProcessor.py &
$ python redactionProcessor.py &
```

### Consumer Shell

```
$ cd consumer
$ . venv/bin/activate
$ python app.py
```

To view the result go to [https://localhost:5000](https://localhost:5000)
