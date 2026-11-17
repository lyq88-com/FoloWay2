import http from '@/common/request'

/**
 * 【四大新增模块·模块1+4】虚拟世界 + AI角色互动笔记接口封装
 * 路径前缀: /world
 * 世界笔记类型: normal=普通 / checkin=用户打卡笔记 / feedback=AI打卡反馈
 */
export default {
  // 可入驻的AI角色列表(创建世界时选择)
  getAiRoles() {
    return http.get('/world/ai-roles')
  },

  // 创建世界 { name, description, rules, is_public, role_ids:[], custom_roles:[], checkin_target }
  create(data) {
    return http.post('/world/create', data)
  },

  // 世界列表 tab=public(公开广场)/mine(我的世界)
  getList(tab = 'public') {
    return http.get('/world/list', { tab })
  },

  // 世界详情(成员/剧情解锁/我的打卡数)
  getDetail(worldId) {
    return http.get(`/world/detail/${worldId}`)
  },

  // 加入公开世界
  join(worldId) {
    return http.post('/world/join', { world_id: worldId })
  },

  // 追加AI角色/自设角色(仅创建者) { role_id } 或 { custom_name }
  addRole(worldId, data) {
    return http.post(`/world/add-role/${worldId}`, data)
  },

  // 离开世界(创建者则为删除世界)
  leave(worldId) {
    return http.post(`/world/leave/${worldId}`)
  },

  // 成员列表
  getMembers(worldId) {
    return http.get(`/world/members/${worldId}`)
  },

  // 用户发布笔记 { content, note_type }
  publishNote(worldId, content, noteType = 'normal') {
    return http.post(`/world/note/${worldId}`, { content, note_type: noteType })
  },

  // 笔记流
  getNotes(worldId) {
    return http.get(`/world/notes/${worldId}`)
  },

  // 评论笔记(AI会回复, 还可能触发AI互评与关系变化)
  comment(noteId, content, replyToId = 0) {
    return http.post(`/world/comment/${noteId}`, { content, reply_to_id: replyToId })
  },

  // 笔记评论列表
  getComments(noteId) {
    return http.get(`/world/comments/${noteId}`)
  },

  // AI角色关系图谱数据
  getRelations(worldId) {
    return http.get(`/world/relations/${worldId}`)
  },

  // 同世界AI互动消息(AI笔记 + AI互评)
  getAiInteractions(worldId) {
    return http.get(`/world/ai-interactions/${worldId}`)
  }
}
