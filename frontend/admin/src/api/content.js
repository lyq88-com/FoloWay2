/**
 * 内容审核 API
 */
import service from './request'

export default {
  getChatContents(params) {
    return service.get('/admin/content/chats', { params })
  },
  getCheckinContents(params) {
    return service.get('/admin/content/checkins', { params })
  },
  reviewContent(id, status) {
    return service.put(`/admin/content/${id}/review`, { status })
  },
  getBadges() {
    return service.get('/admin/badges')
  },
  getLogs(params) {
    return service.get('/admin/logs', { params })
  }
}
