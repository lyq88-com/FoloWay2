/**
 * AI角色管理 API
 */
import service from './request'

export default {
  getRoleList() {
    return service.get('/admin/roles')
  },
  createRole(data) {
    return service.post('/admin/roles', data)
  },
  updateRole(id, data) {
    return service.put(`/admin/roles/${id}`, data)
  },
  deleteRole(id) {
    return service.delete(`/admin/roles/${id}`)
  },
  getRoleAssets(roleId) {
    return service.get(`/admin/roles/${roleId}/assets`)
  },
  updateRoleAsset(roleId, assetId, data) {
    return service.put(`/admin/roles/${roleId}/assets/${assetId}`, data)
  }
}
