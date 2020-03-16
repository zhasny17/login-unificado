import json

with open('utils/schemas.json', 'r') as f:
    schema = json.load(f)
    user_schema_insert = schema.get('user_schema_insert')
    user_schema_update = schema.get('user_schema_update')
