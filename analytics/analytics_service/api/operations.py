# pylint: disable=invalid-name
# pylint: disable=C0301
"""
Implement endpoints of model service
"""
import requests
from tornado.options import options
from connexion import request
from urllib.parse import quote
from .logging import apilog, logger
from .logging import structured_log as struct_log
from .models import Error, Count, Fraction

def _first_dictionary_value(d):
    if not isinstance(d, dict):
        return None
    if len(d) == 0:
        return None
    values = list(d.values())
    return values[0]

@apilog
def get_healthy_fraction():
    """
    Return fraction of healthy participants
    """
    headers = request.headers
    url = f"http://{options.sql_server}/lists/individuals"
    total_url = f"{url}?select=count(individuals.id)"
    healthy_url = f"""{total_url}&where={quote('individuals.status="Healthy"')}"""
    try:
        r_total = requests.get(total_url, headers=headers)
        total = float(_first_dictionary_value(r_total.json()['result'][0]))
        logger().info(f"Making query: {total_url}")
        r_healthy = requests.get(healthy_url, headers=headers)
        healthy = float(_first_dictionary_value(r_healthy.json()['result'][0]))
        logger().info(f"Making query: {healthy_url}")
    except Exception as e: 
        err = Error(f'Could not query individuals: {e}', 500)
        return err, 500

    if total == 0:
        fraction = float('nan')
    else:
        fraction = healthy/total
    return Fraction(fraction_name="healthy_fraction", fraction=fraction), 200


@apilog
def get_number():
    """
    Return number of participants
    """
    headers = request.headers
    url = f"http://{options.sql_server}/lists/individuals"
    total_url = f"{url}?select=count(individuals.id)"
    logger().info(f"Making query: {total_url}")
    try:
        r_total = requests.get(total_url, headers=headers)
        total = int(_first_dictionary_value(r_total.json()['result'][0]))
    except Exception as e: 
        err = Error(f'Could not query individuals: {e}', 500)
        return err, 500

    return Count(count_name="available_individuals", count=total), 200