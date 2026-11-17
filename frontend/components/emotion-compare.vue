<template>
  <view class="emotion-compare">
    <view class="compare-header">
      <text class="compare-title">情绪对比</text>
      <text class="compare-desc">记录练习前后的情绪变化</text>
    </view>

    <view class="compare-body">
      <!-- 练习前 -->
      <view class="compare-col">
        <text class="col-label">练习前</text>
        <view class="emotion-grid">
          <view
            v-for="emo in emotions"
            :key="'before-' + emo.key"
            class="emotion-item"
            :class="{ selected: emotionBefore === emo.key }"
            :style="emotionBefore === emo.key ? { background: emo.bgColor, borderColor: emo.color } : {}"
            @click="selectBefore(emo.key)"
          >
            <text class="emo-icon">{{ emo.icon }}</text>
            <text class="emo-name" :style="{ color: emotionBefore === emo.key ? emo.color : '#999' }">{{ emo.label }}</text>
          </view>
        </view>
      </view>

      <!-- 箭头 -->
      <view class="compare-arrow">
        <text class="arrow-icon">→</text>
      </view>

      <!-- 练习后 -->
      <view class="compare-col">
        <text class="col-label">练习后</text>
        <view class="emotion-grid">
          <view
            v-for="emo in emotions"
            :key="'after-' + emo.key"
            class="emotion-item"
            :class="{ selected: emotionAfter === emo.key }"
            :style="emotionAfter === emo.key ? { background: emo.bgColor, borderColor: emo.color } : {}"
            @click="selectAfter(emo.key)"
          >
            <text class="emo-icon">{{ emo.icon }}</text>
            <text class="emo-name" :style="{ color: emotionAfter === emo.key ? emo.color : '#999' }">{{ emo.label }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 情绪变化提示 -->
    <view class="change-hint" v-if="emotionBefore && emotionAfter">
      <view class="change-badge" :style="{ background: changeInfo.bgColor }">
        <text class="change-icon">{{ changeInfo.icon }}</text>
        <text class="change-text" :style="{ color: changeInfo.color }">{{ changeInfo.text }}</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'EmotionCompare',
  props: {
    value: {
      type: Object,
      default: () => ({ before: null, after: null })
    }
  },
  data() {
    return {
      emotionBefore: this.value.before || null,
      emotionAfter: this.value.after || null,
      emotions: [
        { key: 'happy', label: '开心', icon: '😊', color: '#FF9800', bgColor: 'rgba(255, 152, 0, 0.1)' },
        { key: 'excited', label: '兴奋', icon: '🤩', color: '#FF5722', bgColor: 'rgba(255, 87, 34, 0.1)' },
        { key: 'calm', label: '平静', icon: '😌', color: '#4CAF50', bgColor: 'rgba(76, 175, 80, 0.1)' },
        { key: 'sad', label: '难过', icon: '😢', color: '#2196F3', bgColor: 'rgba(33, 150, 243, 0.1)' },
        { key: 'angry', label: '生气', icon: '😠', color: '#F44336', bgColor: 'rgba(244, 67, 54, 0.1)' },
        { key: 'tired', label: '疲惫', icon: '😴', color: '#9C27B0', bgColor: 'rgba(156, 39, 176, 0.1)' }
      ]
    }
  },
  computed: {
    changeInfo() {
      if (!this.emotionBefore || !this.emotionAfter) return {}
      const valence = {
        happy: 2, excited: 2, calm: 1,
        sad: -2, angry: -2, tired: -1
      }
      const beforeVal = valence[this.emotionBefore] || 0
      const afterVal = valence[this.emotionAfter] || 0
      const diff = afterVal - beforeVal

      if (diff > 0) {
        return {
          icon: '📈',
          text: '情绪改善了！正念练习正在发挥作用',
          color: '#4CAF50',
          bgColor: 'rgba(76, 175, 80, 0.1)'
        }
      } else if (diff < 0) {
        return {
          icon: '🤗',
          text: '情绪有些波动，没关系，接纳当下的感受',
          color: '#FF9800',
          bgColor: 'rgba(255, 152, 0, 0.1)'
        }
      } else {
        return {
          icon: '⚖️',
          text: '情绪保持稳定，平静本身就是力量',
          color: '#2196F3',
          bgColor: 'rgba(33, 150, 243, 0.1)'
        }
      }
    }
  },
  watch: {
    value: {
      handler(val) {
        this.emotionBefore = val.before || null
        this.emotionAfter = val.after || null
      },
      deep: true
    }
  },
  methods: {
    selectBefore(key) {
      this.emotionBefore = key
      this.emitChange()
    },
    selectAfter(key) {
      this.emotionAfter = key
      this.emitChange()
    },
    emitChange() {
      this.$emit('input', { before: this.emotionBefore, after: this.emotionAfter })
      this.$emit('change', { before: this.emotionBefore, after: this.emotionAfter })
    }
  }
}
</script>

<style lang="scss" scoped>
.emotion-compare {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.compare-header {
  margin-bottom: 24rpx;
}

.compare-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
  display: block;
  margin-bottom: 4rpx;
}

.compare-desc {
  font-size: 24rpx;
  color: #999;
}

.compare-body {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.compare-col {
  flex: 1;
}

.col-label {
  font-size: 24rpx;
  color: #666;
  font-weight: 600;
  display: block;
  text-align: center;
  margin-bottom: 16rpx;
}

.emotion-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  justify-content: center;
}

.emotion-item {
  width: calc(33.33% - 8rpx);
  padding: 12rpx 4rpx;
  border-radius: 12rpx;
  background: #F8F8F8;
  border: 2rpx solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  transition: all 0.2s ease;
}

.emotion-item:active {
  transform: scale(0.94);
}

.emo-icon {
  font-size: 32rpx;
}

.emo-name {
  font-size: 20rpx;
  color: #999;
}

.compare-arrow {
  display: flex;
  align-items: center;
  padding-top: 40rpx;
}

.arrow-icon {
  font-size: 32rpx;
  color: #6B8E7B;
}

.change-hint {
  margin-top: 20rpx;
}

.change-badge {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 20rpx;
  border-radius: 16rpx;
}

.change-icon {
  font-size: 28rpx;
}

.change-text {
  font-size: 24rpx;
  flex: 1;
}
</style>
