<template>
    <table class="snapshot_list" cellpadding="0" cellspacing="0">
        <tr v-for="name in snapshotList" class="listRow">
            <td class="listEl">{{ name['id'] }}</td>
        </tr>
        <!-- <tr v-for="(response, index) in snapshotList" :key="index" class="listRow">
            <td class="listEl">{{ response['timeBegin'] }} - {{ response['timeEnd'] }}</td>
            <td class="listEl">{{ response['satellite'] }}</td>
            <td class="listEl">{{ response['instrument'] }}</td>
            <td class="listEl">Level {{ response['processLevel'] }}</td>
        </tr> -->
    </table>
</template>

<script>
export default {
    props: ['snapshotList']
}
</script>

<style scoped>
    .snapshot_list {
        /* background: red; */
        padding-top: 25px;
    }
    .listRow {
        padding: 10px;
        margin: 5px;
    }
    .listRow:hover{
        background: rgba(0, 0, 150, 0.1);
    }
</style>