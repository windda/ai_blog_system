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

// 查询 AI 配置状态（是否已配置 Key、当前模型、打码预览）
export function getAiConfig() {
  return request({ url: '/ai/config', method: 'get' })
}

// 保存 AI API Key + 模型（BYOK）
export function saveAiConfig(apiKey, model) {
  return request({ url: '/ai/config', method: 'post', data: { apiKey, model } })
}

// 清除 AI API Key
export function clearAiConfig() {
  return request({ url: '/ai/config', method: 'delete' })
}
