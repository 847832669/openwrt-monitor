<template>
  <div class="app-panel min-w-0 min-h-[6.25rem] rounded-lg p-4 xl:p-5 hover:border-slate-700 transition-all"
    :class="{ 'animate-glow': glow }">
    <div class="flex items-start justify-between gap-2 mb-2">
      <span class="min-w-0 text-xs text-slate-400 font-medium uppercase tracking-wider truncate">{{ title }}</span>
      <span class="grid place-items-center shrink-0 w-8 h-8 rounded-lg bg-slate-800/50 text-lg">{{ icon }}</span>
    </div>
    <div class="metric-value min-w-0 text-2xl xl:text-[1.7rem] leading-tight font-bold text-white mb-1" :class="valueClass">
      {{ prefix }}{{ value }}{{ suffix }}
    </div>
    <div v-if="subtitle" class="min-w-0 text-xs text-slate-500 truncate">{{ subtitle }}</div>
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
  valueClass: { type: String, default: '' },
})
</script>
