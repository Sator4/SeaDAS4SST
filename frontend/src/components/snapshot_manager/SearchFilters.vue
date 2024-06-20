<template>
    <!-- <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootswatch/5.3.3/pulse/bootstrap.min.css"> -->
    <form>
        <label>Начало временного отрезка:</label>
        <input type="text" v-model="begin_date" placeholder="2023-12-31T00:00">

        <label>Конец временного отрезка:</label>
        <input type="text" v-model="end_date" placeholder="2023-12-31T23:59">

        <label>Координаты:</label>
        <input type="text" v-model="coords" placeholder="запад юг восток север">

        <div>
            <input type="checkbox" v-model="fullBox">
            <label>Снимок закрывает всю область</label>
        </div>

        <label>Спутник:</label>
        <select v-model="satellite"> <!-- add event to change instrument list -->
            <option value="Sentinel-3">Sentinel-3</option>
            <!-- <option value="Sentinel-2">Sentinel-2</option> -->
        </select>

        <div class="instrument" v-if="satellite">
            <label>Прибор:</label>
            <select v-model="instrument">
                <option v-for="i in instruments" :key="i" :value="i">{{ i }}</option>
            </select>
        </div>

        <div class="processLevel" v-if="instrument">
            <label>Уровень обработки:</label>
            <select v-model="processLevel">
                <option v-for="pl in processLevels" :key="pl" :value="pl">{{ pl }}</option>
            </select>
        </div>

        <div class="action">
            <button
                type="button"
                class="btn btn-primary" 
                @click="makeSearchRequest({begin_date, end_date, coords, satellite, instrument, processLevel, fullBox})">{{ 'Поиск' }}
            </button>
            <button 
                type="button" 
                class="btn btn-secondary" 
                @click="clearSearchList()">{{ 'Сброс' }}
            </button>
            <button 
                type="button" 
                class="btn btn-secondary" 
                @click="refreshSearchList()">{{ 'Обновить' }}
            </button>
            <button 
                type="button" 
                class="btn btn-primary" 
                @click="searchAndProcess({begin_date, end_date, coords, satellite, instrument, processLevel, fullBox})">{{ 'Найти, скачать и обработать' }}
            </button>
            <p v-if="this.jobNotification">
                {{ this.jobNotification }}
            </p>
        </div>
    </form>
</template>

<script>
import axios from 'axios'
import router from '../../router'
import SearchFilters from './SearchFilters.vue'
import { useStore } from '../../stores/ChosenFilesStore.js'
import { storeToRefs } from 'pinia'

export default {
    data() {
        let begin_date = ''
        let end_date = ''
        return {
            begin_date,
            end_date,
            instruments: ['SLSTR', 'OLCI'],
            processLevels: ['1', '2'],
            satellite: '',
            instrument: '',
            processLevel: '',
            intervalId: '',
            coords: '',
            fullBox: '',
            jobNotification: storeToRefs(useStore()).jobNotification
        }
    },
    watch: {
        jobNotification(){
            if (this.jobNotification){
                let initLen = this.jobNotification.search(/[.]/)
                if (initLen == -1){
                    initLen = this.jobNotification.length
                }
                this.intervalId = setInterval(() => {
                    this.jobNotification = this.jobNotification + '.'
                    if (this.jobNotification.length > initLen + 5){
                        this.jobNotification = this.jobNotification.substring(0, initLen+1)
                    }
                    clearInterval(this.intervalId)
                    }, 400)
            }
            else {
                clearInterval(this.intervalId)
            }
        }
    },
    components: {
        SearchFilters
    },
    methods: {
        makeSearchRequest(searchRequest){
            this.$emit('makeSearchRequest', searchRequest)
        },
        refreshSearchList(){
            this.$emit('refreshSearchList')
        },
        clearSearchList(){
            this.$emit('clearSearchList')
        },
        searchAndProcess(searchRequest){
            this.$emit('searchAndProcess', searchRequest)
        }
    },
    // mounted() {
    //     setInterval(()=>{
    //         console.log(this.jobNotification)
    //     }, 1000)
    // },
}
</script>

<style scoped>
    input[type="checkbox"] {
        display: inline-block;
        width: 16px;
        margin: 0 10px 25px 0px;
        position: relative;
        top: 1px;
    }
</style>