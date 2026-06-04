<template>
  <div class="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
    <!-- 侧边栏 -->
    <aside class="w-56 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
      <div class="p-5 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-2xl">📶</span>
          <div>
            <h1 class="text-base font-bold text-white">OpenWrt</h1>
            <p class="text-xs text-slate-400">性能监控平台</p>
          </div>
        </div>
        <!-- 告警铃铛 -->
        <button @click="showAlerts = !showAlerts" class="relative">
          <span class="text-xl">🔔</span>
          <span v-if="alertList.length > 0"
            class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5 font-bold">
            {{ alertList.length > 99 ? '99+' : alertList.length }}
          </span>
        </button>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <router-link
          v-for="item in navItems" :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
          :class="$route.path === item.path
            ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="p-4 border-t border-slate-800 space-y-2">
        <div class="flex items-center justify-between text-xs text-slate-500">
          <div class="flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full"
              :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'"></span>
            {{ wsConnected ? '实时连接中' : '已断开' }}
          </div>
          <div class="flex items-center gap-2">
            <a href="https://github.com/847832669/openwrt-monitor" target="_blank"
              class="text-slate-500 hover:text-slate-300 transition-colors" title="GitHub">
              <svg viewBox="0 0 16 16" class="w-4 h-4 fill-current"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            </a>
            <button @click="toggleTheme" class="text-base" :title="'切换' + themeMap[theme].label">
              {{ themeMap[theme].icon }}
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-slate-600">{{ themeMap[theme].label }}</span>
          <span class="text-slate-600">v{{ appVersion }}</span>
        </div>
        <!-- 更新提示 -->
        <div v-if="updateAvailable"
          class="bg-brand-600/20 border border-brand-700/30 rounded-lg px-2 py-1.5 text-center">
          <a href="https://github.com/847832669/openwrt-monitor/releases" target="_blank"
            class="text-brand-300 text-xs hover:underline">
            🆕 v{{ latestVersion }} 可用
          </a>
        </div>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 overflow-auto relative">
      <router-view />

      <!-- 告警面板 -->
      <div v-if="showAlerts"
        class="absolute top-4 right-4 w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 max-h-[70vh] flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <h3 class="text-sm font-semibold text-white">🔔 告警</h3>
          <div class="flex gap-2">
            <button @click="clearAlerts" class="text-xs text-slate-500 hover:text-slate-300">清除</button>
            <button @click="showAlerts = false" class="text-slate-500 hover:text-white">✕</button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-2 space-y-1">
          <div v-if="alertList.length === 0" class="text-center py-8 text-slate-500 text-sm">
            ✅ 暂无告警
          </div>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWebSocket } from './composables/useWebSocket'

const { connected: wsConnected, lastMessage } = useWebSocket()
const showAlerts = ref(false)
const alertList = ref([])
const theme = ref(localStorage.getItem('theme') || '')

// 从 WebSocket 消息中提取告警
onMounted(() => {
  // 每秒检查一次新消息
  setInterval(() => {
    const msg = lastMessage.value
    if (msg && msg.type === 'alert' && msg.alert) {
      const exists = alertList.value.some(a => a.id === msg.alert.id)
      if (!exists) {
        alertList.value.unshift(msg.alert)
        if (alertList.value.length > 100) alertList.value = alertList.value.slice(0, 100)
      }
      lastMessage.value = null // 已消费
    }
  }, 1000)

  // 加载历史告警
  fetch('/api/alerts').then(r => r.json()).then(d => {
    alertList.value = d.alerts || []
  }).catch(() => {})
})

function clearAlerts() {
  alertList.value = []
  fetch('/api/alerts', { method: 'DELETE' }).catch(() => {})
}

function formatAlertTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return d.getHours().toString().padStart(2,'0') + ':' +
         d.getMinutes().toString().padStart(2,'0') + ':' +
         d.getSeconds().toString().padStart(2,'0')
}
// 版本
const appVersion = ref('0.1.0')
const latestVersion = ref(null)
const updateAvailable = ref(false)

// 检查更新
async function checkUpdate() {
  try {
    const res = await fetch('/api/version')
    const ver = await res.json()
    appVersion.value = ver.version

    // 从 GitHub API 查最新版本
    const gh = await fetch('https://api.github.com/repos/847832669/openwrt-monitor/releases/latest', {
      headers: { 'Accept': 'application/vnd.github+json' }
    })
    if (!gh.ok) return
    const release = await gh.json()
    const latest = release.tag_name.replace(/^v/, '')
    latestVersion.value = latest

    // 比较版本号
    const cur = appVersion.value.split('.').map(Number)
    const lat = latest.split('.').map(Number)
    for (let i = 0; i < Math.max(cur.length, lat.length); i++) {
      if ((lat[i] || 0) > (cur[i] || 0)) {
        updateAvailable.value = true
        break
      }
    }
  } catch (e) {
    // 静默失败（GitHub API 限流等）
  }
}

const themeMap = { '': { next: 'warm', icon: '☀️', label: '极夜' }, 'warm': { next: 'oled', icon: '🌙', label: '暖阳' }, 'oled': { next: '', icon: '🖤', label: 'OLED' } }

function toggleTheme() {
  const info = themeMap[theme.value]
  theme.value = info.next
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

// 初始化主题 + 版本检查
onMounted(() => {
  if (theme.value) {
    document.documentElement.setAttribute('data-theme', theme.value)
  }
  checkUpdate()
})

const navItems = [
  { path: '/', icon: '📊', label: '仪表盘' },
  { path: '/system', icon: '📈', label: '系统分析' },
  { path: '/network', icon: '🌐', label: '网络分析' },
  { path: '/lan', icon: '🖥️', label: '连接设备' },
  { path: '/alerts', icon: '🔔', label: '告警规则' },
  { path: '/logs', icon: '📋', label: '系统日志' },
  { path: '/devices', icon: '⚙️', label: '设备管理' },
]
</script>
