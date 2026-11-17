<template>
  <view v-if="type" class="emotion-tag" :style="tagStyle">
    <text class="emotion-tag-icon">{{ emotionConfig.icon }}</text>
    <text class="emotion-tag-text">{{ emotionConfig.label }}</text>
    <text v-if="showIntensity && intensity > 0" class="emotion-tag-intensity">{{ intensity }}/10</text>
  </view>
</template>

<script>
const EMOTION_CONFIG = {
  happy: { label: '开心', icon: '😊', color: '#FFD93D', bg: 'rgba(255, 217, 61, 0.15)' },
  excited: { label: '兴奋', icon: '🤩', color: '#FF6B6B', bg: 'rgba(255, 107, 107, 0.15)' },
  calm: { label: '平静', icon: '😌', color: '#81C784', bg: 'rgba(129, 199, 132, 0.15)' },
  sad: { label: '难过', icon: '😢', color: '#64B5F6', bg: 'rgba(100, 181, 246, 0.15)' },
  angry: { label: '生气', icon: '😠', color: '#EF5350', bg: 'rgba(239, 83, 80, 0.15)' },
  tired: { label: '疲惫', icon: '😩', color: '#9E9E9E', bg: 'rgba(158, 158, 158, 0.15)' },
  normal: { label: '平静', icon: '🌿', color: '#81C784', bg: 'rgba(129, 199, 132, 0.15)' },
  gentle: { label: '温柔', icon: '🤗', color: '#F48FB1', bg: 'rgba(244, 143, 177, 0.15)' },
  encourage: { label: '鼓励', icon: '💪', color: '#FFB74D', bg: 'rgba(255, 183, 77, 0.15)' }
}

export default {
  name: 'EmotionTag',
  props: {
    type: { type: String, default: '' },
    intensity: { type: Number, default: 0 },
    showIntensity: { type: Boolean, default: false },
    size: { type: String, default: 'normal' } // 'small' | 'normal'
  },
  computed: {
    emotionConfig() {
      return EMOTION_CONFIG[this.type] || EMOTION_CONFIG.normal
    },
    tagStyle() {
      const styles = {
        color: this.emotionConfig.color,
        background: this.emotionConfig.bg
      }
      if (this.size === 'small') {
        styles.padding = '2rpx 12rpx'
        styles.fontSize = '20rpx'
      }
      return styles
    }
  }
}
</script>

<style lang="scss" scoped>
.emotion-tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 16rpx;
  gap: 4rpx;
}
.emotion-tag-icon {
  font-size: 22rpx;
}
.emotion-tag-text {
  font-size: 22rpx;
  font-weight: 500;
}
.emotion-tag-intensity {
  font-size: 18rpx;
  opacity: 0.7;
  margin-left: 2rpx;
}
</style>
