/**
 * 管理员认证 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const adminInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const res = await authApi.login(username, password)
    token.value = res.data.token
    adminInfo.value = res.data.admin
    localStorage.setItem('admin_token', res.data.token)
    return res
  }

  async function fetchAdminInfo() {
    const res = await authApi.getAdminInfo()
    adminInfo.value = res.data
    return res
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // 忽略登出请求失败
    }
    token.value = ''
    adminInfo.value = null
    localStorage.removeItem('admin_token')
  }

  return {
    token,
    adminInfo,
    isLoggedIn,
    login,
    fetchAdminInfo,
    logout
  }
})
