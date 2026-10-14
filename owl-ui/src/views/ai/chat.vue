<template>
  <div class="ai-chat-container">
    <!-- 左侧会话列表 -->
    <div class="session-panel">
      <div class="session-header">
        <div class="session-header-left">
          <el-button type="default" size="mini" icon="el-icon-s-home" @click="goHome">首页</el-button>
          <h3>AI 对话</h3>
        </div>
        <el-button type="primary" size="mini" icon="el-icon-plus" @click="newChat">新对话</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.sessionId"
          class="session-item"
          :class="{ active: s.sessionId === currentSessionId }"
          @click="switchSession(s.sessionId)"
        >
          <div class="session-title">{{ s.title || '新对话' }}</div>
          <div class="session-meta">
            <span>{{ s.messageCount || 0 }} 条</span>
            <el-button type="text" size="mini" icon="el-icon-edit" @click.stop="startRename(s)"></el-button>
            <el-button type="text" size="mini" icon="el-icon-delete" @click.stop="deleteSession(s.sessionId)"></el-button>
          </div>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无对话" :image-size="60"></el-empty>
      </div>
    </div>

    <!-- 重命名弹窗 -->
    <el-dialog title="重命名会话" :visible.sync="renameDialogVisible" width="400px" append-to-body>
      <el-input v-model="renameForm.title" placeholder="请输入新标题" />
      <span slot="footer">
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </span>
    </el-dialog>

    <!-- 配置 API Key 弹窗 -->
    <el-dialog title="配置 DeepSeek AI" :visible.sync="configDialogVisible" width="480px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="API Key">
          <el-input v-model="apiKeyInput" type="password" show-password :placeholder="configured ? '已配置，留空表示不修改' : '请输入你的 DeepSeek API Key（sk-...）'" />
          <div v-if="maskedKey" style="font-size:12px;color:#909399;margin-top:4px;">当前已配置：{{ maskedKey }}</div>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="configModel" placeholder="选择模型" style="width:100%">
            <el-option label="deepseek-chat（通用对话）" value="deepseek-chat" />
            <el-option label="deepseek-reasoner（推理）" value="deepseek-reasoner" />
            <el-option label="deepseek-flash（快速·便宜）" value="deepseek-flash" />
          </el-select>
        </el-form-item>
        <div style="font-size:12px;color:#909399;line-height:1.6;">
          Key 仅保存在本机配置文件，不会上传或打包进程序，请放心使用。可在 platform.deepseek.com 申请。
        </div>
      </el-form>
      <span slot="footer">
        <el-button v-if="configured" type="danger" style="float:left" @click="clearConfig">清除 Key</el-button>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </span>
    </el-dialog>

    <!-- 右侧聊天区域 -->
    <div class="chat-panel">
      <div class="chat-header">
        <span>{{ currentSessionTitle || '新对话' }}</span>
        <span class="limit-tip" v-if="remaining !== null">今日剩余：<strong>{{ remaining }}</strong> 次</span>
        <el-button size="mini" icon="el-icon-setting" @click="openConfig">设置 Key</el-button>
      </div>

      <div class="chat-messages" ref="msgContainer">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-row">
          <div v-if="msg.role === 'user'" class="msg-user">
            <div class="msg-bubble user-bubble">{{ msg.content }}</div>
          </div>
          <div v-else class="msg-ai">
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble ai-bubble">
              <span v-html="renderMarkdown(msg.content)"></span>
              <span v-if="msg._streaming" class="typing-cursor">|</span>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="msg-ai">
          <div class="msg-avatar">🤖</div>
          <div class="msg-bubble ai-bubble thinking"><span class="dot-flashing"></span> 思考中...</div>
        </div>
      </div>

      <div class="chat-input">
        <el-input type="textarea" :rows="3" v-model="inputText" placeholder="输入消息，Enter 发送..." :disabled="isLoading" @keydown.enter.native="handleEnter"></el-input>
        <el-button type="primary" :loading="isLoading" :disabled="!inputText.trim()" @click="sendMessage" style="margin-top:8px;">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { getSessions, getHistory, deleteSession, renameSession, sendMessage as apiSend, getAiConfig, saveAiConfig, clearAiConfig } from '@/api/ai'
import { getToken } from '@/utils/auth'

export default {
  name: 'AiChat',
  data() {
    return {
      sessions: [], currentSessionId: null, messages: [], inputText: '',
      isLoading: false, remaining: null,
      renameDialogVisible: false, renameForm: { sessionId: null, title: '' },
      configDialogVisible: false, apiKeyInput: '', configured: false, maskedKey: '', configModel: 'deepseek-chat'
    }
  },
  computed: {
    currentSessionTitle() {
      const s = this.sessions.find(x => x.sessionId === this.currentSessionId)
      return s ? s.title : '新对话'
    }
  },
  created() {
    if (!getToken()) { this.$router.push('/login'); return }
    this.loadSessions()
    this.loadConfig()
  },
  methods: {
    async loadSessions() {
      try {
        const res = await getSessions()
        this.sessions = (res.data || []).sort((a, b) => new Date(b.createTime) - new Date(a.createTime))
      } catch (e) {}
    },
    newChat() { this.currentSessionId = null; this.messages = []; this.inputText = '' },
    // 删除会话
    async deleteSession(sid) {
      try { await this.$confirm('确定删除此会话？', '提示', { type: 'warning' }) }
      catch (e) { if (e === 'cancel') return; return }
      if (this.currentSessionId === sid) { this.currentSessionId = null; this.messages = [] }
      try { await deleteSession(sid); this.sessions = this.sessions.filter(s => s.sessionId !== sid) }
      catch (e) {
        if (e && e.response && e.response.status === 404) {
          this.sessions = this.sessions.filter(s => s.sessionId !== sid)
          this.$message({ type: 'info', message: '会话不存在或已被删除', duration: 2000 })
        }
      }
    },
    // 切换会话
    async switchSession(sid) {
      if (!sid) return
      this.currentSessionId = sid
      try {
        const res = await getHistory(sid)
        this.messages = (res.data || []).map(m => ({ ...m, _streaming: false }))
        this.scrollToBottom()
      } catch (e) { this.messages = []; this.currentSessionId = null }
    },
    // 重命名
    startRename(s) { this.renameForm = { sessionId: s.sessionId, title: s.title || '' }; this.renameDialogVisible = true },
    async confirmRename() {
      const title = this.renameForm.title.trim()
      if (!title) return this.$message.warning('标题不能为空')
      try {
        await renameSession(this.renameForm.sessionId, title)
        const s = this.sessions.find(x => x.sessionId === this.renameForm.sessionId)
        if (s) s.title = title
        this.renameDialogVisible = false; this.$message.success('重命名成功')
      } catch (e) { this.$message.error('重命名失败') }
    },
    // 发送消息 — 不动原有逻辑
    handleEnter(e) { if (e.shiftKey) return; e.preventDefault(); this.sendMessage() },
    async sendMessage() {
      const text = this.inputText.trim()
      if (!text || this.isLoading) return
      this.messages.push({ role: 'user', content: text }); this.inputText = ''; this.isLoading = true; this.scrollToBottom()
      try {
        const res = await apiSend({ sessionId: this.currentSessionId, message: text, model: 'deepseek-chat' }, { timeout: 15000 })
        if (res.code === 200 && res.data) {
          if (res.data.sessionId && !this.currentSessionId) { this.currentSessionId = res.data.sessionId; this.loadSessions() }
          this.messages.push({ role: 'assistant', content: res.data.reply || '模型暂无有效回复，请换个问题重试' })
        } else {
          this.$message.warning(res.msg || '发送失败')
          const last = this.messages[this.messages.length - 1]
          if (last && last.role === 'user') this.messages.pop()
        }
      } catch (e) {
        if ((e.message || '').includes('timeout')) this.$message.error('请求超时，请重试')
        else this.$message.error('网络错误，请重试')
        const last = this.messages[this.messages.length - 1]
        if (last && last.role === 'user') this.messages.pop()
      } finally { this.isLoading = false }
    },
    renderMarkdown(content) {
      if (!content) return ''
      return content.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>').replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/\n/g, '<br>').replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '').replace(/on\w+\s*=\s*"[^"]*"/gi, '')
    },
    scrollToBottom() { this.$nextTick(() => { const el = this.$refs.msgContainer; if (el) el.scrollTop = el.scrollHeight }) },
    goHome() { this.$router.push('/') },
    // 加载 AI 配置状态
    async loadConfig() {
      try {
        const res = await getAiConfig()
        this.configured = !!(res.data && res.data.configured)
        this.maskedKey = (res.data && res.data.maskedKey) || ''
        this.configModel = (res.data && res.data.model) || 'deepseek-chat'
      } catch (e) {}
    },
    // 打开配置弹窗
    openConfig() {
      this.apiKeyInput = ''
      this.configDialogVisible = true
    },
    // 保存 API Key
    async saveConfig() {
      const key = this.apiKeyInput.trim()
      if (!key && !this.configured) return this.$message.warning('请输入 API Key')
      try {
        await saveAiConfig(key, this.configModel)
        this.configDialogVisible = false
        this.configured = true
        this.$message.success('保存成功')
      } catch (e) {
        this.$message.error('保存失败，请重试')
      }
    },
    // 清除 API Key
    async clearConfig() {
      try {
        await this.$confirm('确定清除已保存的 API Key？', '提示', { type: 'warning' })
      } catch (e) { return }
      try {
        await clearAiConfig()
        this.configured = false
        this.maskedKey = ''
        this.apiKeyInput = ''
        this.$message.success('已清除')
      } catch (e) {
        this.$message.error('清除失败，请重试')
      }
    }
  }
}
</script>

<style scoped>
.ai-chat-container { display: flex; height: calc(100vh - 84px); background: #f5f7fa; overflow: hidden; }
.session-panel { width: 260px; background: #fff; border-right: 1px solid #e4e7ed; display: flex; flex-direction: column; flex-shrink: 0; }
.session-header { padding: 16px; border-bottom: 1px solid #ebeef5; display: flex; justify-content: space-between; align-items: center; }
.session-header-left { display: flex; align-items: center; gap: 10px; }
.session-header-left h3 { margin: 0; }
.session-header h3 { margin: 0; font-size: 16px; color: #303133; }
.session-list { flex: 1; overflow-y: auto; padding: 8px; }
.session-item { padding: 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; transition: background 0.2s; }
.session-item:hover { background: #f5f7fa; }
.session-item.active { background: #ecf5ff; }
.session-title { font-size: 14px; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 12px; color: #909399; }
.chat-panel { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-header { padding: 12px 20px; background: #fff; border-bottom: 1px solid #ebeef5; font-size: 15px; color: #303133; display: flex; justify-content: space-between; align-items: center; }
.limit-tip { font-size: 13px; color: #909399; } .limit-tip strong { color: #409eff; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: #f5f7fa; }
.message-row { margin-bottom: 20px; }
.msg-user { display: flex; justify-content: flex-end; }
.msg-ai { display: flex; align-items: flex-start; gap: 10px; }
.msg-avatar { width: 36px; height: 36px; border-radius: 8px; background: #ecf5ff; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.msg-bubble { max-width: 90%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-break: break-word; }
.user-bubble { background: #409eff; color: #fff; border-bottom-right-radius: 4px; }
.ai-bubble { background: #fff; color: #303133; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.ai-bubble >>> pre { background: #f6f8fa; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 8px 0; }
.ai-bubble >>> code { font-size: 13px; font-family: Consolas, monospace; }
.typing-cursor { display: inline-block; color: #409eff; animation: blink 0.8s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.thinking { color: #909399; font-style: italic; }
.dot-flashing { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #409eff; animation: dot-flash 1s infinite alternate; margin-right: 4px; }
@keyframes dot-flash { 0% { opacity: 0.3; transform: scale(0.8); } 100% { opacity: 1; transform: scale(1.2); } }
.chat-input { padding: 16px 20px; background: #fff; border-top: 1px solid #ebeef5; }
</style>