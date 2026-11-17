/**
 * 正念冥想 API - 音频列表 / 练习记录 / 练习计划 / 知识库 / AI引导
 * 后端端点: /mindfulness/audio/list | /mindfulness/session/* | /mindfulness/plan/*
 *
 * 字段映射：
 *   前端 duration_minutes → 后端 duration_min
 *   前端 category         → 后端 session_type
 *   updatePlan 对齐 plan/toggle 语义（只切换启用状态，不传 data）
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /**
   * 获取音频列表（按分类/时长筛选）
   * @param {Object} params - { audio_type?, duration? }
   * @returns {Promise} { list, total }
   */
  getAudios(params = {}) {
    if (USE_MOCK) return mock.getMeditationAudios(params)
    return http.get('/mindfulness/audio/list', params)
  },

  /**
   * 获取音频详情
   * @param {Number} audioId
   * @returns {Promise} 音频详情对象
   */
  getAudio(audioId) {
    if (USE_MOCK) return mock.getMeditationAudio(audioId)
    return http.get(`/mindfulness/audio/${audioId}`)
  },

  /**
   * 创建练习记录（含情绪前后对比）
   * @param {Object} data - { audio_id, session_type/category, duration_min/duration_minutes, completed, emotion_before, emotion_after, intensity_before, intensity_after }
   * @returns {Promise} { id, completed, duration_min, emotion_before, emotion_after }
   */
  createRecord(data) {
    if (USE_MOCK) return mock.createMeditationRecord(data)
    // 字段对齐后端 schema MindfulnessSessionCreate
    return http.post('/mindfulness/session/create', {
      session_type: data.session_type || data.category || 'meditation',
      duration_min: data.duration_min || data.duration_minutes || 10,
      audio_id: data.audio_id || 0,
      emotion_before: data.emotion_before || '',
      emotion_after: data.emotion_after || '',
      intensity_before: data.intensity_before || 0,
      intensity_after: data.intensity_after || 0,
      completed: data.completed ?? 1,
    })
  },

  /**
   * 获取练习记录列表
   * @param {Object} params - { page?, page_size?, category? }
   * @returns {Promise} { list, total, page, page_size }
   */
  getRecords(params = {}) {
    if (USE_MOCK) return mock.getMeditationRecords(params)
    return http.get('/mindfulness/session/list', params)
  },

  /**
   * 获取练习统计
   * @returns {Promise} { total_minutes, total_sessions, completed_sessions, streak_days, avg_duration, category_stats }
   */
  getStats() {
    if (USE_MOCK) return mock.getMeditationStats()
    return http.get('/mindfulness/stats')
  },

  /**
   * 创建练习计划
   * @param {Object} data - { plan_type, session_type, reminder_time, week_days }
   * @returns {Promise} 计划对象
   */
  createPlan(data) {
    if (USE_MOCK) return mock.createMeditationPlan(data)
    // ↓↓↓ 修复 ↓↓↓ 页面表单给的是 { name, target_days, target_duration, preferred_category }，
    // 后端 MindfulnessPlanCreate 只收 { plan_type, session_type, reminder_time, week_days }，
    // 直接透传会被 pydantic 拦成 422，用户看到的就是「创建失败」。这里做字段映射。
    return http.post('/mindfulness/plan/create', {
      plan_type: data.plan_type || 'daily',
      session_type: data.session_type || data.preferred_category || 'meditation',
      name: data.name || '',
      target_days: data.target_days || 7,
      target_duration: data.target_duration || 10,
      reminder_time: data.reminder_time || '08:00',
      week_days: data.week_days || ''
    })
  },

  /**
   * 获取当前练习计划
   * @returns {Promise} 计划对象或null
   */
  getPlan() {
    if (USE_MOCK) return mock.getMeditationPlan()
    return http.get('/mindfulness/plan/list')
  },

  /**
   * 启用/停用计划（对齐后端 plan/toggle 语义，仅切换 active，不传 data）
   * 页面层应移除"标记今日完成"按钮，改为"启用/停用计划"开关
   * @param {Number} planId
   * @returns {Promise} { id, active }
   */
  updatePlan(planId) {
    if (USE_MOCK) return mock.updateMeditationPlan(planId)
    return http.put(`/mindfulness/plan/toggle/${planId}`)
  },

  /**
   * 获取正念知识库
   * @returns {Promise} 知识卡片数组
   */
  getKnowledge() {
    if (USE_MOCK) return mock.getMeditationKnowledge()
    return http.get('/mindfulness/knowledge')
  },

  /**
   * 获取AI引导语（练习中根据进度生成）
   * @param {Object} data - { category, phase, elapsed_minutes, total_minutes }
   * @returns {Promise} { guide_text, next_phase }
   */
  getGuide(data) {
    if (USE_MOCK) return mock.getMeditationGuide(data)
    return http.post('/mindfulness/guide', data)
  }
}
