"""
API Data Model definitions
From Swagger file, with python classes via Bravado
"""

import pkg_resources
import yaml
from bravado_core.spec import Spec

#
# Read in the API definition, and parse it with Bravado
#
_API_DEF = pkg_resources.resource_filename('analytics_service',
                                           'api/swagger.yaml')
_SPEC_DICT = yaml.safe_load(open(_API_DEF, 'r'))

_BRAVADO_CONFIG = {
    'validate_requests': False,
    'validate_responses': False,
    'use_models': True,
    'validate_swagger_spec': True
}

_SWAGGER_SPEC = Spec.from_dict(_SPEC_DICT, config=_BRAVADO_CONFIG)

#
# Generate the Python models from the spec
#

BASEPATH = _SWAGGER_SPEC.flattened_spec['basePath']
Count = _SWAGGER_SPEC.definitions['Count']  # pylint:disable=invalid-name
Fraction = _SWAGGER_SPEC.definitions['Fraction']  # pylint:disable=invalid-name
Error = _SWAGGER_SPEC.definitions['Error']  # pylint:disable=invalid-name
