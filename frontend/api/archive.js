/**
 * 成长档案 API
 * 对应后端 /api/v1/archive 端点
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /** 获取成长报告 (monthly/quarterly/yearly) */
  getReport(period = 'monthly') {
    if (USE_MOCK) return mock.getArchiveReport(period)
    return http.get('/archive/report', { period })
  },

  /** 获取档案列表 */
  getList() {
    if (USE_MOCK) return mock.getArchiveList()
    return http.get('/archive/list')
  },

  /** 数据导出 (json/csv) */
  exportData(format = 'json') {
    if (USE_MOCK) return mock.exportArchiveData(format)
    return http.get('/archive/export', { format })
  },

  /** 生成分享文本 */
  shareReport(period = 'monthly') {
    if (USE_MOCK) return mock.shareArchiveReport(period)
    return http.get('/archive/share', { period })
  }
}
