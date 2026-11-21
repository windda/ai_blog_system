<template>
  <div class="app-container">
    <!-- 汇总卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px;">
      <el-col :span="5"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">今日调用次数</div><div class="summary-value">{{ summary.dailyCalls }}</div></div></el-card></el-col>
      <el-col :span="5"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">今日消耗 Token</div><div class="summary-value">{{ summary.dailyTokens }}</div></div></el-card></el-col>
      <el-col :span="5"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">累计调用次数</div><div class="summary-value">{{ summary.totalCalls }}</div></div></el-card></el-col>
      <el-col :span="5"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">累计总 Token</div><div class="summary-value">{{ summary.totalTokens }}</div></div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">今日额度（已用/限额）</div><div class="summary-value">{{ dailyUsage.todayTokens }} / {{ dailyUsage.dailyLimit }}</div></div></el-card></el-col>
    </el-row>

    <!-- 平台全局 API Key 配置（管理员） -->
    <el-card style="margin-bottom:16px;">
      <div slot="header" style="font-weight:600;">平台全局 API Key 配置</div>
      <el-form :inline="true" size="small">
        <el-form-item label="平台 Key">
          <el-input v-model="platformKeyInput" type="password" show-password placeholder="填写平台共用的 API Key" style="width:320px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-check" @click="savePlatformKey">保存</el-button>
          <el-button v-if="platformKey.configured" type="danger" icon="el-icon-delete" @click="clearPlatformKey">清除</el-button>
        </el-form-item>
      </el-form>
      <div v-if="platformKey.configured" style="font-size:12px;color:#909399;">当前已配置：{{ platformKey.maskedKey }}</div>
      <div style="font-size:12px;color:#909399;margin-top:4px;">平台全局 Key 加密存储在服务端数据库，配置后即时生效，无需修改 yaml 或重启服务。</div>
    </el-card>

    <!-- 供应商接口成功率（容灾监控） -->
    <el-card style="margin-bottom:16px;">
      <div slot="header" style="font-weight:600;">供应商接口成功率（容灾监控）</div>
      <el-table :data="providerList" size="mini" stripe>
        <el-table-column prop="provider" label="服务商" min-width="100" />
        <el-table-column prop="model" label="模型" min-width="130" />
        <el-table-column prop="total" label="调用次数" width="90" align="right" />
        <el-table-column prop="success" label="成功" width="80" align="right" />
        <el-table-column prop="failed" label="失败" width="80" align="right" />
        <el-table-column label="成功率" width="110" align="right">
          <template slot-scope="scope">
            <el-tag :type="scope.row.successRate >= 95 ? 'success' : (scope.row.successRate >= 80 ? 'warning' : 'danger')" size="mini">{{ scope.row.successRate }}%</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avgLatencyMs" label="平均耗时(ms)" width="120" align="right" />
      </el-table>
      <el-empty v-if="providerList.length === 0" description="暂无调用记录" :image-size="60" />
    </el-card>

    <!-- 平台 Key 余额/失效告警 -->
    <el-alert v-if="platformKeyAlert.alert" :title="platformKeyAlert.reason" type="error" show-icon :closable="false" style="margin-bottom:16px;" />

    <!-- Token 监控报表（ECharts） -->
    <el-card style="margin-bottom:16px;">
      <div slot="header" style="font-weight:600;">Token 监控报表</div>
      <el-row :gutter="20">
        <el-col :span="14"><div ref="trendChart" style="height:300px;"></div></el-col>
        <el-col :span="10"><div ref="modelChart" style="height:300px;"></div></el-col>
      </el-row>
    </el-card>

    <!-- 供应商调用日志（含失败原因） -->
    <el-card style="margin-bottom:16px;">
      <div slot="header" style="font-weight:600;">供应商调用日志（含失败原因）</div>
      <el-form :inline="true" size="small">
        <el-form-item label="状态">
          <el-select v-model="callLogQuery.status" placeholder="全部" clearable style="width:120px;" @change="handleCallLogQuery">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型"><el-input v-model="callLogQuery.model" placeholder="模型名" clearable style="width:160px;" @keyup.enter.native="handleCallLogQuery" /></el-form-item>
        <el-form-item><el-button type="primary" icon="el-icon-search" @click="handleCallLogQuery">查询</el-button></el-form-item>
      </el-form>
      <el-table :data="callLogList" v-loading="callLogLoading" size="mini" stripe>
        <el-table-column prop="createTime" label="时间" width="160" />
        <el-table-column prop="userId" label="用户ID" width="80" />
        <el-table-column prop="provider" label="服务商" width="100" />
        <el-table-column prop="model" label="模型" min-width="130" />
        <el-table-column prop="latencyMs" label="耗时(ms)" width="90" align="right" />
        <el-table-column label="状态" width="80" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.success ? 'success' : 'danger'" size="mini">{{ scope.row.success ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="失败原因" min-width="200" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.errorCategory" style="color:#f56c6c;">{{ scope.row.errorCategory }}: {{ scope.row.errorMessage }}</span>
            <span v-else style="color:#909399;">-</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-if="callLogTotal>0" background layout="prev,pager,next" :total="callLogTotal" :page-size="callLogQuery.pageSize" @current-change="handleCallLogPage" style="margin-top:16px;" />
    </el-card>

    <!-- 搜索栏 -->
    <el-card>
      <el-form :inline="true" :model="queryParams" size="small">
        <el-form-item label="用户">
          <el-select v-model="queryParams.filterUser" placeholder="选择用户" clearable style="width:160px;">
            <el-option v-for="u in userList" :key="u.userId" :label="`${u.nickName || u.userName} (ID:${u.userId})`" :value="String(u.userId)" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="queryParams.dateFrom" type="date" placeholder="开始" value-format="yyyy-MM-dd" style="width:130px;" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="queryParams.dateTo" type="date" placeholder="结束" value-format="yyyy-MM-dd" style="width:130px;" /></el-form-item>
        <el-form-item><el-button type="primary" icon="el-icon-search" @click="handleQuery">查询</el-button><el-button icon="el-icon-refresh" @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="margin-top:16px;">
      <el-table :data="recordList" v-loading="loading" stripe style="width:100%;">
        <el-table-column label="用户ID" prop="userId" width="70" />
        <el-table-column label="用户名称" prop="userName" min-width="120" />
        <el-table-column label="会话ID" prop="sessionId" width="70" />
        <el-table-column label="会话标题" prop="sessionTitle" min-width="140" show-overflow-tooltip />
        <el-table-column label="输入Token" prop="promptTokens" width="90" />
        <el-table-column label="输出Token" prop="completionTokens" width="90" />
        <el-table-column label="总Token" prop="totalTokens" width="90" />
        <el-table-column label="模型" prop="model" min-width="100" />
        <el-table-column label="统计来源" prop="statisticsSource" min-width="110">
          <template slot-scope="scope">
            <el-tooltip :content="scope.row.statisticsSource === 'api' ? 'api = 模型返回真实 token' : 'local_estimate = 文本估算，仅参考'" placement="top">
              <el-tag :type="scope.row.statisticsSource === 'api' ? 'success' : 'warning'" size="mini">
                {{ scope.row.statisticsSource === 'api' ? 'api' : 'local_estimate' }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="对话时间" prop="createTime" min-width="160" />
      </el-table>
      <el-pagination v-if="total>0" background layout="prev,pager,next" :total="total" :page-size="queryParams.pageSize" @current-change="handlePageChange" style="margin-top:16px;" />
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/request'
import echarts from 'echarts'

export default {
  name: 'AiTokenRecord',
  data() {
    return {
      loading: false, total: 0, recordList: [],
      userList: [],
      summary: { dailyCalls: 0, dailyTokens: 0, totalCalls: 0, totalTokens: 0 },
      dailyUsage: { todayTokens: 0, dailyLimit: 0 },
      providerList: [],
      platformKey: { configured: false, maskedKey: '' },
      platformKeyInput: '',
      platformKeyAlert: { alert: false, reason: '' },
      chartData: { dailyTrend: [], modelUsage: [] },
      callLogList: [], callLogTotal: 0, callLogLoading: false,
      callLogQuery: { pageNum: 1, pageSize: 10, status: '', model: '' },
      queryParams: { pageNum: 1, pageSize: 10, userId: '', filterUser: '', dateFrom: '', dateTo: '' }
    }
  },
  created() { this.fetchUsers(); this.fetchSummary(); this.fetchRecords(); this.fetchDailyUsage(); this.fetchProviderRate(); this.fetchPlatformKey(); this.fetchPlatformKeyAlert(); this.fetchTokenChart(); this.fetchCallLogs() },
  methods: {
    async fetchDailyUsage() {
      try { const res = await request({ url: '/ai/daily-usage', method: 'get' }); if (res && res.data) this.dailyUsage = res.data } catch (e) {}
    },
    async fetchPlatformKey() {
      try { const res = await request({ url: '/admin/ai/platform-key', method: 'get' }); if (res && res.data) this.platformKey = res.data } catch (e) {}
    },
    async savePlatformKey() {
      const key = this.platformKeyInput.trim()
      if (!key) return this.$message.warning('请输入平台 API Key')
      try {
        await request({ url: '/admin/ai/platform-key', method: 'post', data: { apiKey: key } })
        this.$message.success('平台全局 Key 已保存')
        this.platformKeyInput = ''
        this.fetchPlatformKey()
      } catch (e) { this.$message.error('保存失败，请重试') }
    },
    async clearPlatformKey() {
      try {
        await this.$confirm('确定清除平台全局 Key？清除后用户将回退到各自的自有 Key 或环境变量。', '提示', { type: 'warning' })
      } catch (e) { return }
      try {
        await request({ url: '/admin/ai/platform-key', method: 'delete' })
        this.$message.success('平台全局 Key 已清除')
        this.platformKeyInput = ''
        this.fetchPlatformKey()
      } catch (e) { this.$message.error('清除失败，请重试') }
    },
    async fetchPlatformKeyAlert() {
      try { const res = await request({ url: '/admin/ai/platform-key-alert', method: 'get' }); if (res && res.data) this.platformKeyAlert = res.data } catch (e) {}
    },
    async fetchTokenChart() {
      try {
        const res = await request({ url: '/admin/ai/token-chart', method: 'get' })
        if (res && res.data) { this.chartData = res.data; this.$nextTick(() => this.renderCharts()) }
      } catch (e) {}
    },
    renderCharts() { this.renderTrendChart(); this.renderModelChart() },
    renderTrendChart() {
      const el = this.$refs.trendChart; if (!el) return
      const chart = echarts.init(el)
      const data = this.chartData.dailyTrend || []
      chart.setOption({
        title: { text: '最近 14 天 Token 消耗趋势', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'axis' },
        grid: { left: 50, right: 20, top: 50, bottom: 30 },
        xAxis: { type: 'category', data: data.map(d => d.date) },
        yAxis: { type: 'value' },
        series: [{ type: 'line', data: data.map(d => d.tokens), smooth: true, areaStyle: {}, itemStyle: { color: '#409eff' } }]
      })
    },
    renderModelChart() {
      const el = this.$refs.modelChart; if (!el) return
      const chart = echarts.init(el)
      const data = this.chartData.modelUsage || []
      chart.setOption({
        title: { text: '各模型用量统计', textStyle: { fontSize: 14 } },
        tooltip: { trigger: 'item', formatter: '{b}: {c} token ({d}%)' },
        legend: { bottom: 0 },
        series: [{ type: 'pie', radius: ['35%', '60%'], data: data.map(d => ({ name: d.model, value: d.tokens })) }]
      })
    },
    async fetchCallLogs() {
      this.callLogLoading = true
      try {
        const params = { pageNum: this.callLogQuery.pageNum, pageSize: this.callLogQuery.pageSize }
        if (this.callLogQuery.status) params.status = this.callLogQuery.status
        if (this.callLogQuery.model) params.model = this.callLogQuery.model
        const res = await request({ url: '/admin/ai/call-logs', method: 'get', params })
        this.callLogList = (res && res.rows) ? res.rows : []; this.callLogTotal = (res && res.total) ? res.total : 0
      } catch (e) { this.callLogList = [] }
      this.callLogLoading = false
    },
    handleCallLogQuery() { this.callLogQuery.pageNum = 1; this.fetchCallLogs() },
    handleCallLogPage(p) { this.callLogQuery.pageNum = p; this.fetchCallLogs() },
    async fetchProviderRate() {
      try { const res = await request({ url: '/admin/ai/provider-success-rate', method: 'get' }); if (res && res.data) this.providerList = res.data } catch (e) { this.providerList = [] }
    },
    async fetchUsers() {
      try { const res = await request({ url: '/admin/ai/users', method: 'get' }); if (res && res.data) this.userList = res.data } catch (e) {}
    },
    async fetchSummary() {
      try { const res = await request({ url: '/admin/ai/token-summary', method: 'get' }); if (res && res.data) this.summary = res.data } catch (e) {}
    },
    async fetchRecords() {
      this.loading = true
      try {
        const params = { pageNum: this.queryParams.pageNum, pageSize: this.queryParams.pageSize }
        if (this.queryParams.filterUser) params.userId = this.queryParams.filterUser
        if (this.queryParams.dateFrom) params.dateFrom = this.queryParams.dateFrom
        if (this.queryParams.dateTo) params.dateTo = this.queryParams.dateTo
        const res = await request({ url: '/admin/ai/token-records', method: 'get', params })
        this.recordList = (res && res.rows) ? res.rows : []; this.total = (res && res.total) ? res.total : 0
      } catch (e) { this.recordList = [] }
      this.loading = false
    },
    handleQuery() {
      this.queryParams.pageNum = 1
      // 日期校验：开始日期晚于结束日期时自动交换，保证 start_date <= end_date
      const { dateFrom, dateTo } = this.queryParams
      if (dateFrom && dateTo && dateFrom > dateTo) {
        this.queryParams.dateFrom = dateTo
        this.queryParams.dateTo = dateFrom
        this.$message.warning('开始日期晚于结束日期，已自动交换')
      }
      this.fetchRecords(); this.fetchSummary()
    },
    resetQuery() { this.queryParams = { pageNum: 1, pageSize: 10, userId: '', filterUser: '', dateFrom: '', dateTo: '' }; this.handleQuery() },
    handlePageChange(p) { this.queryParams.pageNum = p; this.fetchRecords() }
  }
}
</script>

<style scoped>
.summary-item { text-align: center; padding: 8px 0; }
.summary-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.summary-value { font-size: 28px; font-weight: bold; color: #409eff; }
</style>