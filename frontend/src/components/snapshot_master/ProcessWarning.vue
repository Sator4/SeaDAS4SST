<template>
    <div class="backdrop">
        <div class="modal">
            <h3>
                Вы собираетесь выполнить операцию {{ operationWarning }} над {{ fileAmountProceed }} файлами. 
            </h3>
            <h3 v-if="fileAmountReject > 0">
                {{ fileAmountReject }} файлов не будет обработано: 
            </h3>
            <p v-for="file in badFiles" class="textLine">
                {{ file }}
            </p>
            <button
                type="button" 
                class="btn-primary btn-list" 
                @click="this.$emit('operation', operationWarning, true)">Подтвердить
            </button>
            <button 
                type="button" 
                class="btn-primary btn-list btn-delete" 
                @click="this.$emit('operation', operationWarning, false)">Отказаться
            </button>
        </div>
    </div>
</template>

<script>
export default {
    props: ['fileAmountReject', 'fileAmountProceed', 'badFiles', 'operationWarning']
}
</script>

<style scoped>
    .modal {
        width: 500px;
        padding: 20px;
        margin: 100px auto;
        background: white;
        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .textLine {
        text-align: left;
    }
    .backdrop {
        top: 0;
        left: 0;
        position: fixed;
        background: rgba(0, 0, 0, 0.5);
        width: 100%;
        height: 100%;
    }
    .btn-primary {
        min-width: 75px;
        min-height: 30px;
        margin: 5px 30px;
    }
</style>