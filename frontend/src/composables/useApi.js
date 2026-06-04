import { ref } from 'vue'

const BASE = '/api'

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  async function get(path) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${BASE}${path}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json()
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
      const res = await fetch(`${BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json()
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
      const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, get, post, del }
}
