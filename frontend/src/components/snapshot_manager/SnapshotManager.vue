<template>
    <DeleteWarning v-if="showWarning" @deleteConfirm="deleteChosen" />
    <div class="row">
        <button class="btn btn-primary" @click="exit()" style="float: right; margin: 5px 30px;">
            Выйти
        </button>
        <SearchFilters 
            @makeSearchRequest="makeSearchRequest" 
            @refreshSearchList="getResultsList" 
            @clearSearchList="clearSearchList"
            @searchAndProcess="searchAndProcess"
        />
        <SnapshotList header='Скачанные файлы' 
            :snapshotList="downloadedFiles" 
            @openDownloadedFiles="openDownloadedFiles"
            @deleteChosen="deleteChosen"
            @saveAs='saveAs'
        />
        <SnapshotList header='Найденные файлы' 
            :snapshotList="responsesFromEumetsat" 
            v-if="responsesFromEumetsat.length" 
            @makeDownloadRequest="downloadChosen"
            @downloadChosen="downloadChosen"
            @getAndProcess="getAndProcess"
        />
    </div>
</template>




<script>
import axios from 'axios'
import SearchFilters from './SearchFilters.vue'
import SnapshotList from './SnapshotList.vue'
import DeleteWarning from './DeleteWarning.vue'
import router from '../../router'
import { useStore } from '../../stores/ChosenFilesStore.js'
import { operation1, sortGoodFiles } from '../snapshot_master/functions.js'
import { storeToRefs } from 'pinia'

export default {
    data() {
        let downloadPercantage = 0
        return {
            path: 'http://localhost:5000/snapshot_manager',
            downloadPercantage,
            responsesFromEumetsat: [],
            downloadedFiles: [],
            showWarning: false,
            jobNotification: storeToRefs(useStore()).jobNotification,
            goodFiles: [],
            downloadConnection: null
        }
    },
    components: {
        SearchFilters,
        SnapshotList,
        DeleteWarning
    },
    methods: {
        async getResultsList(){
            const path = this.path
            await axios.get(path)
            .then((res) => {
                this.responsesFromEumetsat = res.data.responses
                this.downloadedFiles = res.data.downloaded
                if (this.goodFiles.length > 0){
                    this.responsesFromEumetsat = this.goodFiles
                }
            })
            .catch((error) =>{
                console.log(error)
            })

        },
        async makeSearchRequest(searchRequest){
            if (!this.jobNotification){
                this.jobNotification = 'Поиск'
            }
            this.goodFiles = []
            const path = this.path
            await axios.post(path, searchRequest)
            .catch((error) => {
                console.log(error)
            })
            await this.getResultsList()
            this.jobNotification = ''
        },
        clearSearchList(){
            this.jobNotification = ''
            const path = this.path
            axios.delete(path)
            .then(() => {
                this.getResultsList()
            })
            .catch((error) =>{
                console.log(error)
            })
        },

        async downloadChosen(chosenFiles){
            if (!this.jobNotification){
                this.jobNotification = 'Скачивание'
            }
            // const path = 'ws' + this.path.substring(4) + '/download'
            // this.downloadConnection = new WebSocket(path)
            // this.downloadConnection.onopen = (() => {
                //     this.downloadConnection.send(JSON.stringify({'files': chosenFiles}))
            // })

            // this.downloadConnection.onmessage = ((msg) => {
                //     console.log(msg.data)
            // })
            const path = this.path + '/download'
            await axios.post(path, {'files': chosenFiles})
            .then(() => {
                this.getResultsList()
            })
            .catch((error) => {
                console.log(error)
            })
            this.jobNotification = ''
        },
        getAndProcess(chosenFiles, operationParams = {'operation': 'reproject', 'params': {'pixelSizeX': 0.01, 'pixelSizeY': 0.01}}){
            this.goodFiles = sortGoodFiles(operationParams['operation'], chosenFiles)[0]
            const path = this.path + '/download'
            this.responsesFromEumetsat = this.goodFiles
            this.downloadChosen(this.goodFiles)
            .then(() => {
                if (!this.goodFiles){
                    console.log('Скачанных файлов нет')
                }
                else {
                    operation1(operationParams['operation'], true, this.goodFiles, operationParams['params'])
                }
            })
            .catch((error) => {
                console.log(error)
            })
        },

        searchAndProcess(searchRequest){
            this.makeSearchRequest(searchRequest)
            .then(() => {
                this.getAndProcess(this.responsesFromEumetsat)
            })
            .catch((error) => {
                console.log(error)
            })
        },

        openDownloadedFiles(chosenFiles){
            useStore().chosenFiles = chosenFiles
            router.push({name: 'Snapshot Master'})
            .catch((error) => {
                console.log(error)
            })
        },

        deleteFile(productId){
            const path = this.path + '/delete'
            axios.post(path, {'id': productId})
            .then(() => {
                this.getResultsList()
            })
            .catch((error) => {
                console.log(error)
            })
        },
        deleteChosen(chosenFiles, allowDelete=false){
            if (!this.showWarning){
                useStore().chosenFiles = chosenFiles
                this.showWarning = true
            }
            else {
                this.showWarning = false
                if (allowDelete == true){
                    for (let i = 0; i < useStore().chosenFiles.length; i++){
                        this.deleteFile(useStore().chosenFiles[i])
                    }
                }
                useStore().chosenFiles = []
            }
        },

        saveAs(chosenFiles){
            const path = this.path + '/saveas'
            // {"chosenFiles": [{"id": "S3B_SL_2_WST____20240518T000031_20240518T000331_20240518T020732_0179_093_116_1620_MAR_O_NR_003.SEN3"}], "responseType": "blob"}
            axios.post(path, {'chosenFiles': chosenFiles, responseType: 'blob'})
            .then((res) => {
                console.log(res.data)
                let fileUrl = window.URL.createObjectURL(new Blob([res.data]))
                let fileLink = document.createElement('a')
                fileLink.href = fileUrl
                fileLink.setAttribute('download', chosenFiles[0]['id'] + '.zip')
                document.body.appendChild(fileLink)
                fileLink.click()
            })
            .catch((err) => {
                console.log(err)
            })
        },
        exit(){
            const path = this.path + '/exit'
            axios.post(path)
            .then((res) => {
                router.push(res.data.link)
            })
            .catch((error) => {
                console.log(error)
            })
        },
    },
    mounted() {
        this.getResultsList()
    }
}
</script>

<style>
    form {
        max-width: 400px;
        min-width: 300px;
        margin: 0px 0px 0px 50px;
        /* background: #f00; */
        border: #555;
        /* border-style: solid; */
        border-width: 1px;
        text-align: left;
        padding: 10px 0px 20px 20px;
        border-radius: 0px;
        float: left;
    }
    label, h1, h2, h3 {
        color: #555;
        font-family: Calibri;
        font-weight: bold;
    }
    input {
        display: block;
        margin-top: 7px;
        margin-bottom: 15px;
        padding: 8px 6px;
        width: 80%;
        max-width: 250px;
        box-sizing: border-box;
        border: solid;
        color: #000
    }
    select {
        display: block;
        margin-top: 7px;
        margin-bottom: 15px;
        padding: 6px 6px;
        width: 60%;
        box-sizing: border-box;
        border: solid;
        color: #666;
        background-color: #fff;
    }
    /* .pill {
        display: inline-block;
        margin: 20px 10px 0 0;
        padding: 6px 12px;
        background: #eee;
        border-radius: 20px;
        font-size: 12px;
        letter-spacing: 1px;
        font-weight: bold;
        color: #777;
        cursor: pointer;
    } */
    .btn {
        padding: 10px 15px;
        margin-top: 20px;
        border-radius: 0px;
        font-size: 14px;
        max-width: 250px;
    }
    .btn-primary {
        color: white;
        border: 0;
        background: #593196;
    }
    .btn-primary:hover {
        background-color: #482879;
    } 
    .btn-primary:active {
        background: #391f5f;
    }
    .btn-secondary {
        border: #ccc;
        border-style: solid;
        border-width: 1px;
        background: white;
    }
    .btn-secondary:hover {
        background-color: #eee;
    }
    .btn-secondary:active {
        background-color: #906ec4;
        color: #fff;
    }
    .submit {
        text-align: center;
    }
    .error {
        color: #ff0062;
        margin-top: 10px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .snapshot_list {
        /* border-style: solid; */
        /* background: red; */
        /* border-width: 1px; */
        margin: 50px 50px;
        display: grid;
        min-width: 800px;
        max-width: 850px;
    }
    .listHeader {
        color: #333;
        background: rgba(0, 0, 150, 0.2);
        font-family: Calibri;
        font-size: 22px;
        padding: 5px 10px;
    }
    .listRow {
        background: rgba(0, 0, 150, 0.1);
        margin: 10px;
    }
    .listRow:hover {
        background: rgba(0, 0, 150, 0.17);;
    }
    .listEl {
        padding: 0px 15px;
    }
    .btn-list {
        padding: 8px 10px;
        margin: 7px 10px;  /* top right bottom left or top+bottom right+left*/
        border-radius: 2px;
    }
    .btn-delete {
        background: #821c71;
    }
    .btn-delete:hover {
        background: #601554;
    }
    .btn-delete:active {
        background: #4a1041;
    }
    .btn-logo {
        padding: 5px 8px 3px 8px;
    }
    .icon {
        max-height: 20px;
    }
    input[type="checkbox"] {
        display: inline-block;
        width: 18px;
        height: 18px;
        margin: 10px 10px;
        position: relative;
        bottom: 1px;
    }
</style>