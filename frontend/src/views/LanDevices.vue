<template>
  <div class="p-3 lg:p-6 space-y-4 max-w-6xl mx-auto">
    <!-- 标题 -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-white">连接设备</h2>
        <p class="text-sm text-slate-400 mt-0.5">
          在线 <span class="text-green-400 font-bold">{{ onlineCount }}</span> ·
          总计 <span class="text-white font-bold">{{ totalCount }}</span>
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <input v-model="filterText" placeholder="搜索…"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 w-32 lg:w-48 focus:outline-none focus:border-brand-500 placeholder-slate-500" />
        <select v-model="selectedDevice"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name || d.host }}</option>
        </select>
      </div>
    </div>

    <!-- 在线/全部 切换 -->
    <div class="flex gap-2 overflow-x-auto">
      <button v-for="f in filters" :key="f.key"
        @click="activeFilter = f.key"
        class="text-sm px-3 py-1.5 rounded-lg transition-colors shrink-0"
        :class="activeFilter === f.key
          ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
          : 'text-slate-400 hover:text-slate-200 bg-slate-800/50 border border-slate-800'">
        {{ f.label }}
      </button>
    </div>

    <!-- 空状态 -->
    <div v-if="!selectedDevice" class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
      <div class="text-5xl mb-4">🖥️</div>
      <p class="text-slate-400">请先选择上面的设备</p>
    </div>

    <div v-else-if="filteredLeases.length === 0" class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
      <div class="text-4xl mb-3">📡</div>
      <p class="text-slate-400">暂无数据</p>
    </div>

    <!-- 设备列表 -->
    <div v-else>
      <!-- 桌面端表格 -->
      <div class="hidden lg:block bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-slate-400 text-xs uppercase border-b border-slate-800">
                <th class="text-left px-4 py-3 font-medium">状态</th>
                <th class="text-left px-4 py-3 font-medium">主机名</th>
                <th class="text-left px-4 py-3 font-medium">IP 地址</th>
                <th class="text-left px-4 py-3 font-medium">MAC 地址</th>
                <th class="text-left px-4 py-3 font-medium">租约剩余</th>
                <th class="text-left px-4 py-3 font-medium">备注</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/50">
              <tr v-for="lease in filteredLeases" :key="lease.mac"
                class="hover:bg-slate-800/40 transition-colors"
                :class="{ 'opacity-40': !lease.online }">
                <td class="px-4 py-3">
                  <span class="inline-flex items-center gap-1.5">
                    <span :class="lease.online ? 'dot-online' : 'dot-offline'"></span>
                    <span class="text-xs" :class="lease.online ? 'text-green-400' : 'text-slate-500'">{{ lease.online ? '在线' : '离线' }}</span>
                  </span>
                </td>
                <td class="px-4 py-3"><span class="text-white font-medium">{{ lease.hostname || '—' }}</span></td>
                <td class="px-4 py-3 font-mono text-slate-300">{{ lease.ip }}</td>
                <td class="px-4 py-3 font-mono text-slate-400 text-xs">{{ lease.mac }}</td>
                <td class="px-4 py-3 text-slate-400 text-xs">{{ lease.remain }}</td>
                <td class="px-4 py-3">
                  <input :value="remarks[lease.mac] || ''" @input="onRemarkInput(lease.mac, $event)" placeholder="备注…"
                    class="bg-transparent border-b border-slate-700 px-1 py-0.5 text-xs text-slate-300 w-24 focus:outline-none focus:border-brand-500 placeholder-slate-600" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 手机端卡片 -->
      <div class="lg:hidden space-y-2">
        <div v-for="lease in filteredLeases" :key="lease.mac"
          class="bg-slate-900/80 border border-slate-800 rounded-xl p-4"
          :class="{ 'opacity-50': !lease.online }">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span :class="lease.online ? 'dot-online' : 'dot-offline'"></span>
              <span class="text-sm font-medium text-white truncate">{{ lease.hostname || '未知设备' }}</span>
            </div>
            <span class="text-xs shrink-0" :class="lease.online ? 'text-green-400' : 'text-slate-500'">{{ lease.online ? '在线' : '离线' }}</span>
          </div>
          <div class="space-y-1 text-xs text-slate-400">
            <div class="flex justify-between">
              <span class="text-slate-500">IP</span>
              <span class="font-mono text-slate-300">{{ lease.ip }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">MAC</span>
              <span class="font-mono text-slate-400">{{ lease.mac }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">租约</span>
              <span>{{ lease.remain }}</span>
            </div>
            <div class="pt-1">
              <input :value="remarks[lease.mac] || ''" @input="onRemarkInput(lease.mac, $event)" placeholder="添加备注…"
                class="w-full bg-transparent border-b border-slate-700 px-1 py-1 text-xs text-slate-300 focus:outline-none focus:border-brand-500 placeholder-slate-600" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()

const devices = ref([])
const selectedDevice = ref('')
const filterText = ref('')
const activeFilter = ref('all')
const remarks = ref(JSON.parse(localStorage.getItem('device_remarks') || '{}'))

const filters = [
  { key: 'all', label: '全部' },
  { key: 'online', label: '在线' },
  { key: 'offline', label: '离线' },
]

const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || null
})

const lanData = computed(() => currentMetrics.value?.lan)

const leases = computed(() => lanData.value?.leases ?? [])
const onlineCount = computed(() => lanData.value?.online_count ?? 0)
const totalCount = computed(() => lanData.value?.total_count ?? 0)

const filteredLeases = computed(() => {
  let list = leases.value
  if (activeFilter.value === 'online') list = list.filter(l => l.online)
  else if (activeFilter.value === 'offline') list = list.filter(l => !l.online)
  if (filterText.value) {
    const q = filterText.value.toLowerCase()
    list = list.filter(l => l.ip.includes(q) || l.mac.toLowerCase().includes(q) || l.hostname.toLowerCase().includes(q))
  }
  return list
})

function onRemarkInput(mac, event) {
  remarks.value[mac] = event.target.value
  localStorage.setItem('device_remarks', JSON.stringify(remarks.value))
}

onMounted(async () => {
  try {
    const res = await fetch('/api/devices')
    devices.value = await res.json()
    if (devices.value.length > 0) selectedDevice.value = devices.value[0].id
  } catch (e) { /* ignore */ }
})
</script>
