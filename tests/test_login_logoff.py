import pytest
import models
from . import client, app
from freezegun import freeze_time
import datetime
import os


def login(client, **data):
    response = client.post('/login', json=data)
    return response


def logout(client, at_token):
    return client.post('/logoff', headers={'Authorization': 'Bearer: ' + at_token})


def test_login(client):
    response = login(client, grant_type='password', username=app.config['USERNAME'])
    assert response._status_code == 401

    response = login(client, grant_type='refresh_token', username=app.config['USERNAME'])
    assert response._status_code == 401

    response = login(client, grant_type='password', username=app.config['USERNAME'], password=app.config['PASSWORD'])
    assert response._status_code == 200
    rt_token = response.get_json().get('refresh_token')

    response = login(client, grant_type='refresh_token', username=app.config['USERNAME'], refresh_token=rt_token)
    assert response._status_code == 200

    response = login(client, grant_type='dsdc')
    assert response._status_code == 400


def test_logoff(client):
    response = login(client, grant_type='password', username=app.config['USERNAME'], password=app.config['PASSWORD'])
    assert response._status_code == 200
    token = response.get_json().get('acess_token')

    response = logout(client, token)
    assert response._status_code == 204
