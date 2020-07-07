import os
import jwt
import models
from datetime import datetime, timedelta
from flask import Blueprint, request, abort, jsonify
from . import login_schema, validate_instance, return_no_content
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
            abort(404)

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
            models.db.rollback()
            abort(409)

    if grant_type == 'refresh_token':
        refresh_token_id = payload.get('refresh_token')
        refresh_token = models.RefreshToken.query.get(refresh_token_id)
        if not refresh_token or not refresh_token.is_active:
            abort(404)

        access_token = models.AccessToken()
        access_token.refresh_token = refresh_token
        access_token.user = user
        access_token.expiration_date = datetime.utcnow() + timedelta(seconds=AT_EXPIRATION)

        models.db.add(access_token)
        try:
            models.db.session.commit()
        except Exception as ex:
            models.db.rollback()
            abort(409)

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
def logoff():
    token = request.headers.get('Authorization', None)
    token_id = token.replace('Bearer ', '') if token.startswith('Bearer ') else None

    if not token_id:
        abort(400)

    token_id = jwt.decode(token_id, JWT_SECRET, algorithms=['HS256']).get('sub')

    access_token = models.AccessToken.query.get(token_id)
    if not access_token or not access_token.is_active:
        abort(404)

    refresh_token = access_token.refresh_token
    refresh_token.valid = False
    models.db.session.add(refresh_token)

    for at in refresh_token.access_tokens:
        at.valid = False
        models.db.session.add(at)

    models.db.session.commit()

    return return_no_content()
