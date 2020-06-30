import json
from flask import make_response, abort
from jsonschema import validate
from jsonschema.exceptions import ValidationError

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
        abort(400)


def return_no_content():
    res = make_response('', 204)
    return res