/**
 * 性格测评 API - 云端版（对接 FastAPI 8000，统一走 /api/v1 前缀）
 * - GET    /personality/result  { completed, result }
 * - POST   /personality/result  { personality, emotionalResilience, procrastination,
 *                                 companionStyle, rawScores, answers, source }
 * - GET    /personality/history?limit=20
 * - DELETE /personality/result  重置（生效记录转历史）
 *
 * 说明：本模块所有方法都已 try 到调用方的兜底里，抛错不会影响本地流程。
 */
import http from '@/common/request'

export default {
  /** 取当前生效的测评结果；未测/游客返回 { completed:false, result:null } */
  async getResult() {
    const res = await http.get('/personality/result')
    return (res && res.data) || { completed: false, result: null }
  },

  /** 保存/重测，返回落库后的结果对象 */
  async saveResult(payload) {
    const res = await http.post('/personality/result', payload)
    return (res && res.data) || null
  },

  /** 测评历史 */
  async getHistory(limit = 20) {
    const res = await http.get('/personality/history', { limit })
    return (res && res.data) || { total: 0, list: [] }
  },

  /** 重置云端测评（当前生效记录转历史） */
  async reset() {
    const res = await http.del('/personality/result')
    return (res && res.data) || null
  }
}
