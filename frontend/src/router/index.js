import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: '登录', public: true } },
  { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '仪表盘' } },
  { path: '/setup', name: 'setup', component: () => import('../views/SetupWizard.vue'), meta: { title: '初始化' } },
  { path: '/devices', name: 'devices', component: () => import('../views/Devices.vue'), meta: { title: '设备' } },
  { path: '/devices/:id', name: 'device-detail', component: () => import('../views/DeviceDetail.vue'), meta: { title: '设备详情' } },
  { path: '/network', name: 'network', component: () => import('../views/Network.vue'), meta: { title: '网络' } },
  { path: '/system', name: 'system', component: () => import('../views/SystemAnalysis.vue'), meta: { title: '系统分析' } },
  { path: '/lan', name: 'lan', component: () => import('../views/LanDevices.vue'), meta: { title: '连接设备' } },
  { path: '/alerts', name: 'alerts', component: () => import('../views/AlertRules.vue'), meta: { title: '告警规则' } },
  { path: '/logs', name: 'logs', component: () => import('../views/LogViewer.vue'), meta: { title: '系统日志' } },
  { path: '/settings', name: 'settings', component: () => import('../views/Settings.vue'), meta: { title: '系统设置' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

async function getCurrentUser() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'same-origin' })
    if (!res.ok) return null
    return await res.json()
  } catch (e) {
    return null
  }
}

router.beforeEach(async (to) => {
  const user = await getCurrentUser()

  if (to.meta.public) {
    if (to.name === 'login' && user) {
      return to.query.next || '/'
    }
    return true
  }

  if (!user) {
    return {
      name: 'login',
      query: { next: to.fullPath },
    }
  }

  if (to.name === 'setup') return true

  try {
    const res = await fetch('/api/devices', { credentials: 'same-origin' })
    if (!res.ok) return true
    const devices = await res.json()
    if (!devices.length) {
      return {
        name: 'setup',
        query: { next: to.fullPath },
      }
    }
  } catch (e) {
    return true
  }

  return true
})

export default router
