<template>
  <view class="habit-card" :class="{ completed: habit.completed }">
    <view class="card-bg" :style="{ background: habit.color + '30' }"></view>
    
    <view class="card-content">
      <view class="card-left">
        <view class="habit-icon">
          <text class="icon-emoji">{{ habit.icon }}</text>
        </view>
        <view class="habit-info">
          <text class="habit-name">{{ habit.name }}</text>
          <text class="habit-time">{{ getTimeText }}</text>
          <!-- 断卡提示：展示断卡前的历史连续天数 -->
          <!-- ↓↓↓ 措辞修正（2026-10-28）：不把断卡定义成失败，也不再显示刺眼的警示色 ↓↓↓ -->
          <view v-if="habit.broken" class="broken-row">
            <view class="broken-tag">
              <text class="broken-text">暂时停下{{ habit.broken_streak ? ` · 之前连续过 ${habit.broken_streak} 天` : '' }}</text>
            </view>
            <view class="broken-talk" @click.stop="$emit('chat', habit)">
              <text class="broken-talk-text">和TA聊聊这件事</text>
            </view>
          </view>
          <view v-if="habit.target && habit.target.includes('分钟')" class="progress-bar">
            <view class="progress-fill" :style="{ width: progressPercent + '%', background: habit.color }"></view>
          </view>
          <text v-if="habit.target && habit.target.includes('分钟')" class="progress-text">{{ progressText }}</text>
        </view>
      </view>

      <view class="card-right">
        <view class="card-actions">
          <view class="delete-btn" @click.stop="$emit('delete', habit)">
            <text class="delete-icon">✕</text>
          </view>
          <!-- 补卡入口：仅昨日漏卡（宽限期内）且今日未打卡时显示 -->
          <view
            v-if="habit.can_makeup && !habit.completed"
            class="makeup-btn"
            @click.stop="$emit('makeup', habit)"
          >
            <text class="makeup-text">补卡</text>
          </view>
          <view
            v-if="!habit.completed"
            class="start-btn"
            :style="{ background: habit.color }"
            @click.stop="$emit('timer', habit)"
          >
            <text class="start-text">开始</text>
          </view>
          <view v-else class="completed-mark">
            <text class="completed-icon">✓</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'HabitCard',
  props: {
    habit: { type: Object, default: () => ({}) }
  },
  computed: {
    getTimeText() {
      const match = this.habit.target && this.habit.target.match(/(\d+)\s*(分钟|分|min)/)
      if (match) {
        return `${match[1]} 分钟`
      }
      return this.habit.target || ''
    },
    progressPercent() {
      if (!this.habit.target || !this.habit.target.includes('分钟')) return 0
      return this.habit.completed ? 100 : 0
    },
    progressText() {
      if (!this.habit.target || !this.habit.target.includes('分钟')) return ''
      const match = this.habit.target.match(/(\d+)\s*(分钟|分|min)/)
      const total = match ? parseInt(match[1]) : 0
      const completed = this.habit.completed ? total : 0
      return `今日 ${completed}/${total} 分钟`
    }
  }
}
</script>

<style lang="scss" scoped>
.habit-card {
  position: relative;
  border-radius: 24rpx;
  margin-bottom: 20rpx;
  overflow: hidden;
  backdrop-filter: blur(20rpx);
}
.card-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.6;
}
.card-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
}
.card-left {
  display: flex;
  align-items: center;
  flex: 1;
}
.habit-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}
.icon-emoji {
  font-size: 40rpx;
}
.habit-info {
  flex: 1;
}
.habit-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}
.habit-time {
  font-size: 24rpx;
  color: rgba(0, 0, 0, 0.5);
  display: block;
  margin-bottom: 12rpx;
}
/* 断卡标签（2026-10-28：移除刺眼的橙红警示色，改为中性柔和色） */
.broken-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}
.broken-tag {
  display: inline-block;
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  background: rgba(0, 0, 0, 0.05);
}
.broken-text {
  font-size: 20rpx;
  color: #8A9B8E;
}
/* 断卡时不去催，只递一个「聊聊」的入口 */
.broken-talk {
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  background: rgba(107, 142, 123, 0.10);
}
.broken-talk-text {
  font-size: 20rpx;
  color: #6B8E7B;
}
/* 补卡按钮（绿色描边次级按钮，与全局主色一致） */
.makeup-btn {
  padding: 16rpx 28rpx;
  border-radius: 32rpx;
  border: 2rpx solid #6B8E7B;
  background: rgba(107, 142, 123, 0.08);
  transition: all 0.3s ease;
}
.makeup-btn:active {
  transform: scale(0.95);
  background: rgba(107, 142, 123, 0.2);
}
.makeup-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #6B8E7B;
}
.progress-bar {
  height: 8rpx;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4rpx;
  overflow: hidden;
  margin-bottom: 6rpx;
}
.progress-fill {
  height: 100%;
  border-radius: 4rpx;
  transition: width 0.5s ease;
}
.progress-text {
  font-size: 20rpx;
  color: rgba(0, 0, 0, 0.4);
}
.card-right {
  flex-shrink: 0;
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.delete-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}
.delete-btn:active {
  background: rgba(255, 107, 107, 0.2);
  transform: scale(0.95);
}
.delete-icon {
  font-size: 28rpx;
  color: rgba(0, 0, 0, 0.4);
}
.start-btn {
  padding: 20rpx 40rpx;
  border-radius: 32rpx;
  transition: all 0.3s ease;
}
.start-btn:active {
  transform: scale(0.95);
  opacity: 0.8;
}
.start-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}
.completed-mark {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: rgba(76, 175, 80, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}
.completed-icon {
  font-size: 40rpx;
  color: #fff;
  font-weight: bold;
}
</style>
