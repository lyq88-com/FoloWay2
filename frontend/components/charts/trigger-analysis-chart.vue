<template>
  <view class="trigger-analysis-chart">
    <view class="trigger-content" v-if="triggers.length">
      <!-- 触发因素柱状图 -->
      <view class="trigger-chart">
        <view
          v-for="(item, i) in triggers"
          :key="i"
          class="trigger-bar-row"
        >
          <view class="trigger-bar-label">
            <text class="trigger-tag">{{ item.tag }}</text>
            <text class="trigger-count">{{ item.count }}次</text>
          </view>
          <view class="trigger-bar-track">
            <view class="trigger-bar-fill" :style="{ width: item.barWidth + '%' }">
              <view class="trigger-bar-negative" :style="{ width: item.negativeBarWidth + '%' }"></view>
            </view>
          </view>
          <view class="trigger-bar-info">
            <text class="trigger-intensity">平均强度 {{ item.avg_intensity }}</text>
            <text class="trigger-negative" :class="{ high: item.negative_ratio > 50 }">
              负面 {{ item.negative_ratio }}%
            </text>
          </view>
        </view>
      </view>

      <!-- 触发因素分析洞察 -->
      <view class="trigger-insights">
        <view class="insight-card">
          <text class="insight-icon">⚡</text>
          <view class="insight-body">
            <text class="insight-title">最高频触发</text>
            <text class="insight-text">{{ topTrigger.tag }}（{{ topTrigger.count }}次）</text>
          </view>
        </view>
        <view class="insight-card">
          <text class="insight-icon">😰</text>
          <view class="insight-body">
            <text class="insight-title">最易引发负面情绪</text>
            <text class="insight-text">{{ mostNegative.tag }}（负面{{ mostNegative.negative_ratio }}%）</text>
          </view>
        </view>
        <view class="insight-card">
          <text class="insight-icon">🔥</text>
          <view class="insight-body">
            <text class="insight-title">平均强度最高</text>
            <text class="insight-text">{{ mostIntense.tag }}（强度{{ mostIntense.avg_intensity }}）</text>
          </view>
        </view>
      </view>

      <!-- AI建议 -->
      <view class="trigger-advice" v-if="aiAdvice">
        <view class="advice-header">
          <text class="advice-icon">💡</text>
          <text class="advice-title">AI改善建议</text>
        </view>
        <text class="advice-text">{{ aiAdvice }}</text>
      </view>
    </view>

    <view class="empty-state" v-else>
      <text class="empty-icon">🏷️</text>
      <text class="empty-text">暂无触发因素数据</text>
      <text class="empty-hint">记录情绪时选择触发标签即可分析</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'TriggerAnalysisChart',
  props: {
    data: { type: Array, default: () => [] }
  },
  computed: {
    triggers() {
      const list = this.data || []
      const maxCount = Math.max(...list.map(t => t.count), 1)
      return list.map(t => ({
        ...t,
        barWidth: Math.round(t.count / maxCount * 100),
        negativeBarWidth: Math.round(t.negative_ratio)
      }))
    },
    topTrigger() {
      const list = this.triggers
      if (!list.length) return { tag: '-', count: 0 }
      return list.reduce((max, t) => t.count > max.count ? t : max, list[0])
    },
    mostNegative() {
      const list = this.triggers
      if (!list.length) return { tag: '-', negative_ratio: 0 }
      return list.reduce((max, t) => t.negative_ratio > max.negative_ratio ? t : max, list[0])
    },
    mostIntense() {
      const list = this.triggers
      if (!list.length) return { tag: '-', avg_intensity: 0 }
      return list.reduce((max, t) => t.avg_intensity > max.avg_intensity ? t : max, list[0])
    },
    aiAdvice() {
      const list = this.triggers
      if (!list.length) return ''

      const top = this.topTrigger
      const neg = this.mostNegative
      const intense = this.mostIntense

      let parts = []
      if (top.tag) {
        parts.push(`"${top.tag}"是你最常见的情绪触发因素，出现了${top.count}次。`)
      }
      if (neg.negative_ratio > 50) {
        parts.push(`"${neg.tag}"最容易引发负面情绪（${neg.negative_ratio}%），建议尝试在遇到这类情境时先做3次深呼吸，或者记录下当下的感受。`)
      }
      if (intense.avg_intensity > 6) {
        parts.push(`"${intense.tag}"引发的情绪强度较高（${intense.avg_intensity}），考虑为自己安排一些放松活动来缓冲。`)
      }
      if (parts.length === 0) {
        parts.push('你的情绪触发因素分布较均匀，继续保持对情绪的觉察和记录吧！')
      }
      return parts.join(' ')
    }
  }
}
</script>

<style lang="scss" scoped>
.trigger-analysis-chart {
  width: 100%;
}

.trigger-content {
  width: 100%;
}

.trigger-chart {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-bottom: 24rpx;
}
.trigger-bar-row {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.trigger-bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.trigger-tag {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.trigger-count {
  font-size: 24rpx;
  color: #999;
}
.trigger-bar-track {
  height: 28rpx;
  background: #F0F0F0;
  border-radius: 14rpx;
  overflow: hidden;
  position: relative;
}
.trigger-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #A8C9B8 0%, #6B8E7B 100%);
  border-radius: 14rpx;
  transition: width 0.6s ease;
  position: relative;
  overflow: hidden;
}
.trigger-bar-negative {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(255,71,87,0.3) 0%, rgba(255,71,87,0.5) 100%);
  border-radius: 0 14rpx 14rpx 0;
  transition: width 0.6s ease;
}
.trigger-bar-info {
  display: flex;
  justify-content: space-between;
}
.trigger-intensity {
  font-size: 22rpx;
  color: #999;
}
.trigger-negative {
  font-size: 22rpx;
  color: #6B8E7B;
  font-weight: 500;
}
.trigger-negative.high {
  color: #FF4757;
  font-weight: 600;
}

.trigger-insights {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 24rpx;
}
.insight-card {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
}
.insight-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.insight-body {
  flex: 1;
}
.insight-title {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-bottom: 4rpx;
}
.insight-text {
  font-size: 26rpx;
  color: #333;
  font-weight: 600;
  display: block;
}

.trigger-advice {
  padding: 20rpx;
  background: linear-gradient(135deg, rgba(107,142,123,0.08) 0%, rgba(143,188,143,0.05) 100%);
  border-radius: 16rpx;
  border: 1rpx solid rgba(107,142,123,0.15);
}
.advice-header {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}
.advice-icon {
  font-size: 32rpx;
  margin-right: 8rpx;
}
.advice-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #6B8E7B;
}
.advice-text {
  font-size: 26rpx;
  color: #555;
  line-height: 1.7;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0;
}
.empty-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}
.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 8rpx;
}
.empty-hint {
  font-size: 24rpx;
  color: #ccc;
}
</style>
