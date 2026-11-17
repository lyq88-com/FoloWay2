<template>
  <view v-if="visible" class="encouragement-overlay" @click="handleClose">
    <view class="encouragement-card ahp-bounce-in" @click.stop>
      <!-- 背景光效 -->
      <view class="card-glow" :style="{ background: glowGradient }"></view>

      <!-- 头部 -->
      <view class="card-header">
        <view class="ai-avatar" :style="{ background: avatarGradient }">
          <text class="ai-emoji">{{ aiEmoji }}</text>
          <view class="ai-pulse"></view>
        </view>
        <text class="header-title">{{ isPositive ? '🎉 打卡成功' : '💪 没关系' }}</text>
      </view>

      <!-- 习惯信息 -->
      <view class="habit-info">
        <text class="habit-name">{{ habitName }}</text>
        <view class="streak-badge" :style="{ background: streakColor }">
          <text class="streak-text">{{ streak }}天连续</text>
        </view>
      </view>

      <!-- AI鼓励语 -->
      <view class="encouragement-content">
        <view class="quote-mark">"</view>
        <text class="encouragement-text">{{ encouragementText }}</text>
        <view class="quote-mark end">"</view>
      </view>

      <!-- 成就解锁提示 -->
      <view v-if="unlockedTier" class="tier-unlock" @click="handleTierClick">
        <view class="tier-icon-wrap" :style="{ background: unlockedTier.color + '22' }">
          <text class="tier-icon">{{ unlockedTier.icon }}</text>
        </view>
        <view class="tier-info">
          <text class="tier-name">🏆 {{ unlockedTier.name }} 解锁！</text>
          <text class="tier-reward">{{ unlockedTier.reward }}</text>
        </view>
        <text class="tier-arrow">›</text>
      </view>

      <!-- 操作按钮 -->
      <view class="card-actions">
        <view class="action-btn primary" @click="handleWriteDiary">
          <text class="btn-icon">📝</text>
          <text class="btn-text">写日记</text>
        </view>
        <view class="action-btn secondary" @click="handleClose">
          <text class="btn-text">{{ closeButtonText }}</text>
        </view>
      </view>

      <!-- 装饰粒子 -->
      <view v-if="isPositive" class="particles">
        <view v-for="i in 8" :key="i" class="particle" :style="particleStyle(i)"></view>
      </view>
    </view>
  </view>
</template>

<script>
import { getCharacterById } from '@/common/ai-characters'

export default {
  name: 'ai-encouragement-popup',
  props: {
    visible: { type: Boolean, default: false },
    habitName: { type: String, default: '' },
    streak: { type: Number, default: 0 },
    difficulty: { type: String, default: 'easy' },
    action: { type: String, default: 'checkin' }, // 'checkin' | 'uncheck'
    unlockedTier: { type: Object, default: null }
  },
  computed: {
    isPositive() {
      return this.action !== 'uncheck'
    },
    aiEmoji() {
      const charId = this.$store?.state?.aiConfig?.avatarType || 'linxi'
      const char = getCharacterById(charId)
      return char?.emoji || '🌸'
    },
    avatarGradient() {
      const charId = this.$store?.state?.aiConfig?.avatarType || 'linxi'
      const char = getCharacterById(charId)
      if (char?.colors) {
        return `linear-gradient(135deg, ${char.colors.primary}, ${char.colors.accent})`
      }
      return 'linear-gradient(135deg, #6B8E7B, #A8C9B8)'
    },
    glowGradient() {
      if (this.isPositive) {
        return 'radial-gradient(circle at 50% 0%, rgba(107, 142, 123, 0.15), transparent 70%)'
      }
      return 'radial-gradient(circle at 50% 0%, rgba(143, 155, 179, 0.15), transparent 70%)'
    },
    streakColor() {
      if (this.streak >= 100) return 'linear-gradient(135deg, #FF6B6B, #FFD700)'
      if (this.streak >= 30) return 'linear-gradient(135deg, #FFD700, #FFA500)'
      if (this.streak >= 7) return 'linear-gradient(135deg, #6B8E7B, #A8C9B8)'
      return 'linear-gradient(135deg, #4FC3F7, #81D4FA)'
    },
    closeButtonText() {
      return this.isPositive ? '继续加油' : '明天再来'
    },
    encouragementText() {
      // 从store中获取AI回复文本，或使用默认
      const stored = this.$store?.state?.encouragementText
      if (stored) return stored
      if (this.isPositive) {
        return `${this.streak}天连续打卡！你正在创造属于自己的改变~`
      }
      return '没关系，偶尔停下来也很正常。重要的是你还在这里~'
    }
  },
  data() {
    return {}
  },
  methods: {
    handleClose() {
      this.$emit('close')
    },
    handleWriteDiary() {
      this.$emit('write-diary')
    },
    handleTierClick() {
      this.$emit('view-achievement', this.unlockedTier)
    },
    particleStyle(i) {
      const angle = (i - 1) * 45
      const distance = 80 + Math.random() * 40
      const x = Math.cos((angle * Math.PI) / 180) * distance
      const y = Math.sin((angle * Math.PI) / 180) * distance
      return {
        '--tx': `${x}rpx`,
        '--ty': `${y}rpx`,
        animationDelay: `${i * 0.08}s`,
        background: ['#6B8E7B', '#A8C9B8', '#FFD93D', '#4FC3F7', '#FF6B6B', '#81C784', '#FF9800', '#9C27B0'][i - 1]
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.encouragement-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 40rpx;
}

.encouragement-card {
  position: relative;
  width: 100%;
  max-width: 640rpx;
  background: var(--bg-card, #fff);
  border-radius: 32rpx;
  padding: 48rpx 32rpx 32rpx;
  box-shadow: var(--shadow-lg, 0 12rpx 48rpx rgba(0, 0, 0, 0.12));
  overflow: hidden;
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200rpx;
  pointer-events: none;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.ai-avatar {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(107, 142, 123, 0.3);
}

.ai-emoji {
  font-size: 48rpx;
}

.ai-pulse {
  position: absolute;
  top: -4rpx;
  right: -4rpx;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: #6B8E7B;
  border: 3rpx solid var(--bg-card, #fff);
  animation: ahp-pulse 2s ease-in-out infinite;
}

.header-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-primary, #333);
}

.habit-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  margin-bottom: 32rpx;
}

.habit-name {
  font-size: 28rpx;
  color: var(--text-secondary, #8f8f94);
}

.streak-badge {
  padding: 6rpx 20rpx;
  border-radius: 20rpx;
}

.streak-text {
  font-size: 24rpx;
  color: #fff;
  font-weight: 600;
}

.encouragement-content {
  position: relative;
  background: var(--bg-secondary, #F5F6F7);
  border-radius: 24rpx;
  padding: 36rpx 28rpx 28rpx;
  margin-bottom: 24rpx;
}

.quote-mark {
  position: absolute;
  top: 8rpx;
  left: 16rpx;
  font-size: 56rpx;
  font-weight: 700;
  color: var(--primary-light, #A8C9B8);
  line-height: 1;
  font-family: Georgia, serif;
}

.quote-mark.end {
  top: auto;
  left: auto;
  bottom: -8rpx;
  right: 16rpx;
}

.encouragement-text {
  font-size: 30rpx;
  line-height: 1.6;
  color: var(--text-primary, #333);
  text-align: center;
  display: block;
  padding: 0 8rpx;
}

.tier-unlock {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.08), rgba(255, 165, 0, 0.08));
  border: 2rpx solid rgba(255, 215, 0, 0.2);
  border-radius: 20rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 24rpx;
  transition: transform 0.2s;
}

.tier-unlock:active {
  transform: scale(0.97);
}

.tier-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.tier-icon {
  font-size: 36rpx;
}

.tier-info {
  flex: 1;
}

.tier-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary, #333);
  display: block;
  margin-bottom: 4rpx;
}

.tier-reward {
  font-size: 24rpx;
  color: var(--text-secondary, #8f8f94);
}

.tier-arrow {
  font-size: 36rpx;
  color: var(--text-light, #999);
  margin-left: 12rpx;
}

.card-actions {
  display: flex;
  gap: 20rpx;
}

.action-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.action-btn:active {
  transform: scale(0.97);
}

.action-btn.primary {
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  box-shadow: 0 4rpx 16rpx rgba(107, 142, 123, 0.3);
}

.action-btn.primary .btn-icon {
  font-size: 28rpx;
  margin-right: 8rpx;
}

.action-btn.primary .btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}

.action-btn.secondary {
  background: var(--bg-secondary, #F5F6F7);
}

.action-btn.secondary .btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--text-secondary, #666);
}

/* 庆祝粒子 */
.particles {
  position: absolute;
  top: 50%;
  left: 50%;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  animation: particle-burst 1.2s ease-out forwards;
}

@keyframes particle-burst {
  0% {
    opacity: 1;
    transform: translate(0, 0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(var(--tx, 0), var(--ty, 0)) scale(0.3);
  }
}
</style>
