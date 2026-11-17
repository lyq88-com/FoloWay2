<template>
  <view class="badge-item" :class="{ locked: !badge.unlocked }" @click="$emit('click', badge)">
    <view class="badge-icon" :style="iconStyle">
      <text class="emoji">{{ badge.icon }}</text>
      <view v-if="!badge.unlocked" class="lock-overlay">
        <text class="lock-icon">🔒</text>
      </view>
    </view>
    <text class="badge-name">{{ badge.name }}</text>
    <text class="badge-desc">{{ badge.description }}</text>
    <text v-if="badge.unlocked && badge.unlockedAt" class="badge-date">
      {{ formatDate(badge.unlockedAt) }} 解锁
    </text>
    <text v-else class="badge-date locked-text">
      {{ badge.condition || '未解锁' }}
    </text>
  </view>
</template>

<script>
export default {
  name: 'BadgeItem',
  props: {
    badge: { type: Object, default: () => ({}) }
  },
  computed: {
    iconStyle() {
      return this.badge.unlocked
        ? { background: 'linear-gradient(135deg, #FFD93D 0%, #FFA500 100%)' }
        : { background: '#E0E0E0' }
    }
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    }
  }
}
</script>

<style lang="scss" scoped>
.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 16rpx;
  background: #fff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}
.badge-item:active {
  transform: scale(0.96);
}
.badge-item.locked {
  opacity: 0.6;
}
.badge-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12rpx;
  position: relative;
  box-shadow: 0 4rpx 16rpx rgba(255, 169, 0, 0.2);
}
.badge-item.locked .badge-icon {
  box-shadow: none;
}
.emoji {
  font-size: 48rpx;
}
.lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.lock-icon {
  font-size: 32rpx;
}
.badge-name {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 4rpx;
  text-align: center;
}
.badge-desc {
  font-size: 20rpx;
  color: #999;
  text-align: center;
  margin-bottom: 4rpx;
  line-height: 1.3;
}
.badge-date {
  font-size: 20rpx;
  color: #FF9800;
}
.locked-text {
  color: #bbb;
}
</style>
