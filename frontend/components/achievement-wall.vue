<template>
  <view v-if="visible" class="achievement-overlay" @click="handleClose">
    <view class="achievement-panel ahp-slide-up" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <view class="header-left">
          <text class="panel-title">🏆 成就墙</text>
          <text class="panel-subtitle">{{ unlockedCount }}/{{ totalCount }} 已解锁</text>
        </view>
        <view class="header-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- 总进度条 -->
      <view class="progress-section">
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
        </view>
        <text class="progress-text">{{ progressPercent }}%</text>
      </view>

      <!-- 成就列表 -->
      <scroll-view scroll-y class="achievement-list">
        <view
          v-for="tier in achievementTiers"
          :key="tier.streak"
          class="achievement-item"
          :class="{ unlocked: isUnlocked(tier), locked: !isUnlocked(tier) }"
        >
          <!-- 图标 -->
          <view class="item-icon-wrap" :style="{ background: tier.color + (isUnlocked(tier) ? '22' : '0A') }">
            <text class="item-icon" :style="{ opacity: isUnlocked(tier) ? 1 : 0.3 }">{{ tier.icon }}</text>
            <view v-if="isUnlocked(tier)" class="item-check">✓</view>
          </view>

          <!-- 信息 -->
          <view class="item-info">
            <view class="item-header">
              <text class="item-name">{{ tier.name }}</text>
              <view class="item-streak-badge" :style="{ background: isUnlocked(tier) ? tier.color : '#E0E0E0' }">
                <text class="streak-text">{{ tier.streak }}天</text>
              </view>
            </view>
            <text class="item-reward">{{ tier.reward }}</text>
            <text class="item-type">{{ rewardTypeLabel(tier.type) }}</text>

            <!-- 解锁时间 -->
            <text v-if="isUnlocked(tier)" class="item-unlocked-time">
              {{ formatUnlockTime(tier) }}
            </text>
            <text v-else class="item-locked-hint">
              还差 {{ tier.streak - (currentStreak || 0) }} 天解锁
            </text>
          </view>
        </view>

        <!-- 底部提示 -->
        <view class="bottom-tip">
          <text class="tip-icon">💡</text>
          <text class="tip-text">连续打卡越多，解锁的成就奖励越丰富！</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import habitApi from '@/api/habit'

export default {
  name: 'achievement-wall',
  props: {
    visible: { type: Boolean, default: false },
    habitId: { type: Number, default: 0 },
    currentStreak: { type: Number, default: 0 }
  },
  data() {
    return {
      achievementTiers: [],
      unlockedList: []
    }
  },
  computed: {
    totalCount() {
      return this.achievementTiers.length
    },
    unlockedCount() {
      return this.unlockedList.filter(a => a.is_unlocked).length
    },
    progressPercent() {
      if (!this.totalCount) return 0
      return Math.round((this.unlockedCount / this.totalCount) * 100)
    }
  },
  watch: {
    visible(val) {
      if (val) this.loadAchievements()
    }
  },
  methods: {
    async loadAchievements() {
      // 从mock或API获取成就等级定义
      const mock = require('@/common/mock').default
      this.achievementTiers = mock.achievementTiers || []

      try {
        const res = await habitApi.getAchievements(this.habitId || undefined)
        const data = res?.data || res
        if (Array.isArray(data)) {
          this.unlockedList = data
        }
      } catch (e) {
        console.error('加载成就失败', e)
        this.unlockedList = []
      }
    },
    isUnlocked(tier) {
      if (this.currentStreak >= tier.streak) return true
      const found = this.unlockedList.find(
        a => a.trigger_streak === tier.streak && a.is_unlocked
      )
      return !!found
    },
    rewardTypeLabel(type) {
      const map = {
        voice_message: '🎙️ 语音鼓励',
        comic_diary: '🎨 漫画日记',
        special_badge: '🏅 专属徽章'
      }
      return map[type] || type
    },
    formatUnlockTime(tier) {
      const found = this.unlockedList.find(
        a => a.trigger_streak === tier.streak && a.is_unlocked
      )
      if (found?.unlocked_at) {
        const d = new Date(found.unlocked_at)
        return `${d.getMonth() + 1}月${d.getDate()}日解锁`
      }
      return '已解锁'
    },
    handleClose() {
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.achievement-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: flex;
  align-items: flex-end;
}

.achievement-panel {
  width: 100%;
  max-height: 80vh;
  background: var(--bg-card, #fff);
  border-radius: 32rpx 32rpx 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid var(--border-color, #F0F0F0);
}

.header-left {
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--text-primary, #333);
}

.panel-subtitle {
  font-size: 24rpx;
  color: var(--text-secondary, #999);
  margin-top: 6rpx;
}

.header-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  font-size: 36rpx;
  color: var(--text-light, #999);
}

.progress-section {
  display: flex;
  align-items: center;
  padding: 20rpx 32rpx;
  gap: 16rpx;
}

.progress-bar {
  flex: 1;
  height: 16rpx;
  background: var(--bg-secondary, #F0F2F5);
  border-radius: 8rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #FFD700, #FFA500);
  border-radius: 8rpx;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--text-secondary, #999);
  min-width: 60rpx;
  text-align: right;
}

.achievement-list {
  flex: 1;
  padding: 16rpx 32rpx 40rpx;
}

.achievement-item {
  display: flex;
  padding: 24rpx;
  border-radius: 20rpx;
  margin-bottom: 16rpx;
  background: var(--bg-secondary, #F8F9FA);
  transition: all 0.2s;
}

.achievement-item.unlocked {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.06), rgba(255, 165, 0, 0.04));
  border: 2rpx solid rgba(255, 215, 0, 0.15);
}

.achievement-item.locked {
  opacity: 0.7;
}

.item-icon-wrap {
  position: relative;
  width: 80rpx;
  height: 80rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.item-icon {
  font-size: 40rpx;
}

.item-check {
  position: absolute;
  top: -6rpx;
  right: -6rpx;
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: #6B8E7B;
  color: #fff;
  font-size: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3rpx solid var(--bg-card, #fff);
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.item-name {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.item-streak-badge {
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
}

.streak-text {
  font-size: 22rpx;
  color: #fff;
  font-weight: 600;
}

.item-reward {
  font-size: 26rpx;
  color: var(--text-secondary, #666);
  display: block;
  margin-bottom: 6rpx;
  line-height: 1.4;
}

.item-type {
  font-size: 22rpx;
  color: var(--text-light, #999);
  display: block;
}

.item-unlocked-time {
  font-size: 22rpx;
  color: #6B8E7B;
  margin-top: 8rpx;
  display: block;
}

.item-locked-hint {
  font-size: 22rpx;
  color: var(--text-light, #bbb);
  margin-top: 8rpx;
  display: block;
}

.bottom-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx 0 16rpx;
  gap: 8rpx;
}

.tip-icon {
  font-size: 28rpx;
}

.tip-text {
  font-size: 24rpx;
  color: var(--text-light, #999);
}
</style>
