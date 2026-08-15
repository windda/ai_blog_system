import request from '@/utils/request'

// 文章
export function getFrontArticles(params) {
  return request({ url: '/front/article/list', method: 'get', params })
}

export function getFrontArticle(id) {
  return request({ url: '/front/article/' + id, method: 'get' })
}

export function getHotArticles(params) {
  return request({ url: '/front/hot-articles', method: 'get', params })
}

export function getRelatedArticles(articleId) {
  return request({ url: '/front/related-articles/' + articleId, method: 'get' })
}

export function addView(articleId) {
  return request({ url: '/front/article/addView/' + articleId, method: 'post' })
}

export function likeArticle(articleId) {
  return request({ url: '/front/article/' + articleId + '/like', method: 'post' })
}

export function getLikeStatus(articleId) {
  return request({ url: '/front/article/' + articleId + '/like/status', method: 'get' })
}

export function getLikeUsers(articleId) {
  return request({ url: '/front/article/' + articleId + '/like/users', method: 'get' })
}

// 分类 / 标签
export function getFrontCategories() {
  return request({ url: '/front/categories', method: 'get' })
}

export function getFrontTags() {
  return request({ url: '/front/tags', method: 'get' })
}

// 兼容旧名称
export const getArticle = getFrontArticle
export const getCategories = getFrontCategories
export const getTags = getFrontTags
export function collectArticle(articleId) {
  return request({ url: '/front/article/' + articleId + '/collect', method: 'post' })
}

export function getCollectStatus(articleId) {
  return request({ url: '/front/article/' + articleId + '/collect/status', method: 'get' })
}

export function getUserCollections(params) {
  return request({ url: '/front/user/collections', method: 'get', params })
}

export function getUserHistory(params) {
  return request({ url: '/front/user/history', method: 'get', params })
}

export function clearUserHistory() {
  return request({ url: '/front/user/history/clear', method: 'post' })
}

export function getUserArticles(params) {
  return request({ url: '/front/user/article/list', method: 'get', params })
}

export function getUserComments(params) {
  return request({ url: '/front/user/comment/list', method: 'get', params })
}

export function getUserInfo() {
  return request({ url: '/front/user/info', method: 'get' })
}

export function updateUserProfile(data) {
  return request({ url: '/front/user/profile/update', method: 'put', data })
}

export function uploadAvatar(formData) {
  return request({ url: '/front/user/avatar', method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
}

export function updateUserPassword(data) {
  return request({ url: '/front/user/password/update', method: 'put', data })
}

// 前台文章管理
export function addFrontArticle(data) {
  return request({ url: '/front/user/article', method: 'post', data })
}

export function updateFrontArticle(articleId, data) {
  return request({ url: '/front/user/article/' + articleId, method: 'put', data })
}

export function deleteFrontArticle(articleId) {
  return request({ url: '/front/user/article/' + articleId, method: 'delete' })
}

// 浏览历史记录
export function recordFrontHistory(articleId) {
  return request({ url: '/front/article/' + articleId + '/history', method: 'post' })
}

// 前台评论管理
export function updateCommentStatus(commentId, data) {
  return request({ url: '/front/user/comment/' + commentId + '/status', method: 'put', data })
}

export function deleteFrontComment(commentId) {
  return request({ url: '/front/user/comment/' + commentId, method: 'delete' })
}

export const listPubArticle = getFrontArticles