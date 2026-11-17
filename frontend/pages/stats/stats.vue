<template>
  <view class="xt-page xt-s27">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">数据统计</view>
          <view class="page-sub">她只记你的进步，不记你的失败</view>
        </view>
        <view class="icon-btn" @click="goGrowthArchive"><xt-icon name="i-calendar" /></view>
      </view>

      <view class="seg" style="margin:2px 0 12px">
        <view class="sg" :class="{ on: period === 'week' }" @click="switchPeriod('week')">本周</view>
        <view class="sg" :class="{ on: period === 'month' }" @click="switchPeriod('month')">本月</view>
        <view class="sg" :class="{ on: period === 'year' }" @click="switchPeriod('year')">今年</view>
      </view>

      <view class="mem-hero" style="text-align:center;padding:18px 14px">
        <view style="font-size:8px;letter-spacing:1.2px;color:#8E9A91">连续打卡</view>
        <view style="margin-top:4px;font-size:34px;font-weight:900;letter-spacing:-1.5px">{{ summary.streakDays || 0 }}<text style="font-size:11px;font-weight:800;color:#8E9A91"> 天</text></view>
        <view style="margin-top:4px;font-size:8px;color:#8E9A91">累计打卡 {{ summary.totalCheckins || 0 }} 次</view>
      </view>

      <view class="cal-sec" style="margin-top:12px">
        <text class="t">{{ periodTitle }}</text>
        <text class="s">平均 {{ periodAvgRate }}%</text>
      </view>
      <view class="bars" :class="{ 'bars--month': period === 'month', 'bars--year': period === 'year' }">
        <view v-for="(d, i) in periodData" :key="i" class="bcol">
          <view class="bv" :class="{ dim: !d.rate }" :style="{ height: (d.rate || 0) + '%' }"></view>
          <text class="bl">{{ chartDayLabel(d, i) }}</text>
        </view>
      </view>

      <view class="pills" style="margin-top:12px">
        <view class="pill">
          <view class="v">{{ summary.todayCompleted || 0 }}/{{ summary.todayTotal || 0 }}</view>
          <view class="k">今日完成</view>
        </view>
        <view class="pill">
          <view class="v">{{ periodTotal }}<text class="u"> 次</text></view>
          <view class="k">{{ period === 'week' ? '本周打卡' : (period === 'month' ? '本月打卡' : '今年打卡') }}</view>
        </view>
        <view class="pill">
          <view class="v">{{ summary.completionRate || 0 }}<text class="u">%</text></view>
          <view class="k">完成率</view>
        </view>
      </view>

      <view class="n-group-t">分类完成度</view>
      <view v-for="row in categoryRows" :key="row.name" class="set-row">
        <view class="si" :class="row.tint"><xt-icon :name="row.ic" /></view>
        <view class="tx">
          <view class="t">{{ row.name }}</view>
          <view class="meter" style="margin-top:5px"><view class="fill" :style="{ width: (row.rate || 0) + '%' }"></view></view>
        </view>
        <text class="v">{{ row.rate || 0 }}%</text>
      </view>
    </view>
  </view>
</template>

<script>
import statsApi from '@/api/stats'
import emotionApi from '@/api/emotion'
import userApi from '@/api/user'
import { getCharacterById } from '@/common/ai-characters'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const HABIT_ICONS = { '💧': 'i-water', '📚': 'i-book', '🏃': 'i-focus', '🌙': 'i-moon', '🧘': 'i-spark' }
const ROW_TINTS = ['tint-green', 'tint-blue', 'tint-teal', 'tint-peach']

export default {
  components: {
    XtIcon
  },
  data() {
    return {
      summary: {},
      period: 'month',
      weekData: [],
      monthData: [],
      yearData: [],
      habitStats: [],
      badges: [],
      emotionTrendData: {},
      emotionDistData: {},
      emotionTriggers: [],
      habitEmotionCorrelation: [],
      growthReport: null,
      isGeneratingReport: false,
      reportDate: '',
      reportType: 'weekly',
      emotionPeriod: '7d'
    }
  },
  computed: {
    todayProgress() {
      if (!this.summary.todayTotal) return 0
      return Math.round(this.summary.todayCompleted / this.summary.todayTotal * 100)
    },
    weekTotal() {
      return this.weekData.reduce((sum, d) => sum + (d.completed || 0), 0)
    },
    weekAvgRate() {
      if (!this.weekData.length) return 0
      const total = this.weekData.reduce((sum, d) => sum + (d.rate || 0), 0)
      return Math.round(total / this.weekData.length)
    },
    periodData() {
      if (this.period === 'week') return this.weekData
      if (this.period === 'year') return this.yearData
      return this.monthData
    },
    periodTitle() {
      if (this.period === 'week') return '近 7 天完成度'
      if (this.period === 'year') return '今年每月完成度'
      return '本月完成度'
    },
    periodTotal() {
      return this.periodData.reduce((sum, d) => sum + (d.completed || 0), 0)
    },
    periodAvgRate() {
      if (!this.periodData.length) return 0
      const total = this.periodData.reduce((sum, d) => sum + (d.rate || 0), 0)
      return Math.round(total / this.periodData.length)
    },
    categoryRows() {
      return this.habitStats.map((h, i) => ({
        name: h.name,
        rate: h.rate,
        ic: HABIT_ICONS[h.icon] || 'i-spark',
        tint: ROW_TINTS[i % ROW_TINTS.length]
      }))
    },
    aiName() {
      return this.$store.state.aiConfig.name || '林夕'
    },
    aiAvatar() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      return character?.avatar || '🌿'
    },
    currentCharacter() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      return getCharacterById(characterId)
    },
    reportPeriodText() {
      if (!this.growthReport) return ''
      const typeMap = { weekly: '周报', monthly: '月报', quarterly: '季报', yearly: '年报' }
      return typeMap[this.growthReport.type] || '报告'
    }
  },
  onShow() {
    this.loadAll()
  },
  methods: {
    switchPeriod(p) {
      if (this.period === p) return
      this.period = p
      if (p === 'year' && !this.yearData.length) this.loadYearData()
    },
    chartDayLabel(d, i) {
      if (this.period === 'week') return d.day || ''
      if (this.period === 'year') {
        const raw = d.date || ''
        return raw ? String(Number(String(raw).slice(-2))) : ''
      }
      // 月度 30 根柱子，标签每 5 天显示一次，避免挤在一起
      if (i % 5 !== 0) return ''
      const raw = d.date || ''
      return raw ? String(raw).slice(-2) : ''
    },
    async loadYearData() {
      try {
        const res = await statsApi.getYearData()
        if (res && res.code === 200) this.yearData = res.data || []
      } catch (e) {
        console.error('加载年度统计失败', e)
        uni.showToast({ title: '年度统计加载失败', icon: 'none' })
      }
    },
    goGrowthArchive() {
      uni.navigateTo({ url: '/pages/growth-archive/growth-archive' })
    },
    async loadAll() {
      try {
        const [summaryRes, weekRes, monthRes, habitRes, badgeRes] = await Promise.all([
          statsApi.getSummary(),
          statsApi.getWeekData(),
          statsApi.getMonthData(),
          statsApi.getHabitStats(),
          userApi.getBadges()
        ])
        if (summaryRes.code === 200) this.summary = summaryRes.data
        if (weekRes.code === 200) this.weekData = weekRes.data
        if (monthRes.code === 200) this.monthData = monthRes.data
        if (habitRes.code === 200) this.habitStats = habitRes.data
        if (badgeRes.code === 200) this.badges = badgeRes.data.slice(0, 5)
      } catch (e) {
        console.error('加载统计数据失败', e)
      }
      this.loadEmotionVisualization()
      this.loadHabitEmotionCorrelation()
    },
    async loadEmotionVisualization() {
      try {
        const [trendRes, distRes, triggerRes] = await Promise.all([
          emotionApi.getEmotionTrend(this.emotionPeriod),
          emotionApi.getEmotionDistribution('30d'),
          emotionApi.getEmotionTriggers('30d')
        ])
        if (trendRes.code === 200) this.emotionTrendData = trendRes.data
        if (distRes.code === 200) this.emotionDistData = distRes.data
        if (triggerRes.code === 200) this.emotionTriggers = triggerRes.data
      } catch (e) {
        console.error('加载情绪可视化数据失败', e)
      }
    },
    async loadHabitEmotionCorrelation() {
      try {
        const res = await statsApi.getHabitEmotionCorrelation()
        // ↓↓↓ 修复 ↓↓↓ 后端 /stats/emotion/habit-correlation 原来返回
        // { success_top, fail_top, ... } 摘要对象，而图表要的是
        // 「每个习惯一行」的数组 → 直接赋值会报 "Expected Array, got Object"，永远显示「暂无数据」。
        // 后端已改为返回数组（每个习惯 = habit_name/correlation/improvement/...），
        // 这里保留兼容：拿到数组直接用，拿到对象就取 correlations 字段，都没有则置空走空态。
        if (res.code !== 200) return
        const d = res.data
        let rows = []
        if (Array.isArray(d)) rows = d
        else if (d && Array.isArray(d.correlations)) rows = d.correlations
        this.habitEmotionCorrelation = rows
      } catch (e) {
        console.error('加载习惯情绪关联失败', e)
      }
    },
    onTrendPeriodChange(period) {
      this.emotionPeriod = period
      this.loadEmotionTrend(period)
    },
    async loadEmotionTrend(period) {
      try {
        const res = await emotionApi.getEmotionTrend(period)
        if (res.code === 200) this.emotionTrendData = res.data
      } catch (e) {
        console.error('加载情绪趋势失败', e)
      }
    },
    isToday(dateStr) {
      const d = new Date()
      const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      return dateStr === today
    },
    goProfile() {
      uni.switchTab({ url: '/pages/profile/profile' })
    },
    switchReportType(type) {
      if (this.reportType === type) return
      this.reportType = type
      this.growthReport = null
    },
    async generateReport() {
      if (this.isGeneratingReport) return
      this.isGeneratingReport = true
      try {
        await this.delay(800)
        const res = await statsApi.getGrowthReport(this.reportType)
        if (res.code === 200) {
          this.growthReport = res.data
          this.reportDate = new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })
          uni.showToast({ title: '报告生成成功！', icon: 'success' })
        } else {
          throw new Error(res.message || '生成失败')
        }
      } catch (e) {
        console.error('生成报告失败:', e)
        uni.showToast({ title: '生成报告失败', icon: 'none' })
      } finally {
        this.isGeneratingReport = false
      }
    },
    async exportData(format) {
      try {
        uni.showLoading({ title: '导出中...' })
        await this.delay(500)
        const res = await statsApi.exportData(format)
        if (res.code === 200 && res.data) {
          const content = res.data.content || ''
          const filename = res.data.filename || `export_${Date.now()}.${format}`
          if (format === 'json') {
            uni.setClipboardData({
              data: content,
              success: () => {
                uni.showToast({ title: 'JSON已复制到剪贴板', icon: 'success' })
              }
            })
          } else {
            uni.setClipboardData({
              data: content,
              success: () => {
                uni.showToast({ title: 'CSV已复制到剪贴板', icon: 'success' })
              }
            })
          }
        }
      } catch (e) {
        console.error('导出失败:', e)
        uni.showToast({ title: '导出失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    },
    shareReport() {
      if (!this.growthReport) {
        uni.showToast({ title: '请先生成报告', icon: 'none' })
        return
      }
      const summary = this.growthReport.summary || '我的成长报告'
      const analysis = this.growthReport.ai_analysis || ''
      const shareText = `【循途成长报告】\n${summary}\n\n${analysis}\n\n——来自循途`

      uni.setClipboardData({
        data: shareText,
        success: () => {
          uni.showToast({ title: '报告已复制，快去分享吧！', icon: 'success' })
        }
      })
    },
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿 .seg span / .meter i 的元素选择器在 uni-app 中改用等价 class */
.seg .sg {
  flex: 1;
  padding: 7px 0;
  border-radius: 9px;
  text-align: center;
  font-size: 8px;
  color: #8E9A91;
  background: var(--v7-card);
}
.seg .sg.on {
  color: #26332C;
  font-weight: 900;
  background: #fff;
  box-shadow: 0 0 0 1px var(--v7-line);
}
.meter .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9CBFAA, var(--v7-green));
}
/* 月度 30 根柱子：收窄间距，避免每根柱子被挤成 3-4px */
.bars.bars--month {
  gap: 2px;
  padding-left: 0;
  padding-right: 0;
}
.bars.bars--month .bl {
  font-size: 6px;
}
/* 年度 12 根柱子 */
.bars.bars--year {
  gap: 4px;
}
.bars.bars--year .bl {
  font-size: 6px;
}
</style>
