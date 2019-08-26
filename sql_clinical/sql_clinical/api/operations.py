# pylint: disable=invalid-name
# pylint: disable=C0301
"""
Implement endpoints of model service
"""
import os
import json
import requests
from sql_clinical import orm
from sql_clinical.orm import models
from sql_clinical.api.logging import apilog, logger
from sql_clinical.api.logging import structured_log as struct_log
from sql_clinical.api.models import Error, BASEPATH
from sql_clinical.orm.models import Individual, Consent


OPA_URL = os.environ.get("OPA_ADDR", "http://localhost:8181")
POLICY_PATH = os.environ.get("POLICY_PATH", "/v1/data/static/allow")


def _report_search_failed(typename, exception, **kwargs):
    """
    Generate standard log message + request error for error:
    Internal error performing search

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = typename + ' search failed'
    message = 'Internal error searching for '+typename+'s'
    logger().error(struct_log(action=report, exception=str(exception),
                              **kwargs))
    return Error(message=message, code=500)


def _report_update_failed(typename, exception, **kwargs):
    """
    Generate standard log message + request error for error:
    Internal error performing update (PUT)

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = typename + ' updated failed'
    message = 'Internal error updating '+typename+'s'
    logger().error(struct_log(action=report, exception=str(exception), **kwargs))
    return Error(message=message, code=500)


def check_auth(url, user, method, url_as_array, token):
    input_dict = {"input": {
        "user": user,
        "path": url_as_array,
        "method": method
    }}
    if token is not None:
        input_dict["input"]["token"] = token

    logger().info("Checking auth...")
    logger().info(json.dumps(input_dict, indent=2))
    try:
        rsp = requests.post(url, data=json.dumps(input_dict))
    except Exception as err:
        logger().info(err)
        return {}
    j = rsp.json()
    if rsp.status_code >= 300:
        err = _report_search_failed("Error checking auth, got status %s and message: %s" % (j.status_code, j.text))
        return err, 500
    logger().info("Auth response:")
    logger().info(json.dumps(j, indent=2))
    return j


@apilog
def get_individuals(whereConditions):
    """
    Return all individuals, possibly selecting by provided conditions
    """
    try:
        q = Individual().query.all()
    except orm.ORMException as e:
        err = _report_search_failed('individuals', e, individual_id="all")
        return err, 500

    return [orm.dump(p) for p in q], 200


@apilog
def get_one_individual(individual_id):
    """
    Return single individual object
    """
    url = OPA_URL + POLICY_PATH
    path = ["individuals", individual_id]
    user = "alice"
    researcher = True
    entitlements = ["primary", "secondaryA"]

    token = {"payload": {"researcher": researcher,
                         "entitlements": entitlements}}
    j = check_auth(url, user, "GET", path, token)
    try:
        result = j.get("result", {})
    except Exception as ex:
        err = Error(message="Authorization process failed" +
                     str(individual_id) + " " +
                     str(ex))
        return err, 500

    if result:
        logger().info("Get One Individual: Authz success.")
    else:
        err = Error(message="Authorization failed: "+str(individual_id),
                    code=403)
        return err, 403

    try:
        q = Individual().query.get(individual_id)
    except orm.ORMException as e:
        err = _report_search_failed('individual', e,
                                    individual_id=str(individual_id))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(individual_id),
                    code=404)
        return err, 404

    return orm.dump(q), 200
