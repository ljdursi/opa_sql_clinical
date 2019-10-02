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
import sql_clinical.orm


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run sql clinical service')
    parser.add_argument('--database', default="./data/model_service.sqlite")
    parser.add_argument('--port', default=3000)
    parser.add_argument('--tokens', action='store_true', default=False)
    parser.add_argument('--logfile', default="./log/model_service.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    args = parser.parse_args(args)

    # set up the application
    app = connexion.FlaskApp(__name__, server='tornado')
    define("dbfile", default=args.database)
    define("use_tokens", args.tokens)
    sql_clinical.orm.init_db()
    db_session = sql_clinical.orm.get_session()

    @app.app.teardown_appcontext
    def shutdown_session(exception=None):  # pylint:disable=unused-variable,unused-argument
        """
        Tear down the DB session
        """
        db_session.remove()

    # configure logging
    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.app.logger.addHandler(log_handler)
    app.app.logger.setLevel(numeric_loglevel)

    # add the swagger APIs
    api_def = pkg_resources.resource_filename('sql_clinical',
                                              'api/swagger.yaml')
    app.add_api(api_def, strict_validation=True, validate_responses=True)

    app.run(port=args.port)


if __name__ == "__main__":
    main()