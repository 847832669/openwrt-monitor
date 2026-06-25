const API_UTC_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/

export function parseApiTime(value) {
  if (!value) return null
  if (value instanceof Date) return value
  const text = String(value)
  const date = new Date(API_UTC_PATTERN.test(text) ? `${text}Z` : text)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatLocalTime(value, options = {}) {
  const date = parseApiTime(value)
  if (!date) return options.fallback ?? '-'
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: options.seconds === false ? undefined : '2-digit',
  })
}

export function formatLocalMinute(value, options = {}) {
  return formatLocalTime(value, { ...options, seconds: false })
}

export function formatLocalHourLabel(value, options = {}) {
  const date = parseApiTime(value)
  if (!date) return options.fallback ?? String(value || '-')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  return `${month}-${day} ${hour}:00`
}

export function formatLocalDateTime(value, options = {}) {
  const date = parseApiTime(value)
  if (!date) return options.fallback ?? '-'
  return date.toLocaleString('zh-CN', { hour12: false })
}
