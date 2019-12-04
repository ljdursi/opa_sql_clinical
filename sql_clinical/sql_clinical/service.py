import sys
import os
import logging
import argparse

from flask import Flask, request, jsonify
from flask.logging import default_handler
from .orm import init_db, get_session, tables
from .opa.opa import compile
from sqlalchemy.sql import text

TABLES = None
SESSION = None
app = Flask(__name__)

def authorization(method, path, table, entitlement):
    result = compile(q='data.filtering.allow==true',
                     input={'method': method, 'path': path,
                            'consent': entitlement},
                     unknowns=[table, 'consents'],
                     from_table=table)
    return result

def validate_authorization(method, path, table, entitlement):
    app.logger.info("In validate")
    if not table in TABLES:
        return False, 'Not found', 404
    
    app.logger.info("table name = ", table)
    auth = authorization(method, path, table, 'SecondaryB')
    if not auth.defined:
        return False, 'Not authorized', 403

    app.logger.info("auth_defined = ", auth.defined)
    if len(auth.sql.clauses) > 1:
        return False, 'Do not know how to handle multiple clauses yet', 501

    join_clause = auth.sql.clauses[0].sql()
    app.logger.info("join_clasue = ", join_clause)
    if not join_clause.startswith("INNER JOIN"):
        return False, 'Do not know how to handle non-join clauses yet', 501

    app.logger.info("About to return true")
    return True, auth, join_clause

@app.route('/lists/<resource>')
def query_list(resource):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()
    authz = 'SecondaryB'

    success, msg, result = validate_authorization(method, path, table, authz)
    if not success:
        return msg, result

    join_clause = result

    args = request.args
    if 'select' not in args.keys():
        select = table+".*"
    else:
        select_fields = [table+"."+field for field in args['select'].strip().split(',')]
        select = ",".join(select_fields)

    if 'where' not in args.keys():
        where = None
    else:
        where = args['where']

    if where:
        query = text(f"SELECT {select} FROM {table} {join_clause} WHERE {where};")
    else:
        query = text(f"SELECT {select} FROM {table} {join_clause};")

    rows = SESSION.execute(query).fetchall()
    columns = SESSION.execute(query).keys()

    result = [ {key: value for (key, value) in zip(columns, r)} for r in rows ] 
    return jsonify(result=result), 200


@app.route('/items/<resource>/<id>')
def query_id(resource, id):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()
    authz = 'SecondaryB'

    success, msg, result = validate_authorization(method, path, table, authz)
    if not success:
        return msg, result

    join_clause = result

    # first do unauthorized count query so we can find the 
    # difference between a 404 (does not exist) and 
    # a 401 (forbidden)
    count_query = text(f"SELECT COUNT(id) FROM {table} where {table}.id=\"{id}\"")
    rows = SESSION.execute(count_query).fetchall()
    count = rows[0][0]
    app.logger.info(rows[0])
    if count == 0:
        return 'Not found', 404

    if count > 1:
        return 'Multiple objects with id, invalid query', 401

    query = text(f"SELECT {table}.* FROM {table} {join_clause} WHERE {table}.id=\"{id}\"")
    rows = SESSION.execute(query).fetchall()
    columns = SESSION.execute(query).keys()

    count = len(rows)
    if count == 0:
        return 'Forbidden', 401

    result = {key: value for (key, value) in zip(columns, rows[0])}
    return jsonify(result=result), 200

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    def_opa_server = os.getenv('OPA_ADDR', 'http://127.0.0.1:8181')
    parser = argparse.ArgumentParser('Run sql clinical service')
    parser.add_argument('--database', default="./data/model_service.sqlite")
    parser.add_argument('--port', default=3000)
    parser.add_argument('--opa', default=def_opa_server)
    parser.add_argument('--logfile', default="./log/model_service.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    args = parser.parse_args(args)

    # set up the application
    app.config['dbfile'] = args.database
    app.config['opa_server'] = args.opa

    @app.teardown_appcontext
    def shutdown_session(exception=None):  # pylint:disable=unused-variable,unused-argument
        """
        Tear down the DB session
        """
        SESSION.remove()

    # configure logging
    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.logger.addHandler(log_handler)
    app.logger.setLevel(numeric_loglevel)

    init_db('sqlite:///'+args.database)
    global SESSION
    SESSION = get_session()
    global TABLES
    TABLES = set(tables()) - {'consents'}
#    TABLES = {'individuals'}

    app.run(port=args.port)


if __name__ == "__main__":
    main()