<template>
  <div class="blog-front-container">
    <!-- 头部 -->
    <div class="blog-header">
      <h1 class="blog-title">个人博客</h1>
      <p class="blog-subtitle">分享技术，记录生活</p>
    </div>

    <!-- 文章列表 -->
    <div class="blog-content">
      <div class="article-list">
        <div v-for="item in articleList" :key="item.articleId" class="article-card" @click="goArticle(item.articleId)">
          <div class="article-body">
            <h2 class="article-title">{{ item.title }}</h2>
            <p class="article-summary">{{ item.summary || '暂无摘要' }}</p>
            <div class="article-meta">
              <span class="meta-item">
                <i class="el-icon-user"></i> {{ item.authorName || '匿名' }}
              </span>
              <span class="meta-item">
                <i class="el-icon-time"></i> {{ item.createTime ? item.createTime.slice(0, 10) : '' }}
              </span>
              <span class="meta-item">
                <i class="el-icon-view"></i> {{ item.viewCount || 0 }} 次阅读
              </span>
              <span class="meta-item">
                <i class="el-icon-chat-dot-round"></i> {{ item.commentCount || 0 }} 条评论
              </span>
              <el-tag v-if="item.categoryName" size="small" type="success">{{ item.categoryName }}</el-tag>
            </div>
          </div>
        </div>
        <div v-if="articleList.length === 0" class="empty-tip">
          <el-empty description="暂无文章"></el-empty>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="total > 0">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="queryParams.pageSize"
          :current-page.sync="queryParams.pageNum"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { listPubArticle } from "@/api/blog/front";

export default {
  name: "BlogFront",
  data() {
    return {
      articleList: [],
      total: 0,
      queryParams: {
        pageNum: 1,
        pageSize: 10
      }
    };
  },
  created() {
    this.getList();
  },
  methods: {
    getList() {
      listPubArticle(this.queryParams).then(res => {
        this.articleList = res.rows || [];
        this.total = res.total || 0;
      });
    },
    handlePageChange(page) {
      this.queryParams.pageNum = page;
      this.getList();
    },
    goArticle(id) {
      this.$router.push('/blog-front/article/' + id);
    }
  }
};
</script>

<style scoped>
.blog-front-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}
.blog-header {
  text-align: center;
  padding: 40px 0 30px;
}
.blog-title {
  font-size: 32px;
  color: #303133;
  margin: 0;
}
.blog-subtitle {
  color: #909399;
  margin-top: 8px;
  font-size: 14px;
}
.article-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 20px 24px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.article-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}
.article-title {
  font-size: 20px;
  color: #303133;
  margin: 0 0 10px;
}
.article-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.article-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #909399;
}
.meta-item i {
  margin-right: 4px;
}
.empty-tip {
  padding: 60px 0;
}
.pagination-wrap {
  text-align: center;
  padding: 20px 0;
}
</style>
