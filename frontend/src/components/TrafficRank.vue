<template>
  <section class="app-panel traffic-rank rounded-lg p-4 overflow-hidden">
    <div class="traffic-rank-aura"></div>
    <div class="relative z-10">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between mb-4">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <span class="grid place-items-center w-8 h-8 rounded-lg bg-slate-800/60 border border-slate-700/70 text-base">⇅</span>
            <div>
              <h3 class="text-sm font-semibold text-slate-200">网络流量排行</h3>
              <p class="mt-0.5 text-xs text-slate-500">{{ noteText }}</p>
            </div>
          </div>
        </div>
        <div class="flex flex-wrap gap-2">
          <span class="status-pill text-xs text-slate-400">
            {{ sourceLabel }}
          </span>
          <span class="status-pill text-xs" :class="mode === 'bytes' ? 'text-cyan-300' : 'text-amber-300'">
            {{ modeLabel }}
          </span>
          <span v-if="sampledFlows" class="status-pill text-xs text-slate-400">
            {{ sampledFlows }} 条连接
          </span>
        </div>
      </div>

      <div v-if="items.length" class="space-y-3">
        <button v-for="(item, index) in items" :key="item.ip"
          type="button"
          @click="$emit('select', item)"
          class="traffic-rank-row block w-full text-left border border-slate-800/90 rounded-lg px-3 py-3">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex items-start gap-3">
              <span class="traffic-rank-index numeric-value">{{ index + 1 }}</span>
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-semibold text-white truncate max-w-[12rem] sm:max-w-xs">
                    {{ displayName(item) }}
                  </span>
                  <span v-for="proto in topProtocols(item)" :key="proto.name"
                    class="rounded border border-slate-700/70 bg-slate-900/70 px-1.5 py-0.5 text-[10px] uppercase text-slate-400">
                    {{ proto.name }} {{ proto.count }}
                  </span>
                  <span v-for="app in topApplications(item)" :key="app.name"
                    class="rounded border border-cyan-400/25 bg-cyan-400/10 px-1.5 py-0.5 text-[10px] text-cyan-300">
                    {{ app.name }} {{ app.count }}
                  </span>
                </div>
                <div class="mt-1 text-[11px] text-slate-500 font-mono truncate">
                  {{ subline(item) }}
                </div>
              </div>
            </div>
            <div class="shrink-0 text-right">
              <div class="numeric-value text-sm font-semibold text-white">{{ primaryValue(item) }}</div>
              <div class="mt-1 text-[11px] text-slate-500">{{ secondaryValue(item) }}</div>
            </div>
          </div>

          <div class="mt-3 h-2 rounded-full bg-slate-800/90 overflow-hidden">
            <div class="traffic-rank-bar h-full rounded-full"
              :class="mode === 'bytes' ? 'traffic-rank-bar-bytes' : 'traffic-rank-bar-connections'"
              :style="{ width: scoreWidth(item) }"></div>
          </div>

          <div v-if="mode === 'bytes'" class="mt-2 grid grid-cols-2 gap-3 text-[11px]">
            <div>
              <div class="flex items-center justify-between text-slate-500 mb-1">
                <span>下载</span>
                <span class="numeric-value text-cyan-300">{{ formatBytes(item.download_bytes) }}</span>
              </div>
              <div class="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-cyan-400 transition-all duration-500"
                  :style="{ width: directionWidth(item.download_bytes, item.total_bytes) }"></div>
              </div>
            </div>
            <div>
              <div class="flex items-center justify-between text-slate-500 mb-1">
                <span>上传</span>
                <span class="numeric-value text-amber-300">{{ formatBytes(item.upload_bytes) }}</span>
              </div>
              <div class="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-amber-400 transition-all duration-500"
                  :style="{ width: directionWidth(item.upload_bytes, item.total_bytes) }"></div>
              </div>
            </div>
          </div>
        </button>
      </div>

      <div v-else class="traffic-rank-empty rounded-lg border border-dashed border-slate-800 px-4 py-8 text-center">
        <div class="text-sm font-semibold text-slate-300">暂无网络排行数据</div>
        <p class="mt-1 text-xs text-slate-500">当前固件没有暴露连接明细，或暂时没有可识别的局域网连接。</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rank: { type: Object, default: () => ({}) },
  limit: { type: Number, default: 8 },
})

defineEmits(['select'])

const mode = computed(() => props.rank?.mode || 'unavailable')
const sampledFlows = computed(() => Number(props.rank?.sampled_flows || 0))
const items = computed(() => (props.rank?.items || []).slice(0, props.limit))
const maxScore = computed(() => Math.max(...items.value.map(item => Number(item.score || 0)), 1))
const sourceLabel = computed(() => {
  if (props.rank?.source === 'nlbwmon') return 'nlbwmon'
  if (props.rank?.source === 'conntrack-command') return 'conntrack'
  return '数据源待定'
})
const modeLabel = computed(() => {
  if (mode.value === 'bytes') return '按流量'
  if (mode.value === 'connections') return '按连接'
  return '未就绪'
})
const noteText = computed(() => {
  if (props.rank?.note) return props.rank.note
  if (mode.value === 'bytes') return '基于连接跟踪字节统计'
  if (mode.value === 'connections') return '字节计数不可用，使用连接热度'
  return '等待连接跟踪数据'
})

function displayName(item) {
  return item.hostname || item.ip || '-'
}

function subline(item) {
  const parts = []
  if (item.hostname && item.ip) parts.push(item.ip)
  if (item.mac) parts.push(item.mac)
  if (item.interface) parts.push(item.interface)
  return parts.join(' · ') || item.ip || '-'
}

function topProtocols(item) {
  return Object.entries(item.protocols || {})
    .map(([name, count]) => ({ name, count }))
    .slice(0, 2)
}

function topApplications(item) {
  const protocolNames = new Set(Object.keys(item.protocols || {}).map(name => name.toLowerCase()))
  return Object.entries(item.applications || {})
    .map(([name, count]) => ({ name, count }))
    .filter(item => item.name && item.name !== 'OTHER' && !protocolNames.has(item.name.toLowerCase()))
    .slice(0, 2)
}

function scoreWidth(item) {
  const score = Number(item.score || 0)
  if (!score) return '0%'
  return `${Math.max(score / maxScore.value * 100, 4)}%`
}

function directionWidth(value, total) {
  const base = Number(total || 0)
  if (!base) return '0%'
  return `${Math.max(Number(value || 0) / base * 100, Number(value || 0) > 0 ? 4 : 0)}%`
}

function primaryValue(item) {
  if (mode.value === 'bytes') return formatBytes(item.total_bytes)
  return `${item.connections || 0} 连接`
}

function secondaryValue(item) {
  if (mode.value === 'bytes') return `${item.connections || 0} 连接`
  return `${item.packets || 0} 包`
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
</script>

<style scoped>
.traffic-rank {
  position: relative;
}

.traffic-rank-aura {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, color-mix(in srgb, var(--c-cyan-400) 10%, transparent), transparent 34%),
    radial-gradient(circle at 92% 0%, color-mix(in srgb, var(--c-amber-400) 14%, transparent), transparent 18rem);
  opacity: .72;
}

.traffic-rank-row {
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--app-surface-muted) 82%, transparent), transparent),
    color-mix(in srgb, var(--app-surface) 86%, transparent);
  transition: transform .18s ease, border-color .18s ease, background .18s ease;
}

.traffic-rank-row:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--c-cyan-400) 40%, var(--app-border));
}

.traffic-rank-index {
  display: grid;
  width: 1.75rem;
  height: 1.75rem;
  place-items: center;
  border-radius: 8px;
  color: var(--c-cyan-400);
  background: color-mix(in srgb, var(--c-cyan-400) 12%, var(--app-surface-muted));
  border: 1px solid color-mix(in srgb, var(--c-cyan-400) 28%, var(--app-border));
  font-size: .78rem;
  font-weight: 800;
}

.traffic-rank-bar {
  position: relative;
  transition: width .55s ease;
}

.traffic-rank-bar::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .38), transparent);
  animation: rankSweep 2.4s ease-in-out infinite;
}

.traffic-rank-bar-bytes {
  background: linear-gradient(90deg, var(--c-cyan-400), var(--c-amber-400));
}

.traffic-rank-bar-connections {
  background: linear-gradient(90deg, var(--c-green-400), var(--c-cyan-400));
}

.traffic-rank-empty {
  background: color-mix(in srgb, var(--app-surface-muted) 52%, transparent);
}

@keyframes rankSweep {
  0% {
    transform: translateX(-100%);
  }
  55%, 100% {
    transform: translateX(100%);
  }
}
</style>
