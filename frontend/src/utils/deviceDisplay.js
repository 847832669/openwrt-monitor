export const DEVICE_ICONS = [
  { key: 'router', icon: '📡', label: '路由器' },
  { key: 'gateway', icon: '🌐', label: '网关' },
  { key: 'wifi', icon: '📶', label: '无线' },
  { key: 'server', icon: '🗄️', label: '服务器' },
  { key: 'nas', icon: '💾', label: '存储' },
  { key: 'shield', icon: '🛡️', label: '防火墙' },
  { key: 'lab', icon: '🧪', label: '实验' },
  { key: 'home', icon: '🏠', label: '家庭' },
]

const iconMap = Object.fromEntries(DEVICE_ICONS.map(item => [item.key, item]))

export function getDeviceIcon(device) {
  const key = device?.icon || 'router'
  return iconMap[key]?.icon || iconMap.router.icon
}

export function getDeviceIconLabel(key) {
  return iconMap[key]?.label || iconMap.router.label
}

export function getDeviceDisplayName(device) {
  return device?.name || device?.host || '未命名设备'
}
