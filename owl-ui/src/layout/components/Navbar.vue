<template>
  <div class="navbar">
    <hamburger id="hamburger-container" :is-active="sidebar.opened" class="hamburger-container" @toggleClick="toggleSideBar" />

    <breadcrumb id="breadcrumb-container" class="breadcrumb-container" v-if="!topNav"/>
    <top-nav id="topmenu-container" class="topmenu-container" v-if="topNav"/>

    <div class="right-menu">
      <template v-if="device!=='mobile'">
        <search id="header-search" class="right-menu-item" />
        
        <!-- 返回首页 -->
        <el-tooltip content="返回首页" effect="dark" placement="bottom">
          <span class="right-menu-item hover-effect" @click="goHome">
            <svg-icon icon-class="home" />
            <span style="font-size:13px;margin-left:4px">首页</span>
          </span>
        </el-tooltip>

        <screenfull id="screenfull" class="right-menu-item hover-effect" />

        <!-- 站内通知 -->
        <el-tooltip content="站内通知" effect="dark" placement="bottom">
          <span class="right-menu-item hover-effect notification-badge" @click="openNotifications">
            <svg-icon icon-class="message" />
            <el-badge v-if="unreadBadge" :value="unreadBadge" class="badge" />
          </span>
        </el-tooltip>

        <el-tooltip content="布局大小" effect="dark" placement="bottom">
          <size-select id="size-select" class="right-menu-item hover-effect" />
        </el-tooltip>

      </template>

      <!-- 前台博客入口（移动端也显示，方便跳转前台） -->
      <el-tooltip content="前台博客" effect="dark" placement="bottom">
        <span class="right-menu-item hover-effect front-blog-btn" @click="goFront">
          <svg-icon icon-class="guide" />
        </span>
      </el-tooltip>

      <el-dropdown class="avatar-container right-menu-item hover-effect" trigger="click">
        <div class="avatar-wrapper">
          <img :src="avatar" class="user-avatar">
          <i class="el-icon-caret-bottom" />
        </div>
        <el-dropdown-menu slot="dropdown">
          <router-link to="/user/profile">
            <el-dropdown-item>个人中心</el-dropdown-item>
          </router-link>
          <el-dropdown-item @click.native="setting = true">
            <span>布局设置</span>
          </el-dropdown-item>
          <el-dropdown-item divided @click.native="logout">
            <span>退出登录</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Breadcrumb from '@/components/Breadcrumb'
import TopNav from '@/components/TopNav'
import Hamburger from '@/components/Hamburger'
import Screenfull from '@/components/Screenfull'
import SizeSelect from '@/components/SizeSelect'
import Search from '@/components/HeaderSearch'

export default {
  components: {
    Breadcrumb,
    TopNav,
    Hamburger,
    Screenfull,
    SizeSelect,
    Search
  },
  computed: {
    ...mapGetters([
      'sidebar',
      'avatar',
      'device'
    ]),
    unreadBadge() {
      return this.$store.getters['notifications/unreadBadge']
    },
    setting: {
      get() {
        return this.$store.state.settings.showSettings
      },
      set(val) {
        this.$store.dispatch('settings/changeSetting', {
          key: 'showSettings',
          value: val
        })
      }
    },
    topNav: {
      get() {
        return this.$store.state.settings.topNav
      }
    }
  },
  methods: {
    toggleSideBar() {
      this.$store.dispatch('app/toggleSideBar')
    },
    async logout() {
      this.$confirm('确定注销并退出系统吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$store.dispatch('LogOut').then(() => {
          // 断开 WebSocket
          this.$store.dispatch('notifications/reset')
          import('@/plugins/socketio').then(s => s.disconnect())
          location.href = '/index';
        })
      }).catch(() => {});
    },
    openNotifications() {
      const list = this.$store.getters['notifications/notificationList']
      if (list.length === 0) {
        this.$message.info('暂无新通知')
        return
      }
      // 显示通知列表弹窗
      this.$alert(
        list.map(n => `<div style="margin-bottom:12px;padding:8px;background:#f5f7fa;border-radius:4px;">
          <div style="font-weight:bold;color:#333;margin-bottom:4px;">${n.title || '系统通知'}</div>
          <div style="color:#666;font-size:13px;">${n.content || ''}</div>
          <div style="color:#909399;font-size:12px;margin-top:4px;">${n.time || ''}</div>
        </div>`).join(''),
        '站内通知',
        {
          dangerouslyUseHTMLString: true,
          showCancelButton: true,
          cancelButtonText: '关闭',
          confirmButtonText: '全部标记为已读',
          confirmButtonClass: 'el-button--primary'
        }
      ).then(() => {
        this.$store.dispatch('notifications/clear')
        this.$message.success('已清除未读通知')
      }).catch(() => {})
    },
    goHome() {
      this.$router.push('/index')
    },
    goFront() {
      this.$router.push('/')
    }
  }
}
</script>

<style lang="scss" scoped>
.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    cursor: pointer;
    transition: background .3s;
    -webkit-tap-highlight-color:transparent;

    &:hover {
      background: rgba(0, 0, 0, .025)
    }
  }

  .breadcrumb-container {
    float: left;
  }

  .topmenu-container {
    position: absolute;
    left: 50px;
  }

  .errLog-container {
    display: inline-block;
    vertical-align: top;
  }

  .right-menu {
    float: right;
    height: 100%;
    line-height: 50px;

    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: #5a5e66;
      vertical-align: text-bottom;

      &.hover-effect {
        cursor: pointer;
        transition: background .3s;

        &:hover {
          background: rgba(0, 0, 0, .025)
        }
      }
    }

    .avatar-container {
      margin-right: 30px;

      .avatar-wrapper {
        margin-top: 5px;
        position: relative;

        .user-avatar {
          cursor: pointer;
          width: 40px;
          height: 40px;
          border-radius: 10px;
        }

        .el-icon-caret-bottom {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 25px;
          font-size: 12px;
        }
      }
    }
  }
}
</style>