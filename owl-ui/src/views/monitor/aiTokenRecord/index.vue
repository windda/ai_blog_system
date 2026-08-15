<template>
  <div class="app-container">
    <!-- 汇总卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px;">
      <el-col :span="6"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">今日调用次数</div><div class="summary-value">{{ summary.dailyCalls }}</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">今日消耗 Token</div><div class="summary-value">{{ summary.dailyTokens }}</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">累计调用次数</div><div class="summary-value">{{ summary.totalCalls }}</div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover"><div class="summary-item"><div class="summary-label">累计总 Token</div><div class="summary-value">{{ summary.totalTokens }}</div></div></el-card></el-col>
    </el-row>

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
        <el-table-column label="输入Token" prop="promptTokens" width="90" />
        <el-table-column label="输出Token" prop="completionTokens" width="90" />
        <el-table-column label="总Token" prop="totalTokens" width="90" />
        <el-table-column label="模型" prop="model" min-width="100" />
        <el-table-column label="对话时间" prop="createTime" min-width="160" />
      </el-table>
      <el-pagination v-if="total>0" background layout="prev,pager,next" :total="total" :page-size="queryParams.pageSize" @current-change="handlePageChange" style="margin-top:16px;" />
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'AiTokenRecord',
  data() {
    return {
      loading: false, total: 0, recordList: [],
      userList: [],
      summary: { dailyCalls: 0, dailyTokens: 0, totalCalls: 0, totalTokens: 0 },
      queryParams: { pageNum: 1, pageSize: 10, userId: '', filterUser: '', dateFrom: '', dateTo: '' }
    }
  },
  created() { this.fetchUsers(); this.fetchSummary(); this.fetchRecords() },
  methods: {
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
    handleQuery() { this.queryParams.pageNum = 1; this.fetchRecords(); this.fetchSummary() },
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