import json
from flask import make_response
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from utils.error_handler import BadRequestException

with open('utils/schemas.json', 'r') as f:
    schema = json.load(f)
    user_schema_insert = schema.get('user_schema_insert')
    user_schema_update = schema.get('user_schema_update')
    login_schema = schema.get('login_schema')


def validate_instance(payload, schema):
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as err:
        print(f'Payload invalido: {err.message}')
        raise BadRequestException(message=f'Payload invalido: {err.message}')


def return_no_content():
    res = make_response('', 204)
    return res
