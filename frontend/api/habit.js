/**
 * 习惯 API - 习惯管理/打卡
 * 后端前缀：/habit（单数）
 * 补卡端点改为 POST /habit/checkin/makeup，body 带 { habit_id, makeup_date }
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /** 获取今日习惯列表 */
  getTodayHabits() {
    if (USE_MOCK) return mock.getTodayHabits()
    return http.get('/habit/today')
  },

  /** 获取所有习惯（includePaused=1 时把已暂停的也带上，方便在列表里「重新拾起来」） */
  getAllHabits(includePaused = 0) {
    if (USE_MOCK) return mock.getAllHabits()
    return http.get('/habit/list', { include_paused: includePaused })
  },

  /** 打卡 */
  checkin(habitId) {
    if (USE_MOCK) return mock.checkin(habitId)
    return http.post('/habit/checkin', { habit_id: habitId })
  },

  /** 取消打卡 */
  uncheckin(habitId) {
    if (USE_MOCK) return mock.uncheckin(habitId)
    return http.post(`/habit/uncheckin/${habitId}`)
  },

  /**
   * 补卡（补昨日漏卡，仅 1 天宽限期内有效）
   * body 带 habit_id 和 makeup_date（null 时后端默认昨天）
   */
  makeupCheckin(habitId, makeupDate = null) {
    if (USE_MOCK) return mock.makeupCheckin(habitId)
    return http.post('/habit/checkin/makeup', {
      habit_id: habitId,
      makeup_date: makeupDate,
    })
  },

  /** 获取习惯模板列表 */
  getTemplates() {
    if (USE_MOCK) return mock.getTemplates()
    return http.get('/habit/templates')
  },

  /** 添加习惯(从模板) */
  addHabit(templateId) {
    if (USE_MOCK) return mock.addHabit(templateId)
    return http.post(`/habit/templates/${templateId}/use`)
  },

  /** 创建自定义习惯 */
  createHabit(data) {
    if (USE_MOCK) return mock.createHabit(data)
    return http.post('/habit/create', data)
  },

  /** 删除习惯 */
  deleteHabit(habitId) {
    if (USE_MOCK) return mock.deleteHabit(habitId)
    return http.del(`/habit/delete/${habitId}`)
  },

  /** 获取AI鼓励语(打卡成功/取消时) */
  getEncouragement(data) {
    if (USE_MOCK) return mock.getEncouragement(data)
    return http.post('/habit/encouragement', data)
  },

  /** 提交打卡日记（保存用户写的日记文本，使用 CheckinDiary 表，与 AI 生成的 habit-ai/diary 不同） */
  submitDiary(data) {
    if (USE_MOCK) return mock.submitDiary(data)
    return http.post(`/habit/${data.habit_id}/checkin/diary`, data)
  },

  /** 获取打卡日记列表 */
  getDiaries(habitId) {
    if (USE_MOCK) return mock.getDiaries(habitId)
    return http.get(`/habit/${habitId || ''}/checkin/diary`)
  },

  /** 获取成就奖励列表 */
  getAchievements(habitId) {
    if (USE_MOCK) return mock.getAchievements(habitId)
    return http.get(`/habit/${habitId || ''}/achievements`)
  },

  /** 检查成就解锁 */
  checkAchievements(data) {
    if (USE_MOCK) return mock.checkAchievements(data)
    return http.post(`/habit/${data.habit_id}/achievements/check`, data)
  },

  // ↓↓↓ 新增（2026-10-28）习惯-伙伴融合 ↓↓↓
  // 说明：以下均为本次新增能力，mock.js 没有对应实现，故不接 USE_MOCK 分支（USE_MOCK 本就是 false）

  /** 暂停习惯（数据保留，期间不校验、不催、不列入今日待办） */
  pauseHabit(habitId, reason = '') {
    return http.post(`/habit/${habitId}/pause`, { reason })
  },

  /** 重启习惯 */
  resumeHabit(habitId) {
    return http.post(`/habit/${habitId}/resume`, {})
  },

  /** 上报「今天没做到」（只陪伴，不说教） */
  markMissed(habitId, emotion = '') {
    return http.post(`/habit/${habitId}/missed`, { emotion })
  },

  /** 习惯完整过往：开启时间 / 中断 / 重启时间线（伙伴据此不失忆） */
  getHabitStory(habitId) {
    return http.get(`/habit/${habitId}/story`)
  },

  /** 习惯相关记忆（可按习惯、按事件细分） */
  getHabitMemories(habitId = 0, event = '') {
    return http.get('/memory/list', { topic: 'habit', habit_id: habitId, event })
  },

  /** 口头打卡解析：只询问，不直接打卡 */
  verbalParse(text) {
    return http.post('/habit/verbal/parse', { text })
  },

  /** 口头打卡确认 */
  verbalConfirm(habitId, confirmed, emotion = '') {
    return http.post('/habit/verbal/confirm', { habit_id: habitId, confirmed, emotion })
  },

  /** 世界剧情碎片素材（习惯经历） */
  getWorldFragment(habitId) {
    return http.get(`/habit/${habitId}/world-fragment`)
  },

  /** 习惯话题总开关：读取 */
  getCompanionSetting() {
    return http.get('/habit/companion/setting')
  },

  /** 习惯话题总开关：保存 */
  saveCompanionSetting(data) {
    return http.put('/habit/companion/setting', data)
  },

  /** 陪伴向复盘（只讲一起走过的事，不打分、不排名） */
  getCompanionReview(days = 30) {
    return http.get('/stats/companion-review', { days })
  },

  /** 月度陪伴向复盘 */
  getMonthlyCompanion(year = 0, month = 0) {
    return http.get('/archive/monthly-companion', { year, month })
  },

  // ↓↓↓ 新增（2026-10-28 打卡上下文延续） ↓↓↓
  /** 把这条习惯短期静默（默认 3 天）：不挂会话上下文、不主动提起 */
  muteHabitTopic(habitId, days = 3) {
    return http.post('/habit/topic/mute', { habit_id: habitId, days })
  },

  /** 解除静默（用户自己又聊起它时） */
  unmuteHabitTopic(habitId) {
    return http.post('/habit/topic/unmute', { habit_id: habitId })
  }
  // ↑↑↑ 新增结束 ↑↑↑
}
