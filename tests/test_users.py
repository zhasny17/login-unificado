import pytest
import models
from tests.test_login_logoff import login
from . import client, app
from freezegun import freeze_time
import datetime
import os


def test_user(client):
    response = client.get('/')
    assert response._status_code == 200
    assert response.data == b'hello!'

    response = login(client, grant_type='password', username=app.config['USERNAME'], password=app.config['PASSWORD'])
    at_token = response.get_json().get('acess_token')

    # Get All Users
    response = client.get('/users', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 200

    response = client.get('/users?page=0&pagesize=0', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 200

    response = client.get('/users?page=f&pagesize=0', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 400

    # Create User
    user_json = {"username": "teste", "name": "Pedro", "password": "123"}
    response = client.post('/users', headers={'Authorization': 'Bearer: ' + at_token}, json=user_json)
    assert response._status_code == 204

    # Get User
    user = models.User.query.filter(models.User.username == 'teste').first()
    response = client.get('/users/' + user.id, headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 200

    response = client.get('/users/5', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 404

    # Edit User
    user_edit = {"username": "teste1", "name": "Pedro1"}
    response = client.put('/users/' + user.id, headers={'Authorization': 'Bearer: ' + at_token}, json=user_edit)
    assert response._status_code == 204

    response = client.put('/users/5', headers={'Authorization': 'Bearer: ' + at_token}, json=user_edit)
    assert response._status_code == 404

    # Delete User
    response = client.delete('/users/' + user.id, headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 204

    response = client.delete('/users/5', headers={'Authorization': 'Bearer: ' + at_token})
    assert response._status_code == 404

    # Introspect
    response = client.post('/users/introspect', json={})
    assert response._status_code == 400

    response = client.post('/users/introspect', json={'token': '31412'})
    assert response._status_code == 400

    response = client.post('/users/introspect', json={'token': at_token})
    assert response._status_code == 200

    exp_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=int(os.environ.get('AT_EXPIRATION')) + 1)

    @freeze_time(exp_date.strftime("%y-%m-%dT%H:%M:%S"))
    def token_unactive():
        response = client.post('/users/introspect', json={'token': at_token})
        assert response._status_code == 400

    token_unactive()
