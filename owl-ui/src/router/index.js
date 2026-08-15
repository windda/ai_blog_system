import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

/* Layout */
import Layout from '@/layout'

// 公共路由
export const constantRoutes = [
  {
    path: '/redirect',
    component: Layout,
    hidden: true,
    children: [
      {
        path: '/redirect/:path(.*)',
        component: () => import('@/views/redirect')
      }
    ]
  },
  {
    path: '/login',
    component: () => import('@/views/login'),
    hidden: true
  },
  {
    path: '/register',
    component: () => import('@/views/register'),
    hidden: true
  },
  // ===== 前台博客路由 =====
  {
    path: '/',
    component: () => import('@/views/front/index'),
    name: 'FrontHome',
    hidden: true,
    meta: { title: '博客首页' }
  },
  {
    path: '/article/:id(\\d+)',
    component: () => import('@/views/front/articleDetail'),
    name: 'FrontArticleDetail',
    hidden: true,
    meta: { title: '文章详情' }
  },
  {
    path: '/profile',
    component: () => import('@/views/front/profile'),
    name: 'FrontProfile',
    hidden: true,
    meta: { title: '个人中心' }
  },
  // ===== 后台路由 =====
  {
    path: '/404',
    component: () => import('@/views/error/404'),
    hidden: true
  },
  {
    path: '/401',
    component: () => import('@/views/error/401'),
    hidden: true
  },
  {
    path: '/index',
    component: Layout,
    redirect: '/',
    children: [
      {
        path: '',
        component: () => import('@/views/index'),
        name: 'Index',
        meta: { title: '首页', icon: 'dashboard', affix: true }
      },
      {
        path: 'article/:id(\\d+)',
        component: () => import('@/views/blog/articleDetail'),
        name: 'ArticleDetail',
        hidden: true,
        meta: { title: '文章详情' }
      }
    ]
  },
  {
    path: '/user',
    component: Layout,
    hidden: true,
    redirect: '/404',
    children: [
      {
        path: 'profile',
        component: () => import('@/views/system/user/profile/index'),
        name: 'Profile',
        meta: { title: '个人中心', icon: 'user' }
      }
    ]
  },
  // ===== 前台 AI 对话路由 =====
  {
    path: '/ai/chat',
    component: () => import('@/views/ai/chat'),
    name: 'AiChat',
    hidden: true,
    meta: { title: 'AI 助手' }
  }
]

// 动态路由
export const dynamicRoutes = [
  {
    path: '/system/user-auth',
    component: Layout,
    hidden: true,
    permissions: ['system:user:edit'],
    children: [{
      path: 'role/:userId(\\d+)',
      component: () => import('@/views/system/user/authRole'),
      name: 'AuthRole',
      meta: { title: '分配角色', activeMenu: '/system/user'}
    }]
  },
  {
    path: '/system/role-auth',
    component: Layout,
    hidden: true,
    permissions: ['system:role:edit'],
    children: [{
      path: 'user/:roleId(\\d+)',
      component: () => import('@/views/system/role/authUser'),
      name: 'AuthUser',
      meta: { title: '分配用户', activeMenu: '/system/role' }
    }]
  },
  {
    path: '/system/dict-data',
    component: Layout,
    hidden: true,
    permissions: ['system:dict:list'],
    children: [{
      path: 'index/:dictId(\\d+)',
      component: () => import('@/views/system/dict/data'),
      name: 'Data',
      meta: { title: '字典数据', activeMenu: '/system/dict' }
    }]
  },
  {
    path: '/monitor/job-log',
    component: Layout,
    hidden: true,
    permissions: ['monitor:job:list'],
    children: [{
      path: 'index',
      component: () => import('@/views/monitor/job/log'),
      name: 'JobLog',
      meta: { title: '调度日志', activeMenu: '/monitor/job' }
    }]
  },
  {
    path: '/tool/gen-edit',
    component: Layout,
    hidden: true,
    permissions: ['tool:gen:edit'],
    children: [{
      path: 'index/:tableId(\\d+)',
      component: () => import('@/views/tool/gen/editTable'),
      name: 'GenEdit',
      meta: { title: '修改生成配置', activeMenu: '/tool/gen' }
    }]
  }
]

let routerPush = Router.prototype.push;
Router.prototype.push = function push(location) {
  return routerPush.call(this, location).catch(err => err)
}

export default new Router({
  mode: 'history',
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})