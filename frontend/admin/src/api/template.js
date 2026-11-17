/**
 * 任务模板管理 API
 */
import service from './request'

export default {
  getTemplateList(params) {
    return service.get('/admin/templates', { params })
  },
  createTemplate(data) {
    return service.post('/admin/templates', data)
  },
  updateTemplate(id, data) {
    return service.put(`/admin/templates/${id}`, data)
  },
  deleteTemplate(id) {
    return service.delete(`/admin/templates/${id}`)
  }
}
