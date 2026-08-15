<template>
  <div class="front-blog">
    <header class="front-header">
      <div class="header-inner">
        <div class="logo"><h1 @click="goHome">📝 个人技术博客</h1></div>
        <button class="mobile-menu-btn" @click="showMobileMenu = !showMobileMenu"><span></span><span></span><span></span></button>
        <nav class="nav-menu" :class="{ open: showMobileMenu }">
          <a :class="{ active: currentTab === 'home' }" @click="switchTab('home'); showMobileMenu = false">首页</a>
          <a :class="{ active: currentTab === 'categories' }" @click="switchTab('categories'); showMobileMenu = false">分类</a>
          <a :class="{ active: currentTab === 'tags' }" @click="switchTab('tags'); showMobileMenu = false">标签</a>
          <template v-if="isLoggedIn">
            <a class="notice-bell" @click="showNotices = true">
              🔔<span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </a>
            <a v-if="!isAdmin" class="profile-link" @click="goProfile">👤 个人中心</a>
            <a class="ai-link" @click="goAiChat">🤖 AI 助手</a>
            <a v-if="isAdmin" class="admin-link" @click="goAdmin">后台管理</a>
            <a class="logout-link" @click="handleLogout">退出</a>
          </template>
          <template v-else>
            <a class="login-link" @click="goLogin">登录</a>
            <a class="register-link" @click="goRegister">注册</a>
          </template>
        </nav>
      </div>
    </header>

    <div class="front-body">
      <div class="container">
        <div class="main-content">
          <div v-if="currentTab === 'home'" v-loading="loading">
            <article class="article-card" v-for="article in articleList" :key="article.articleId" @click="goArticle(article.articleId)">
              <div class="article-cover" v-if="article.coverImage"><img :src="resolveImageUrl(article.coverImage)" :alt="article.title"></div>
              <div class="article-info">
                <h2 class="article-title">{{ article.title }}</h2>
                <div class="article-meta">
                  <span class="meta-item"><i class="el-icon-user"></i> {{ article.authorName || '匿名' }}</span>
                  <span class="meta-item"><i class="el-icon-time"></i> {{ article.createTime ? article.createTime.slice(0, 10) : '' }}</span>
                  <span class="meta-item" v-if="article.categoryName"><i class="el-icon-collection-tag"></i> {{ article.categoryName }}</span>
                  <span class="meta-item"><i class="el-icon-view"></i> {{ article.viewCount || 0 }}</span>
                </div>
                <div class="article-tags-row" v-if="article.tags && article.tags.length">
                  <el-tag v-for="tag in article.tags" :key="tag.tagId" size="mini" effect="plain" style="margin-right: 6px;">{{ tag.tagName }}</el-tag>
                </div>
                <p class="article-summary">{{ article.summary || '暂无摘要' }}</p>
              </div>
            </article>
            <el-empty v-if="!loading && articleList.length === 0" description="暂无文章"></el-empty>
            <div class="pagination-wrapper" v-if="total > 0"><el-pagination background layout="prev, pager, next" :total="total" :page-size="queryParams.pageSize" :current-page.sync="queryParams.pageNum" @current-change="fetchArticles" /></div>
          </div>
          <div v-if="currentTab === 'categories'" v-loading="loading">
            <h2 class="section-title">文章分类</h2>
            <div class="category-list">
              <div class="category-card" v-for="cat in categoryList" :key="cat.categoryId" @click="filterByCategory(cat)"><div class="category-name">{{ cat.categoryName }}</div><div class="category-count">{{ cat.articleCount }} 篇文章</div></div>
            </div>
            <el-empty v-if="!loading && categoryList.length === 0" description="暂无分类"></el-empty>
          </div>
          <div v-if="currentTab === 'tags'" v-loading="loading">
            <h2 class="section-title">标签云</h2>
            <div class="tag-cloud"><el-tag v-for="tag in tagList" :key="tag.tagId" :type="tagTypes[tag.tagId % tagTypes.length]" size="medium" effect="plain" class="tag-item">{{ tag.tagName }}</el-tag></div>
            <el-empty v-if="!loading && tagList.length === 0" description="暂无标签"></el-empty>
          </div>
        </div>

        <aside class="sidebar">
          <div class="widget search-widget"><el-input placeholder="搜索文章..." v-model="keyword" size="medium" @keyup.enter.native="searchArticles"><el-button slot="append" icon="el-icon-search" @click="searchArticles"></el-button></el-input></div>
          <div class="widget" v-if="siteNotice">
            <h3 class="widget-title">📢 公告</h3>
            <div class="notice-content" v-html="siteNotice"></div>
          </div>
          <div class="widget">
            <h3 class="widget-title">📋 关于本站</h3>
            <div class="about-content"><p>个人技术博客，分享编程经验与技术思考。</p><p style="color:#909399;font-size:12px;margin-top:4px;">🚀 Flask + Vue 全栈项目实战</p></div>
          </div>
          <div class="widget">
            <h3 class="widget-title">🔥 热门文章</h3>
            <div class="hot-list">
              <div class="hot-item" v-for="(article, index) in hotArticles" :key="article.articleId" @click="goArticle(article.articleId)"><span class="hot-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span><span class="hot-title">{{ article.title }}</span></div>
            </div>
            <el-empty v-if="hotArticles.length === 0" description="暂无数据" :image-size="60"></el-empty>
          </div>
          <div class="widget">
            <h3 class="widget-title">📂 分类</h3>
            <div class="category-side-list"><div class="category-side-item" v-for="cat in categoryList" :key="cat.categoryId" @click="filterByCategory(cat)"><span>{{ cat.categoryName }}</span><el-tag size="mini" type="info">{{ cat.articleCount }}</el-tag></div></div>
          </div>
          <div class="widget">
            <h3 class="widget-title">🔗 友情链接</h3>
            <div class="friend-link-list">
              <div v-for="link in friendLinks" :key="link.linkId"><a :href="link.linkUrl" target="_blank" class="friend-link">{{ link.linkName }}</a></div>
              <span v-if="friendLinks.length === 0" style="font-size:12px;color:#999;">暂无友链</span>
            </div>
          </div>
        </aside>
      </div>
    </div>

    <!-- 通知弹窗 -->
    <el-dialog title="消息通知" :visible.sync="showNotices" width="480px" append-to-body>
      <div class="notice-list">
        <div v-for="n in notices" :key="n.noticeId" class="notice-item" :class="{ unread: !n.isRead }" @click="readNotice(n)">
          <div class="notice-msg">{{ n.message }}</div>
          <div class="notice-time">{{ (n.createTime || '').slice(0, 16) }}</div>
        </div>
      </div>
      <el-empty v-if="notices.length === 0" description="暂无通知" :image-size="60"></el-empty>
      <span slot="footer">
        <el-button size="small" @click="markAllRead">全部已读</el-button>
      </span>
    </el-dialog>

    <footer class="front-footer"><p>Copyright © 2026 个人技术博客AI系统 All Rights Reserved.</p></footer>
  </div>
</template>

<script>
import { getFrontArticles, getHotArticles, getFrontCategories, getFrontTags } from '@/api/blog/front'
import { getToken, removeToken } from '@/utils/auth'
import request from '@/utils/request'

export default {
  name: 'FrontBlog',
  data() {
    return {
      loading: false, currentTab: 'home', showMobileMenu: false,
      articleList: [], total: 0,
      queryParams: { pageNum: 1, pageSize: 5, keyword: undefined, categoryId: undefined },
      hotArticles: [], categoryList: [], tagList: [], keyword: '', selectedCategory: null,
      tagTypes: ['', 'success', 'info', 'warning', 'danger'], searchTimer: null,
      siteNotice: '', friendLinks: [],
      unreadCount: 0, notices: [], showNotices: false
    }
  },
  computed: {
    isLoggedIn() { return !!getToken() },
    isAdmin() { return this.$store.state.user?.roles?.includes('admin') },
    userName() { return this.$store.state.user?.name || '' }
  },
  created() {
    const urlCategoryId = this.$route.query.categoryId
    if (urlCategoryId) this.queryParams.categoryId = parseInt(urlCategoryId)
    this.fetchArticles(); this.fetchHotArticles(); this.fetchCategories(); this.fetchTags()
    this.fetchNotice(); this.fetchFriendLinks()
    if (this.isLoggedIn) { this.fetchUnreadCount(); this.fetchNotices() }
  },
  methods: {
    async fetchArticles() { this.loading = true; try { const res = await getFrontArticles({ ...this.queryParams }); this.articleList = res.rows || []; this.total = res.total || 0 } catch (e) {} this.loading = false },
    async fetchHotArticles() { try { const res = await getHotArticles({ limit: 5 }); this.hotArticles = res.data || [] } catch (e) {} },
    async fetchCategories() { try { const res = await getFrontCategories(); this.categoryList = res.data || [] } catch (e) {} },
    async fetchTags() { try { const res = await getFrontTags(); this.tagList = res.data || [] } catch (e) {} },
    async fetchNotice() { try { const res = await request({ url: '/front/notice', method: 'get' }); if (res && res.data) { this.siteNotice = res.data.noticeContent || '' } } catch (e) {} },
    async fetchFriendLinks() { try { const res = await request({ url: '/front/friend-links', method: 'get' }); this.friendLinks = (res && res.data) ? res.data : [] } catch (e) {} },
    async fetchUnreadCount() { try { const res = await request({ url: '/front/user/notices/unread-count', method: 'get' }); this.unreadCount = (res && res.data) ? (res.data.count || 0) : 0 } catch (e) {} },
    async fetchNotices() { try { const res = await request({ url: '/front/user/notices', method: 'get', params: { pageSize: 20 } }); this.notices = (res && res.rows) ? res.rows : [] } catch (e) {} },
    async readNotice(n) { if (!n.isRead) { try { await request({ url: '/front/user/notice/' + n.noticeId + '/read', method: 'put' }); n.isRead = true; this.unreadCount = Math.max(0, this.unreadCount - 1) } catch (e) {} } },
    async markAllRead() { try { await request({ url: '/front/user/notices/read-all', method: 'post' }); this.notices.forEach(n => n.isRead = true); this.unreadCount = 0 } catch (e) {} },
    goHome() { this.currentTab = 'home'; this.queryParams.pageNum = 1; this.queryParams.categoryId = undefined; this.fetchArticles() },
    switchTab(tab) { this.currentTab = tab; if (tab === 'home') { this.selectedCategory = null; this.queryParams.categoryId = undefined; this.fetchArticles() } else if (tab === 'categories') this.fetchCategories(); else if (tab === 'tags') this.fetchTags() },
    filterByCategory(cat) { this.currentTab = 'home'; this.selectedCategory = cat; this.queryParams.categoryId = cat.categoryId; this.queryParams.pageNum = 1; this.fetchArticles() },
    searchArticles() { this.queryParams.keyword = this.keyword || undefined; this.queryParams.pageNum = 1; this.currentTab = 'home'; this.fetchArticles() },
    goArticle(id) { if (id) this.$router.push('/article/' + id) },
    goLogin() { this.$router.push('/login') }, goRegister() { this.$router.push('/register') },
    goProfile() { this.$router.push('/profile') }, goAdmin() { this.$router.push('/index') },
    goAiChat() { this.$router.push('/ai/chat') },
    handleLogout() { this.$confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => { removeToken(); this.$store.dispatch('LogOut').then(() => location.reload()).catch(() => location.reload()) }).catch(() => {}) },
    resolveImageUrl(path) { if (!path) return ''; if (path.startsWith('http://') || path.startsWith('https://')) return path; if (path.startsWith('/dev-api/')) return path; return process.env.VUE_APP_BASE_API + path }
  }
}
</script>

<style scoped>
.front-blog { min-height: 100vh; background: #f5f7fa; }
.front-header { background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); position: sticky; top: 0; z-index: 100; }
.header-inner { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; height: 60px; }
.logo h1 { margin: 0; font-size: 22px; color: #333; cursor: pointer; }
.mobile-menu-btn { display: none; }
.nav-menu a { margin-left: 24px; color: #666; text-decoration: none; font-size: 15px; cursor: pointer; }
.nav-menu a:hover, .nav-menu a.active { color: #1890ff; }
.notice-bell { position: relative; cursor: pointer; }
.badge { position: absolute; top: -8px; right: -12px; background: #f56c6c; color: #fff; border-radius: 10px; padding: 1px 6px; font-size: 11px; min-width: 18px; text-align: center; }
.front-body { max-width: 1200px; margin: 24px auto; padding: 0 20px; }
.container { display: flex; gap: 24px; }
.main-content { flex: 1; min-width: 0; }
.sidebar { width: 320px; flex-shrink: 0; }
.article-card { background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 20px; cursor: pointer; transition: all 0.3s; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.article-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.article-cover img { width: 100%; height: 240px; object-fit: cover; }
.article-info { padding: 20px; }
.article-title { margin: 0 0 12px; font-size: 20px; color: #333; }
.article-meta { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 8px; font-size: 13px; color: #999; }
.article-summary { margin: 0; color: #666; font-size: 14px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.widget { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.widget-title { margin: 0 0 12px; font-size: 16px; color: #333; padding-bottom: 8px; border-bottom: 2px solid #f0f0f0; }
.notice-content { font-size: 13px; color: #e6a23c; line-height: 1.6; padding: 8px; background: #fdf6ec; border-radius: 4px; }
.about-content { font-size: 14px; color: #666; }
.hot-item { display: flex; align-items: center; padding: 8px 0; cursor: pointer; }
.hot-rank { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 10px; background: #f0f0f0; color: #666; }
.rank-1 { background: #ff6b6b; color: #fff; } .rank-2 { background: #ffa502; color: #fff; } .rank-3 { background: #2ed573; color: #fff; }
.hot-title { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.category-side-item { display: flex; justify-content: space-between; padding: 6px 0; cursor: pointer; }
.friend-link-list { display: flex; flex-wrap: wrap; gap: 8px; }
.friend-link { font-size: 13px; color: #409eff; text-decoration: none; padding: 4px 10px; background: #ecf5ff; border-radius: 4px; }
.section-title { margin: 0 0 20px; font-size: 22px; color: #333; }
.category-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.category-card { background: #fff; border-radius: 8px; padding: 24px 20px; text-align: center; cursor: pointer; transition: all 0.3s; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid #f0f0f0; }
.category-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(64,158,255,0.15); border-color: #409eff; }
.category-name { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 8px; }
.category-count { font-size: 13px; color: #999; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 12px; }
.tag-item { cursor: pointer; font-size: 14px !important; padding: 8px 18px !important; border-radius: 20px !important; transition: all 0.3s; }
.tag-item:hover { transform: scale(1.05); }
.pagination-wrapper { text-align: center; margin-top: 24px; }
.front-footer { text-align: center; padding: 32px; color: #999; font-size: 13px; border-top: 1px solid #eee; margin-top: 40px; }
.notice-item { padding: 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.notice-item.unread { background: #f0f7ff; font-weight: 500; }
.notice-msg { font-size: 14px; color: #333; }
.notice-time { font-size: 12px; color: #999; margin-top: 4px; }
@media (max-width: 768px) { .category-list { grid-template-columns: repeat(2, 1fr); } }
</style>