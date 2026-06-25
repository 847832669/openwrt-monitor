import { ref } from 'vue'

const BASE = '/api'

export async function apiFetch(path, options = {}) {
  const url = path.startsWith('/api') ? path : `${BASE}${path}`
  const headers = { ...(options.headers || {}) }
  let body = options.body

  if (body && !(body instanceof FormData) && typeof body !== 'string') {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
    body = JSON.stringify(body)
  }

  const res = await fetch(url, {
    credentials: 'same-origin',
    ...options,
    headers,
    body,
  })

  if (res.status === 401 && !window.location.pathname.startsWith('/login')) {
    const next = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.href = `/login?next=${next}`
  }

  return res
}

export async function requestJson(path, options = {}) {
  const res = await apiFetch(path, options)
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch (e) {
      data = text
    }
  }
  if (!res.ok) {
    const message = typeof data === 'object' && data?.detail ? data.detail : `HTTP ${res.status}`
    throw new Error(message)
  }
  return data
}

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  async function get(path) {
    loading.value = true
    error.value = null
    try {
      return await requestJson(path)
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function post(path, data) {
    loading.value = true
    error.value = null
    try {
      return await requestJson(path, {
        method: 'POST',
        body: data,
      })
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function patch(path, data) {
    loading.value = true
    error.value = null
    try {
      return await requestJson(path, {
        method: 'PATCH',
        body: data,
      })
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function del(path) {
    loading.value = true
    error.value = null
    try {
      return await requestJson(path, { method: 'DELETE' })
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, get, post, patch, del }
}
