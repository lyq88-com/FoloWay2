<template>
  <view class="plan-progress" v-if="plan">
    <!-- 计划概览 -->
    <view class="plan-header">
      <view class="plan-info">
        <text class="plan-name">{{ plan.name }}</text>
        <text class="plan-days">{{ plan.completed_days }}/{{ plan.target_days }}天</text>
      </view>
      <view class="plan-progress-ring">
        <view class="ring-track"></view>
        <view class="ring-fill" :style="ringStyle"></view>
        <text class="ring-text">{{ progressPercent }}%</text>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-segments">
        <view
          v-for="(record, idx) in plan.daily_records"
          :key="idx"
          class="segment"
          :class="{
            completed: record.completed,
            today: isToday(record.date),
            missed: !record.completed && isPast(record.date)
          }"
        >
          <text class="segment-day">{{ getDayLabel(record.date, idx) }}</text>
          <text class="segment-icon">{{ record.completed ? '✓' : (isToday(record.date) ? '●' : '') }}</text>
        </view>
      </view>
    </view>

    <!-- 今日状态 -->
    <view class="today-status" v-if="todayRecord">
      <view class="status-icon" :class="{ done: todayRecord.completed }">
        <text>{{ todayRecord.completed ? '🎉' : '⏳' }}</text>
      </view>
      <view class="status-text">
        <text class="status-title">{{ todayRecord.completed ? '今日已完成' : '今日待完成' }}</text>
        <text class="status-desc" v-if="todayRecord.completed">练习{{ todayRecord.duration }}分钟，继续加油！</text>
        <text class="status-desc" v-else>目标{{ plan.target_duration }}分钟{{ plan.preferred_category ? ' · ' + categoryLabel : '' }}</text>
      </view>
    </view>

    <!-- 激励语 -->
    <view class="motivation" v-if="motivationText">
      <text>{{ motivationText }}</text>
    </view>
  </view>

  <!-- 无计划时的引导 -->
  <view class="plan-progress empty" v-else>
    <view class="empty-icon">📋</view>
    <text class="empty-title">还没有练习计划</text>
    <text class="empty-desc">创建一个练习计划，开启你的正念之旅</text>
    <view class="create-btn" @click="$emit('create')">
      <text>创建计划</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'MeditationPlanProgress',
  props: {
    plan: { type: Object, default: null }
  },
  computed: {
    progressPercent() {
      if (!this.plan || !this.plan.target_days) return 0
      return Math.min(100, Math.round((this.plan.completed_days / this.plan.target_days) * 100))
    },
    ringStyle() {
      const deg = (this.progressPercent / 100) * 360
      return {
        background: `conic-gradient(#6B8E7B ${deg}deg, #E8E8E8 ${deg}deg)`
      }
    },
    todayRecord() {
      if (!this.plan || !this.plan.daily_records) return null
      const today = this._getTodayStr()
      return this.plan.daily_records.find(r => r.date === today)
    },
    categoryLabel() {
      const labels = {
        breathing: '呼吸放松',
        body_scan: '身体扫描',
        mindfulness: '正念冥想',
        anxiety_relief: '焦虑缓解',
        sleep_aid: '助眠安神'
      }
      return labels[this.plan?.preferred_category] || ''
    },
    motivationText() {
      if (!this.plan) return ''
      const pct = this.progressPercent
      if (pct === 0) return '千里之行，始于足下。今天就开始第一次练习吧~'
      if (pct < 30) return '好的开始是成功的一半，继续保持！'
      if (pct < 60) return '你已经养成了初步的习惯，坚持下去！'
      if (pct < 80) return '太棒了！你已经完成了大部分，胜利在望！'
      if (pct < 100) return '即将达成目标！最后冲刺，你一定可以！'
      return '恭喜你完成了全部计划！正念已经成为你生活的一部分~'
    }
  },
  methods: {
    _getTodayStr() {
      const d = new Date()
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    },
    isToday(dateStr) {
      return dateStr === this._getTodayStr()
    },
    isPast(dateStr) {
      return dateStr < this._getTodayStr()
    },
    getDayLabel(dateStr, idx) {
      const d = new Date(dateStr + 'T00:00:00')
      const dayNames = ['日', '一', '二', '三', '四', '五', '六']
      return dayNames[d.getDay()] || (idx + 1)
    }
  }
}
</script>

<style lang="scss" scoped>
.plan-progress {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28rpx;
}

.plan-info {
  flex: 1;
}

.plan-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.plan-days {
  font-size: 26rpx;
  color: #6B8E7B;
  font-weight: 600;
}

.plan-progress-ring {
  position: relative;
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ring-track {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #E8E8E8;
}

.ring-fill {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.ring-text {
  position: relative;
  z-index: 1;
  font-size: 24rpx;
  font-weight: 700;
  color: #6B8E7B;
  background: #fff;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-bar-wrap {
  margin-bottom: 24rpx;
}

.progress-segments {
  display: flex;
  gap: 8rpx;
  overflow-x: auto;
  padding-bottom: 8rpx;
}

.segment {
  flex-shrink: 0;
  width: 64rpx;
  height: 72rpx;
  border-radius: 12rpx;
  background: #F5F5F5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  transition: all 0.3s ease;
}

.segment.completed {
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
}

.segment.today {
  border: 3rpx solid #6B8E7B;
}

.segment.missed {
  background: #FFF0F0;
}

.segment-day {
  font-size: 20rpx;
  color: #999;
}

.segment.completed .segment-day {
  color: rgba(255, 255, 255, 0.8);
}

.segment-icon {
  font-size: 24rpx;
  color: #6B8E7B;
  font-weight: 700;
}

.segment.completed .segment-icon {
  color: #fff;
}

.today-status {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, rgba(107, 142, 123, 0.06), rgba(107, 142, 123, 0.02));
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
}

.status-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: rgba(107, 142, 123, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
}

.status-icon.done {
  background: rgba(76, 175, 80, 0.15);
}

.status-icon text {
  font-size: 32rpx;
}

.status-text {
  flex: 1;
}

.status-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 4rpx;
}

.status-desc {
  font-size: 24rpx;
  color: #888;
}

.motivation {
  background: linear-gradient(135deg, rgba(255, 213, 79, 0.08), rgba(255, 213, 79, 0.02));
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
}

.motivation text {
  font-size: 24rpx;
  color: #795548;
  line-height: 1.5;
}

/* 空状态 */
.plan-progress.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 28rpx;
}

.empty-icon {
  font-size: 64rpx;
  margin-bottom: 16rpx;
}

.empty-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.empty-desc {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 24rpx;
  text-align: center;
}

.create-btn {
  padding: 16rpx 48rpx;
  border-radius: 40rpx;
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  box-shadow: 0 6rpx 20rpx rgba(107, 142, 123, 0.3);
}

.create-btn:active {
  transform: scale(0.96);
}

.create-btn text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 600;
}
</style>
