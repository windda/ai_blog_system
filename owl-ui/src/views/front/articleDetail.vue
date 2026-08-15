<template>
  <div class="front-article-detail">
    <!-- 顶部导航 -->
    <header class="front-header">
      <div class="header-inner">
        <div class="logo"><h1 @click="goHome">📝 个人技术博客</h1></div>
        <nav class="nav-menu">
          <a @click="goHome">首页</a>
          <a v-if="article && article.categoryName" style="color:#1890ff;">{{ article.categoryName }}</a>
          <a v-if="isLoggedIn && !isAdmin" class="profile-link" @click="goProfile">👤 个人中心</a>
          <a v-if="isAdmin" @click="goAdmin" class="admin-link">后台管理</a>
        </nav>
      </div>
    </header>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-container"><el-skeleton :rows="10" animated /></div>

    <!-- 加载失败 / 文章不存在 -->
    <div v-else-if="loadError" class="error-container">
      <el-empty description="文章不存在或已被删除">
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </el-empty>
    </div>

    <!-- 文章内容 -->
    <div class="article-body" v-else-if="article">
      <div class="container">
        <div class="article-main">
          <article class="article-card">
            <h1 class="article-title">{{ article.title }}</h1>
            <div class="article-meta">
              <span><i class="el-icon-user"></i> {{ article.authorName || '匿名' }}</span>
              <span><i class="el-icon-time"></i> {{ article.createTime ? article.createTime.slice(0, 10) : '' }}</span>
              <span><i class="el-icon-view"></i> {{ article.viewCount || 0 }} 次阅读</span>
              <el-tag v-if="article.categoryName" size="small" type="success">{{ article.categoryName }}</el-tag>
            </div>
            <div class="article-cover" v-if="article.coverImage">
              <img :src="resolveImageUrl(article.coverImage)" :alt="article.title">
            </div>
            <div class="article-content" v-html="article.content" ref="articleContent"></div>
            <!-- 文章底部操作栏 -->
            <div class="article-actions">
              <!-- 点赞按钮：仅登录用户可见 -->
              <div class="like-area" v-if="isLoggedIn">
                <el-button
                  :type="liked ? 'danger' : 'default'"
                  :icon="liked ? 'el-icon-star-on' : 'el-icon-star-off'"
                  :loading="likeLoading"
                  @click="handleLike"
                >
                  {{ liked ? '已点赞' : '点赞' }} ({{ likeCount }})
                </el-button>
                <!-- 收藏按钮 -->
                <el-button
                  :type="collected ? 'warning' : 'default'"
                  :icon="collected ? 'el-icon-star-on' : 'el-icon-star-off'"
                  :loading="collectLoading"
                  @click="handleCollect"
                  style="margin-left:8px;"
                >
                  {{ collected ? '已收藏' : '收藏' }}
                </el-button>
              </div>
              <!-- 点赞用户列表：全部访问者可见 -->
              <div class="like-area" v-if="likeCount > 0">
                <el-button type="text" size="small" @click="showLikeUsers">
                  已有 {{ likeCount }} 人点赞，查看详情
                </el-button>
              </div>
              <!-- 点赞用户列表弹窗 -->
              <el-dialog title="点赞用户" :visible.sync="likeUsersVisible" width="400px" append-to-body>
                <div class="like-users-list">
                  <div class="like-user-item" v-for="user in likeUsers" :key="user.userId">
                    <el-avatar :size="32" style="margin-right: 10px;">{{ (user.nickName || '?')[0] }}</el-avatar>
                    <span>{{ user.nickName || '匿名用户' }}</span>
                    <span style="margin-left: auto; font-size: 12px; color: #999;">{{ user.createTime ? user.createTime.slice(0, 10) : '' }}</span>
                  </div>
                </div>
                <el-empty v-if="likeUsers.length === 0" description="暂无点赞" :image-size="60"></el-empty>
              </el-dialog>
            </div>
            <div class="article-tags" v-if="article.tags && article.tags.length">
              <span class="tag-label">标签：</span>
              <el-tag v-for="tag in article.tags" :key="tag.tagId" size="small" style="margin-right: 8px;">{{ tag.tagName }}</el-tag>
            </div>
          </article>

          <!-- 作者信息卡片 -->
          <div class="author-card" v-if="article.authorName">
            <div class="author-avatar">
              <el-avatar :size="56">{{ (article.authorName || '?')[0] }}</el-avatar>
            </div>
            <div class="author-info">
              <div class="author-name">{{ article.authorName }}</div>
              <div class="author-desc">技术博客作者</div>
            </div>
          </div>

          <!-- 相关推荐 -->
          <div class="related-section" v-if="relatedArticles.length > 0">
            <h3 class="section-title">📖 相关推荐</h3>
            <div class="related-list">
              <div class="related-item" v-for="item in relatedArticles" :key="item.articleId" @click="goArticle(item.articleId)">
                <div class="related-cover" v-if="item.coverImage">
                  <img :src="resolveImageUrl(item.coverImage)" :alt="item.title" loading="lazy">
                </div>
                <div class="related-info">
                  <div class="related-title">{{ item.title }}</div>
                  <div class="related-meta">
                    <span><i class="el-icon-view"></i> {{ item.viewCount || 0 }}</span>
                    <span>{{ item.createTime ? item.createTime.slice(0, 10) : '' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 评论 -->
          <div class="comment-section">
            <h3 class="section-title">💬 评论（{{ comments.length }}）</h3>
            <div class="comment-form" v-if="isLoggedIn">
              <el-input type="textarea" :rows="3" v-model="commentForm.content" placeholder="写下你的评论..." maxlength="500" show-word-limit />
              <div class="comment-form-actions">
                <span class="login-as">评论身份：{{ userName }}</span>
                <el-button type="primary" size="small" @click="submitComment" :loading="submitting">发表评论</el-button>
              </div>
            </div>
            <div class="comment-form" v-else>
              <el-alert title="请先登录后再发表评论" type="info" :closable="false" show-icon>
                <el-button type="text" style="margin-left: 8px;" @click="$router.push('/login')">去登录</el-button>
                <el-button type="text" style="margin-left: 4px;" @click="$router.push('/register')">去注册</el-button>
              </el-alert>
            </div>
            <div class="comments-list">
              <div class="comment-item" v-for="comment in comments" :key="comment.commentId">
                <div class="comment-avatar"><el-avatar :size="36">{{ (comment.authorName || '?')[0] }}</el-avatar></div>
                <div class="comment-body">
                  <div class="comment-header">
                    <span class="comment-author">{{ comment.authorName || '用户' }}</span>
                    <span class="comment-time">{{ comment.createTime ? comment.createTime.slice(0, 16) : '' }}</span>
                  </div>
                  <div class="comment-content">{{ comment.content }}</div>
                </div>
              </div>
            </div>
            <el-empty v-if="comments.length === 0" description="暂无评论，来发表第一条吧~" :image-size="80"></el-empty>
          </div>
        </div>

        <aside class="sidebar">
          <div class="widget">
            <h3 class="widget-title">📂 分类</h3>
            <div class="category-side-list">
              <div class="category-side-item" v-for="cat in categoryList" :key="cat.categoryId" @click="goCategory(cat)">
                <span>{{ cat.categoryName }}</span>
                <el-tag size="mini" type="info">{{ cat.articleCount }}</el-tag>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>

    <footer class="front-footer">
      <p>Copyright © 2026 个人技术博客AI系统 All Rights Reserved.</p>
    </footer>
  </div>
</template>

<script>
import { getFrontArticle, getFrontCategories, getRelatedArticles, likeArticle, getLikeStatus, getLikeUsers, collectArticle, getCollectStatus, recordFrontHistory } from '@/api/blog/front'
import { addComment, listCommentByArticle } from '@/api/blog/comment'
import { getToken } from '@/utils/auth'

export default {
  name: 'FrontArticleDetail',
  data() {
    return {
      loading: true,
      loadError: false,
      article: null,
      comments: [],
      categoryList: [],
      relatedArticles: [],
      commentForm: { content: '' },
      submitting: false,
      likeLoading: false, liked: false, likeCount: 0,
      likeUsers: [], likeUsersVisible: false,
      collectLoading: false, collected: false
    }
  },
  computed: {
    isLoggedIn() { return !!getToken() },
    isAdmin() { return this.$store.state.user?.roles?.includes('admin') },
    userName() { return this.$store.state.user?.name || '已登录用户' }
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
      this.fetchArticle()
      this.fetchCategories()
      this.fetchComments()
      this.fetchRelated()
      this.fetchLikeStatus()
      this.fetchCollectStatus()
      this.recordHistory()
    },
    async fetchCollectStatus() {
      try {
        const id = this.$route.params.id
        const res = await getCollectStatus(id)
        if (res && res.code === 200 && res.data) {
          this.collected = res.data.collected
        }
      } catch (e) {}
    },
    async handleCollect() {
      if (this.collectLoading) return
      this.collectLoading = true
      try {
        const id = this.$route.params.id
        const res = await collectArticle(id)
        if (res && res.code === 200 && res.data) {
          this.collected = res.data.collected
          this.$message.success(this.collected ? '已收藏' : '已取消收藏')
        }
      } catch (e) { this.$message.error('操作失败') }
      this.collectLoading = false
    },
    async recordHistory() {
      try {
        const id = this.$route.params.id
        await recordFrontHistory(id)
      } catch (e) {}
    },
    async fetchLikeStatus() {
      try {
        const id = this.$route.params.id
        const res = await getLikeStatus(id)
        if (res && res.code === 200 && res.data) {
          this.liked = res.data.liked
          this.likeCount = res.data.likeCount || 0
        }
      } catch (e) { /* 未登录或接口异常，保持默认未点赞状态 */ }
    },
    async showLikeUsers() {
      this.likeUsersVisible = true
      try {
        const id = this.$route.params.id
        const res = await getLikeUsers(id)
        if (res && res.data) {
          this.likeUsers = res.data || []
        }
      } catch (e) { /* ignore */ }
    },
    async fetchArticle() {
      this.loading = true
      this.loadError = false
      try {
        const id = this.$route.params.id
        const res = await getFrontArticle(id)
        const articleData = res && res.data ? res.data : null
        this.article = articleData
        if (!articleData) {
          this.loadError = true
        }
      } catch (e) {
        console.error('获取文章详情失败:', e)
        this.loadError = true
      } finally {
        this.loading = false
      }
    },
    async handleLike() {
      if (this.likeLoading) return
      this.likeLoading = true
      try {
        const id = this.$route.params.id
        const res = await likeArticle(id)
        if (res && res.code === 200 && res.data) {
          // 同步更新点赞状态和数量（后端返回 {liked, likeCount}）
          this.liked = res.data.liked
          this.likeCount = res.data.likeCount
          this.$message.success(this.liked ? '点赞成功' : '已取消点赞')
        }
      } catch (e) {
        this.$message.error('点赞失败，请稍后重试')
      } finally {
        this.likeLoading = false
      }
    },
    async fetchComments() {
      try { const id = this.$route.params.id; const res = await listCommentByArticle(id); this.comments = (res && res.data) ? res.data : [] } catch (e) { this.comments = [] }
    },
    async fetchCategories() {
      try { const res = await getFrontCategories(); this.categoryList = (res && res.data) ? res.data : [] } catch (e) {}
    },
    async fetchRelated() {
      try { const id = this.$route.params.id; const res = await getRelatedArticles(id); this.relatedArticles = (res && res.data) ? res.data : [] } catch (e) {}
    },
    async submitComment() {
      if (!this.isLoggedIn) return this.$message.warning('请先登录后再评论')
      if (!this.commentForm.content.trim()) return this.$message.warning('请输入评论内容')
      this.submitting = true
      try { await addComment({ articleId: parseInt(this.$route.params.id), content: this.commentForm.content }); this.$message.success('评论发表成功'); this.commentForm.content = ''; this.fetchComments() } catch (e) { this.$message.error('评论失败') }
      this.submitting = false
    },
    goHome() { this.$router.push('/') },
    goProfile() { this.$router.push('/profile') },
    goAdmin() { this.$router.push('/index') },
    goArticle(id) { this.$router.push('/article/' + id) },
    goCategory(cat) { this.$router.push('/?categoryId=' + cat.categoryId) },
    resolveImageUrl(path) { if (!path) return ''; if (path.startsWith('http')) return path; return process.env.VUE_APP_BASE_API + path }
  }
}
</script>

<style scoped>
.front-article-detail { min-height: 100vh; background: #f5f7fa; }
.front-header { background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); position: sticky; top: 0; z-index: 100; }
.header-inner { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; height: 60px; }
.logo h1 { margin: 0; font-size: 22px; color: #333; cursor: pointer; }
.nav-menu a { margin-left: 24px; color: #666; text-decoration: none; font-size: 15px; cursor: pointer; }
.nav-menu a:hover { color: #1890ff; }
.nav-menu .admin-link { color: #1890ff; font-weight: bold; }
.article-body { max-width: 1200px; margin: 24px auto; padding: 0 20px; }
.container { display: flex; gap: 24px; }
.article-main { flex: 1; min-width: 0; }
.article-card { background: #fff; border-radius: 8px; padding: 32px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.article-title { margin: 0 0 16px; font-size: 28px; color: #333; line-height: 1.4; }
.article-meta { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; font-size: 14px; color: #999; }
.article-meta i { margin-right: 4px; }
.article-cover { margin-bottom: 24px; }
.article-cover img { width: 100%; max-height: 400px; object-fit: cover; border-radius: 8px; }
.article-content { font-size: 16px; line-height: 1.8; color: #333; overflow: hidden; word-break: break-word; }
.article-content ::v-deep pre { background: #282c34; color: #abb2bf; padding: 20px; border-radius: 8px; overflow-x: auto; font-size: 14px; line-height: 1.6; margin: 16px 0; }
.article-content ::v-deep code { font-family: 'Consolas', 'Monaco', 'Courier New', monospace; }
.article-content ::v-deep p code { background: #f0f0f0; color: #e74c3c; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
.article-content ::v-deep img { max-width: 100%; height: auto; border-radius: 6px; margin: 12px 0; }
.article-content ::v-deep blockquote { border-left: 4px solid #1890ff; padding: 10px 20px; margin: 16px 0; background: #f0f7ff; color: #555; }
.article-content ::v-deep table { border-collapse: collapse; width: 100%; margin: 16px 0; }
.article-content ::v-deep th, .article-content ::v-deep td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
.article-content ::v-deep th { background: #f5f5f5; font-weight: bold; }
.article-actions { display: flex; justify-content: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #f0f0f0; }
.article-tags { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.tag-label { font-size: 14px; color: #999; margin-right: 8px; }
.author-card { display: flex; align-items: center; gap: 16px; background: #fff; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.author-name { font-size: 16px; font-weight: bold; color: #333; }
.author-desc { font-size: 13px; color: #999; margin-top: 4px; }
.related-section { background: #fff; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.related-list { display: flex; flex-direction: column; gap: 12px; }
.related-item { display: flex; gap: 12px; cursor: pointer; padding: 8px; border-radius: 6px; transition: background 0.2s; }
.related-item:hover { background: #f5f7fa; }
.related-cover { width: 100px; height: 66px; flex-shrink: 0; border-radius: 4px; overflow: hidden; }
.related-cover img { width: 100%; height: 100%; object-fit: cover; }
.related-info { flex: 1; min-width: 0; }
.related-title { font-size: 15px; color: #333; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.related-meta { display: flex; gap: 12px; font-size: 12px; color: #999; margin-top: 4px; }
.comment-section { background: #fff; border-radius: 8px; padding: 24px; margin-top: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.section-title { margin: 0 0 20px; font-size: 18px; color: #333; }
.comment-form { margin-bottom: 24px; }
.comment-form-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.login-as { font-size: 13px; color: #909399; }
.comment-item { display: flex; gap: 12px; padding: 16px 0; border-bottom: 1px solid #f0f0f0; }
.comment-body { flex: 1; }
.comment-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.comment-author { font-weight: bold; color: #333; font-size: 14px; }
.comment-time { color: #999; font-size: 12px; }
.comment-content { color: #666; font-size: 14px; line-height: 1.5; }
.sidebar { width: 280px; flex-shrink: 0; }
.widget { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.widget-title { margin: 0 0 16px; font-size: 16px; color: #333; padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; }
.category-side-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; cursor: pointer; font-size: 14px; }
.category-side-item:hover { color: #1890ff; }
.loading-container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
.error-container { max-width: 600px; margin: 80px auto; padding: 0 20px; text-align: center; }
.front-footer { text-align: center; padding: 32px; color: #999; font-size: 13px; border-top: 1px solid #eee; margin-top: 40px; }
@media (max-width: 768px) { .container { flex-direction: column; } .sidebar { width: 100%; } }
</style>
