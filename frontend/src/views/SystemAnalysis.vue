<template>
  <div class="page-container page-container-wide space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">系统分析</h2>
        <p class="text-sm text-slate-400 mt-0.5">CPU 每核趋势 · 内存分布 · 进程排行 · 历史回看</p>
      </div>
      <div class="grid grid-cols-2 gap-2 sm:flex sm:items-center sm:justify-end">
        <!-- 时间范围 -->
        <select v-model="timeRange" @change="loadHistory"
          class="app-control px-2 text-sm text-slate-200">
          <option value="0">实时</option>
          <option value="1">近 1 小时</option>
          <option value="6">近 6 小时</option>
          <option value="24">近 24 小时</option>
          <option value="168">近 7 天</option>
        </select>
        <select v-model="selectedDevice"
          class="app-control px-3 text-sm text-slate-200">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ deviceOptionLabel(d) }}</option>
        </select>
      </div>
    </div>

    <div v-if="!selectedDevice" class="text-center py-12 text-slate-500">请先选择设备</div>

    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- CPU 曲线 -->
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">⚡ CPU 使用率</h3>
          <div ref="cpuChartRef" class="w-full h-56 sm:h-64 2xl:h-80"></div>
        </div>

        <!-- 内存曲线 -->
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🧠 内存使用率</h3>
          <div ref="memChartRef" class="w-full h-56 sm:h-64 2xl:h-80"></div>
        </div>
      </div>

      <!-- 负载 + conntrack -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">📈 系统负载</h3>
          <div ref="loadChartRef" class="w-full h-48 sm:h-56 2xl:h-72"></div>
        </div>
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🔗 连接跟踪</h3>
          <div ref="ctChartRef" class="w-full h-48 sm:h-56 2xl:h-72"></div>
        </div>
      </div>

      <!-- 进程排行 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🔥 CPU TOP 10</h3>
          <div class="space-y-1" v-if="topCpu.length">
            <div v-for="(p, i) in topCpu" :key="p.pid"
              class="flex items-center gap-2 text-xs py-1 hover:bg-slate-800/40 rounded px-1">
              <span class="text-slate-500 w-5">{{ i+1 }}</span>
              <span class="text-white font-mono flex-1 truncate">{{ p.name }}</span>
              <span class="numeric-value text-cyan-400 w-12 text-right">{{ p.cpu }}%</span>
            </div>
          </div>
        </div>
        <div class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">💾 内存 TOP 10</h3>
          <div class="space-y-1" v-if="topMem.length">
            <div v-for="(p, i) in topMem" :key="p.pid"
              class="flex items-center gap-2 text-xs py-1 hover:bg-slate-800/40 rounded px-1">
              <span class="text-slate-500 w-5">{{ i+1 }}</span>
              <span class="text-white font-mono flex-1 truncate">{{ p.name }}</span>
              <span class="numeric-value text-amber-400 w-12 text-right">{{ p.mem }}%</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'
import { getDeviceDisplayName, getDeviceIcon } from '../utils/deviceDisplay'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()

const devices = ref([])
const selectedDevice = ref('')
const timeRange = ref('0')

const cpuChartRef = ref(null)
const memChartRef = ref(null)
const loadChartRef = ref(null)
const ctChartRef = ref(null)

let cpuChart = null, memChart = null, loadChart = null, ctChart = null
let echartsModule = null
let echartsPromise = null
const historyData = ref({ points: [] })

function deviceOptionLabel(device) {
  return `${getDeviceIcon(device)} ${getDeviceDisplayName(device)}`
}

// 实时数据
const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || null
})
const sysData = computed(() => currentMetrics.value?.system)
const netData = computed(() => currentMetrics.value?.network)
const topCpu = computed(() => (sysData.value?.top_cpu ?? []).slice(0, 10))
const topMem = computed(() => (sysData.value?.top_mem ?? []).slice(0, 10))
const coreCount = computed(() => sysData.value?.cpu_per_core?.length ?? 1)

const coreColors = ['#22d3ee', '#fbbf24', '#a78bfa', '#34d399', '#f472b6', '#fb923c', '#38bdf8', '#f97316']

async function loadEcharts() {
  if (echartsModule) return echartsModule
  if (!echartsPromise) echartsPromise = import('../utils/echarts')
  const mod = await echartsPromise
  echartsModule = mod.getEcharts()
  return echartsModule
}

function fmtTime(ts) {
  const d = new Date(ts)
  return d.getHours().toString().padStart(2,'0') + ':' +
         d.getMinutes().toString().padStart(2,'0') + ':' +
         d.getSeconds().toString().padStart(2,'0')
}

function fmtShortTime(ts) {
  const d = new Date(ts)
  return d.getHours().toString().padStart(2,'0') + ':' +
         d.getMinutes().toString().padStart(2,'0')
}

async function loadHistory() {
  if (!selectedDevice.value || timeRange.value === '0') return
  try {
    const res = await fetch(`/api/metrics/history/${selectedDevice.value}?hours=${timeRange.value}`)
    historyData.value = await res.json()
    renderAllCharts()
  } catch (e) {
    console.error('加载历史数据失败', e)
  }
}

function renderAllCharts() {
  nextTick(() => {
    renderCPUChart()
    renderMemChart()
    renderLoadChart()
    renderCTChart()
  })
}

async function renderCPUChart() {
  if (!cpuChartRef.value) return
  const echarts = await loadEcharts()
  if (!cpuChartRef.value) return
  if (!cpuChart) cpuChart = echarts.init(cpuChartRef.value, 'dark')

  let times, data
  if (timeRange.value !== '0' && historyData.value.points?.length) {
    const pts = historyData.value.points
    times = pts.map(p => fmtShortTime(p.t))
    data = pts.map(p => p.cpu)
  } else {
    // 实时模式用最近积累的数据
    times = cpuHistory.value.map(d => d.time)
    data = cpuHistory.value.map(d => d.avg)
  }

  cpuChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 },
      formatter: (p) => `${p[0].axisValue}<br/>⚡ CPU: ${p[0].value}%` },
    grid: { left: 40, right: 8, top: 8, bottom: 28 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value}%' } },
    series: [{
      type: 'line', data, smooth: true, symbol: 'none',
      lineStyle: { color: '#22d3ee', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
        { offset: 0, color: 'rgba(34,211,238,0.3)' }, { offset: 1, color: 'rgba(34,211,238,0)' }]) },
    }],
  })
}

async function renderMemChart() {
  if (!memChartRef.value) return
  const echarts = await loadEcharts()
  if (!memChartRef.value) return
  if (!memChart) memChart = echarts.init(memChartRef.value, 'dark')

  let times, data
  if (timeRange.value !== '0' && historyData.value.points?.length) {
    const pts = historyData.value.points
    times = pts.map(p => fmtShortTime(p.t))
    data = pts.map(p => p.mem)
  } else {
    times = memHistory.value.map(d => d.time)
    data = memHistory.value.map(d => d.pct)
  }

  memChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 },
      formatter: (p) => `${p[0].axisValue}<br/>🧠 内存: ${p[0].value}%` },
    grid: { left: 40, right: 8, top: 8, bottom: 28 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value}%' } },
    series: [{
      type: 'line', data, smooth: true, symbol: 'none',
      lineStyle: { color: '#34d399', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
        { offset: 0, color: 'rgba(52,211,153,0.3)' }, { offset: 1, color: 'rgba(52,211,153,0)' }]) },
    }],
  })
}

async function renderLoadChart() {
  if (!loadChartRef.value) return
  const echarts = await loadEcharts()
  if (!loadChartRef.value) return
  if (!loadChart) loadChart = echarts.init(loadChartRef.value, 'dark')

  let times, d1, d5, d15
  if (timeRange.value !== '0' && historyData.value.points?.length) {
    const pts = historyData.value.points
    times = pts.map(p => fmtShortTime(p.t))
    d1 = pts.map(p => p.load1)
    d5 = pts.map(p => p.load5)
    d15 = pts.map(p => p.load15)
  } else {
    times = histLoad.value.map(d => d.time)
    d1 = histLoad.value.map(d => d.l1)
    d5 = histLoad.value.map(d => d.l5)
    d15 = histLoad.value.map(d => d.l15)
  }

  loadChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 } },
    legend: { data: ['1m','5m','15m'], textStyle: { color: '#94a3b8', fontSize: 10 }, bottom: 0 },
    grid: { left: 40, right: 8, top: 8, bottom: 32 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9 } },
    series: [
      { name: '1m', type: 'line', data: d1, smooth: true, symbol: 'none', lineStyle: { color: '#fbbf24', width: 1 } },
      { name: '5m', type: 'line', data: d5, smooth: true, symbol: 'none', lineStyle: { color: '#a78bfa', width: 1 } },
      { name: '15m', type: 'line', data: d15, smooth: true, symbol: 'none', lineStyle: { color: '#64748b', width: 1 } },
    ],
  })
}

async function renderCTChart() {
  if (!ctChartRef.value) return
  const echarts = await loadEcharts()
  if (!ctChartRef.value) return
  if (!ctChart) ctChart = echarts.init(ctChartRef.value, 'dark')

  let times, data
  if (timeRange.value !== '0' && historyData.value.points?.length) {
    const pts = historyData.value.points
    times = pts.map(p => fmtShortTime(p.t))
    data = pts.map(p => p.ct)
  } else {
    times = ctHistory.value.map(d => d.time)
    data = ctHistory.value.map(d => d.ct)
  }

  ctChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 },
      formatter: (p) => `${p[0].axisValue}<br/>🔗 连接: ${p[0].value}` },
    grid: { left: 40, right: 8, top: 8, bottom: 28 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9 } },
    series: [{
      type: 'line', data, smooth: true, symbol: 'none',
      lineStyle: { color: '#f472b6', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
        { offset: 0, color: 'rgba(244,114,182,0.3)' }, { offset: 1, color: 'rgba(244,114,182,0)' }]) },
    }],
  })
}

// 实时数据积累
const cpuHistory = ref([])
const memHistory = ref([])
const histLoad = ref([])
const ctHistory = ref([])

watch([sysData, netData], () => {
  if (!sysData.value || timeRange.value !== '0') return
  const now = new Date()
  const time = now.getHours().toString().padStart(2,'0') + ':' +
               now.getMinutes().toString().padStart(2,'0') + ':' +
               now.getSeconds().toString().padStart(2,'0')

  const cores = sysData.value.cpu_per_core || []
  const avg = cores.length ? (cores.reduce((a,b)=>a+b, 0) / cores.length) : (sysData.value.cpu_percent || 0)

  cpuHistory.value.push({ time, avg })
  if (cpuHistory.value.length > 120) cpuHistory.value = cpuHistory.value.slice(-120)

  memHistory.value.push({ time, pct: sysData.value.memory_percent || 0 })
  if (memHistory.value.length > 120) memHistory.value = memHistory.value.slice(-120)

  histLoad.value.push({
    time, l1: sysData.value.load_1m || 0, l5: sysData.value.load_5m || 0, l15: sysData.value.load_15m || 0,
  })
  if (histLoad.value.length > 120) histLoad.value = histLoad.value.slice(-120)

  ctHistory.value.push({ time, ct: netData.value?.conntrack_count ?? 0 })
  if (ctHistory.value.length > 120) ctHistory.value = ctHistory.value.slice(-120)

  if (timeRange.value === '0') renderAllCharts()
})

watch(selectedDevice, () => {
  if (timeRange.value !== '0') loadHistory()
})

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0) selectedDevice.value = devices.value[0].id
  } catch (e) { /* ignore */ }
})

onUnmounted(() => {
  cpuChart?.dispose(); memChart?.dispose()
  loadChart?.dispose(); ctChart?.dispose()
})
</script>
