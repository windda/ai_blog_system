<template>
  <div class="profile-page">
    <header class="front-header">
      <div class="header-inner">
        <div class="logo"><h1 @click="goHome">📝个人技术博客</h1></div>
        <nav class="nav-menu">
          <a @click="goHome">首页</a>
          <a v-if="isAdmin" @click="goAdmin" class="admin-link">后台管理</a>
          <a class="logout-link" @click="handleLogout">退出</a>
        </nav>
      </div>
    </header>

    <div class="profile-body">
      <div class="container">
        <div class="profile-sidebar">
          <div class="user-card">
            <div style="cursor:pointer;margin-bottom:12px;" @click="openAvatarCropper">
              <el-avatar :size="80" :src="userAvatar">{{ (userInfo.nickName || userName)[0] }}</el-avatar>
            </div>
            <div class="user-card-name">{{ userInfo.nickName || userName }}</div>
            <div class="user-card-desc">{{ userInfo.remark || '这个人很懒，什么都没写~' }}</div>
          </div>
          <el-menu :default-active="activeTab" @select="switchTab" class="profile-menu">
            <el-menu-item index="articles"><i class="el-icon-document"></i>我的文章</el-menu-item>
            <el-menu-item index="comments"><i class="el-icon-chat-line-round"></i>我的评论</el-menu-item>
            <el-menu-item index="collections"><i class="el-icon-star-off"></i>我的收藏</el-menu-item>
            <el-menu-item index="history"><i class="el-icon-time"></i>浏览历史</el-menu-item>
            <el-menu-item index="settings"><i class="el-icon-setting"></i>资料设置</el-menu-item>
          </el-menu>
        </div>

        <div class="profile-content">
          <!-- 我的文章 -->
          <div v-if="activeTab === 'articles'" v-loading="loading">
            <h2 class="section-title">我的文章
              <el-button type="primary" size="small" @click="openArticleDialog()" style="float:right;">发布文章</el-button>
            </h2>
            <div class="search-bar"><el-input v-model="searchKeyword" placeholder="搜索文章标题..." size="small" clearable @clear="fetchArticles(1)" @keyup.enter.native="fetchArticles(1)" style="width:260px;"><el-button slot="append" icon="el-icon-search" @click="fetchArticles(1)" /></el-input></div>
            <el-empty v-if="!loading && articles.length === 0" description="暂无文章"></el-empty>
            <div v-for="(a, idx) in articles" :key="a.articleId" class="list-item">
              <div class="list-info" @click="goArticle(a.articleId)" style="cursor:pointer;">
                <div class="list-title">{{ (articlePage-1)*pageSize + idx + 1 }}. {{ a.title }}</div>
                <div class="list-meta">{{ a.categoryName || '未分类' }} · {{ a.viewCount || 0 }}阅读 · {{ (a.createTime||'').slice(0,10) }} · {{ a.status==='0'?'草稿':'已发布' }}</div>
              </div>
              <div class="list-actions">
                <el-button type="text" size="small" @click="openArticleDialog(a)">编辑</el-button>
                <el-button type="text" size="small" style="color:#f56c6c;" @click="deleteArticle(a.articleId)">删除</el-button>
              </div>
            </div>
            <el-pagination v-if="articleTotal>pageSize" layout="prev,pager,next" :total="articleTotal" :page-size="pageSize" @current-change="fetchArticles" />
          </div>

          <!-- 文章弹窗 -->
          <el-dialog :title="articleForm.articleId?'编辑文章':'发布文章'" :visible.sync="articleDialogVisible" width="800px" append-to-body>
            <el-form label-width="80px">
              <el-form-item label="标题"><el-input v-model="articleForm.title" placeholder="请输入标题" /></el-form-item>
              <el-form-item label="分类"><el-select v-model="articleForm.categoryId" clearable style="width:100%;"><el-option v-for="cat in categoryList" :key="cat.categoryId" :label="cat.categoryName" :value="cat.categoryId" /></el-select></el-form-item>
              <el-form-item label="封面图">
                <el-upload class="avatar-uploader" :action="coverUploadUrl" :headers="uploadHeaders" :show-file-list="false" :on-success="handleCoverSuccess" :before-upload="beforeCoverUpload">
                  <img v-if="articleForm.coverImage" :src="resolveImg(articleForm.coverImage)" style="width:200px;height:112px;object-fit:cover;border-radius:4px;border:1px dashed #d9d9d9;" />
                  <i v-else class="el-icon-plus" style="font-size:28px;color:#8c939d;width:200px;height:112px;line-height:112px;border:1px dashed #d9d9d9;border-radius:4px;"></i>
                </el-upload>
                <el-button v-if="articleForm.coverImage" type="danger" size="mini" icon="el-icon-delete" style="margin-left:8px;" @click="articleForm.coverImage=''">删除封面</el-button>
              </el-form-item>
              <el-form-item label="摘要"><el-input v-model="articleForm.summary" type="textarea" :rows="2" /></el-form-item>
              <el-form-item label="状态">
                <el-radio-group v-model="articleForm.status">
                  <el-radio label="1">发布</el-radio>
                  <el-radio label="0">草稿</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="内容"><editor v-model="articleForm.content" :min-height="300" /></el-form-item>
            </el-form>
            <span slot="footer"><el-button @click="articleDialogVisible=false">取消</el-button><el-button type="primary" @click="saveArticle" :loading="saving">发布</el-button></span>
          </el-dialog>

          <!-- 我的评论 -->
          <div v-if="activeTab === 'comments'" v-loading="loading">
            <h2 class="section-title">我的评论</h2>
            <div class="search-bar"><el-input v-model="searchKeyword" placeholder="搜索评论内容..." size="small" clearable @clear="fetchComments(1)" @keyup.enter.native="fetchComments(1)" style="width:260px;"><el-button slot="append" icon="el-icon-search" @click="fetchComments(1)" /></el-input></div>
            <el-empty v-if="!loading && comments.length===0" description="暂无评论"></el-empty>
            <div v-for="(c, idx) in comments" :key="c.commentId" class="list-item">
              <div class="list-info">
                <div class="list-title">{{ (commentPage-1)*pageSize + idx + 1 }}. 评论于《{{ c.articleTitle||'文章' }}》</div>
                <div class="list-meta">{{ (c.createTime||'').slice(0,16) }} · <el-tag v-if="c.status==='0'" size="mini" type="warning">待审核</el-tag><el-tag v-else-if="c.status==='1'" size="mini" type="success">已通过</el-tag></div>
                <div style="color:#666;font-size:13px;margin-top:4px;">{{ c.content }}</div>
              </div>
              <div class="list-actions">
                <el-button type="text" size="small" @click="showCommentDetail(c)">详情</el-button>
                <el-button v-if="c.status==='0'" type="text" size="small" @click="approveComment(c.commentId)">通过</el-button>
                <el-button v-if="c.status==='1'" type="text" size="small" @click="rejectComment(c.commentId)">驳回</el-button>
                <el-button type="text" size="small" style="color:#f56c6c;" @click="deleteComment(c.commentId)">删除</el-button>
              </div>
            </div>
          </div>
          <el-dialog title="评论详情" :visible.sync="commentDetailVisible" width="550px" append-to-body>
            <el-form label-width="90px" v-if="detailComment">
              <el-form-item label="评论编号"><span>{{ detailComment.commentId }}</span></el-form-item>
              <el-form-item label="所属文章"><span>{{ detailComment.articleTitle||'未知' }}</span></el-form-item>
              <el-form-item label="评论者"><span>{{ detailComment.authorName||'匿名' }}</span></el-form-item>
              <el-form-item label="评论时间"><span>{{ (detailComment.createTime||'').slice(0,16) }}</span></el-form-item>
              <el-form-item label="评论内容"><div style="background:#f5f7fa;padding:12px;border-radius:4px;line-height:1.6;white-space:pre-wrap;">{{ detailComment.content }}</div></el-form-item>
            </el-form>
          </el-dialog>

          <!-- 我的收藏 -->
          <div v-if="activeTab === 'collections'" v-loading="loading">
            <h2 class="section-title">我的收藏</h2>
            <div class="search-bar"><el-input v-model="searchKeyword" placeholder="搜索收藏文章..." size="small" clearable @clear="fetchCollections(1)" @keyup.enter.native="fetchCollections(1)" style="width:260px;"><el-button slot="append" icon="el-icon-search" @click="fetchCollections(1)" /></el-input></div>
            <el-empty v-if="!loading && collections.length===0" description="暂无收藏"></el-empty>
            <div v-for="(c, idx) in collections" :key="c.articleId" class="list-item" @click="goArticle(c.articleId)" style="cursor:pointer;">
              <div class="list-info"><div class="list-title">{{ (collectPage-1)*pageSize + idx + 1 }}. {{ c.title }}</div><div class="list-meta">{{ c.viewCount||0 }}阅读 · {{ (c.createTime||'').slice(0,10) }}</div></div>
            </div>
            <el-pagination v-if="collectTotal>pageSize" layout="prev,pager,next" :total="collectTotal" :page-size="pageSize" @current-change="fetchCollections" />
          </div>

          <!-- 浏览历史 -->
          <div v-if="activeTab === 'history'" v-loading="loading">
            <h2 class="section-title">浏览历史 <el-button size="mini" type="danger" @click="clearHistory" style="float:right;">清空历史</el-button></h2>
            <div class="search-bar"><el-input v-model="searchKeyword" placeholder="搜索浏览记录..." size="small" clearable @clear="fetchHistory(1)" @keyup.enter.native="fetchHistory(1)" style="width:260px;"><el-button slot="append" icon="el-icon-search" @click="fetchHistory(1)" /></el-input></div>
            <el-empty v-if="!loading && history.length===0" description="暂无浏览记录"></el-empty>
            <div v-for="(h, idx) in history" :key="h.articleId" class="list-item" @click="goArticle(h.articleId)" style="cursor:pointer;">
              <div class="list-info"><div class="list-title">{{ (historyPage-1)*pageSize + idx + 1 }}. {{ h.title }}</div><div class="list-meta">{{ (h.createTime||'').slice(0,16) }} · {{ h.viewCount||0 }}阅读</div></div>
            </div>
            <el-pagination v-if="historyTotal>pageSize" layout="prev,pager,next" :total="historyTotal" :page-size="pageSize" @current-change="fetchHistory" />
          </div>

          <!-- 资料设置 -->
          <div v-if="activeTab === 'settings'">
            <h2 class="section-title">个人资料</h2>
            <el-form label-width="100px" style="max-width:600px;">
              <el-form-item label="头像">
                <div style="cursor:pointer;" @click="openAvatarCropper">
                  <el-avatar :size="60" :src="userAvatar">{{ (userInfo.nickName||userName)[0] }}</el-avatar>
                  <span style="margin-left:12px;color:#409eff;cursor:pointer;">点击更换头像</span>
                </div>
              </el-form-item>
              <el-form-item label="昵称"><el-input v-model="userInfo.nickName" /></el-form-item>
              <el-form-item label="邮箱"><el-input v-model="userInfo.email" /></el-form-item>
              <el-form-item label="手机号"><el-input v-model="userInfo.phonenumber" /></el-form-item>
              <el-form-item label="个人简介"><el-input v-model="userInfo.remark" type="textarea" :rows="3" /></el-form-item>
              <el-form-item><el-button type="primary" @click="saveProfile" :loading="savingProfile">保存资料</el-button></el-form-item>
            </el-form>
            <el-divider />
            <h2 class="section-title">修改密码</h2>
            <el-form label-width="100px" style="max-width:500px;">
              <el-form-item label="旧密码"><el-input v-model="pwdForm.oldPwd" type="password" /></el-form-item>
              <el-form-item label="新密码"><el-input v-model="pwdForm.newPwd" type="password" /></el-form-item>
              <el-form-item><el-button type="danger" @click="changePwd" :loading="changingPwd">修改密码</el-button></el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>

    <!-- 头像裁剪弹窗 -->
    <el-dialog title="修改头像" :visible.sync="avatarCropperVisible" width="800px" append-to-body>
      <el-row>
        <el-col :xs="24" :md="12" :style="{height:'350px'}">
          <vue-cropper ref="cropper" :img="avatarCropperImg" :info="true" :autoCrop="true" :autoCropWidth="200" :autoCropHeight="200" :fixedBox="true" @realTime="avatarRealTime" v-if="avatarCropperVisible" />
        </el-col>
        <el-col :xs="24" :md="12" :style="{height:'350px'}">
          <div style="text-align:center;"><img :src="avatarPreviewUrl" style="width:200px;height:200px;border-radius:50%;" /></div>
        </el-col>
      </el-row>
      <br />
      <el-row>
        <el-col :span="24" style="text-align:center;">
          <el-upload action="#" :http-request="requestAvatarUpload" :show-file-list="false" :before-upload="beforeAvatarCropperUpload" style="display:inline-block;margin-right:10px;">
            <el-button size="small">选择图片<i class="el-icon-upload el-icon--right"></i></el-button>
          </el-upload>
          <el-button icon="el-icon-refresh-left" size="small" @click="avatarRotateLeft"></el-button>
          <el-button icon="el-icon-refresh-right" size="small" @click="avatarRotateRight"></el-button>
          <el-button type="primary" size="small" @click="avatarUploadImg">提 交</el-button>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script>
import { getToken, removeToken } from '@/utils/auth'
import { getUserArticles, getUserCollections, getUserComments, getUserHistory, clearUserHistory, updateUserProfile, updateUserPassword, getUserInfo, uploadAvatar } from '@/api/blog/front'
import { addFrontArticle, updateFrontArticle, deleteFrontArticle, updateCommentStatus, deleteFrontComment } from '@/api/blog/front'
import { getFrontCategories } from '@/api/blog/front'
import Editor from '@/components/Editor'
import { VueCropper } from "vue-cropper";

export default {
  name: 'FrontProfile',
  components: { Editor, VueCropper },
  data() {
    return {
      activeTab: 'articles', loading: false, pageSize: 10, searchKeyword: '',
      articles: [], articleTotal: 0, articlePage: 1,
      comments: [], commentPage: 1,
      collections: [], collectTotal: 0, collectPage: 1,
      history: [], historyTotal: 0, historyPage: 1,
      userInfo: { nickName: '', email: '', phonenumber: '', remark: '', avatar: '' },
      pwdForm: { oldPwd: '', newPwd: '' },
      savingProfile: false, changingPwd: false,
      articleDialogVisible: false,
      articleForm: { articleId: null, title: '', summary: '', content: '', categoryId: null, coverImage: '', status: '1' },
      saving: false, categoryList: [],
      uploadAvatarUrl: process.env.VUE_APP_BASE_API + '/front/user/avatar',
      coverUploadUrl: process.env.VUE_APP_BASE_API + '/common/upload',
      commentDetailVisible: false, detailComment: null,
      avatarCropperVisible: false, avatarCropperImg: '', avatarPreviewUrl: ''
    }
  },
  computed: {
    userName() { return this.$store.state.user?.name || '用户' },
    userAvatar() {
      if (this.userInfo.avatar) return this.userInfo.avatar.startsWith('http') ? this.userInfo.avatar : process.env.VUE_APP_BASE_API + this.userInfo.avatar
      return this.$store.state.user?.avatar || ''
    },
    isAdmin() { return this.$store.state.user?.roles?.includes('admin') },
    isLoggedIn() { return !!getToken() },
    uploadHeaders() { return { Authorization: 'Bearer ' + getToken() } }
  },
  created() {
    if (!this.isLoggedIn) { this.$router.push('/login'); return }
    this.fetchUserInfo(); this.fetchCategories(); this.switchTab('articles')
  },
  methods: {
    async fetchUserInfo() { try { const res = await getUserInfo(); if (res && res.data) this.userInfo = res.data } catch (e) {} },
    async fetchCategories() { try { const res = await getFrontCategories(); this.categoryList = (res && res.data) ? res.data : [] } catch (e) {} },
    openAvatarCropper() { this.avatarCropperImg = this.userAvatar; this.avatarPreviewUrl = this.userAvatar; this.avatarCropperVisible = true; },
    beforeAvatarCropperUpload(file) { if (file.type.indexOf('image/') == -1) { this.$message.error('请上传图片文件'); return false; } const reader = new FileReader(); reader.readAsDataURL(file); reader.onload = () => { this.avatarCropperImg = reader.result; }; return false; },
    requestAvatarUpload() {},
    avatarRealTime(data) { this.avatarPreviewUrl = data.url; },
    avatarRotateLeft() { this.$refs.cropper.rotateLeft(); },
    avatarRotateRight() { this.$refs.cropper.rotateRight(); },
    avatarUploadImg() { this.$refs.cropper.getCropBlob(data => { const formData = new FormData(); formData.append('avatarfile', data); uploadAvatar(formData).then(res => { if (res.code === 200 && res.data) { this.userInfo.avatar = res.data.avatar; this.$message.success('头像更新成功'); this.avatarCropperVisible = false; } else { this.$message.error('上传失败'); } }).catch(() => this.$message.error('上传失败')); }); },
    handleCoverSuccess(res) { if (res.code === 200) { this.articleForm.coverImage = res.fileName; this.$message.success('封面上传成功'); } else { this.$message.error('封面上传失败'); } },
    beforeCoverUpload(file) { const isImg = file.type === 'image/jpeg' || file.type === 'image/png'; const isLt5M = file.size / 1024 / 1024 < 5; if (!isImg) { this.$message.error('只能上传 jpg/png 图片'); return false; } if (!isLt5M) { this.$message.error('图片不能超过 5MB'); return false; } return true; },
    resolveImg(path) { if (!path) return ''; if (path.startsWith('http')) return path; return process.env.VUE_APP_BASE_API + path; },
    switchTab(tab) { this.activeTab=tab; this.searchKeyword=''; if (tab==='articles') this.fetchArticles(1); else if (tab==='comments') this.fetchComments(1); else if (tab==='collections') this.fetchCollections(1); else if (tab==='history') this.fetchHistory(1) },
    async fetchArticles(p=1) { this.loading=true; try { const r=await getUserArticles({pageNum:p,pageSize:this.pageSize,keyword:this.searchKeyword||undefined}); this.articles=(r&&r.rows)?r.rows:[]; this.articleTotal=(r&&r.total)?r.total:0 } catch(e){this.articles=[]} this.loading=false },
    openArticleDialog(a) { this.articleForm=a?{articleId:a.articleId,title:a.title||'',summary:a.summary||'',content:a.content||'',categoryId:a.categoryId||null,coverImage:a.coverImage||'',status:a.status||'1'}:{articleId:null,title:'',summary:'',content:'',categoryId:null,coverImage:'',status:'1'}; this.articleDialogVisible=true },
    async saveArticle() { if(!this.articleForm.title.trim()) return this.$message.warning('请输入标题'); this.saving=true; try { if(this.articleForm.articleId){await updateFrontArticle(this.articleForm.articleId,this.articleForm);this.$message.success('更新成功')}else{await addFrontArticle(this.articleForm);this.$message.success('发布成功')} this.articleDialogVisible=false; this.fetchArticles(1) } catch(e){this.$message.error('操作失败')} this.saving=false },
    async deleteArticle(id) { try { await this.$confirm('确定删除?','提示',{type:'warning'}); await deleteFrontArticle(id); this.$message.success('已删除'); this.fetchArticles(1) } catch(e) { if(e!=='cancel') this.$message.error('删除失败') } },
    async fetchComments(p=1) { this.loading=true; try { const r=await getUserComments({pageNum:p,pageSize:this.pageSize,keyword:this.searchKeyword||undefined}); this.comments=(r&&r.rows)?r.rows:[] } catch(e){this.comments=[]} this.loading=false },
    approveComment(id){updateCommentStatus(id,{status:'1'}).then(()=>{this.$message.success('已通过');this.fetchComments(1)}).catch(()=>this.$message.error('操作失败'))},
    rejectComment(id){updateCommentStatus(id,{status:'2'}).then(()=>{this.$message.success('已驳回');this.fetchComments(1)}).catch(()=>this.$message.error('操作失败'))},
    async deleteComment(id) { try { await this.$confirm('确定删除?','提示',{type:'warning'}); await deleteFrontComment(id); this.$message.success('已删除'); this.fetchComments(1) } catch(e) { if(e!=='cancel') this.$message.error('删除失败') } },
    showCommentDetail(c) { this.detailComment=c; this.commentDetailVisible=true },
    async fetchCollections(p=1) { this.loading=true; try { const r=await getUserCollections({pageNum:p,pageSize:this.pageSize,keyword:this.searchKeyword||undefined}); this.collections=(r&&r.rows)?r.rows:[]; this.collectTotal=(r&&r.total)?r.total:0 } catch(e){this.collections=[]} this.loading=false },
    async fetchHistory(p=1) { this.loading=true; try { const r=await getUserHistory({pageNum:p,pageSize:this.pageSize,keyword:this.searchKeyword||undefined}); this.history=(r&&r.rows)?r.rows:[]; this.historyTotal=(r&&r.total)?r.total:0 } catch(e){this.history=[]} this.loading=false },
    async clearHistory() { try { await clearUserHistory(); this.$message.success('已清空'); this.fetchHistory(1) } catch(e) { this.$message.error('清空失败') } },
    async saveProfile() { this.savingProfile=true; try { await updateUserProfile({nickName:this.userInfo.nickName,email:this.userInfo.email,phonenumber:this.userInfo.phonenumber,introduction:this.userInfo.remark}); this.$message.success('更新成功') } catch(e){this.$message.error('更新失败')} this.savingProfile=false },
    async changePwd() { if(!this.pwdForm.oldPwd||!this.pwdForm.newPwd) return this.$message.warning('请输入密码'); this.changingPwd=true; try { await updateUserPassword({oldPassword:this.pwdForm.oldPwd,newPassword:this.pwdForm.newPwd}); this.$message.success('密码修改成功'); this.pwdForm={oldPwd:'',newPwd:''} } catch(e){this.$message.error('修改失败')} this.changingPwd=false },
    goHome(){this.$router.push('/')}, goAdmin(){this.$router.push('/index')}, goArticle(id){this.$router.push('/article/'+id)},
    handleLogout(){this.$confirm('确定退出?','提示',{type:'warning'}).then(()=>{removeToken();this.$store.dispatch('LogOut').then(()=>location.reload())}).catch(()=>{})}
  }
}
</script>

<style scoped>
.profile-page{min-height:100vh;background:#f5f7fa}.front-header{background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.06);position:sticky;top:0;z-index:100}.header-inner{max-width:1200px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between;height:60px}.logo h1{margin:0;font-size:22px;color:#333;cursor:pointer}.nav-menu a{margin-left:24px;color:#666;text-decoration:none;font-size:15px;cursor:pointer}.profile-body{max-width:1200px;margin:24px auto;padding:0 20px}.container{display:flex;gap:24px}.profile-sidebar{width:240px;flex-shrink:0}.user-card{background:#fff;border-radius:8px;padding:24px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:16px}.user-card-name{font-size:18px;font-weight:700;color:#333;margin-top:8px}.user-card-desc{font-size:12px;color:#999;margin-top:4px}.profile-menu{border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06)}.profile-content{flex:1;background:#fff;border-radius:8px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,.06);min-height:400px}.search-bar{margin-bottom:16px}.list-item{display:flex;align-items:center;padding:12px 0;border-bottom:1px solid #f0f0f0}.list-info{flex:1}.list-title{font-size:15px;color:#333}.list-meta{font-size:12px;color:#999;margin-top:4px}.list-actions{flex-shrink:0;margin-left:12px}.section-title{margin:0 0 20px;font-size:20px;color:#333}.avatar-uploader{display:inline-block}
</style>