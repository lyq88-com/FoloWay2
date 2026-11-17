<template>
  <view class="emotion-distribution-chart">
    <view class="dist-content" v-if="distribution.length">
      <!-- 环形图 -->
      <view class="donut-chart">
        <view class="donut-wrap">
          <view class="donut-ring">
            <view
              v-for="(seg, i) in segments"
              :key="i"
              class="donut-seg"
              :style="seg.style"
            ></view>
          </view>
          <view class="donut-center">
            <text class="donut-total">{{ totalRecords }}</text>
            <text class="donut-label">总记录</text>
          </view>
        </view>
      </view>

      <!-- 图例列表 -->
      <view class="dist-legend">
        <view
          v-for="(item, i) in distribution"
          :key="i"
          class="dist-item"
          :class="{ active: activeIndex === i }"
          @click="toggleActive(i)"
        >
          <view class="dist-left">
            <view class="dist-dot" :style="{ background: item.color }"></view>
            <text class="dist-emoji">{{ item.icon }}</text>
            <text class="dist-name">{{ item.label }}</text>
          </view>
          <view class="dist-right">
            <text class="dist-count">{{ item.count }}次</text>
            <text class="dist-ratio">{{ item.ratio }}%</text>
            <view class="dist-bar-wrap">
              <view class="dist-bar" :style="{ width: item.ratio + '%', background: item.color }"></view>
            </view>
          </view>
        </view>
      </view>

      <!-- 情绪状态分析 -->
      <view class="dist-analysis">
        <view class="analysis-row">
          <text class="analysis-label">积极情绪占比</text>
          <view class="analysis-bar-wrap">
            <view class="analysis-bar positive" :style="{ width: positiveRatio + '%' }"></view>
          </view>
          <text class="analysis-val">{{ positiveRatio }}%</text>
        </view>
        <view class="analysis-row">
          <text class="analysis-label">负面情绪占比</text>
          <view class="analysis-bar-wrap">
            <view class="analysis-bar negative" :style="{ width: negativeRatio + '%' }"></view>
          </view>
          <text class="analysis-val">{{ negativeRatio }}%</text>
        </view>
        <view class="analysis-row">
          <text class="analysis-label">中性情绪占比</text>
          <view class="analysis-bar-wrap">
            <view class="analysis-bar neutral" :style="{ width: neutralRatio + '%' }"></view>
          </view>
          <text class="analysis-val">{{ neutralRatio }}%</text>
        </view>
      </view>
    </view>

    <view class="empty-state" v-else>
      <text class="empty-icon">🌈</text>
      <text class="empty-text">暂无情绪分布数据</text>
    </view>
  </view>
</template>

<script>
const EMOTION_META = {
  happy: { label: '开心', color: '#FFD93D', icon: '😊', valence: 'positive' },
  excited: { label: '兴奋', color: '#FF6B6B', icon: '🤩', valence: 'positive' },
  calm: { label: '平静', color: '#6B8E7B', icon: '😌', valence: 'neutral' },
  sad: { label: '难过', color: '#74B9FF', icon: '😢', valence: 'negative' },
  angry: { label: '生气', color: '#FF4757', icon: '😠', valence: 'negative' },
  tired: { label: '疲惫', color: '#A29BFE', icon: '😴', valence: 'negative' }
}

export default {
  name: 'EmotionDistributionChart',
  props: {
    data: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      activeIndex: -1
    }
  },
  computed: {
    distribution() {
      const dist = (this.data && this.data.distribution) || []
      return dist.map(item => {
        const meta = EMOTION_META[item.emotion] || {}
        return {
          ...item,
          label: meta.label || item.label || item.emotion,
          color: meta.color || '#999',
          icon: meta.icon || '❓',
          valence: meta.valence || 'neutral'
        }
      })
    },
    totalRecords() {
      return (this.data && this.data.total) || 0
    },
    segments() {
      const total = this.totalRecords
      if (total === 0) return []
      let accumulated = 0
      return this.distribution.map((item, i) => {
        const ratio = item.count / total
        const startAngle = accumulated * 360 - 90
        const endAngle = (accumulated + ratio) * 360 - 90
        accumulated += ratio
        return {
          style: this.makeDonutSegment(startAngle, endAngle, item.color)
        }
      })
    },
    positiveRatio() {
      const total = this.totalRecords
      if (!total) return 0
      const count = this.distribution.filter(d => d.valence === 'positive').reduce((s, d) => s + d.count, 0)
      return Math.round(count / total * 100)
    },
    negativeRatio() {
      const total = this.totalRecords
      if (!total) return 0
      const count = this.distribution.filter(d => d.valence === 'negative').reduce((s, d) => s + d.count, 0)
      return Math.round(count / total * 100)
    },
    neutralRatio() {
      const total = this.totalRecords
      if (!total) return 0
      const count = this.distribution.filter(d => d.valence === 'neutral').reduce((s, d) => s + d.count, 0)
      return Math.round(count / total * 100)
    }
  },
  methods: {
    toggleActive(index) {
      this.activeIndex = this.activeIndex === index ? -1 : index
    },
    makeDonutSegment(startAngle, endAngle, color) {
      // CSS conic-gradient approach for ring segments
      const start = startAngle + 90 // normalize so 0 is top
      const end = endAngle + 90
      return {
        background: `conic-gradient(${color} ${start}deg ${end}deg, transparent ${end}deg ${start + 360}deg)`,
        position: 'absolute',
        top: '0',
        left: '0',
        right: '0',
        bottom: '0',
        borderRadius: '50%'
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.emotion-distribution-chart {
  width: 100%;
}

.dist-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.donut-chart {
  margin-bottom: 24rpx;
}
.donut-wrap {
  position: relative;
  width: 240rpx;
  height: 240rpx;
}
.donut-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
}
.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.06);
}
.donut-total {
  font-size: 44rpx;
  font-weight: 700;
  color: #333;
}
.donut-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

.dist-legend {
  width: 100%;
}
.dist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #F5F5F5;
  transition: background 0.2s;
}
.dist-item.active {
  background: #F8F9FA;
  border-radius: 12rpx;
  padding: 16rpx;
}
.dist-left {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.dist-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}
.dist-emoji {
  font-size: 28rpx;
}
.dist-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}
.dist-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
}
.dist-count {
  font-size: 24rpx;
  color: #666;
}
.dist-ratio {
  font-size: 28rpx;
  font-weight: 700;
  color: #333;
}
.dist-bar-wrap {
  width: 120rpx;
  height: 8rpx;
  background: #F0F0F0;
  border-radius: 4rpx;
  overflow: hidden;
}
.dist-bar {
  height: 100%;
  border-radius: 4rpx;
  transition: width 0.6s ease;
}

.dist-analysis {
  width: 100%;
  margin-top: 20rpx;
  padding: 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
}
.analysis-row {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}
.analysis-row:last-child {
  margin-bottom: 0;
}
.analysis-label {
  font-size: 24rpx;
  color: #666;
  width: 180rpx;
  flex-shrink: 0;
}
.analysis-bar-wrap {
  flex: 1;
  height: 16rpx;
  background: #E8E8E8;
  border-radius: 8rpx;
  overflow: hidden;
  margin: 0 16rpx;
}
.analysis-bar {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.6s ease;
}
.analysis-bar.positive {
  background: linear-gradient(90deg, #FFD93D, #FFA500);
}
.analysis-bar.negative {
  background: linear-gradient(90deg, #74B9FF, #0984E3);
}
.analysis-bar.neutral {
  background: linear-gradient(90deg, #6B8E7B, #8FBC8F);
}
.analysis-val {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
  width: 60rpx;
  text-align: right;
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
}
</style>
