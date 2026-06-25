<template>
  <div class="page-container page-container-medium space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">设备管理</h2>
        <p class="text-sm text-slate-400 mt-0.5">添加和管理 OpenWrt 路由器</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <router-link to="/setup"
          class="hidden sm:inline-flex items-center px-3 py-2 rounded-lg border border-slate-700 text-sm text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors">
          初始化向导
        </router-link>
        <button @click="showAdd = true"
          class="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm transition-colors">
          + 添加设备
        </button>
      </div>
    </div>

    <!-- 设备列表 -->
    <div class="space-y-3">
      <div v-for="item in devices" :key="item.id"
        class="app-panel rounded-lg p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between hover:border-slate-700 transition-colors">
        <div class="flex min-w-0 items-center gap-4">
          <div class="relative grid place-items-center w-12 h-12 rounded-lg bg-slate-800/50 border border-slate-800 text-2xl shrink-0">
            {{ getDeviceIcon(item) }}
            <span class="absolute -right-0.5 -bottom-0.5 ring-4 ring-slate-950"
              :class="item.online ? 'dot-online' : 'dot-offline'"></span>
          </div>
          <div class="min-w-0">
            <div class="flex min-w-0 items-center gap-2">
              <span class="font-semibold text-white truncate">{{ getDeviceDisplayName(item) }}</span>
              <span v-if="!item.name" class="text-xs text-slate-500">(未设置别名)</span>
            </div>
            <div class="text-xs text-slate-400 mt-0.5 break-all">
              {{ item.host }}:{{ item.port }}
              <span v-if="item.firmware" class="ml-2">{{ item.firmware }}</span>
              <span class="ml-2">{{ item.username }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2 sm:justify-end">
          <span v-if="item.uptime > 0" class="text-xs text-slate-500">
            {{ formatUptime(item.uptime) }}
          </span>
          <router-link :to="`/devices/${item.id}`"
            class="text-slate-500 hover:text-brand-400 px-2 py-1 text-sm transition-colors" title="详情">
            详情
          </router-link>
          <button @click="editDevice(item)"
            class="text-slate-500 hover:text-brand-400 px-2 py-1 text-sm transition-colors" title="编辑">
            ✏️
          </button>
          <button @click="deleteDevice(item.id)"
            class="text-slate-500 hover:text-red-400 px-2 py-1 text-sm transition-colors">
            ✕
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="devices.length === 0 && !loading"
        class="app-panel-soft border-dashed rounded-lg p-12 text-center">
        <div class="text-4xl mb-3">📡</div>
        <p class="text-slate-400">还没有添加设备</p>
        <p class="text-xs text-slate-500 mt-1">使用初始化向导接入你的第一台 OpenWrt 路由器</p>
        <router-link to="/setup"
          class="inline-flex mt-4 bg-brand-600 hover:bg-brand-500 text-white px-5 py-2 rounded-lg text-sm transition-colors">
          开始初始化
        </router-link>
      </div>
    </div>

    <!-- 添加设备弹窗 -->
    <div v-if="showAdd"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div class="app-panel rounded-lg p-4 sm:p-6 w-full max-w-md mx-4 max-h-[90dvh] overflow-y-auto">
        <h3 class="text-lg font-semibold text-white mb-4">{{ editingDevice ? '编辑设备' : '添加设备' }}</h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-slate-400 block mb-1">设备别名（可选）</label>
            <input v-model="form.name"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              placeholder="例如：主路由" />
          </div>
          <div>
            <label class="text-xs text-slate-400 block mb-2">设备图标</label>
            <div class="grid grid-cols-4 gap-2">
              <button v-for="item in DEVICE_ICONS" :key="item.key" type="button"
                @click="form.icon = item.key"
                class="rounded-lg border px-2 py-2 text-center transition-colors"
                :class="form.icon === item.key
                  ? 'border-brand-600 bg-brand-600/20 text-white'
                  : 'border-slate-700 bg-slate-800/40 text-slate-400 hover:text-slate-200 hover:border-slate-600'">
                <span class="block text-xl leading-none">{{ item.icon }}</span>
                <span class="mt-1 block text-[11px] truncate">{{ item.label }}</span>
              </button>
            </div>
          </div>
          <div>
            <label class="text-xs text-slate-400 block mb-1">IP 地址 *</label>
            <input v-model="form.host"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              placeholder="192.168.1.1" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-slate-400 block mb-1">端口</label>
              <input v-model.number="form.port"
                class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label class="text-xs text-slate-400 block mb-1">用户名</label>
              <input v-model="form.username"
                class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
          </div>
          <div>
            <label class="text-xs text-slate-400 block mb-1">认证方式</label>
            <select v-model="form.auth_type"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500">
              <option value="key">SSH 密钥</option>
              <option value="password">密码</option>
            </select>
          </div>
          <div v-if="form.auth_type === 'key'">
            <label class="text-xs text-slate-400 block mb-1">密钥路径</label>
            <input v-model="form.private_key_path"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              placeholder="~/.ssh/id_rsa" />
          </div>
          <div v-else>
            <label class="text-xs text-slate-400 block mb-1">密码</label>
            <input v-model="form.password" type="password"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-6">
          <button @click="cancelModal()"
            class="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">取消</button>
          <button @click="editingDevice ? saveEdit() : addDevice()"
            class="bg-brand-600 hover:bg-brand-500 text-white px-6 py-2 rounded-lg text-sm transition-colors"
            :disabled="!form.host">
            {{ editingDevice ? '保存' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { DEVICE_ICONS, getDeviceDisplayName, getDeviceIcon } from '../utils/deviceDisplay'

const { get, post, del } = useApi()
const devices = ref([])
const loading = ref(true)
const showAdd = ref(false)
const form = ref({
  name: '', icon: 'router', host: '', port: 22, username: 'root',
  auth_type: 'key', private_key_path: '~/.ssh/id_rsa', password: '',
})
const editingDevice = ref(null)

function editDevice(item) {
  editingDevice.value = item
  form.value = {
    name: item.name || '',
    icon: item.icon || 'router',
    host: item.host,
    port: item.port,
    username: item.username,
    auth_type: item.auth_type,
    private_key_path: item.private_key_path || '',
    password: '',
  }
  showAdd.value = true
}

function cancelModal() {
  showAdd.value = false
  editingDevice.value = null
  form.value = { name: '', icon: 'router', host: '', port: 22, username: 'root',
    auth_type: 'key', private_key_path: '~/.ssh/id_rsa', password: '' }
}

async function saveEdit() {
  if (!editingDevice.value) return
  try {
    // 不传密码（保持原密码）如果密码没修改
    const body = { ...form.value }
    if (!body.password) delete body.password
    const res = await fetch(`/api/devices/${editingDevice.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    cancelModal()
    await loadDevices()
  } catch (e) {
    alert('保存失败: ' + e.message)
  }
}

async function loadDevices() {
  try {
    devices.value = await get('/devices')
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function addDevice() {
  try {
    await post('/devices', form.value)
    showAdd.value = false
    form.value = { name: '', icon: 'router', host: '', port: 22, username: 'root',
      auth_type: 'key', private_key_path: '~/.ssh/id_rsa', password: '' }
    await loadDevices()
  } catch (e) {
    alert('添加失败: ' + e.message)
  }
}

async function deleteDevice(id) {
  if (!confirm('确定删除此设备？')) return
  try {
    await del(`/devices/${id}`)
    await loadDevices()
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

function formatUptime(s) {
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const mins = Math.floor((s % 3600) / 60)
  return `${days}d ${hours}h ${mins}m`
}

onMounted(loadDevices)
</script>
