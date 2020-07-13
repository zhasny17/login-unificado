import pytest
import models
from . import client, app
from tests.test_login_logoff import login
from freezegun import freeze_time
import datetime
import os


def test_auth(client):
    response = client.get('/users', headers={})
    assert response._status_code == 401

    response = client.get('/users', headers={'Authorization': 'Bear: '})
    assert response._status_code == 401

    response = login(client, grant_type='password', username='renan12', password='qpalzm')
    at_token = response.get_json().get('acess_token')

    response = client.delete('/users/2', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 403

    exp_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=int(os.environ.get('AT_EXPIRATION')) + 1)

    @freeze_time(exp_date.strftime("%y-%m-%dT%H:%M:%S"))
    def token_unactive():
        response = client.get('/users', headers={'Authorization': 'Bearer: ' + at_token})
        assert response._status_code == 401
    token_unactive()


def test_validate_payload(client):
    response = login(client, grant_type='password', username=app.config['USERNAME'], password=app.config['PASSWORD'])
    at_token = response.get_json().get('acess_token')

    user_json = {"username": "teste"}
    response = client.post('/users', headers={'Authorization': 'Bearer: ' + at_token}, json=user_json)
    assert response._status_code == 400
