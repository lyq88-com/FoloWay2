/**
 * 用户管理 API
 */
import service from './request'

export default {
  getUserList(params) {
    return service.get('/admin/users', { params })
  },
  getUserDetail(id) {
    return service.get(`/admin/users/${id}`)
  },
  updateUserStatus(id, status) {
    return service.put(`/admin/users/${id}/status`, { status })
  }
}
