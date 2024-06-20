import axios from "axios"
import { useStore } from '../../stores/ChosenFilesStore.js'

async function operation1(operation, proceed, goodFiles, params){
    if (proceed){
        if (!useStore().jobNotification){
            useStore().jobNotification = 'Обработка'
        }
        const path = 'http://localhost:5000/snapshot_master'
        await axios.post(path, {'files': goodFiles, 'operation': operation, 'params': params})
        .then(() => {
            console.log('Success!')
        })
        .catch((error) => {
            console.log(error)
        })
        useStore().jobNotification = ''
    }
    else {
        // console.log('Увы и ах, ' + operation + ' отменяется')
    }
}

function sortGoodFiles(operation, chosenFiles){
    let goodFiles = []
    let badFiles = []
    if (operation == 'l2gen'){
        for (let i = 0; i < chosenFiles.length; i++){
            if (chosenFiles[i]['processLevel'] == 2){
                badFiles.push(chosenFiles[i]['id'])
            }
            else if (chosenFiles[i]['instrument'] == 'SLSTR'){
                badFiles.push(chosenFiles[i]['id'])
            }
            else {
                goodFiles.push(chosenFiles[i]['id'])
            }
        }
    }
    else if (operation == 'reproject'){
        for (let i = 0; i < chosenFiles.length; i++){
            if (chosenFiles[i]['timeLength'] < 500){
                goodFiles.push(chosenFiles[i])
            }
        }
    }
    return [goodFiles, badFiles]
}


export {operation1, sortGoodFiles}