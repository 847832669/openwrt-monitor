<template>
  <div class="page-container page-container-medium">
    <div class="grid grid-cols-1 xl:grid-cols-[0.9fr_1.1fr] gap-5 items-stretch">
      <section class="app-panel rounded-lg p-5 lg:p-6 overflow-hidden relative min-h-[30rem]">
        <div class="absolute inset-0 setup-grid opacity-45"></div>
        <div class="relative z-10 flex flex-col h-full">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="status-pill text-xs text-cyan-400">
                <span class="dot-online"></span>
                初始化向导
              </div>
              <h2 class="mt-4 text-2xl lg:text-3xl font-bold text-white">接入你的 OpenWrt</h2>
              <p class="mt-2 text-sm text-slate-400 max-w-md">
                通过 SSH 验证连接，识别系统信息，然后把设备加入实时监控。
              </p>
            </div>
            <router-link to="/devices"
              class="hidden sm:inline-flex items-center px-3 py-2 rounded-lg border border-slate-700 text-sm text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors">
              设备列表
            </router-link>
          </div>

          <div class="flex-1 grid place-items-center py-8">
            <div class="setup-radar">
              <div class="setup-ring ring-a"></div>
              <div class="setup-ring ring-b"></div>
              <div class="setup-ring ring-c"></div>
              <div class="setup-sweep"></div>
              <div class="setup-core">
                <span>SSH</span>
              </div>
              <div class="setup-node node-a">
                <span></span>
              </div>
              <div class="setup-node node-b">
                <span></span>
              </div>
              <div class="setup-node node-c">
                <span></span>
              </div>
            </div>
          </div>

          <div class="relative z-10 grid grid-cols-3 gap-2">
            <div v-for="item in steps" :key="item.id" class="app-panel-soft rounded-lg px-3 py-2">
              <div class="text-[11px] text-slate-500">{{ item.id }}</div>
              <div class="mt-1 text-sm font-semibold"
                :class="step >= item.id ? 'text-white' : 'text-slate-500'">
                {{ item.label }}
              </div>
              <div class="mt-2 h-1 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :class="step >= item.id ? 'bg-cyan-400' : 'bg-slate-700'"
                  :style="{ width: step >= item.id ? '100%' : '18%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="app-panel rounded-lg p-5 lg:p-6">
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h3 class="text-lg font-semibold text-white">{{ currentTitle }}</h3>
            <p class="text-sm text-slate-400 mt-1">{{ currentSubtitle }}</p>
          </div>
          <span class="status-pill text-xs text-slate-400">{{ step }} / 3</span>
        </div>

        <Transition name="wizard-slide" mode="out-in">
          <div v-if="step === 1" key="connect" class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="space-y-1.5">
                <span class="text-xs text-slate-400">设备别名</span>
                <input v-model="form.name" class="app-control w-full px-3 text-sm text-white"
                  placeholder="主路由" />
              </label>
              <label class="space-y-1.5">
                <span class="text-xs text-slate-400">OpenWrt IP</span>
                <input v-model="form.host" class="app-control w-full px-3 text-sm text-white font-mono"
                  placeholder="192.168.0.1" />
              </label>
            </div>

            <div>
              <div class="text-xs text-slate-400 mb-2">设备图标</div>
              <div class="grid grid-cols-4 sm:grid-cols-8 gap-2">
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

            <div class="grid grid-cols-2 gap-3">
              <label class="space-y-1.5">
                <span class="text-xs text-slate-400">SSH 端口</span>
                <input v-model.number="form.port" type="number" min="1" max="65535"
                  class="app-control w-full px-3 text-sm text-white font-mono" />
              </label>
              <label class="space-y-1.5">
                <span class="text-xs text-slate-400">用户名</span>
                <input v-model="form.username" class="app-control w-full px-3 text-sm text-white font-mono" />
              </label>
            </div>

            <div class="grid grid-cols-2 gap-2 app-panel-soft rounded-lg p-1">
              <button v-for="item in authOptions" :key="item.value" @click="form.auth_type = item.value"
                class="rounded-lg px-3 py-2 text-sm transition-colors"
                :class="form.auth_type === item.value
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'">
                {{ item.label }}
              </button>
            </div>

            <label v-if="form.auth_type === 'password'" class="space-y-1.5 block">
              <span class="text-xs text-slate-400">SSH 密码</span>
              <input v-model="form.password" type="password" class="app-control w-full px-3 text-sm text-white"
                placeholder="输入路由器 root 密码" />
            </label>

            <label v-else class="space-y-1.5 block">
              <span class="text-xs text-slate-400">私钥路径</span>
              <input v-model="form.private_key_path" class="app-control w-full px-3 text-sm text-white font-mono"
                placeholder="~/.ssh/id_rsa" />
            </label>

            <div v-if="errorText" class="rounded-lg border border-red-400/40 bg-red-900/20 px-3 py-2 text-sm text-red-300">
              {{ errorText }}
            </div>

            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
              <p class="text-xs text-slate-500">
                连接测试只读取基础信息，不会修改路由器配置。
              </p>
              <button @click="testConnection" :disabled="!canTest || testing"
                class="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg text-sm transition-colors">
                {{ testing ? '测试中…' : '测试连接' }}
              </button>
            </div>
          </div>

          <div v-else-if="step === 2" key="result" class="space-y-4">
            <div class="app-panel-soft rounded-lg p-4 border-cyan-400/30">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <div class="text-xs text-cyan-400">连接成功</div>
                  <h4 class="mt-1 text-xl font-semibold text-white">{{ detail.hostname || form.host }}</h4>
                </div>
                <span class="status-pill text-xs text-green-400">
                  <span class="dot-online"></span>
                  已识别
                </span>
              </div>
              <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                <InfoTile label="型号" :value="detail.model || '-'" />
                <InfoTile label="固件" :value="detail.firmware || '-'" />
                <InfoTile label="内核" :value="detail.kernel || '-'" />
                <InfoTile label="架构" :value="detail.arch || '-'" />
                <InfoTile label="运行时间" :value="formatUptime(detail.uptime_seconds)" />
                <InfoTile label="软件包" :value="detail.package_count ? `${detail.package_count} 个` : '-'" />
              </div>
            </div>

            <div class="app-panel-soft rounded-lg p-4">
              <div class="text-xs text-slate-500 mb-3">IPv4 接口</div>
              <div v-if="detail.interfaces?.length" class="space-y-2">
                <div v-for="iface in detail.interfaces" :key="iface.name + iface.address"
                  class="flex items-center justify-between gap-3 rounded-lg bg-slate-800/40 px-3 py-2">
                  <span class="text-sm text-slate-300">{{ iface.name }}</span>
                  <span class="text-sm font-mono text-white">{{ iface.address }}/{{ iface.prefix }}</span>
                </div>
              </div>
              <div v-else class="text-sm text-slate-500">没有读取到接口地址</div>
            </div>

            <div class="flex flex-col sm:flex-row sm:justify-between gap-2">
              <button @click="step = 1"
                class="px-4 py-2 rounded-lg border border-slate-700 text-sm text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors">
                返回修改
              </button>
              <button @click="saveDevice" :disabled="saving"
                class="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm transition-colors">
                {{ saving ? '保存中…' : '保存并进入详情' }}
              </button>
            </div>
          </div>

          <div v-else key="done" class="space-y-4">
            <div class="app-panel-soft rounded-lg p-6 text-center">
              <div class="mx-auto grid place-items-center w-14 h-14 rounded-lg bg-green-400/15 text-green-400 text-3xl">
                ✓
              </div>
              <h4 class="mt-4 text-xl font-semibold text-white">设备已加入监控</h4>
              <p class="mt-2 text-sm text-slate-400">正在跳转到设备详情页。</p>
            </div>
          </div>
        </Transition>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DEVICE_ICONS } from '../utils/deviceDisplay'

const router = useRouter()
const route = useRoute()
const step = ref(1)
const testing = ref(false)
const saving = ref(false)
const errorText = ref('')
const detail = ref({})
const createdId = ref(null)

const form = ref({
  name: '主路由',
  icon: 'router',
  host: '192.168.0.1',
  port: 22,
  username: 'root',
  auth_type: 'password',
  private_key_path: '~/.ssh/id_rsa',
  password: '',
})

const steps = [
  { id: 1, label: '连接' },
  { id: 2, label: '识别' },
  { id: 3, label: '保存' },
]

const authOptions = [
  { value: 'password', label: '密码登录' },
  { value: 'key', label: 'SSH 密钥' },
]

const currentTitle = computed(() => {
  if (step.value === 1) return '填写连接信息'
  if (step.value === 2) return '确认设备信息'
  return '完成'
})

const currentSubtitle = computed(() => {
  if (step.value === 1) return '先测试 SSH 是否可达，再保存到本地监控。'
  if (step.value === 2) return '检查识别到的信息是否符合预期。'
  return '初始化流程已完成。'
})

const canTest = computed(() => {
  if (!form.value.host || !form.value.username || !form.value.port) return false
  if (form.value.auth_type === 'password') return Boolean(form.value.password)
  return Boolean(form.value.private_key_path)
})

const InfoTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], default: '-' },
  },
  setup(props) {
    return () => h('div', { class: 'rounded-lg bg-slate-800/40 px-3 py-2 min-w-0' }, [
      h('div', { class: 'text-[11px] text-slate-500' }, props.label),
      h('div', { class: 'mt-1 text-sm font-medium text-white truncate' }, props.value || '-'),
    ])
  },
})

async function requestJson(url, options = {}) {
  const res = await fetch(url, options)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || data.message || `HTTP ${res.status}`)
  }
  return data
}

async function testConnection() {
  errorText.value = ''
  testing.value = true
  try {
    const data = await requestJson('/api/devices/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    if (!data.ok) {
      throw new Error(data.message || '连接失败')
    }
    detail.value = data.detail || {}
    step.value = 2
  } catch (e) {
    errorText.value = e.message
  } finally {
    testing.value = false
  }
}

async function saveDevice() {
  errorText.value = ''
  saving.value = true
  try {
    const data = await requestJson('/api/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    createdId.value = data.id
    step.value = 3
    setTimeout(() => router.push(route.query.next || '/'), 600)
  } catch (e) {
    errorText.value = e.message
    step.value = 1
  } finally {
    saving.value = false
  }
}

function formatUptime(seconds) {
  const s = Number(seconds || 0)
  if (!s) return '-'
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const mins = Math.floor((s % 3600) / 60)
  return `${days}天 ${hours}小时 ${mins}分钟`
}
</script>

<style scoped>
.setup-grid {
  background-image:
    linear-gradient(color-mix(in srgb, var(--c-cyan-400) 12%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--c-cyan-400) 12%, transparent) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(circle at center, black, transparent 70%);
}

.setup-radar {
  position: relative;
  width: min(20rem, 78vw);
  aspect-ratio: 1;
  border-radius: 50%;
  display: grid;
  place-items: center;
}

.setup-ring,
.setup-sweep,
.setup-core,
.setup-node {
  position: absolute;
  border-radius: 50%;
}

.setup-ring {
  inset: 0;
  border: 1px solid color-mix(in srgb, var(--c-cyan-400) 26%, transparent);
  animation: setup-pulse 3.6s ease-in-out infinite;
}

.ring-b {
  inset: 14%;
  animation-delay: .5s;
}

.ring-c {
  inset: 28%;
  animation-delay: 1s;
}

.setup-sweep {
  inset: 6%;
  background: conic-gradient(from 0deg, transparent 0 72%, color-mix(in srgb, var(--c-cyan-400) 28%, transparent), transparent 88% 100%);
  animation: setup-rotate 3.2s linear infinite;
}

.setup-core {
  width: 5.5rem;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  background: radial-gradient(circle, color-mix(in srgb, var(--c-brand-600) 42%, transparent), color-mix(in srgb, var(--c-sl-900) 82%, transparent));
  border: 1px solid color-mix(in srgb, var(--c-brand-300) 45%, transparent);
  box-shadow: 0 0 34px color-mix(in srgb, var(--c-cyan-400) 26%, transparent);
}

.setup-core span {
  color: var(--c-sl-50);
  font-weight: 800;
  letter-spacing: 0;
}

.setup-node {
  width: 1rem;
  aspect-ratio: 1;
  background: var(--c-green-400);
  box-shadow: 0 0 16px var(--c-green-400);
}

.setup-node span {
  position: absolute;
  inset: -0.45rem;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--c-green-400) 36%, transparent);
  animation: setup-ping 2.2s ease-out infinite;
}

.node-a {
  top: 17%;
  left: 26%;
}

.node-b {
  right: 13%;
  top: 48%;
  background: var(--c-cyan-400);
  box-shadow: 0 0 16px var(--c-cyan-400);
}

.node-c {
  bottom: 18%;
  left: 42%;
  background: var(--c-amber-400);
  box-shadow: 0 0 16px var(--c-amber-400);
}

.wizard-slide-enter-active,
.wizard-slide-leave-active {
  transition: opacity .22s ease, transform .22s ease;
}

.wizard-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.wizard-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes setup-rotate {
  to { transform: rotate(360deg); }
}

@keyframes setup-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: .55;
  }
  50% {
    transform: scale(1.04);
    opacity: .95;
  }
}

@keyframes setup-ping {
  0% {
    opacity: .9;
    transform: scale(.6);
  }
  100% {
    opacity: 0;
    transform: scale(1.8);
  }
}
</style>
