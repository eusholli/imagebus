#!/bin/bash

tput setaf 7
echo "Starting imagebus processes..."

echo "Starting kafka"
docker-compose down
docker-compose up > /dev/null &
echo "Wait 15 seconds to allow kafka to start..."
sleep 15

echo "Starting consumer"
cd consumer
. venv/bin/activate
python app.py &
deactivate
cd ..

echo "Starting producer"
cd producer
. venv/bin/activate
python producer.py &
deactivate
cd ..

echo "Starting imageaiProcessor"
cd imageai
. venv/bin/activate
python imageaiProcessor.py &

echo "Starting redaction"
python redaction.py &
deactivate
cd ..

echo "All running..."
