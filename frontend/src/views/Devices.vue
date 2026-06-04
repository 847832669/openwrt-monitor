<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">设备管理</h2>
        <p class="text-sm text-slate-400 mt-0.5">添加和管理 OpenWrt 路由器</p>
      </div>
      <button @click="showAdd = true"
        class="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm transition-colors">
        + 添加设备
      </button>
    </div>

    <!-- 设备列表 -->
    <div class="space-y-3">
      <div v-for="item in devices" :key="item.id"
        class="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center justify-between hover:border-slate-700 transition-colors">
        <div class="flex items-center gap-4">
          <span :class="item.online ? 'dot-online' : 'dot-offline'"></span>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-semibold text-white">{{ item.name || item.host }}</span>
              <span v-if="!item.name" class="text-xs text-slate-500">(未命名)</span>
            </div>
            <div class="text-xs text-slate-400 mt-0.5">
              {{ item.host }}:{{ item.port }}
              <span v-if="item.firmware" class="ml-2">{{ item.firmware }}</span>
              <span class="ml-2">{{ item.username }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="item.uptime > 0" class="text-xs text-slate-500">
            {{ formatUptime(item.uptime) }}
          </span>
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
        class="bg-slate-900/60 border border-dashed border-slate-700 rounded-xl p-12 text-center">
        <div class="text-4xl mb-3">📡</div>
        <p class="text-slate-400">还没有添加设备</p>
        <p class="text-xs text-slate-500 mt-1">点击上方按钮添加你的第一台 OpenWrt 路由器</p>
      </div>
    </div>

    <!-- 添加设备弹窗 -->
    <div v-if="showAdd"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div class="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-white mb-4">{{ editingDevice ? '编辑设备' : '添加设备' }}</h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-slate-400 block mb-1">名称（可选）</label>
            <input v-model="form.name"
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
              placeholder="例如：主路由" />
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
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, post, del } = useApi()
const devices = ref([])
const loading = ref(true)
const showAdd = ref(false)
const form = ref({
  name: '', host: '', port: 22, username: 'root',
  auth_type: 'key', private_key_path: '~/.ssh/id_rsa', password: '',
})
const editingDevice = ref(null)

function editDevice(item) {
  editingDevice.value = item
  form.value = {
    name: item.name || '',
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
  form.value = { name: '', host: '', port: 22, username: 'root',
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
    form.value = { name: '', host: '', port: 22, username: 'root',
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
