/**
 * Axios 请求封装 - 管理后台对接 FastAPI
 * Mock 模式下拦截请求返回模拟数据
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { setupMock } from '@/mock'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

// 安装 Mock 拦截器
setupMock(service)

// 请求拦截
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截
service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    ElMessage.error(error.message || '网络异常')
    return Promise.reject(error)
  }
)

export default service
