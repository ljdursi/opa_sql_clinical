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
from .opa.opa import query_http as opa_query

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
            claim = header[len(claim_prefix):].lower().replace('-','_')
            claims.append({"name": claim, "jwt": value})

    return claims

def check_tokens(method, path):
    user = _get_id_token()
    entitlements = _get_claims_tokens()
    result = opa_query(path='filtering', query='valid_tokens',
                         input={'method': method, 'path': path, 'user': user,
                                'entitlements': entitlements})
    return result


def list_authorization(method, path, table, **kwargs):
    user = _get_id_token()
    entitlements = _get_claims_tokens()
    result = opa_compile(q='data.filtering.allow==true',
                         input={'method': method, 'path': path, 'user': user,
                                'entitlements': entitlements, **kwargs},
                         unknowns=[table, 'consents'],
                         from_table=table)
    return result


def item_authorization(method, path, table, **kwargs):
    user = _get_id_token()
    entitlements = _get_claims_tokens()
    result = opa_query(path='filtering', query='allow', 
                         input={'method': method, 'path': path, 'user': user,
                                'entitlements': entitlements, **kwargs})
    return result


def validate_authorization(method, path, table, query_type='list', **kwargs):
    if not table in TABLES:
        return False, 'Not found', 404, None
    
    if not check_tokens(method, path):
        return False, 'Unauthorized', 401, None

    if query_type == 'list':
        auth = list_authorization(method, path, table)
        if not auth.defined:
            return False, 'Not authorized', 403, None

        join_clauses = [clause.sql() for clause in auth.sql.clauses]
        if not all([clause.startswith("INNER JOIN") for clause in join_clauses]):
            return False, 'Do not know how to handle non-join clauses yet', 501, None

        return True, auth, 200, join_clauses
    else:
        auth = item_authorization(method, path, table, **kwargs)
        if not auth:
            return False, 'Not authorized', 403, None

        return True, auth, 200, None


def construct_list_query(SELECT, FROM, join_clauses, WHERE=None):
    base_query = text(f"SELECT {FROM}.* FROM {FROM}")

    subqueries = [text(f"{base_query} {joinclause}") for joinclause in join_clauses]
    if WHERE:
        subqueries = [text(f"{subquery} WHERE {WHERE}") for subquery in subqueries]

    query = text(f"SELECT {SELECT} FROM ({subqueries[0]}")
    for subquery in subqueries[1:]:
        query = text(f"{query} UNION {subquery}")

    query = text(f"{query});")
    return query


@app.route('/lists/<resource>')
def query_list(resource):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()

    success, msg, code, join_clauses = validate_authorization(method, path, table, query_type='list')
    if not success:
        return msg, code

    args = request.args
    if 'select' not in args.keys():
        select = "*"
    else:
        select_fields = [unquote(field) for field in args['select'].strip().split(',')]
        select = ",".join(select_fields)

    if 'where' not in args.keys():
        where = None
    else:
        where = unquote(args['where'])

    list_query = construct_list_query(select, table, join_clauses, WHERE=where)
    rows = SESSION.execute(list_query).fetchall()
    columns = SESSION.execute(list_query).keys()
    result = [ {key: value for (key, value) in zip(columns, r)} for r in rows ] 

    return jsonify(result=result), 200


@app.route('/items/<resource>/<id>')
def query_id(resource, id):
    path = request.path.split('/')[2:]
    method = request.method
    table = resource.strip()

    # first find the consents for this item
    consents_query = text(f"SELECT consents.project FROM consents INNER JOIN {table} on {table}.id == consents.id WHERE {table}.id=\"{id}\"")
    consents = SESSION.execute(consents_query).fetchall()
    consents = list(set([consent[0] for consent in consents]))

    if not consents:
        return "Not found", 404

    success, msg, code, _ = validate_authorization(method, path, table, query_type='item', consents=consents)
    if not success:
        return msg, code

    # successfully authorized!  Look up and return the actual entry
    item_query = text(f"SELECT {table}.* FROM {table} WHERE {table}.id=\"{id}\"")
    item = SESSION.execute(item_query).fetchall()
    item_columns = SESSION.execute(item_query).keys()
    app.logger.info(item)

    result = {key: value for (key, value) in zip(item_columns, item[0])}
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