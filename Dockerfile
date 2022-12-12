FROM python:3.11-alpine

RUN pip install --no-cache-dir influxdb
RUN pip install --no-cache-dir influxdb_client

WORKDIR /usr/src/app

COPY dockerhub_influxdb2.py ./

CMD [ "python", "/usr/src/app/dockerhub_influxdb2.py" ]
