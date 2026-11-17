/**
 * 陪伴模式 API
 * - mock 模式：本地内存记录 + 场景化流式回复
 * - 真实模式：/companion/start /companion/end /companion/records；对话复用 /chat/send (携带场景字段)
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /**
   * 开始陪伴（后端写入 companion_record 表）
   * @param {object} payload { role_id, scene_type, scene_name, bg_img, bg_sound }
   */
  startCompanion(payload) {
    if (USE_MOCK) return mock.companionStart(payload)
    return http.post('/companion/start', payload)
  },

  /**
   * 结束陪伴
   * @param {number} recordId 陪伴记录ID
   */
  endCompanion(recordId) {
    if (USE_MOCK) return mock.companionEnd(recordId)
    return http.post('/companion/end', { record_id: recordId })
  },

  /** 陪伴记录列表 */
  getCompanionRecords() {
    if (USE_MOCK) return mock.companionRecords()
    return http.get('/companion/records')
  },

  /**
   * 陪伴场景下的 AI 对话（流式）
   * 真实模式复用现有 /chat/send 接口，附加 scene_type/scene_name 由后端拼接 system prompt
   * @param {string} content 用户消息
   * @param {function} onChunk 流式回调
   * @param {object} context { sceneType, sceneName, roleId, recentMessages }
   */
  async companionChat(content, onChunk, context = {}) {
    if (USE_MOCK) {
      return mock.companionChat(content, onChunk, context)
    }
    return http.streamPost('/chat/send', {
      content,
      role_type: context.roleType || 'cute',
      // v3.1：真实角色标识，用于注入人设与隔离记忆（不传则后端回退到 role_type）
      role_key: context.roleKey || '',
      scene_type: context.sceneType || '',
      scene_name: context.sceneName || ''
    }, onChunk)
  }
}
