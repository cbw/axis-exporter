"""
Entrypoint for the application
"""

import argparse
from axis_exporter.exporter import ExporterServer

def main():
    parser = argparse.ArgumentParser(description='Exports Axis Communications IP camera metrics to Prometheus')

    parser.add_argument('--address', type=str, dest='address', default='0.0.0.0', help='address to serve on')
    parser.add_argument('--port', type=int, dest='port', default='9312', help='port to bind')
    parser.add_argument('--endpoint', type=str, dest='endpoint', default='/metrics',
                        help='endpoint where metrics will be published')

    args = parser.parse_args()

    exporter = ExporterServer(**vars(args))
    exporter.run()


if __name__ == '__main__':
    main()
