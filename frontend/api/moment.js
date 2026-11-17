import http from '@/common/request'

/**
 * 朋友圈接口封装
 * 路径前缀: /moment (BASE_URL = /api/v1 已在 request.js 内拼接)
 * 两步发布流程:
 *   1) uploadImage 逐张上传图片, 拿到 url
 *   2) publish 用 url 数组创建动态
 */
export default {
  // 上传图片(两步发布第一步)
  uploadImage(filePath) {
    return http.uploadFile(filePath, '/moment/upload', 'file')
  },

  // 发布动态(两步发布第二步)
  publish(data) {
    // data: { content, images: [url], location }
    return http.post('/moment/publish', data)
  },

  // 获取动态列表
  getList(page = 1, pageSize = 20) {
    return http.get('/moment/list', { page, page_size: pageSize })
  },

  // 获取动态详情
  getDetail(momentId) {
    return http.get(`/moment/detail/${momentId}`)
  },

  // 删除动态(联动清理图片)
  delete(momentId) {
    return http.del(`/moment/delete/${momentId}`)
  },

  // 点赞/取消点赞(toggle)
  toggleLike(momentId) {
    return http.post(`/moment/like/${momentId}`)
  },

  // 获取点赞用户列表
  getLikers(momentId) {
    return http.get(`/moment/likers/${momentId}`)
  },

  // 发表评论
  comment(momentId, content, replyToId = 0) {
    return http.post(`/moment/comment/${momentId}`, {
      content,
      reply_to_id: replyToId
    })
  },

  // 获取评论列表
  getComments(momentId) {
    return http.get(`/moment/comments/${momentId}`)
  }
}
