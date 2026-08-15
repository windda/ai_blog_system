import request from '@/utils/request'

// 获取博客仪表盘数据
export function getDashboard(params) {
  return request({
    url: '/blog/dashboard',
    method: 'get',
    params: params
  })
}