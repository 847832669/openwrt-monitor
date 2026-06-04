import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Devices from '../views/Devices.vue'
import Network from '../views/Network.vue'
import LanDevices from '../views/LanDevices.vue'
import SystemAnalysis from '../views/SystemAnalysis.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard, meta: { title: '仪表盘' } },
  { path: '/devices', name: 'devices', component: Devices, meta: { title: '设备' } },
  { path: '/network', name: 'network', component: Network, meta: { title: '网络' } },
  { path: '/system', name: 'system', component: SystemAnalysis, meta: { title: '系统分析' } },
  { path: '/lan', name: 'lan', component: LanDevices, meta: { title: '连接设备' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
