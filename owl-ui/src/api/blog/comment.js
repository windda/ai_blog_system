import request from '@/utils/request'

// 查询评论列表（后台管理用）
export function listComment(query) {
  return request({
    url: '/blog/comment/list',
    method: 'get',
    params: query
  })
}

// 查询文章评论列表（前台用）
export function listCommentByArticle(articleId) {
  return request({
    url: '/blog/comment/list/' + articleId,
    method: 'get'
  })
}

// 新增评论
export function addComment(data) {
  return request({
    url: '/blog/comment',
    method: 'post',
    data: data
  })
}

// 审核评论
export function updateCommentStatus(data) {
  return request({
    url: '/blog/comment/status',
    method: 'put',
    data: data
  })
}

// 删除评论
export function delComment(commentId) {
  return request({
    url: '/blog/comment/' + commentId,
    method: 'delete'
  })
}
