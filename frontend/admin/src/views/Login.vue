<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>
    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <div class="logo-icon">🎯</div>
        <h2>AI习惯伙伴</h2>
        <p>管理后台</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent>
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>默认账号: admin / admin123</span>
      </div>
    </el-card>
    <div class="login-footer">
      <p>AI习惯伙伴管理系统 &copy; 2026</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, InfoFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } catch (e) {
      // 错误已在拦截器中提示
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);

  &-1 {
    width: 400px;
    height: 400px;
    top: -100px;
    right: -100px;
  }
  &-2 {
    width: 300px;
    height: 300px;
    bottom: -80px;
    left: -80px;
  }
  &-3 {
    width: 200px;
    height: 200px;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.05);
  }
}

.login-card {
  width: 420px;
  border-radius: 16px;
  padding: 20px 10px;
  z-index: 1;

  :deep(.el-card__body) {
    padding: 30px;
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;

  .logo-icon {
    font-size: 48px;
    margin-bottom: 8px;
  }

  h2 {
    font-size: 26px;
    color: #303133;
    margin: 0 0 6px;
  }

  p {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }
}

.login-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}

.login-footer {
  position: absolute;
  bottom: 20px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  z-index: 1;
}
</style>
