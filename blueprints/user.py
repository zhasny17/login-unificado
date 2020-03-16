from flask import Blueprint

bp = Blueprint('user', __name__)

@bp.route('/', methods=["GET"])
def hello():
    return 'hello!'