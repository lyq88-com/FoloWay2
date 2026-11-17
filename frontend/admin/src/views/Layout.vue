<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo-section">
        <div class="logo-icon">🎯</div>
        <span v-show="!isCollapse" class="logo-text">AI习惯伙伴</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        class="layout-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/user">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/role">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI角色素材</span>
        </el-menu-item>
        <el-menu-item index="/template">
          <el-icon><List /></el-icon>
          <span>任务模板</span>
        </el-menu-item>
        <el-menu-item index="/content">
          <el-icon><Document /></el-icon>
          <span>内容管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <div class="admin-info">
              <el-avatar :size="32" class="admin-avatar">
                {{ adminInfo?.nickname?.charAt(0) || 'A' }}
              </el-avatar>
              <span class="admin-name">{{ adminInfo?.nickname || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <el-icon><UserFilled /></el-icon>
                  {{ adminInfo?.roleName || '管理员' }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  DataAnalysis, User, ChatDotRound, List, Document,
  Fold, Expand, ArrowDown, UserFilled, SwitchButton
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapse = ref(false)
const adminInfo = ref(null)

onMounted(async () => {
  try {
    await authStore.fetchAdminInfo()
    adminInfo.value = authStore.adminInfo
  } catch (e) {
    // 如果获取信息失败，用本地数据
    adminInfo.value = { nickname: '管理员', roleName: '管理员' }
  }
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (e) {
    // 用户取消
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.layout-aside {
  background: #304156;
  transition: width 0.3s;
  overflow-x: hidden;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 60px;
  background: #2b3a4d;
  color: #fff;

  .logo-icon {
    font-size: 24px;
  }

  .logo-text {
    font-size: 18px;
    font-weight: 600;
    white-space: nowrap;
  }
}

.layout-menu {
  border-right: none;

  &:not(.el-menu--collapse) {
    width: 220px;
  }
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;

  .collapse-btn {
    font-size: 20px;
    cursor: pointer;
    color: #5a5e66;

    &:hover {
      color: #409eff;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0 8px;

  .admin-avatar {
    background: #409eff;
    color: #fff;
  }

  .admin-name {
    font-size: 14px;
    color: #303133;
  }
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
