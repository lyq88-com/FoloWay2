<template>
  <view v-if="visible" class="popup-mask" @click="closePanel">
    <view class="panel-content" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <text class="panel-title">时间轴</text>
        <text class="panel-close" @click="closePanel">✕</text>
      </view>

      <scroll-view scroll-y class="panel-body" @scrolltolower="loadMore">
        <!-- 统计摘要 -->
        <view class="timeline-summary">
          <view class="summary-item">
            <text class="summary-num green">{{ timelineStats.completed }}</text>
            <text class="summary-label">已完成</text>
          </view>
          <view class="summary-item">
            <text class="summary-num orange">{{ timelineStats.makeup }}</text>
            <text class="summary-label">补卡</text>
          </view>
          <view class="summary-item">
            <text class="summary-num red">{{ timelineStats.interrupted }}</text>
            <text class="summary-label">中断</text>
          </view>
          <view class="summary-item">
            <text class="summary-num blue">{{ timelineStats.totalDays }}</text>
            <text class="summary-label">总天数</text>
          </view>
        </view>

        <!-- 地图里程关联 -->
        <view class="map-link-card" @click="goToWalkMap">
          <view class="map-link-info">
            <text class="map-link-icon">🗺️</text>
            <view class="map-link-text">
              <text class="map-link-title">环球行走里程</text>
              <text class="map-link-desc">累计行进 {{ totalCheckins }} 步 / 当前: {{ currentStageName }}</text>
            </view>
          </view>
          <text class="map-link-arrow">›</text>
        </view>

        <!-- 日期选择器 -->
        <view class="date-selector">
          <scroll-view scroll-x class="date-scroll">
            <view class="date-list">
              <view
                v-for="date in dateList"
                :key="date.key"
                class="date-item"
                :class="{ active: selectedDate === date.key }"
                @click="selectDate(date.key)"
              >
                <text class="date-weekday">{{ date.weekday || '' }}</text>
                <text class="date-day">{{ date.day || '' }}</text>
                <view v-if="date.hasRecord" class="date-dot" :class="date.recordType"></view>
              </view>
            </view>
          </scroll-view>
        </view>

        <!-- 时间轴主体 -->
        <view class="timeline-container">
          <view v-if="currentDayRecords.length === 0" class="empty-timeline">
            <text class="empty-icon">📅</text>
            <text class="empty-text">当天暂无记录</text>
          </view>

          <view v-else>
            <!-- 日期标题 -->
            <view class="timeline-date-header">
              <text class="date-title">{{ formatSelectedDate }}</text>
              <view class="date-badge">
                <text>{{ currentDayRecords.length }}条记录</text>
              </view>
            </view>

            <!-- 时间轴列表 -->
            <view class="timeline-list">
              <view
                v-for="(record, idx) in currentDayRecords"
                :key="idx"
                class="timeline-item"
                :class="record.status"
              >
                <view class="timeline-dot-wrap">
                  <view class="timeline-dot" :class="record.status">
                    <text class="dot-icon">{{ getStatusIcon(record.status) }}</text>
                  </view>
                  <view v-if="idx < currentDayRecords.length - 1" class="timeline-line"></view>
                </view>
                <view class="timeline-content">
                  <view class="record-header">
                    <text class="record-icon">{{ record.icon || '⭐' }}</text>
                    <text class="record-name">{{ record.name }}</text>
                    <text class="record-time">{{ record.time }}</text>
                  </view>
                  <view class="record-tags">
                    <view class="record-tag" :class="record.status">
                      <text>{{ getStatusText(record.status) }}</text>
                    </view>
                    <view v-if="record.emotion" class="record-tag emotion">
                      <text>{{ record.emotion }}</text>
                    </view>
                    <view v-if="record.mileage > 0" class="record-tag mileage">
                      <text>🗺️ +{{ record.mileage }}步</text>
                    </view>
                  </view>
                  <view v-if="record.aiMessage" class="record-ai-message">
                    <text class="ai-avatar">{{ aiAvatar }}</text>
                    <text class="ai-message-text">{{ record.aiMessage }}</text>
                  </view>
                  <view v-if="record.note" class="record-note">
                    <text class="note-label">📝 留言</text>
                    <text class="note-content">{{ record.note }}</text>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 图例 -->
        <view class="legend-section">
          <text class="legend-title">标记说明</text>
          <view class="legend-row">
            <view class="legend-item">
              <view class="legend-dot completed"></view>
              <text>正常完成</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot makeup"></view>
              <text>补卡</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot interrupted"></view>
              <text>中断</text>
            </view>
          </view>
        </view>
        <view class="form-bottom-space"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'timeline-panel',
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      selectedDate: '',
      allRecords: {},
      dateList: []
    }
  },
  computed: {
    currentDayRecords() {
      return this.allRecords[this.selectedDate] || []
    },
    formatSelectedDate() {
      if (!this.selectedDate) return ''
      const [y, m, d] = this.selectedDate.split('-')
      return `${y}年${parseInt(m)}月${parseInt(d)}日`
    },
    timelineStats() {
      let completed = 0, makeup = 0, interrupted = 0
      Object.values(this.allRecords).forEach(records => {
        records.forEach(r => {
          if (r.status === 'completed') completed++
          else if (r.status === 'makeup') makeup++
          else if (r.status === 'interrupted') interrupted++
        })
      })
      const totalDays = Object.keys(this.allRecords).length
      return { completed, makeup, interrupted, totalDays }
    },
    totalCheckins() {
      return this.$store.getters.totalCheckins || 0
    },
    currentStageName() {
      const stage = this.$store.getters.currentStage
      return stage ? stage.name : '初始起点'
    },
    aiAvatar() {
      const charId = this.$store.state.aiConfig?.avatarType || 'linxi'
      const avatars = {
        linxi: '🌸', mianmian: '🍑', yuki: '⚡', kira: '🗡️', yueqing: '🌙',
        fengye: '🍁', nova: '🤖', zero: '📊', xingchen: '✨', muhan: '📜',
        qinghe: '🌿', chenfeng: '💨', sunny: '☀️', lele: '😄', linglong: '🔔',
        baihu: '🐯', qinglan: '🕊️', xuanwu: '🐢', huoyun: '🔥', linling: '💝'
      }
      return avatars[charId] || '🌸'
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadData()
        this.buildDateList()
      }
    }
  },
  methods: {
    loadData() {
      // 从Vuex store获取行走历史
      const walkHistory = this.$store.state.walkMap?.walkHistory || []
      // 从本地存储获取打卡留言
      const habitNotes = uni.getStorageSync('habit_notes') || {}
      // 从Vuex获取习惯列表
      const habits = this.$store.state.habits || []
      // 从Vuex获取情绪记录
      const emotionRecords = this.$store.state.emotionRecords || []

      const allRecords = {}

      // 处理行走历史（打卡/情绪/正念记录）
      walkHistory.forEach(h => {
        const date = h.date
        if (!allRecords[date]) allRecords[date] = []
        const time = h.time || '00:00'
        let status = 'completed'
        // 判断是否为补卡（如果是过去日期的记录可能是补卡）
        const recordDate = new Date(date + 'T00:00:00')
        const now = new Date()
        const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
        if (date < todayStr && h.timestamp && (Date.now() - h.timestamp < 86400000 * 2)) {
          // 如果记录时间与日期不匹配，可能为补卡
          const recordTime = new Date(h.timestamp)
          if (recordDate.toDateString() !== new Date(recordTime.getFullYear(), recordTime.getMonth(), recordTime.getDate()).toDateString()) {
            status = 'makeup'
          }
        }
        const habitInfo = habits.find(hb => hb.name === h.description)
        const mileage = h.type === 'habit' ? 1 : (h.type === 'meditation' ? 0.5 : 0.3)
        allRecords[date].push({
          icon: habitInfo?.icon || this.getTypeIcon(h.type),
          name: h.description || '习惯打卡',
          time: time,
          status: status,
          emotion: h.emotion || '',
          mileage: mileage,
          aiMessage: this.getAIMessageForRecord(h, date),
          note: this.getNoteForRecord(habitInfo?.id, date, habitNotes)
        })
      })

      // 处理中断记录（检查哪些天没有打卡）
      this.findInterruptedDays(allRecords)

      // 处理情绪记录
      emotionRecords.forEach(e => {
        const date = this.formatDate(e.date || e.timestamp)
        if (!allRecords[date]) allRecords[date] = []
        // 避免重复
        const exists = allRecords[date].find(r => r.name === e.emotion && r.status === 'completed')
        if (!exists) {
          allRecords[date].push({
            icon: '💭',
            name: `情绪记录: ${e.emotion || '平静'}`,
            time: this.formatTimestamp(e.timestamp),
            status: 'completed',
            emotion: e.emotion || '',
            mileage: 0.3,
            aiMessage: '',
            note: e.note || ''
          })
        }
      })

      // 按时间排序
      Object.keys(allRecords).forEach(date => {
        allRecords[date].sort((a, b) => a.time.localeCompare(b.time))
      })

      this.allRecords = allRecords
    },
    findInterruptedDays(allRecords) {
      const habits = this.$store.state.habits || []
      if (habits.length === 0) return
      // 过去30天内，如果有习惯但没有打卡记录，标记为中断
      const now = new Date()
      for (let i = 1; i <= 30; i++) {
        const d = new Date(now)
        d.setDate(d.getDate() - i)
        const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        const records = allRecords[dateStr] || []
        const hasHabitRecord = records.some(r => r.mileage >= 1)
        if (!hasHabitRecord && habits.length > 0) {
          if (!allRecords[dateStr]) allRecords[dateStr] = []
          allRecords[dateStr].push({
            icon: '❌',
            name: `${habits.length}个习惯未完成`,
            time: '--:--',
            status: 'interrupted',
            emotion: '',
            mileage: 0,
            aiMessage: '这一天没有打卡记录，没关系，偶尔休息一下也是可以的~',
            note: ''
          })
        }
      }
    },
    getAIMessageForRecord(record, date) {
      // 根据记录类型生成AI消息
      const walkHistory = this.$store.state.walkMap?.walkHistory || []
      const sameDayRecords = walkHistory.filter(h => h.date === date)
      // 查找对应的习惯打卡留言
      const habitNotes = uni.getStorageSync('habit_notes') || {}
      for (const [habitId, notes] of Object.entries(habitNotes)) {
        const dayNote = notes.find(n => {
          const noteDate = new Date(n.date)
          const noteDateStr = `${noteDate.getFullYear()}-${String(noteDate.getMonth() + 1).padStart(2, '0')}-${String(noteDate.getDate()).padStart(2, '0')}`
          return noteDateStr === date
        })
        if (dayNote && dayNote.aiResponse) return dayNote.aiResponse
      }
      return ''
    },
    getNoteForRecord(habitId, date, habitNotes) {
      if (!habitId) return ''
      const notes = habitNotes[habitId] || []
      const dayNote = notes.find(n => {
        const noteDate = new Date(n.date)
        const noteDateStr = `${noteDate.getFullYear()}-${String(noteDate.getMonth() + 1).padStart(2, '0')}-${String(noteDate.getDate()).padStart(2, '0')}`
        return noteDateStr === date
      })
      return dayNote ? dayNote.content : ''
    },
    getTypeIcon(type) {
      const icons = { habit: '⭐', emotion: '💭', meditation: '🧘' }
      return icons[type] || '⭐'
    },
    getStatusIcon(status) {
      const icons = { completed: '✓', makeup: '↻', interrupted: '✕' }
      return icons[status] || '•'
    },
    getStatusText(status) {
      const map = { completed: '已完成', makeup: '补卡', interrupted: '中断' }
      return map[status] || '未知'
    },
    formatTimestamp(ts) {
      if (!ts) return '--:--'
      const d = new Date(ts)
      return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    },
    formatDate(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    },
    buildDateList() {
      const list = []
      const now = new Date()
      const weekdays = ['日', '一', '二', '三', '四', '五', '六']
      for (let i = 0; i < 30; i++) {
        const d = new Date(now)
        d.setDate(d.getDate() - i)
        const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        const records = this.allRecords[dateStr] || []
        let recordType = ''
        if (records.length > 0) {
          if (records.some(r => r.status === 'interrupted')) recordType = 'interrupted'
          else if (records.some(r => r.status === 'makeup')) recordType = 'makeup'
          else recordType = 'completed'
        }
        list.push({
          key: dateStr,
          weekday: weekdays[d.getDay()],
          day: d.getDate(),
          hasRecord: records.length > 0,
          recordType
        })
      }
      this.dateList = list
      if (!this.selectedDate) {
        this.selectedDate = list[0].key
      }
    },
    selectDate(key) {
      this.selectedDate = key
    },
    loadMore() {
      // 可扩展加载更早的记录
    },
    goToWalkMap() {
      this.closePanel()
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/walk/walk' })
      }, 300)
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
  justify-content: space-between;
  align-items: center;
  padding: 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.panel-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
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

/* 统计摘要 */
.timeline-summary {
  display: flex;
  justify-content: space-between;
  background: #F8F9FA;
  border-radius: 20rpx;
  padding: 24rpx 16rpx;
  margin-bottom: 20rpx;
}
.summary-item {
  flex: 1;
  text-align: center;
}
.summary-num {
  font-size: 40rpx;
  font-weight: 700;
  display: block;
}
.summary-num.green { color: #4CAF50; }
.summary-num.orange { color: #FF9800; }
.summary-num.red { color: #F44336; }
.summary-num.blue { color: #2196F3; }
.summary-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
  display: block;
}

/* 地图里程关联 */
.map-link-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.map-link-info {
  display: flex;
  align-items: center;
  flex: 1;
}
.map-link-icon {
  font-size: 40rpx;
  margin-right: 16rpx;
}
.map-link-text {
  flex: 1;
}
.map-link-title {
  font-size: 28rpx;
  color: #2E7D32;
  font-weight: 600;
  display: block;
}
.map-link-desc {
  font-size: 22rpx;
  color: #4CAF50;
  margin-top: 4rpx;
  display: block;
}
.map-link-arrow {
  font-size: 40rpx;
  color: #4CAF50;
}

/* 日期选择器 */
.date-selector {
  margin-bottom: 20rpx;
}
.date-scroll {
  white-space: nowrap;
}
.date-list {
  display: flex;
  gap: 12rpx;
  padding: 8rpx 0;
}
.date-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 80rpx;
  height: 100rpx;
  background: #F5F6F7;
  border-radius: 16rpx;
  padding: 12rpx 0;
  position: relative;
  flex-shrink: 0;
}
.date-item.active {
  background: #6B8E7B;
}
.date-weekday {
  font-size: 20rpx;
  color: #999;
}
.date-item.active .date-weekday {
  color: rgba(255, 255, 255, 0.7);
}
.date-day {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-top: 4rpx;
}
.date-item.active .date-day {
  color: #fff;
}
.date-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  margin-top: 6rpx;
}
.date-dot.completed { background: #4CAF50; }
.date-dot.makeup { background: #FF9800; }
.date-dot.interrupted { background: #F44336; }

/* 空状态 */
.empty-timeline {
  text-align: center;
  padding: 80rpx 0;
}
.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 16rpx;
}
.empty-text {
  font-size: 28rpx;
  color: #999;
}

/* 时间轴日期标题 */
.timeline-date-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}
.date-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}
.date-badge {
  background: #E8F5E9;
  padding: 6rpx 20rpx;
  border-radius: 16rpx;
}
.date-badge text {
  font-size: 22rpx;
  color: #6B8E7B;
}

/* 时间轴列表 */
.timeline-list {
  position: relative;
}
.timeline-item {
  display: flex;
  margin-bottom: 8rpx;
}
.timeline-dot-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 56rpx;
  flex-shrink: 0;
}
.timeline-dot {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}
.timeline-dot.completed {
  background: #E8F5E9;
}
.timeline-dot.completed .dot-icon {
  color: #4CAF50;
  font-size: 20rpx;
}
.timeline-dot.makeup {
  background: #FFF3E0;
}
.timeline-dot.makeup .dot-icon {
  color: #FF9800;
  font-size: 20rpx;
}
.timeline-dot.interrupted {
  background: #FFEBEE;
}
.timeline-dot.interrupted .dot-icon {
  color: #F44336;
  font-size: 20rpx;
}
.timeline-line {
  width: 3rpx;
  flex: 1;
  min-height: 40rpx;
  background: #E0E0E0;
  margin-top: 4rpx;
}
.timeline-content {
  flex: 1;
  background: #F8F9FA;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-left: 16rpx;
  margin-bottom: 16rpx;
}
.timeline-item.interrupted .timeline-content {
  background: #FFEBEE;
}
.timeline-item.makeup .timeline-content {
  background: #FFF8E1;
}
.record-header {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}
.record-icon {
  font-size: 28rpx;
  margin-right: 8rpx;
}
.record-name {
  flex: 1;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}
.record-time {
  font-size: 22rpx;
  color: #999;
}
.record-tags {
  display: flex;
  gap: 8rpx;
  margin-bottom: 8rpx;
  flex-wrap: wrap;
}
.record-tag {
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
}
.record-tag.completed {
  background: #E8F5E9;
}
.record-tag.completed text {
  color: #4CAF50;
  font-size: 20rpx;
}
.record-tag.makeup {
  background: #FFF3E0;
}
.record-tag.makeup text {
  color: #FF9800;
  font-size: 20rpx;
}
.record-tag.interrupted {
  background: #FFEBEE;
}
.record-tag.interrupted text {
  color: #F44336;
  font-size: 20rpx;
}
.record-tag.emotion {
  background: #E3F2FD;
}
.record-tag.emotion text {
  color: #2196F3;
  font-size: 20rpx;
}
.record-tag.mileage {
  background: #F3E5F5;
}
.record-tag.mileage text {
  color: #7B1FA2;
  font-size: 20rpx;
}
.record-ai-message {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  background: rgba(107, 142, 123, 0.08);
  border-radius: 12rpx;
  padding: 12rpx;
  margin-top: 8rpx;
}
.ai-avatar {
  font-size: 24rpx;
  flex-shrink: 0;
}
.ai-message-text {
  font-size: 24rpx;
  color: #6B8E7B;
  line-height: 1.5;
  flex: 1;
}
.record-note {
  margin-top: 8rpx;
  padding: 12rpx;
  background: #FFF8E1;
  border-radius: 12rpx;
}
.note-label {
  font-size: 20rpx;
  color: #B8941A;
  display: block;
  margin-bottom: 4rpx;
}
.note-content {
  font-size: 24rpx;
  color: #8B6914;
  line-height: 1.5;
}

/* 图例 */
.legend-section {
  margin-top: 24rpx;
  padding: 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
}
.legend-title {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 12rpx;
}
.legend-row {
  display: flex;
  gap: 32rpx;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.legend-item text {
  font-size: 22rpx;
  color: #666;
}
.legend-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
}
.legend-dot.completed { background: #4CAF50; }
.legend-dot.makeup { background: #FF9800; }
.legend-dot.interrupted { background: #F44336; }

.form-bottom-space {
  height: 120rpx;
}
</style>
