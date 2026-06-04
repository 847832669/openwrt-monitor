<template>
  <div class="p-3 lg:p-6 space-y-6 max-w-6xl mx-auto">
    <!-- 标题 + 设备统计 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">连接设备</h2>
        <p class="text-sm text-slate-400 mt-0.5">
          在线 <span class="text-green-400 font-bold">{{ onlineCount }}</span> ·
          总计 <span class="text-white font-bold">{{ totalCount }}</span>
        </p>
      </div>
      <div class="flex items-center gap-3">
        <input v-model="filterText" placeholder="搜索 IP / MAC / 名称…"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 w-48 focus:outline-none focus:border-brand-500 placeholder-slate-500" />
        <select v-model="selectedDevice"
          class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name || d.host }}</option>
        </select>
      </div>
    </div>

    <!-- 在线/全部 切换 -->
    <div class="flex gap-2">
      <button v-for="f in filters" :key="f.key"
        @click="activeFilter = f.key"
        class="text-sm px-3 py-1.5 rounded-lg transition-colors"
        :class="activeFilter === f.key
          ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
          : 'text-slate-400 hover:text-slate-200 bg-slate-800/50 border border-slate-800'">
        {{ f.label }}
      </button>
    </div>

    <!-- 无设备提示 -->
    <div v-if="!selectedDevice" class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
      <div class="text-5xl mb-4">🖥️</div>
      <p class="text-slate-400">请先选择上面的设备</p>
    </div>

    <!-- 设备表格 -->
    <div v-else-if="filteredLeases.length === 0" class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
      <div class="text-4xl mb-3">📡</div>
      <p class="text-slate-400">暂无数据</p>
      <p class="text-xs text-slate-500 mt-1">等待采集数据中…</p>
    </div>

    <div v-else class="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
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
                <span class="text-xs" :class="lease.online ? 'text-green-400' : 'text-slate-500'">
                  {{ lease.online ? '在线' : '离线' }}
                </span>
              </span>
            </td>
            <td class="px-4 py-3">
              <span class="text-white font-medium">{{ lease.hostname || '—' }}</span>
            </td>
            <td class="px-4 py-3 font-mono text-slate-300">{{ lease.ip }}</td>
            <td class="px-4 py-3 font-mono text-slate-400 text-xs">{{ lease.mac }}</td>
            <td class="px-4 py-3 text-slate-400 text-xs">{{ lease.remain }}</td>
            <td class="px-4 py-3">
              <input
                :value="remarks[lease.mac] || ''"
                @input="onRemarkInput(lease.mac, $event)"
                placeholder="添加备注…"
                class="bg-transparent border-b border-slate-700 px-1 py-0.5 text-xs text-slate-300 w-28 focus:outline-none focus:border-brand-500 placeholder-slate-600"
              />
            </td>
          </tr>
        </tbody>
      </table>
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
  if (activeFilter.value === 'online') {
    list = list.filter(l => l.online)
  } else if (activeFilter.value === 'offline') {
    list = list.filter(l => !l.online)
  }
  if (filterText.value) {
    const q = filterText.value.toLowerCase()
    list = list.filter(l =>
      l.ip.includes(q) ||
      l.mac.toLowerCase().includes(q) ||
      l.hostname.toLowerCase().includes(q)
    )
  }
  return list
})

function onRemarkInput(mac, event) {
  // 直接修改 ref 内部对象，触发响应式更新
  remarks.value[mac] = event.target.value
  localStorage.setItem('device_remarks', JSON.stringify(remarks.value))
}

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].id
    }
  } catch (e) { /* ignore */ }
})
</script>
