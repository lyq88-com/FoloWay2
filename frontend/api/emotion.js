/**
 * 情绪记录 API - 情绪打卡 / 趋势分析 / 触发因素
 * 后端端点: /emotion/create | /emotion/list | /emotion/trend | /emotion/distribution | /emotion/triggers | /emotion/delete/{id}
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /**
   * 创建情绪记录（支持补录）
   * @param {Object} data - { emotion, intensity, tags, description, record_date, habit_id }
   * @returns {Promise} { id, emotion, intensity, record_date, ai_reply }
   */
  createEmotion(data) {
    if (USE_MOCK) return mock.createEmotion(data)
    return http.post('/emotion/create', data)
  },

  /**
   * 获取情绪记录列表（分页）
   * @param {Object} params - { page, page_size }
   * @returns {Promise} { list, total, page, page_size }
   */
  getEmotionList(params = {}) {
    if (USE_MOCK) return mock.getEmotionList(params)
    return http.get('/emotion/list', params)
  },

  /**
   * 情绪趋势分析
   * @param {String} period - '7d' | '30d' | '90d'
   * @returns {Promise} { labels, intensities, emotions, distribution }
   */
  getEmotionTrend(period = '7d') {
    if (USE_MOCK) return mock.getEmotionTrend(period)
    return http.get('/emotion/trend', { period })
  },

  /**
   * 情绪分布统计
   * @param {String} period - '7d' | '30d' | '90d'
   * @returns {Promise} { distribution, total }
   */
  getEmotionDistribution(period = '30d') {
    if (USE_MOCK) return mock.getEmotionDistribution(period)
    return http.get('/emotion/distribution', { period })
  },

  /**
   * 触发因素分析
   * @param {String} period - '7d' | '30d' | '90d'
   * @returns {Promise} [{ tag, count, avg_intensity, negative_ratio }]
   */
  getEmotionTriggers(period = '30d') {
    if (USE_MOCK) return mock.getEmotionTriggers(period)
    return http.get('/emotion/triggers', { period })
  },

  /**
   * 删除情绪记录
   * @param {Number} recordId
   */
  deleteEmotion(recordId) {
    if (USE_MOCK) return mock.deleteEmotion(recordId)
    return http.del(`/emotion/delete/${recordId}`)
  }
}
