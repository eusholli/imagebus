#!/bin/bash

echo "Installing consumer"
cd consumer

virtualenv venv

. venv/bin/activate

pip install -r requirements.txt

deactivate

cd ..

echo "Installing producer"
cd producer

virtualenv venv

. venv/bin/activate

pip install -r requirements.txt

deactivate

cd ..

echo "Installing imageai"
cd imageai

virtualenv venv

. venv/bin/activate

pip install -r requirements.txt
curl -L -o yolo.h5 https://github.com/OlafenwaMoses/ImageAI/releases/download/1.0/yolo.h5

deactivate

cd ..

echo "Installation Complete"


