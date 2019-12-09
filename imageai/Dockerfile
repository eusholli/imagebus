FROM ufoym/deepo:cpu

RUN pip3 install -r requirements.txt

COPY . /app

WORKDIR "/app"
CMD ["python", "imageaiProcessor.py"]
