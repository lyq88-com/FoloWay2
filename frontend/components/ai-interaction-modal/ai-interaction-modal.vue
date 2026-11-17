<template>
  <view v-if="visible" class="ai-interaction-modal" :class="{ 'modal-success': type === 'success', 'modal-fail': type === 'fail', 'modal-reminder': type === 'reminder' }" @click="onClose">
    <view class="modal-content" @click.stop>
      <!-- AI 角色立绘区 -->
      <view class="ai-avatar-section">
        <view class="avatar-glow" :style="glowStyle"></view>
        <view class="avatar-container">
          <CharacterHead :characterId="characterId" size="large" />
          <view v-if="type === 'success'" class="celebration-ring">
            <view class="ring-1"></view>
            <view class="ring-2"></view>
            <view class="ring-3"></view>
          </view>
          <view v-if="type === 'success'" class="sparkles">
            <view class="sparkle s1">✨</view>
            <view class="sparkle s2">🌟</view>
            <view class="sparkle s3">💫</view>
            <view class="sparkle s4">✨</view>
            <view class="sparkle s5">⭐</view>
          </view>
          <view v-if="type === 'fail'" class="comfort-emoji">🫂</view>
        </view>
        <view class="ai-name-tag" :style="tagBgStyle">
          <text class="ai-name-text">{{ aiName }}</text>
          <view class="typing-dots" v-if="loading">
            <view class="dot d1"></view>
            <view class="dot d2"></view>
            <view class="dot d3"></view>
          </view>
          <view class="speaking-indicator" v-else-if="speaking">
            <view class="wave w1"></view>
            <view class="wave w2"></view>
            <view class="wave w3"></view>
          </view>
        </view>
      </view>

      <!-- 对话气泡 -->
      <view class="dialogue-section">
        <view class="bubble-container" v-if="displayText">
          <view class="bubble-tail" :style="bubbleColorStyle"></view>
          <view class="bubble-content" :style="bubbleBgStyle">
            <text class="bubble-text">{{ displayText }}</text>
          </view>
        </view>
        
        <!-- 输入中状态 -->
        <view v-if="loading" class="loading-bubble" :style="bubbleBgStyle">
          <view class="thinking-dots">
            <view class="think-dot d1"></view>
            <view class="think-dot d2"></view>
            <view class="think-dot d3"></view>
          </view>
          <text class="loading-text">{{ loadingText }}</text>
        </view>
      </view>

      <!-- 统计信息（打卡成功时显示） -->
      <view v-if="showStats && !loading" class="stats-section">
        <view class="stat-item" v-if="stats.streakDays > 0">
          <text class="stat-emoji">🔥</text>
          <text class="stat-value">{{ stats.streakDays }}</text>
          <text class="stat-label">连续天</text>
        </view>
        <view class="stat-item">
          <text class="stat-emoji">✅</text>
          <text class="stat-value">{{ stats.totalCheckins }}</text>
          <text class="stat-label">总打卡</text>
        </view>
        <view class="stat-item" v-if="stats.stageName">
          <text class="stat-emoji">📍</text>
          <text class="stat-value small">{{ stats.stageName }}</text>
          <text class="stat-label">当前地点</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-buttons">
        <view class="btn btn-primary" :style="primaryBtnStyle" @click="onPrimaryAction">
          <text class="btn-icon">{{ primaryBtnIcon }}</text>
          <text class="btn-text">{{ primaryBtnText }}</text>
        </view>
        <view v-if="showSecondaryBtn" class="btn btn-secondary" @click="onSecondaryAction">
          <text class="btn-icon">{{ secondaryBtnIcon }}</text>
          <text class="btn-text">{{ secondaryBtnText }}</text>
        </view>
        <view class="btn btn-text-only" @click="onClose">
          <text class="btn-text">{{ closeText }}</text>
        </view>
      </view>

      <!-- 限时盲盒（打卡成功时） -->
      <view v-if="showBlindBox && !loading" class="blind-box-trigger" @click="onBlindBox">
        <view class="blind-box-icon-wrap">
          <text class="blind-box-icon">🎁</text>
          <view class="blind-box-glow"></view>
        </view>
        <view class="blind-box-info">
          <text class="blind-box-title">每日励志盲盒</text>
          <text class="blind-box-hint">点击解锁今日专属语录</text>
        </view>
        <view class="blind-box-arrow">›</view>
      </view>
    </view>
  </view>
</template>

<script>
import CharacterHead from '@/components/character-sprite/character-head.vue'
import { getCharacterById } from '@/common/ai-characters'

export default {
  name: 'AIInteractionModal',
  components: { CharacterHead },
  props: {
    visible: { type: Boolean, default: false },
    type: { type: String, default: 'success' }, // success | fail | reminder
    characterId: { type: String, default: 'linxi' },
    message: { type: String, default: '' },
    loading: { type: Boolean, default: false },
    loadingText: { type: String, default: '正在思考...' },
    speaking: { type: Boolean, default: false },
    stats: { type: Object, default: () => ({}) },
    showBlindBox: { type: Boolean, default: false }
  },
  computed: {
    aiName() {
      const c = getCharacterById(this.characterId)
      return c ? c.name : 'AI伙伴'
    },
    displayText() {
      return this.message
    },
    showStats() {
      return this.type === 'success' && this.stats && (this.stats.streakDays || this.stats.totalCheckins)
    },
    showSecondaryBtn() {
      return this.type === 'success' || this.type === 'fail'
    },
    primaryBtnText() {
      const map = {
        success: '继续打卡',
        fail: '调整计划',
        reminder: '立即打卡'
      }
      return map[this.type] || '好的'
    },
    primaryBtnIcon() {
      const map = { success: '✅', fail: '💪', reminder: '🚀' }
      return map[this.type] || '→'
    },
    secondaryBtnText() {
      return '聊聊'
    },
    secondaryBtnIcon() {
      return '💬'
    },
    closeText() {
      return '稍后再说'
    },
    glowStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return {
          background: `radial-gradient(circle, ${c.colors.accent}40 0%, transparent 70%)`
        }
      }
      return {}
    },
    bubbleBgStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return {
          background: `linear-gradient(135deg, ${c.colors.light} 0%, ${c.colors.secondary} 100%)`,
          borderColor: c.colors.accent + '30'
        }
      }
      return { background: 'linear-gradient(135deg, #fff9f0, #fff5e8)', borderColor: 'rgba(107,142,123,0.2)' }
    },
    bubbleColorStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return { borderTopColor: c.colors.secondary }
      }
      return { borderTopColor: '#fff5e8' }
    },
    tagBgStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return { background: `linear-gradient(135deg, ${c.colors.primary}, ${c.colors.accent})` }
      }
      return { background: 'linear-gradient(135deg, #6B8E7B, #8FBC8F)' }
    },
    primaryBtnStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return { background: `linear-gradient(135deg, ${c.colors.primary}, ${c.colors.accent})` }
      }
      return { background: 'linear-gradient(135deg, #6B8E7B, #8FBC8F)' }
    }
  },
  methods: {
    onClose() {
      this.$emit('close')
    },
    onPrimaryAction() {
      this.$emit('primary')
    },
    onSecondaryAction() {
      this.$emit('chat')
    },
    onBlindBox() {
      this.$emit('blindBox')
    }
  }
}
</script>

<style lang="scss" scoped>
.ai-interaction-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 40rpx;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  width: 100%;
  max-width: 640rpx;
  background: #fff;
  border-radius: 40rpx;
  padding: 50rpx 40rpx 40rpx;
  position: relative;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.2);
  animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
  from { transform: translateY(40rpx); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* AI 头像区 */
.ai-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30rpx;
  position: relative;
}

.avatar-glow {
  position: absolute;
  width: 300rpx;
  height: 300rpx;
  top: -50rpx;
  filter: blur(40rpx);
  opacity: 0.6;
}

.avatar-container {
  position: relative;
  z-index: 1;
  width: 180rpx;
  height: 180rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.celebration-ring {
  position: absolute;
  top: -30rpx;
  left: -30rpx;
  right: -30rpx;
  bottom: -30rpx;
  pointer-events: none;
}

.celebration-ring .ring-1,
.celebration-ring .ring-2,
.celebration-ring .ring-3 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 3rpx solid transparent;
}

.celebration-ring .ring-1 {
  width: 100%;
  height: 100%;
  border-color: #FFD93D;
  animation: ringExpand 2s ease-out infinite;
}

.celebration-ring .ring-2 {
  width: 80%;
  height: 80%;
  border-color: #FF6B6B;
  animation: ringExpand 2s ease-out 0.5s infinite;
}

.celebration-ring .ring-3 {
  width: 60%;
  height: 60%;
  border-color: #4ECDC4;
  animation: ringExpand 2s ease-out 1s infinite;
}

@keyframes ringExpand {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
}

.sparkles {
  position: absolute;
  top: -20rpx;
  left: 0;
  right: 0;
  height: 240rpx;
  pointer-events: none;
}

.sparkle {
  position: absolute;
  font-size: 36rpx;
  animation: sparkleFloat 2s ease-in-out infinite;
}

.sparkle.s1 { top: 0; left: 30%; animation-delay: 0s; }
.sparkle.s2 { top: 20rpx; left: 80%; animation-delay: 0.3s; }
.sparkle.s3 { top: 60rpx; left: 10%; animation-delay: 0.6s; font-size: 28rpx; }
.sparkle.s4 { top: 80rpx; right: 20%; animation-delay: 0.9s; }
.sparkle.s5 { top: 120rpx; left: 50%; animation-delay: 1.2s; font-size: 24rpx; }

@keyframes sparkleFloat {
  0%, 100% { transform: translateY(0) scale(1); opacity: 1; }
  50% { transform: translateY(-15rpx) scale(1.2); opacity: 0.7; }
}

.comfort-emoji {
  position: absolute;
  bottom: -10rpx;
  right: -20rpx;
  font-size: 48rpx;
  animation: bounce 1.5s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10rpx); }
}

.ai-name-tag {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 8rpx 24rpx;
  border-radius: 20rpx;
  margin-top: 16rpx;
}

.ai-name-text {
  font-size: 26rpx;
  color: #fff;
  font-weight: 600;
}

.typing-dots {
  display: flex;
  gap: 4rpx;
}

.typing-dots .dot {
  width: 8rpx;
  height: 8rpx;
  background: #fff;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-dots .d1 { animation-delay: 0s; }
.typing-dots .d2 { animation-delay: 0.2s; }
.typing-dots .d3 { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-8rpx); opacity: 1; }
}

.speaking-indicator {
  display: flex;
  gap: 3rpx;
  align-items: center;
}

.speaking-indicator .wave {
  width: 4rpx;
  background: #fff;
  border-radius: 2rpx;
  animation: waveBeat 1s ease-in-out infinite;
}

.speaking-indicator .w1 { height: 12rpx; animation-delay: 0s; }
.speaking-indicator .w2 { height: 20rpx; animation-delay: 0.15s; }
.speaking-indicator .w3 { height: 14rpx; animation-delay: 0.3s; }

@keyframes waveBeat {
  0%, 100% { height: 8rpx; }
  50% { height: 24rpx; }
}

/* 对话气泡 */
.dialogue-section {
  position: relative;
  z-index: 2;
}

.bubble-container {
  position: relative;
}

.bubble-tail {
  position: absolute;
  top: -16rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 16rpx solid transparent;
  border-right: 16rpx solid transparent;
  border-bottom: 16rpx solid;
}

.bubble-content {
  border-radius: 24rpx;
  padding: 32rpx 28rpx;
  border: 2rpx solid;
  min-height: 120rpx;
}

.bubble-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.7;
  display: block;
}

.loading-bubble {
  border-radius: 24rpx;
  padding: 32rpx 28rpx;
  border: 2rpx solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  min-height: 100rpx;
}

.thinking-dots {
  display: flex;
  gap: 8rpx;
}

.thinking-dots .think-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #999;
  animation: thinkPulse 1.4s ease-in-out infinite;
}

.thinking-dots .d1 { animation-delay: 0s; }
.thinking-dots .d2 { animation-delay: 0.2s; }
.thinking-dots .d3 { animation-delay: 0.4s; }

@keyframes thinkPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-text {
  font-size: 26rpx;
  color: #666;
}

/* 统计区 */
.stats-section {
  display: flex;
  justify-content: center;
  gap: 40rpx;
  margin: 30rpx 0;
  padding: 24rpx;
  background: #F8FBF9;
  border-radius: 20rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-emoji {
  font-size: 32rpx;
  margin-bottom: 4rpx;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #2D4A3E;
}

.stat-value.small {
  font-size: 26rpx;
  max-width: 120rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

/* 按钮 */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 30rpx;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  transition: all 0.2s ease;
}

.btn:active {
  transform: scale(0.97);
}

.btn-primary {
  box-shadow: 0 8rpx 24rpx rgba(107, 142, 123, 0.3);
}

.btn-primary .btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}

.btn-primary .btn-icon {
  font-size: 32rpx;
}

.btn-secondary {
  background: #F5F5F5;
}

.btn-secondary .btn-text {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.btn-secondary .btn-icon {
  font-size: 28rpx;
}

.btn-text-only {
  padding: 16rpx;
}

.btn-text-only .btn-text {
  font-size: 26rpx;
  color: #999;
}

/* 盲盒 */
.blind-box-trigger {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 24rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border-radius: 20rpx;
  transition: transform 0.2s ease;
}

.blind-box-trigger:active {
  transform: scale(0.98);
}

.blind-box-icon-wrap {
  position: relative;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.blind-box-icon {
  font-size: 48rpx;
  animation: boxShake 2s ease-in-out infinite;
}

@keyframes boxShake {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-8deg); }
  75% { transform: rotate(8deg); }
}

.blind-box-glow {
  position: absolute;
  top: -10rpx;
  left: -10rpx;
  right: -10rpx;
  bottom: -10rpx;
  background: radial-gradient(circle, rgba(255, 193, 7, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: glowPulse 2s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.1); }
}

.blind-box-info {
  flex: 1;
}

.blind-box-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #E65100;
  display: block;
}

.blind-box-hint {
  font-size: 22rpx;
  color: #FF9800;
  display: block;
  margin-top: 4rpx;
}

.blind-box-arrow {
  font-size: 36rpx;
  color: #FF9800;
}

/* 不同类型 */
.modal-success .bubble-content {
  box-shadow: 0 8rpx 32rpx rgba(76, 175, 80, 0.15);
}

.modal-fail .bubble-content {
  box-shadow: 0 8rpx 32rpx rgba(255, 152, 0, 0.15);
}

.modal-reminder .bubble-content {
  box-shadow: 0 8rpx 32rpx rgba(33, 150, 243, 0.15);
}
</style>
