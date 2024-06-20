<template>
    <div class="row">
        <button class="btn btn-primary" @click="exit()" style="float: left; margin: 5px 50px 0px 20px;">
            Назад
        </button>
        <ProceedWarning v-if="showWarning" :fileAmountProceed="goodFiles.length" :fileAmountReject="badFiles.length" :badFiles="badFiles" :operationWarning="operationWarning" @operation="operation"/>
        <MasterParams  @warning="warning"/>
        <MasterList :snapshotList="this.chosenFiles"/>
    </div>
</template>

<script>
import axios from 'axios'
import { useStore } from '../../stores/ChosenFilesStore.js'
import MasterList from './MasterList.vue'
import MasterParams from './MasterParams.vue'
import ProceedWarning from './ProcessWarning.vue'
import router from '../../router/index.js'
import { operation1, sortGoodFiles } from './functions.js'


export default {
    data() {
        let operationParams
        return {
            path: 'http://localhost:5000/snapshot_master',
            chosenFiles: useStore().chosenFiles,
            goodFiles: [],
            badFiles: [],
            showWarning: false,
            operationWarning: '',
            operationParams
        }
    },
    components: {
        MasterList,
        MasterParams,
        ProceedWarning
    },
    methods: {
        warning(operation, params){
            let wrapLine = 55
            let wrapList = 10
            this.operationParams = params
            let sorted = sortGoodFiles(operation, this.chosenFiles)
            this.goodFiles = sorted[0]
            this.badFiles = sorted[1]
            if (this.badFiles.length > wrapList){
                this.badFiles = this.badFiles.slice(0, wrapList)
                this.badFiles.push('...')
            }
            for (let i = 0; i < this.badFiles.length; i++){
                if (this.badFiles[i].length > wrapLine){
                    this.badFiles[i] = this.badFiles[i].slice(0, wrapLine) + '...'
                }
            }
            this.operationWarning = operation
            // if (this.goodFiles.length > 1){
            //     this.showWarning = true
            // }
            // else {
            //     this.operation(operation, true)
            // }
            this.showWarning = true
        },

        operation(operation, proceed, goodFiles=this.goodFiles){
            this.showWarning = false
            operation1(operation, proceed, goodFiles, this.operationParams)
        },

        exit(){
            router.push({name: 'Snapshot Manager'})
            .catch((error) => {
                console.log(error)
            })
        }
    },
    mounted() {
        const path = this.path
        axios.post(path, {'files': this.chosenFiles, 'operation': 'getFullData'})
        .then((res) => {
            this.chosenFiles = res.data.downloaded
        })
        .catch((error) => {
            console.log(error)
        })
    }
}
</script>

<style>

</style>