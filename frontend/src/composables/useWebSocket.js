import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const lastMessage = ref(null)
  const metrics = ref({})
  let ws = null
  let reconnectTimer = null
  let pingTimer = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    ws = new WebSocket(`${protocol}//${host}/ws/metrics`)

    ws.onopen = () => {
      connected.value = true
      console.log('[WS] 已连接')
      // 每30秒 ping
      pingTimer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) ws.send('ping')
      }, 30000)
    }

    ws.onclose = () => {
      connected.value = false
      if (pingTimer) clearInterval(pingTimer)
      console.log('[WS] 断开，3秒后重连')
      reconnectTimer = setTimeout(connect, 3000)
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
        }
      } catch (e) {
        // 心跳文本消息忽略
      }
    }
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (pingTimer) clearInterval(pingTimer)
    ws?.close()
    ws = null
  }

  onMounted(() => connect())
  onUnmounted(() => disconnect())

  return { connected, lastMessage, metrics }
}
