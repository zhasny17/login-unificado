from flask import Blueprint, abort, request, make_response
from datetime import datetime
import models
from . import user_schema_insert, user_schema_update
from jsonschema import validate
from jsonschema.exceptions import ValidationError

#############################################################################
#                                 VARIABLES                                 #
#############################################################################
bp = Blueprint('user', __name__)


#############################################################################
#                             HELPER FUNCTIONS                              #
#############################################################################
def jsonify_user(user):
    fmt_str = '%Y-%m-%d %H:%M:%S'
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'active': user.active,
        'admin': user.admin,
        'created_at': None if not user.created_at else datetime.strftime(user.created_at, fmt_str),
        'removed_at': None if not user.removed_at else datetime.strftime(user.removed_at, fmt_str),
        'updated_at': None if not user.updated_at else datetime.strftime(user.updated_at, fmt_str),
        'removed': user.removed
    }


def return_no_content():
    res = make_response('', 204)
    return res


def validate_instance(body, schema):
    try:
        validate(instance=body, schema=schema)
    except ValidationError as err:
        print(f'Erro na instancia de usuario recebida: {err.message}')
        abort(400)

#############################################################################
#                                  ROUTES                                   #
#############################################################################
@bp.route('/', methods=["GET"])
def hello():
    return 'hello!'


@bp.route('/users', methods=["GET"])
def getAll():
    page = request.args.get('page', 1)
    page_size = request.args.get('pagesize', 1000)
    try:
        page = int(page)
        if page < 1:
            page = 1
        page_size = int(page_size)
        if page_size < 1:
            page_size = 1
    except Exception:
        abort(400)
    users = models.User.query.paginate(page=page, per_page=page_size).items
    for index, user in enumerate(users):
        users[index] = jsonify_user(user)
    return {'users': users}


@bp.route('/users', methods=["POST"])
def insert():
    user_body = request.json
    validate_instance(body=user_body, schema=user_schema_insert)
    password = user_body.get('password')
    user = models.User()
    user.username = user_body.get('username')
    user.name = user_body.get('name')
    user.password = models.User.hash_password(password)
    models.db.session.add(user)
    try:
        models.db.session.commit()
        return return_no_content()
    except Exception as err:
        print(f'Erro ao inserir usuario: {err}')
        models.db.session.rollback()
        abort(409)


@bp.route('/users/<string:user_id>', methods=["GET"])
def getOne(user_id):
    user = models.User.query.get(user_id)
    if not user:
        abort(404)
    return jsonify_user(user)


@bp.route('/users/<string:user_id>', methods=["PUT"])
def update(user_id):
    user_body = request.json
    validate_instance(body=user_body, schema=user_schema_update)
    user = models.User.query.get(user_id)
    if not user:
        abort(404)
    user.username = user_body.get('username')
    user.name = user_body.get('name')
    models.db.session.add(user)
    try:
        models.db.session.commit()
        return return_no_content()
    except Exception as err:
        print(f'Erro ao inserir usuario: {err}')
        models.db.session.rollback()
        abort(409)


@bp.route('/users/<string:user_id>', methods=["DELETE"])
def remove(user_id):
    user = models.User.query.get(user_id)
    if not user:
        abort(404)
    user.removed = True
    user.removed_at = datetime.utcnow()
    models.db.session.add(user)
    try:
        models.db.session.commit()
    except Exception as err:
        print(f'Erro ao remover usuario{err}')
        models.db.session.rollback()
        abort(409)
    return return_no_content()
