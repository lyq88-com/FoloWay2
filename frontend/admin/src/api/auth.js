/**
 * 认证 API
 */
import service from './request'

export default {
  login(username, password) {
    return service.post('/admin/login', { username, password })
  },
  getAdminInfo() {
    return service.get('/admin/info')
  },
  logout() {
    return service.post('/admin/logout')
  }
}
