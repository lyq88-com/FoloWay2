import http from '@/common/request'

/**
 * 角色人设接口（陪伴感增强 v3）
 * 路径前缀: /persona
 *
 * 官方角色：完整人设故事线 / 说话风格 / 小癖好 / 心情状态
 * 自捏角色：雷区、说话禁忌、表达习惯、生气·开心的样子、音色自选
 * 扭蛋角色：抽出来即配套完整独立人设 + 独立记忆空间
 */
export default {
  // 下拉选项：音色 / 心情 / 稀有度
  getOptions() {
    return http.get('/persona/options')
  },

  // 角色列表 scope: all/official/custom/gacha/mine
  getRoles(scope = 'all', detail = false) {
    return http.get('/persona/roles', { scope, detail })
  },

  // 按 role_key 取角色详情
  getRoleByKey(roleKey) {
    return http.get(`/persona/role/key/${encodeURIComponent(roleKey || '')}`, { detail: true })
  },

  // 角色详情
  getRole(id) {
    return http.get(`/persona/role/${id}`, { detail: true })
  },

  // 创建自捏角色
  createRole(data) {
    return http.post('/persona/role', data)
  },

  // 创建前试聊：用表单草稿让 TA 回一句（不落库，纯校验设定是否生效）
  previewRole(data) {
    return http.post('/persona/preview', data)
  },

  // 编辑自捏角色
  updateRole(id, data) {
    return http.put(`/persona/role/${id}`, data)
  },

  // 删除自捏角色（连带清空它名下的记忆）
  removeRole(id) {
    return http.del(`/persona/role/${id}`)
  },

  // 设置角色心情/状态 { mood, moodNote }
  setMood(id, mood, moodNote = '') {
    return http.post(`/persona/role/${id}/mood`, { mood, moodNote })
  },

  // 扭蛋角色池一览
  getGachaPool() {
    return http.get('/persona/gacha/pool')
  },

  // 抽一个角色（完整人设 + 独立记忆空间）
  drawGachaCharacter() {
    return http.post('/persona/gacha/draw')
  }
}
