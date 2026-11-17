<template>
  <view class="xt-page xt-s29">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">成长足迹</view>
          <view class="page-sub">她替你记住的那些瞬间</view>
        </view>
        <view class="icon-btn" @click="goStats"><xt-icon name="i-calendar" /></view>
      </view>

      <view class="pills">
        <view class="pill">
          <view class="v">{{ totalCheckins }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 次</text></view>
          <view class="k">累计打卡</view>
        </view>
        <view class="pill">
          <view class="v">{{ totalStepsDisplay }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 步</text></view>
          <view class="k">总步数</view>
        </view>
        <view class="pill">
          <view class="v">{{ activeDays }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 天</text></view>
          <view class="k">活跃天数</view>
        </view>
      </view>

      <view class="bond-strip">
        <text>{{ currentStage.name }}</text>
        <view class="bar"><view class="fill" :style="{ width: stageProgress + '%' }"></view></view>
        <text style="color: var(--v7-green); font-weight: 900">{{ stageProgress }}%</text>
      </view>
      <view class="quiz-hint" style="margin: -2px 0 4px">
        <text v-if="nextMilestone">距离「{{ nextMilestone.name }}」还需 {{ nextMilestone.needed }} 次打卡</text>
        <text v-else>已全部通关，旅途圆满</text>
      </view>

      <view v-if="walkHistory.length === 0" class="quiz-hint" style="margin-top: 18px; text-align: center">
        还没有行走记录，完成习惯打卡后她会向前行走
      </view>

      <view v-else class="tl">
        <view v-for="(item, idx) in displayHistory" :key="'history-' + idx" class="tl-item">
          <view class="d">{{ item.date }} {{ item.time }}</view>
          <view class="t">{{ item.description }}</view>
          <view class="m">
            {{ stageNameById(item.stageId) }} ·
            {{ item.type === 'habit' ? '习惯打卡' : (item.type === 'emotion' ? '情绪记录' : '正念冥想') }} ·
            +{{ item.stepCount || 1 }} 步
          </view>
        </view>
      </view>

      <view v-if="walkHistory.length > displayLimit" class="focus-btns" style="margin-top: 4px">
        <view class="fbtn ghost" @click="loadMore">查看更多（{{ walkHistory.length - displayLimit }} 条）</view>
      </view>

      <view style="height: 18px"></view>
    </view>
  </view>
</template>

<script>
import { MAP_STAGES, getNextMilestone } from '@/common/walk-map-config.js'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      allStages: MAP_STAGES,
      displayLimit: 20
    }
  },
  computed: {
    totalCheckins() {
      return this.$store.getters.totalCheckins
    },
    totalStepsDisplay() {
      const steps = this.$store.state.walkMap.totalSteps
      if (steps >= 1000) return (steps / 1000).toFixed(1) + 'k'
      return Math.round(steps)
    },
    activeDays() {
      const history = this.$store.getters.walkHistory
      if (!history || history.length === 0) return 0
      const dates = new Set(history.map(h => h.date))
      return dates.size
    },
    currentStage() {
      return this.$store.getters.currentStage
    },
    stageProgress() {
      return this.$store.getters.stageProgress
    },
    nextMilestone() {
      return getNextMilestone(this.totalCheckins)
    },
    walkHistory() {
      return this.$store.getters.walkHistory
    },
    displayHistory() {
      return [...this.walkHistory].reverse().slice(0, this.displayLimit)
    },
    typeCounts() {
      const history = this.walkHistory
      return {
        habit: history.filter(h => h.type === 'habit').length,
        emotion: history.filter(h => h.type === 'emotion').length,
        meditation: history.filter(h => h.type === 'meditation').length
      }
    },
    currentStageBgStyle() {
      const stage = this.currentStage
      return {
        background: `linear-gradient(135deg, ${stage.theme.skyTop} 0%, ${stage.theme.skyBottom} 100%)`
      }
    }
  },
  methods: {
    goStats() {
      uni.navigateTo({ url: '/pages/stats/stats' })
    },
    isStageUnlocked(stage) {
      return this.totalCheckins >= stage.threshold
    },
    dotStyle(stage) {
      return {
        background: `linear-gradient(135deg, ${stage.theme.accent}, ${stage.theme.pathColor})`
      }
    },
    typePercent(type) {
      const total = this.typeCounts.habit + this.typeCounts.emotion + this.typeCounts.meditation
      if (total === 0) return 0
      return Math.round((this.typeCounts[type] / total) * 100)
    },
    typeEmoji(type) {
      const map = { habit: '✅', emotion: '💭', meditation: '🧘' }
      return map[type] || '👣'
    },
    stageNameById(stageId) {
      const stage = MAP_STAGES.find(s => s.id === stageId)
      return stage ? stage.name : '未知'
    },
    loadMore() {
      this.displayLimit += 20
    }
  }
}
</script>

<style scoped>
/* i 元素选择器的等价 class（进度条） */
.bond-strip .bar .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9CBFAA, var(--v7-green));
}
</style>
