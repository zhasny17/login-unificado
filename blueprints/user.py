from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
import models
from . import user_schema_insert, user_schema_update, change_pass_schema, reset_pass_schema, validate_instance, return_no_content
from utils import auth, upload_handler
from utils.error_handler import BadRequestException, ConflictException, NotFoundException, ForbiddenException
import smtplib
from email.mime.text import MIMEText
import ssl
import os
import jinja2


#############################################################################
#                                 VARIABLES                                 #
#############################################################################
bp = Blueprint('user', __name__)

SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = os.environ.get('SMTP_PORT')
SMTP_USER_EMAIL = os.environ.get('SMTP_USER_EMAIL')
SMTP_USER_PASSWORD = os.environ.get('SMTP_USER_PASSWORD')

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')

SYSTEM_BASE_URL = os.environ.get('SYSTEM_BASE_URL')

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


def send_email(user_id, username):

    with open('./reset-password.html', 'r') as f:
        template = jinja2.Template(f.read())

    html = template.render(
        url=f'{SYSTEM_BASE_URL}/users/{user_id}/reset/password'
    )

    message = MIMEText(html, 'html')
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp_client:
            smtp_client.starttls(context=context)
            smtp_client.login(SMTP_USER_EMAIL, SMTP_USER_PASSWORD)

            smtp_client.sendmail(SENDER_EMAIL, username, message)
    except Exception:
        raise BadRequestException(message='Erro no envio do email')

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
    if not user or user.removed:
        raise NotFoundException(message='usuario nao encontrado')
    response = jsonify_user(user)
    return jsonify(response)


@bp.route('/users/<string:user_id>', methods=["PUT"])
@auth.authenticate_admin
def update(user_id):
    user_body = request.json
    validate_instance(body=user_body, schema=user_schema_update)
    user = models.User.query.get(user_id)
    if not user or user.removed or not user.active:
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
    if not user or user.removed:
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


@bp.route('/users/change/password', methods=['POST'])
@auth.authenticate_user
def change_pass():
    payload = request.get_json()

    validate_instance(payload=payload, schema=change_pass_schema)

    current_password = payload.get('current_password')
    new_password = payload.get('new_password')

    user = auth.get_user()

    if user.password != models.User.hash_password(current_password):
        raise ConflictException(message='Informacoes invalidas')

    user.password = models.User.hash_password(new_password)

    models.db.session.add(user)

    models.db.session.commit()

    return return_no_content()


@bp.route('/users/email/reset/password', methods=['GET'])
@auth.authenticate_user
def send_email_to_reset_pass():
    user = auth.get_user()
    user_id = user.id
    username = user.username
    send_email(user_id=user_id, username=username)
    return return_no_content()


@bp.route('/users/<string:user_id>/reset/password', methods=['POST'])
def reset_pass(user_id):
    payload = request.get_json()

    validate_instance(payload=payload, schema=reset_pass_schema)

    first_new_password = payload.get('first_new_password')
    second_new_password = payload.get('second_new_password')

    user = models.User.query.get(user_id)

    if not user or user.removed or not user.active:
        raise NotFoundException(message='Usuario invalido')

    if first_new_password != second_new_password:
        raise ConflictException(message='Informacoes invalidas')

    user.password = models.User.hash_password(first_new_password)

    models.db.session.add(user)

    models.db.session.commit()

    return return_no_content()


@bp.route('/users/active', methods=['POST'])
@auth.authenticate_user
def reset_pass(user_id):
    user = auth.get_user()

    if not user or user.removed:
        raise NotFoundException(message='Usuario invalido')

    actual_status = user.active

    user.active = not actual_status

    models.db.session.add(user)

    models.db.session.commit()

    return return_no_content()
