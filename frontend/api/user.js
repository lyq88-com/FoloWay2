/**
 * 用户 API - 个人信息/徽章/AI配置
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /** 获取用户信息 (后端: GET /auth/info) */
  getUserInfo() {
    if (USE_MOCK) return mock.getUserInfo()
    return http.get('/auth/info')
  },

  /** 获取徽章列表 (后端: GET /badges/my) */
  getBadges() {
    if (USE_MOCK) return mock.getBadges()
    return http.get('/badges/my')
  },

  /** 获取AI角色列表 (后端: GET /chat/personas) */
  getAiRoles() {
    if (USE_MOCK) return mock.getAiRoles()
    return http.get('/chat/personas')
  },

  /** 获取AI情绪素材/问候语 (后端: GET /chat/greeting) */
  getAiEmotion(status) {
    if (USE_MOCK) return mock.getAiEmotion(status)
    return http.get('/chat/greeting')
  },

  /** 更新AI配置 (后端暂无，本地存储) */
  updateAiConfig(config) {
    if (USE_MOCK) return mock.updateAiConfig(config)
    // 暂存到本地
    uni.setStorageSync('ai_config', config)
    return Promise.resolve({ updated: true, config })
  },

  /** 更新设置 (后端暂无，本地存储) */
  updateSettings(settings) {
    if (USE_MOCK) return mock.updateSettings(settings)
    uni.setStorageSync('user_settings', settings)
    return Promise.resolve({ updated: true, settings })
  },

  /** 更新用户资料 (后端: PUT /user/update) */
  updateProfile(data) {
    if (USE_MOCK) return mock.updateProfile(data)
    return http.put('/user/update', data)
  },

  // ↓↓↓ 新增 ↓↓↓ 编辑个人资料：云端资料读取 + 头像上传
  /** 读取云端用户资料 (后端: GET /user/info，含 phone / signature) */
  getProfile() {
    if (USE_MOCK) return mock.getUserInfo()
    return http.get('/user/info')
  },

  /** 上传头像 (后端: POST /user/avatar，字段名 file) */
  uploadAvatar(filePath) {
    if (USE_MOCK) {
      // mock 模式直接回本地临时路径，避免上传报错打断流程
      return Promise.resolve({
        code: 200, message: 'ok',
        data: { url: filePath, path: filePath, avatar: filePath }
      })
    }
    return http.uploadFile(filePath, '/user/avatar', 'file')
  }
  // ↑↑↑ 新增 ↑↑↑
}
