<template>
  <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-all"
    :class="{ 'animate-glow': glow }">
    <div class="flex items-start justify-between mb-2">
      <span class="text-xs text-slate-400 font-medium uppercase tracking-wider">{{ title }}</span>
      <span class="text-lg">{{ icon }}</span>
    </div>
    <div class="metric-value text-2xl font-bold text-white mb-1">
      {{ prefix }}{{ value }}{{ suffix }}
    </div>
    <div v-if="subtitle" class="text-xs text-slate-500">{{ subtitle }}</div>
    <!-- 迷你进度条 -->
    <div v-if="progress !== undefined" class="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div class="h-full rounded-full transition-all duration-500"
        :style="{ width: Math.min(progress, 100) + '%' }"
        :class="progress > 80 ? 'bg-red-400' : progress > 50 ? 'bg-amber-400' : 'bg-green-400'">
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  value: [String, Number],
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  subtitle: String,
  icon: { type: String, default: '📊' },
  progress: Number,
  glow: Boolean,
})
</script>
