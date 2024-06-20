<template>
    <table class="snapshot_list" cellpadding="0" cellspacing="0">
        <thead class="listHeader">
            <tr>
                <th>
                    {{ header + ' (' + this.snapshotList.length + '):'}}
                </th>
                <th>
                    <button 
                        type="button" 
                        class="btn-primary btn-list" 
                        @click="getFile(this.chosenFiles)">{{ buttonGetChosen }}
                    </button>
                </th>
                <th v-if="this.header == 'Скачанные файлы'">
                    <button 
                        type="button" 
                        class="btn-primary btn-list btn-logo" 
                        @click="saveAs([response])"><img src='../../assets/save_as.svg' class="icon" alt="Сохранить как">
                    </button>
                </th>
                <th v-if="this.header == 'Скачанные файлы'">
                    <button 
                        type="button" 
                        class="btn-primary btn-list btn-delete btn-logo" 
                        @click="deleteFile(this.chosenFiles)"><img src='../../assets/trash_can.svg' class="icon" alt="Удалить">
                    </button>
                </th>
                <th>
                    <input type="checkbox" v-model="masterCheck" @change="checkAll()">
                </th>
                <th v-if="this.header == 'Найденные файлы'">
                    <button 
                        type="button" 
                        class="btn-primary btn-list" 
                        @click="getAndProcess(this.chosenFiles, {'operation': 'reproject'})">{{ buttonDownloadProcess }}
                    </button>
                </th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(response, index) in snapshotList" :key="index" class="listRow">
                <td class="listEl">{{ response['timeBegin'] }} - {{ response['timeEnd'] }}</td>
                <td class="listEl">{{ response['satellite'] }}</td>
                <td class="listEl">{{ response['instrument'] }}</td>
                <td class="listEl">Level {{ response['processLevel'] }}</td>
                <td>
                    <button 
                        type="button" 
                        class="btn-primary btn-list" 
                        @click="getFile([response])">{{ buttonGet }}
                    </button>
                </td>
                <td v-if="this.header == 'Скачанные файлы'">
                    <button 
                        type="button" 
                        class="btn-primary btn-list btn-logo" 
                        @click="saveAs([response])"><img src='../../assets/save_as.svg' class="icon" alt="Сохранить как">
                    </button>
                </td>
                <td v-if="this.header == 'Скачанные файлы'">
                    <button 
                        type="button" 
                        class="btn-primary btn-list btn-delete btn-logo" 
                        @click="deleteFile([response])"><img src='../../assets/trash_can.svg' class="icon" alt="Удалить">
                    </button>
                </td>
                <td>
                    <input type="checkbox" :id="index" :value="response" v-model="chosenFiles">
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import trash_can from '../../assets/trash_can.svg'

export default {
    props: ['header' ,'snapshotList'],
    data() {
        let buttonGet
        let buttonDelete
        let buttonGetChosen
        let buttonDeleteChosen
        let buttonDownloadProcess = 'Скачать и обработать'
        let buttonSaveAs = 'Сохранить как'
        return {
            buttonGet,
            buttonDelete,
            buttonGetChosen,
            buttonDeleteChosen,
            buttonDownloadProcess,
            buttonSaveAs,
            chosenFiles: [],
            masterCheck: false
        }
    },
    methods: {
        getFile(chosenFiles){
            if (chosenFiles.length > 0){
                if (this.header == 'Скачанные файлы'){
                    this.$emit('openDownloadedFiles', chosenFiles)
                } 
                else if (this.header == 'Найденные файлы'){
                    this.$emit('downloadChosen', chosenFiles)
                }
            }
        },
        getAndProcess(chosenFiles, operationParams){
            this.$emit('getAndProcess', chosenFiles, operationParams)
        },
        saveAs(chosenFiles){
            this.$emit('saveAs', chosenFiles)
        },
        deleteFile(chosenFiles){
            if (chosenFiles.length > 0){
                this.$emit('buttonDeleteChosen', chosenFiles)
            }
        },
        checkAll(){
            if (!this.masterCheck){
                this.chosenFiles = []
                return
            }
            for (let i = 0; i < this.snapshotList.length; i++){
                this.chosenFiles.push(this.snapshotList[i])
            }
        }
    },
    created() {
        if (this.header == 'Скачанные файлы'){
            this.buttonGet = 'Открыть'
            this.buttonDelete = 'Удалить'
            this.buttonGetChosen = 'Открыть выбранные'
            this.buttonDeleteChosen = 'Удалить выбранные'
        }
        else if (this.header == 'Найденные файлы'){
            this.buttonGet = 'Скачать'
            this.buttonGetChosen = 'Скачать выбранные'
        }

    },
}
</script>
