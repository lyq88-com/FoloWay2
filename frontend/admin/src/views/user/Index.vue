<template>
  <div class="user-page">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :inline="true" :model="searchForm" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="昵称/手机号"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" value="1" />
            <el-option label="禁用" value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="userList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column label="用户" width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="36">{{ row.avatar || row.nickname.charAt(0) }}</el-avatar>
              <div class="user-info">
                <div class="user-name">{{ row.nickname }}</div>
                <div class="user-phone">{{ row.phone }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="genderText" label="性别" width="80" align="center" />
        <el-table-column prop="levelName" label="等级" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="warning">Lv.{{ row.level }} {{ row.levelName }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="habitCount" label="习惯数" width="80" align="center" />
        <el-table-column prop="totalCheckins" label="总打卡" width="90" align="center" />
        <el-table-column prop="streakDays" label="连续天数" width="90" align="center">
          <template #default="{ row }">
            <span :class="{ 'streak-hot': row.streakDays >= 7 }">🔥 {{ row.streakDays }}天</span>
          </template>
        </el-table-column>
        <el-table-column prop="aiRole" label="AI伙伴" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :color="getRoleColor(row.aiRole)" effect="dark">
              {{ getRoleName(row.aiRole) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="statusText" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.statusText }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="registerTime" label="注册时间" width="180" />
        <el-table-column prop="lastLoginTime" label="最后登录" width="180" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="handleDetail(row)">详情</el-button>
            <el-button
              size="small"
              :type="row.status === 1 ? 'danger' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '封禁' : '解封' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="detailVisible" title="用户详情" width="700px" top="5vh">
      <div v-loading="detailLoading">
        <template v-if="userDetail">
          <!-- 基本信息 -->
          <el-descriptions :column="2" border class="detail-section">
            <el-descriptions-item label="头像">
              <el-avatar :size="48">{{ userDetail.avatar || userDetail.nickname.charAt(0) }}</el-avatar>
            </el-descriptions-item>
            <el-descriptions-item label="昵称">{{ userDetail.nickname }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ userDetail.phone }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ userDetail.genderText }}</el-descriptions-item>
            <el-descriptions-item label="等级">Lv.{{ userDetail.level }} {{ userDetail.levelName }}</el-descriptions-item>
            <el-descriptions-item label="AI伙伴">{{ getRoleName(userDetail.aiRole) }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ userDetail.registerTime }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ userDetail.lastLoginTime }}</el-descriptions-item>
          </el-descriptions>

          <!-- 习惯列表 -->
          <h4 class="detail-title">用户习惯</h4>
          <el-row :gutter="12">
            <el-col :span="8" v-for="habit in userDetail.habits" :key="habit.id">
              <el-card shadow="hover" class="habit-mini-card">
                <div class="habit-mini-header">
                  <span class="habit-icon">{{ habit.icon }}</span>
                  <span class="habit-name">{{ habit.name }}</span>
                </div>
                <div class="habit-mini-info">
                  <span>目标: {{ habit.target }}</span>
                  <el-tag size="small" :type="habit.difficulty === 'easy' ? 'success' : habit.difficulty === 'medium' ? 'warning' : 'danger'">
                    {{ habit.difficulty }}
                  </el-tag>
                </div>
                <div class="habit-mini-streak">连续 {{ habit.streak }} 天</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 最近打卡 -->
          <h4 class="detail-title">最近7天打卡</h4>
          <el-table :data="userDetail.recentCheckins" size="small" border>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="完成情况" align="center">
              <template #default="{ row }">
                {{ row.completed }} / {{ row.total }}
              </template>
            </el-table-column>
            <el-table-column label="完成率" width="200">
              <template #default="{ row }">
                <el-progress :percentage="row.rate" :color="row.rate >= 67 ? '#67C23A' : row.rate >= 34 ? '#E6A23C' : '#F56C6C'" />
              </template>
            </el-table-column>
          </el-table>

          <!-- 徽章 -->
          <h4 class="detail-title">已获徽章</h4>
          <div class="badge-list">
            <div v-for="badge in userDetail.badges" :key="badge.id" class="badge-item">
              <span class="badge-icon">{{ badge.icon }}</span>
              <span class="badge-name">{{ badge.name }}</span>
            </div>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import userApi from '@/api/user'

const loading = ref(false)
const userList = ref([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const userDetail = ref(null)

const searchForm = reactive({
  keyword: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const roleMap = {
  cute: { name: '小萌', color: '#FF9800' },
  gentle: { name: '暖阳', color: '#FFC107' },
  serious: { name: '严师', color: '#607D8B' },
  energetic: { name: '闪电', color: '#E91E63' }
}

const getRoleName = (type) => roleMap[type]?.name || type
const getRoleColor = (type) => roleMap[type]?.color || '#909399'

const fetchList = async () => {
  loading.value = true
  try {
    const res = await userApi.getUserList({
      page: pagination.page,
      pageSize: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status
    })
    userList.value = res.data.list
    pagination.total = res.data.total
  } catch (e) {
    console.error('获取用户列表失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  fetchList()
}

const handleDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await userApi.getUserDetail(row.id)
    userDetail.value = res.data
  } catch (e) {
    console.error('获取用户详情失败:', e)
  } finally {
    detailLoading.value = false
  }
}

const handleToggleStatus = async (row) => {
  const action = row.status === 1 ? '封禁' : '解封'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.nickname}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userApi.updateUserStatus(row.id, row.status === 1 ? 0 : 1)
    ElMessage.success(`${action}成功`)
    fetchList()
  } catch (e) {
    // 用户取消或请求失败
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.user-page {
  min-height: 100%;
}

.search-card {
  margin-bottom: 16px;

  :deep(.el-card__body) {
    padding: 18px 20px 0;
  }
}

.table-card {
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info {
  .user-name {
    font-size: 14px;
    color: #303133;
    font-weight: 500;
  }
  .user-phone {
    font-size: 12px;
    color: #909399;
  }
}

.streak-hot {
  color: #F56C6C;
  font-weight: 600;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  margin: 20px 0 12px;
  font-size: 15px;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}

.habit-mini-card {
  margin-bottom: 12px;

  :deep(.el-card__body) {
    padding: 12px;
  }
}

.habit-mini-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  .habit-icon {
    font-size: 24px;
  }
  .habit-name {
    font-weight: 600;
    color: #303133;
  }
}

.habit-mini-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.habit-mini-streak {
  font-size: 12px;
  color: #F56C6C;
  font-weight: 500;
}

.badge-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.badge-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f0f9ff;
  border-radius: 20px;
  border: 1px solid #d0e8ff;

  .badge-icon {
    font-size: 20px;
  }
  .badge-name {
    font-size: 13px;
    color: #303133;
  }
}
</style>
