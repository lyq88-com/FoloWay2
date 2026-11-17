import http from '@/common/request'

/**
 * 长效记忆接口（陪伴感增强 v3）
 * 路径前缀: /memory
 *
 * 三层：profile 长期固定信息 / event 对话事件 / preference 偏好
 * 全部接口都带 role_key —— 记忆跟角色走，A 角色记住的内容不会串到 B 角色
 */
export default {
  // 记忆列表（可按分层筛选） { role_key, layer, page, page_size }
  getList(params = {}) {
    return http.get('/memory/list', params)
  },

  // 各层记忆数量 { role_key }
  getStats(roleKey = '') {
    return http.get('/memory/stats', { role_key: roleKey })
  },

  // 手动补一条记忆 { content, layer, title, salience, role_key }
  add(data) {
    return http.post('/memory/add', data)
  },

  // 编辑一条记忆 { content, title, layer, salience }
  update(id, data) {
    return http.put(`/memory/${id}`, data)
  },

  // 单条删除（软删除）
  remove(id) {
    return http.del(`/memory/${id}`)
  },

  // 一键清空 { role_key }；传 all=true 清空所有角色
  clear(roleKey = '', allRoles = false) {
    return http.del('/memory/clear', { role_key: roleKey, all_roles: allRoles })
  },

  // 从一段文本里按规则抽取记忆 { text, role_key }
  extract(text, roleKey = '') {
    return http.post('/memory/extract', { text, role_key: roleKey })
  }
}
