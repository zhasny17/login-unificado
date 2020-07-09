from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
import models
from . import user_schema_insert, user_schema_update, validate_instance, return_no_content
from utils import auth, upload_handler
from utils.error_handler import BadRequestException, ConflictException, NotFoundException

#############################################################################
#                                 VARIABLES                                 #
#############################################################################
bp = Blueprint('user', __name__)


#############################################################################
#                             HELPER FUNCTIONS                              #
#############################################################################
def jsonify_user(user):
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'active': user.active,
        'admin': user.admin,
        'photo_url': user.photo_url,
        'created_at': user.created_at,
        'removed_at': user.removed_at,
        'updated_at': user.updated_at,
        'removed': user.removed
    }


#############################################################################
#                                  ROUTES                                   #
#############################################################################
@bp.route('/', methods=["GET"])
def hello():
    return 'hello!'


@bp.route('/users', methods=["GET"])
@auth.authenticate_user
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
        raise BadRequestException(message='Erro no recebimento dos parametros de paginacao')
    users = models.User.query.paginate(page=page, per_page=page_size).items
    for index, user in enumerate(users):
        users[index] = jsonify_user(user)
    return jsonify({'users': users})


@bp.route('/users', methods=["POST"])
@auth.authenticate_admin
def insert():
    user_body = request.json
    validate_instance(body=user_body, schema=user_schema_insert)
    password = user_body.get('password')
    user = models.User()
    user.username = user_body.get('username')
    user.name = user_body.get('name')
    user.photo_url = user_body.get('photo_url')
    user.password = models.User.hash_password(password)
    models.db.session.add(user)
    try:
        models.db.session.commit()
        return return_no_content()
    except Exception as err:
        print(f'Erro ao inserir usuario: {err}')
        models.db.session.rollback()
        raise ConflictException(message='Conflito no banco de dados')


@bp.route('/users/<string:user_id>', methods=["GET"])
@auth.authenticate_user
def getOne(user_id):
    user = models.User.query.get(user_id)
    if not user:
        raise NotFoundException(message='usuario nao encontrado')
    response = jsonify_user(user)
    return jsonify(response)


@bp.route('/users/<string:user_id>', methods=["PUT"])
@auth.authenticate_admin
def update(user_id):
    user_body = request.json
    validate_instance(body=user_body, schema=user_schema_update)
    user = models.User.query.get(user_id)
    if not user:
        raise NotFoundException(message='usuario nao encontrado')
    user.username = user_body.get('username')
    user.name = user_body.get('name')
    models.db.session.add(user)
    try:
        models.db.session.commit()
        return return_no_content()
    except Exception as err:
        print(f'Erro ao inserir usuario: {err}')
        models.db.session.rollback()
        raise ConflictException(message='Conflito no banco de dados')


@bp.route('/users/<string:user_id>', methods=["DELETE"])
@auth.authenticate_admin
def remove(user_id):
    user = models.User.query.get(user_id)
    if not user:
        raise NotFoundException(message='usuario nao encontrado')
    user.removed = True
    user.removed_at = datetime.utcnow()
    models.db.session.add(user)
    try:
        models.db.session.commit()
    except Exception as err:
        print(f'Erro ao remover usuario{err}')
        models.db.session.rollback()
        raise ConflictException(message='Conflito no banco de dados')
    return return_no_content()


@bp.route('/users/introspect', methods=['POST'])
def istrospect():
    payload = request.get_json()

    if 'token 'not in payload:
        raise BadRequestException(message='Necessario informar o token de acesso')

    token = payload.get('token')

    token = models.AccessToken.query.filter_by(id=token).first()
    if not token or not token.is_active():
        raise NotFoundException(message='Token invalido')

    return jsonify_user(token.user)


@bp.route('/users/request/upload/<string:image_name>', methods=['POST'])
def generate_upload_link(image_name):
    upload_obj = upload_handler.upload_image(imageName=image_name)

    if not upload_obj:
        raise BadRequestException(message='Erro ao gerar link de upload de imagem')

    return jsonify(upload_obj)


@bp.route('users/change/photo', methods=['POST'])
@auth.authenticate_user
def change_photo():
    payload = request.get_json()

    if 'new_photo_url' not in payload:
        raise BadRequestException(message='Necessario informar uma nova url de foto')

    user = auth.get_user()

    user.photo_url = payload.get('new_photo_url')

    models.db.session.add(user)
    try:
        models.db.session.commit()
        return return_no_content()
    except Exception:
        raise ConflictException(message='Conflito no banco de dados')
