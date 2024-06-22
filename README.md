# SeaDAS4SST
Сервис для автоматизации поиска, скачивания и обработки спутниковых снимков средствами Eumdac и SeaDAS.
Eumdac

Eumdac — это библиотека Python, обеспечивающая доступ к спутниковым данным Eumetsat и включает в себя множество методов для использования API Eumetsat и множество cli функций для поиска и скачивания данных.


## Запуск

Серверная часть:
```
python backend/flaskr/main.py
```
Клиентская часть:
```
cd frontend
npm run serve
```



## API

```python
import requests
import json

url = 'http://localhost:5000'   # адрес сервиса
```

### Snapshot manager:

```python
r = requests.get(url + '/snapshot_manager') # получить информацию о скачанных и найденных снимках
print(r.text)

searchParams = {  # в квадратных скобках написаны возможные значения
    'satellite': 'Sentinel-3',      # ['Sentinel-3']
    'instrument': 'SLSTR',          # ['SLSTR', 'OLCI'], по умолчанию: 'SLSTR'
    'processLevel': 2,              # [1, 2], по умолчанию: 2
    'coords': '',                   # север восток запад юг, по умолчанию: '-180 -90 180 90'
    'fullBox': '',      # [true, false], по умолчанию: false
    'begin_date': '2024-06-10T00:00',
    'end_date': '2024-06-10T01:00' # см. eumdac describe -c %коллекция%, чтобы узнать id коллекции, см. /backend/flaskr/functions.py getCollection()
}

r = requests.post(url + '/snapshot_manager', json=searchParams)  # совершить поиск по параметрам
ids = json.loads(r.text)['responses']
for i in ids:
    print(i)


r = requests.delete(url + '/snapshot_manager')  # сбросить список найденных снимков
print(r.text)
```

```python
download = { 'files': [
    {'id': 'S3B_SL_2_WST____20240609T235821_20240610T000121_20240610T021224_0179_094_059_1260_MAR_O_NR_003.SEN3'},
    {'id': 'S3A_SL_2_WST____20240609T235913_20240610T000213_20240610T010919_0179_113_201_5040_MAR_O_NR_003.SEN3'},
    {'id': 'S3B_SL_2_WST____20240610T000121_20240610T000421_20240610T021306_0180_094_059_1440_MAR_O_NR_003.SEN3'}
]}

r = requests.post(url + '/snapshot_manager/download', json=download)  # скачать на локальный сервер
```


```python
delete = {'id': 'S3B_SL_2_WST____20240609T235821_20240610T000121_20240610T021224_0179_094_059_1260_MAR_O_NR_003.SEN3'}

r = requests.post(url + '/snapshot_manager/delete', json=delete)  # удалить с локального сервера
```

```python
saveas = {
    'chosenFiles': [
        {'id': 'S3B_SL_2_WST____20240609T235821_20240610T000121_20240610T021224_0179_094_059_1260_MAR_O_NR_003.SEN3'}
    ]
}
r = requests.post(url + '/snapshot_manager/saveas', json=saveas)  # скачать на локальный компьютер (не завершено)
print(r.text)
```

### Snapshot master:

```python
master = {
    'files': [
        {'id': 'S3B_SL_2_WST____20240609T235821_20240610T000121_20240610T021224_0179_094_059_1260_MAR_O_NR_003.SEN3'}
    ],
    'operation': 'reproject',
    'params': {
        'pixelSizeX': 0.01, 
        'pixelSizeY': 0.01
    }
}

r = requests.post(url + '/snapshot_master', json=master)
```