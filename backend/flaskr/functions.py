import os
import xml.etree.ElementTree as ET
from db import db, Snapshot


def subtractTime(rawt1, rawt2):  # format: yyyymmddThhmmss
    monthsCumulative = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    t1 = rawt1.replace('-', '').replace(':', '')
    t2 = rawt2.replace('-', '').replace(':', '')
    time1 = (int(t1[:4]) * 365 + monthsCumulative[int(t1[4:6])] + int(t1[6:8])) * 86400 + int(t1[9:11]) * 3600 + int(t1[11:13]) * 60 + int(t1[13:15])
    time2 = (int(t2[:4]) * 365 + monthsCumulative[int(t2[4:6])] + int(t2[6:8])) * 86400 + int(t2[9:11]) * 3600 + int(t2[11:13]) * 60 + int(t2[13:15])
    return abs(time2 - time1)


def parseResponse(responsesTemp):
    parsed = []
    for i in responsesTemp:
        id, timeBegin, timeEnd, timeLength, satellite, instrument, processLevel = i, '', '', 0, '', '', ''
        timeBegin = i[16:20] + '-' + i[20:22] + '-' + i[22:24] + ' (' + i[25:27] + ':' + i[27:29] + ')'
        timeEnd = i[32:36] + '-' + i[36:38] + '-' + i[38:40] + ' (' + i[41:43] + ':' + i[43:45] + ')'
        timeLength = subtractTime(i[16:31], i[32:47])
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
            'timeLength': timeLength,
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
        timeLength = subtractTime(timeEnd, timeBegin)
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
            'timeLength': timeLength,
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
    t = os.listdir('./backend/catalogue')
    downloadedFiles = []
    for file in t:
        if file[-5:] == '.SEN3':
            downloadedFiles.append(file)
    return downloadedFiles

def zipdir(path, save_path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))


def getCollection(params):
    print(params)
    collection = 'EO:EUM:DAT:0412'
    if params['satellite'] != '':
        if params['satellite'] == 'Sentinel-3':
            if params['instrument'] == 'SLSTR':
                if params['processLevel'] == '2':
                    collection = 'EO:EUM:DAT:0412'
                elif params['processLevel'] == '1':
                    collection = 'EO:EUM:DAT:0411'
            elif params['instrument'] == 'OLCI':
                if params['processLevel'] == '2':
                    collection = 'EO:EUM:DAT:0407'
                elif params['processLevel'] == '1':
                    collection = 'EO:EUM:DAT:0409'
    return collection