<template>
  <div class="page-container page-container-wide space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <router-link to="/devices" class="hover:text-slate-300 transition-colors">设备管理</router-link>
          <span>/</span>
          <span class="text-slate-400">设备详情</span>
        </div>
        <div class="mt-2 flex items-center gap-3">
          <span class="grid place-items-center w-11 h-11 rounded-lg bg-slate-800/50 border border-slate-800 text-2xl">
            {{ deviceIcon }}
          </span>
          <h2 class="text-2xl font-bold text-white">{{ displayName }}</h2>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="loadDetail" :disabled="loading || refreshing"
          class="px-3 py-2 rounded-lg border border-slate-700 text-sm text-slate-300 hover:text-white hover:bg-slate-800/50 disabled:opacity-50 transition-colors">
          {{ refreshing ? '刷新中…' : '刷新详情' }}
        </button>
        <router-link to="/setup"
          class="bg-brand-600 hover:bg-brand-500 text-white px-3 py-2 rounded-lg text-sm transition-colors">
          初始化向导
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="app-panel-soft border-dashed rounded-lg p-12 text-center">
      <div class="text-3xl mb-3 animate-spin">⏳</div>
      <p class="text-sm text-slate-400">正在读取设备详情…</p>
    </div>

    <div v-else-if="loadError" class="app-panel-soft border-dashed rounded-lg p-12 text-center">
      <div class="text-4xl mb-3">⚠️</div>
      <h3 class="text-lg font-semibold text-slate-300">详情加载失败</h3>
      <p class="text-sm text-slate-500 mt-1">{{ loadError }}</p>
    </div>

    <template v-else>
      <section class="app-panel rounded-lg p-5 lg:p-6 overflow-hidden relative">
        <div class="device-hero-grid"></div>
        <div class="relative z-10 grid grid-cols-1 xl:grid-cols-[1.25fr_0.75fr] gap-6">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="status-pill text-xs" :class="isOnline ? 'text-green-400' : 'text-red-400'">
                <span :class="isOnline ? 'dot-online' : 'dot-offline'"></span>
                {{ isOnline ? '在线' : '离线' }}
              </span>
              <span class="status-pill text-xs text-slate-400">SSH {{ device?.host }}:{{ device?.port }}</span>
              <span v-if="probeError" class="status-pill text-xs text-amber-400">画像读取失败</span>
            </div>

            <div class="mt-5 flex items-center gap-3">
              <span class="grid place-items-center w-12 h-12 rounded-lg bg-slate-800/50 border border-slate-800 text-3xl shrink-0">
                {{ deviceIcon }}
              </span>
              <div class="min-w-0">
                <h3 class="text-2xl lg:text-3xl font-bold text-white break-words">{{ displayName }}</h3>
                <p class="mt-1 text-sm text-slate-500 truncate">{{ hostname }}</p>
              </div>
            </div>
            <p class="mt-2 text-sm text-slate-400 break-words">
              {{ modelText }} · {{ firmwareText }}
            </p>

            <div class="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-3 border-t border-slate-800 pt-5">
              <div class="min-w-0">
                <div class="text-[11px] text-slate-500">WAN</div>
                <div class="mt-1 metric-value text-sm font-mono text-white truncate">{{ publicIp }}</div>
              </div>
              <div class="min-w-0">
                <div class="text-[11px] text-slate-500">LAN</div>
                <div class="mt-1 metric-value text-sm font-mono text-white truncate">{{ device?.host || '-' }}</div>
              </div>
              <div class="min-w-0">
                <div class="text-[11px] text-slate-500">运行时间</div>
                <div class="mt-1 metric-value text-sm text-white truncate">{{ uptimeText }}</div>
              </div>
              <div class="min-w-0">
                <div class="text-[11px] text-slate-500">采集时间</div>
                <div class="mt-1 metric-value text-sm text-white truncate">{{ snapshotTime }}</div>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 content-center">
            <div class="device-ring">
              <svg viewBox="0 0 120 120" class="w-full h-full">
                <circle cx="60" cy="60" r="48" class="ring-track" />
                <circle cx="60" cy="60" r="48" class="ring-value cpu" :style="{ strokeDashoffset: ringOffset(cpuValue) }" />
              </svg>
              <div class="absolute inset-0 grid place-items-center text-center">
                <div>
                  <div class="text-[11px] text-slate-500">CPU</div>
                  <div class="metric-value text-2xl font-bold text-white">{{ cpuValue }}%</div>
                </div>
              </div>
            </div>
            <div class="device-ring">
              <svg viewBox="0 0 120 120" class="w-full h-full">
                <circle cx="60" cy="60" r="48" class="ring-track" />
                <circle cx="60" cy="60" r="48" class="ring-value memory" :style="{ strokeDashoffset: ringOffset(memValue) }" />
              </svg>
              <div class="absolute inset-0 grid place-items-center text-center">
                <div>
                  <div class="text-[11px] text-slate-500">内存</div>
                  <div class="metric-value text-2xl font-bold text-white">{{ memValue }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 2xl:grid-cols-6 gap-3 xl:gap-4">
        <MetricCard title="CPU" :value="cpuValue" suffix="%" icon="⚡" :progress="cpuValue" :glow="cpuValue > 80" />
        <MetricCard title="内存" :value="memValue" suffix="%" icon="🧠" :progress="memValue" />
        <MetricCard title="负载" :value="loadText" icon="📈" :subtitle="'1 / 5 / 15 分钟'" />
        <MetricCard title="温度" :value="tempValue" suffix="°C" icon="🌡️" :progress="temperatureProgress" :glow="tempValue > 70" />
        <MetricCard title="连接" :value="conntrackCount" icon="🔗" :subtitle="conntrackMax ? `上限 ${conntrackMax}` : ''" :progress="conntrackPercent" />
        <MetricCard title="LAN 在线" :value="onlineDeviceCount" suffix=" 台" icon="🖥️" :subtitle="totalDeviceCount ? `共 ${totalDeviceCount} 台` : ''" />
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 2xl:grid-cols-[1.6fr_0.75fr_0.75fr] gap-4 xl:gap-5 items-stretch">
        <div class="xl:col-span-2 min-h-[26rem]">
          <TrafficChart title="近 1 小时吞吐" :data="trafficChartData" unit="bytes" fill />
        </div>

        <section class="app-panel rounded-lg p-4 h-full">
          <h3 class="text-sm font-semibold text-slate-300 mb-4">系统可视化</h3>
          <div class="space-y-4">
            <div>
              <div class="flex items-center justify-between text-xs mb-2">
                <span class="text-slate-500">CPU 核心</span>
                <span class="text-slate-300">{{ cpuCores.length || 1 }} 核</span>
              </div>
              <div class="space-y-2">
                <div v-for="(core, index) in normalizedCores" :key="index" class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-slate-400">Core {{ index }}</span>
                    <span class="numeric-value text-slate-300">{{ core }}%</span>
                  </div>
                  <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500"
                      :class="core > 80 ? 'bg-red-400' : core > 50 ? 'bg-amber-400' : 'bg-cyan-400'"
                      :style="{ width: barWidth(core) }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="border-t border-slate-800 pt-4">
              <div class="flex items-center justify-between text-xs mb-2">
                <span class="text-slate-500">内存</span>
                <span class="text-slate-300">{{ memoryText }}</span>
              </div>
              <div class="h-2.5 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-green-400 transition-all duration-500"
                  :style="{ width: barWidth(memValue) }"></div>
              </div>
            </div>

            <div class="border-t border-slate-800 pt-4">
              <div class="text-xs text-slate-500 mb-2">磁盘</div>
              <div v-if="diskUsage.length" class="space-y-3">
                <div v-for="disk in diskUsage" :key="disk.mount" class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-slate-400">{{ disk.mount }}</span>
                    <span class="text-slate-300">{{ formatGb(disk.used_gb) }} / {{ formatGb(disk.total_gb) }}</span>
                  </div>
                  <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500"
                      :class="disk.percent > 80 ? 'bg-red-400' : disk.percent > 50 ? 'bg-amber-400' : 'bg-green-400'"
                      :style="{ width: barWidth(disk.percent) }"></div>
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-slate-500">暂无磁盘数据</div>
            </div>
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 2xl:grid-cols-3 gap-4 xl:gap-5">
        <section class="xl:col-span-2 app-panel rounded-lg p-4">
          <div class="flex items-center justify-between gap-3 mb-4">
            <h3 class="text-sm font-semibold text-slate-300">网络接口</h3>
            <span class="text-xs text-slate-500">{{ interfaceRows.length }} 个接口</span>
          </div>
          <div v-if="interfaceRows.length" class="space-y-2">
            <div v-for="iface in interfaceRows" :key="iface.name"
              class="grid grid-cols-1 lg:grid-cols-[1fr_1.8fr] gap-3 border border-slate-800 rounded-lg px-3 py-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full" :class="iface.isWan ? 'bg-cyan-400' : 'bg-green-400'"></span>
                  <span class="font-semibold text-white truncate">{{ iface.name }}</span>
                  <span v-if="iface.address" class="text-xs text-slate-500 font-mono truncate">{{ iface.address }}</span>
                </div>
                <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                  <span>RX {{ formatBytes(iface.rx_bytes) }}</span>
                  <span>TX {{ formatBytes(iface.tx_bytes) }}</span>
                  <span v-if="iface.rx_errors || iface.tx_errors" class="text-amber-400">
                    错误 {{ iface.rx_errors + iface.tx_errors }}
                  </span>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-slate-500">RX 包</span>
                    <span class="numeric-value text-slate-300">{{ iface.rx_packets }}</span>
                  </div>
                  <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-cyan-400 transition-all duration-500"
                      :style="{ width: iface.rxWidth }"></div>
                  </div>
                </div>
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-slate-500">TX 包</span>
                    <span class="numeric-value text-slate-300">{{ iface.tx_packets }}</span>
                  </div>
                  <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-amber-400 transition-all duration-500"
                      :style="{ width: iface.txWidth }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500 py-8 text-center">暂无接口数据</div>
        </section>

        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-4">连接状态</h3>
          <div class="space-y-5">
            <div>
              <div class="flex items-center justify-between text-xs mb-2">
                <span class="text-slate-500">Conntrack</span>
                <span class="text-slate-300">{{ conntrackPercent.toFixed(1) }}%</span>
              </div>
              <div class="h-3 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :class="conntrackPercent > 80 ? 'bg-red-400' : conntrackPercent > 50 ? 'bg-amber-400' : 'bg-green-400'"
                  :style="{ width: barWidth(conntrackPercent) }"></div>
              </div>
            </div>

            <div class="border-t border-slate-800 pt-4">
              <div class="text-xs text-slate-500 mb-3">TCP 状态</div>
              <div v-if="tcpStateRows.length" class="space-y-2">
                <div v-for="item in tcpStateRows" :key="item.name">
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="text-slate-400">{{ item.name }}</span>
                    <span class="numeric-value text-slate-300">{{ item.count }}</span>
                  </div>
                  <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-cyan-400 transition-all duration-500"
                      :style="{ width: item.width }"></div>
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-slate-500">暂无 TCP 状态数据</div>
            </div>

            <div class="border-t border-slate-800 pt-4">
              <div class="text-xs text-slate-500 mb-3">协议分布</div>
              <div v-if="protocolRows.length" class="flex flex-wrap gap-2">
                <span v-for="item in protocolRows" :key="item.name"
                  class="status-pill text-xs text-slate-300">
                  {{ item.name }} {{ item.count }}
                </span>
              </div>
              <div v-else class="text-xs text-slate-500">暂无协议数据</div>
            </div>
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 2xl:grid-cols-3 gap-4 xl:gap-5">
        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-4">设备画像</h3>
          <div class="space-y-3 text-sm">
            <DetailLine label="型号" :value="modelText" />
            <DetailLine label="板卡" :value="probe?.board_name || '-'" />
            <DetailLine label="固件" :value="firmwareText" />
            <DetailLine label="内核" :value="kernelText" />
            <DetailLine label="架构" :value="probe?.arch || '-'" />
            <DetailLine label="默认路由" :value="probe?.default_route || '-'" mono />
            <DetailLine label="DNS" :value="dnsText" mono />
            <DetailLine label="软件包" :value="probe?.package_count ? `${probe.package_count} 个` : '-'" />
          </div>
        </section>

        <section class="xl:col-span-2 app-panel rounded-lg p-4">
          <div class="flex items-center justify-between gap-3 mb-4">
            <h3 class="text-sm font-semibold text-slate-300">局域网在线设备</h3>
            <router-link to="/lan" class="text-xs text-brand-300 hover:text-white transition-colors">查看全部</router-link>
          </div>
          <div v-if="lanDevices.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="item in lanDevices" :key="item.mac || item.ip"
              class="border border-slate-800 rounded-lg px-3 py-3 min-w-0">
              <div class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <div class="font-semibold text-white truncate">{{ item.hostname || item.ip }}</div>
                  <div class="mt-1 text-xs text-slate-500 font-mono truncate">{{ item.mac }}</div>
                </div>
                <span class="status-pill text-xs" :class="item.online ? 'text-green-400' : 'text-slate-500'">
                  {{ item.online ? '在线' : '离线' }}
                </span>
              </div>
              <div class="mt-3 flex items-center justify-between text-xs">
                <span class="text-slate-500 font-mono">{{ item.ip }}</span>
                <span class="text-slate-400">{{ item.remain || '-' }}</span>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500 py-8 text-center">暂无局域网设备数据</div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import MetricCard from '../components/MetricCard.vue'
import TrafficChart from '../components/TrafficChart.vue'
import { useWebSocket } from '../composables/useWebSocket'
import { getDeviceDisplayName, getDeviceIcon } from '../utils/deviceDisplay'
import { formatLocalMinute, formatLocalTime } from '../utils/time'

const route = useRoute()
const { metrics: wsMetrics } = useWebSocket()

const detail = ref(null)
const history = ref({ points: [] })
const loading = ref(true)
const refreshing = ref(false)
const loadError = ref('')

const deviceId = computed(() => Number(route.params.id))
const device = computed(() => detail.value?.device || null)
const probe = computed(() => detail.value?.probe || null)
const probeError = computed(() => detail.value?.probe_error || '')
const snapshot = computed(() => detail.value?.snapshot || {})
const liveMetrics = computed(() => wsMetrics.value[deviceId.value] || snapshot.value?.data || null)

const sysRaw = computed(() => liveMetrics.value?.system || {})
const netRaw = computed(() => liveMetrics.value?.network || {})
const lanRaw = computed(() => liveMetrics.value?.lan || {})

const displayName = computed(() => getDeviceDisplayName(device.value))
const deviceIcon = computed(() => getDeviceIcon(device.value))
const hostname = computed(() => probe.value?.hostname || lanRaw.value?.router_hostname || device.value?.name || device.value?.host || '-')
const modelText = computed(() => probe.value?.model || '-')
const firmwareText = computed(() => probe.value?.firmware || device.value?.firmware || '-')
const kernelText = computed(() => probe.value?.kernel || '-')
const isOnline = computed(() => device.value?.online || Boolean(liveMetrics.value && !liveMetrics.value.error))
const publicIp = computed(() => netRaw.value?.public_ip || '-')
const cpuValue = computed(() => Number(sysRaw.value?.cpu_percent || 0).toFixed(1))
const memValue = computed(() => Number(sysRaw.value?.memory_percent || 0).toFixed(1))
const tempValue = computed(() => {
  const temps = sysRaw.value?.temperature_c
  return temps?.length ? Number(temps[0].temp_c || 0).toFixed(1) : 0
})
const temperatureProgress = computed(() => Math.min(100, Math.max(0, (Number(tempValue.value) - 30) * 1.7)))
const loadText = computed(() => {
  const a = Number(sysRaw.value?.load_1m || 0).toFixed(2)
  const b = Number(sysRaw.value?.load_5m || 0).toFixed(2)
  const c = Number(sysRaw.value?.load_15m || 0).toFixed(2)
  return `${a} / ${b} / ${c}`
})
const conntrackCount = computed(() => netRaw.value?.conntrack_count || 0)
const conntrackMax = computed(() => netRaw.value?.conntrack_max || 0)
const conntrackPercent = computed(() => Number(netRaw.value?.conntrack_percent || 0))
const onlineDeviceCount = computed(() => lanRaw.value?.online_count || 0)
const totalDeviceCount = computed(() => lanRaw.value?.total_count || 0)
const cpuCores = computed(() => sysRaw.value?.cpu_per_core || [])
const normalizedCores = computed(() => cpuCores.value.length ? cpuCores.value : [Number(cpuValue.value)])
const diskUsage = computed(() => sysRaw.value?.disk_usage || [])
const memoryText = computed(() => {
  const used = sysRaw.value?.memory_used_mb
  const total = sysRaw.value?.memory_total_mb
  if (!total) return '-'
  return `${formatMb(used)} / ${formatMb(total)}`
})
const uptimeText = computed(() => formatUptime(
  sysRaw.value?.uptime_seconds || probe.value?.uptime_seconds || device.value?.uptime || 0,
))
const snapshotTime = computed(() => formatTime(snapshot.value?.collected_at || liveMetrics.value?.timestamp))
const dnsText = computed(() => probe.value?.dns?.length ? probe.value.dns.join(', ') : '-')

const DetailLine = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], default: '-' },
    mono: Boolean,
  },
  setup(props) {
    return () => h('div', { class: 'grid grid-cols-[5rem_1fr] gap-3 border-b border-slate-800 last:border-b-0 pb-3 last:pb-0' }, [
      h('span', { class: 'text-slate-500' }, props.label),
      h('span', {
        class: [
          'text-slate-200 min-w-0 break-words',
          props.mono ? 'font-mono text-xs' : '',
        ],
      }, props.value || '-'),
    ])
  },
})

const addressMap = computed(() => {
  const map = {}
  for (const item of probe.value?.interfaces || []) {
    map[item.name] = `${item.address}/${item.prefix}`
  }
  return map
})

const wanName = computed(() => {
  const ifaces = netRaw.value?.interfaces || {}
  const names = Object.keys(ifaces)
  return names.find(n => n === 'pppoe-wan')
    || names.find(n => n === 'eth1')
    || names.find(n => !['lo', 'sit0', 'dummy0', 'gre0', 'gretap0', 'erspan0', 'docker0'].includes(n))
    || names[0]
    || ''
})

const interfaceRows = computed(() => {
  const ifaces = netRaw.value?.interfaces || {}
  const rows = Object.entries(ifaces).map(([name, data]) => ({
    name,
    address: addressMap.value[name] || '',
    isWan: name === wanName.value,
    ...data,
  }))
  const maxRx = Math.max(...rows.map(item => item.rx_packets || 0), 1)
  const maxTx = Math.max(...rows.map(item => item.tx_packets || 0), 1)
  return rows
    .sort((a, b) => Number(b.isWan) - Number(a.isWan) || (b.rx_bytes + b.tx_bytes) - (a.rx_bytes + a.tx_bytes))
    .map(item => ({
      ...item,
      rxWidth: barWidth((item.rx_packets || 0) / maxRx * 100),
      txWidth: barWidth((item.tx_packets || 0) / maxTx * 100),
    }))
})

const tcpStateRows = computed(() => {
  const entries = Object.entries(netRaw.value?.tcp_states || {})
    .map(([name, count]) => ({ name, count: Number(count) }))
    .sort((a, b) => b.count - a.count)
  const max = Math.max(...entries.map(item => item.count), 1)
  return entries.map(item => ({
    ...item,
    width: barWidth(item.count / max * 100),
  }))
})

const protocolRows = computed(() => Object.entries(netRaw.value?.conntrack_protocols || {})
  .map(([name, count]) => ({ name, count }))
  .sort((a, b) => Number(b.count) - Number(a.count)))

const lanDevices = computed(() => (lanRaw.value?.leases || [])
  .slice()
  .sort((a, b) => Number(b.online) - Number(a.online))
  .slice(0, 8))

const trafficChartData = computed(() => (history.value.points || []).map((point) => {
  return {
    time: formatLocalMinute(point.t),
    rx: point.rx || 0,
    tx: point.tx || 0,
  }
}))

async function requestJson(url) {
  const res = await fetch(url)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}

async function loadDetail() {
  loadError.value = ''
  if (!loading.value) refreshing.value = true
  try {
    detail.value = await requestJson(`/api/devices/${deviceId.value}/detail`)
  } catch (e) {
    loadError.value = e.message
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function loadHistory() {
  try {
    history.value = await requestJson(`/api/metrics/history/${deviceId.value}?hours=1`)
  } catch (e) {
    history.value = { points: [] }
  }
}

function barWidth(value) {
  const percent = Math.min(100, Math.max(0, Number(value) || 0))
  if (percent === 0) return '0%'
  return `${Math.max(percent, 4)}%`
}

function ringOffset(value) {
  const radius = 48
  const circumference = 2 * Math.PI * radius
  const percent = Math.min(100, Math.max(0, Number(value) || 0))
  return circumference - (percent / 100) * circumference
}

function formatUptime(seconds) {
  const s = Number(seconds || 0)
  if (!s) return '-'
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const mins = Math.floor((s % 3600) / 60)
  if (days > 0) return `${days}天 ${hours}小时`
  if (hours > 0) return `${hours}小时 ${mins}分钟`
  return `${mins}分钟`
}

function formatTime(value) {
  return formatLocalTime(value)
}

function formatMb(value) {
  const mb = Number(value || 0)
  if (mb >= 1024) return `${(mb / 1024).toFixed(2)} GB`
  return `${mb.toFixed(0)} MB`
}

function formatGb(value) {
  const gb = Number(value || 0)
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  return `${(gb * 1024).toFixed(0)} MB`
}

function formatBytes(value) {
  let val = Number(value || 0)
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let index = 0
  while (val >= 1024 && index < units.length - 1) {
    val /= 1024
    index += 1
  }
  return `${val.toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

onMounted(async () => {
  await Promise.all([loadDetail(), loadHistory()])
})

watch(() => route.params.id, async () => {
  loading.value = true
  await Promise.all([loadDetail(), loadHistory()])
})
</script>

<style scoped>
.device-hero-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--c-cyan-400) 8%, transparent) 1px, transparent 1px),
    linear-gradient(color-mix(in srgb, var(--c-cyan-400) 8%, transparent) 1px, transparent 1px),
    radial-gradient(circle at 82% 20%, color-mix(in srgb, var(--c-brand-600) 24%, transparent), transparent 22rem);
  background-size: 34px 34px, 34px 34px, auto;
  mask-image: linear-gradient(90deg, black, transparent 90%);
}

.device-ring {
  position: relative;
  aspect-ratio: 1;
  min-height: 9rem;
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-surface-muted) 58%, transparent);
  border: 1px solid var(--app-border);
}

.ring-track,
.ring-value {
  fill: none;
  stroke-width: 9;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.ring-track {
  stroke: color-mix(in srgb, var(--c-sl-700) 60%, transparent);
}

.ring-value {
  stroke-linecap: round;
  stroke-dasharray: 301.59;
  transition: stroke-dashoffset .5s ease;
}

.ring-value.cpu {
  stroke: var(--c-cyan-400);
}

.ring-value.memory {
  stroke: var(--c-green-400);
}
</style>
