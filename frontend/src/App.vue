<template>
  <router-view v-if="isLoginRoute" />

  <div v-else class="app-shell text-slate-100 overflow-hidden flex flex-col">
    <!-- ===== 桌面端侧边栏 ===== -->
    <aside :class="[
      'app-sidebar fixed inset-y-0 left-0 z-40 app-panel border-y-0 border-l-0 flex flex-col transition-transform duration-300 lg:translate-x-0',
      sidebarOpen ? 'translate-x-0' : '-translate-x-full'
    ]">
      <div class="p-4 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="grid place-items-center w-9 h-9 rounded-lg bg-brand-600/20 text-brand-300 text-lg">📶</span>
          <div>
            <h1 class="text-base font-bold text-white">OpenWrt</h1>
            <p class="text-xs text-slate-400">性能监控平台</p>
          </div>
        </div>
        <!-- 关闭按钮（手机端） -->
        <button @click="sidebarOpen = false" class="lg:hidden text-slate-400 hover:text-white text-lg">✕</button>
      </div>
      <nav class="flex-1 p-3 space-y-1 overflow-auto">
        <router-link v-for="item in navItems" :key="item.path"
          :to="item.path"
          @click="sidebarOpen = false"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors whitespace-nowrap border"
          :class="$route.path === item.path
            ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
            : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-slate-800/50 hover:border-slate-800'"
        >
          <span class="text-lg shrink-0">{{ item.icon }}</span>
          <span class="truncate">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="p-3 border-t border-slate-800 space-y-2">
        <router-link v-if="securityWarning" to="/settings"
          class="block rounded-lg border border-amber-400/30 bg-amber-900/20 px-2.5 py-2 text-xs text-amber-200 hover:border-amber-400/50">
          安全设置待处理
        </router-link>
        <div class="flex items-center justify-between text-xs text-slate-500">
          <div class="status-pill">
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
            <button @click="logout" class="text-xs text-slate-500 hover:text-slate-300 transition-colors" title="退出登录">
              退出
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-slate-600">{{ themeMap[theme].label }}</span>
          <div class="relative"
            @mouseenter="showChangelog = true"
            @mouseleave="showChangelog = false"
            @focusin="showChangelog = true"
            @focusout="showChangelog = false">
            <button @click="checkUpdate"
              class="text-slate-600 hover:text-brand-300 transition-colors"
              title="点击检查更新">
              v{{ appVersion }}{{ checkingVer ? ' 🔍' : '' }}
            </button>
            <div v-if="showChangelog"
              class="absolute bottom-full right-0 z-50 mb-2 w-72 max-w-[calc(100vw-2rem)] rounded-lg border border-slate-700 bg-slate-950/95 p-3 text-left text-xs shadow-2xl backdrop-blur">
              <div class="flex items-center justify-between gap-3">
                <div class="font-semibold text-white">v{{ changelog.version }} 更新日志</div>
                <a href="https://github.com/847832669/openwrt-monitor/releases" target="_blank"
                  class="shrink-0 text-[11px] text-brand-300 hover:underline">
                  Releases
                </a>
              </div>
              <div class="mt-2 max-h-72 overflow-auto space-y-3 pr-1">
                <div v-for="section in changelog.sections" :key="section.title">
                  <div class="mb-1 font-semibold text-slate-300">{{ section.title }}</div>
                  <ul class="space-y-1 text-slate-400">
                    <li v-for="item in section.items" :key="item" class="leading-5">
                      {{ item }}
                    </li>
                  </ul>
                </div>
              </div>
              <div class="mt-2 border-t border-slate-800 pt-2 text-[11px] text-slate-500">
                点击版本号检查远端最新版本
              </div>
            </div>
          </div>
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
    <div class="app-main flex-1 flex flex-col min-h-0">
      <!-- 顶部导航条（手机端） -->
      <header class="mobile-header lg:hidden flex items-center justify-between px-4 py-2.5 app-panel border-x-0 border-t-0 shrink-0">
        <button @click="sidebarOpen = true" class="text-xl text-slate-300 hover:text-white">
          ☰
        </button>
        <div class="flex items-center gap-1 text-sm font-bold text-white">
          <span>📶</span> OpenWrt
        </div>
        <button @click="showAlerts = !showAlerts" class="relative text-xl">
          🔔
          <span v-if="displayAlerts.length > 0"
            class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5 font-bold">
            {{ displayAlerts.length > 99 ? '99+' : displayAlerts.length }}
          </span>
        </button>
      </header>

      <!-- 页面内容 -->
      <main class="app-content flex-1 overflow-auto">
        <router-view />

        <!-- 告警面板 -->
        <div v-if="showAlerts"
          class="fixed top-4 right-3 left-3 sm:left-auto sm:right-4 sm:w-96 app-panel rounded-lg z-50 max-h-[70vh] flex flex-col">
          <div class="flex items-center justify-between px-4 py-3 border-b border-slate-800">
            <h3 class="text-sm font-semibold text-white">🔔 告警</h3>
            <div class="flex gap-2">
              <button @click="clearAlerts" class="text-xs text-slate-500 hover:text-slate-300">清除</button>
              <button @click="showAlerts = false" class="text-slate-500 hover:text-white">✕</button>
            </div>
          </div>
          <div class="flex-1 overflow-auto p-2 space-y-1">
            <div v-if="displayAlerts.length === 0" class="text-center py-8 text-slate-500 text-sm">✅ 暂无告警</div>
            <div v-for="a in displayAlerts" :key="a.id"
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
      <nav class="mobile-bottom-nav lg:hidden flex items-center justify-around app-panel border-x-0 border-b-0 px-1 py-1 shrink-0">
        <router-link v-for="item in mobileNav" :key="item.path"
          :to="item.path"
          class="flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] transition-colors min-w-0"
          :class="$route.path === item.path ? 'text-brand-300' : 'text-slate-500'">
          <span class="text-lg">{{ item.icon }}</span>
          <span class="truncate max-w-[3.25rem]">{{ item.label }}</span>
        </router-link>
        <button @click="sidebarOpen = true"
          class="flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] text-slate-500 transition-colors min-w-0">
          <span class="text-lg">☰</span>
          <span class="truncate max-w-[3.25rem]">更多</span>
        </button>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWebSocket } from './composables/useWebSocket'
import { requestJson } from './composables/useApi'

const route = useRoute()
const router = useRouter()
const isLoginRoute = computed(() => route.name === 'login')
const { connected: wsConnected, alerts: wsAlerts, clearAlerts: clearWsAlerts } = useWebSocket(computed(() => !isLoginRoute.value))
const sidebarOpen = ref(false)
const showAlerts = ref(false)
const alertList = ref([])
const securityInfo = ref(null)
const appVersion = ref('0.4.2')
const latestVersion = ref(null)
const updateAvailable = ref(false)
const checkingVer = ref(false)
const checkToast = ref('')
const showChangelog = ref(false)
const RAW_PACKAGE_URL = 'https://raw.githubusercontent.com/847832669/openwrt-monitor/main/frontend/package.json'
const TAGS_API_URL = 'https://api.github.com/repos/847832669/openwrt-monitor/tags?per_page=5'
const changelog = {
  version: '0.4.2',
  sections: [
    {
      title: '✨ 新功能',
      items: [
        '初始化向导、设备详情页和设备识别增强',
        '品牌/设备图标、自定义图标和重要设备标记',
        '网络分析页新增终端流量排行',
        '管理员登录、SSH 密码加密、备份恢复和历史数据维护',
      ],
    },
    {
      title: '🐛 修复',
      items: [
        '初始化向导入口逻辑调整',
        '仪表盘模块对齐问题修复',
        '设备密码留空编辑不再覆盖原密码',
        '版本检查避开 GitHub API 限流',
      ],
    },
    {
      title: '🎨 优化',
      items: [
        '响应式布局适配桌面、4K、Pad 和手机',
        '路由、ECharts 和图标资源拆分加载',
        '设备图标增加底色并压缩 SVG 资源',
      ],
    },
  ],
}
const displayAlerts = computed(() => {
  const seen = new Set()
  return [...wsAlerts.value, ...alertList.value]
    .filter((item) => {
      const id = item.id || `${item.title}-${item.message}-${item.time}`
      if (seen.has(id)) return false
      seen.add(id)
      return true
    })
    .slice(0, 100)
})
const securityWarning = computed(() => {
  const info = securityInfo.value
  return Boolean(info && !info.auth_disabled && (info.default_secret || info.default_admin_password))
})

function normalizeVersion(value) {
  return String(value || '').trim().replace(/^v/i, '')
}

function compareVersions(current, latest) {
  const cur = normalizeVersion(current).split('.').map(Number)
  const lat = normalizeVersion(latest).split('.').map(Number)
  for (let i = 0; i < Math.max(cur.length, lat.length); i++) {
    if ((lat[i] || 0) > (cur[i] || 0)) return 1
    if ((lat[i] || 0) < (cur[i] || 0)) return -1
  }
  return 0
}

async function loadLocalVersion() {
  const res = await fetch('/api/version', { cache: 'no-store' })
  if (!res.ok) throw new Error(`本地版本读取失败: ${res.status}`)
  const data = await res.json()
  appVersion.value = normalizeVersion(data.version)
  return appVersion.value
}

async function loadLatestVersion() {
  try {
    const rawRes = await fetch(`${RAW_PACKAGE_URL}?t=${Date.now()}`, { cache: 'no-store' })
    if (rawRes.ok) {
      const pkg = await rawRes.json()
      const version = normalizeVersion(pkg.version)
      if (version) return version
    }
  } catch (e) {
    // raw 源不可达时再用 GitHub API 兜底。
  }

  const tagsRes = await fetch(TAGS_API_URL, { cache: 'no-store' })
  if (!tagsRes.ok) throw new Error(`远端版本读取失败: ${tagsRes.status}`)
  const tags = await tagsRes.json()
  const tag = tags.map(t => t.name).find(t => /^v\d+\.\d+\.\d+$/.test(t))
  if (!tag) throw new Error('未找到版本标签')
  return normalizeVersion(tag)
}

async function refreshVersionState() {
  const [current, latest] = await Promise.all([
    loadLocalVersion(),
    loadLatestVersion(),
  ])
  latestVersion.value = latest
  updateAvailable.value = compareVersions(current, latest) > 0
}

async function checkUpdate() {
  checkingVer.value = true
  try {
    await refreshVersionState()
    checkToast.value = updateAvailable.value
      ? '🆕 v' + latestVersion.value + ' 可用'
      : '✅ 已是最新版本'
  } catch (e) {
    checkToast.value = '⚠️ 无法连接版本源'
  } finally {
    checkingVer.value = false
    setTimeout(() => checkToast.value = '', 3000)
  }
}

async function prefetchLatestVersion() {
  try {
    await refreshVersionState()
  } catch (e) {
    try {
      await loadLocalVersion()
    } catch (err) {
      // 忽略启动时版本读取失败，点击检查更新时再提示。
    }
  }
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
  { path: '/settings', icon: '🛡️', label: '系统设置' },
]

const mobileNav = navItems.slice(0, 4)

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
  clearWsAlerts()
  fetch('/api/alerts', { method: 'DELETE' }).catch(() => {})
}

async function logout() {
  try {
    await requestJson('/auth/logout', { method: 'POST' })
  } catch (e) {
    // 即便服务端已过期，也回到登录页。
  }
  router.push({ name: 'login' })
}

onMounted(() => {
  if (theme.value) document.documentElement.setAttribute('data-theme', theme.value)
  if (isLoginRoute.value) return
  fetch('/api/alerts').then(r => r.json()).then(d => { alertList.value = d.alerts || [] }).catch(() => {})
  requestJson('/settings/security').then(d => { securityInfo.value = d }).catch(() => {})
  prefetchLatestVersion()
})
</script>
