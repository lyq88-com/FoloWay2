import http from '@/common/request'

/**
 * 主动陪伴接口（陪伴感增强 v3）
 * 路径前缀: /proactive
 *
 * 不是只有用户发消息才回应：打开会话时拉一条 TA 主动说的话
 */
export default {
  // 取一条主动消息 { role_key, session_id, fast }
  // 返回 data=null 表示这会儿没什么值得主动说的，前端不要硬塞气泡
  next(roleKey = '', sessionId = 0, fast = false) {
    return http.get('/proactive/next', {
      role_key: roleKey,
      session_id: sessionId || undefined,
      fast
    })
  },

  // 主动互动历史
  history(roleKey = '', limit = 20) {
    return http.get('/proactive/history', { role_key: roleKey, limit })
  },

  // 标记已读
  markRead(id) {
    return http.post(`/proactive/${id}/read`)
  }
}
