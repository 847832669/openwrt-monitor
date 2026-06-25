<template>
  <div class="page-container page-container-wide space-y-4">
    <div class="flex flex-col xl:flex-row xl:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-white">连接设备</h2>
        <p class="text-sm text-slate-400 mt-0.5">
          在线 <span class="text-green-400 font-bold">{{ onlineCount }}</span>
          · 总计 <span class="text-white font-bold">{{ totalCount }}</span>
          · 重要 <span class="text-amber-400 font-bold">{{ importantCount }}</span>
        </p>
      </div>
      <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:flex xl:flex-wrap xl:items-center xl:justify-end">
        <input v-model="filterText" placeholder="搜索名称 / 厂商 / IP / MAC"
          class="app-control px-3 text-sm text-slate-200 w-full sm:w-64 placeholder-slate-500" />
        <select v-model="selectedDevice"
          class="app-control px-3 text-sm text-slate-200 w-full sm:w-64">
          <option value="">选择设备…</option>
          <option v-for="d in devices" :key="d.id" :value="d.id">{{ deviceOptionLabel(d) }}</option>
        </select>
      </div>
    </div>

    <div class="flex gap-2 overflow-x-auto">
      <button v-for="f in filters" :key="f.key"
        @click="activeFilter = f.key"
        class="text-sm px-3 py-1.5 rounded-lg transition-colors shrink-0"
        :class="activeFilter === f.key
          ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
          : 'text-slate-400 hover:text-slate-200 bg-slate-800/50 border border-slate-800'">
        {{ f.label }}
      </button>
      <button @click="showRecognitionPanel = !showRecognitionPanel"
        class="text-sm px-3 py-1.5 rounded-lg transition-colors shrink-0 border"
        :class="showRecognitionPanel
          ? 'bg-cyan-400/10 text-cyan-300 border-cyan-400/30'
          : 'text-slate-400 hover:text-slate-200 bg-slate-800/50 border-slate-800'">
        识别增强
      </button>
    </div>

    <section v-if="showRecognitionPanel" class="app-panel rounded-lg p-4">
      <div class="grid grid-cols-1 xl:grid-cols-[1.25fr_0.75fr] gap-4">
        <div>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-3">
            <div>
              <h3 class="text-sm font-semibold text-slate-300">自定义识别规则</h3>
              <p class="text-xs text-slate-500 mt-0.5">按主机名、MAC/OUI 前缀、厂商或 IP 命中后自动建议厂商、类型和图标</p>
            </div>
            <button @click="resetRuleForm"
              class="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">
              新建规则
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2 mb-3">
            <input v-model="ruleForm.name" class="app-control px-3 text-sm text-white" placeholder="规则名称" />
            <select v-model="ruleForm.match_type" class="app-control px-3 text-sm text-slate-200">
              <option value="hostname">主机名</option>
              <option value="mac_prefix">MAC/OUI</option>
              <option value="vendor">厂商</option>
              <option value="ip">IP</option>
            </select>
            <input v-model="ruleForm.pattern" class="app-control px-3 text-sm text-white" placeholder="匹配内容，如 iphone 或 001122" />
            <input v-model.number="ruleForm.priority" type="number" min="0" max="999" class="app-control px-3 text-sm text-white" placeholder="优先级" />
            <input v-model="ruleForm.vendor" class="app-control px-3 text-sm text-white" placeholder="厂商建议" />
            <select v-model="ruleForm.device_type" class="app-control px-3 text-sm text-slate-200">
              <option value="">类型建议</option>
              <option value="phone">手机</option>
              <option value="computer">电脑</option>
              <option value="storage">存储</option>
              <option value="printer">打印机</option>
              <option value="camera">摄像头</option>
              <option value="media">影音</option>
              <option value="home">智能家居</option>
            </select>
            <select v-model="ruleForm.icon" class="app-control px-3 text-sm text-slate-200">
              <option value="">图标建议</option>
              <option v-for="item in LAN_DEVICE_ICONS" :key="item.key" :value="item.key">{{ item.label }}</option>
            </select>
            <label class="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/40 px-3 text-sm text-slate-300">
              <input v-model="ruleForm.enabled" type="checkbox" class="accent-brand-600" />
              启用
            </label>
          </div>

          <div class="flex flex-wrap gap-2 mb-3">
            <button @click="saveRule"
              class="rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-white hover:bg-brand-500 transition-colors">
              {{ ruleForm.id ? '保存规则' : '添加规则' }}
            </button>
            <button v-if="ruleForm.id" @click="deleteRule(ruleForm.id)"
              class="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-200 hover:bg-red-500/20 transition-colors">
              删除规则
            </button>
            <span v-if="ruleMessage" class="self-center text-xs text-slate-400">{{ ruleMessage }}</span>
          </div>

          <div class="overflow-x-auto rounded-lg border border-slate-800">
            <table class="min-w-[48rem] w-full text-xs">
              <thead class="bg-slate-900/60 text-slate-500">
                <tr>
                  <th class="px-3 py-2 text-left">规则</th>
                  <th class="px-3 py-2 text-left">匹配</th>
                  <th class="px-3 py-2 text-left">建议</th>
                  <th class="px-3 py-2 text-left">状态</th>
                  <th class="px-3 py-2 text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800">
                <tr v-for="rule in recognitionRules" :key="rule.id" class="hover:bg-slate-800/30">
                  <td class="px-3 py-2 text-slate-200">{{ rule.name || '未命名规则' }}</td>
                  <td class="px-3 py-2 text-slate-400">{{ matchTypeLabel(rule.match_type) }} · {{ rule.pattern }}</td>
                  <td class="px-3 py-2 text-slate-400">{{ [rule.vendor, iconLabel(rule.icon), rule.device_type].filter(Boolean).join(' / ') || '-' }}</td>
                  <td class="px-3 py-2" :class="rule.enabled ? 'text-green-300' : 'text-slate-500'">{{ rule.enabled ? '启用' : '停用' }}</td>
                  <td class="px-3 py-2 text-right">
                    <button @click="editRule(rule)" class="text-brand-300 hover:text-brand-200">编辑</button>
                  </td>
                </tr>
                <tr v-if="!recognitionRules.length">
                  <td colspan="5" class="px-3 py-6 text-center text-slate-500">暂无自定义识别规则</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="space-y-3">
          <div>
            <h3 class="text-sm font-semibold text-slate-300">OUI 数据导入</h3>
            <p class="text-xs text-slate-500 mt-0.5">支持每行 “001122 厂商” 或 “00:11:22,厂商”</p>
          </div>
          <textarea v-model="ouiImportText"
            class="app-control w-full min-h-40 px-3 py-2 text-sm text-white"
            placeholder="例如：&#10;AABBCC 小米&#10;00:11:22,Apple"></textarea>
          <div class="flex flex-wrap items-center gap-2">
            <input v-model="ouiSource" class="app-control px-3 text-sm text-white flex-1 min-w-0" placeholder="来源标签" />
            <button @click="importOui"
              class="rounded-lg bg-cyan-500/90 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-400 transition-colors">
              导入
            </button>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
            已导入 <span class="numeric-value text-white">{{ ouiOverrides.length }}</span> 条 OUI 覆盖
            <span v-if="ouiMessage" class="block mt-1 text-cyan-300">{{ ouiMessage }}</span>
          </div>
        </div>
      </div>
    </section>

    <div v-if="!selectedDevice" class="app-panel-soft border-dashed rounded-lg p-12 text-center">
      <div class="text-5xl mb-4">▣</div>
      <p class="text-slate-400">请先选择上面的设备</p>
    </div>

    <div v-else-if="filteredLeases.length === 0" class="app-panel-soft border-dashed rounded-lg p-12 text-center">
      <div class="text-4xl mb-3">◇</div>
      <p class="text-slate-400">暂无匹配设备</p>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-[1fr_22rem] gap-4">
      <section class="app-panel rounded-lg overflow-hidden">
        <div class="hidden lg:grid grid-cols-[4rem_1.7fr_1fr_1fr_1.2fr_7rem] gap-3 px-4 py-3 text-xs uppercase text-slate-500 border-b border-slate-800">
          <span>状态</span>
          <span>设备</span>
          <span>厂商</span>
          <span>IP</span>
          <span>MAC</span>
          <span class="text-right">操作</span>
        </div>

        <div class="divide-y divide-slate-800/50">
          <div v-for="lease in filteredLeases" :key="lease.mac || lease.ip"
            class="grid grid-cols-1 lg:grid-cols-[4rem_1.7fr_1fr_1fr_1.2fr_7rem] gap-3 px-4 py-3 hover:bg-slate-800/40 transition-colors"
            :class="{ 'opacity-55': !lease.online }">
            <div class="flex lg:block items-center justify-between">
              <span class="inline-flex items-center gap-1.5">
                <span :class="lease.online ? 'dot-online' : 'dot-offline'"></span>
                <span class="text-xs" :class="lease.online ? 'text-green-400' : 'text-slate-500'">
                  {{ lease.online ? '在线' : '离线' }}
                </span>
              </span>
              <span v-if="lease.important" class="lg:hidden status-pill text-xs text-amber-300">重要</span>
            </div>

            <div class="min-w-0 flex items-center gap-3">
              <span class="relative grid place-items-center w-10 h-10 rounded-lg bg-slate-800/60 border border-slate-700/60 text-lg shrink-0">
                <span v-if="lanIconInfo(lease).type === 'image'" class="lan-icon-plate w-8 h-8 rounded-md">
                  <img
                    :src="lanIconInfo(lease).src"
                    :alt="lanIconInfo(lease).label"
                    class="max-w-6 max-h-6" />
                </span>
                <span v-else>{{ lanIconInfo(lease).icon }}</span>
                <span v-if="lease.important"
                  class="absolute -right-1 -top-1 grid place-items-center w-4 h-4 rounded-full bg-amber-400 text-slate-950 text-[10px] font-bold">!</span>
              </span>
              <div class="min-w-0">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-white font-semibold truncate">{{ getLanDeviceDisplayName(lease) }}</span>
                  <span v-if="lease.custom_name" class="hidden sm:inline text-[11px] text-brand-300">固定</span>
                </div>
                <div class="mt-0.5 text-xs text-slate-500 truncate">
                  {{ lease.hostname || '无 DHCP 主机名' }}
                  <span v-if="lease.note" class="ml-2 text-slate-400">{{ lease.note }}</span>
                </div>
              </div>
            </div>

            <div class="flex lg:block items-center justify-between gap-3">
              <span class="lg:hidden text-xs text-slate-500">厂商</span>
              <div>
                <div class="text-sm text-slate-200 truncate">{{ lease.vendor || '未知厂商' }}</div>
                <div v-if="lease.mac_is_randomized" class="text-[11px] text-amber-400">随机 MAC</div>
              </div>
            </div>

            <div class="flex lg:block items-center justify-between gap-3">
              <span class="lg:hidden text-xs text-slate-500">IP</span>
              <span class="font-mono text-sm text-slate-300">{{ lease.ip }}</span>
            </div>

            <div class="flex lg:block items-center justify-between gap-3">
              <span class="lg:hidden text-xs text-slate-500">MAC</span>
              <div class="min-w-0">
                <div class="font-mono text-xs text-slate-400 truncate">{{ lease.mac }}</div>
                <div class="text-[11px] text-slate-600 truncate">{{ lease.remain || '-' }}</div>
              </div>
            </div>

            <div class="flex items-center lg:justify-end gap-2">
              <button @click="editLease(lease)"
                class="px-2.5 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors">
                编辑
              </button>
            </div>
          </div>
        </div>
      </section>

      <aside class="space-y-4">
        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">厂商分布</h3>
          <div class="space-y-2">
            <div v-for="item in vendorRows" :key="item.name">
              <div class="flex items-center justify-between text-xs mb-1">
                <span class="text-slate-400 truncate">{{ item.name }}</span>
                <span class="numeric-value text-slate-300">{{ item.count }}</span>
              </div>
              <div class="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-cyan-400" :style="{ width: item.width }"></div>
              </div>
            </div>
            <div v-if="!vendorRows.length" class="text-xs text-slate-500">暂无厂商数据</div>
          </div>
        </section>

        <section class="app-panel rounded-lg p-4">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">重要设备</h3>
          <div v-if="importantLeases.length" class="space-y-2">
            <button v-for="lease in importantLeases" :key="lease.mac"
              @click="editLease(lease)"
              class="w-full flex items-center gap-3 rounded-lg border border-slate-800 px-3 py-2 text-left hover:border-amber-400/40 transition-colors">
              <span class="grid place-items-center w-8 h-8 rounded-lg bg-amber-400/10 text-amber-300">
                <span v-if="lanIconInfo(lease).type === 'image'" class="lan-icon-plate w-7 h-7 rounded-md">
                  <img
                    :src="lanIconInfo(lease).src"
                    :alt="lanIconInfo(lease).label"
                    class="max-w-5 max-h-5" />
                </span>
                <span v-else>{{ lanIconInfo(lease).icon }}</span>
              </span>
              <span class="min-w-0">
                <span class="block text-sm text-white truncate">{{ getLanDeviceDisplayName(lease) }}</span>
                <span class="block text-xs text-slate-500 truncate">{{ lease.ip }} · {{ lease.vendor }}</span>
              </span>
            </button>
          </div>
          <div v-else class="text-xs text-slate-500">还没有标记重要设备</div>
        </section>
      </aside>
    </div>

    <div v-if="editingLease" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-3">
      <div class="app-panel rounded-lg p-4 sm:p-6 w-full max-w-2xl max-h-[90dvh] overflow-y-auto">
        <div class="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 class="text-lg font-semibold text-white">编辑终端设备</h3>
            <p class="text-xs text-slate-500 mt-1 font-mono">{{ editingLease.mac }} · {{ editingLease.ip }}</p>
          </div>
          <button @click="editingLease = null" class="text-slate-500 hover:text-white">✕</button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="text-xs text-slate-400 block mb-1">固定名称</label>
            <input v-model="profileForm.name"
              class="app-control w-full px-3 text-sm text-white"
              :placeholder="editingLease.hostname || editingLease.ip" />
          </div>

          <div>
            <label class="text-xs text-slate-400 block mb-2">设备图标</label>
            <div class="space-y-2 mb-2">
              <input v-model="iconFilterText"
                class="app-control w-full px-3 text-sm text-white"
                placeholder="搜索品牌 / 类型图标" />
              <div class="flex gap-2 overflow-x-auto pb-1">
                <button v-for="group in iconGroupOptions" :key="group.key" type="button"
                  @click="activeIconGroup = group.key"
                  class="shrink-0 rounded-lg border px-3 py-2 text-xs transition-colors"
                  :class="activeIconGroup === group.key
                    ? 'border-brand-600 bg-brand-600/20 text-brand-200'
                    : 'border-slate-700 bg-slate-800/40 text-slate-400 hover:text-slate-200 hover:border-slate-600'">
                  {{ group.label }}
                </button>
              </div>
            </div>
            <div class="grid grid-cols-3 sm:grid-cols-6 gap-2 max-h-72 overflow-y-auto pr-1">
              <button v-for="item in filteredLanIcons" :key="item.key" type="button"
                @click="selectBuiltinIcon(item.key)"
                class="rounded-lg border px-2 py-2 text-center transition-colors"
                :class="profileForm.icon === item.key && !profileForm.custom_icon
                  ? 'border-brand-600 bg-brand-600/20 text-white'
                  : 'border-slate-700 bg-slate-800/40 text-slate-400 hover:text-slate-200 hover:border-slate-600'">
                <span class="grid place-items-center h-7 leading-none">
                  <span v-if="item.type === 'image'" class="lan-icon-plate w-7 h-7 rounded-md">
                    <img
                      :src="item.src"
                      :alt="item.label"
                      class="max-w-5 max-h-5" />
                  </span>
                  <span v-else class="text-xl">{{ item.icon }}</span>
                </span>
                <span class="mt-1 block text-[10px] truncate">{{ item.label }}</span>
              </button>
              <div v-if="!filteredLanIcons.length"
                class="col-span-3 sm:col-span-6 rounded-lg border border-dashed border-slate-700 py-6 text-center text-xs text-slate-500">
                没有匹配的图标
              </div>
            </div>

            <div class="mt-3 rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-3">
              <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                <div class="grid place-items-center w-12 h-12 rounded-lg bg-slate-800/70 border border-slate-700 shrink-0">
                  <span v-if="profileForm.custom_icon" class="lan-icon-plate w-10 h-10 rounded-lg">
                    <img
                      :src="profileForm.custom_icon"
                      alt="自定义图标预览"
                      class="max-w-8 max-h-8" />
                  </span>
                  <span v-else class="text-xl text-slate-500">+</span>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-sm text-slate-200">自定义上传</div>
                  <div class="text-xs text-slate-500 mt-0.5">支持 SVG、PNG、JPG、WebP，最大 512 KB</div>
                  <div v-if="uploadError" class="text-xs text-red-300 mt-1">{{ uploadError }}</div>
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" @click="openIconPicker"
                    class="px-3 py-2 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">
                    选择文件
                  </button>
                  <button v-if="profileForm.custom_icon" type="button" @click="clearCustomIcon"
                    class="px-3 py-2 rounded-lg border border-slate-700 text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
                    移除
                  </button>
                </div>
              </div>
              <input ref="fileInput" type="file"
                class="hidden"
                accept="image/svg+xml,image/png,image/jpeg,image/jpg,image/webp"
                @change="handleIconUpload" />
            </div>
          </div>

          <label class="flex items-center justify-between gap-3 rounded-lg border border-slate-800 px-3 py-3">
            <span>
              <span class="block text-sm text-slate-200">重要设备</span>
              <span class="block text-xs text-slate-500">在列表和侧栏中突出显示</span>
            </span>
            <input v-model="profileForm.important" type="checkbox"
              class="w-5 h-5 accent-brand-600" />
          </label>

          <div>
            <label class="text-xs text-slate-400 block mb-1">备注</label>
            <input v-model="profileForm.note"
              class="app-control w-full px-3 text-sm text-white"
              placeholder="例如：客厅电视、NAS、父母手机" />
          </div>

          <div class="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-3 text-xs text-slate-400">
            <div>厂商：<span class="text-slate-200">{{ editingLease.vendor || '未知厂商' }}</span></div>
            <div class="mt-1">OUI：<span class="font-mono text-slate-300">{{ editingLease.oui || '-' }}</span></div>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-6">
          <button @click="editingLease = null"
            class="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">取消</button>
          <button @click="saveProfile"
            class="bg-brand-600 hover:bg-brand-500 text-white px-6 py-2 rounded-lg text-sm transition-colors">
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'
import { getDeviceDisplayName, getDeviceIcon } from '../utils/deviceDisplay'
import {
  getLanDeviceDisplayName,
  getLanDeviceIconInfo,
  getLanDeviceIconLabel,
  LAN_DEVICE_ICONS,
  LAN_ICON_GROUPS,
} from '../utils/lanDeviceDisplay'

const { get } = useApi()
const { metrics: wsMetrics } = useWebSocket()

const devices = ref([])
const selectedDevice = ref('')
const latestSnapshot = ref(null)
const filterText = ref('')
const activeFilter = ref('all')
const editingLease = ref(null)
const profileForm = ref({ name: '', icon: 'device', custom_icon: '', important: false, note: '' })
const fileInput = ref(null)
const uploadError = ref('')
const iconFilterText = ref('')
const activeIconGroup = ref('all')
const showRecognitionPanel = ref(false)
const recognitionRules = ref([])
const ouiOverrides = ref([])
const ouiImportText = ref('')
const ouiSource = ref('manual')
const ruleMessage = ref('')
const ouiMessage = ref('')
const emptyRuleForm = () => ({
  id: null,
  name: '',
  match_type: 'hostname',
  pattern: '',
  vendor: '',
  icon: '',
  device_type: '',
  priority: 50,
  enabled: true,
})
const ruleForm = ref(emptyRuleForm())

const MAX_ICON_SIZE = 512 * 1024
const ALLOWED_ICON_TYPES = new Set(['image/svg+xml', 'image/png', 'image/jpeg', 'image/jpg', 'image/webp'])
const ALLOWED_ICON_EXTS = ['.svg', '.png', '.jpg', '.jpeg', '.webp']

const filters = [
  { key: 'all', label: '全部' },
  { key: 'important', label: '重要' },
  { key: 'online', label: '在线' },
  { key: 'offline', label: '离线' },
  { key: 'randomized', label: '随机 MAC' },
]
const iconGroupOptions = [{ key: 'all', label: '全部' }, ...LAN_ICON_GROUPS]

function deviceOptionLabel(device) {
  return `${getDeviceIcon(device)} ${getDeviceDisplayName(device)}`
}

function lanIconInfo(device) {
  return getLanDeviceIconInfo(device)
}

function iconLabel(icon) {
  return icon ? getLanDeviceIconLabel(icon) : ''
}

function matchTypeLabel(type) {
  return {
    hostname: '主机名',
    mac_prefix: 'MAC/OUI',
    vendor: '厂商',
    ip: 'IP',
  }[type] || type
}

const currentMetrics = computed(() => {
  if (!selectedDevice.value) return null
  return wsMetrics.value[selectedDevice.value] || latestSnapshot.value?.data || null
})

const lanData = computed(() => currentMetrics.value?.lan || {})
const leases = computed(() => lanData.value?.leases ?? [])
const onlineCount = computed(() => lanData.value?.online_count ?? 0)
const totalCount = computed(() => lanData.value?.total_count ?? 0)
const importantCount = computed(() => leases.value.filter(item => item.important).length)

const filteredLeases = computed(() => {
  let list = leases.value.slice()
  if (activeFilter.value === 'important') list = list.filter(item => item.important)
  else if (activeFilter.value === 'online') list = list.filter(item => item.online)
  else if (activeFilter.value === 'offline') list = list.filter(item => !item.online)
  else if (activeFilter.value === 'randomized') list = list.filter(item => item.mac_is_randomized)

  const q = filterText.value.trim().toLowerCase()
  if (q) {
    list = list.filter((item) => [
      item.ip,
      item.mac,
      item.hostname,
      item.display_name,
      item.custom_name,
      item.vendor,
      item.note,
    ].some(value => String(value || '').toLowerCase().includes(q)))
  }

  return list.sort((a, b) => Number(b.important) - Number(a.important)
    || Number(b.online) - Number(a.online)
    || getLanDeviceDisplayName(a).localeCompare(getLanDeviceDisplayName(b), 'zh-CN'))
})

const importantLeases = computed(() => leases.value
  .filter(item => item.important)
  .sort((a, b) => Number(b.online) - Number(a.online))
  .slice(0, 8))

const vendorRows = computed(() => {
  const counts = new Map()
  for (const lease of leases.value) {
    const name = lease.vendor || '未知厂商'
    counts.set(name, (counts.get(name) || 0) + 1)
  }
  const rows = Array.from(counts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8)
  const max = Math.max(...rows.map(item => item.count), 1)
  return rows.map(item => ({
    ...item,
    width: `${Math.max(item.count / max * 100, 6)}%`,
  }))
})

const filteredLanIcons = computed(() => {
  const q = iconFilterText.value.trim().toLowerCase()
  return LAN_DEVICE_ICONS.filter((item) => {
    const matchesGroup = activeIconGroup.value === 'all' || item.group === activeIconGroup.value
    const matchesText = !q || [
      item.key,
      item.label,
      item.group,
    ].some(value => String(value || '').toLowerCase().includes(q))
    return matchesGroup && matchesText
  })
})

async function loadLatestSnapshot() {
  if (!selectedDevice.value) return
  try {
    latestSnapshot.value = await get(`/metrics/latest/${selectedDevice.value}`)
  } catch (e) {
    latestSnapshot.value = null
  }
}

async function loadRecognitionConfig() {
  try {
    const [rules, oui] = await Promise.all([
      get('/lan/recognition/rules'),
      get('/lan/recognition/oui'),
    ])
    recognitionRules.value = rules || []
    ouiOverrides.value = oui || []
  } catch (e) {
    recognitionRules.value = []
    ouiOverrides.value = []
  }
}

function resetRuleForm() {
  ruleForm.value = emptyRuleForm()
  ruleMessage.value = ''
}

function editRule(rule) {
  ruleForm.value = {
    id: rule.id,
    name: rule.name || '',
    match_type: rule.match_type || 'hostname',
    pattern: rule.pattern || '',
    vendor: rule.vendor || '',
    icon: rule.icon || '',
    device_type: rule.device_type || '',
    priority: rule.priority ?? 50,
    enabled: Boolean(rule.enabled),
  }
  ruleMessage.value = ''
}

async function saveRule() {
  if (!ruleForm.value.pattern.trim()) {
    ruleMessage.value = '请填写匹配内容'
    return
  }
  const payload = { ...ruleForm.value }
  const url = payload.id ? `/api/lan/recognition/rules/${payload.id}` : '/api/lan/recognition/rules'
  const method = payload.id ? 'PATCH' : 'POST'
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    ruleMessage.value = await res.text()
    return
  }
  ruleMessage.value = '规则已保存，下一轮采集后生效'
  resetRuleForm()
  await loadRecognitionConfig()
}

async function deleteRule(id) {
  const res = await fetch(`/api/lan/recognition/rules/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    ruleMessage.value = '删除失败'
    return
  }
  ruleMessage.value = '规则已删除'
  resetRuleForm()
  await loadRecognitionConfig()
}

async function importOui() {
  if (!ouiImportText.value.trim()) {
    ouiMessage.value = '请先粘贴 OUI 数据'
    return
  }
  const res = await fetch('/api/lan/recognition/oui/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: ouiImportText.value, source: ouiSource.value || 'manual' }),
  })
  if (!res.ok) {
    ouiMessage.value = await res.text()
    return
  }
  const data = await res.json()
  ouiMessage.value = `已导入 ${data.imported || 0} 条，下一轮采集后生效`
  ouiImportText.value = ''
  await loadRecognitionConfig()
}

function editLease(lease) {
  editingLease.value = lease
  uploadError.value = ''
  iconFilterText.value = ''
  activeIconGroup.value = 'all'
  profileForm.value = {
    name: lease.custom_name || '',
    icon: lease.icon || 'device',
    custom_icon: lease.custom_icon || '',
    important: Boolean(lease.important),
    note: lease.note || '',
  }
}

function selectBuiltinIcon(key) {
  profileForm.value.icon = key
  profileForm.value.custom_icon = ''
  uploadError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function openIconPicker() {
  uploadError.value = ''
  fileInput.value?.click()
}

function clearCustomIcon() {
  profileForm.value.custom_icon = ''
  profileForm.value.icon = profileForm.value.icon === 'custom'
    ? (editingLease.value?.suggested_icon || 'device')
    : profileForm.value.icon
  uploadError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function handleIconUpload(event) {
  const file = event.target.files?.[0]
  uploadError.value = ''
  if (!file) return

  const lowerName = file.name.toLowerCase()
  const typeOk = ALLOWED_ICON_TYPES.has(file.type)
    || ALLOWED_ICON_EXTS.some(ext => lowerName.endsWith(ext))
  if (!typeOk) {
    uploadError.value = '仅支持 SVG、PNG、JPG 或 WebP 图标'
    event.target.value = ''
    return
  }
  if (file.size > MAX_ICON_SIZE) {
    uploadError.value = '图标不能超过 512 KB'
    event.target.value = ''
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    profileForm.value.custom_icon = String(reader.result || '')
    profileForm.value.icon = 'custom'
  }
  reader.onerror = () => {
    uploadError.value = '读取图标失败'
  }
  reader.readAsDataURL(file)
}

async function saveProfile() {
  if (!editingLease.value?.mac) return
  const res = await fetch(`/api/lan/profiles/${encodeURIComponent(editingLease.value.mac)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profileForm.value),
  })
  if (!res.ok) {
    alert('保存失败')
    return
  }
  const profile = await res.json()
  applyProfileToLocal(profile)
  editingLease.value = null
}

function patchLeaseProfile(lease, profile) {
  if (!lease || lease.mac !== profile.mac) return
  lease.custom_name = profile.name || ''
  lease.display_name = profile.name || lease.hostname || lease.ip || '未知设备'
  lease.icon = profile.icon || lease.suggested_icon || 'device'
  lease.custom_icon = profile.custom_icon || ''
  lease.important = Boolean(profile.important)
  lease.note = profile.note || ''
}

function applyProfileToLocal(profile) {
  const live = wsMetrics.value[selectedDevice.value]
  for (const source of [latestSnapshot.value?.data, live]) {
    for (const lease of source?.lan?.leases || []) {
      patchLeaseProfile(lease, profile)
    }
  }
}

onMounted(async () => {
  try {
    devices.value = await get('/devices')
    await loadRecognitionConfig()
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].id
      await loadLatestSnapshot()
    }
  } catch (e) { /* ignore */ }
})

watch(selectedDevice, async (value, oldValue) => {
  if (!value || value === oldValue) return
  latestSnapshot.value = null
  await loadLatestSnapshot()
})
</script>
