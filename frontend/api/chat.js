/**
 * AI 对话 API
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /** 获取对话历史 */
  getChatHistory() {
    if (USE_MOCK) return mock.getChatHistory()
    return http.get('/chat/history')
  },

  /** 发送消息 (非流式，与后端 /chat/send SSE 不匹配，仅作降级用) */
  sendMessage(content, personality = 'cute') {
    if (USE_MOCK) return mock.sendMessage(content, personality)
    return http.post('/chat/send', {
      content,
      role_type: personality,
      dialogue_style: 'gentle',
      scene_type: 'daily',
      scene_name: '',
      session_id: 0,
    })
  },

  /**
   * 流式发送消息 (SSE)
   * @param {string} content - 用户消息
   * @param {function} onChunk - 每收到一段文字回调 (chunk: string) => void
   * @param {object} context - 上下文 { role_type, dialogue_style, scene_type, scene_name, session_id }
   * @returns {Promise<string>} 完整AI回复
   */
  async streamSend(content, onChunk, context = {}) {
    if (USE_MOCK) {
      return mock.streamSend(content, onChunk, context)
    }
    // 真实API: SSE流式，对齐后端 ChatSendRequest 字段
    return http.streamPost('/chat/send', {
      content,
      role_type: context.role_type || 'companion',
      // v3.1：真实角色标识（ai_roles.role_type）。后端据此注入人设 + 隔离记忆。
      // 不传时后端回退到 role_type，老行为不变。
      role_key: context.role_key || '',
      dialogue_style: context.dialogue_style || 'gentle',
      scene_type: context.scene_type || 'daily',
      scene_name: context.scene_name || '',
      session_id: context.session_id || 0,
      // 2026-10-28 打卡上下文延续：本次对话挂载哪条习惯的完整历程。
      // 不传时后端沿用会话已挂载的习惯（持久化）；传 -1 表示显式退出习惯专题。
      habit_id: (typeof context.habit_id === 'number') ? context.habit_id : undefined,
      // 多语言：BCP-47 语种码（en-US / ja-JP ...），后端据此让 AI 用该语种回复；空值=默认中文
      language: context.language || '',
    }, onChunk, null, null, (meta) => {
      // 会话 id 回传：带上之后服务端才攒得下历史，AI 才能记住前面聊过什么
      if (meta && meta.sessionId && typeof context.onSessionId === 'function') {
        context.onSessionId(meta.sessionId)
      }
      // 习惯会话模式状态回传
      if (meta && meta.habitContext && typeof context.onHabitContext === 'function') {
        context.onHabitContext(meta.habitContext)
      }
    })
  },

  /**
   * 前端危机预检
   * @param {string} content - 用户输入文本
   * @returns {Promise<object>} { is_crisis, severity, keywords, response, hotline }
   */
  crisisCheck(content) {
    if (USE_MOCK) return mock.crisisCheck(content)
    return http.post('/chat/crisis-check', { content })
  }
}
