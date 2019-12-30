#!/bin/bash -x

echo "Kill imagebus processes..."

pkill -f app.py
pkill -f producer.py
pkill -f imageaiProcessor.py
pkill -f redaction.py

docker-compose down

echo "All killed"
