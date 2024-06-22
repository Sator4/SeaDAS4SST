from flask import Flask, jsonify, request, send_file
from flask_cors import CORS, cross_origin
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_sock import Sock
import subprocess
import os
import zipfile
import json
import shutil
import SimpleSeaDAS.OCSSW as OCSSW
import SimpleSeaDAS.GPT as GPT
from db import db, validate_password, validate_username, User
from constants import *
from functions import *

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app, resources={r"/*":{'origins':'*'}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////media/sator/STORAGE/Github/Copernicus/service_vue3/backend/database.db'
app.config['SECRET_KEY'] = 'verysecretkey'

db.init_app(app)

sock = Sock(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

###################### AUTH ###########################

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

###################### /AUTH ###########################


@app.route('/snapshot_manager', methods=['GET', 'POST', 'DELETE'])
# @login_required
def index():
    response_object = {'status' : 'success'}
    responsesFromEumetsat = []
    if request.method == "POST":
        responsesFromEumetsat = []
        post_data = request.get_json()
        coords = []
        if post_data['coords'] != '':
            coords = post_data['coords'].split(' ')
        if len(coords) != 4:
            coords = ['-180', '-90', '180', '90']
        collection = getCollection(post_data)
        
        if post_data['fullBox'] != '':
            coordsCorner = [str(float(coords[0])-0.01), str(float(coords[3])), str(float(coords[0])), str(float(coords[3])+0.01)]
            responsesRaw1 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['begin_date'], '-e', post_data['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[0])-0.01), str(float(coords[1])), str(float(coords[0])), str(float(coords[1])+0.01)]
            responsesRaw2 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['begin_date'], '-e', post_data['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[2])-0.01), str(float(coords[3])), str(float(coords[2])), str(float(coords[3])+0.01)]
            responsesRaw3 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['begin_date'], '-e', post_data['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[2])-0.01), str(float(coords[1])), str(float(coords[2])), str(float(coords[1])+0.01)]
            responsesRaw4 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['begin_date'], '-e', post_data['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            responses1 = [i for i in responsesRaw1.decode().split('\n')][:-1]
            responses2 = [i for i in responsesRaw2.decode().split('\n')][:-1]
            responses3 = [i for i in responsesRaw3.decode().split('\n')][:-1]
            responses4 = [i for i in responsesRaw4.decode().split('\n')][:-1]
            for i in responses1:
                if i in responses2 and i in responses3 and i in responses4:
                    responsesFromEumetsat.append(i)

        else:
            responsesFromEumetsatRaw = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['begin_date'], '-e', post_data['end_date'], '--bbox', 
                            coords[0], coords[1], coords[2], coords[3]])
            responsesFromEumetsat = [i for i in responsesFromEumetsatRaw.decode().split('\n')][:-1]

    elif request.method == "DELETE":
        responsesFromEumetsat = []
    response_object['responses'] = parseResponse(responsesFromEumetsat)
    downloadedFiles = seekDownloaded()
    # response_object['downloaded'] = parseXml(cwd + '/backend/catalogue/', downloadedFiles)
    response_object['downloaded'] = parseResponse(downloadedFiles)
    return jsonify(response_object)


@app.route('/snapshot_manager/download', methods=['POST'])
# @login_required
def download():
    response_object = {'status' : 'success'}
    cat = './backend/catalogue/'
    # subprocess.run(['python3', cwd + '/backend/test.py'])
    # post_data = json.loads(ws.receive())
    post_data = request.get_json()
    download_ids = [file['id'] for file in post_data['files'] if not os.path.exists(cat + file['id'])]

    for download_id in download_ids:
        path = cat + download_id
        collection = getCollection((parseResponse([download_id])[0]))
        proc = subprocess.Popen(['eumdac', 'download', '-c', collection, '-p', download_id, '-o', cat], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

        for l in proc.stdout:
            if l:
                print(l)
        for l in proc.stderr:
            if l:
                print(l)
                # ws.send(l.decode())

        with zipfile.ZipFile(path + '.zip') as zip:
            zip.extractall(path)
        os.remove(path + '.zip')
    return jsonify(response_object)



@app.route('/snapshot_manager/exit', methods=['POST'])
# @login_required
def exit():
    response_object = {'status' : 'success'}
    response_object['link'] = '/'
    # logout_user()
    current_user = ''
    return jsonify(response_object)


@app.route('/snapshot_manager/delete', methods=['POST'])
# @login_required
def delete():
    response_object = {'status' : 'success'}
    post_data = request.get_json()
    shutil.rmtree('./backend/catalogue/' + post_data['id'])
    return jsonify(response_object)


@app.route('/snapshot_manager/saveas', methods=['POST'])
# @login_required
def saveAs():
    cat = '/backend/catalogue/'
    post_data = request.get_json()
    snapshot_ids = [file['id'] for file in post_data['chosenFiles']]
    shutil.make_archive(cwd + cat + snapshot_ids[0], 'zip', cwd + cat, snapshot_ids[0])
    return send_file(cwd + cat + snapshot_ids[0] + '.zip')


@app.route('/snapshot_master', methods=['POST'])
# @login_required
def master():
    response_object = {'status' : 'success'}
    post_data = request.get_json()
    folder_names = [folder_name['id'] for folder_name in post_data['files']]

    for folder_name in folder_names:
        path_to_target = cwd + '/backend/catalogue/' + folder_name + '/' + folder_name + '/xfdumanifest.xml'
        path_to_dest = cwd + '/backend/catalogue/Reprojected/' + folder_name
        
        if post_data['operation'] == 'l2gen':
            params = post_data['params']
            ocssw = OCSSW(path_to_ocssw)
            ocssw.l2gen({
                'ifile': path_to_target,
                'ofile': path_to_dest,
                'parfile': params        #   #СОМНИТЕЛЬНО
            })

        elif post_data['operation'] == 'reproject':
            params = post_data['params']
            # if params['addDeltaBands'] == 'true':

            gpt = GPT(path_to_gpt)
            gpt.reproject(
                path_to_target, 
                path_to_dest,
                params
            )

        elif post_data['operation'] == 'getFullData':
            response_object['downloaded'] = parseXml(cwd + '/backend/catalogue/', folder_names)
        else:
            response_object['status'] = 'unknown operation'  
    return jsonify(response_object)




if __name__ == '__main__':
    # ConsumerKey = 'a15dLDPZDGWFrphVPt_tEWHWY0Ua'   # раскомментировать эти 6 строчек и перезапустить, если будет падать
    # ConsumerSecret = 'WIbmopmrJXQ_pR41pzUl1CdCr_Ia'
    # credentials = (ConsumerKey, ConsumerSecret)
    # subprocess.call(["eumdac", 'set-credentials', ConsumerKey, ConsumerSecret])
    # token = eumdac.AccessToken(credentials)
    # print(token)

    # subprocess.call(["eumdac", 'search', '-c=EO:EUM:DAT:0412', '-s', '2024-03-01T00:00', '-e', '2024-03-04T01:00'])
    
    app.run(debug=True)