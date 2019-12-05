import sys
import os
import logging
import json
import argparse
from urllib.parse import unquote

from flask import Flask, request, jsonify
from sqlalchemy.sql import text
from .orm import init_db, get_session, tables
from .opa.opa import compile as opa_compile

TABLES = None
SESSION = None
app = Flask(__name__)


def _get_id_token():
    if not 'Authorization' in request.headers:
        return None

    parts = request.headers['Authorization'].split()
    if len(parts) <= 1:
        return None

    return parts[-1]


def _get_claims_tokens():
    claims = []

    claim_prefix = 'X-Claim-'
    for header, value in request.headers.items():
        if header.startswith(claim_prefix):
            claims.append(value)

    return claims

def _unique_dictionaries(list_of_dicts):
    frozensets = [frozenset(d.items()) for d in list_of_dicts]
    frozensets_set = set(frozensets)
    return [dict(fs) for fs in frozensets]


def authorization(method, path, table):
    user = _get_id_token()
    entitlements = _get_claims_tokens()
    result = opa_compile(q='data.filtering.allow==true',
                         input={'method': method, 'path': path, 'user': user,
                                'entitlements': entitlements},
                         unknowns=[table, 'consents'],
                         from_table=table)
    return result

def validate_authorization(method, path, table):
    app.logger.info("In validate")
    if not table in TABLES:
        return False, 'Not found', 404
    
    app.logger.info("table name = %s", table)
    auth = authorization(method, path, table)
    if not auth.defined:
        return False, 'Not authorized', 403

    app.logger.info("auth_defined = %s", str(auth.defined))

    join_clauses = [clause.sql() for clause in auth.sql.clauses]
    app.logger.info(f"join_clauses = {join_clauses}")
    if not all([clause.startswith("INNER JOIN") for clause in join_clauses]):
        return False, 'Do not know how to handle non-join clauses yet', 501

    app.logger.info("About to return true")
    return True, auth, join_clauses

@app.route('/lists/<resource>')
def query_list(resource):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()

    success, msg, result = validate_authorization(method, path, table)
    if not success:
        return msg, result

    join_clauses = result

    args = request.args
    if 'select' not in args.keys():
        select = table+".*"
    else:
        select_fields = [unquote(field) for field in args['select'].strip().split(',')]
        select = ",".join(select_fields)

    if 'where' not in args.keys():
        where = None
    else:
        where = unquote(args['where'])

    result = []
    for join_clause in join_clauses:
        if where:
            query = text(f"SELECT {select} FROM {table} {join_clause} WHERE {where};")
        else:
            query = text(f"SELECT {select} FROM {table} {join_clause};")

        app.logger.info(str(query))
        rows = SESSION.execute(query).fetchall()
        columns = SESSION.execute(query).keys()
        result += [ {key: value for (key, value) in zip(columns, r)} for r in rows ] 


    result = _unique_dictionaries(result)
    return jsonify(result=result), 200


@app.route('/items/<resource>/<id>')
def query_id(resource, id):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()

    success, msg, result = validate_authorization(method, path, table)
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
    parser.add_argument('--host', default="localhost")
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

    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()