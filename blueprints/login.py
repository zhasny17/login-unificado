import os
import jwt
import models
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from . import login_schema, validate_instance, return_no_content
from utils import auth
from utils.error_handler import NotFoundException, ConflictException, BadRequestException, UnauthorizedException
#############################################################################
#                                 VARIABLES                                 #
#############################################################################
bp = Blueprint('login', __name__)

RT_EXPIRATION = int(os.environ.get('RT_EXPIRATION'))
AT_EXPIRATION = int(os.environ.get('AT_EXPIRATION'))
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION'))
JWT_SECRET = os.environ.get('JWT_SECRET')
#############################################################################
#                             HELPER FUNCTIONS                              #
#############################################################################

#############################################################################
#                                  ROUTES                                   #
#############################################################################
@bp.route('/login', methods=['POST'])
def login():
    payload = request.get_json()
    validate_instance(payload=payload, schema=login_schema)

    grant_type = payload.get('grant_type')

    if grant_type == 'password':
        username = payload.get('username')
        password = models.User.hash_password(password=payload.get('password'))

        user = models.User.query.filter_by(username=username, password=password, active=True, removed=False).first()
        if not user:
            raise UnauthorizedException(message='Nao autorizado')

        refresh_token = models.RefreshToken()
        refresh_token.user = user
        refresh_token.expiration_date = datetime.utcnow() + timedelta(seconds=RT_EXPIRATION)

        access_token = models.AccessToken()
        access_token.refresh_token = refresh_token
        access_token.user = user
        access_token.expiration_date = datetime.utcnow() + timedelta(seconds=AT_EXPIRATION)

        models.db.session.add(refresh_token)
        models.db.session.add(access_token)
        try:
            models.db.session.commit()
        except Exception:
            models.db.session.rollback()
            raise ConflictException(message='Conflito no banco de dados')

    elif grant_type == 'refresh_token':
        jwt_rt = payload.get('refresh_token')
        if not jwt_rt:
            raise UnauthorizedException(message='Nao autorizado')

        refresh_token_id = auth.decode_jwt(jwt_rt)
        refresh_token = models.RefreshToken.query.get(refresh_token_id)
        if not refresh_token or not refresh_token.is_active:
            raise UnauthorizedException(message='Nao autorizado')

        user = refresh_token.user
        access_token = models.AccessToken()
        access_token.refresh_token = refresh_token
        access_token.user = user
        access_token.expiration_date = datetime.utcnow() + timedelta(seconds=AT_EXPIRATION)
        models.db.session.add(access_token)
        try:
            models.db.session.commit()
        except Exception:
            models.db.session.rollback()
            raise ConflictException(message='Conflito no banco de dados')
    else:
        raise BadRequestException(message='Grant_type Inválido')

    at_jwt = {
        'sub': access_token.id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    }
    rt_jwt = {
        'sub': refresh_token.id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    }

    response = {
        'acess_token': jwt.encode(at_jwt, JWT_SECRET, algorithm='HS256').decode('utf-8'),
        'refresh_token': jwt.encode(rt_jwt, JWT_SECRET, algorithm='HS256').decode('utf-8'),
        'expires_in': JWT_EXPIRATION
    }
    return jsonify(response)


@bp.route('/logoff', methods=['POST'])
@auth.authenticate_user
def logoff():
    access_token = auth.get_token()

    refresh_token = access_token.refresh_token
    refresh_token.valid = False
    models.db.session.add(refresh_token)

    for at in refresh_token.access_tokens:
        at.valid = False
        models.db.session.add(at)

    models.db.session.commit()

    return return_no_content()
