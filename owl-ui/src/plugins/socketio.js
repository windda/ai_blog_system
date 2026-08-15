/**
 * SocketIO 全局工具类（Tier4 前端对接）
 *
 * 功能：
 * 1. 登录后连接 WebSocket，根据 user_id 加入 room
 * 2. 断线自动重连，登出时断开销毁
 * 3. 封装 on/emit 供全局使用
 *
 * 使用方式：
 *   import socket from '@/plugins/socketio'
 *   socket.on('notice:new', callback)
 *   socket.connect(token, userId)
 *   socket.disconnect()
 */
import io from 'socket.io-client'

const SOCKET_URL = 'http://localhost:9000'

let socket = null
let _listeners = {} // 记录已注册的事件回调，便于重连时恢复

/**
 * 初始化 SocketIO 连接
 * @param {string} token   JWT token
 * @param {number} userId  当前登录用户ID
 */
export function connect(token, userId) {
  if (socket && socket.connected) {
    return socket
  }

  socket = io(SOCKET_URL, {
    query: { token },
    transports: ['websocket', 'polling'], // WebSocket 优先，降级 HTTP 轮询
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000
  })

  socket.on('connect', () => {
    console.log('[SocketIO] 已连接:', socket.id)
    // 重新绑定之前注册的事件
    Object.entries(_listeners).forEach(([event, callback]) => {
      socket.off(event).on(event, callback)
    })
  })

  socket.on('disconnect', (reason) => {
    console.log('[SocketIO] 断开:', reason)
  })

  socket.on('connect_error', (err) => {
    console.warn('[SocketIO] 连接错误:', err.message)
  })

  return socket
}

/**
 * 注册事件监听器（会自动在重连后恢复）
 * @param {string}   event    事件名
 * @param {Function} callback 回调函数
 */
export function on(event, callback) {
  _listeners[event] = callback
  if (socket) {
    socket.off(event).on(event, callback)
  }
}

/**
 * 移除事件监听器
 * @param {string} event 事件名
 */
export function off(event) {
  delete _listeners[event]
  if (socket) {
    socket.off(event)
  }
}

/**
 * 断开 SocketIO 连接并清理
 */
export function disconnect() {
  _listeners = {}
  if (socket) {
    socket.removeAllListeners()
    socket.disconnect()
    socket = null
  }
}

/**
 * 获取当前 socket 实例
 */
export function getSocket() {
  return socket
}

export default {
  connect,
  disconnect,
  on,
  off,
  getSocket
}