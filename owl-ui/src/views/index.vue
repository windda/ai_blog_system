<template>
  <div class="dashboard-editor-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="panel-group">
      <el-col :xs="12" :sm="12" :lg="6" class="card-panel-col">
        <div class="card-panel card-panel-articles" @click="goTo('article')">
          <div class="card-panel-icon-wrapper">
            <svg-icon icon-class="peoples" class-name="card-panel-icon" />
          </div>
          <div class="card-panel-description">
            <div class="card-panel-text">已发布文章</div>
            <count-to :start-val="0" :end-val="totalArticles" :duration="1500" class="card-panel-num" />
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="card-panel-col">
        <div class="card-panel card-panel-comments" @click="goTo('comment')">
          <div class="card-panel-icon-wrapper">
            <svg-icon icon-class="message" class-name="card-panel-icon" />
          </div>
          <div class="card-panel-description">
            <div class="card-panel-text">评论总数</div>
            <count-to :start-val="0" :end-val="totalComments" :duration="1500" class="card-panel-num" />
          </div>
          <el-tag v-if="pendingComments > 0" size="mini" type="danger" class="pending-tag">
            {{ pendingComments }} 待审核
          </el-tag>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="card-panel-col">
        <div class="card-panel card-panel-categories" @click="goToIfAdmin('category')">
          <div class="card-panel-icon-wrapper">
            <svg-icon icon-class="tree" class-name="card-panel-icon" />
          </div>
          <div class="card-panel-description">
            <div class="card-panel-text">分类数</div>
            <count-to :start-val="0" :end-val="totalCategories" :duration="1500" class="card-panel-num" />
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="card-panel-col">
        <div class="card-panel card-panel-tags" @click="goToIfAdmin('tag')">
          <div class="card-panel-icon-wrapper">
            <svg-icon icon-class="tag" class-name="card-panel-icon" />
          </div>
          <div class="card-panel-description">
            <div class="card-panel-text">标签数</div>
            <count-to :start-val="0" :end-val="totalTags" :duration="1500" class="card-panel-num" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表 + 最新评论 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 文章发布趋势图表 -->
      <el-col :xs="24" :sm="24" :lg="16">
        <el-card shadow="never" class="box-card">
          <div slot="header" class="clearfix">
            <span style="font-weight: bold; font-size: 16px;">近7天文章发布趋势</span>
            <span style="float: right; font-size: 12px; color: #999;">
              今日总浏览：<span style="color: #1890ff; font-weight: bold;">{{ todayViews }}</span>
            </span>
          </div>
          <div ref="trendChart" style="width: 100%; height: 280px;"></div>
        </el-card>
      </el-col>
      <!-- 最新评论动态 -->
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card shadow="never" class="box-card">
          <div slot="header" class="clearfix">
            <span style="font-weight: bold; font-size: 16px;">最新评论动态</span>
            <el-button style="float: right; padding: 3px 0" type="text" @click="goTo('comment')">
              更多
            </el-button>
          </div>
          <div class="comment-list" v-if="recentComments.length > 0">
            <div class="comment-item" v-for="item in recentComments" :key="item.commentId">
              <div class="comment-header">
                <span class="comment-author">{{ item.authorName || '匿名' }}</span>
                <span class="comment-status">
                  <el-tag 
                    :type="item.status === '1' ? 'success' : 'warning'" 
                    size="mini"
                  >
                    {{ item.status === '1' ? '已通过' : '待审核' }}
                  </el-tag>
                </span>
              </div>
              <div class="comment-content">{{ item.content }}</div>
              <div class="comment-footer">
                <span class="comment-article" @click="goArticle(item.articleId)">
                  于「{{ item.articleTitle }}」
                </span>
                <span class="comment-time">{{ item.createTime }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无评论" :image-size="80"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新文章列表 -->
    <el-card shadow="never" class="box-card" style="margin-top: 20px;">
      <div slot="header" class="clearfix">
        <span style="font-weight: bold; font-size: 16px;">最新发布</span>
        <el-tag 
          v-for="cat in categoryList" 
          :key="cat.categoryId"
          :type="selectedCategory === cat.categoryId ? 'primary' : 'info'"
          style="margin-left: 8px; cursor: pointer;"
          size="small"
          @click="filterByCategory(cat.categoryId)"
        >
          {{ cat.categoryName }}
        </el-tag>
        <el-tag 
          v-if="selectedCategory"
          size="small" 
          style="margin-left: 8px; cursor: pointer;"
          type="warning"
          @click="filterByCategory(null)"
        >
          清除筛选
        </el-tag>
      </div>

      <el-table v-loading="loading" :data="articleList" style="width: 100%">
        <el-table-column label="封面" width="120" align="center">
          <template slot-scope="scope">
            <el-image
              v-if="scope.row.coverImage"
              :src="scope.row.coverImage"
              style="width: 100px; height: 56px; border-radius: 4px;"
              fit="cover"
            >
              <div slot="error" style="width:100px;height:56px;background:#f5f7fa;border-radius:4px;"></div>
            </el-image>
            <span v-else style="color:#c0c4cc;font-size:12px;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="200">
          <template slot-scope="scope">
            <el-link type="primary" :underline="false" @click="goArticle(scope.row.articleId)">
              {{ scope.row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="分类" prop="categoryName" width="120" />
        <el-table-column label="作者" prop="authorName" width="120" />
        <el-table-column label="浏览量" prop="viewCount" width="80" align="center" />
        <el-table-column label="置顶" width="70" align="center">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.isTop == '1'" type="warning" size="mini">置顶</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template slot-scope="scope">
            <span>{{ parseTime(scope.row.createTime) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        :page.sync="queryParams.pageNum"
        :limit.sync="queryParams.pageSize"
        @pagination="fetchDashboard"
      />
    </el-card>
  </div>
</template>

<script>
import CountTo from 'vue-count-to'
import { getDashboard } from '@/api/blog/dashboard'
import { listCategory } from '@/api/blog/category'
import echarts from 'echarts'

export default {
  name: 'Index',
  components: { CountTo },
  data() {
    return {
      loading: true,
      // 统计卡片
      totalArticles: 0,
      totalComments: 0,
      totalCategories: 0,
      totalTags: 0,
      todayViews: 0,
      pendingComments: 0,
      // 文章列表
      articleList: [],
      total: 0,
      categoryList: [],
      selectedCategory: null,
      queryParams: {
        pageNum: 1,
        pageSize: 5,
        categoryId: undefined
      },
      // 趋势图
      trend: [],
      trendChartInstance: null,
      // 最新评论
      recentComments: []
    }
  },
  created() {
    this.fetchDashboard()
    this.getCategoryList()
  },
  mounted() {
    // 给window绑定resize事件，图表自适应
    this.__resizeHandler = () => {
      if (this.trendChartInstance) {
        this.trendChartInstance.resize()
      }
    }
    window.addEventListener('resize', this.__resizeHandler)
  },
  beforeDestroy() {
    if (this.trendChartInstance) {
      this.trendChartInstance.dispose()
      this.trendChartInstance = null
    }
    if (this.__resizeHandler) {
      window.removeEventListener('resize', this.__resizeHandler)
    }
  },
  methods: {
    fetchDashboard() {
      this.loading = true
      const params = {
        pageNum: this.queryParams.pageNum,
        pageSize: this.queryParams.pageSize
      }
      if (this.selectedCategory) {
        params.categoryId = this.selectedCategory
      }

      getDashboard(params).then(res => {
        const data = res.data
        // 统计卡片
        this.totalArticles = data.totalArticles || 0
        this.totalComments = data.totalComments || 0
        this.totalCategories = data.totalCategories || 0
        this.totalTags = data.totalTags || 0
        this.todayViews = data.todayViews || 0
        this.pendingComments = data.pendingComments || 0
        // 文章列表
        this.articleList = data.articleList || []
        this.total = data.total || 0
        // 趋势数据
        this.trend = data.trend || []
        // 最新评论
        this.recentComments = data.recentComments || []

        this.loading = false

        // 图表渲染（nextTick确保DOM已更新）
        this.$nextTick(() => {
          this.initTrendChart()
        })
      })
    },
    getCategoryList() {
      listCategory({ pageNum: 1, pageSize: 99 }).then(res => {
        this.categoryList = res.rows || []
      })
    },
    filterByCategory(categoryId) {
      this.selectedCategory = categoryId
      this.queryParams.pageNum = 1
      this.fetchDashboard()
    },
    goArticle(id) {
      this.$router.push('/index/article/' + id)
    },
    goTo(route) {
      const map = {
        article: '/blog/article',
        comment: '/blog/comment',
        category: '/blog/category',
        tag: '/blog/tag'
      }
      if (map[route]) {
        this.$router.push(map[route])
      }
    },
    goToIfAdmin(route) {
      // 分类和标签管理仅管理员可访问，普通用户点击给出提示
      const roles = this.$store.state.user.roles || []
      const isAdminUser = roles.some(r => r === 'admin')
      if (!isAdminUser) {
        this.$message.warning('分类/标签管理仅限管理员操作')
        return
      }
      this.goTo(route)
    },
    initTrendChart() {
      if (!this.$refs.trendChart || this.trend.length === 0) return

      if (this.trendChartInstance) {
        this.trendChartInstance.dispose()
      }

      this.trendChartInstance = echarts.init(this.$refs.trendChart)

      const dates = this.trend.map(t => {
        // 只显示月-日
        const parts = t.date.split('-')
        return parts[1] + '/' + parts[2]
      })
      const counts = this.trend.map(t => t.count)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: '#e8e8e8' } },
          axisLabel: { color: '#666', fontSize: 12 }
        },
        yAxis: {
          type: 'value',
          minInterval: 1,
          splitLine: { lineStyle: { color: '#f0f0f0' } },
          axisLabel: { color: '#666' }
        },
        series: [{
          name: '发布文章',
          type: 'bar',
          data: counts,
          barWidth: '40%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#40c9c6' },
                { offset: 1, color: '#36a3f7' }
              ]
            }
          },
          emphasis: {
            itemStyle: {
              color: '#1890ff'
            }
          }
        }]
      }

      this.trendChartInstance.setOption(option)
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-editor-container {
  padding: 32px;
  background-color: rgb(240, 242, 245);

  .panel-group {
    margin-top: 0;

    .card-panel-col {
      margin-bottom: 32px;
    }

    .card-panel {
      height: 108px;
      font-size: 12px;
      position: relative;
      overflow: hidden;
      color: #666;
      background: #fff;
      box-shadow: 4px 4px 40px rgba(0, 0, 0, .05);
      border-color: rgba(0, 0, 0, .05);
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-3px);
        box-shadow: 4px 8px 24px rgba(0, 0, 0, .1);
      }

      .card-panel-icon-wrapper {
        float: left;
        margin: 14px 0 0 14px;
        padding: 16px;
        transition: all 0.3s;
        border-radius: 6px;
      }

      .card-panel-icon {
        float: left;
        font-size: 48px;
      }

      .card-panel-description {
        float: right;
        font-weight: bold;
        margin: 26px;
        margin-left: 0px;

        .card-panel-text {
          line-height: 18px;
          color: rgba(0, 0, 0, 0.45);
          font-size: 16px;
          margin-bottom: 12px;
        }

        .card-panel-num {
          font-size: 20px;
        }
      }

      .pending-tag {
        position: absolute;
        top: 8px;
        right: 8px;
      }
    }

    // 卡片图标颜色
    .card-panel-articles {
      .card-panel-icon-wrapper { background: #40c9c6; }
      .card-panel-icon { color: #fff; }
    }
    .card-panel-comments {
      .card-panel-icon-wrapper { background: #36a3f7; }
      .card-panel-icon { color: #fff; }
    }
    .card-panel-categories {
      .card-panel-icon-wrapper { background: #34bfa3; }
      .card-panel-icon { color: #fff; }
    }
    .card-panel-tags {
      .card-panel-icon-wrapper { background: #f4516c; }
      .card-panel-icon { color: #fff; }
    }
  }

  // 评论列表
  .comment-list {
    max-height: 280px;
    overflow-y: auto;

    .comment-item {
      padding: 10px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child { border-bottom: none; }

      .comment-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;

        .comment-author {
          font-weight: bold;
          color: #333;
          font-size: 13px;
        }
      }

      .comment-content {
        color: #666;
        font-size: 13px;
        line-height: 1.5;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .comment-footer {
        display: flex;
        justify-content: space-between;
        font-size: 12px;

        .comment-article {
          color: #1890ff;
          cursor: pointer;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 150px;

          &:hover { color: #40a9ff; }
        }

        .comment-time {
          color: #999;
          flex-shrink: 0;
        }
      }
    }
  }
}
</style>