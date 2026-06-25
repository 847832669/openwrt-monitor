<template>
  <div class="page-container page-container-medium space-y-5">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">系统设置</h2>
        <p class="mt-1 text-sm text-slate-400">访问保护、备份恢复和历史数据维护。</p>
      </div>
      <button @click="reloadAll"
        class="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800/50 hover:text-white">
        刷新状态
      </button>
    </div>

    <div v-if="message"
      class="rounded-lg border px-3 py-2 text-sm"
      :class="messageType === 'ok'
        ? 'border-green-400/40 bg-green-900/20 text-green-200'
        : 'border-red-400/40 bg-red-900/20 text-red-300'">
      {{ message }}
    </div>

    <section class="app-panel rounded-lg p-4 sm:p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="status-pill text-xs text-cyan-300">安全状态</div>
          <h3 class="mt-3 text-lg font-semibold text-white">登录与密钥</h3>
          <p class="mt-1 text-sm text-slate-400">
            默认使用单管理员登录保护前端和 API；本地调试可通过 OWM_AUTH_DISABLED=true 关闭。
          </p>
        </div>
        <div class="grid gap-2 sm:grid-cols-3 lg:min-w-[28rem]">
          <div v-for="item in securityTiles" :key="item.label" class="app-panel-soft rounded-lg p-3">
            <div class="text-xs text-slate-500">{{ item.label }}</div>
            <div class="mt-2 flex items-center gap-2">
              <span class="inline-block h-2 w-2 rounded-full"
                :class="item.tone === 'ok' ? 'bg-green-400' : 'bg-amber-400'"></span>
              <span class="text-sm font-semibold text-white">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="security?.default_secret || security?.default_admin_password"
        class="mt-4 rounded-lg border border-amber-400/30 bg-amber-900/20 p-3 text-sm leading-6 text-amber-100">
        <p v-if="security.default_secret">检测到默认 OWM_SECRET_KEY。生产环境请配置一个足够长的随机字符串，否则 JWT 和 SSH 密码加密都使用默认密钥。</p>
        <p v-if="security.default_admin_password">检测到默认 OWM_ADMIN_PASSWORD=admin。长期运行前请修改管理员密码。</p>
      </div>
    </section>

    <div class="grid grid-cols-1 xl:grid-cols-[1fr_0.95fr] gap-5">
      <section class="app-panel rounded-lg p-4 sm:p-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="status-pill text-xs text-slate-400">备份恢复</div>
            <h3 class="mt-3 text-lg font-semibold text-white">配置导入导出</h3>
            <p class="mt-1 text-sm text-slate-400">
              导出包含设备配置、LAN 设备画像、识别规则、OUI 覆盖和告警规则。
            </p>
          </div>
        </div>

        <div class="mt-4 rounded-lg border border-amber-400/25 bg-amber-900/10 px-3 py-2 text-xs leading-5 text-amber-100">
          配置导出会包含设备 SSH 密码明文，请只保存到可信位置。
        </div>

        <div class="mt-5 grid gap-3 sm:grid-cols-2">
          <button @click="exportConfig"
            class="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-500">
            导出配置 JSON
          </button>
          <button @click="downloadDatabase"
            class="rounded-lg border border-slate-700 px-4 py-2.5 text-sm text-slate-300 transition-colors hover:bg-slate-800/50 hover:text-white">
            导出数据库备份
          </button>
        </div>

        <div class="mt-5 app-panel-soft rounded-lg p-3">
          <label class="block text-xs text-slate-400 mb-2">导入配置 JSON</label>
          <div class="flex flex-col gap-3 sm:flex-row">
            <input ref="fileInput" type="file" accept="application/json,.json" @change="onFileSelected"
              class="app-control w-full px-3 py-2 text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-slate-700 file:px-3 file:py-1.5 file:text-sm file:text-slate-100" />
            <button @click="importConfig" :disabled="!importData || busy"
              class="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-50">
              导入
            </button>
          </div>
          <p class="mt-2 text-xs text-slate-500">导入后下一轮采集会刷新设备识别结果。</p>
        </div>
      </section>

      <section class="app-panel rounded-lg p-4 sm:p-5">
        <div class="status-pill text-xs text-slate-400">数据维护</div>
        <h3 class="mt-3 text-lg font-semibold text-white">历史数据保留</h3>
        <p class="mt-1 text-sm text-slate-400">
          影响 metric_history 和 traffic_history，流量排行历史仍按约 60 秒写入。
        </p>

        <div class="mt-5 grid grid-cols-4 gap-2 app-panel-soft rounded-lg p-1">
          <button v-for="day in retentionOptions" :key="day" @click="updateRetention(day)"
            class="rounded-lg px-3 py-2 text-sm transition-colors"
            :class="maintenance.history_retention_days === day
              ? 'bg-brand-600 text-white'
              : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'">
            {{ day }} 天
          </button>
        </div>

        <button @click="cleanupHistory" :disabled="busy"
          class="mt-5 w-full rounded-lg border border-amber-400/40 bg-amber-900/10 px-4 py-2.5 text-sm font-semibold text-amber-100 transition-colors hover:border-amber-400/70 disabled:cursor-not-allowed disabled:opacity-50">
          立即清理历史数据
        </button>

        <div v-if="lastCleanup" class="mt-4 grid gap-2 text-xs text-slate-400">
          <div class="flex justify-between gap-3 rounded-lg bg-slate-900/50 px-3 py-2">
            <span>清理截止</span>
            <span class="font-mono text-slate-200">{{ formatDate(lastCleanup.cutoff) }}</span>
          </div>
          <div class="flex justify-between gap-3 rounded-lg bg-slate-900/50 px-3 py-2">
            <span>系统历史</span>
            <span class="font-mono text-slate-200">{{ lastCleanup.metric_deleted }} 条</span>
          </div>
          <div class="flex justify-between gap-3 rounded-lg bg-slate-900/50 px-3 py-2">
            <span>流量历史</span>
            <span class="font-mono text-slate-200">{{ lastCleanup.traffic_deleted }} 条</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { requestJson } from '../composables/useApi'
import { formatLocalDateTime } from '../utils/time'

const security = ref(null)
const maintenance = ref({ history_retention_days: 7 })
const retentionOptions = [3, 7, 14, 30]
const busy = ref(false)
const message = ref('')
const messageType = ref('ok')
const importData = ref(null)
const fileInput = ref(null)
const lastCleanup = ref(null)
const securityTiles = computed(() => [
  {
    label: '认证',
    value: security.value?.auth_disabled ? '已关闭' : '已启用',
    tone: security.value?.auth_disabled ? 'warn' : 'ok',
  },
  {
    label: '生产密钥',
    value: security.value?.default_secret ? '默认值' : '已修改',
    tone: security.value?.default_secret ? 'warn' : 'ok',
  },
  {
    label: '管理员密码',
    value: security.value?.default_admin_password ? '默认值' : '已修改',
    tone: security.value?.default_admin_password ? 'warn' : 'ok',
  },
])

function showMessage(text, type = 'ok') {
  message.value = text
  messageType.value = type
  setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 4000)
}

async function reloadAll() {
  try {
    const [sec, maint] = await Promise.all([
      requestJson('/settings/security'),
      requestJson('/settings/maintenance'),
    ])
    security.value = sec
    maintenance.value = {
      history_retention_days: maint.history_retention_days || 7,
    }
  } catch (e) {
    showMessage(e.message || '加载设置失败', 'error')
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function exportConfig() {
  busy.value = true
  try {
    const data = await requestJson('/settings/export')
    const filename = `openwrt-monitor-config-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`
    downloadBlob(
      new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
      filename,
    )
    showMessage('配置已导出')
  } catch (e) {
    showMessage(e.message || '导出失败', 'error')
  } finally {
    busy.value = false
  }
}

function downloadDatabase() {
  window.location.href = '/api/settings/backup/database'
}

async function onFileSelected(event) {
  importData.value = null
  const file = event.target.files?.[0]
  if (!file) return
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    if (data?.version !== 1) {
      throw new Error('不支持的配置版本')
    }
    importData.value = data
    showMessage('配置文件已读取，确认后可导入')
  } catch (e) {
    showMessage(e.message || '读取配置失败', 'error')
  }
}

async function importConfig() {
  if (!importData.value) return
  if (!confirm('导入会覆盖相同设备和画像配置，确认继续？')) return
  busy.value = true
  try {
    const result = await requestJson('/settings/import', {
      method: 'POST',
      body: { data: importData.value },
    })
    importData.value = null
    if (fileInput.value) fileInput.value.value = ''
    await reloadAll()
    showMessage(result.message || '配置已导入')
  } catch (e) {
    showMessage(e.message || '导入失败', 'error')
  } finally {
    busy.value = false
  }
}

async function updateRetention(days) {
  busy.value = true
  try {
    const result = await requestJson('/settings/maintenance/retention', {
      method: 'PATCH',
      body: { days },
    })
    maintenance.value.history_retention_days = result.history_retention_days
    showMessage(`历史数据保留已设置为 ${days} 天`)
  } catch (e) {
    showMessage(e.message || '保存失败', 'error')
  } finally {
    busy.value = false
  }
}

async function cleanupHistory() {
  if (!confirm('确定立即清理超过保留天数的历史数据？')) return
  busy.value = true
  try {
    lastCleanup.value = await requestJson('/settings/maintenance/cleanup', { method: 'POST' })
    showMessage('历史数据清理完成')
  } catch (e) {
    showMessage(e.message || '清理失败', 'error')
  } finally {
    busy.value = false
  }
}

function formatDate(value) {
  return formatLocalDateTime(value)
}

onMounted(reloadAll)
</script>
