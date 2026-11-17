import http from '@/common/request'

/**
 * 活动模块接口
 * 路径前缀: /activity
 * 后端: server/app/api/v1/activity.py（每日签到 + 活跃任务进度）
 */
export default {
  /** 签到状态（不写库） */
  getSignin() {
    return http.get('/activity/signin')
  },

  /** 签到（一天只成功一次） */
  signin() {
    return http.post('/activity/signin', {})
  },

  /** 活跃任务进度 */
  getTasks() {
    return http.get('/activity/tasks')
  }
}
