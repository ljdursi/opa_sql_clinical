from __future__ import print_function
import sys
import logging
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import opa

app = Flask(__name__)
conn = create_engine('sqlite:///clinical_service.sqlite', echo=True)

TABLES = ['individuals']

def authorization(method, path, table, entitlement):
    result = opa.compile(q='data.filtering.allow==true',
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

    rows = conn.execute(query).fetchall()
    columns = conn.execute(query).keys()

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
    rows = conn.execute(count_query).fetchall()
    count = rows[0][0]
    app.logger.info(rows[0])
    if count == 0:
        return 'Not found', 404

    if count > 1:
        return 'Multiple objects with id, invalid query', 401

    query = text(f"SELECT {table}.* FROM {table} {join_clause} WHERE {table}.id=\"{id}\"")
    rows = conn.execute(query).fetchall()
    columns = conn.execute(query).keys()

    count = len(rows)
    if count == 0:
        return 'Forbidden', 401

    result = {key: value for (key, value) in zip(columns, rows[0])}
    return jsonify(result=result), 200


if __name__ == '__main__':
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run()