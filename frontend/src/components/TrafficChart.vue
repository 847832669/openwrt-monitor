<template>
  <div class="app-panel rounded-lg p-4"
    :class="fill ? 'h-full flex flex-col' : ''">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-slate-300">{{ title }}</h3>
      <div class="flex gap-3 text-xs">
        <span class="flex items-center gap-1">
          <span class="w-2.5 h-0.5 bg-cyan-400 inline-block"></span> RX
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2.5 h-0.5 bg-amber-400 inline-block"></span> TX
        </span>
        <span class="text-slate-500 ml-1">{{ unitSuffix }}/s</span>
      </div>
    </div>
    <div ref="chartRef" class="w-full min-h-0" :class="fill ? 'flex-1' : ''" :style="{ height: fill ? undefined : height }"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  title: { type: String, default: '实时流量' },
  height: { type: String, default: '200px' },
  data: { type: Array, default: () => [] },
  unit: { type: String, default: 'bits' },
  fill: Boolean,
})

const chartRef = ref(null)
let chart = null
let inited = false
let echartsModule = null

const unitSuffix = computed(() => props.unit === 'bytes' ? 'B' : 'b')

function fmt(v) {
  if (!v || v === 0) return '0 ' + unitSuffix.value
  const step = props.unit === 'bytes' ? 1024 : 1000
  const suffix = props.unit === 'bytes'
    ? ['B', 'KB', 'MB', 'GB', 'TB']
    : ['b', 'Kb', 'Mb', 'Gb', 'Tb']
  let val = v
  let i = 0
  while (val >= step && i < suffix.length - 1) { val /= step; i++ }
  return val.toFixed(i === 0 ? 0 : 1) + ' ' + suffix[i]
}

// 单位格式（短名，用于 Y 轴）
function shortUnit() {
  const suffix = props.unit === 'bytes' ? '' : ''
  return suffix
}

async function loadEcharts() {
  if (!echartsModule) {
    const mod = await import('../utils/echarts')
    echartsModule = mod.getEcharts()
  }
  return echartsModule
}

function createChartOptions(echarts) {
  return {
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 12 },
      formatter: (params) => {
        if (!params || !params.length) return ''
        const time = params[0].axisValue
        const rx = fmt(params[0].value)
        const tx = fmt(params[1]?.value ?? 0)
        return `<div style="font-size:12px">${time}</div>
                <div>⬇ RX: ${rx}/s</div>
                <div>⬆ TX: ${tx}/s</div>`
      },
    },
    grid: { left: 50, right: 12, top: 10, bottom: 28 },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 10 },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      min: 0,
      axisLabel: {
        color: '#64748b', fontSize: 10,
        formatter: (v) => {
          const step = props.unit === 'bytes' ? 1024 : 1000
          let val = v
          let i = 0
          const units = ['', 'K', 'M', 'G', 'T']
          while (val >= step && i < units.length - 1) { val /= step; i++ }
          return (i === 0 ? val.toFixed(0) : val.toFixed(1)) + units[i]
        },
      },
    },
    series: [
      {
        name: 'RX',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        animationDuration: 400,
        animationDurationUpdate: 300,
        animationEasingUpdate: 'linear',
        lineStyle: { color: '#22d3ee', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34, 211, 238, 0.3)' },
            { offset: 1, color: 'rgba(34, 211, 238, 0)' },
          ]),
        },
      },
      {
        name: 'TX',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        animationDuration: 400,
        animationDurationUpdate: 300,
        animationEasingUpdate: 'linear',
        lineStyle: { color: '#fbbf24', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(251, 191, 36, 0.3)' },
            { offset: 1, color: 'rgba(251, 191, 36, 0)' },
          ]),
        },
      },
    ],
  }
}

async function initChart() {
  if (!chartRef.value || chart) return
  const echarts = await loadEcharts()
  if (!chartRef.value || chart) return
  chart = echarts.init(chartRef.value, 'dark')
  // 只设置一次完整配置
  chart.setOption(createChartOptions(echarts))
  inited = true
  // 如果有初始数据，更新一下
  if (props.data.length) updateData()
}

function updateData() {
  if (!chart || !inited) return
  const times = props.data.map(d => d.time)
  const rxData = props.data.map(d => d.rx)
  const txData = props.data.map(d => d.tx)

  // 只更新数据，不重建配置 — 动画过渡更丝滑
  chart.setOption({
    xAxis: { data: times },
    series: [
      { data: rxData },
      { data: txData },
    ],
  }, { notMerge: false })
}

watch(() => props.data, () => {
  updateData()
}, { deep: true })

watch(() => props.unit, () => {
  // 单位切换时重建（因为 tooltip 和 Y 轴格式化变了）
  if (chart) {
    chart.dispose()
    chart = null
    inited = false
  }
  nextTick(initChart)
})

onMounted(() => {
  nextTick(initChart)
  const resize = () => chart?.resize()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  chart?.dispose()
  chart = null
  inited = false
})
</script>
