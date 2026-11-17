import http from '@/common/request'

/**
 * 【四大新增模块·模块2】日程提醒接口封装
 * 路径前缀: /schedule (BASE_URL = /api/v1 已在 request.js 内拼接)
 */
export default {
  // 创建日程 { title, description, schedule_date, start_time, end_time, habit_id, remind_minutes }
  create(data) {
    return http.post('/schedule/create', data)
  },

  // 查询日程: day=YYYY-MM-DD 查单日 / month=YYYY-MM 查整月
  getList({ day = '', month = '' } = {}) {
    return http.get('/schedule/list', { day, month })
  },

  // 日程详情
  getDetail(id) {
    return http.get(`/schedule/detail/${id}`)
  },

  // 更新日程(字段可选)
  update(id, data) {
    return http.put(`/schedule/update/${id}`, data)
  },

  // 删除日程
  remove(id) {
    return http.del(`/schedule/delete/${id}`)
  },

  // AI伙伴根据打卡情况生成建议日程
  aiGenerate(forDate) {
    return http.post('/schedule/ai-generate', { for_date: forDate })
  },

  // 完成日程(绑定习惯则自动打卡)
  complete(id) {
    return http.post(`/schedule/complete/${id}`)
  },

  // 提醒扫描: 返回到点该提醒的日程(含AI伙伴提醒文案)
  remindScan() {
    return http.get('/schedule/remind/scan')
  }
}
