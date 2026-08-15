<template>
  <div class="article-detail-container">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <el-button type="text" icon="el-icon-arrow-left" @click="$router.push('/blog-front')">返回博客首页</el-button>
    </div>

    <!-- 文章内容 -->
    <div class="article-card" v-if="article">
      <h1 class="article-title">{{ article.title }}</h1>
      <div class="article-meta">
        <span><i class="el-icon-user"></i> {{ article.authorName || '匿名' }}</span>
        <span><i class="el-icon-time"></i> {{ article.createTime ? article.createTime.slice(0, 10) : '' }}</span>
        <span><i class="el-icon-view"></i> {{ article.viewCount || 0 }} 次阅读</span>
        <el-tag v-if="article.categoryName" size="small" type="success">{{ article.categoryName }}</el-tag>
      </div>
      <div class="article-content" v-html="article.content"></div>
    </div>

    <!-- 评论区 -->
    <div class="comment-section">
      <h3 class="section-title">评论（{{ comments.length }}）</h3>

      <!-- 发表评论 -->
      <div class="comment-form">
        <el-input
          type="textarea"
          :rows="3"
          v-model="commentForm.content"
          placeholder="写下你的评论..."
          maxlength="500"
          show-word-limit
        ></el-input>
        <div class="comment-form-footer">
          <span class="comment-tip" v-if="replyTo">回复 @{{ replyTo.authorName }}：</span>
          <el-button type="primary" size="small" @click="submitComment" :loading="submitting">
            {{ replyTo ? '回复' : '发表评论' }}
          </el-button>
          <el-button v-if="replyTo" size="small" @click="cancelReply">取消回复</el-button>
        </div>
      </div>

      <!-- 评论列表 -->
      <div class="comment-list">
        <div v-for="item in comments" :key="item.commentId" class="comment-item">
          <div class="comment-avatar">
            <el-avatar :size="36">{{ item.authorName ? item.authorName[0] : '?' }}</el-avatar>
          </div>
          <div class="comment-body">
            <div class="comment-header">
              <span class="comment-author">{{ item.authorName || '匿名' }}</span>
              <span class="comment-time">{{ item.createTime ? item.createTime.slice(0, 16) : '' }}</span>
            </div>
            <div class="comment-content">{{ item.content }}</div>
            <div class="comment-actions">
              <span class="comment-action" @click="replyComment(item)">回复</span>
            </div>
            <!-- 子评论（回复） -->
            <div v-if="item.children && item.children.length" class="reply-list">
              <div v-for="reply in item.children" :key="reply.commentId" class="reply-item">
                <div class="reply-header">
                  <span class="reply-author">{{ reply.authorName || '匿名' }}</span>
                  <span class="reply-time">{{ reply.createTime ? reply.createTime.slice(0, 16) : '' }}</span>
                </div>
                <div class="reply-content">
                  <span v-if="reply.parentAuthorName" class="at-user">@{{ reply.parentAuthorName }} </span>
                  {{ reply.content }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="comments.length === 0" class="empty-comment">
          <el-empty description="暂无评论，来说两句吧"></el-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getArticle } from "@/api/blog/front";
import { listCommentByArticle, addComment } from "@/api/blog/comment";

export default {
  name: "BlogFrontArticle",
  data() {
    return {
      article: null,
      comments: [],
      commentForm: {
        articleId: null,
        content: '',
        parentId: null
      },
      replyTo: null,
      submitting: false,
      articleId: null
    };
  },
  created() {
    this.loadData()
  },
  watch: {
    '$route.params.id': function(newId, oldId) {
      if (newId && newId !== oldId) {
        this.loadData()
      }
    }
  },
  methods: {
    loadData() {
      this.articleId = parseInt(this.$route.params.id)
      this.commentForm.articleId = this.articleId
      this.loadArticle()
      this.loadComments()
    },
    loadArticle() {
      getArticle(this.articleId).then(res => {
        // API 返回格式: { code: 200, data: {...} }
        const articleData = res && res.data ? res.data : null
        if (!articleData) {
          this.$message.error('文章不存在')
          this.$router.push('/blog-front')
          return
        }
        this.article = articleData
      }).catch(() => {
        this.$message.error('文章加载失败')
        this.$router.push('/blog-front')
      });
    },
    loadComments() {
      listCommentByArticle(this.articleId).then(res => {
        let list = (res && res.data) ? res.data : [];
        // 构建树形结构：parent_id 为空的是一级评论
        let map = {};
        let roots = [];
        list.forEach(item => {
          item.children = [];
          map[item.commentId] = item;
        });
        list.forEach(item => {
          if (item.parentId) {
            if (map[item.parentId]) {
              map[item.parentId].children.push(item);
            } else {
              // 父评论不存在也作为一级
              roots.push(item);
            }
          } else {
            roots.push(item);
          }
        });
        this.comments = roots;
      });
    },
    submitComment() {
      if (!this.commentForm.content.trim()) {
        this.$message.warning('请输入评论内容');
        return;
      }
      this.submitting = true;
      addComment(this.commentForm).then(() => {
        this.$message.success('评论成功，待审核后显示');
        this.commentForm.content = '';
        this.commentForm.parentId = null;
        this.replyTo = null;
        this.loadComments();
      }).catch(() => {
        this.$message.error('评论失败');
      }).finally(() => {
        this.submitting = false;
      });
    },
    replyComment(item) {
      this.replyTo = item;
      this.commentForm.parentId = item.commentId;
      // 滚动到评论区
      window.scrollTo({ top: document.querySelector('.comment-form').offsetTop - 100, behavior: 'smooth' });
    },
    cancelReply() {
      this.replyTo = null;
      this.commentForm.parentId = null;
    }
  }
};
</script>

<style scoped>
.article-detail-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}
.back-bar {
  margin-bottom: 16px;
}
.article-card {
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 20px;
}
.article-title {
  font-size: 26px;
  color: #303133;
  margin: 0 0 16px;
}
.article-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}
.article-meta i {
  margin-right: 4px;
}
.article-content {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
}
.article-content img {
  max-width: 100%;
  border-radius: 4px;
}

/* 评论区 */
.comment-section {
  background: #fff;
  border-radius: 8px;
  padding: 24px 32px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.section-title {
  font-size: 18px;
  color: #303133;
  margin: 0 0 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}
.comment-form {
  margin-bottom: 24px;
}
.comment-form-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}
.comment-tip {
  font-size: 13px;
  color: #909399;
  flex: 1;
}
.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}
.comment-avatar {
  flex-shrink: 0;
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}
.comment-time {
  font-size: 12px;
  color: #c0c4cc;
}
.comment-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 6px;
}
.comment-actions {
  font-size: 13px;
  color: #909399;
}
.comment-action {
  cursor: pointer;
  margin-right: 16px;
}
.comment-action:hover {
  color: #409eff;
}
.reply-list {
  margin-top: 10px;
  padding-left: 12px;
  border-left: 3px solid #e4e7ed;
  background: #fafafa;
  border-radius: 4px;
}
.reply-item {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.reply-item:last-child {
  border-bottom: none;
}
.reply-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.reply-author {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
}
.reply-time {
  font-size: 12px;
  color: #c0c4cc;
}
.reply-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
}
.at-user {
  color: #409eff;
}
.empty-comment {
  padding: 30px 0;
}
</style>