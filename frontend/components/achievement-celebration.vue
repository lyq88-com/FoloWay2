<template>
  <view v-if="visible" class="celebration-mask" @click="close">
    <view class="celebration-container" @click.stop>
      <!-- 烟花/粒子效果 -->
      <view class="firework" v-for="i in 12" :key="i" :style="fireworkStyle(i)"></view>

      <!-- 主内容 -->
      <view class="celebration-card">
        <view class="card-header">
          <text class="milestone-number">{{ data.milestone }}</text>
          <text class="milestone-unit">天</text>
        </view>
        <text class="card-title">{{ data.title }}</text>
        <view class="card-divider"></view>
        <view class="card-story">
          <text class="story-text">{{ data.ai_dialogue }}</text>
        </view>

        <!-- 成就徽章 -->
        <view class="badge-section">
          <view class="achievement-badge">
            <text class="badge-icon">🏅</text>
            <text class="badge-text">{{ data.title }}</text>
          </view>
        </view>

        <!-- 操作按钮 -->
        <view class="celebration-actions">
          <view class="celebration-btn" @click="onShare">
            <text class="btn-icon">📤</text>
            <text class="btn-label">分享</text>
          </view>
          <view class="celebration-btn primary" @click="onViewDiary">
            <text class="btn-icon">📖</text>
            <text class="btn-label">查看日记</text>
          </view>
          <view class="celebration-btn" @click="close">
            <text class="btn-icon">✨</text>
            <text class="btn-label">继续</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { useStore } from 'vuex'
import { computed } from 'vue'

export default {
  name: 'AchievementCelebration',
  setup() {
    const store = useStore()
    const data = computed(() => store.getters.achievementCelebrationData || {})
    const visible = computed(() => !!data.value.milestone)

    const close = () => store.commit('clearAchievementCelebration')

    const fireworkStyle = (i) => {
      const angle = (i * 30) * Math.PI / 180
      const distance = 120 + Math.random() * 40
      const x = Math.cos(angle) * distance
      const y = Math.sin(angle) * distance
      const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
      const color = colors[i % colors.length]
      return {
        '--x': `${x}px`,
        '--y': `${y}px`,
        '--color': color,
        animationDelay: `${i * 0.05}s`,
      }
    }

    const onShare = () => {
      const text = `我达成了「${data.value.title}」成就！连续${data.value.milestone}天打卡！`
      uni.setClipboardData({
        data: text,
        success: () => uni.showToast({ title: '已复制分享文案', icon: 'success' })
      })
    }

    const onViewDiary = () => {
      close()
      uni.switchTab({ url: '/pages/chat/chat' })
    }

    return { visible, data, close, fireworkStyle, onShare, onViewDiary }
  }
}
</script>

<style scoped>
.celebration-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  z-index: 10000;
  display: flex; align-items: center; justify-content: center;
}
.celebration-container {
  position: relative;
  width: 320px;
  height: 400px;
  display: flex; align-items: center; justify-content: center;
}
.firework {
  position: absolute;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--color, #FFD700);
  top: 50%; left: 50%;
  animation: explode 1.2s ease-out forwards;
  animation-delay: var(--delay, 0s);
  opacity: 0;
}
@keyframes explode {
  0% { transform: translate(-50%, -50%) scale(0); opacity: 1; }
  50% { opacity: 1; }
  100% { transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(0.3); opacity: 0; }
}
.celebration-card {
  width: 280px;
  background: #fff;
  border-radius: 20px;
  padding: 24px 20px 16px;
  text-align: center;
  animation: cardBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1;
}
@keyframes cardBounce {
  from { transform: scale(0.5) translateY(30px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}
.card-header { display: flex; align-items: baseline; justify-content: center; }
.milestone-number { font-size: 48px; font-weight: 900; color: #FFD700; text-shadow: 0 2px 8px rgba(255,215,0,0.3); }
.milestone-unit { font-size: 18px; color: #999; margin-left: 4px; }
.card-title { display: block; font-size: 18px; font-weight: bold; color: #333; margin-top: 4px; }
.card-divider { width: 40px; height: 3px; background: #FFD700; border-radius: 2px; margin: 12px auto; }
.card-story { text-align: left; margin: 8px 0 16px; }
.story-text { font-size: 14px; color: #555; line-height: 1.7; }
.badge-section { margin: 12px 0; }
.achievement-badge {
  display: inline-flex; align-items: center;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  padding: 8px 16px; border-radius: 20px;
}
.badge-icon { font-size: 18px; margin-right: 6px; }
.badge-text { font-size: 14px; color: #fff; font-weight: bold; }
.celebration-actions { display: flex; justify-content: space-around; margin-top: 12px; }
.celebration-btn {
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 12px; border-radius: 12px; min-width: 70px;
}
.celebration-btn.primary { background: #f0f0f0; }
.btn-icon { font-size: 22px; }
.btn-label { font-size: 11px; color: #666; margin-top: 4px; }
</style>
