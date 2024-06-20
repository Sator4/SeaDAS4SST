import { createRouter, createWebHistory } from 'vue-router'
import SnapshotManager from '@/components/snapshot_manager/SnapshotManager.vue'
import Authentication from '@/components/Authentication.vue'
import SnapshotMaster from '@/components/snapshot_master/SnapshotMaster.vue' 

const routes = [
  {
    path: '/',
    name: 'Authentication',
    component: Authentication
  },
  {
    path: '/snapshot_manager',
    name: 'Snapshot Manager',
    component: SnapshotManager
  },
  {
    path: '/snapshot_master',
    name: 'Snapshot Master',
    component: SnapshotMaster,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
