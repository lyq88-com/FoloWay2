<template>
  <div class="content-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <h3>内容管理</h3>
          <span class="toolbar-desc">审核用户聊天记录和打卡内容</span>
        </div>
        <div class="toolbar-right">
          <el-radio-group v-model="activeTab" @change="handleTabChange">
            <el-radio-button value="chats">聊天记录</el-radio-button>
            <el-radio-button value="checkins">打卡内容</el-radio-button>
            <el-radio-button value="badges">徽章管理</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-card>

    <!-- 聊天记录审核 -->
    <template v-if="activeTab === 'chats'">
      <el-card shadow="never" class="filter-card">
        <el-form :inline="true" @submit.prevent>
          <el-form-item label="审核状态">
            <el-select v-model="chatFilter.status" placeholder="全部" clearable style="width: 140px" @change="fetchChats">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
      <el-card shadow="never" class="table-card">
        <el-table :data="chatList" v-loading="chatLoading" stripe border style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column label="用户" width="160">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="32">{{ row.userAvatar }}</el-avatar>
                <span>{{ row.userNickname }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="消息角色" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.role === 'user' ? 'primary' : 'success'" size="small">
                {{ row.role === 'user' ? '用户' : 'AI' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
          <el-table-column label="情绪" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getEmotionType(row.emotion)" size="small">
                {{ getEmotionText(row.emotion) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="审核状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getReviewType(row.reviewStatus)" size="small">
                {{ getReviewText(row.reviewStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="时间" width="180" />
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="success" :disabled="row.reviewStatus === 'approved'" @click="handleReview(row, 'approved')">通过</el-button>
              <el-button size="small" type="danger" :disabled="row.reviewStatus === 'rejected'" @click="handleReview(row, 'rejected')">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="chatPage.page"
            v-model:page-size="chatPage.pageSize"
            :total="chatPage.total"
            layout="total, prev, pager, next"
            @current-change="fetchChats"
          />
        </div>
      </el-card>
    </template>

    <!-- 打卡内容审核 -->
    <template v-if="activeTab === 'checkins'">
      <el-card shadow="never" class="filter-card">
        <el-form :inline="true" @submit.prevent>
          <el-form-item label="审核状态">
            <el-select v-model="checkinFilter.status" placeholder="全部" clearable style="width: 140px" @change="fetchCheckins">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
      <el-card shadow="never" class="table-card">
        <el-table :data="checkinList" v-loading="checkinLoading" stripe border style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column label="用户" width="160">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="32">{{ row.userAvatar }}</el-avatar>
                <span>{{ row.userNickname }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="习惯" width="140">
            <template #default="{ row }">
              <span style="font-size: 16px">{{ getHabitIcon(row.habitType) }}</span>
              {{ row.habitName }}
            </template>
          </el-table-column>
          <el-table-column prop="content" label="打卡文字" min-width="250" show-overflow-tooltip />
          <el-table-column label="图片" width="80" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.hasImage" color="#409EFF" :size="20"><Picture /></el-icon>
              <span v-else style="color: #c0c4cc">无</span>
            </template>
          </el-table-column>
          <el-table-column label="审核状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getReviewType(row.reviewStatus)" size="small">
                {{ getReviewText(row.reviewStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="checkinTime" label="打卡时间" width="180" />
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="success" :disabled="row.reviewStatus === 'approved'" @click="handleReview(row, 'approved')">通过</el-button>
              <el-button size="small" type="danger" :disabled="row.reviewStatus === 'rejected'" @click="handleReview(row, 'rejected')">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="checkinPage.page"
            v-model:page-size="checkinPage.pageSize"
            :total="checkinPage.total"
            layout="total, prev, pager, next"
            @current-change="fetchCheckins"
          />
        </div>
      </el-card>
    </template>

    <!-- 徽章管理 -->
    <template v-if="activeTab === 'badges'">
      <el-card shadow="never" class="table-card">
        <el-table :data="badgeList" v-loading="badgeLoading" stripe border style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" align="center" />
          <el-table-column label="图标" width="60" align="center">
            <template #default="{ row }">
              <span style="font-size: 24px">{{ row.icon }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" width="140" />
          <el-table-column prop="code" label="编码" width="160" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="触发条件" width="200">
            <template #default="{ row }">
              <el-tag size="small">{{ row.conditionType }}</el-tag>
              <span style="margin-left: 8px">≥ {{ row.conditionValue }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="earnedCount" label="获得人数" width="100" align="center">
            <template #default="{ row }">
              <span style="color: #E6A23C; font-weight: 600">{{ row.earnedCount }}人</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import contentApi from '@/api/content'

const activeTab = ref('chats')

// 聊天记录
const chatLoading = ref(false)
const chatList = ref([])
const chatFilter = reactive({ status: '' })
const chatPage = reactive({ page: 1, pageSize: 10, total: 0 })

// 打卡内容
const checkinLoading = ref(false)
const checkinList = ref([])
const checkinFilter = reactive({ status: '' })
const checkinPage = reactive({ page: 1, pageSize: 10, total: 0 })

// 徽章
const badgeLoading = ref(false)
const badgeList = ref([])

const habitIcons = {
  morning: '💧', sport: '🏃', read: '📚', drink: '🥤',
  sleep: '😴', meditate: '🧘', write: '✏️', code: '💻'
}

const getHabitIcon = (type) => habitIcons[type] || '📝'

const getEmotionType = (emotion) => {
  const map = { positive: 'success', negative: 'danger', neutral: 'info' }
  return map[emotion] || 'info'
}

const getEmotionText = (emotion) => {
  const map = { positive: '积极', negative: '消极', neutral: '中性' }
  return map[emotion] || emotion
}

const getReviewType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

const getReviewText = (status) => {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[status] || status
}

const fetchChats = async () => {
  chatLoading.value = true
  try {
    const res = await contentApi.getChatContents({
      page: chatPage.page,
      pageSize: chatPage.pageSize,
      status: chatFilter.status
    })
    chatList.value = res.data.list
    chatPage.total = res.data.total
  } catch (e) {
    console.error('获取聊天记录失败:', e)
  } finally {
    chatLoading.value = false
  }
}

const fetchCheckins = async () => {
  checkinLoading.value = true
  try {
    const res = await contentApi.getCheckinContents({
      page: checkinPage.page,
      pageSize: checkinPage.pageSize,
      status: checkinFilter.status
    })
    checkinList.value = res.data.list
    checkinPage.total = res.data.total
  } catch (e) {
    console.error('获取打卡内容失败:', e)
  } finally {
    checkinLoading.value = false
  }
}

const fetchBadges = async () => {
  badgeLoading.value = true
  try {
    const res = await contentApi.getBadges()
    badgeList.value = res.data.list
  } catch (e) {
    console.error('获取徽章列表失败:', e)
  } finally {
    badgeLoading.value = false
  }
}

const handleTabChange = (tab) => {
  if (tab === 'chats' && chatList.value.length === 0) fetchChats()
  if (tab === 'checkins' && checkinList.value.length === 0) fetchCheckins()
  if (tab === 'badges' && badgeList.value.length === 0) fetchBadges()
}

const handleReview = async (row, status) => {
  try {
    await contentApi.reviewContent(row.id, status)
    ElMessage.success(status === 'approved' ? '已通过' : '已拒绝')
    row.reviewStatus = status
  } catch (e) {
    console.error('审核失败:', e)
  }
}

onMounted(() => {
  fetchChats()
})
</script>

<style scoped lang="scss">
.toolbar-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  h3 {
    margin: 0;
    font-size: 18px;
    color: #303133;
  }
  .toolbar-desc {
    font-size: 13px;
    color: #909399;
    margin-top: 2px;
    display: block;
  }
}

.filter-card {
  margin-bottom: 16px;

  :deep(.el-card__body) {
    padding: 16px 20px 0;
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
  gap: 8px;
  font-size: 14px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
