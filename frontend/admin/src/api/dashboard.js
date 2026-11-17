/**
 * 看板统计 API
 */
import service from './request'

export default {
  getStats() {
    return service.get('/admin/dashboard/stats')
  }
}
