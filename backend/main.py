from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError 
import uuid
import eumdac
import subprocess
import os
import sqlite3
import zipfile
import SimpleSeaDAS.OCSSW as OCSSW
import SimpleSeaDAS.GPT as GPT
from esa_snappy import ProductIO

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app, resources={r"/*":{'origins':'*'}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////media/sator/STORAGE/Github/Copernicus/service_vue3/backend/database.db'
app.config['SECRET_KEY'] = 'verysecretkey'
db = SQLAlchemy()
db.init_app(app)

current_user = ''


bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


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


responsesFromEumetsat = []

downloadedFiles = []

collection = ''

def parseResponse(responsesTemp):
    parsed = []
    for i in responsesTemp:
        id, timeBegin, timeEnd, satellite, instrument, processLevel = i, '', '', '', '', ''
        timeBegin = i[16:20] + '-' + i[20:22] + '-' + i[22:24] + ' (' + i[25:27] + ':' + i[27:29] + ')'
        timeEnd = i[32:36] + '-' + i[36:38] + '-' + i[38:40] + ' (' + i[41:43] + ':' + i[43:45] + ')'
        if i[:3] == 'S3A':
            satellite = 'Sentinel-3A'
        elif i[:3] == 'S3B':
            satellite = 'Sentinel-3B'
        if i[4:6] == 'SL':
            instrument = 'SLSTR'
        elif i[4:6] == 'OL':
            instrument = 'OLCI'
        processLevel = i[7]
        parsed.append({
            'id': id,
            'timeBegin': timeBegin,
            'timeEnd': timeEnd,
            'satellite': satellite,
            'instrument': instrument,
            'processLevel': processLevel
        })
    return parsed

def seekDownloaded():
    global downloadedFiles
    t = os.listdir('./backend/catalogue')
    downloadedFiles = []
    for file in t:
        if file[-9:] == '.SEN3.zip':
            downloadedFiles.append(file)
    return


@app.route('/snapshot_manager', methods=['GET', 'POST', 'DELETE'])
# @login_required
def index():
    response_object = {'status' : 'success'}
    global responsesFromEumetsat, collection
    if request.method == "POST":
        responsesFromEumetsat = []
        post_data = request.get_json()
        coords = []
        # print(post_data)
        if 'coords' in post_data['text']:
            coords = post_data['text']['coords'].split(' ')
        if len(coords) != 4:
            coords = ['-180', '-90', '180', '90']
        collection = ''
        if not 'satellite' in post_data['text'] or not 'instrument' in post_data['text'] or not 'processLevel' in post_data['text']:
            collection = 'EO:EUM:DAT:0412'
        else:
            if post_data['text']['satellite'] == 'Sentinel-3':
                if post_data['text']['instrument'] == 'SLSTR':
                    if post_data['text']['processLevel'] == '2':
                        collection = 'EO:EUM:DAT:0412'
                    elif post_data['text']['processLevel'] == '1':
                        collection = 'EO:EUM:DAT:0411'
                elif post_data['text']['instrument'] == 'OLCI':
                    if post_data['text']['processLevel'] == '2':
                        collection = 'EO:EUM:DAT:0407'
                    elif post_data['text']['processLevel'] == '1':
                        collection = 'EO:EUM:DAT:0409'
        
        if 'fullBox' in post_data['text']:
            coordsCorner = [str(float(coords[0])-0.01), str(float(coords[3])), str(float(coords[0])), str(float(coords[3])+0.01)]
            responsesRaw1 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[0])-0.01), str(float(coords[1])), str(float(coords[0])), str(float(coords[1])+0.01)]
            responsesRaw2 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[2])-0.01), str(float(coords[3])), str(float(coords[2])), str(float(coords[3])+0.01)]
            responsesRaw3 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            coordsCorner = [str(float(coords[2])-0.01), str(float(coords[1])), str(float(coords[2])), str(float(coords[1])+0.01)]
            responsesRaw4 = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coordsCorner[0], coordsCorner[1], coordsCorner[2], coordsCorner[3]])
            responses1 = [i for i in responsesRaw1.decode().split('\n')][:-1]
            responses2 = [i for i in responsesRaw2.decode().split('\n')][:-1]
            responses3 = [i for i in responsesRaw3.decode().split('\n')][:-1]
            responses4 = [i for i in responsesRaw4.decode().split('\n')][:-1]
            for i in responses1:
                if i in responses2 and i in responses3 and i in responses4:
                    responsesFromEumetsat.append(i)

        else:
            # responsesFromEumetsatRaw = subprocess.check_output(["eumdac", 'search', '-c=EO:EUM:DAT:0411', '-s', '2024-03-04T00:00', '-e', '2024-03-04T01:00'])
            responsesFromEumetsatRaw = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coords[0], coords[1], coords[2], coords[3]])
            responsesFromEumetsat = [i for i in responsesFromEumetsatRaw.decode().split('\n')][:-1]


    elif request.method == "DELETE":
        responsesFromEumetsat = []
    else:
        response_object['responses'] = parseResponse(responsesFromEumetsat)
        seekDownloaded()
        response_object['downloaded'] = parseResponse(downloadedFiles)
    return jsonify(response_object)


@app.route('/snapshot_manager/download', methods=['POST'])
# @login_required
def download():
    response_object = {'status' : 'success'}
    download_id = request.get_data().decode()  #[:-1]  # костыль чтобы убрать \r с конца названия
    subprocess.run(['eumdac', 'download', '-c', collection, '-p', 
                    download_id, '-o', './backend/catalogue'])
    return jsonify(response_object)


@app.route('/snapshot_manager/exit', methods=['POST'])
# @login_required
def exit():
    response_object = {'status' : 'success'}
    response_object['link'] = '/'
    # logout_user()
    current_user = ''
    return jsonify(response_object)


@app.route('/snapshot_manager/open', methods=['GET', 'POST'])
# @login_required
def master():
    response_object = {'status' : 'success'}

    if request.method == 'POST':
        post_data = request.get_json()
        # with zipfile.ZipFile('./backend/catalogue/' + post_data['id']) as z:
        #     with z.open('EOPMetadata.xml') as f:
        #         for line in f:
        #             print(line)



    return jsonify(response_object)




if __name__ == '__main__':
    # ConsumerKey = 'a15dLDPZDGWFrphVPt_tEWHWY0Ua'   # раскомментировать эти 6 строчек и перезапустить, если будет падать
    # ConsumerSecret = 'WIbmopmrJXQ_pR41pzUl1CdCr_Ia'
    # credentials = (ConsumerKey, ConsumerSecret)
    # subprocess.call(["eumdac", 'set-credentials', ConsumerKey, ConsumerSecret])
    # token = eumdac.AccessToken(credentials)
    # print(token)

    # subprocess.call(["eumdac", "describe"])

    # t = 'eumdac search -c="EO:EUM:DAT:0412" -s 2024-03-01T00:00 -e 2024-03-04T01:00'
    # print(1)
    # subprocess.call(["eumdac", 'search', '-c=EO:EUM:DAT:0411', '-s', '2024-03-01T00:00', '-e', '2024-03-04T01:00'])



    # ocssw_path = "/home/sator/SeaDAS/ocssw"
    # ocssw = OCSSW(ocssw_path)
    # print(ocssw)
    # ocssw.l2gen({
    #     'ifile': '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/S3A_OL_1_EFR____20240509T012207_20240509T012507_20240509T031808_0179_112_131_2160_MAR_O_NR_002.SEN3/xfdumanifest.xml',
    #     'ofile': '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/S3A_OL_2_EFR____20240509T012207_20240509T012507_20240509T031808_0179_112_131_2160_MAR_O_NR_002.SEN3/S3A_OLCI_EFR.20240509T012206.L2.OC.nc'
    # })

    path_to_gpt = "/home/sator/SeaDAS/bin/gpt"
    path_to_target = '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/S3B_SL_2_WST____20240321T015406_20240321T015706_20240321T035221_0179_091_060_2160_MAR_O_NR_003.SEN3/xfdumanifest.xml'
    gpt = GPT(path_to_gpt)
    gpt.reproject('/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/S3B_SL_2_WST____20240321T015406_20240321T015706_20240321T035221_0179_091_060_2160_MAR_O_NR_003.SEN3/xfdumanifest.xml',
                  '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/Reprojected/',
              {'pixelSizeX': 0.01, 'pixelSizeY': 0.01})

    


    # app.run(debug=True)