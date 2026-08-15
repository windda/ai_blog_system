import request from '@/utils/request'

// 查询公开文章列表（首页用，只看已发布）
export function listPubArticle(query) {
  return request({
    url: '/blog/article/pub/list',
    method: 'get',
    params: query
  })
}

// 查询文章列表（后台管理用，只看自己的）
export function listArticle(query) {
  return request({
    url: '/blog/article/list',
    method: 'get',
    params: query
  })
}

// 查询文章详细
export function getArticle(articleId) {
  return request({
    url: '/blog/article/' + articleId,
    method: 'get'
  })
}

// 新增文章
export function addArticle(data) {
  return request({
    url: '/blog/article',
    method: 'post',
    data: data
  })
}

// 修改文章
export function updateArticle(data) {
  return request({
    url: '/blog/article',
    method: 'put',
    data: data
  })
}

// 删除文章
export function delArticle(articleId) {
  return request({
    url: '/blog/article/' + articleId,
    method: 'delete'
  })
}

// 增加浏览次数
export function addArticleView(articleId) {
  return request({
    url: '/blog/article/view/' + articleId,
    method: 'put'
  })
}

