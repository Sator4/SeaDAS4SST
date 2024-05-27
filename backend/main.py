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
import zipfile
import xml.etree.ElementTree as ET
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
path_to_gpt = "/home/sator/SeaDAS_8.3/bin/gpt"
path_to_ocssw = "/home/sator/SeaDAS_9.0.1/ocssw"
cwd = '/media/sator/STORAGE/Github/Copernicus/service_vue3'


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


def parseXml(catPath, fileList):
    parsed = []
    for file in fileList:
        # print(os.path.exists(catPath))
        metadata = {}
        tree = ET.parse(catPath + file + '/EOPMetadata.xml')
        root = tree.getroot()
        for elem in root.iter():
            tag = elem.tag[elem.tag.find('}') + 1:]
            if tag in metadata:
                tag += '1'
            metadata[tag] = elem.text

        timeBegin = metadata['beginPosition']
        timeEnd = metadata['endPosition']
        satellite = metadata['shortName']
        instrument = metadata['shortName1']
        posList = metadata['posList']
        id = metadata['Identifier']
        size = metadata['size']
        collection = metadata['parentIdentifier']
        processLevel = str(int(metadata['processingLevel']))

        parsed.append({
            'timeBegin': timeBegin,
            'timeEnd': timeEnd,
            'satellite': satellite,
            'instrument': instrument,
            'posList': posList,
            'id': id,
            'size': size,
            'collection': collection,
            'processLevel': processLevel
        })
    return parsed






def seekDownloaded():
    global downloadedFiles
    t = os.listdir('./backend/catalogue')
    downloadedFiles = []
    for file in t:
        if file[-5:] == '.SEN3':
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
            responsesFromEumetsatRaw = subprocess.check_output(["eumdac", 'search', '-c', collection, '-s', 
                            post_data['text']['begin_date'], '-e', post_data['text']['end_date'], '--bbox', 
                            coords[0], coords[1], coords[2], coords[3]])
            responsesFromEumetsat = [i for i in responsesFromEumetsatRaw.decode().split('\n')][:-1]


    elif request.method == "DELETE":
        responsesFromEumetsat = []
    else:
        response_object['responses'] = parseResponse(responsesFromEumetsat)
        seekDownloaded()
        # response_object['downloaded'] = parseXml(cwd + '/backend/catalogue/', downloadedFiles)
        response_object['downloaded'] = parseResponse(downloadedFiles)
    return jsonify(response_object)


@app.route('/snapshot_manager/download', methods=['POST'])
# @login_required
def download():
    response_object = {'status' : 'success'}
    post_data = request.get_json()
    download_id = post_data['id']
    subprocess.run(['eumdac', 'download', '-c', collection, '-p', download_id, '-o', './backend/catalogue'])

    with zipfile.ZipFile('./backend/catalogue/' + download_id + '.zip') as zip:
        zip.extractall('./backend/catalogue/' + download_id)
    os.remove('./backend/catalogue/' + download_id + '.zip')

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
    os.remove('./backend/catalogue/' + post_data['id'])
    return jsonify(response_object)


@app.route('/snapshot_master', methods=['POST'])
# @login_required
def master():
    response_object = {'status' : 'success'}
    post_data = request.get_json()
    folder_names = post_data['ids']

    for folder_name in folder_names:
        path_to_target = cwd + '/backend/catalogue/' + folder_name + '/' + folder_name + '/xfdumanifest.xml'
        path_to_dest = cwd + '/backend/catalogue/Reprojected/' + folder_name
        
        if post_data['operation'] == 'l2gen':
            ocssw = OCSSW(path_to_ocssw)
            ocssw.l2gen({
                'ifile': path_to_target,
                'ofile': path_to_dest
            })

        elif post_data['operation'] == 'reproject':
            gpt = GPT(path_to_gpt)
            gpt.reproject(
                path_to_target, 
                path_to_dest,
                {
                    # 'src': 'EPSG:4326',
                    'resampling': 'Nearest',
                    'orientation': 0,
                    'pixelSizeX': 0.01,
                    'pixelSizeY': 0.01
                }
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

    # subprocess.call(["eumdac", "describe"])

    # t = 'eumdac search -c="EO:EUM:DAT:0412" -s 2024-03-01T00:00 -e 2024-03-04T01:00'
    # print(1)
    # subprocess.call(["eumdac", 'search', '-c=EO:EUM:DAT:0411', '-s', '2024-03-01T00:00', '-e', '2024-03-04T01:00'])
    


    app.run(debug=True)