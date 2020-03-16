from flask import Flask
import os
from blueprints import user
import models

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

    models.db.init_app(app=app)
    models.migrate.init_app(app=app)

    # NOTE register blueprints
    app.register_blueprint(user.bp)
    
    models.db.create_all(app=app)

    @app.after_request
    def after_request(response):
        header = response.headers
        header['Access-Control-Allow-Origin'] = '*'
        header['Access-Control-Allow-Methods'] = '*'
        header['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, X-CSRF-TOKEN'
        return response

    return app
