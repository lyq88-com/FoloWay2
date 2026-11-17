<template>
  <view v-if="visible" class="popup-mask" @click="closePanel">
    <view class="panel-content" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <text class="panel-title">数据统计</text>
        <view class="period-tabs">
          <text
            v-for="p in periods"
            :key="p.key"
            class="period-tab"
            :class="{ active: currentPeriod === p.key }"
            @click="currentPeriod = p.key"
          >{{ p.label }}</text>
        </view>
        <text class="panel-close" @click="closePanel">✕</text>
      </view>

      <scroll-view scroll-y class="panel-body">
        <!-- 概览卡片 -->
        <view class="overview-cards">
          <view class="overview-card">
            <text class="overview-num">{{ stats.completionRate }}%</text>
            <text class="overview-label">完成率</text>
          </view>
          <view class="overview-card">
            <text class="overview-num">{{ stats.maxStreak }}</text>
            <text class="overview-label">连续天数</text>
          </view>
          <view class="overview-card">
            <text class="overview-num">{{ stats.totalFocusTime }}m</text>
            <text class="overview-label">坚持时长</text>
          </view>
          <view class="overview-card">
            <text class="overview-num">{{ stats.incompleteCount }}</text>
            <text class="overview-label">未完成</text>
          </view>
        </view>

        <!-- 折线图 -->
        <view class="chart-card">
          <view class="chart-header">
            <text class="chart-title">{{ periodLabel }}完成趋势</text>
          </view>
          <view class="line-chart">
            <view class="chart-y-axis">
              <text v-for="tick in yTicks" :key="tick" class="y-tick">{{ tick }}</text>
            </view>
            <view class="chart-area">
              <!-- 网格线 -->
              <view v-for="i in 5" :key="'grid'+i" class="grid-line"></view>
              <!-- 折线 -->
              <view class="line-container">
                <view class="line-svg-wrap">
                  <view
                    v-for="(point, idx) in linePoints"
                    :key="'pt'+idx"
                    class="line-point"
                    :style="{ left: point.x + '%', bottom: point.y + '%' }"
                  >
                    <view class="point-dot"></view>
                    <view v-if="idx < lineSegments.length" class="line-segment" :style="lineSegments[idx]"></view>
                  </view>
                </view>
              </view>
              <!-- X轴标签 -->
              <view class="x-labels">
                <text v-for="(label, idx) in xLabels" :key="'xl'+idx" class="x-label">{{ label }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 饼图 -->
        <view class="chart-card">
          <view class="chart-header">
            <text class="chart-title">习惯完成分布</text>
          </view>
          <view class="pie-chart-area">
            <view class="pie-chart">
              <view class="pie-center">
                <text class="pie-center-num">{{ stats.totalCheckins }}</text>
                <text class="pie-center-label">总打卡</text>
              </view>
              <view
                v-for="(slice, idx) in pieSlices"
                :key="'slice'+idx"
                class="pie-slice"
                :style="slice.style"
              ></view>
            </view>
            <view class="pie-legend">
              <view v-for="(item, idx) in pieData" :key="'leg'+idx" class="legend-item">
                <view class="legend-color" :style="{ background: item.color }"></view>
                <text class="legend-name">{{ item.name }}</text>
                <text class="legend-value">{{ item.value }}次</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 各习惯详细数据 -->
        <view class="chart-card">
          <view class="chart-header">
            <text class="chart-title">单项习惯统计</text>
          </view>
          <view
            v-for="habit in habitStats"
            :key="habit.id"
            class="habit-stat-row"
          >
            <view class="habit-stat-info">
              <text class="habit-stat-icon">{{ habit.icon }}</text>
              <view class="habit-stat-text">
                <text class="habit-stat-name">{{ habit.name }}</text>
                <text class="habit-stat-detail">连续{{ habit.streak }}天 / 完成{{ habit.total }}次</text>
              </view>
            </view>
            <view class="habit-stat-bar-wrap">
              <view class="habit-stat-bar" :style="{ width: habit.completionPct + '%', background: habit.color }"></view>
            </view>
            <text class="habit-stat-pct">{{ habit.completionPct }}%</text>
          </view>
        </view>

        <!-- 每周完成频次 -->
        <view class="chart-card">
          <view class="chart-header">
            <text class="chart-title">每周完成频次</text>
          </view>
          <view class="bar-chart">
            <view v-for="(bar, idx) in weeklyBars" :key="'bar'+idx" class="bar-col">
              <view class="bar-wrap">
                <view class="bar-fill" :style="{ height: bar.height + '%', background: bar.color }"></view>
              </view>
              <text class="bar-label">{{ bar.label }}</text>
              <text class="bar-value">{{ bar.value }}</text>
            </view>
          </view>
        </view>

        <!-- AI改进建议 -->
        <view class="chart-card ai-suggestion-card">
          <view class="chart-header">
            <text class="chart-title">AI 本周改进建议</text>
            <view class="ai-tag"><text>AI</text></view>
          </view>
          <view class="ai-suggestion-content">
            <view class="ai-suggestion-avatar">{{ aiAvatar }}</view>
            <view class="ai-suggestion-text">
              <text class="suggestion-text">{{ aiSuggestion }}</text>
              <view class="suggestion-refresh" @click="generateAISuggestion">
                <text>换一条建议</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 导出按钮 -->
        <view class="export-section">
          <view class="export-btn" @click="exportData">
            <text class="export-icon">📤</text>
            <text class="export-text">导出统计数据</text>
          </view>
        </view>
        <view class="form-bottom-space"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'statistics-panel',
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      currentPeriod: 'week',
      periods: [
        { key: 'day', label: '日' },
        { key: 'week', label: '周' },
        { key: 'month', label: '月' }
      ],
      habits: [],
      walkHistory: [],
      emotionRecords: [],
      aiSuggestion: '',
      aiAvatar: '🌸'
    }
  },
  computed: {
    periodLabel() {
      const map = { day: '今日', week: '本周', month: '本月' }
      return map[this.currentPeriod] || '本周'
    },
    stats() {
      const habits = this.habits
      const completed = habits.filter(h => h.completed).length
      const total = habits.length
      const completionRate = total > 0 ? Math.round(completed / total * 100) : 0
      const maxStreak = habits.reduce((max, h) => Math.max(max, h.streak || 0), 0)
      const incompleteCount = total - completed
      // 从行走历史中计算专注时长
      const walkHistory = this.walkHistory || []
      const periodMs = this.getPeriodMs()
      const now = Date.now()
      const recentHistory = walkHistory.filter(h => now - (h.timestamp || 0) < periodMs)
      const totalFocusTime = recentHistory.reduce((sum, h) => {
        if (h.type === 'meditation') return sum + 5
        if (h.type === 'habit') return sum + 10
        return sum
      }, 0)
      const totalCheckins = this.$store.getters.totalCheckins || 0
      return { completionRate, maxStreak, totalFocusTime, incompleteCount, totalCheckins }
    },
    yTicks() {
      return ['100%', '75%', '50%', '25%', '0%']
    },
    xLabels() {
      if (this.currentPeriod === 'day') {
        return ['06', '09', '12', '15', '18', '21']
      } else if (this.currentPeriod === 'week') {
        return ['一', '二', '三', '四', '五', '六', '日']
      } else {
        return ['1', '8', '15', '22', '30']
      }
    },
    linePoints() {
      const data = this.trendData
      if (data.length === 0) return []
      const max = Math.max(...data, 100)
      return data.map((val, idx) => ({
        x: (idx / Math.max(1, data.length - 1)) * 100,
        y: (val / max) * 100
      }))
    },
    lineSegments() {
      const pts = this.linePoints
      const segs = []
      for (let i = 0; i < pts.length - 1; i++) {
        const p1 = pts[i]
        const p2 = pts[i + 1]
        const dx = p2.x - p1.x
        const dy = p2.y - p1.y
        const len = Math.sqrt(dx * dx + dy * dy)
        const angle = Math.atan2(-dy, dx) * 180 / Math.PI
        segs.push({
          position: 'absolute',
          left: p1.x + '%',
          bottom: p1.y + '%',
          width: len + '%',
          height: '3px',
          background: '#6B8E7B',
          transform: 'rotate(' + angle + 'deg)',
          transformOrigin: '0 50%',
          borderRadius: '2px'
        })
      }
      return segs
    },
    trendData() {
      if (this.currentPeriod === 'day') {
        return [20, 40, 60, 50, 70, 80]
      } else if (this.currentPeriod === 'week') {
        const walkHistory = this.walkHistory || []
        const now = new Date()
        const dayOfWeek = now.getDay() || 7
        const weekStart = new Date(now)
        weekStart.setDate(now.getDate() - dayOfWeek + 1)
        weekStart.setHours(0, 0, 0, 0)
        const data = []
        for (let i = 0; i < 7; i++) {
          const dayStart = weekStart.getTime() + i * 86400000
          const dayEnd = dayStart + 86400000
          const count = walkHistory.filter(h => h.timestamp >= dayStart && h.timestamp < dayEnd).length
          data.push(count * 20)
        }
        return data
      } else {
        const data = []
        const now = new Date()
        const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
        const buckets = 5
        const perBucket = Math.ceil(daysInMonth / buckets)
        for (let b = 0; b < buckets; b++) {
          const startDay = b * perBucket + 1
          const endDay = Math.min(startDay + perBucket - 1, daysInMonth)
          const count = this.walkHistory.filter(h => {
            const d = new Date(h.timestamp || 0)
            return d.getMonth() === now.getMonth() && d.getDate() >= startDay && d.getDate() <= endDay
          }).length
          data.push(count * 15)
        }
        return data
      }
    },
    pieData() {
      const habits = this.habits
      const colors = ['#6B8E7B', '#4FC3F7', '#FF6B6B', '#FFD93D', '#4DD0E1', '#7986CB', '#BA68C8', '#81C784']
      if (habits.length === 0) {
        return [{ name: '暂无数据', value: 1, color: '#E0E0E0' }]
      }
      return habits.slice(0, 8).map((h, idx) => ({
        name: h.name || '未命名',
        value: h.streak || 1,
        color: h.color || colors[idx % colors.length]
      }))
    },
    pieSlices() {
      const total = this.pieData.reduce((sum, d) => sum + d.value, 0)
      let currentAngle = 0
      return this.pieData.map(d => {
        const angle = (d.value / total) * 360
        const style = this.buildPieSliceStyle(currentAngle, angle, d.color)
        currentAngle += angle
        return { style }
      })
    },
    habitStats() {
      const habits = this.habits
      return habits.map(h => {
        const total = h.streak || 0
        const completed = h.completed ? 1 : 0
        const completionPct = total > 0 ? Math.min(100, Math.round(total / Math.max(total, 7) * 100)) : 0
        return {
          id: h.id,
          icon: h.icon || '⭐',
          name: h.name,
          streak: h.streak || 0,
          total: total,
          completionPct,
          color: h.color || '#6B8E7B'
        }
      })
    },
    weeklyBars() {
      const walkHistory = this.walkHistory || []
      const now = new Date()
      const labels = ['一', '二', '三', '四', '五', '六', '日']
      const dayOfWeek = now.getDay() || 7
      const weekStart = new Date(now)
      weekStart.setDate(now.getDate() - dayOfWeek + 1)
      weekStart.setHours(0, 0, 0, 0)
      const bars = []
      for (let i = 0; i < 7; i++) {
        const dayStart = weekStart.getTime() + i * 86400000
        const dayEnd = dayStart + 86400000
        const count = walkHistory.filter(h => h.timestamp >= dayStart && h.timestamp < dayEnd).length
        bars.push({
          label: labels[i],
          value: count,
          height: Math.min(100, count * 20),
          color: i === dayOfWeek - 1 ? '#6B8E7B' : '#B0D0C0'
        })
      }
      return bars
    },
    aiCharacterId() {
      return this.$store.state.aiConfig?.avatarType || 'linxi'
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadData()
        this.generateAISuggestion()
      }
    }
  },
  methods: {
    loadData() {
      this.habits = this.$store.state.habits || []
      this.walkHistory = this.$store.state.walkMap?.walkHistory || []
      this.emotionRecords = this.$store.state.emotionRecords || []
      this.aiAvatar = this.getAIAvatar(this.aiCharacterId)
    },
    getPeriodMs() {
      if (this.currentPeriod === 'day') return 86400000
      if (this.currentPeriod === 'week') return 86400000 * 7
      return 86400000 * 30
    },
    getAIAvatar(charId) {
      const avatars = {
        linxi: '🌸', mianmian: '🍑', yuki: '⚡', kira: '🗡️', yueqing: '🌙',
        fengye: '🍁', nova: '🤖', zero: '📊', xingchen: '✨', muhan: '📜',
        qinghe: '🌿', chenfeng: '💨', sunny: '☀️', lele: '😄', linglong: '🔔',
        baihu: '🐯', qinglan: '🕊️', xuanwu: '🐢', huoyun: '🔥', linling: '💝'
      }
      return avatars[charId] || '🌸'
    },
    buildPieSliceStyle(startAngle, angle, color) {
      const radius = 120
      const cx = 50
      const cy = 50
      const startRad = (startAngle - 90) * Math.PI / 180
      const endRad = (startAngle + angle - 90) * Math.PI / 180
      const x1 = cx + radius * Math.cos(startRad)
      const y1 = cy + radius * Math.sin(startRad)
      const x2 = cx + radius * Math.cos(endRad)
      const y2 = cy + radius * Math.sin(endRad)
      const largeArc = angle > 180 ? 1 : 0
      if (angle >= 360) {
        return {
          background: color,
          borderRadius: '50%',
          position: 'absolute',
          top: '0',
          left: '0',
          width: '100%',
          height: '100%'
        }
      }
      const path = `M${cx},${cy} L${x1},${y1} A${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} Z`
      return {
        clipPath: `path('${path}')`,
        background: color,
        position: 'absolute',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%'
      }
    },
    generateAISuggestion() {
      const completionRate = this.stats.completionRate
      const maxStreak = this.stats.maxStreak
      const incompleteCount = this.stats.incompleteCount
      const suggestions = []
      if (completionRate >= 80) {
        suggestions.push(`太棒了！${this.periodLabel}完成率${completionRate}%，继续保持这个节奏！你的AI伙伴为你感到骄傲~`)
        suggestions.push(`连续${maxStreak}天的坚持很了不起！建议你尝试增加一个新习惯，挑战自己~`)
      } else if (completionRate >= 50) {
        suggestions.push(`${this.periodLabel}完成率${completionRate}%，还有提升空间。建议把每日提醒时间调整到你最活跃的时段~`)
        suggestions.push(`你已坚持${maxStreak}天，但还有${incompleteCount}个任务未完成。试试把它们拆分成更小的步骤~`)
        suggestions.push(`数据显示你在下午时段完成率偏低，可以尝试把重要习惯安排在上午~`)
      } else {
        suggestions.push(`完成率${completionRate}%有些偏低，别担心！从小目标开始，每天完成1-2个就好~`)
        suggestions.push(`看起来最近有些松懈，这很正常。建议从最简单的习惯重新开始打卡~`)
        suggestions.push(`连续${maxStreak}天的记录说明你有能力坚持！让我们重新找回节奏吧~`)
      }
      if (this.walkHistory.length > 0) {
        const lastActive = this.walkHistory[this.walkHistory.length - 1]
        const daysSince = Math.floor((Date.now() - (lastActive.timestamp || 0)) / 86400000)
        if (daysSince > 2) {
          suggestions.push(`已经${daysSince}天没有打卡了，AI伙伴想你了！从今天的一个小习惯开始吧~`)
        }
      }
      this.aiSuggestion = suggestions[Math.floor(Math.random() * suggestions.length)]
    },
    exportData() {
      const data = {
        exportDate: new Date().toISOString(),
        period: this.currentPeriod,
        stats: this.stats,
        habitStats: this.habitStats,
        trendData: this.trendData,
        weeklyBars: this.weeklyBars,
        walkHistory: this.walkHistory.slice(-100)
      }
      try {
        uni.setStorageSync('ahp_stats_export', JSON.stringify(data))
        uni.setClipboardData({
          data: JSON.stringify(data, null, 2),
          success: () => {
            uni.showToast({ title: '统计数据已复制到剪贴板', icon: 'none' })
          }
        })
      } catch (e) {
        uni.showToast({ title: '导出失败', icon: 'none' })
      }
    },
    closePanel() {
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.popup-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.panel-content {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.panel-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
}
.period-tabs {
  display: flex;
  background: #F5F6F7;
  border-radius: 24rpx;
  padding: 4rpx;
}
.period-tab {
  padding: 8rpx 24rpx;
  font-size: 24rpx;
  color: #999;
  border-radius: 20rpx;
}
.period-tab.active {
  background: #6B8E7B;
  color: #fff;
}
.panel-close {
  font-size: 36rpx;
  color: #999;
  padding: 8rpx;
}
.panel-body {
  flex: 1;
  padding: 24rpx 32rpx;
  max-height: 78vh;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.overview-card {
  background: linear-gradient(135deg, #F8F9FA 0%, #F0F7F3 100%);
  border-radius: 20rpx;
  padding: 28rpx 24rpx;
  text-align: center;
}
.overview-num {
  font-size: 48rpx;
  font-weight: 700;
  color: #6B8E7B;
  display: block;
}
.overview-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
  display: block;
}

/* 图表卡片 */
.chart-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  border: 1rpx solid #F5F5F5;
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}
.chart-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}
.ai-tag {
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
}
.ai-tag text {
  font-size: 20rpx;
  color: #fff;
  font-weight: 600;
}

/* 折线图 */
.line-chart {
  display: flex;
  height: 280rpx;
}
.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 60rpx;
  padding-right: 8rpx;
}
.y-tick {
  font-size: 18rpx;
  color: #ccc;
  text-align: right;
}
.chart-area {
  flex: 1;
  position: relative;
  padding-bottom: 32rpx;
}
.grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1rpx;
  background: #F0F0F0;
}
.grid-line:nth-child(1) { top: 0; }
.grid-line:nth-child(2) { top: 25%; }
.grid-line:nth-child(3) { top: 50%; }
.grid-line:nth-child(4) { top: 75%; }
.grid-line:nth-child(5) { bottom: 32rpx; }
.line-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 32rpx;
}
.line-svg-wrap {
  position: relative;
  width: 100%;
  height: 100%;
}
.line-point {
  position: absolute;
}
.point-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #6B8E7B;
  border: 3rpx solid #fff;
  box-shadow: 0 2rpx 6rpx rgba(107, 142, 123, 0.3);
  position: absolute;
  bottom: -8rpx;
  left: -8rpx;
}
.line-segment {
  transform-origin: 0 50%;
}
.x-labels {
  display: flex;
  justify-content: space-between;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}
.x-label {
  font-size: 18rpx;
  color: #ccc;
}

/* 饼图 */
.pie-chart-area {
  display: flex;
  align-items: center;
  gap: 32rpx;
}
.pie-chart {
  position: relative;
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
}
.pie-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: #fff;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.pie-center-num {
  font-size: 36rpx;
  font-weight: 700;
  color: #6B8E7B;
}
.pie-center-label {
  font-size: 20rpx;
  color: #999;
}
.pie-slice {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.pie-legend {
  flex: 1;
}
.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}
.legend-color {
  width: 20rpx;
  height: 20rpx;
  border-radius: 6rpx;
  margin-right: 12rpx;
  flex-shrink: 0;
}
.legend-name {
  flex: 1;
  font-size: 24rpx;
  color: #666;
}
.legend-value {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

/* 单项统计 */
.habit-stat-row {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #F5F5F5;
}
.habit-stat-row:last-child {
  border-bottom: none;
}
.habit-stat-info {
  display: flex;
  align-items: center;
  width: 200rpx;
  flex-shrink: 0;
}
.habit-stat-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}
.habit-stat-text {
  flex: 1;
}
.habit-stat-name {
  font-size: 26rpx;
  color: #333;
  display: block;
  font-weight: 500;
}
.habit-stat-detail {
  font-size: 20rpx;
  color: #999;
  display: block;
}
.habit-stat-bar-wrap {
  flex: 1;
  height: 12rpx;
  background: #F5F6F7;
  border-radius: 6rpx;
  overflow: hidden;
  margin: 0 16rpx;
}
.habit-stat-bar {
  height: 100%;
  border-radius: 6rpx;
  transition: width 0.3s ease;
}
.habit-stat-pct {
  font-size: 24rpx;
  color: #6B8E7B;
  font-weight: 600;
  width: 60rpx;
  text-align: right;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  height: 240rpx;
  padding-top: 20rpx;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.bar-wrap {
  width: 40rpx;
  height: 160rpx;
  display: flex;
  align-items: flex-end;
  background: #F5F6F7;
  border-radius: 8rpx 8rpx 0 0;
  overflow: hidden;
}
.bar-fill {
  width: 100%;
  border-radius: 8rpx 8rpx 0 0;
  transition: height 0.3s ease;
}
.bar-label {
  font-size: 20rpx;
  color: #999;
  margin-top: 8rpx;
}
.bar-value {
  font-size: 20rpx;
  color: #6B8E7B;
  font-weight: 600;
}

/* AI建议 */
.ai-suggestion-card {
  background: linear-gradient(135deg, #F0F7F3 0%, #E8F5E9 100%);
}
.ai-suggestion-content {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}
.ai-suggestion-avatar {
  font-size: 40rpx;
  flex-shrink: 0;
}
.ai-suggestion-text {
  flex: 1;
}
.suggestion-text {
  font-size: 26rpx;
  color: #333;
  line-height: 1.6;
  display: block;
  margin-bottom: 12rpx;
}
.suggestion-refresh {
  display: inline-block;
  padding: 8rpx 24rpx;
  background: rgba(107, 142, 123, 0.15);
  border-radius: 20rpx;
}
.suggestion-refresh text {
  font-size: 22rpx;
  color: #6B8E7B;
}

/* 导出 */
.export-section {
  margin-bottom: 24rpx;
}
.export-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80rpx;
  background: #F5F6F7;
  border-radius: 40rpx;
  gap: 12rpx;
}
.export-btn:active {
  background: #E8E8E8;
}
.export-icon {
  font-size: 28rpx;
}
.export-text {
  font-size: 28rpx;
  color: #666;
}
.form-bottom-space {
  height: 120rpx;
}
</style>
