FROM python:3-alpine
ADD . /usr/src/axis_exporter
RUN pip3 install -e /usr/src/axis_exporter
ENTRYPOINT ["axis-exporter"]
EXPOSE 9416
