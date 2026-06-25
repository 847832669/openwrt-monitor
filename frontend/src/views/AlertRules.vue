<template>
  <div class="page-container page-container-narrow space-y-6">
    <div>
      <h2 class="text-xl font-bold text-white">告警规则</h2>
      <p class="text-sm text-slate-400 mt-0.5">自定义告警触发条件 · 修改即时生效</p>
    </div>

    <div class="app-panel rounded-lg overflow-x-auto">
      <table class="min-w-[48rem] w-full text-sm">
        <thead>
          <tr class="text-slate-400 text-xs uppercase border-b border-slate-800">
            <th class="text-left px-4 py-3 font-medium w-8">状态</th>
            <th class="text-left px-4 py-3 font-medium">规则</th>
            <th class="text-left px-4 py-3 font-medium">级别</th>
            <th class="text-left px-4 py-3 font-medium">指标</th>
            <th class="text-left px-4 py-3 font-medium">条件</th>
            <th class="text-left px-4 py-3 font-medium w-28">阈值</th>
            <th class="text-left px-4 py-3 font-medium w-20">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/50">
          <tr v-for="rule in rules" :key="rule.id"
            class="hover:bg-slate-800/40 transition-colors"
            :class="{ 'opacity-40': !rule.enabled }">
            <td class="px-4 py-3">
              <button @click="toggleRule(rule)"
                class="w-5 h-5 rounded flex items-center justify-center text-xs transition-colors"
                :class="rule.enabled ? 'bg-green-500/20 text-green-400' : 'bg-slate-800 text-slate-600'">
                {{ rule.enabled ? '✓' : '✕' }}
              </button>
            </td>
            <td class="px-4 py-3 text-white font-medium">{{ rule.name }}</td>
            <td class="px-4 py-3">
              <span class="text-xs px-1.5 py-0.5 rounded font-medium"
                :class="rule.level === 'crit' ? 'bg-red-900/50 text-red-300' : rule.level === 'warn' ? 'bg-amber-900/50 text-amber-300' : 'bg-blue-900/50 text-blue-300'">
                {{ rule.level === 'crit' ? '严重' : rule.level === 'warn' ? '警告' : '信息' }}
              </span>
            </td>
            <td class="px-4 py-3 font-mono text-slate-300 text-xs">{{ rule.field }}</td>
            <td class="px-4 py-3 font-mono text-slate-400 text-xs">{{ rule.op === 'gt' ? '>' : rule.op === 'lt' ? '<' : '=' }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-1">
                <input type="number" step="any"
                  :value="editingRule === rule.id ? editThreshold : rule.threshold"
                  @focus="startEdit(rule)"
                  @input="editThreshold = $event.target.value"
                  @blur="saveThreshold(rule)"
                  @keydown.enter="saveThreshold(rule)"
                  class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white font-mono text-right focus:outline-none focus:border-brand-500"
                />
                <span class="text-slate-500 text-xs w-5">{{ rule.unit }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <button @click="resetRule(rule)" class="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                重置
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="app-panel-soft rounded-lg p-4">
      <h4 class="text-sm font-semibold text-slate-300 mb-2">📝 说明</h4>
      <ul class="text-xs text-slate-400 space-y-1 list-disc list-inside">
        <li>点击 <span class="text-green-400">✓</span> / <span class="text-slate-600">✕</span> 切换规则启用状态</li>
        <li>点击阈值数字直接修改，回车或失焦保存</li>
        <li>修改即刻生效，无需重启</li>
        <li>同一告警 5 分钟内不重复触发</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const rules = ref([])
const editingRule = ref(null)
const editThreshold = ref('')

async function loadRules() {
  try {
    const res = await fetch('/api/alerts/rules')
    const data = await res.json()
    rules.value = (data.rules || []).map(r => ({ ...r, threshold: Number(r.threshold) }))
  } catch (e) {
    console.error('加载规则失败', e)
  }
}

async function updateRule(rule, updates) {
  try {
    const res = await fetch(`/api/alerts/rules/${rule.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
  } catch (e) {
    console.error('更新规则失败', e)
  }
}

async function toggleRule(rule) {
  rule.enabled = !rule.enabled
  await updateRule(rule, { enabled: rule.enabled })
}

function startEdit(rule) {
  editingRule.value = rule.id
  editThreshold.value = rule.threshold
}

async function saveThreshold(rule) {
  const val = parseFloat(editThreshold.value)
  if (isNaN(val) || val < 0) return
  rule.threshold = val
  editingRule.value = null
  await updateRule(rule, { threshold: val })
}

async function resetRule(rule) {
  // 找默认值
  const defaults = {
    cpu_high: 80, cpu_crit: 95, mem_low: 85, mem_crit: 92,
    conntrack_high: 80, load_high: 5.0, disk_high: 85, device_offline: 0,
  }
  const val = defaults[rule.id]
  if (val !== undefined) {
    rule.threshold = val
    await updateRule(rule, { threshold: val })
  }
}

onMounted(loadRules)
</script>
