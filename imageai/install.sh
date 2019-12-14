#!/bin/bash -x

virtualenv venv

. venv/bin/activate

pip install -r requirements.txt

curl -L -o yolo.h5 https://github.com/OlafenwaMoses/ImageAI/releases/download/1.0/yolo.h5

