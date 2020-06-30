from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import uuid
import hashlib

db = SQLAlchemy()
migrate = Migrate(db=db)

tables_config = {
    'mysql_charset': 'utf8mb4',
}


def generate_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __table_args__ = (
        tables_config
    )

    @staticmethod
    def hash_password(password):
        if not password:
            return None
        return hashlib.sha256(password.encode()).hexdigest()

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True))
    removed_at = db.Column(db.DateTime(timezone=True))
    removed = db.Column(db.Boolean, nullable=False, default=False)


class AccessToken(db.Model):
    __table_args__ = (
        tables_config
    )
    __tablename__ = 'access_token'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    valid = db.Column(db.Boolean, nullable=False, default=True)
    expiration_date = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('access_tokens', lazy=True))
    refresh_token_id = db.Column(db.String(36), db.ForeignKey('refresh_token.id'), nullable=False)
    refresh_token = db.relationship('RefreshToken', backref=db.backref('access_tokens', lazy=True))

    def has_expired(self, when=None):
        if datetime.utcnow() >= self.expiration_date:
            return True
        else:
            return False

    def is_active(self):
        return self.valid and not self.has_expired()


class RefreshToken(db.Model):
    __table_args__ = (
        tables_config
    )
    __tablename__ = 'refresh_token'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    valid = db.Column(db.Boolean, nullable=False, default=True)
    expiration_date = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('refresh_tokens', lazy=True))

    def has_expired(self):
        if datetime.utcnow() >= self.expiration_date:
            return True
        else:
            return False

    def is_active(self):
        return self.valid and not self.has_expired()
