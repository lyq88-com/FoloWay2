<template>
  <view class="intensity-slider">
    <view class="slider-header">
      <text class="slider-label">情绪强度</text>
      <view class="slider-value" :style="{ background: currentGradient }">
        <text class="value-text">{{ displayValue }}</text>
      </view>
    </view>

    <view class="slider-track-wrap">
      <!-- 背景轨道 -->
      <view class="slider-track" :style="{ background: trackGradient }"></view>
      <!-- 已选中填充 -->
      <view class="slider-fill" :style="{ width: fillWidth + '%', background: currentGradient }"></view>
      <!-- 滑块按钮 -->
      <view
        class="slider-thumb"
        :style="{ left: thumbLeft + '%', background: currentGradient }"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      ></view>
    </view>

    <view class="slider-marks">
      <view class="mark" v-for="mark in marks" :key="mark" @click="setValue(mark)">
        <text class="mark-text" :class="{ active: value === mark }">{{ mark }}</text>
      </view>
    </view>

    <view class="slider-hint">
      <text class="hint-text">{{ hint }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'EmotionIntensitySlider',
  props: {
    // 当前强度值 0-10
    value: { type: Number, default: 5 },
    // 情绪类型（用于调整颜色基调）
    emotion: { type: String, default: 'calm' }
  },
  data() {
    return {
      trackWidth: 0,
      trackLeft: 0,
      isDragging: false,
      marks: [0, 2, 4, 6, 8, 10]
    }
  },
  computed: {
    displayValue() {
      return this.value
    },
    fillWidth() {
      return (this.value / 10) * 100
    },
    thumbLeft() {
      return (this.value / 10) * 100
    },
    // 颜色配置 - 根据情绪类型和强度动态调整
    currentColors() {
      // 负面情绪：低强度=偏蓝灰，高强度=红
      // 正面情绪：低强度=偏灰，高强度=金黄/橙
      // 中性情绪：低强度=蓝，高强度=青绿
      const emotionColorMap = {
        happy: { low: '#FFE082', mid: '#FFB74D', high: '#FF9800' },
        excited: { low: '#F48FB1', mid: '#EC407A', high: '#D81B60' },
        calm: { low: '#B2DFDB', mid: '#4DB6AC', high: '#00897B' },
        sad: { low: '#90CAF9', mid: '#42A5F5', high: '#1565C0' },
        angry: { low: '#EF9A9A', mid: '#E53935', high: '#B71C1C' },
        tired: { low: '#B0BEC5', mid: '#78909C', high: '#37474F' }
      }
      return emotionColorMap[this.emotion] || emotionColorMap.calm
    },
    currentColor() {
      const v = this.value
      if (v <= 3) return this.currentColors.low
      if (v <= 7) return this.currentColors.mid
      return this.currentColors.high
    },
    currentGradient() {
      const v = this.value
      let from, to
      if (v <= 3) { from = this.currentColors.low; to = this.currentColors.mid }
      else if (v <= 7) { from = this.currentColors.mid; to = this.currentColors.high }
      else { from = this.currentColors.mid; to = this.currentColors.high }
      return `linear-gradient(135deg, ${from}, ${to})`
    },
    trackGradient() {
      return `linear-gradient(90deg, ${this.currentColors.low}, ${this.currentColors.mid}, ${this.currentColors.high})`
    },
    hint() {
      const v = this.value
      if (v === 0) return '几乎无感'
      if (v <= 2) return '轻微'
      if (v <= 4) return '较轻'
      if (v <= 6) return '中等'
      if (v <= 8) return '较强'
      return '非常强烈'
    }
  },
  watch: {
    value() {
      // 父组件可能通过点击 mark 更新，这里不需要额外处理
    }
  },
  methods: {
    measureTrack() {
      // 获取轨道的宽度和位置
      const query = uni.createSelectorQuery().in(this)
      query.select('.slider-track-wrap').boundingClientRect(rect => {
        if (rect) {
          this.trackWidth = rect.width
          this.trackLeft = rect.left
        }
      }).exec()
    },
    onTouchStart(e) {
      this.isDragging = true
      this.measureTrack()
      this.updateFromTouch(e)
    },
    onTouchMove(e) {
      if (!this.isDragging) return
      this.updateFromTouch(e)
    },
    onTouchEnd() {
      this.isDragging = false
    },
    updateFromTouch(e) {
      if (!this.trackWidth) {
        this.measureTrack()
        return
      }
      const touch = e.touches[0] || e.changedTouches[0]
      if (!touch) return
      const x = touch.clientX - this.trackLeft
      const ratio = Math.max(0, Math.min(1, x / this.trackWidth))
      const newValue = Math.round(ratio * 10)
      if (newValue !== this.value) {
        this.$emit('input', newValue)
        this.$emit('change', newValue)
      }
    },
    setValue(val) {
      this.$emit('input', val)
      this.$emit('change', val)
    }
  },
  mounted() {
    // 延迟测量以确保 DOM 渲染完成
    setTimeout(() => this.measureTrack(), 100)
  }
}
</script>

<style lang="scss" scoped>
.intensity-slider {
  padding: 20rpx 0;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}
.slider-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.slider-value {
  min-width: 64rpx;
  height: 48rpx;
  padding: 0 16rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
  transition: background 0.3s ease;
}
.value-text {
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;
}

.slider-track-wrap {
  position: relative;
  height: 48rpx;
  margin: 12rpx 24rpx;
}
.slider-track {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 12rpx;
  border-radius: 6rpx;
  transform: translateY(-50%);
  opacity: 0.35;
}
.slider-fill {
  position: absolute;
  top: 50%;
  left: 0;
  height: 12rpx;
  border-radius: 6rpx;
  transform: translateY(-50%);
  transition: width 0.15s ease, background 0.3s ease;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}
.slider-thumb {
  position: absolute;
  top: 50%;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  border: 4rpx solid #fff;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.25);
  transition: left 0.15s ease, background 0.3s ease;
  z-index: 2;
}

.slider-marks {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 24rpx 0;
}
.mark {
  display: flex;
  align-items: center;
  justify-content: center;
}
.mark-text {
  font-size: 24rpx;
  color: #999;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  transition: all 0.2s ease;
}
.mark-text.active {
  color: #fff;
  font-weight: 700;
}

.slider-hint {
  margin-top: 16rpx;
  text-align: center;
}
.hint-text {
  font-size: 24rpx;
  color: #999;
}
</style>
