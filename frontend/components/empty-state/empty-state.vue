<template>
  <view class="empty-state">
    <view class="empty-icon-wrap" :class="{ bounce: animated }">
      <text class="empty-icon">{{ icon }}</text>
      <view class="empty-ring"></view>
    </view>
    <text class="empty-text">{{ text }}</text>
    <text v-if="subtext" class="empty-subtext">{{ subtext }}</text>
    <view v-if="actionText" class="empty-action" @click="$emit('action')">
      <text class="action-text">{{ actionText }}</text>
      <view class="action-arrow">›</view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    icon: { type: String, default: '📝' },
    text: { type: String, default: '暂无内容' },
    subtext: { type: String, default: '' },
    actionText: { type: String, default: '' }
  },
  data() {
    return { animated: false }
  },
  mounted() {
    setTimeout(() => { this.animated = true }, 200)
  }
}
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;
}
.empty-icon-wrap {
  position: relative;
  width: 140rpx;
  height: 140rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}
.empty-icon-wrap.bounce {
  animation: icon-bounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.empty-icon {
  font-size: 72rpx;
  z-index: 2;
  position: relative;
}
.empty-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(107, 142, 123, 0.08), rgba(107, 142, 123, 0.02));
  animation: ring-pulse 2s ease-in-out infinite;
}
@keyframes icon-bounce {
  0% { transform: scale(0); }
  60% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 0.3; }
}
.empty-text {
  font-size: 30rpx;
  color: #8A9B8E;
  font-weight: 500;
  margin-bottom: 8rpx;
}
.empty-subtext {
  font-size: 24rpx;
  color: #B0BDB5;
  margin-bottom: 24rpx;
}
.empty-action {
  display: flex;
  align-items: center;
  padding: 16rpx 40rpx;
  background: linear-gradient(135deg, #6B8E7B, #7FA08E);
  border-radius: 40rpx;
  box-shadow: 0 4rpx 16rpx rgba(107, 142, 123, 0.3);
  transition: all 0.3s ease;
}
.empty-action:active {
  transform: scale(0.95);
  box-shadow: 0 2rpx 8rpx rgba(107, 142, 123, 0.2);
}
.action-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 600;
}
.action-arrow {
  font-size: 32rpx;
  color: #fff;
  margin-left: 8rpx;
  font-weight: 300;
}
</style>
