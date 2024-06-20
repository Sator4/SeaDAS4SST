<template>
    <div class="backdrop">
        <div class="modal">
            <h3>
                Вы уверены, что хотите удалить выбранные файлы?
            </h3>
            <button 
                type="button" 
                class="btn-primary btn-list" 
                @click="this.$emit('deleteConfirm', [], true)">Да
            </button>
            <button 
                type="button" 
                class="btn-primary btn-list" 
                @click="this.$emit('deleteConfirm', [], false)">Нет
            </button>
        </div>
    </div>
</template>

<script>
export default {

}
</script>

<style scoped>
    .modal {
        width: 500px;
        padding: 20px;
        margin: 100px auto;
        background: white;
        text-align: center;
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