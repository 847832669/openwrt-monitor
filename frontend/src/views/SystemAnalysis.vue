<template>
  <div class="p-6 space-y-6 max-w-7xl mx-auto">
    <!-- 标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">系统分析</h2>
        <p class="text-sm text-slate-400 mt-0.5">CPU 每核追踪 · 内存分布 · 进程排行</p>
      </div>
      <select v-model="selectedDevice"
        class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
        <option value="">选择设备…</option>
        <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name || d.host }}</option>
      </select>
    </div>

    <div v-if="!selectedDevice" class="text-center py-12 text-slate-500">请先选择设备</div>

    <template v-else-if="sysData">
      <!-- 第一行：CPU + 内存实时卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- CPU 每核曲线 -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">⚡ CPU 每核使用率</h3>
          <div ref="cpuChartRef" class="w-full h-56"></div>
          <div class="flex gap-2 mt-2 text-xs text-slate-500 flex-wrap">
            <span v-for="(_, i) in coreColors" :key="i"
              class="flex items-center gap-1">
              <span class="w-2.5 h-2.5 rounded-full" :style="{ background: coreColors[i] }"></span>
              核心{{ i+1 }}
            </span>
          </div>
        </div>

        <!-- 内存分布面积图 -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🧠 内存分布</h3>
          <div ref="memChartRef" class="w-full h-56"></div>
          <div class="flex gap-3 mt-2 text-xs text-slate-500">
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span> 已用</span>
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> 缓存</span>
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-slate-600"></span> 可用</span>
          </div>
        </div>
      </div>

      <!-- 进程排行 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- CPU TOP -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🔥 CPU TOP 10</h3>
          <div class="space-y-1" v-if="topCpu.length">
            <div v-for="(p, i) in topCpu" :key="p.pid"
              class="flex items-center gap-2 text-xs py-1 hover:bg-slate-800/40 rounded px-1">
              <span class="text-slate-500 w-5">{{ i+1 }}</span>
              <span class="text-white font-mono flex-1 truncate">{{ p.name }}</span>
              <span class="text-cyan-400 font-mono w-12 text-right">{{ p.cpu }}%</span>
              <span class="text-slate-500 w-16 text-right">PID {{ p.pid }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500 py-4 text-center">等待数据…</div>
        </div>

        <!-- 内存 TOP -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">💾 内存 TOP 10</h3>
          <div class="space-y-1" v-if="topMem.length">
            <div v-for="(p, i) in topMem" :key="p.pid"
              class="flex items-center gap-2 text-xs py-1 hover:bg-slate-800/40 rounded px-1">
              <span class="text-slate-500 w-5">{{ i+1 }}</span>
              <span class="text-white font-mono flex-1 truncate">{{ p.name }}</span>
              <span class="text-amber-400 font-mono w-12 text-right">{{ p.mem }}%</span>
              <span class="text-slate-500 w-16 text-right">PID {{ p.pid }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500 py-4 text-center">等待数据…</div>
        </div>
      </div>
    </template>

    <div v-else class="text-center py-12 text-slate-500">等待数据采集…</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()

const devices = ref([])
const selectedDevice = ref('')
const cpuChartRef = ref(null)
const memChartRef = ref(null)
let cpuChart = null
let memChart = null

// 历史数据积累（最近 120 个点）
const cpuHistory = ref([])
const memHistory = ref([])

const coreColors = ['#22d3ee', '#fbbf24', '#a78bfa', '#34d399', '#f472b6', '#fb923c', '#38bdf8', '#f97316']

const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || null
})

const sysData = computed(() => currentMetrics.value?.system)

const cores = computed(() => sysData.value?.cpu_per_core ?? [])
const topCpu = computed(() => (sysData.value?.top_cpu ?? []).slice(0, 10))
const topMem = computed(() => (sysData.value?.top_mem ?? []).slice(0, 10))

// 每来一次新数据，积累一个点
watch(sysData, () => {
  if (!sysData.value) return
  const now = new Date()
  const time = now.getHours().toString().padStart(2,'0') + ':' +
               now.getMinutes().toString().padStart(2,'0') + ':' +
               now.getSeconds().toString().padStart(2,'0')

  // CPU 每核
  cpuHistory.value.push({ time, cores: [...cores.value] })
  if (cpuHistory.value.length > 120) cpuHistory.value = cpuHistory.value.slice(-120)

  // 内存
  const sys = sysData.value
  memHistory.value.push({
    time,
    used: sys.memory_used_mb || 0,
    available: sys.memory_available_mb || 0,
    total: sys.memory_total_mb || 1,
    cache: Math.max(0, (sys.memory_total_mb || 0) - (sys.memory_used_mb || 0) - (sys.memory_available_mb || 0)),
  })
  if (memHistory.value.length > 120) memHistory.value = memHistory.value.slice(-120)

  updateCharts()
})

function updateCharts() {
  if (!cpuChartRef.value || !memChartRef.value) return
  nextTick(() => {
    renderCPUChart()
    renderMemChart()
  })
}

function renderCPUChart() {
  if (!cpuChart) {
    cpuChart = echarts.init(cpuChartRef.value, 'dark')
  }
  const times = cpuHistory.value.map(d => d.time)
  const coreCount = cores.value.length || 1
  const series = []
  for (let i = 0; i < coreCount; i++) {
    series.push({
      name: `核心 ${i+1}`,
      type: 'line',
      data: cpuHistory.value.map(d => d.cores[i] ?? 0),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: coreColors[i], width: 1.5 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: coreColors[i] + '44' },
          { offset: 1, color: coreColors[i] + '00' },
        ]),
      },
    })
  }
  cpuChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 } },
    legend: { show: false },
    grid: { left: 40, right: 8, top: 8, bottom: 28 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value}%' } },
    series,
  }, { notMerge: false })
}

function renderMemChart() {
  if (!memChart) {
    memChart = echarts.init(memChartRef.value, 'dark')
  }
  const times = memHistory.value.map(d => d.time)
  const used = memHistory.value.map(d => d.used)
  const cache = memHistory.value.map(d => d.cache)
  const avail = memHistory.value.map(d => d.available)

  memChart.setOption({
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 11 },
      formatter: (params) => {
        const t = params[0].axisValue
        const u = params[0].value
        const c = params[1].value
        const a = params[2].value
        return `<div>${t}</div>
                <div>🔵 已用: ${u.toFixed(0)} MB</div>
                <div>🟢 缓存: ${c.toFixed(0)} MB</div>
                <div>⬜ 可用: ${a.toFixed(0)} MB</div>`
      },
    },
    grid: { left: 48, right: 8, top: 8, bottom: 28 },
    xAxis: { type: 'category', data: times, axisLabel: { color: '#64748b', fontSize: 9 }, axisLine: { show: false } },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: '{value} MB' },
    },
    series: [
      {
        name: '已用',
        type: 'line',
        data: used,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#22d3ee', width: 1.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
          { offset: 0, color: 'rgba(34,211,238,0.4)' }, { offset: 1, color: 'rgba(34,211,238,0)' },
        ])},
      },
      {
        name: '缓存',
        type: 'line',
        data: cache,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#34d399', width: 1.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
          { offset: 0, color: 'rgba(52,211,153,0.3)' }, { offset: 1, color: 'rgba(52,211,153,0)' },
        ])},
      },
      {
        name: '可用',
        type: 'line',
        data: avail,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#475569', width: 1, type: 'dashed' },
      },
    ],
  }, { notMerge: false })
}

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0) selectedDevice.value = devices.value[0].id
  } catch (e) { /* ignore */ }
})

onUnmounted(() => {
  cpuChart?.dispose()
  memChart?.dispose()
})
</script>
