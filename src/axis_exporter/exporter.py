"""
Pulls data from specified Axis camera and presents as Prometheus metrics
"""
from _socket import gaierror
import os
import sys

import requests
from requests.auth import HTTPDigestAuth
import time
from . import prometheus_metrics
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from socketserver import ForkingMixIn
from prometheus_client import generate_latest, Summary
from urllib.parse import parse_qs
from urllib.parse import urlparse

TEMPERATURE_API="/axis-cgi/temperaturecontrol.cgi?action=statusall"
PARAMETER_LIST_API="/axis-cgi/param.cgi?action=list"

def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary(
    'request_processing_seconds', 'Time spent processing request')


def parse_response(response):
    # Split the text into lines
    lines = response.strip().split('\n')
    
    # Initialize an empty dictionary
    data = {}
    
    # Loop over the lines
    for line in lines:
        # Split each line into key and value using the first '=' delimiter
        key, value = line.split('=', 1)

        # Split the key into its components
        components = key.split('.')
        
        # Initialize a nested dictionary based on the components of the key
        d = data
        for component in components[:-1]:
            if component not in d:
                d[component] = {}
            d = d[component]
        
        # Assign the value to the final key in the nested dictionary
        d[components[-1]] = value.strip()
    
    return data

class ForkingHTTPServer(ForkingMixIn, HTTPServer):
    max_children = 30
    timeout = 30

class RequestHandler(BaseHTTPRequestHandler):
    """
    Endpoint handler
    """
    def return_error(self):
        self.send_response(500)
        self.end_headers()

    def do_GET(self):
        """
        Process GET request

        :return: Response with Prometheus metrics
        """
        # this will be used to return the total amount of time the request took
        start_time = time.time()
        # get parameters from the URL
        url = urlparse(self.path)
        # following boolean will be passed to True if an error is detected during the argument parsing
        error_detected = False
        query_components = parse_qs(urlparse(self.path).query)

        camera_host = None
        camera_port = None
        camera_user = os.getenv('AXIS_USERNAME')
        camera_password = os.getenv('AXIS_PASSWORD')
        camera_proto = None
        try:
            camera_host = query_components['camera_host'][0]
            camera_port = int(query_components['camera_port'][0])
            camera_proto = query_components['camera_proto'][0]
        except KeyError as e:
            print_err("missing or invalid parameter %s" % e)
            self.return_error()
            error_detected = True

        if camera_user is None:
            try:
                camera_user = query_components['camera_user'][0]
            except KeyError as e:
                print_err("missing parameter %s" % e)
                self.return_error()
                error_detected = True

        if camera_password is None:
            try:
                camera_password = query_components['camera_password'][0]
            except KeyError as e:
                print_err("missing parameter %s" % e)
                self.return_error()
                error_detected = True


        if url.path == self.server.endpoint and camera_host and camera_user and camera_password and camera_port and camera_proto is not None:

            camera_url = "{}://{}:{}".format(camera_proto, camera_host, camera_port)
            
            request_url = camera_url + PARAMETER_LIST_API
            response = requests.get(request_url, auth=HTTPDigestAuth(camera_user, camera_password))
            data = parse_response(response.text)

            model = data['root']['Brand']['ProdNbr']

            request_url = camera_url + TEMPERATURE_API
            response = requests.get(request_url, auth=HTTPDigestAuth(camera_user, camera_password))
            data = parse_response(response.text)

            for _, sensor in data['Sensor'].items():
                prometheus_metrics.axis_temp_gauge.labels(product_name=model,
                                                          node=camera_host,
                                                          sensor_name=sensor['Name']).set(sensor['Fahrenheit'])

            for heater_id, heater in data['Heater'].items():
                if heater['Status'] == "Stopped":
                    heater_state = 0
                elif heater['Status'] == "Running":
                    heater_state = 1
                else:
                    heater_state = 2

                prometheus_metrics.axis_heater_status.labels(product_name=model,
                                                             node=camera_host,
                                                             heater_id=heater_id).set(heater_state)

                prometheus_metrics.axis_heater_timer.labels(product_name=model,
                                                            node=camera_host,
                                                            heater_id=heater_id).set(heater['TimeUntilStop'])

            # get the amount of time the request took
            REQUEST_TIME.observe(time.time() - start_time)

            # generate and publish metrics
            metrics = generate_latest(prometheus_metrics.registry)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics)

        elif url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write("""<html>
            <head><title>Axis Communications Camera Exporter</title></head>
            <body>
            <h1>Axis Communications Camera Exporter</h1>
            <p>Visit <a href="/metrics">Metrics</a> to use.</p>
            </body>
            </html>""")

        else:
            if not error_detected:
                self.send_response(404)
                self.end_headers()


class ExporterServer(object):
    """
    Basic server implementation that exposes metrics to Prometheus
    """

    def __init__(self, address='0.0.0.0', port=9312, endpoint="/metrics"):
        self._address = address
        self._port = port
        self.endpoint = endpoint

    def print_info(self):
        print_err("Starting exporter on: http://{}:{}{}".format(self._address, self._port, self.endpoint))
        print_err("Press Ctrl+C to quit")

    def run(self):
        self.print_info()

        server = ForkingHTTPServer((self._address, self._port), RequestHandler)
        server.endpoint = self.endpoint

        try:
            while True:
                server.handle_request()
        except KeyboardInterrupt:
            print_err("Killing exporter")
            server.server_close()
