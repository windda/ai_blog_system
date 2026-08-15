import request from '@/utils/request'

// 获取会话列表
export function getSessions() {
  return request({ url: '/ai/chat/history', method: 'get' })
}

// 获取会话消息历史
export function getHistory(sessionId) {
  return request({ url: `/ai/chat/history/${sessionId}`, method: 'get' })
}

// 删除会话
export function deleteSession(sessionId) {
  return request({ url: `/ai/chat/history/${sessionId}`, method: 'delete' })
}

// 重命名会话
export function renameSession(sessionId, title) {
  return request({ url: `/ai/chat/history/${sessionId}/rename`, method: 'put', data: { title } })
}

// 清空所有对话
export function clearAllSessions() {
  return request({ url: '/ai/chat/history/clear', method: 'post' })
}

// 发送消息（HTTP POST 模式，支持超时配置）
export function sendMessage(data, config = {}) {
  return request({ url: '/ai/chat', method: 'post', data, timeout: config.timeout || 8000 })
}
