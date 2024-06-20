from flask import jsonify, request
from flask_bcrypt import Bcrypt
from flask_login import login_user, LoginManager

from main import app
from db import db, User, validate_username, validate_password

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
def authentication():
    response_object = {'status' : 'success'}
    return jsonify(response_object)


@app.route('/login', methods=['POST'])
def login():
    response_object = {'status' : 'success'}
    response_object['link'] = '/'
    response_object['errorMessage'] = ''
    post_data = request.get_json()

    global current_user
    current_user = User.query.filter_by(username=post_data['login']).first()

    if not current_user:
        response_object['errorMessage'] = 'Пользователя с таким логином не существует'
    elif not bcrypt.check_password_hash(current_user.password, post_data['password']):
        response_object['errorMessage'] = 'Неверный пароль'
    else:
        login_user(current_user)
        response_object['link'] = '/snapshot_manager'

    return jsonify(response_object)


@app.route('/register', methods=['POST'])
def register():
    response_object = {'status' : 'success'}
    response_object['errorMessage'] = ''
    response_object['successMessage'] = ''
    post_data = request.get_json()

    if not validate_username(post_data['login']):
        response_object['errorMessage'] = 'Неподходящее имя пользователя'
    elif not validate_password(post_data['password']):
        response_object['errorMessage'] = 'Неподходящий пароль'
    else:
        hashed_password = bcrypt.generate_password_hash(post_data['password'])
        new_user = User(username=post_data['login'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        response_object['successMessage'] = 'Регистрация прошла успешно!'

    return jsonify(response_object)