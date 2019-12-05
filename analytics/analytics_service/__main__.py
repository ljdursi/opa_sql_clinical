#!/usr/bin/env python3
"""
Driver program for service
"""
import sys
import argparse
import logging
import pkg_resources
import connexion
from tornado.options import define


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run sql clinical service')
    parser.add_argument('--host', default="localhost")
    parser.add_argument('--port', default=4000)
    parser.add_argument('--sql_host', default="sql_clinical")
    parser.add_argument('--sql_port', default=3000)
    parser.add_argument('--logfile', default="./log/model_service.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    args = parser.parse_args(args)

    # set up the application
    app = connexion.FlaskApp(__name__, server='tornado')
    define("sql_server", args.sql_host+":"+str(args.sql_port))

    # configure logging
    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.app.logger.addHandler(log_handler)
    app.app.logger.setLevel(numeric_loglevel)

    # add the swagger APIs
    api_def = pkg_resources.resource_filename('analytics_service',
                                              'api/swagger.yaml')
    app.add_api(api_def, strict_validation=True, validate_responses=True)

    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
