from flask import Flask
import os

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='{}://{}:{}@{}/{}'.format(
            os.environ.get('DB_CONNECTOR'),
            os.environ.get('DB_USERNAME'),
            os.environ.get('DB_PASSWORD'),
            os.environ.get('DB_HOST'),
            os.environ.get('DB_NAME')
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    if config:
        app.config.from_mapping(**config)
    return app
