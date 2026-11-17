<template>
  <div class="dashboard-page" v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-body">
            <div class="stat-icon" :style="{ background: card.color }">
              <el-icon :size="28"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-extra" v-if="card.extra">
                <el-icon v-if="card.trend === 'up'" color="#67C23A"><Top /></el-icon>
                <el-icon v-else-if="card.trend === 'down'" color="#F56C6C"><Bottom /></el-icon>
                {{ card.extra }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>用户增长趋势 (近30天)</span>
            </div>
          </template>
          <div ref="userTrendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>AI角色分布</span>
            </div>
          </template>
          <div ref="roleChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>打卡趋势 (近7天)</span>
            </div>
          </template>
          <div ref="checkinTrendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>习惯类型分布</span>
            </div>
          </template>
          <div ref="habitChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近操作 -->
    <el-card shadow="hover" class="activity-card">
      <template #header>
        <div class="card-header">
          <span>最近操作动态</span>
        </div>
      </template>
      <el-table :data="recentActivities" stripe size="default">
        <el-table-column prop="adminName" label="操作人" width="120" />
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getActionTagType(row.action)">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="120" />
        <el-table-column prop="createdAt" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import dashboardApi from '@/api/dashboard'
import {
  User, TrendCharts, Check, ChatLineRound, Top, Bottom
} from '@element-plus/icons-vue'

const loading = ref(true)
const stats = ref(null)
const recentActivities = ref([])

// 图表引用
const userTrendChartRef = ref(null)
const roleChartRef = ref(null)
const checkinTrendChartRef = ref(null)
const habitChartRef = ref(null)

let userTrendChart = null
let roleChart = null
let checkinTrendChart = null
let habitChart = null

// 统计卡片
const statCards = ref([])

const getActionTagType = (action) => {
  const map = {
    '登录': 'info',
    '更新用户状态': 'warning',
    '创建模板': 'success',
    '更新AI角色': 'primary',
    '审核内容': 'warning',
    '删除模板': 'danger'
  }
  return map[action] || 'info'
}

const initStatCards = () => {
  const o = stats.value.overview
  statCards.value = [
    { title: '总用户数', value: o.totalUsers, icon: User, color: 'linear-gradient(135deg, #667eea, #764ba2)', extra: `今日新增 ${o.newUsersToday}`, trend: 'up' },
    { title: '活跃用户', value: o.activeUsers, icon: TrendCharts, color: 'linear-gradient(135deg, #f093fb, #f5576c)', extra: `占比 ${Math.round(o.activeUsers / o.totalUsers * 100)}%`, trend: 'up' },
    { title: '今日打卡', value: o.todayCheckins, icon: Check, color: 'linear-gradient(135deg, #4facfe, #00f2fe)', extra: `累计 ${o.totalCheckins}`, trend: 'up' },
    { title: '平均完成率', value: o.avgCompletionRate + '%', icon: ChatLineRound, color: 'linear-gradient(135deg, #43e97b, #38f9d7)', extra: `AI对话 ${o.aiConversations}次`, trend: 'up' }
  ]
}

const initCharts = () => {
  // 用户增长趋势
  if (userTrendChartRef.value) {
    userTrendChart = echarts.init(userTrendChartRef.value)
    const trend = stats.value.userTrend
    userTrendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['累计用户', '新增用户'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
      xAxis: { type: 'category', data: trend.map(d => d.date), axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value' },
      series: [
        {
          name: '累计用户',
          type: 'line',
          smooth: true,
          data: trend.map(d => d.total),
          itemStyle: { color: '#667eea' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.4)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
          ]) }
        },
        {
          name: '新增用户',
          type: 'bar',
          data: trend.map(d => d.new),
          itemStyle: { color: '#f5576c', borderRadius: [4, 4, 0, 0] }
        }
      ]
    })
  }

  // AI角色分布
  if (roleChartRef.value) {
    roleChart = echarts.init(roleChartRef.value)
    roleChart.setOption({
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      legend: { bottom: 0, left: 'center' },
      series: [{
        name: 'AI角色',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '45%'],
        data: stats.value.roleDistribution.map(d => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: d.color }
        })),
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' } }
      }]
    })
  }

  // 打卡趋势
  if (checkinTrendChartRef.value) {
    checkinTrendChart = echarts.init(checkinTrendChartRef.value)
    const trend = stats.value.checkinTrend
    checkinTrendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['打卡次数', '完成率(%)'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
      xAxis: { type: 'category', data: trend.map(d => d.date) },
      yAxis: [
        { type: 'value', name: '次数' },
        { type: 'value', name: '完成率', axisLabel: { formatter: '{value}%' } }
      ],
      series: [
        {
          name: '打卡次数',
          type: 'bar',
          data: trend.map(d => d.count),
          itemStyle: { color: '#4facfe', borderRadius: [6, 6, 0, 0] }
        },
        {
          name: '完成率(%)',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: trend.map(d => d.rate),
          itemStyle: { color: '#43e97b' },
          lineStyle: { width: 3 }
        }
      ]
    })
  }

  // 习惯类型分布
  if (habitChartRef.value) {
    habitChart = echarts.init(habitChartRef.value)
    habitChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '5%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: stats.value.habitDistribution.map(d => d.name), axisLabel: { fontSize: 11 } },
      series: [{
        name: '用户数',
        type: 'bar',
        data: stats.value.habitDistribution.map(d => ({
          value: d.value,
          itemStyle: { color: d.color, borderRadius: [0, 6, 6, 0] }
        })),
        label: { show: true, position: 'right' }
      }]
    })
  }
}

const handleResize = () => {
  userTrendChart?.resize()
  roleChart?.resize()
  checkinTrendChart?.resize()
  habitChart?.resize()
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await dashboardApi.getStats()
    stats.value = res.data
    recentActivities.value = res.data.recentActivities
    initStatCards()
    await nextTick()
    initCharts()
    window.addEventListener('resize', handleResize)
  } catch (e) {
    console.error('Dashboard加载失败:', e)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  userTrendChart?.dispose()
  roleChart?.dispose()
  checkinTrendChart?.dispose()
  habitChart?.dispose()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  min-height: 100%;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 10px;

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-extra {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 320px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.activity-card {
  margin-bottom: 20px;
}
</style>
