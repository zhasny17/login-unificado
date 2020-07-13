import json
import pytest
import models
from core import create_app
import os


with open("tests/config.test.json", "r") as f:
    data = json.load(f)
    for key, value in data.items():
        os.environ[key] = value

app = create_app(config={'TESTING': True})
app.config['USERNAME'] = os.environ.get('APP_USERNAME')
app.config['PASSWORD'] = os.environ.get('APP_PW')


def setup_db():
    models.db.create_all()


def teardown_db():
    models.db.reflect()
    models.db.drop_all()


def script_sql():
    with open("tests/data.sql", "rb") as f:
        data = f.read().decode('utf-8')
        for query in data.split('\r\n\r\n'):
            models.db.engine.execute(query, multi=True)


@pytest.fixture
def client():
    with app.app_context():
        teardown_db()
        setup_db()
        script_sql()
        yield app.test_client()
