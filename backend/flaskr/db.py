from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Snapshot(db.Model, UserMixin):
    snapshot_name = db.Column(db.String(120), primary_key=True)


def validate_username(username):
    existing_user_username = User.query.filter_by(username=username).first()
    if existing_user_username:
        return False
    if username == '':
        return False
    return True

def validate_password(password):
    if len(password) < 4 or len(password) > 20:
        return False
    return True