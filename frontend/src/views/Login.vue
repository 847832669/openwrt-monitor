<template>
  <main class="min-h-dvh grid lg:grid-cols-[1fr_28rem] bg-slate-950 text-slate-100 overflow-hidden">
    <section class="relative hidden lg:flex flex-col justify-between p-10 overflow-hidden">
      <div class="absolute inset-0 login-grid opacity-45"></div>
      <div class="relative z-10 flex items-center gap-3">
        <span class="grid h-11 w-11 place-items-center rounded-lg bg-brand-600/20 text-2xl">📶</span>
        <div>
          <h1 class="text-lg font-bold text-white">OpenWrt Monitor</h1>
          <p class="text-sm text-slate-400">家庭网络性能监控平台</p>
        </div>
      </div>

      <div class="relative z-10 max-w-3xl">
        <div class="status-pill inline-flex text-xs text-cyan-300">
          <span class="dot-online"></span>
          访问保护已启用
        </div>
        <h2 class="mt-6 text-4xl font-bold tracking-normal text-white">
          进入你的网络控制台
        </h2>
        <p class="mt-4 max-w-xl text-sm leading-7 text-slate-400">
          输入管理员账号继续。长期部署时请修改默认管理员密码和 OWM_SECRET_KEY。
        </p>
      </div>
    </section>

    <section class="flex min-h-dvh items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md">
        <div class="mb-8 lg:hidden flex items-center gap-3">
          <span class="grid h-11 w-11 place-items-center rounded-lg bg-brand-600/20 text-2xl">📶</span>
          <div>
            <h1 class="text-lg font-bold text-white">OpenWrt Monitor</h1>
            <p class="text-sm text-slate-400">性能监控平台</p>
          </div>
        </div>

        <form class="app-panel rounded-lg p-5 sm:p-6" @submit.prevent="login">
          <div class="mb-6">
            <div class="status-pill inline-flex text-xs text-slate-400">管理员登录</div>
            <h2 class="mt-4 text-2xl font-bold text-white">欢迎回来</h2>
            <p class="mt-2 text-sm text-slate-400">使用部署时配置的管理员账号进入控制台。</p>
          </div>

          <div v-if="security?.auth_disabled" class="mb-4 rounded-lg border border-amber-400/40 bg-amber-900/20 px-3 py-2 text-sm text-amber-200">
            当前已通过 OWM_AUTH_DISABLED 关闭认证。
          </div>

          <div v-if="errorText" class="mb-4 rounded-lg border border-red-400/40 bg-red-900/20 px-3 py-2 text-sm text-red-300">
            {{ errorText }}
          </div>

          <label class="block space-y-1.5">
            <span class="text-xs text-slate-400">用户名</span>
            <input v-model="form.username" autocomplete="username"
              class="app-control w-full px-3 text-sm text-white"
              placeholder="admin" />
          </label>

          <label class="mt-4 block space-y-1.5">
            <span class="text-xs text-slate-400">密码</span>
            <input v-model="form.password" autocomplete="current-password" type="password"
              class="app-control w-full px-3 text-sm text-white"
              placeholder="管理员密码" />
          </label>

          <button type="submit" :disabled="loading || !form.username || !form.password"
            class="mt-6 flex w-full items-center justify-center rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-50">
            {{ loading ? '登录中...' : '登录' }}
          </button>

          <div v-if="security?.default_secret || security?.default_admin_password"
            class="mt-5 space-y-2 rounded-lg border border-amber-400/30 bg-amber-900/10 p-3 text-xs leading-5 text-amber-100">
            <p v-if="security.default_secret">检测到默认 OWM_SECRET_KEY，请在生产环境修改。</p>
            <p v-if="security.default_admin_password">检测到默认管理员密码 admin，请设置 OWM_ADMIN_PASSWORD。</p>
          </div>
        </form>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { requestJson } from '../composables/useApi'

const route = useRoute()
const loading = ref(false)
const errorText = ref('')
const security = ref(null)
const form = ref({
  username: 'admin',
  password: '',
})

async function login() {
  loading.value = true
  errorText.value = ''
  try {
    const data = await requestJson('/auth/login', {
      method: 'POST',
      body: form.value,
    })
    security.value = data.security
    const next = typeof route.query.next === 'string' && route.query.next.startsWith('/')
      ? route.query.next
      : '/'
    window.location.href = next
  } catch (e) {
    errorText.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const me = await requestJson('/auth/me')
    security.value = me.security
  } catch (e) {
    // 未登录时忽略。
  }
})
</script>

<style scoped>
.login-grid {
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 44px 44px;
}
</style>
