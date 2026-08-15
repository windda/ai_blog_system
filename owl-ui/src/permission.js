import router from './router'
import store from './store'
import { Message } from 'element-ui'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
import { isRelogin } from '@/utils/request'

NProgress.configure({ showSpinner: false })

// 白名单
const whiteList = ['/login', '/auth-redirect', '/bind', '/register', '/']
// 前台路由前缀
const frontRoutePrefixes = ['/article/', '/profile', '/ai/chat']

function isWhiteListed(path) {
  if (whiteList.indexOf(path) !== -1) return true
  return frontRoutePrefixes.some(prefix => path.startsWith(prefix))
}

function isFrontRoute(path) {
  return path === '/' || frontRoutePrefixes.some(prefix => path.startsWith(prefix))
}

router.beforeEach((to, from, next) => {
  NProgress.start()
  if (getToken()) {
    to.meta.title && store.dispatch('settings/setTitle', to.meta.title)
    if (isFrontRoute(to.path)) {
      if (to.path === '/profile' && store.getters.roles.includes('admin')) {
        NProgress.done()
        next('/index')
        return
      }
      if (store.getters.roles.length === 0) {
        store.dispatch('GetInfo').then(() => {
          next()
          NProgress.done()
        }).catch(() => {
          next()
          NProgress.done()
        })
      } else {
        next()
        NProgress.done()
      }
      return
    }
    if (!store.getters.roles.includes('admin')) {
      NProgress.done()
      next('/')
      return
    }
    if (to.path === '/login') {
      next()
      NProgress.done()
    } else if (store.getters.roles.length === 0) {
      isRelogin.show = true
      store.dispatch('GetInfo').then(() => {
        isRelogin.show = false
        store.dispatch('GenerateRoutes').then(accessRoutes => {
          router.addRoutes(accessRoutes)
          next({ ...to, replace: true })
        })
      }).catch(err => {
        store.dispatch('LogOut').then(() => {
          Message.error(err)
          next({ path: '/' })
        })
      })
    } else if (store.getters.permission_routes.length === 0) {
      store.dispatch('GenerateRoutes').then(accessRoutes => {
        router.addRoutes(accessRoutes)
        next({ ...to, replace: true })
      }).catch(() => {
        next({ ...to, replace: true })
      })
    } else {
      next()
    }
  } else {
    if (isWhiteListed(to.path)) {
      next()
    } else {
      next(`/login?redirect=${to.fullPath}`)
      NProgress.done()
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})