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
          <div class="flex items-center gap-1.5">
            <button @click="checkUpdate"
              class="text-slate-600 hover:text-brand-300 transition-colors"
              title="点击检查更新">
              v{{ appVersion }}{{ checkingVer ? ' 🔍' : '' }}
            </button>
            <button @click="openChangelog"
              class="grid h-5 w-5 place-items-center rounded-md border border-slate-800 text-slate-500 transition-colors hover:border-brand-600/50 hover:bg-brand-600/10 hover:text-brand-300"
              title="查看更新日志"
              aria-label="查看更新日志">
              <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 fill-none stroke-current stroke-[1.8]">
                <path d="M5 4.5h10M5 8h10M5 11.5h6" stroke-linecap="round" />
                <path d="M4 2.75h12A1.25 1.25 0 0 1 17.25 4v12A1.25 1.25 0 0 1 16 17.25H4A1.25 1.25 0 0 1 2.75 16V4A1.25 1.25 0 0 1 4 2.75Z" />
              </svg>
            </button>
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

      <!-- 更新日志弹窗 -->
      <div v-if="changelogOpen"
        class="fixed inset-0 z-[80] flex items-end justify-center bg-black/60 p-3 backdrop-blur-sm sm:items-center"
        @click.self="closeChangelog">
        <section class="app-panel flex max-h-[86vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg shadow-2xl">
          <header class="flex items-start justify-between gap-3 border-b border-slate-800 px-4 py-3">
            <div class="min-w-0">
              <div class="text-[11px] uppercase tracking-[0.16em] text-brand-300">GitHub Sync</div>
              <h3 class="mt-1 truncate text-lg font-bold text-white">
                更新日志
                <span v-if="remoteChangelog.versions.length" class="text-sm font-medium text-slate-400">
                  {{ remoteChangelog.versions.length }} 个版本
                </span>
              </h3>
            </div>
            <div class="flex shrink-0 items-center gap-1.5">
              <button @click="loadRemoteChangelog(true)"
                class="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-400 transition-colors hover:border-brand-600/50 hover:bg-brand-600/10 hover:text-brand-300 disabled:cursor-wait disabled:opacity-60"
                :disabled="changelogLoading"
                title="刷新">
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-none stroke-current stroke-2">
                  <path d="M16 8a6 6 0 1 0-1.76 4.24" stroke-linecap="round" />
                  <path d="M16 4v4h-4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
              <a :href="remoteChangelog.url || GITHUB_RELEASES_URL" target="_blank"
                class="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-400 transition-colors hover:border-brand-600/50 hover:bg-brand-600/10 hover:text-brand-300"
                title="打开 GitHub">
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-none stroke-current stroke-2">
                  <path d="M7.5 5H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-2.5" stroke-linecap="round" />
                  <path d="M11 3h6v6M9 11l8-8" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </a>
              <button @click="closeChangelog"
                class="grid h-8 w-8 place-items-center rounded-md border border-slate-800 text-slate-400 transition-colors hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-200"
                title="关闭">
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-none stroke-current stroke-2">
                  <path d="M5 5l10 10M15 5 5 15" stroke-linecap="round" />
                </svg>
              </button>
            </div>
          </header>

          <div class="flex-1 overflow-auto px-4 py-4">
            <div v-if="changelogLoading" class="space-y-3">
              <div class="h-4 w-40 animate-pulse rounded bg-slate-800"></div>
              <div class="h-20 animate-pulse rounded-lg bg-slate-900/80"></div>
              <div class="h-24 animate-pulse rounded-lg bg-slate-900/80"></div>
            </div>

            <div v-else-if="changelogError"
              class="rounded-lg border border-amber-500/30 bg-amber-900/15 p-4 text-sm text-amber-100">
              <div class="font-semibold">无法同步更新日志</div>
              <div class="mt-1 text-amber-200/80">{{ changelogError }}</div>
              <button @click="loadRemoteChangelog(true)"
                class="mt-3 rounded-md border border-amber-400/40 px-3 py-1.5 text-xs text-amber-100 transition-colors hover:bg-amber-400/10">
                重试
              </button>
            </div>

            <div v-else class="space-y-5">
              <div class="flex flex-wrap items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-xs text-slate-400">
                <span>{{ remoteChangelog.sourceLabel }}</span>
                <span v-if="remoteChangelog.syncedAt">同步于 {{ remoteChangelog.syncedAt }}</span>
              </div>

              <div v-for="version in remoteChangelog.versions" :key="version.title"
                class="rounded-lg border border-slate-800 bg-slate-950/35 p-3">
                <div class="mb-3 flex items-center justify-between gap-3">
                  <h4 class="text-base font-bold text-white">{{ version.title }}</h4>
                  <span class="text-[11px] text-slate-500">{{ version.sections.length }} 类更新</span>
                </div>

                <div class="space-y-3">
                  <div v-for="section in version.sections" :key="version.title + section.title">
                    <div class="mb-1.5 text-sm font-semibold text-slate-200">{{ section.title }}</div>
                    <ul class="space-y-1.5 text-sm text-slate-400">
                      <li v-for="item in section.items" :key="version.title + section.title + item.text"
                        class="leading-6">
                        <span v-if="item.label" class="font-semibold text-slate-200">{{ item.label }}：</span>
                        <span>{{ item.text }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
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
const CHANGELOG_API_URL = 'https://api.github.com/repos/847832669/openwrt-monitor/contents/CHANGELOG.md?ref=main'
const RAW_PACKAGE_URL = 'https://raw.githubusercontent.com/847832669/openwrt-monitor/main/frontend/package.json'
const RAW_CHANGELOG_URL = 'https://raw.githubusercontent.com/847832669/openwrt-monitor/main/CHANGELOG.md'
const TAGS_API_URL = 'https://api.github.com/repos/847832669/openwrt-monitor/tags?per_page=5'
const RELEASE_API_URL = 'https://api.github.com/repos/847832669/openwrt-monitor/releases/latest'
const GITHUB_RELEASES_URL = 'https://github.com/847832669/openwrt-monitor/releases'
const GITHUB_CHANGELOG_URL = 'https://github.com/847832669/openwrt-monitor/blob/main/CHANGELOG.md'
const changelogOpen = ref(false)
const changelogLoading = ref(false)
const changelogError = ref('')
const remoteChangelog = ref({
  sourceLabel: '',
  syncedAt: '',
  url: GITHUB_CHANGELOG_URL,
  versions: [],
})
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

function cleanMarkdownText(value) {
  return String(value || '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^[-*]\s+/, '')
    .trim()
}

function parseListItem(line) {
  const text = cleanMarkdownText(line)
  const labelMatch = text.match(/^([^：:]{1,32})[：:]\s*(.+)$/)
  if (labelMatch) {
    return {
      label: labelMatch[1].trim(),
      text: labelMatch[2].trim(),
    }
  }
  return { label: '', text }
}

function parseChangelogBlock(lines, headingIndexes, startIndex) {
  const title = cleanMarkdownText(lines[startIndex].replace(/^##\s+/, ''))
  const nextIndex = headingIndexes.find(index => index > startIndex)
  const bodyLines = lines.slice(startIndex + 1, nextIndex > -1 ? nextIndex : lines.length)
  const sections = []
  let current = null

  bodyLines.forEach((rawLine) => {
    const line = rawLine.trim()
    if (!line || line === '暂无') return

    if (/^###\s+/.test(line)) {
      current = {
        title: cleanMarkdownText(line.replace(/^###\s+/, '')),
        items: [],
      }
      sections.push(current)
      return
    }

    if (/^[-*]\s+/.test(line)) {
      if (!current) {
        current = { title: '更新内容', items: [] }
        sections.push(current)
      }
      current.items.push(parseListItem(line))
    }
  })

  return {
    title,
    sections: sections.filter(section => section.items.length > 0),
  }
}

function parseChangelogMarkdown(markdown) {
  const lines = String(markdown || '').split(/\r?\n/)
  const headingIndexes = lines
    .map((line, index) => (/^##\s+/.test(line.trim()) ? index : -1))
    .filter(index => index > -1)
  const versionIndexes = headingIndexes.filter(index => /^##\s+v?\d+\.\d+\.\d+/.test(lines[index].trim()))

  if (versionIndexes.length === 0) throw new Error('GitHub CHANGELOG 中未找到正式版本段落')

  const versions = versionIndexes
    .map(index => parseChangelogBlock(lines, headingIndexes, index))
    .filter(version => version.sections.length > 0)

  if (versions.length === 0) throw new Error('GitHub CHANGELOG 中未找到可展示的更新内容')

  return { versions }
}

function parseReleaseMarkdown(release) {
  const body = String(release.body || '').trim()
  const title = release.name || release.tag_name || '最新版本'
  const lines = body.split(/\r?\n/)
  const sections = []
  let current = null

  lines.forEach((rawLine) => {
    const line = rawLine.trim()
    if (!line) return

    if (/^#{2,4}\s+/.test(line)) {
      current = {
        title: cleanMarkdownText(line.replace(/^#{2,4}\s+/, '')),
        items: [],
      }
      sections.push(current)
      return
    }

    if (/^[-*]\s+/.test(line)) {
      if (!current) {
        current = { title: '更新内容', items: [] }
        sections.push(current)
      }
      current.items.push(parseListItem(line))
    }
  })

  const usefulSections = sections.filter(section => section.items.length > 0)
  if (usefulSections.length > 0) {
    return {
      versions: [{ title, sections: usefulSections }],
    }
  }

  const parsed = parseChangelogMarkdown(`## ${title}\n${body}`)
  return {
    versions: parsed.versions.map(version => ({ ...version, title })),
  }
}

function decodeBase64Content(value) {
  const binary = atob(String(value || '').replace(/\s/g, ''))
  const bytes = Uint8Array.from(binary, char => char.charCodeAt(0))
  return new TextDecoder('utf-8').decode(bytes)
}

function formatSyncTime() {
  const now = new Date()
  return now.getHours().toString().padStart(2, '0') + ':' +
    now.getMinutes().toString().padStart(2, '0')
}

async function loadRemoteChangelog(force = false) {
  if (!force && remoteChangelog.value.versions.length > 0) return
  changelogLoading.value = true
  changelogError.value = ''

  try {
    const apiRes = await fetch(`${CHANGELOG_API_URL}&t=${Date.now()}`, { cache: 'no-store' })
    if (!apiRes.ok) throw new Error(`GitHub CHANGELOG API 读取失败: ${apiRes.status}`)
    const file = await apiRes.json()
    const parsed = parseChangelogMarkdown(decodeBase64Content(file.content))
    remoteChangelog.value = {
      ...parsed,
      sourceLabel: '来源：GitHub CHANGELOG.md',
      syncedAt: formatSyncTime(),
      url: GITHUB_CHANGELOG_URL,
    }
  } catch (apiError) {
    try {
      const rawRes = await fetch(`${RAW_CHANGELOG_URL}?t=${Date.now()}`, { cache: 'no-store' })
      if (!rawRes.ok) throw new Error(`GitHub raw CHANGELOG 读取失败: ${rawRes.status}`)
      const parsed = parseChangelogMarkdown(await rawRes.text())
      remoteChangelog.value = {
        ...parsed,
        sourceLabel: '来源：GitHub raw CHANGELOG.md',
        syncedAt: formatSyncTime(),
        url: GITHUB_CHANGELOG_URL,
      }
    } catch (rawError) {
      try {
        const releaseRes = await fetch(RELEASE_API_URL, { cache: 'no-store' })
        if (!releaseRes.ok) throw new Error(`GitHub Release 读取失败: ${releaseRes.status}`)
        const release = await releaseRes.json()
        const parsed = parseReleaseMarkdown(release)
        remoteChangelog.value = {
          ...parsed,
          sourceLabel: '来源：GitHub 最新 Release',
          syncedAt: formatSyncTime(),
          url: release.html_url || GITHUB_RELEASES_URL,
        }
      } catch (releaseError) {
        changelogError.value = apiError?.message || rawError?.message || releaseError?.message || '请稍后重试'
      }
    }
  } finally {
    changelogLoading.value = false
  }
}

async function openChangelog() {
  changelogOpen.value = true
  await loadRemoteChangelog(true)
}

function closeChangelog() {
  changelogOpen.value = false
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
