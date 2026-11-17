<template>
  <view class="habit-emotion-heatmap">
    <view class="heatmap-content" v-if="correlations.length">
      <!-- 关联度排行 -->
      <view class="correlation-list">
        <view
          v-for="(item, i) in sortedCorrelations"
          :key="i"
          class="correlation-item"
        >
          <view class="corr-left">
            <view class="corr-icon" :style="{ background: getCorrelationColor(item.correlation) + '20' }">
              <text class="corr-emoji">{{ item.habit_icon }}</text>
            </view>
            <view class="corr-info">
              <text class="corr-name">{{ item.habit_name }}</text>
              <text class="corr-meta">{{ item.checkin_count }}次打卡</text>
            </view>
          </view>
          <view class="corr-middle">
            <view class="corr-emotion-flow">
              <text class="flow-emoji">{{ getEmotionEmoji(item.emotion_before) }}</text>
              <text class="flow-arrow">→</text>
              <text class="flow-emoji">{{ getEmotionEmoji(item.emotion_after) }}</text>
            </view>
            <text class="flow-text">{{ getEmotionLabel(item.emotion_before) }} → {{ getEmotionLabel(item.emotion_after) }}</text>
          </view>
          <view class="corr-right">
            <view class="corr-score-ring" :style="ringStyle(item.correlation)">
              <text class="corr-score">{{ Math.round(item.correlation * 100) }}</text>
            </view>
            <text class="corr-improvement" :class="{ positive: item.improvement > 0 }">
              {{ item.improvement > 0 ? '+' : '' }}{{ item.improvement }}%
            </text>
          </view>
        </view>
      </view>

      <!-- 热力矩阵 -->
      <view class="heatmap-matrix">
        <text class="matrix-title">习惯-情绪关联强度矩阵</text>
        <view class="matrix-grid">
          <!-- 表头 -->
          <view class="matrix-header-row">
            <view class="matrix-corner"></view>
            <view
              v-for="(item, i) in sortedCorrelations"
              :key="'h' + i"
              class="matrix-header"
            >
              <text class="header-emoji">{{ item.habit_icon }}</text>
            </view>
          </view>
          <!-- 每行一个关联度等级 -->
          <view
            v-for="level in heatLevels"
            :key="level.key"
            class="matrix-data-row"
          >
            <view class="matrix-row-label">
              <text class="row-label-text">{{ level.label }}</text>
            </view>
            <view
              v-for="(item, i) in sortedCorrelations"
              :key="'c' + i"
              class="matrix-cell"
              :style="getCellStyle(item, level)"
            >
              <text class="cell-value">{{ getCellValue(item, level) }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- AI洞察 -->
      <view class="heatmap-insights">
        <view class="insight-title-row">
          <text class="insight-emoji">🔍</text>
          <text class="insight-heading">AI关联洞察</text>
        </view>
        <view class="insight-list">
          <view class="insight-item" v-for="(text, i) in insights" :key="i">
            <text class="insight-bullet">•</text>
            <text class="insight-text">{{ text }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="empty-state" v-else>
      <text class="empty-icon">🔗</text>
      <text class="empty-text">暂无习惯-情绪关联数据</text>
      <text class="empty-hint">坚持打卡和记录情绪后即可分析关联</text>
    </view>
  </view>
</template>

<script>
const EMOTION_META = {
  happy: { label: '开心', icon: '😊' },
  excited: { label: '兴奋', icon: '🤩' },
  calm: { label: '平静', icon: '😌' },
  sad: { label: '难过', icon: '😢' },
  angry: { label: '生气', icon: '😠' },
  tired: { label: '疲惫', icon: '😴' }
}

export default {
  name: 'HabitEmotionHeatmap',
  props: {
    data: { type: Array, default: () => [] }
  },
  data() {
    return {
      heatLevels: [
        { key: 'correlation', label: '关联度', max: 1, suffix: '' },
        { key: 'improvement', label: '改善率', max: 100, suffix: '%' },
        { key: 'checkin_count', label: '打卡数', max: 30, suffix: '' },
        { key: 'avg_intensity_after', label: '后强度', max: 10, suffix: '' }
      ]
    }
  },
  computed: {
    correlations() {
      return this.data || []
    },
    sortedCorrelations() {
      return [...this.correlations].sort((a, b) => b.correlation - a.correlation)
    },
    insights() {
      const list = this.sortedCorrelations
      if (!list.length) return []

      const results = []
      const best = list[0]
      const worst = list[list.length - 1]

      if (best && best.correlation > 0.7) {
        results.push(`"${best.habit_name}"与情绪改善的关联度最高（${Math.round(best.correlation * 100)}%），打卡后情绪从${this.getEmotionLabel(best.emotion_before)}转为${this.getEmotionLabel(best.emotion_after)}，改善明显。`)
      }
      if (best && best.improvement > 30) {
        // ↓↓↓ 修复 ↓↓↓ 后端 improvement 的语义是「打卡日 vs 未打卡日的心理状态分提升幅度（百分点）」，
        // 不是原始强度下降，原文案写成「强度平均下降」会与实际数值矛盾（强度常常是升的）。
        results.push(`"${best.habit_name}"对情绪改善效果显著，打卡日心理状态提升${best.improvement}%，建议优先保持这个习惯。`)
      }
      if (worst && worst.correlation < 0.5) {
        results.push(`"${worst.habit_name}"与情绪改善的关联度较低，可能需要调整执行方式或时间。`)
      }
      const avgImprovement = list.reduce((s, c) => s + c.improvement, 0) / list.length
      if (avgImprovement > 25) {
        results.push(`整体来看，习惯打卡对情绪有明显的正向影响，平均改善${Math.round(avgImprovement)}%。`)
      }

      return results.length ? results : ['继续坚持打卡和记录情绪，关联分析会越来越准确~']
    }
  },
  methods: {
    getEmotionLabel(emo) {
      return (EMOTION_META[emo] || {}).label || emo
    },
    getEmotionEmoji(emo) {
      return (EMOTION_META[emo] || {}).icon || '❓'
    },
    getCorrelationColor(score) {
      if (score >= 0.75) return '#6B8E7B'
      if (score >= 0.5) return '#8FBC8F'
      if (score >= 0.3) return '#C6E48B'
      return '#E8E8E8'
    },
    ringStyle(score) {
      const deg = Math.round(score * 360)
      const color = this.getCorrelationColor(score)
      return {
        background: `conic-gradient(${color} ${deg}deg, #F0F0F0 ${deg}deg)`
      }
    },
    getCellValue(item, level) {
      const val = item[level.key]
      if (level.key === 'correlation') return Math.round(val * 100)
      return val + level.suffix
    },
    getCellStyle(item, level) {
      const val = item[level.key]
      const ratio = Math.min(val / level.max, 1)
      if (level.key === 'improvement') {
        if (val > 30) return { background: `rgba(107,142,123,${0.15 + ratio * 0.5})` }
        if (val > 0) return { background: `rgba(168,201,184,${0.1 + ratio * 0.3})` }
        return { background: 'rgba(255,71,87,0.1)' }
      }
      if (level.key === 'correlation') {
        return { background: `rgba(107,142,123,${0.1 + ratio * 0.6})` }
      }
      return { background: `rgba(107,142,123,${0.1 + ratio * 0.3})` }
    }
  }
}
</script>

<style lang="scss" scoped>
.habit-emotion-heatmap {
  width: 100%;
}

.heatmap-content {
  width: 100%;
}

/* 关联度列表 */
.correlation-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.correlation-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
}
.corr-left {
  display: flex;
  align-items: center;
  width: 30%;
}
.corr-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
  flex-shrink: 0;
}
.corr-emoji {
  font-size: 28rpx;
}
.corr-info {
  flex: 1;
  min-width: 0;
}
.corr-name {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.corr-meta {
  font-size: 20rpx;
  color: #999;
  display: block;
}
.corr-middle {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.corr-emotion-flow {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.flow-emoji {
  font-size: 28rpx;
}
.flow-arrow {
  font-size: 24rpx;
  color: #999;
}
.flow-text {
  font-size: 18rpx;
  color: #999;
  margin-top: 4rpx;
}
.corr-right {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.corr-score-ring {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.corr-score-ring::after {
  content: '';
  position: absolute;
  top: 6rpx;
  left: 6rpx;
  right: 6rpx;
  bottom: 6rpx;
  border-radius: 50%;
  background: #fff;
}
.corr-score {
  font-size: 22rpx;
  font-weight: 700;
  color: #333;
  z-index: 1;
}
.corr-improvement {
  font-size: 20rpx;
  color: #999;
  margin-top: 6rpx;
}
.corr-improvement.positive {
  color: #6B8E7B;
  font-weight: 600;
}

/* 热力矩阵 */
.heatmap-matrix {
  margin-bottom: 24rpx;
}
.matrix-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}
.matrix-grid {
  width: 100%;
  overflow-x: auto;
}
.matrix-header-row {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}
.matrix-corner {
  width: 80rpx;
  flex-shrink: 0;
}
.matrix-header {
  flex: 1;
  text-align: center;
  min-width: 60rpx;
}
.header-emoji {
  font-size: 24rpx;
}
.matrix-data-row {
  display: flex;
  align-items: center;
  margin-bottom: 4rpx;
}
.matrix-row-label {
  width: 80rpx;
  flex-shrink: 0;
}
.row-label-text {
  font-size: 20rpx;
  color: #999;
}
.matrix-cell {
  flex: 1;
  min-width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8rpx;
  margin: 0 2rpx;
}
.cell-value {
  font-size: 18rpx;
  color: #333;
  font-weight: 600;
}

/* AI洞察 */
.heatmap-insights {
  padding: 20rpx;
  background: linear-gradient(135deg, rgba(107,142,123,0.08) 0%, rgba(143,188,143,0.05) 100%);
  border-radius: 16rpx;
  border: 1rpx solid rgba(107,142,123,0.15);
}
.insight-title-row {
  display: flex;
  align-items: center;
  margin-bottom: 12rpx;
}
.insight-emoji {
  font-size: 32rpx;
  margin-right: 8rpx;
}
.insight-heading {
  font-size: 28rpx;
  font-weight: 600;
  color: #6B8E7B;
}
.insight-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.insight-item {
  display: flex;
  align-items: flex-start;
}
.insight-bullet {
  font-size: 26rpx;
  color: #6B8E7B;
  margin-right: 8rpx;
  line-height: 1.7;
}
.insight-text {
  font-size: 26rpx;
  color: #555;
  line-height: 1.7;
  flex: 1;
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
