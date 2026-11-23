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
    <el-dialog title="配置 AI API Key" :visible.sync="configDialogVisible" width="480px" append-to-body>
      <el-form label-width="80px">
        <div style="font-size:12px;color:#606266;line-height:1.8;background:#f5f7fa;padding:10px;border-radius:4px;margin-bottom:12px;">
          <div style="font-weight:600;margin-bottom:4px;">两种调用模式：</div>
          <div>① <strong>使用平台统一额度</strong>：不填写 Key，直接对话，消耗平台共用 Key；</div>
          <div>② <strong>使用自己的 API Key</strong>：填写并保存 Key，优先用你自己的 Key。</div>
          <div style="color:#909399;margin-top:4px;">两种模式都受平台每日 Token 限额管控。</div>
        </div>
        <el-form-item label="API Key">
          <el-input v-model="apiKeyInput" type="password" show-password :placeholder="configured ? '已配置，留空表示不修改' : '请输入你的 API Key'" />
          <div v-if="maskedKey" style="font-size:12px;color:#909399;margin-top:4px;">当前已配置：{{ maskedKey }}</div>
        </el-form-item>
        <div style="font-size:12px;color:#909399;line-height:1.6;">
          您的 API Key 将加密存储在服务端，仅用于您本人调用，不会对外泄露。API Key 由对应模型厂商提供。
        </div>
      </el-form>
      <span slot="footer">
        <el-button v-if="configured" type="danger" style="float:left" @click="clearConfig">清除 Key</el-button>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </span>
    </el-dialog>

    <!-- 用户个人用量面板 -->
    <el-dialog title="我的用量" :visible.sync="usageDialogVisible" width="760px" append-to-body>
      <!-- 平台额度：只统计平台 Key 消耗，受每日限额管控 -->
      <div class="usage-section-title">平台额度</div>
      <div class="usage-cards">
        <div class="usage-card"><div class="usage-card-value">{{ usage.todayPlatformTokens }}</div><div class="usage-card-label">今日已消耗 Token</div></div>
        <div class="usage-card"><div class="usage-card-value">{{ usage.todayPlatformTokens }} / {{ usage.dailyLimit }}</div><div class="usage-card-label">平台额度（已用/限额）</div></div>
        <div class="usage-card"><div class="usage-card-value">{{ usage.todayPlatformCount }}</div><div class="usage-card-label">今日调用次数</div></div>
      </div>
      <!-- 自有密钥调用统计：不计入平台额度，无总量上限 -->
      <div class="usage-section-title">自有密钥调用统计（不计入平台额度）</div>
      <div class="usage-cards">
        <div class="usage-card"><div class="usage-card-value">{{ usage.todayUserTokens }}</div><div class="usage-card-label">今日消耗 Token</div></div>
        <div class="usage-card"><div class="usage-card-value">{{ usage.todayUserCount }}</div><div class="usage-card-label">今日调用次数</div></div>
      </div>
      <el-table :data="myRecords" v-loading="myRecordsLoading" size="mini" style="margin-top:16px;" max-height="360">
        <el-table-column prop="createTime" label="时间" width="160" />
        <el-table-column prop="model" label="模型" width="140" />
        <el-table-column prop="sessionTitle" label="会话" min-width="150" show-overflow-tooltip />
        <el-table-column prop="promptTokens" label="输入" width="80" align="right" />
        <el-table-column prop="completionTokens" label="输出" width="80" align="right" />
        <el-table-column prop="totalTokens" label="总 Token" width="90" align="right" />
        <el-table-column prop="statisticsSource" label="来源" width="110" />
      </el-table>
    </el-dialog>

    <!-- 右侧聊天区域 -->
    <div class="chat-panel">
      <div class="chat-header">
        <span>{{ currentSessionTitle || '新对话' }}</span>
        <el-select v-model="currentModel" size="mini" filterable allow-create default-first-option style="width:180px;" placeholder="选择模型" @change="onModelChange">
          <el-option-group v-for="p in providerList" :key="p.provider" :label="p.provider">
            <el-option v-for="m in p.models" :key="m" :label="m" :value="m" />
          </el-option-group>
        </el-select>
        <span class="limit-tip">平台额度已用：<strong>{{ usage.todayPlatformTokens }}</strong> / {{ usage.dailyLimit }} token</span>
        <el-select v-model="callMode" size="mini" style="width:150px;" title="选择调用模式">
          <el-option label="平台统一额度" value="platform" />
          <el-option label="使用自己的 Key" value="user" :disabled="!configured" />
          <el-option label="自动（自有优先）" value="auto" />
        </el-select>
        <el-button size="mini" icon="el-icon-data-line" @click="openUsage">我的用量</el-button>
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
        <div class="chat-input-actions">
          <!-- ASR 语音输入按钮：由后台开关 ai.asr.enabled 控制（默认关闭，管理员后台开启后显示） -->
          <el-button v-if="asrEnabled" :type="isRecording ? 'danger' : 'default'" :icon="isRecording ? 'el-icon-close' : 'el-icon-microphone'" :loading="asrLoading" @click="toggleRecord">{{ isRecording ? '停止录音' : '语音输入' }}</el-button>
          <el-button type="primary" :loading="isLoading" :disabled="!inputText.trim()" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSessions, getHistory, deleteSession, renameSession, getAiConfig, saveAiConfig, clearAiConfig } from '@/api/ai'
import { getToken } from '@/utils/auth'

export default {
  name: 'AiChat',
  data() {
    return {
      sessions: [], currentSessionId: null, messages: [], inputText: '',
      isLoading: false, remaining: null,
      renameDialogVisible: false, renameForm: { sessionId: null, title: '' },
      configDialogVisible: false, apiKeyInput: '', configured: false, maskedKey: '', configModel: 'deepseek-chat', asrEnabled: false,
      currentModel: localStorage.getItem('ai_model') || 'deepseek-chat',
      callMode: 'auto',
      providerList: [],
      // 用户个人用量面板
      usage: { todayPlatformTokens: 0, todayPlatformCount: 0, dailyLimit: 0, todayUserTokens: 0, todayUserCount: 0 },
      usageDialogVisible: false, myRecords: [], myRecordsLoading: false,
      // ASR 录音
      isRecording: false, mediaRecorder: null, audioChunks: [], asrLoading: false
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
    this.loadProviders()
    this.loadUsage()
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

      // 调用模式：platform 强制平台统一额度 / user 强制自己的 Key / auto 自有优先
      let apiKey = localStorage.getItem('ai_api_key') || ''
      const keySource = this.callMode
      if (this.callMode === 'platform') apiKey = ''  // 平台模式不传自有 Key
      const model = this.currentModel || localStorage.getItem('ai_model') || 'deepseek-chat'

      // 推送用户消息 + 空占位的 AI 消息（流式逐 token 填充）
      this.messages.push({ role: 'user', content: text })
      this.inputText = ''
      this.isLoading = true
      const aiMsg = { role: 'assistant', content: '', _streaming: true }
      this.messages.push(aiMsg)
      this.scrollToBottom()

      const token = getToken()
      const baseApi = process.env.VUE_APP_BASE_API || ''
      try {
        const resp = await fetch(`${baseApi}/ai/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
          },
          body: JSON.stringify({ sessionId: this.currentSessionId, message: text, apiKey: apiKey, model: model, keySource: keySource })
        })

        if (!resp.ok) {
          throw new Error('HTTP ' + resp.status)
        }

        const reader = resp.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          // 按 \n\n 分割 SSE 事件
          let idx
          while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const eventBlock = buffer.slice(0, idx)
            buffer = buffer.slice(idx + 2)
            for (const line of eventBlock.split('\n')) {
              if (!line.startsWith('data:')) continue
              const dataStr = line.slice(5).trim()
              if (!dataStr || dataStr === '[DONE]') continue
              try {
                const payload = JSON.parse(dataStr)
                if (payload.token) {
                  aiMsg.content += payload.token
                  this.scrollToBottom()
                } else if (payload.done) {
                  aiMsg.content = payload.fullText || aiMsg.content
                  aiMsg._streaming = false
                  if (payload.sessionId && !this.currentSessionId) {
                    this.currentSessionId = payload.sessionId
                    this.loadSessions()
                  }
                  // 对话完成、token 已入库后，立即刷新顶部「今日已用」，避免用户误以为无消耗
                  this.loadUsage()
                } else if (payload.error) {
                  aiMsg._streaming = false
                  this.$message.error(payload.error)
                }
              } catch (e) { /* 忽略单条解析失败 */ }
            }
          }
        }
        aiMsg._streaming = false
        if (!aiMsg.content) aiMsg.content = '（无回复）'
      } catch (e) {
        const idx = this.messages.indexOf(aiMsg)
        if (idx !== -1) this.messages.splice(idx, 1)
        this.$message.error('网络错误，请重试')
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },
    renderMarkdown(content) {
      if (!content) return ''
      return content.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>').replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/\n/g, '<br>').replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '').replace(/on\w+\s*=\s*"[^"]*"/gi, '')
    },
    scrollToBottom() { this.$nextTick(() => { const el = this.$refs.msgContainer; if (el) el.scrollTop = el.scrollHeight }) },
    goHome() { this.$router.push('/') },
    // 加载启用的供应商 + 模型列表（动态渲染顶部模型下拉）
    async loadProviders() {
      try {
        const token = getToken()
        const baseApi = process.env.VUE_APP_BASE_API || ''
        const resp = await fetch(`${baseApi}/ai/providers`, {
          headers: { 'Authorization': 'Bearer ' + token }
        })
        const data = await resp.json()
        this.providerList = (data && data.data) ? data.data : []
      } catch (e) { this.providerList = [] }
    },
    // 加载 AI 配置状态
    async loadConfig() {
      try {
        const res = await getAiConfig()
        this.configured = !!(res.data && res.data.configured)
        this.maskedKey = (res.data && res.data.maskedKey) || ''
        this.configModel = (res.data && res.data.model) || 'deepseek-chat'
        this.asrEnabled = !!(res.data && res.data.asrEnabled)
      } catch (e) {}
    },
    // 打开配置弹窗
    openConfig() {
      this.apiKeyInput = ''
      this.configDialogVisible = true
    },
    // 切换模型（同一会话内切换，后续消息用新模型，上下文沿用）
    onModelChange(model) {
      if (model) {
        localStorage.setItem('ai_model', model)
      }
    },
    // 保存 API Key
    async saveConfig() {
      const key = this.apiKeyInput.trim()
      if (!key && !this.configured) return this.$message.warning('请输入 API Key')
      try {
        await saveAiConfig(key, this.configModel)
        // 统一存 localStorage（键名统一：ai_api_key / ai_model）
        if (key) localStorage.setItem('ai_api_key', key)
        localStorage.setItem('ai_model', this.configModel)
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
        localStorage.removeItem('ai_api_key')
        localStorage.removeItem('ai_model')
        this.configured = false
        this.maskedKey = ''
        this.apiKeyInput = ''
        this.$message.success('已清除')
      } catch (e) {
        this.$message.error('清除失败，请重试')
      }
    },
    // ============ 用户个人用量面板 ============
    async loadUsage() {
      try {
        const token = getToken()
        const baseApi = process.env.VUE_APP_BASE_API || ''
        const resp = await fetch(`${baseApi}/ai/daily-usage`, { headers: { 'Authorization': 'Bearer ' + token } })
        const data = await resp.json()
        if (data && data.data) this.usage = data.data
      } catch (e) {}
    },
    openUsage() {
      this.usageDialogVisible = true
      // 打开弹窗时刷新顶部汇总，确保汇总和明细都是最新
      this.loadUsage()
      this.loadMyRecords()
    },
    async loadMyRecords() {
      this.myRecordsLoading = true
      try {
        const token = getToken()
        const baseApi = process.env.VUE_APP_BASE_API || ''
        const resp = await fetch(`${baseApi}/ai/my-token-records?pageNum=1&pageSize=50`, { headers: { 'Authorization': 'Bearer ' + token } })
        const data = await resp.json()
        this.myRecords = (data && data.rows) ? data.rows : []
      } catch (e) { this.myRecords = [] } finally { this.myRecordsLoading = false }
    },
    // ============ ASR 语音识别（网页端录音 -> 后端转写） ============
    // 注意：主分支已隐藏语音按钮，此段 ASR 代码保留不删除。
    // 语音识别功能在 feature-asr 分支迭代，作为后续扩展。
    toggleRecord() {
      if (this.isRecording) { this.stopRecord() } else { this.startRecord() }
    },
    async startRecord() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        this.audioChunks = []
        this.mediaRecorder = new MediaRecorder(stream)
        this.mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) this.audioChunks.push(e.data) }
        this.mediaRecorder.onstop = () => { this.uploadAudio() }
        this.mediaRecorder.start()
        this.isRecording = true
      } catch (e) {
        this.$message.error('无法访问麦克风，请检查浏览器权限')
      }
    },
    stopRecord() {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop()
        this.isRecording = false
        if (this.mediaRecorder.stream) this.mediaRecorder.stream.getTracks().forEach(t => t.stop())
      }
    },
    async uploadAudio() {
      if (!this.audioChunks.length) return
      this.asrLoading = true
      const blob = new Blob(this.audioChunks, { type: 'audio/webm' })
      try {
        const token = getToken()
        const baseApi = process.env.VUE_APP_BASE_API || ''
        const fd = new FormData()
        fd.append('file', blob, 'record.webm')
        const resp = await fetch(`${baseApi}/ai/asr`, { method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: fd })
        const data = await resp.json()
        if (data && data.code === 200 && data.data && data.data.text) {
          this.inputText = (this.inputText ? this.inputText + ' ' : '') + data.data.text
          this.$message.success('语音识别成功')
          // ASR 也产生 token 消耗，识别成功后刷新今日用量
          this.loadUsage()
        } else {
          this.$message.error((data && data.msg) || '语音识别失败')
        }
      } catch (e) {
        this.$message.error('语音识别请求失败')
      } finally { this.asrLoading = false }
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
.chat-input-actions { display: flex; gap: 8px; margin-top: 8px; justify-content: flex-end; }
.usage-cards { display: flex; gap: 12px; flex-wrap: wrap; }
.usage-section-title { font-size: 13px; font-weight: 600; color: #606266; margin: 14px 0 8px; }
.usage-card { flex: 1; min-width: 120px; background: #f5f7fa; border-radius: 8px; padding: 14px; text-align: center; }
.usage-card-value { font-size: 20px; font-weight: 600; color: #303133; }
.usage-card-label { font-size: 12px; color: #909399; margin-top: 6px; }
</style>
