<template>
  <div class="h-screen bg-slate-950 text-slate-100 overflow-hidden flex flex-col">
    <!-- ===== 桌面端侧边栏 ===== -->
    <aside :class="[
      'fixed inset-y-0 left-0 z-40 w-56 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-300 lg:translate-x-0',
      sidebarOpen ? 'translate-x-0' : '-translate-x-full'
    ]">
      <div class="p-4 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-2xl">📶</span>
          <div>
            <h1 class="text-base font-bold text-white">OpenWrt</h1>
            <p class="text-xs text-slate-400">性能监控平台</p>
          </div>
        </div>
        <!-- 关闭按钮（手机端） -->
        <button @click="sidebarOpen = false" class="lg:hidden text-slate-400 hover:text-white text-lg">✕</button>
      </div>
      <nav class="flex-1 p-2 space-y-0.5 overflow-auto">
        <router-link v-for="item in navItems" :key="item.path"
          :to="item.path"
          @click="sidebarOpen = false"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors whitespace-nowrap"
          :class="$route.path === item.path
            ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'"
        >
          <span class="text-lg shrink-0">{{ item.icon }}</span>
          <span class="truncate">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="p-3 border-t border-slate-800 space-y-1.5">
        <div class="flex items-center justify-between text-xs text-slate-500">
          <div class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full"
              :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'"></span>
            {{ wsConnected ? '连接中' : '断开' }}
          </div>
          <div class="flex items-center gap-1.5">
            <a href="https://github.com/847832669/openwrt-monitor" target="_blank"
              class="text-slate-500 hover:text-slate-300 transition-colors">
              <svg viewBox="0 0 16 16" class="w-3.5 h-3.5 fill-current"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            </a>
            <button @click="toggleTheme" class="text-sm" :title="'切换' + themeMap[theme].label">
              {{ themeMap[theme].icon }}
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-slate-600">{{ themeMap[theme].label }}</span>
          <button @click="checkUpdate" class="text-slate-600 hover:text-brand-300 transition-colors" title="点击检查更新">
            v{{ appVersion }}{{ checkingVer ? ' 🔍' : '' }}
          </button>
        </div>
        <div v-if="updateAvailable"
          class="bg-brand-600/20 border border-brand-700/30 rounded-lg px-2 py-1 text-center">
          <a href="https://github.com/847832669/openwrt-monitor/releases" target="_blank"
            class="text-brand-300 text-xs hover:underline">
            🆕 v{{ latestVersion }} 可用
          </a>
        </div>
      </div>
    </aside>

    <!-- 手机端侧边栏遮罩 -->
    <div v-if="sidebarOpen" @click="sidebarOpen = false"
      class="fixed inset-0 z-30 bg-black/50 lg:hidden"></div>

    <!-- ===== 主内容区 ===== -->
    <div class="flex-1 flex flex-col min-h-0 lg:ml-56">
      <!-- 顶部导航条（手机端） -->
      <header class="lg:hidden flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 shrink-0">
        <button @click="sidebarOpen = true" class="text-xl text-slate-300 hover:text-white">
          ☰
        </button>
        <div class="flex items-center gap-1 text-sm font-bold text-white">
          <span>📶</span> OpenWrt
        </div>
        <button @click="showAlerts = !showAlerts" class="relative text-xl">
          🔔
          <span v-if="alertList.length > 0"
            class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5 font-bold">
            {{ alertList.length > 99 ? '99+' : alertList.length }}
          </span>
        </button>
      </header>

      <!-- 页面内容 -->
      <main class="flex-1 overflow-auto">
        <router-view />

        <!-- 告警面板 -->
        <div v-if="showAlerts"
          class="fixed top-4 right-4 w-80 lg:w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 max-h-[70vh] flex flex-col">
          <div class="flex items-center justify-between px-4 py-3 border-b border-slate-800">
            <h3 class="text-sm font-semibold text-white">🔔 告警</h3>
            <div class="flex gap-2">
              <button @click="clearAlerts" class="text-xs text-slate-500 hover:text-slate-300">清除</button>
              <button @click="showAlerts = false" class="text-slate-500 hover:text-white">✕</button>
            </div>
          </div>
          <div class="flex-1 overflow-auto p-2 space-y-1">
            <div v-if="alertList.length === 0" class="text-center py-8 text-slate-500 text-sm">✅ 暂无告警</div>
            <div v-for="a in alertList" :key="a.id"
              class="flex items-start gap-2 p-2 rounded-lg text-xs"
              :class="a.level === 'crit' ? 'bg-red-900/20' : a.level === 'warn' ? 'bg-amber-900/20' : 'bg-slate-800/50'">
              <span>{{ a.level === 'crit' ? '🔴' : a.level === 'warn' ? '🟡' : '🔵' }}</span>
              <div class="flex-1 min-w-0">
                <div class="text-slate-200 font-medium">{{ a.title }}</div>
                <div class="text-slate-400 mt-0.5">{{ a.message }}</div>
                <div class="text-slate-600 mt-0.5">{{ formatAlertTime(a.time) }}</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- 手机端底部导航 -->
      <nav class="lg:hidden flex items-center justify-around bg-slate-900 border-t border-slate-800 px-1 py-1 shrink-0">
        <router-link v-for="item in mobileNav" :key="item.path"
          :to="item.path"
          class="flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] transition-colors min-w-0"
          :class="$route.path === item.path ? 'text-brand-300' : 'text-slate-500'">
          <span class="text-lg">{{ item.icon }}</span>
          <span class="truncate max-w-[3rem]">{{ item.label }}</span>
        </router-link>
      </nav>
      <!-- 更新检查 Toast -->
      <div v-if="checkToast"
        class="fixed bottom-20 lg:bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg text-sm shadow-lg transition-all"
        :class="checkToast.includes('✅') ? 'bg-green-900/80 text-green-300 border border-green-700/50' :
                checkToast.includes('🆕') ? 'bg-brand-600/80 text-brand-200 border border-brand-500/50' :
                'bg-slate-800 text-slate-300 border border-slate-600'">
        {{ checkToast }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const wsConnected = ref(false)
const sidebarOpen = ref(false)
const showAlerts = ref(false)
const alertList = ref([])
const appVersion = ref('0.4.0')
const latestVersion = ref(null)
const updateAvailable = ref(false)
const checkingVer = ref(false)
const checkToast = ref('')

async function checkUpdate() {
  checkingVer.value = true
  try {
    // 先获取本地版本
    const verRes = await fetch('/api/version')
    const verData = await verRes.json()
    appVersion.value = verData.version

    // 查 GitHub 最新 release
    const ghRes = await fetch('https://api.github.com/repos/847832669/openwrt-monitor/tags?per_page=5')
    if (!ghRes.ok) {
      checkToast.value = '无法检查更新'
      setTimeout(() => checkToast.value = '', 2000)
      return
    }
    const tags = await ghRes.json()
    const verTags = tags.map(t => t.name).filter(t => t.startsWith('v'))
    if (!verTags.length) {
      checkToast.value = '未找到版本信息'
      setTimeout(() => checkToast.value = '', 2000)
      return
    }
    const latest = verTags[0].replace(/^v/, '')
    latestVersion.value = latest

    const cur = appVersion.value.split('.').map(Number)
    const lat = latest.split('.').map(Number)
    let newer = false
    for (let i = 0; i < Math.max(cur.length, lat.length); i++) {
      if ((lat[i] || 0) > (cur[i] || 0)) { newer = true; break }
    }
    updateAvailable.value = newer

    if (newer) {
      checkToast.value = '🆕 v' + latest + ' 可用'
    } else {
      checkToast.value = '✅ 已是最新版本'
    }
  } catch (e) {
    checkToast.value = '⚠️ 检查失败'
  }
  checkingVer.value = false
  setTimeout(() => checkToast.value = '', 3000)
}

const theme = ref(localStorage.getItem('theme') || '')

const themeMap = {
  '': { next: 'warm', icon: '☀️', label: '极夜' },
  'warm': { next: 'oled', icon: '🌙', label: '暖阳' },
  'oled': { next: '', icon: '🖤', label: 'OLED' },
}

const navItems = [
  { path: '/', icon: '📊', label: '仪表盘' },
  { path: '/system', icon: '📈', label: '系统分析' },
  { path: '/network', icon: '🌐', label: '网络分析' },
  { path: '/lan', icon: '🖥️', label: '连接设备' },
  { path: '/logs', icon: '📋', label: '系统日志' },
  { path: '/alerts', icon: '🔔', label: '告警规则' },
  { path: '/devices', icon: '⚙️', label: '设备管理' },
]

const mobileNav = navItems.slice(0, 5)

function toggleTheme() {
  const info = themeMap[theme.value]
  theme.value = info.next
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

function formatAlertTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return d.getHours().toString().padStart(2, '0') + ':' +
    d.getMinutes().toString().padStart(2, '0') + ':' +
    d.getSeconds().toString().padStart(2, '0')
}

function clearAlerts() {
  alertList.value = []
  fetch('/api/alerts', { method: 'DELETE' }).catch(() => {})
}

// WebSocket 连接
import { onMounted, onUnmounted } from 'vue'
let ws = null
let pingTimer = null

function connectWS() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/metrics`)
  ws.onopen = () => { wsConnected.value = true }
  ws.onclose = () => {
    wsConnected.value = false
    setTimeout(connectWS, 3000)
  }
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.type === 'alert' && msg.alert) {
        const exists = alertList.value.some(a => a.id === msg.alert.id)
        if (!exists) {
          alertList.value.unshift(msg.alert)
          if (alertList.value.length > 100) alertList.value = alertList.value.slice(0, 100)
        }
      }
      if (msg.type === 'ping') ws?.send('pong')
    } catch { /* text pings */ }
  }
  pingTimer = setInterval(() => {
    if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
  }, 30000)
}

onMounted(() => {
  if (theme.value) document.documentElement.setAttribute('data-theme', theme.value)
  connectWS()
  fetch('/api/alerts').then(r => r.json()).then(d => { alertList.value = d.alerts || [] }).catch(() => {})
  // 版本检查
  fetch('/api/version').then(r => r.json()).then(v => { appVersion.value = v.version }).catch(() => {})
  fetch('https://api.github.com/repos/847832669/openwrt-monitor/tags?per_page=5')
    .then(r => r.ok ? r.json() : null).then(tags => {
      if (tags && tags.length) {
        // 找最新的 v* 标签
        const verTags = tags.map(t => t.name).filter(t => t.startsWith('v'))
        if (verTags.length) {
          const latest = verTags[0].replace(/^v/, '')
          latestVersion.value = latest
          const cur = appVersion.value.split('.').map(Number)
          const lat = latest.split('.').map(Number)
          updateAvailable.value = false
          for (let i = 0; i < Math.max(cur.length, lat.length); i++) {
            if ((lat[i] || 0) > (cur[i] || 0)) { updateAvailable.value = true; break }
          }
        }
      }
    }).catch(() => {})
})

onUnmounted(() => {
  clearInterval(pingTimer)
  ws?.close()
})
</script>
