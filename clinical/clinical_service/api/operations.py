# pylint: disable=invalid-name
# pylint: disable=C0301
"""
Implement endpoints of model service
"""
import json
import requests
from tornado.options import options
from connexion import request
from .logging import apilog, logger
from .logging import structured_log as struct_log
from .models import Error, Individual


def _request_failed(msg, url, **kwargs):
    """
    Generate standard log message + request error for error:
    Internal error performing search

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = f'request failed: {url}, {msg}'
    logger().error(struct_log(action=report, **kwargs))
    return Error(message=msg, code=500)


@apilog
def get_individuals(whereConditions=None):
    """
    Return all individuals, possibly selecting by provided conditions
    """
    headers = request.headers
    url = f"http://{options.sql_server}/lists/individuals"
    try:
        r = requests.get(url, headers=headers)
    except Exception as e: 
        err = _request_failed(str(e), url, exception=str(e))
        return err, 500

    if r.status_code >= 500:
        err = _request_failed(r.text, url)
        return err, 500

    if r.status_code in [401, 403]:
        err = Error(message=f"Authorization failed", code=r.status_code)
        return err, r.status_code

    items = r.json()['result']
    logger().info(f"{items}")
    individuals = [Individual(**item) for item in items]

    return individuals, 200


@apilog
def get_one_individual(individual_id):
    """
    Return single individual object
    """
    headers = request.headers
    url = f"http://{options.sql_server}/items/individuals/{individual_id}"
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        err = Error(message="connection failed" +
                    str(individual_id) + " " +
                    str(e))
        return err, 500

    if r.status_code >= 500:
        err = Error(message=f"SQL query failed {r.text}", code=500)
        return err, 500

    if r.status_code == 404:
        err = Error(message=f"Not found {individual_id}", code=404)
        return err, 404

    if r.status_code in [401, 403]:
        err = Error(message=f"Authorization failed", code=r.status_code)
        return err, r.status_code

    individual = Individual(**r.json()['result'])
    #return json.dumps(individual.marshal()), 200
    return individual, 200