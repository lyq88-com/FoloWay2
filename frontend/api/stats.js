/**
 * 统计 API
 * 后端 /stats/week、/stats/month、/stats/habits 返回数组结构（非 summary 包装）
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /** 获取统计概览 */
  getSummary() {
    if (USE_MOCK) return mock.getStatsSummary()
    return http.get('/stats/summary')
  },

  /** 获取本周打卡数据 [{date, completed, rate}] */
  getWeekData() {
    if (USE_MOCK) return mock.getWeekData()
    return http.get('/stats/week')
  },

  /** 获取月度趋势 [{date, completed, rate}] */
  getMonthData() {
    if (USE_MOCK) return mock.getMonthData()
    return http.get('/stats/month')
  },

  /** 获取习惯维度统计 [{id, name, icon, color, streak, rate, totalCheckins}] */
  getHabitStats() {
    if (USE_MOCK) return mock.getHabitStats()
    return http.get('/stats/habits')
  },

  /** 习惯-情绪关联分析 */
  getHabitEmotionCorrelation() {
    if (USE_MOCK) return mock.getHabitEmotionCorrelation()
    return http.get('/stats/emotion/habit-correlation')
  },

  /** AI成长报告 (weekly/monthly/quarterly/yearly)，参数名 period */
  getGrowthReport(period = 'weekly') {
    if (USE_MOCK) return mock.getGrowthReport(period)
    return http.get('/archive/report', { period })
  },

  /** 数据导出 (json/csv) */
  exportData(format = 'json') {
    if (USE_MOCK) return mock.exportData(format)
    return http.get('/archive/export', { format })
  }
}
