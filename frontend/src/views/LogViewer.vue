<template>
  <div class="p-6 space-y-4 max-w-7xl mx-auto h-full flex flex-col">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-xl font-bold text-white">系统日志</h2>
        <p class="text-sm text-slate-400 mt-0.5">实时查看 OpenWrt 运行日志</p>
      </div>
      <div class="flex items-center gap-3">
        <select v-model="logLevel" @change="applyFilter"
          class="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="">所有级别</option>
          <option value="error">🔴 错误</option>
          <option value="warn">🟡 警告</option>
          <option value="info">🔵 信息</option>
          <option value="debug">⚪ 调试</option>
        </select>
        <input v-model="filterText" @input="applyFilter" placeholder="关键词搜索…"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 w-40 focus:outline-none focus:border-brand-500 placeholder-slate-500" />
        <select v-model="logLines" @change="loadLogs"
          class="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
          <option :value="50">50 条</option>
          <option :value="100">100 条</option>
          <option :value="200">200 条</option>
          <option :value="500">500 条</option>
        </select>
        <select v-model="selectedDevice"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name || d.host }}</option>
        </select>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="flex items-center justify-between shrink-0" v-if="selectedDevice">
      <div class="flex items-center gap-2 text-xs text-slate-500">
        <span>共 <span class="text-white font-bold">{{ filteredLogs.length }}</span> 条</span>
        <span v-if="loading" class="text-brand-300 animate-pulse">加载中…</span>
      </div>
      <div class="flex items-center gap-2">
        <button @click="toggleAutoRefresh"
          class="text-xs px-2.5 py-1 rounded-lg border transition-colors"
          :class="autoRefresh
            ? 'border-green-600 bg-green-600/20 text-green-400'
            : 'border-slate-700 bg-slate-800 text-slate-400'">
          {{ autoRefresh ? '🟢 实时' : '⏸ 暂停' }}
        </button>
        <button @click="scrollToBottom"
          class="text-xs px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
          ⬇ 底部
        </button>
        <button @click="copyLogs"
          class="text-xs px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
          📋 复制
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!selectedDevice" class="flex-1 flex items-center justify-center text-slate-500 text-sm">
      请先选择设备
    </div>

    <!-- 日志内容 -->
    <div v-else ref="logContainer"
      class="flex-1 bg-black/40 border border-slate-800 rounded-xl overflow-auto font-mono text-xs leading-relaxed">
      <div v-if="filteredLogs.length === 0" class="p-6 text-center text-slate-600">
        {{ loading ? '加载中…' : '暂无日志' }}
      </div>
      <div v-else class="p-3 space-y-0.5">
        <div v-for="(entry, i) in filteredLogs" :key="i"
          class="flex gap-2 py-0.5 px-1 rounded hover:bg-slate-800/30"
          :class="levelBg(entry.level)">
          <span class="text-slate-600 w-6 text-right shrink-0 select-none">{{ i + 1 }}</span>
          <span class="shrink-0" v-html="levelIcon(entry.level)"></span>
          <span class="text-slate-600 w-20 shrink-0">{{ entry.time }}</span>
          <span class="flex-1 break-all" :class="levelText(entry.level)">{{ entry.raw }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useApi } from '../composables/useApi'

const { get } = useApi()
const devices = ref([])
const selectedDevice = ref('')
const logContainer = ref(null)
const entries = ref([])
const filterText = ref('')
const logLevel = ref('')
const logLines = ref(100)
const loading = ref(false)
const autoRefresh = ref(true)
let refreshTimer = null

const filteredLogs = computed(() => {
  let list = entries.value
  if (logLevel.value) {
    list = list.filter(e => e.level === logLevel.value)
  }
  if (filterText.value) {
    const q = filterText.value.toLowerCase()
    list = list.filter(e => e.raw.toLowerCase().includes(q))
  }
  return list
})

function levelIcon(level) {
  const icons = { error: '🔴', warn: '🟡', info: '🔵', debug: '⚪' }
  return icons[level] || '⚪'
}

function levelBg(level) {
  return level === 'error' ? 'bg-red-900/10' : level === 'warn' ? 'bg-amber-900/10' : ''
}

function levelText(level) {
  return level === 'error' ? 'text-red-300' : level === 'warn' ? 'text-amber-300' : level === 'debug' ? 'text-slate-500' : 'text-slate-300'
}

async function loadLogs() {
  if (!selectedDevice.value) return
  loading.value = true
  try {
    const url = `/api/logs/${selectedDevice.value}?lines=${logLines.value}${filterText.value ? '&filter=' + encodeURIComponent(filterText.value) : ''}`
    const res = await fetch(url)
    const data = await res.json()
    entries.value = data.entries || []
    await nextTick()
    if (autoRefresh.value) scrollToBottom()
  } catch (e) {
    console.error('加载日志失败', e)
  }
  loading.value = false
}

function applyFilter() {
  loadLogs()
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) loadLogs()
}

function copyLogs() {
  const text = filteredLogs.value.map(e => e.raw).join('\n')
  navigator.clipboard.writeText(text).catch(() => {})
}

watch(selectedDevice, () => {
  if (autoRefresh.value) loadLogs()
})

onMounted(async () => {
  try {
    const res = await fetch('/api/devices')
    const data = await res.json()
    devices.value = data
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].id
    }
  } catch (e) { /* ignore */ }

  // 自动刷新
  refreshTimer = setInterval(() => {
    if (autoRefresh.value && selectedDevice.value) {
      loadLogs()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
