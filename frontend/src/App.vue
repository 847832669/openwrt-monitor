<template>
  <div class="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
    <!-- 侧边栏 -->
    <aside class="w-56 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
      <div class="p-5 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-2xl">📶</span>
          <div>
            <h1 class="text-base font-bold text-white">OpenWrt</h1>
            <p class="text-xs text-slate-400">性能监控平台</p>
          </div>
        </div>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <router-link
          v-for="item in navItems" :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
          :class="$route.path === item.path
            ? 'bg-brand-600/20 text-brand-300 border border-brand-700/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="p-4 border-t border-slate-800">
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <span class="inline-block w-2 h-2 rounded-full"
            :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'"></span>
          {{ wsConnected ? '实时连接中' : '已断开' }}
        </div>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWebSocket } from './composables/useWebSocket'

const { connected: wsConnected } = useWebSocket()

const navItems = [
  { path: '/', icon: '📊', label: '仪表盘' },
  { path: '/system', icon: '📈', label: '系统分析' },
  { path: '/network', icon: '🌐', label: '网络分析' },
  { path: '/lan', icon: '🖥️', label: '连接设备' },
  { path: '/devices', icon: '⚙️', label: '设备管理' },
]
</script>
