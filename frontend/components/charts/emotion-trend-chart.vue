<template>
  <view class="emotion-trend-chart">
    <!-- 周期切换 -->
    <view class="period-switcher">
      <view
        v-for="p in periods"
        :key="p.value"
        class="period-btn"
        :class="{ active: currentPeriod === p.value }"
        @click="switchPeriod(p.value)"
      >
        <text>{{ p.label }}</text>
      </view>
    </view>

    <!-- 趋势图区域 -->
    <view class="chart-area" v-if="trendData.labels && trendData.labels.length">
      <view class="chart-svg-wrap">
        <!-- SVG折线图 -->
        <view class="svg-container">
          <view class="y-axis">
            <text class="y-label" v-for="n in 6" :key="n">{{ 10 - (n - 1) * 2 }}</text>
          </view>
          <view class="chart-body">
            <!-- 网格线 -->
            <view class="grid-line" v-for="n in 5" :key="'g' + n" :style="{ bottom: (n - 1) * 20 + '%' }"></view>
            <!-- 折线区域填充 -->
            <view class="area-fill" :style="areaFillStyle"></view>
            <!-- 折线 -->
            <view class="line-segments">
              <view
                v-for="(seg, i) in lineSegments"
                :key="'s' + i"
                class="line-seg"
                :style="seg.style"
                :class="seg.emotionClass"
              ></view>
            </view>
            <!-- 数据点 -->
            <view class="data-points">
              <view
                v-for="(point, i) in dataPoints"
                :key="'p' + i"
                class="data-point"
                :class="point.emotionClass"
                :style="point.style"
                @click="showPointDetail(i)"
              >
                <view class="point-inner"></view>
                <view class="point-tooltip" v-if="activePoint === i">
                  <text class="tooltip-date">{{ point.date }}</text>
                  <text class="tooltip-value">强度 {{ point.value }}</text>
                  <text class="tooltip-emotion">{{ point.emotionLabel }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
        <!-- X轴标签 -->
        <view class="x-axis">
          <text class="x-label" v-for="(label, i) in xLabels" :key="'x' + i">{{ label }}</text>
        </view>
      </view>

      <!-- 情绪分布图例 -->
      <view class="legend-row">
        <view class="legend-item" v-for="emo in emotionLegend" :key="emo.key">
          <view class="legend-dot" :style="{ background: emo.color }"></view>
          <text class="legend-text">{{ emo.label }}</text>
          <text class="legend-count">{{ emo.count }}次</text>
        </view>
      </view>

      <!-- 趋势统计摘要 -->
      <view class="trend-summary">
        <view class="summary-item">
          <text class="summary-val">{{ avgIntensity }}</text>
          <text class="summary-label">平均强度</text>
        </view>
        <view class="summary-divider2"></view>
        <view class="summary-item">
          <text class="summary-val" :class="trendDirectionClass">{{ trendDirection }}</text>
          <text class="summary-label">趋势方向</text>
        </view>
        <view class="summary-divider2"></view>
        <view class="summary-item">
          <text class="summary-val">{{ recordDays }}</text>
          <text class="summary-label">记录天数</text>
        </view>
        <view class="summary-divider2"></view>
        <view class="summary-item">
          <text class="summary-val">{{ dominantEmotionLabel }}</text>
          <text class="summary-label">主导情绪</text>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty-state" v-else>
      <text class="empty-icon">📊</text>
      <text class="empty-text">暂无情绪趋势数据</text>
      <text class="empty-hint">去情绪打卡页记录今天的心情吧~</text>
    </view>
  </view>
</template>

<script>
const EMOTION_META = {
  happy: { label: '开心', color: '#FFD93D', icon: '😊' },
  excited: { label: '兴奋', color: '#FF6B6B', icon: '🤩' },
  calm: { label: '平静', color: '#6B8E7B', icon: '😌' },
  sad: { label: '难过', color: '#74B9FF', icon: '😢' },
  angry: { label: '生气', color: '#FF4757', icon: '😠' },
  tired: { label: '疲惫', color: '#A29BFE', icon: '😴' }
}

export default {
  name: 'EmotionTrendChart',
  props: {
    data: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      currentPeriod: '7d',
      periods: [
        { label: '7天', value: '7d' },
        { label: '30天', value: '30d' },
        { label: '90天', value: '90d' }
      ],
      activePoint: -1
    }
  },
  computed: {
    trendData() {
      return this.data || {}
    },
    chartWidth() {
      const len = (this.trendData.labels || []).length
      if (len <= 7) return 100
      if (len <= 30) return 200
      return 350
    },
    dataPoints() {
      const labels = this.trendData.labels || []
      const intensities = this.trendData.intensities || []
      const emotions = this.trendData.emotions || []
      const len = labels.length
      if (len === 0) return []

      const stepX = len > 1 ? 100 / (len - 1) : 0
      return intensities.map((val, i) => {
        const x = i * stepX
        const y = 100 - (val / 10) * 100
        const emo = emotions[i] || ''
        const meta = EMOTION_META[emo] || {}
        return {
          date: labels[i],
          value: val,
          emotion: emo,
          emotionLabel: meta.label || '无',
          emotionClass: 'emo-' + (emo || 'none'),
          style: {
            left: x + '%',
            bottom: (val / 10) * 100 + '%'
          }
        }
      }).filter(p => p.value > 0)
    },
    lineSegments() {
      const points = this.dataPoints
      if (points.length < 2) return []
      const segments = []
      for (let i = 1; i < points.length; i++) {
        const p1 = points[i - 1]
        const p2 = points[i]
        const dx = parseFloat(p2.style.left) - parseFloat(p1.style.left)
        const dy = parseFloat(p2.style.bottom) - parseFloat(p1.style.bottom)
        const length = Math.sqrt(dx * dx + dy * dy)
        const angle = Math.atan2(-dy, dx) * (180 / Math.PI)
        segments.push({
          style: {
            left: p1.style.left,
            bottom: p1.style.bottom,
            width: length + '%',
            transform: `rotate(${-angle}deg)`,
            transformOrigin: '0 50%'
          },
          emotionClass: p2.emotionClass
        })
      }
      return segments
    },
    areaFillStyle() {
      const points = this.dataPoints
      if (points.length < 2) return {}
      const pointsStr = points.map(p => `${p.style.left},${100 - parseFloat(p.style.bottom)}`).join(' ')
      return {
        clipPath: `polygon(${pointsStr}, ${parseFloat(points[points.length - 1].style.left)}% 100%, ${parseFloat(points[0].style.left)}% 100%)`
      }
    },
    xLabels() {
      const labels = this.trendData.labels || []
      const len = labels.length
      if (len <= 7) return labels.map(l => l.slice(5))
      if (len <= 30) {
        return labels.filter((_, i) => i % 5 === 0).map(l => l.slice(5))
      }
      return labels.filter((_, i) => i % 15 === 0).map(l => l.slice(5))
    },
    emotionLegend() {
      const distribution = this.trendData.distribution || {}
      return Object.entries(distribution)
        .map(([key, count]) => ({
          key,
          label: (EMOTION_META[key] || {}).label || key,
          color: (EMOTION_META[key] || {}).color || '#999',
          count
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 4)
    },
    avgIntensity() {
      const intensities = (this.trendData.intensities || []).filter(v => v > 0)
      if (!intensities.length) return '0.0'
      return (intensities.reduce((s, v) => s + v, 0) / intensities.length).toFixed(1)
    },
    recordDays() {
      return (this.trendData.intensities || []).filter(v => v > 0).length
    },
    trendDirection() {
      const intensities = (this.trendData.intensities || []).filter(v => v > 0)
      if (intensities.length < 2) return '稳定'
      const first3 = intensities.slice(0, Math.ceil(intensities.length / 3))
      const last3 = intensities.slice(-Math.ceil(intensities.length / 3))
      const avgFirst = first3.reduce((s, v) => s + v, 0) / first3.length
      const avgLast = last3.reduce((s, v) => s + v, 0) / last3.length
      const diff = avgLast - avgFirst
      if (diff > 0.5) return '上升'
      if (diff < -0.5) return '下降'
      return '稳定'
    },
    trendDirectionClass() {
      const dir = this.trendDirection
      if (dir === '上升') return 'dir-up'
      if (dir === '下降') return 'dir-down'
      return 'dir-stable'
    },
    dominantEmotionLabel() {
      const distribution = this.trendData.distribution || {}
      const entries = Object.entries(distribution).sort((a, b) => b[1] - a[1])
      if (!entries.length) return '-'
      const meta = EMOTION_META[entries[0][0]] || {}
      return meta.icon || entries[0][0]
    }
  },
  methods: {
    switchPeriod(period) {
      this.currentPeriod = period
      this.$emit('change', period)
    },
    showPointDetail(index) {
      this.activePoint = this.activePoint === index ? -1 : index
    }
  }
}
</script>

<style lang="scss" scoped>
.emotion-trend-chart {
  width: 100%;
}

.period-switcher {
  display: flex;
  background: #F0F0F0;
  border-radius: 16rpx;
  padding: 6rpx;
  margin-bottom: 24rpx;
}
.period-btn {
  flex: 1;
  text-align: center;
  padding: 12rpx 0;
  border-radius: 12rpx;
  transition: all 0.3s;
}
.period-btn.active {
  background: #fff;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.08);
}
.period-btn text {
  font-size: 26rpx;
  color: #999;
  font-weight: 500;
}
.period-btn.active text {
  color: #6B8E7B;
  font-weight: 600;
}

.chart-area {
  width: 100%;
}

.chart-svg-wrap {
  width: 100%;
}

.svg-container {
  display: flex;
  height: 320rpx;
  position: relative;
}
.y-axis {
  width: 40rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10rpx 0;
}
.y-label {
  font-size: 18rpx;
  color: #bbb;
  text-align: right;
  padding-right: 8rpx;
}
.chart-body {
  flex: 1;
  position: relative;
  margin-left: 8rpx;
}
.grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1rpx;
  background: #F0F0F0;
}
.area-fill {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(107,142,123,0.15) 0%, rgba(107,142,123,0.02) 100%);
}
.line-segments {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
}
.line-seg {
  position: absolute;
  height: 3rpx;
  border-radius: 2rpx;
  background: #6B8E7B;
}
.line-seg.emo-happy { background: #FFD93D; }
.line-seg.emo-excited { background: #FF6B6B; }
.line-seg.emo-calm { background: #6B8E7B; }
.line-seg.emo-sad { background: #74B9FF; }
.line-seg.emo-angry { background: #FF4757; }
.line-seg.emo-tired { background: #A29BFE; }

.data-points {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
}
.data-point {
  position: absolute;
  width: 20rpx;
  height: 20rpx;
  margin-left: -10rpx;
  margin-bottom: -10rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.point-inner {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #6B8E7B;
  border: 3rpx solid #fff;
  box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.15);
}
.data-point.emo-happy .point-inner { background: #FFD93D; }
.data-point.emo-excited .point-inner { background: #FF6B6B; }
.data-point.emo-calm .point-inner { background: #6B8E7B; }
.data-point.emo-sad .point-inner { background: #74B9FF; }
.data-point.emo-angry .point-inner { background: #FF4757; }
.data-point.emo-tired .point-inner { background: #A29BFE; }

.point-tooltip {
  position: absolute;
  bottom: 28rpx;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.8);
  border-radius: 12rpx;
  padding: 12rpx 16rpx;
  white-space: nowrap;
  z-index: 10;
}
.tooltip-date {
  font-size: 20rpx;
  color: #ccc;
  display: block;
}
.tooltip-value {
  font-size: 24rpx;
  color: #fff;
  font-weight: 600;
  display: block;
}
.tooltip-emotion {
  font-size: 20rpx;
  color: #FFD93D;
  display: block;
}

.x-axis {
  display: flex;
  justify-content: space-between;
  padding-left: 48rpx;
  padding-right: 8rpx;
  margin-top: 12rpx;
}
.x-label {
  font-size: 18rpx;
  color: #bbb;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
  padding: 16rpx 0;
  border-top: 1rpx solid #F5F5F5;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6rpx;
}
.legend-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}
.legend-text {
  font-size: 24rpx;
  color: #666;
}
.legend-count {
  font-size: 22rpx;
  color: #999;
}

.trend-summary {
  display: flex;
  align-items: center;
  margin-top: 16rpx;
  padding: 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
}
.summary-item {
  flex: 1;
  text-align: center;
}
.summary-val {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
  display: block;
}
.summary-val.dir-up { color: #FF6B6B; }
.summary-val.dir-down { color: #74B9FF; }
.summary-val.dir-stable { color: #6B8E7B; }
.summary-label {
  font-size: 20rpx;
  color: #999;
  display: block;
  margin-top: 4rpx;
}
.summary-divider2 {
  width: 1rpx;
  height: 50rpx;
  background: #E8E8E8;
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
