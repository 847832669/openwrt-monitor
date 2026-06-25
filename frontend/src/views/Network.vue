<template>
  <div class="page-container page-container-wide space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">网络分析</h2>
        <p class="text-sm text-slate-400 mt-0.5">接口详情 · 连接状态 · 协议分布</p>
      </div>
      <div class="grid grid-cols-1 gap-2 sm:flex sm:items-center sm:justify-end">
        <div class="flex gap-2 overflow-x-auto">
          <button v-for="item in trafficPeriods" :key="item.key" type="button"
            @click="setTrafficPeriod(item.key)"
            class="shrink-0 rounded-lg border px-3 py-2 text-xs transition-colors"
            :class="trafficPeriod === item.key
              ? 'border-brand-600 bg-brand-600/20 text-brand-200'
              : 'border-slate-700 bg-slate-800/40 text-slate-400 hover:text-slate-200 hover:border-slate-600'">
            {{ item.label }}
          </button>
        </div>
        <select v-model="selectedDevice"
          class="app-control w-full sm:w-64 px-3 text-sm text-slate-200">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ deviceOptionLabel(d) }}</option>
        </select>
      </div>
    </div>

    <TrafficRank v-if="selectedDevice" :rank="trafficRank" :limit="12" @select="selectTrafficDevice" />

    <section v-if="selectedDevice" class="grid grid-cols-1 xl:grid-cols-[1fr_24rem] gap-4">
      <div class="app-panel rounded-lg p-4">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-3">
          <div>
            <h3 class="text-sm font-semibold text-slate-300">设备历史流量趋势</h3>
            <p class="text-xs text-slate-500 mt-0.5">{{ trafficSummaryLabel }}</p>
          </div>
          <button @click="loadTrafficHistory"
            class="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">
            刷新
          </button>
        </div>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <div class="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
            <div class="text-xs text-slate-500">总流量</div>
            <div class="numeric-value mt-1 text-lg font-bold text-white">{{ fmtBytes(trafficSummary.total_bytes) }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
            <div class="text-xs text-slate-500">下载</div>
            <div class="numeric-value mt-1 text-lg font-bold text-cyan-300">{{ fmtBytes(trafficSummary.download_bytes) }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
            <div class="text-xs text-slate-500">上传</div>
            <div class="numeric-value mt-1 text-lg font-bold text-amber-300">{{ fmtBytes(trafficSummary.upload_bytes) }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
            <div class="text-xs text-slate-500">采样</div>
            <div class="numeric-value mt-1 text-lg font-bold text-white">{{ trafficHistory?.count || 0 }}</div>
          </div>
        </div>
        <div ref="trafficTrendRef" class="w-full h-56 sm:h-64 2xl:h-80"></div>
      </div>

      <aside class="space-y-4">
        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">异常流量提醒</h3>
          <div v-if="trafficAlerts.length" class="space-y-2">
            <div v-for="alert in trafficAlerts" :key="alert.ip + alert.mac"
              class="rounded-lg border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs">
              <div class="font-semibold text-amber-200">{{ alert.hostname || alert.ip || alert.mac }}</div>
              <div class="mt-1 text-amber-100/80">{{ alert.message }} · +{{ fmtBytes(alert.delta_bytes) }}</div>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500">当前没有明显异常峰值</div>
        </section>

        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">TOP 设备详情</h3>
          <div v-if="selectedTrafficItem" class="space-y-3">
            <div>
              <div class="text-base font-semibold text-white truncate">{{ selectedTrafficItem.hostname || selectedTrafficItem.ip }}</div>
              <div class="mt-1 font-mono text-xs text-slate-500 truncate">
                {{ selectedTrafficItem.ip }} · {{ selectedTrafficItem.mac || '无 MAC' }}
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-lg bg-slate-900/50 border border-slate-800 p-2">
                <div class="text-slate-500">总流量</div>
                <div class="numeric-value text-white mt-1">{{ fmtBytes(selectedTrafficItem.total_bytes) }}</div>
              </div>
              <div class="rounded-lg bg-slate-900/50 border border-slate-800 p-2">
                <div class="text-slate-500">连接数</div>
                <div class="numeric-value text-white mt-1">{{ selectedTrafficItem.connections || 0 }}</div>
              </div>
            </div>
            <div ref="trafficDetailRef" class="w-full h-44"></div>
          </div>
          <div v-else class="text-xs text-slate-500">点击上方排行中的设备查看详情</div>
        </section>
      </aside>
    </section>

    <!-- 接口列表 -->
    <div v-if="Object.keys(interfaces).length > 0" class="space-y-3">
      <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">网络接口</h3>
      <div class="grid gap-3">
        <div v-for="(stats, name) in interfaces" :key="name"
          class="app-panel rounded-lg p-4">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-bold text-white font-mono">{{ name }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded"
                :class="stats.rx_bytes > 0 ? 'bg-green-900/50 text-green-300' : 'bg-slate-800 text-slate-500'">
                {{ stats.rx_bytes > 0 ? '活跃' : '待机' }}
              </span>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span class="text-slate-500 block text-xs">下行</span>
              <span class="numeric-value text-cyan-400 font-bold">{{ fmtBytes(stats.rx_bytes) }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">上行</span>
              <span class="numeric-value text-amber-400 font-bold">{{ fmtBytes(stats.tx_bytes) }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">丢包 (RX/TX)</span>
              <span class="numeric-value text-slate-300">{{ stats.rx_errors }}/{{ stats.tx_errors }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">丢包 (RX/TX)</span>
              <span class="numeric-value text-slate-300">{{ stats.rx_dropped }}/{{ stats.tx_dropped }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="selectedDevice" class="text-center py-8 text-slate-500 text-sm">
      等待数据采集…
    </div>

    <!-- TCP 状态分布 -->
    <div v-if="tcpStates.length" class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
      <div class="app-panel rounded-lg p-4">
        <h3 class="text-sm font-semibold text-slate-300 mb-3">🔌 TCP 连接状态</h3>
        <div class="space-y-1.5">
          <div v-for="s in tcpStates" :key="s.state"
            class="flex items-center gap-2 text-sm">
            <span class="w-2 h-2 rounded-full"
              :class="stateColor(s.state)"></span>
            <span class="text-slate-400 w-24">{{ s.state }}</span>
            <div class="flex-1 h-4 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all"
                :style="{ width: (s.count / maxTcp * 100) + '%' }"
                :class="s.state === 'ESTAB' ? 'bg-green-400' : 'bg-slate-600'"></div>
            </div>
            <span class="numeric-value text-white text-right w-16">{{ s.count }}</span>
          </div>
        </div>
      </div>

      <!-- 协议分布 -->
      <div class="app-panel rounded-lg p-4">
        <h3 class="text-sm font-semibold text-slate-300 mb-3">📦 连接协议分布</h3>
        <div class="flex items-center justify-center h-48 sm:h-56 2xl:h-72">
          <div ref="protoChartRef" class="w-full h-full"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'
import TrafficRank from '../components/TrafficRank.vue'
import { getDeviceDisplayName, getDeviceIcon } from '../utils/deviceDisplay'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()
const devices = ref([])
const selectedDevice = ref('')
const latestSnapshot = ref(null)
const trafficHistory = ref(null)
const trafficPeriod = ref('day')
const selectedTrafficItem = ref(null)
const trafficDeviceDetail = ref(null)
const protoChartRef = ref(null)
const trafficTrendRef = ref(null)
const trafficDetailRef = ref(null)
let protoChart = null
let trafficTrendChart = null
let trafficDetailChart = null
let echartsModule = null

async function loadEcharts() {
  if (!echartsModule) {
    const mod = await import('../utils/echarts')
    echartsModule = mod.getEcharts()
  }
  return echartsModule
}

function deviceOptionLabel(device) {
  return `${getDeviceIcon(device)} ${getDeviceDisplayName(device)}`
}

const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || latestSnapshot.value?.data || null
})

const netData = computed(() => currentMetrics.value?.network)

const interfaces = computed(() => netData.value?.interfaces ?? {})
const trafficRank = computed(() => netData.value?.traffic_rank || {})
const trafficPeriods = [
  { key: 'day', label: '今日' },
  { key: 'week', label: '本周' },
  { key: 'month', label: '本月' },
]
const trafficSummary = computed(() => trafficHistory.value?.summary || {
  download_bytes: 0,
  upload_bytes: 0,
  total_bytes: 0,
  connections: 0,
})
const trafficAlerts = computed(() => trafficHistory.value?.alerts || [])
const trafficSummaryLabel = computed(() => {
  const item = trafficPeriods.find(period => period.key === trafficPeriod.value)
  return `${item?.label || '今日'} · 基于排行快照汇总`
})

const tcpStates = computed(() => {
  const states = netData.value?.tcp_states ?? {}
  return Object.entries(states).map(([state, count]) => ({ state, count }))
    .sort((a, b) => b.count - a.count)
})

const maxTcp = computed(() => Math.max(...tcpStates.value.map(s => s.count), 1))

function stateColor(state) {
  const colors = {
    'ESTAB': 'bg-green-400',
    'TIME-WAIT': 'bg-amber-400',
    'CLOSE-WAIT': 'bg-orange-400',
    'LAST-ACK': 'bg-red-400',
    'FIN-WAIT-1': 'bg-sky-400',
    'FIN-WAIT-2': 'bg-sky-400',
    'SYN-SENT': 'bg-blue-400',
    'SYN-RECV': 'bg-purple-400',
    'LISTEN': 'bg-slate-400',
  }
  return colors[state] || 'bg-slate-500'
}

function fmtBytes(b) {
  if (b >= 1e12) return (b / 1e12).toFixed(2) + ' TB'
  if (b >= 1e9) return (b / 1e9).toFixed(2) + ' GB'
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB'
  if (b >= 1e3) return (b / 1e3).toFixed(0) + ' KB'
  return b + ' B'
}

function fmtTimeLabel(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:00`
}

function setTrafficPeriod(period) {
  if (trafficPeriod.value === period) return
  trafficPeriod.value = period
  loadTrafficHistory()
}

async function renderProtoChart() {
  if (!protoChartRef.value) return
  const protos = netData.value?.conntrack_protocols ?? {}
  const entries = Object.entries(protos).filter(([_, v]) => v > 0)

  if (!protoChart) {
    const echarts = await loadEcharts()
    if (!protoChartRef.value || protoChart) return
    protoChart = echarts.init(protoChartRef.value, 'dark')
  }

  protoChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: entries.length > 0
        ? entries.map(([k, v]) => ({ name: k.toUpperCase(), value: v }))
        : [{ name: '无数据', value: 1 }],
      label: { color: '#94a3b8', fontSize: 11 },
      itemStyle: {
        borderRadius: 4,
        borderColor: '#0f172a',
        borderWidth: 2,
      },
      color: ['#22d3ee', '#fbbf24', '#a78bfa', '#34d399', '#f472b6', '#fb923c'],
    }],
  })
}

async function renderTrafficTrendChart() {
  if (!trafficTrendRef.value) return
  const echarts = await loadEcharts()
  if (!trafficTrendRef.value) return
  if (!trafficTrendChart) trafficTrendChart = echarts.init(trafficTrendRef.value, 'dark')
  const points = trafficHistory.value?.trend || []
  trafficTrendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['下载', '上传'], textStyle: { color: '#94a3b8', fontSize: 10 }, top: 0 },
    grid: { left: 48, right: 12, top: 32, bottom: 28 },
    xAxis: {
      type: 'category',
      data: points.map(item => fmtTimeLabel(item.t)),
      axisLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 9 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 9, formatter: value => fmtBytes(value).replace(' ', '') },
    },
    series: [
      { name: '下载', type: 'line', smooth: true, symbol: 'none', data: points.map(item => item.download_bytes || 0), lineStyle: { color: '#22d3ee', width: 1.5 } },
      { name: '上传', type: 'line', smooth: true, symbol: 'none', data: points.map(item => item.upload_bytes || 0), lineStyle: { color: '#fbbf24', width: 1.5 } },
    ],
  })
}

async function renderTrafficDetailChart() {
  if (!trafficDetailRef.value || !selectedTrafficItem.value) return
  const echarts = await loadEcharts()
  if (!trafficDetailRef.value || !selectedTrafficItem.value) return
  if (!trafficDetailChart) trafficDetailChart = echarts.init(trafficDetailRef.value, 'dark')
  const points = trafficDeviceDetail.value?.points || []
  trafficDetailChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 42, right: 8, top: 10, bottom: 26 },
    xAxis: { type: 'category', data: points.map(item => fmtTimeLabel(item.t)), axisLine: { show: false }, axisLabel: { color: '#64748b', fontSize: 9 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#64748b', fontSize: 9, formatter: value => fmtBytes(value).replace(' ', '') } },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: points.map(item => item.total_bytes || 0),
      lineStyle: { color: '#a78bfa', width: 1.5 },
    }],
  })
}

watch(netData, () => nextTick(renderProtoChart), { deep: true })
watch(trafficHistory, () => nextTick(renderTrafficTrendChart), { deep: true })
watch(trafficDeviceDetail, () => nextTick(renderTrafficDetailChart), { deep: true })

async function loadLatestSnapshot() {
  if (!selectedDevice.value) return
  try {
    latestSnapshot.value = await get(`/metrics/latest/${selectedDevice.value}`)
  } catch (e) {
    latestSnapshot.value = null
  }
}

async function loadTrafficHistory() {
  if (!selectedDevice.value) return
  try {
    trafficHistory.value = await get(`/metrics/traffic/${selectedDevice.value}?period=${trafficPeriod.value}&limit=12`)
    if (!selectedTrafficItem.value && trafficHistory.value?.top?.length) {
      selectedTrafficItem.value = trafficHistory.value.top[0]
      await loadTrafficDeviceDetail(selectedTrafficItem.value)
    }
  } catch (e) {
    trafficHistory.value = null
  }
}

async function loadTrafficDeviceDetail(item) {
  if (!selectedDevice.value || !item) return
  const params = new URLSearchParams({ hours: trafficPeriod.value === 'month' ? '168' : '24' })
  if (item.ip) params.set('ip', item.ip)
  if (item.mac) params.set('mac', item.mac)
  try {
    trafficDeviceDetail.value = await get(`/metrics/traffic/${selectedDevice.value}/device?${params}`)
  } catch (e) {
    trafficDeviceDetail.value = null
  }
}

async function selectTrafficDevice(item) {
  selectedTrafficItem.value = item
  await loadTrafficDeviceDetail(item)
}

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].id
      await loadLatestSnapshot()
      await loadTrafficHistory()
    }
  } catch (e) { /* ignore */ }
  nextTick(renderProtoChart)
})

watch(selectedDevice, async (value, oldValue) => {
  if (!value || value === oldValue) return
  latestSnapshot.value = null
  trafficHistory.value = null
  trafficDeviceDetail.value = null
  selectedTrafficItem.value = null
  await loadLatestSnapshot()
  await loadTrafficHistory()
})
</script>
