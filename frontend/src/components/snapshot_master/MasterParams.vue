<template>
    <form>
        <h2>Мастер снимков</h2>

        <label>Операция:</label>
        <select v-model="chosenOperation">
            <option value="reproject">reproject</option>
            <option value="l2gen">l2gen</option>
        </select>


        <div v-if="chosenOperation == 'reproject'">
            <label>Угол поворота:</label>
            <input type="text" v-model="orientation">
            
            <label>Размер пикселя по X (градусов):</label>
            <input type="text" v-model="pixelSizeX">
            
            <label>Размер пикселя по Y (градусов):</label>
            <input type="text" v-model="pixelSizeY">

            <label>Вывести сетку:</label>
            <select v-model="addDeltaBands">
                <option value="true">Да</option>
                <option value="false">Нет</option>
            </select>
            
            <button 
                type="button" 
                class="btn-primary btn-list" 
                @click="reproject()">reproject
            </button>
        </div>

        <label v-if="chosenOperation == 'l2gen'">Параметры:</label>
        <div v-if="chosenOperation == 'l2gen'">
            <textarea v-model="l2genParams" cols="25" rows="5"></textarea>
        </div>
        <div v-if="chosenOperation == 'l2gen'">
            <button 
                type="button" 
                class="btn-primary btn-list" 
                @click="l2gen()">l2gen
            </button>
        </div>

        <div>
            <button
                type="button"
                class="btn-primary btn-list"
                @click="reset()">Сброс
            </button>
        </div>
    </form>
</template>

<script>
export default {
    data() {
        return {
            chosenOperation: '',
            l2genParams: '',
            orientation: 0,
            pixelSizeX: 0.01,
            pixelSizeY: 0.01,
            addDeltaBands: 'false'
        }
    },
    methods: {
        reproject(){
            let reprojectParams = {
                'orientation': this.orientation, 
                'pixelSizeX': this.pixelSizeX, 
                'pixelSizeY': this.pixelSizeY,
                'addDeltaBands': this.addDeltaBands.toString()
                }
            this.$emit("warning", 'reproject', reprojectParams)
        },
        l2gen(){
            this.$emit("warning", 'l2gen', this.l2genParams)
        },
        reset(){
            this.chosenOperation = '',
            this.l2genParams = '',
            this.orientation = 0,
            this.pixelSizeX = 0.01,
            this.pixelSizeY = 0.01
        }
    }
}
</script>

<style scoped>
</style>