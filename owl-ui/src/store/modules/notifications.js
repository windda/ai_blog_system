/**
 * 站内通知 Vuex 模块（Tier4 新增）
 *
 * 状态：
 * - unreadCount: 未读通知数（导航栏小红点显示）
 * - list: 通知列表（按时间倒序）
 *
 * 使用：
 *   this.$store.commit('notifications/ADD', notice)
 *   this.$store.commit('notifications/CLEAR')
 *   this.$store.getters['notifications/unreadBadge']
 */
import { Notification } from 'element-ui'
import socket from '@/plugins/socketio'

const state = {
  unreadCount: 0,
  list: []
}

const mutations = {
  ADD(state, notice) {
    state.list.unshift({
      ...notice,
      id: Date.now(),
      read: false
    })
    state.unreadCount++
  },
  CLEAR(state) {
    state.unreadCount = 0
    state.list.forEach(n => n.read = true)
  },
  RESET(state) {
    state.unreadCount = 0
    state.list = []
  }
}

const getters = {
  unreadBadge: state => state.unreadCount > 0 ? state.unreadCount : '',
  notificationList: state => state.list.filter(n => !n.read)
}

const actions = {
  /**
   * 初始化监听：注册后端推送事件
   * 应在全局 import 时调用，确保事件只绑定一次
   */
  init({ commit }) {
    socket.on('new_notification', (data) => {
      commit('ADD', data)
      // ElementUI 右上角弹窗通知
      Notification({
        title: data.title || '新通知',
        message: data.content || '',
        type: 'info',
        duration: 5000,
        position: 'top-right'
      })
    })
  },

  /**
   * 清除未读
   */
  clear({ commit }) {
    commit('CLEAR')
  },

  /**
   * 登出时重置
   */
  reset({ commit }) {
    commit('RESET')
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}