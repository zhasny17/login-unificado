from flask import request, g
from functools import wraps
import jwt
import os
import models
from utils.error_handler import UnauthorizedException, ForbiddenException

JWT_SECRET = os.environ.get('JWT_SECRET')

#############################################################################
#                             HELPER FUNCTIONS                              #
#############################################################################


def check_token():
    if 'Authorization' not in request.headers:
        return None
    bearer_token = request.headers.get('Authorization')
    if not bearer_token.startswith("Bearer ") and len(bearer_token.split()) != 2:
        return None
    token = bearer_token.split()[1]
    access_token_id = decode_jwt(token)
    if not access_token_id:
        return None
    access_token = models.AccessToken.query.get(access_token_id)
    if not access_token or not access_token.is_active():
        return None
    g.token = access_token
    user = access_token.user
    return user


def decode_jwt(token):
    try:
        token_id = jwt.decode(token, JWT_SECRET, algorithm='HS256').get("sub")
        return token_id
    except Exception:
        return None


def get_user():
    token = g.get('token')
    user = token.user
    return user


def get_token():
    token = g.get('token')
    return token


#############################################################################
#                 AUTHENTICATION DECORATORS FUNCTIONS                       #
#############################################################################

def authenticate_admin(f):
    @wraps(f)
    def authenticate(*args, **kwargs):
        user = check_token()
        if not user:
            raise UnauthorizedException(message='Nao autorizado')
        if not user.admin:
            raise ForbiddenException(message='Permissoes insuficientes')
        return f(*args, **kwargs)
    return authenticate


def authenticate_user(f):
    @wraps(f)
    def authenticate(*args, **kwargs):
        user = check_token()
        if not user:
            raise UnauthorizedException(message='Nao autorizado')
        return f(*args, **kwargs)
    return authenticate
