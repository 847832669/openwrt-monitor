import { ref, onMounted, onUnmounted, unref, watch } from 'vue'

const connected = ref(false)
const lastMessage = ref(null)
const metrics = ref({})
const alerts = ref([])
let ws = null
let reconnectTimer = null
let pingTimer = null
let subscribers = 0
let reconnectAttempts = 0

export function useWebSocket(enabled = true) {
  function connect() {
    if (
      ws &&
      (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    ws = new WebSocket(`${protocol}//${host}/ws/metrics`)

    ws.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
      pingTimer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
      }, 30000)
    }

    ws.onclose = () => {
      connected.value = false
      if (pingTimer) clearInterval(pingTimer)
      pingTimer = null
      ws = null
      if (subscribers > 0) {
        reconnectAttempts += 1
        const delay = Math.min(10000, 1000 * reconnectAttempts)
        reconnectTimer = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      ws?.close()
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'ping') {
          ws.send('pong')
          return
        }
        lastMessage.value = msg

        if (msg.type === 'metrics') {
          metrics.value = {
            ...metrics.value,
            [msg.device_id]: {
              ...msg.payload,
              timestamp: new Date().toISOString(),
            },
          }
        } else if (msg.type === 'alert' && msg.alert) {
          const exists = alerts.value.some((item) => item.id === msg.alert.id)
          if (!exists) {
            alerts.value = [msg.alert, ...alerts.value].slice(0, 100)
          }
        }
      } catch (e) {
        // 心跳文本消息忽略
      }
    }
  }

  function disconnect() {
    subscribers = Math.max(0, subscribers - 1)
    if (subscribers > 0) return

    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (pingTimer) clearInterval(pingTimer)
    reconnectTimer = null
    pingTimer = null
    ws?.close()
    ws = null
  }

  function clearAlerts() {
    alerts.value = []
  }

  onMounted(() => {
    if (!unref(enabled)) return
    subscribers += 1
    connect()
  })
  onUnmounted(() => disconnect())

  watch(
    () => unref(enabled),
    (value, oldValue) => {
      if (value && !oldValue) {
        subscribers += 1
        connect()
      } else if (!value && oldValue) {
        disconnect()
      }
    },
  )

  return { connected, lastMessage, metrics, alerts, clearAlerts, connect }
}
