<template>
  <div class="p-3 lg:p-6 space-y-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">网络分析</h2>
        <p class="text-sm text-slate-400 mt-0.5">接口详情 · 连接状态 · 协议分布</p>
      </div>
      <select v-model="selectedDevice"
        class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
        <option value="">选择设备…</option>
        <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name || d.host }}</option>
      </select>
    </div>

    <!-- 接口列表 -->
    <div v-if="Object.keys(interfaces).length > 0" class="space-y-3">
      <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">网络接口</h3>
      <div class="grid gap-3">
        <div v-for="(stats, name) in interfaces" :key="name"
          class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
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
              <span class="text-cyan-400 font-mono font-bold">{{ fmtBytes(stats.rx_bytes) }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">上行</span>
              <span class="text-amber-400 font-mono font-bold">{{ fmtBytes(stats.tx_bytes) }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">丢包 (RX/TX)</span>
              <span class="text-slate-300 font-mono">{{ stats.rx_errors }}/{{ stats.tx_errors }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs">丢包 (RX/TX)</span>
              <span class="text-slate-300 font-mono">{{ stats.rx_dropped }}/{{ stats.tx_dropped }}</span>
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
      <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
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
            <span class="text-white font-mono text-right w-16">{{ s.count }}</span>
          </div>
        </div>
      </div>

      <!-- 协议分布 -->
      <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <h3 class="text-sm font-semibold text-slate-300 mb-3">📦 连接协议分布</h3>
        <div class="flex items-center justify-center h-48">
          <div ref="protoChartRef" class="w-full h-full"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()
const devices = ref([])
const selectedDevice = ref('')
const protoChartRef = ref(null)
let protoChart = null

const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || null
})

const netData = computed(() => currentMetrics.value?.network)

const interfaces = computed(() => netData.value?.interfaces ?? {})

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

function renderProtoChart() {
  if (!protoChartRef.value) return
  const protos = netData.value?.conntrack_protocols ?? {}
  const entries = Object.entries(protos).filter(([_, v]) => v > 0)

  if (!protoChart) {
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

watch(netData, () => nextTick(renderProtoChart), { deep: true })

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0)
      selectedDevice.value = devices.value[0].id
  } catch (e) { /* ignore */ }
  nextTick(renderProtoChart)
})
</script>
