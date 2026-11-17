<template>
  <view v-if="visible" class="crisis-overlay" @click.stop="handleOverlay">
    <view class="crisis-modal" @click.stop>
      <!-- 顶部图标区 -->
      <view class="crisis-header">
        <view class="crisis-icon-wrap">
          <text class="crisis-icon">{{ severityIcon }}</text>
        </view>
        <text class="crisis-title">{{ severityTitle }}</text>
        <text class="crisis-subtitle">我注意到你提到了一些让我担心的事情</text>
      </view>

      <!-- 关怀话术 -->
      <view class="crisis-body">
        <view class="crisis-message-card">
          <view class="crisis-message-avatar">
            <text class="crisis-message-emoji">{{ aiEmoji }}</text>
          </view>
          <view class="crisis-message-content">
            <text class="crisis-message-text">{{ crisisData.response || defaultResponse }}</text>
          </view>
        </view>

        <!-- 深呼吸引导 -->
        <view class="breathing-guide" @click="startBreathing">
          <view class="breathing-circle" :class="{ active: isBreathing }">
            <text class="breathing-text">{{ breathingText }}</text>
          </view>
          <text class="breathing-hint">{{ isBreathing ? '跟随节奏呼吸...' : '点击开始深呼吸引导' }}</text>
        </view>
      </view>

      <!-- 热线电话 -->
      <view class="hotline-section">
        <text class="hotline-label">24小时心理援助热线</text>
        <view class="hotline-list">
          <view
            v-for="(resource, idx) in crisisResources"
            :key="idx"
            class="hotline-item"
            @click="callHotline(resource.phone)"
          >
            <view class="hotline-icon-wrap">
              <text class="hotline-icon">📞</text>
            </view>
            <view class="hotline-info">
              <text class="hotline-name">{{ resource.name }}</text>
              <text class="hotline-phone">{{ resource.phone }}</text>
            </view>
            <text class="hotline-call-btn">拨打</text>
          </view>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="crisis-actions">
        <view class="crisis-btn secondary" @click="handleContinue">
          <text class="crisis-btn-text">继续和AI聊聊</text>
        </view>
        <view class="crisis-btn primary" @click="handleClose">
          <text class="crisis-btn-text">我知道了</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CrisisInterventionModal',
  props: {
    visible: { type: Boolean, default: false },
    crisisData: { type: Object, default: () => ({}) },
    aiEmoji: { type: String, default: '🌿' }
  },
  data() {
    return {
      isBreathing: false,
      breathingText: '深呼吸',
      breathingTimer: null,
      breathingPhase: 0,
      defaultResponse: '我听到你了，此刻的你一定承受着很大的痛苦。请相信，你的感受是真实的，你的存在是有意义的。你不是一个人。',
      defaultResources: [
        { name: '全国24小时心理援助热线', phone: '400-161-9995' },
        { name: '北京心理危机研究与干预中心', phone: '010-82951332' },
        { name: '生命热线', phone: '400-821-1215' }
      ]
    }
  },
  computed: {
    severityIcon() {
      const s = this.crisisData.severity
      if (s === 'high') return '🆘'
      if (s === 'medium') return '💛'
      return '🤝'
    },
    severityTitle() {
      const s = this.crisisData.severity
      if (s === 'high') return '你很重要'
      if (s === 'medium') return '我在这里陪着你'
      return '让我帮帮你'
    },
    crisisResources() {
      return this.crisisData.resources || this.defaultResources
    }
  },
  watch: {
    visible(val) {
      if (!val && this.breathingTimer) {
        this.stopBreathing()
      }
    }
  },
  beforeDestroy() {
    this.stopBreathing()
  },
  methods: {
    startBreathing() {
      if (this.isBreathing) {
        this.stopBreathing()
        return
      }
      this.isBreathing = true
      const phases = [
        { text: '吸气...', duration: 4000 },
        { text: '屏住...', duration: 2000 },
        { text: '呼气...', duration: 6000 },
        { text: '休息...', duration: 2000 }
      ]
      const runPhase = () => {
        if (!this.isBreathing) return
        const phase = phases[this.breathingPhase % phases.length]
        this.breathingText = phase.text
        this.breathingTimer = setTimeout(() => {
          this.breathingPhase++
          if (this.breathingPhase < 8) {
            runPhase()
          } else {
            this.stopBreathing()
          }
        }, phase.duration)
      }
      this.breathingPhase = 0
      runPhase()
    },
    stopBreathing() {
      this.isBreathing = false
      this.breathingText = '深呼吸'
      this.breathingPhase = 0
      if (this.breathingTimer) {
        clearTimeout(this.breathingTimer)
        this.breathingTimer = null
      }
    },
    callHotline(phone) {
      uni.makePhoneCall({
        phoneNumber: phone,
        fail: () => {
          uni.setClipboardData({
            data: phone,
            success: () => {
              uni.showToast({ title: '电话号码已复制', icon: 'none' })
            }
          })
        }
      })
    },
    handleContinue() {
      this.$emit('continue')
      this.$emit('close')
    },
    handleClose() {
      this.$emit('close')
    },
    handleOverlay() {
      // 不允许点击遮罩关闭
    }
  }
}
</script>

<style lang="scss" scoped>
.crisis-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.crisis-modal {
  width: 100%;
  max-width: 620rpx;
  background: #fff;
  border-radius: 32rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 85vh;
}

/* 头部 */
.crisis-header {
  padding: 50rpx 40rpx 30rpx;
  text-align: center;
  background: linear-gradient(135deg, #FFF5F5 0%, #FFF0F6 100%);
}
.crisis-icon-wrap {
  margin-bottom: 20rpx;
}
.crisis-icon {
  font-size: 80rpx;
}
.crisis-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: #E53935;
  margin-bottom: 10rpx;
}
.crisis-subtitle {
  display: block;
  font-size: 26rpx;
  color: #888;
}

/* 关怀话术 */
.crisis-body {
  padding: 30rpx 40rpx;
}
.crisis-message-card {
  display: flex;
  align-items: flex-start;
  background: #F8F9FA;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}
.crisis-message-avatar {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.crisis-message-emoji {
  font-size: 32rpx;
}
.crisis-message-content {
  flex: 1;
}
.crisis-message-text {
  font-size: 28rpx;
  line-height: 1.7;
  color: #333;
}

/* 呼吸引导 */
.breathing-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}
.breathing-circle {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
  transition: transform 2s ease-in-out;
}
.breathing-circle.active {
  animation: breathPulse 4s ease-in-out infinite;
}
@keyframes breathPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}
.breathing-text {
  font-size: 26rpx;
  color: #6B8E7B;
  font-weight: 600;
}
.breathing-hint {
  font-size: 24rpx;
  color: #aaa;
}

/* 热线 */
.hotline-section {
  padding: 0 40rpx 20rpx;
}
.hotline-label {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 16rpx;
}
.hotline-list {
  display: flex;
  flex-direction: column;
}
.hotline-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background: #F5F5F5;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
}
.hotline-item:active {
  background: #EEEEEE;
}
.hotline-icon-wrap {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: #E53935;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.hotline-icon {
  font-size: 28rpx;
}
.hotline-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.hotline-name {
  font-size: 24rpx;
  color: #555;
}
.hotline-phone {
  font-size: 28rpx;
  font-weight: 600;
  color: #E53935;
}
.hotline-call-btn {
  font-size: 24rpx;
  color: #fff;
  background: #E53935;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}

/* 操作按钮 */
.crisis-actions {
  display: flex;
  padding: 20rpx 40rpx 40rpx;
  gap: 20rpx;
}
.crisis-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.crisis-btn.secondary {
  background: #F0F0F0;
}
.crisis-btn.primary {
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
}
.crisis-btn-text {
  font-size: 28rpx;
  font-weight: 600;
}
.crisis-btn.secondary .crisis-btn-text {
  color: #666;
}
.crisis-btn.primary .crisis-btn-text {
  color: #fff;
}
</style>
