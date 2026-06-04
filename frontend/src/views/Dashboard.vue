<template>
  <div class="p-6 space-y-6 max-w-7xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">仪表盘</h2>
        <p class="text-sm text-slate-400 mt-0.5">实时监控 · 数据 {{ interval }}s 刷新</p>
      </div>
      <div class="flex items-center gap-3">
        <select v-model="interval" @change="changeInterval"
          class="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="1">1s</option>
          <option value="3">3s</option>
          <option value="5">5s</option>
          <option value="10">10s</option>
        </select>
        <select v-model="selectedDevice"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">
            {{ d.name || d.host }}
          </option>
        </select>
      </div>
    </div>

    <!-- 无设备提示 -->
    <div v-if="devices.length === 0"
      class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
      <div class="text-5xl mb-4">📡</div>
      <h3 class="text-lg font-semibold text-slate-300 mb-2">还没有添加设备</h3>
      <p class="text-sm text-slate-500 mb-4">先去「设备管理」添加你的 OpenWrt 路由器</p>
      <router-link to="/devices"
        class="inline-block bg-brand-600 hover:bg-brand-500 text-white px-6 py-2 rounded-lg text-sm transition-colors">
        + 添加设备
      </router-link>
    </div>

    <!-- 指标卡片行 -->
    <div v-if="currentMetrics && devices.length > 0">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <MetricCard
          title="CPU"
          :value="cpuValue"
          suffix="%"
          icon="⚡"
          :progress="cpuValue"
          :glow="cpuValue > 80" />
        <MetricCard
          title="内存"
          :value="memValue"
          suffix="%"
          icon="🧠"
          :progress="memValue" />
        <MetricCard
          title="温度"
          :value="tempValue"
          suffix="°C"
          icon="🌡️"
          :progress="tempValue > 50 ? (tempValue - 50) * 2 : 0"
          :glow="tempValue > 70" />
        <MetricCard
          title="上行"
          :value="txRate"
          suffix="/s"
          icon="⬆️"
          :subtitle="wanName"
          :progress="0" />
        <MetricCard
          title="下行"
          :value="rxRate"
          suffix="/s"
          icon="⬇️"
          :subtitle="wanName"
          :progress="0" />
      </div>

      <!-- 流量曲线 -->
      <div class="mt-6">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-slate-300">
            {{ trafficTimeRange === '0' ? '实时网络流量' : '历史网络流量' }}
            <span class="text-xs text-slate-500 font-normal ml-1">({{ trafficTimeLabel }})</span>
          </h3>
          <div class="flex items-center gap-2">
            <select v-model="trafficTimeRange" @change="loadTrafficHistory"
              class="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
              <option value="0">实时</option>
              <option value="1">近 1 小时</option>
              <option value="6">近 6 小时</option>
              <option value="24">近 24 小时</option>
            </select>
            <button @click="toggleUnit"
              class="text-xs px-2.5 py-1 rounded-lg border transition-colors"
              :class="unitMode === 'bits'
                ? 'border-brand-600 bg-brand-600/20 text-brand-300'
                : 'border-slate-700 bg-slate-800 text-slate-400 hover:text-slate-200'">
              {{ unitMode === 'bits' ? 'b/s' : 'B/s' }}
            </button>
          </div>
        </div>
        <TrafficChart :height="'280px'" :data="chartData" :unit="unitMode" />
      </div>

      <!-- 第二行：负载 + 连接 + 磁盘 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        <!-- 系统负载 -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">📈 系统负载</h3>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-400">1 分钟</span>
              <span class="text-white font-mono font-bold">{{ sysLoad1 }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-400">5 分钟</span>
              <span class="text-white font-mono font-bold">{{ sysLoad5 }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-400">15 分钟</span>
              <span class="text-white font-mono font-bold">{{ sysLoad15 }}</span>
            </div>
          </div>
        </div>

        <!-- 连接跟踪 -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">🔗 连接跟踪</h3>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-400">当前连接</span>
              <span class="text-white font-mono font-bold">{{ conntrackCount }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-400">最大连接</span>
              <span class="text-white font-mono font-bold">{{ conntrackMax }}</span>
            </div>
            <div class="mt-2 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500"
                :style="{ width: conntrackPercent + '%' }"
                :class="conntrackPercent > 80 ? 'bg-red-400' : conntrackPercent > 50 ? 'bg-amber-400' : 'bg-green-400'">
              </div>
            </div>
          </div>
        </div>

        <!-- 磁盘 -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">💾 磁盘使用</h3>
          <div class="space-y-3" v-if="diskUsage.length">
            <div v-for="disk in diskUsage" :key="disk.mount" class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-slate-400">{{ disk.mount }}</span>
                <span class="text-slate-300">{{ fmtDiskSize(disk.used_gb) }} / {{ fmtDiskSize(disk.total_gb) }}</span>
              </div>
              <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :style="{ width: disk.percent + '%' }"
                  :class="disk.percent > 80 ? 'bg-red-400' : disk.percent > 50 ? 'bg-amber-400' : 'bg-green-400'">
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-xs text-slate-500">暂无数据</div>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-12 text-slate-500">
      <div class="animate-spin text-3xl mb-2">⏳</div>
      <p>加载中…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import MetricCard from '../components/MetricCard.vue'
import TrafficChart from '../components/TrafficChart.vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()

const devices = ref([])
const selectedDevice = ref('')
const loading = ref(true)
const trafficHistory = ref([])
const unitMode = ref('bits') // 'bits' | 'bytes'
const interval = ref(3)

async function changeInterval() {
  try {
    await fetch('/api/settings/interval', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_seconds: Number(interval.value) }),
    })
  } catch (e) {
    console.error('修改采集间隔失败', e)
  }
}

function toggleUnit() {
  unitMode.value = unitMode.value === 'bits' ? 'bytes' : 'bits'
}

// 流量历史
const trafficTimeRange = ref('0')
const trafficHistoryData = ref({ points: [] })

const trafficTimeLabel = computed(() => {
  const labels = { '0': '实时', '1': '近1小时', '6': '近6小时', '24': '近24小时' }
  return labels[trafficTimeRange.value] || '实时'
})

const chartData = computed(() => {
  if (trafficTimeRange.value !== '0' && trafficHistoryData.value.points?.length) {
    // 历史模式：用 API 返回的数据
    const pts = trafficHistoryData.value.points
    const step = Math.max(1, Math.floor(pts.length / 120))  // 降采样到约 120 点
    const sampled = []
    for (let i = 0; i < pts.length; i += step) {
      const d = new Date(pts[i].t)
      sampled.push({
        time: d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0'),
        rx: pts[i].rx,
        tx: pts[i].tx,
      })
    }
    return sampled
  }
  // 实时模式
  return trafficHistory.value
})

async function loadTrafficHistory() {
  if (!selectedDevice.value || trafficTimeRange.value === '0') return
  try {
    const res = await fetch(`/api/metrics/history/${selectedDevice.value}?hours=${trafficTimeRange.value}`)
    trafficHistoryData.value = await res.json()
  } catch (e) {
    console.error('加载流量历史失败', e)
  }
}

// 从 WebSocket 获取当前设备指标
const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || null
})

// 格式函数 — 支持 bits/s 和 bytes/s
function fmtBits(val, mode) {
  if (!val || val === 0) return mode === 'bits' ? '0 b' : '0 B'
  const div = mode === 'bytes' ? 1 : 1 // val already in bits for 'bits', in bytes for 'bytes'
  const threshold = mode === 'bytes' ? 1024 : 1000
  const suffix = mode === 'bytes' ? ['B', 'KB', 'MB', 'GB', 'TB'] : ['b', 'Kb', 'Mb', 'Gb', 'Tb']
  const step = mode === 'bytes' ? 1024 : 1000
  let v = val
  let i = 0
  while (v >= step && i < suffix.length - 1) { v /= step; i++ }
  return v.toFixed(i === 0 ? 0 : 1) + ' ' + suffix[i]
}

function fmtDiskSize(gb) {
  if (!gb || gb === 0) return '0 B'
  if (gb >= 1) return gb.toFixed(2) + ' GB'
  const mb = gb * 1024
  if (mb >= 1) return mb.toFixed(2) + ' MB'
  const kb = mb * 1024
  return kb.toFixed(2) + ' KB'
}

// 派生指标
const cpuValue = computed(() => currentMetrics.value?.system?.cpu_percent ?? 0)
const memValue = computed(() => currentMetrics.value?.system?.memory_percent ?? 0)
const tempValue = computed(() => {
  const temps = currentMetrics.value?.system?.temperature_c
  return temps?.length ? temps[0].temp_c : 0
})

const sysRaw = computed(() => currentMetrics.value?.system)
const netRaw = computed(() => currentMetrics.value?.network)

const sysLoad1 = computed(() => sysRaw.value?.load_1m?.toFixed(2) ?? '-')
const sysLoad5 = computed(() => sysRaw.value?.load_5m?.toFixed(2) ?? '-')
const sysLoad15 = computed(() => sysRaw.value?.load_15m?.toFixed(2) ?? '-')

const conntrackCount = computed(() => netRaw.value?.conntrack_count ?? 0)
const conntrackMax = computed(() => netRaw.value?.conntrack_max ?? 65536)
const conntrackPercent = computed(() => netRaw.value?.conntrack_percent ?? 0)

const diskUsage = computed(() => sysRaw.value?.disk_usage ?? [])

// 流量速率（从接口累计差值计算）
let lastRx = {}
let lastTx = {}
const rxRate = ref('0 b')
const txRate = ref('0 b')
const wanName = ref('pppoe-wan')
let trafficTimer = null

function updateTraffic() {
  const ifaces = netRaw.value?.interfaces
  if (!ifaces) return

  const now = new Date()
  const time = now.getHours().toString().padStart(2, '0') + ':' +
               now.getMinutes().toString().padStart(2, '0') + ':' +
               now.getSeconds().toString().padStart(2, '0')

  // 只取 WAN 口流量（pppoe-wan > eth1 > 第一个非虚拟接口）
  const wanKey = Object.keys(ifaces).find(n => n === 'pppoe-wan')
             || Object.keys(ifaces).find(n => n === 'eth1')
             || Object.keys(ifaces).find(n => !['sit0','dummy0','gre0','gretap0','erspan0','docker0'].includes(n))
  if (wanKey) wanName.value = wanKey
  const totalRx = wanKey ? (ifaces[wanKey]?.rx_bytes || 0) : 0
  const totalTx = wanKey ? (ifaces[wanKey]?.tx_bytes || 0) : 0

  const deviceId = selectedDevice.value
  if (lastRx[deviceId] !== undefined) {
    const rxDiffBytes = totalRx - lastRx[deviceId]
    const txDiffBytes = totalTx - lastTx[deviceId]

    // 根据单位模式：bits 模式要 *8，bytes 模式直接用
    const rxDiff = unitMode.value === 'bits' ? rxDiffBytes * 8 : rxDiffBytes
    const txDiff = unitMode.value === 'bits' ? txDiffBytes * 8 : txDiffBytes

    rxRate.value = fmtBits(rxDiff, unitMode.value)
    txRate.value = fmtBits(txDiff, unitMode.value)

    trafficHistory.value.push({ time, rx: rxDiff, tx: txDiff })
    if (trafficHistory.value.length > 120) {
      trafficHistory.value = trafficHistory.value.slice(-120)
    }
  }

  lastRx[deviceId] = totalRx
  lastTx[deviceId] = totalTx
}

// 自动选择第一个设备 + 加载采集间隔
onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].id
    }
    const res = await fetch('/api/settings/interval')
    const data = await res.json()
    if (data.interval_seconds) interval.value = data.interval_seconds
  } catch (e) {
    console.error('初始化加载失败', e)
  }
  loading.value = false
})

// 监听 WebSocket 数据更新流量
watch(currentMetrics, () => {
  if (trafficTimeRange.value === '0') {
    updateTraffic()
  }
}, { deep: true })

// 设备切换时重新加载历史流量
watch(selectedDevice, () => {
  if (trafficTimeRange.value !== '0') {
    loadTrafficHistory()
  }
})
</script>
