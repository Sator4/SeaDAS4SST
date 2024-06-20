import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core"

export const useStore = defineStore('store', {
    state: () => {
        return {
            chosenFiles: useLocalStorage('chosenFiles', []),
            jobNotification: ''
        }
    }
})