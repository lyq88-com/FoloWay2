<template>
  <view class="xt-page xt-s52">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view class="ttl">
          <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
          <view>
            <view class="page-title">专注统计</view>
            <view class="page-sub">平均每天坐 {{ stat.daily_avg_minutes }} 分钟</view>
          </view>
        </view>
        <view class="icon-btn" @click="exportReport"><xt-icon name="i-calendar" /></view>
      </view>

      <!-- 统计周期 -->
      <view class="seg" style="margin-bottom: 11px">
        <span
          v-for="p in periods"
          :key="p.key"
          :class="{ on: period === p.key }"
          @click="switchPeriod(p.key)"
        >{{ p.label }}</span>
      </view>

      <!-- 三格数据 -->
      <view class="pills">
        <view class="pill">
          <view class="v">{{ Math.floor((stat.total_minutes || 0) / 60) }}<span>h</span> {{ (stat.total_minutes || 0) % 60 }}<span>m</span></view>
          <view class="k">专注总时长</view>
        </view>
        <view class="pill">
          <view class="v">{{ stat.session_count }}<span> 次</span></view>
          <view class="k">发起次数</view>
        </view>
        <view class="pill">
          <view class="v">{{ stat.daily_avg_minutes }}<span> 分钟</span></view>
          <view class="k">日均时长</view>
        </view>
      </view>

      <!-- 标签时长趋势 -->
      <view class="mem-hero" style="margin-top: 11px; padding: 12px 13px">
        <view style="display: flex; justify-content: space-between; align-items: center">
          <text style="font-size: 9px; font-weight: 900">标签时长</text>
          <text style="font-size: 7px; font-weight: 800; color: #24493A">共 {{ stat.tag_pie.length }} 类</text>
        </view>
        <view class="bars" v-if="stat.tag_pie.length">
          <view v-for="(t, i) in stat.tag_pie" :key="i" class="bcol">
            <view class="bv" :style="{ height: Math.min(100, Math.round(t.minutes / (stat.total_minutes || 1) * 220)) + '%' }"></view>
            <view class="bl">{{ t.tag }}</view>
          </view>
        </view>
        <view v-else class="m" style="margin-top: 8px">这段时间还没有专注记录</view>
      </view>

      <!-- 时段热力 -->
      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">24 小时</text>
        <text class="s">越深的日子，你在</text>
      </view>
      <view class="heat">
        <i
          v-for="h in stat.hour_heat"
          :key="h.hour"
          class="l4"
          :style="{ opacity: heatOpacity(h.seconds) }"
        ></i>
      </view>
      <view class="heat-legend">
        <text>少</text>
        <i style="background: #F1F2EA"></i>
        <i style="background: #E3EADF"></i>
        <i style="background: #C3D4C8"></i>
        <i style="background: #94AE9F"></i>
        <i style="background: var(--v7-green)"></i>
        <text>多</text>
      </view>

      <!-- 结论 -->
      <view class="mem-item" style="margin-top: 11px; align-items: flex-start">
        <view class="mi tint-peach"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">最早一次在 {{ stat.earliest_start || '—' }} 开始</view>
          <view class="m">这段时间你发起了 {{ stat.session_count }} 次专注，平均每次 {{ Math.round(stat.total_minutes / (stat.session_count || 1)) }} 分钟。</view>
        </view>
      </view>

      <!-- 角色陪伴 -->
      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">角色陪伴</text>
        <text class="s">不排名，只看陪伴</text>
      </view>
      <view v-if="stat.role_rank.length">
        <view v-for="(r, i) in stat.role_rank" :key="i" class="mem-item" style="align-items: center">
          <view class="mi tint-green"><xt-icon name="i-heart" /></view>
          <view class="tx">
            <view class="t">{{ r.name }} · {{ r.minutes }} 分钟</view>
            <view class="meter" style="margin-top: 5px">
              <i :style="{ width: rankPercent(r) + '%' }"></i>
            </view>
          </view>
        </view>
      </view>
      <view v-else class="mem-hero">
        <view class="m">还没有角色陪伴数据</view>
      </view>

      <view style="height: 18px"></view>
    </view>
  </view>
</template>

<script>
/**
 * 专注统计报表
 * -------------------------------
 * - 维度：日 / 周 / 月 / 自定义（本次交付日/周/月 + 预留 custom 参数）
 * - 指标：总时长 / 日均 / 最早开始 / 发起次数 / 标签饼图 / 时段热力 / 角色排行
 * - 导出：文本报告复制到剪贴板（多端可用，无需原生分享插件）
 * - 图表用 CSS 渐变实现，不引入图表库，保证多端一致与包体轻量
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      periods: [
        { key: 'day', label: '今日' },
        { key: 'week', label: '本周' },
        { key: 'month', label: '本月' }
      ],
      period: 'week',
      stat: {
        total_minutes: 0, daily_avg_minutes: 0, session_count: 0,
        earliest_start: '', tag_pie: [], hour_heat: [], role_rank: []
      },
      pieColors: ['#A8C5B6', '#B39DDB', '#E6C89C', '#8FB5D6', '#E8B0A0', '#7E6FB5']
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    /** conic-gradient 饼图背景（按时长占比分配扇区） */
    pieStyle() {
      const items = this.stat.tag_pie || []
      const total = items.reduce((s, t) => s + t.minutes, 0)
      if (!total) return 'conic-gradient(#EAF1EC 0deg 360deg)'
      let acc = 0
      const segs = []
      items.forEach((t, i) => {
        const from = (acc / total) * 360
        acc += t.minutes
        const to = (acc / total) * 360
        segs.push(`${this.pieColors[i % this.pieColors.length]} ${from}deg ${to}deg`)
      })
      return `conic-gradient(${segs.join(',')})`
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() { this.load() },
  methods: {
    async load() {
      try {
        const res = await focusApi.getStat(this.period)
        if (res && res.code === 200) this.stat = res.data
      } catch (e) { /* noop */ }
    },
    switchPeriod(p) {
      this.period = p
      this.load()
    },
    heatOpacity(seconds) {
      // 归一化到 0.12 ~ 1
      const max = Math.max(...(this.stat.hour_heat || []).map(h => h.seconds), 1)
      return seconds ? Math.max(0.12, seconds / max) : 0.06
    },
    rankPercent(r) {
      const max = Math.max(...(this.stat.role_rank || []).map(x => x.minutes), 1)
      return Math.round((r.minutes / max) * 100)
    },
    /** 导出统计报告为文本（剪贴板，多端可用） */
    exportReport() {
      const s = this.stat
      const lines = [
        '专注统计报告',
        `统计范围：${s.start || ''} ~ ${s.end || ''}`,
        `专注总时长：${s.total_minutes} 分钟（日均 ${s.daily_avg_minutes} 分钟）`,
        `发起次数：${s.session_count} 次；最早开始：${s.earliest_start || '--'}`,
        '',
        '标签时长分布：'
      ]
      s.tag_pie.forEach(t => lines.push(`  · ${t.tag}：${t.minutes} 分钟`))
      lines.push('', '角色陪伴排行：')
      s.role_rank.forEach((r, i) => lines.push(`  ${i + 1}. ${r.name}：${r.minutes} 分钟`))
      uni.setClipboardData({
        data: lines.join('\n'),
        success: () => uni.showToast({ title: '报告已复制，可粘贴导出', icon: 'none' })
      })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 图表较多时在内容区滚动 */
.xt-page.xt-s52 .body {
  overflow-y: auto;
  padding-bottom: 18px;
}
.xt-page.xt-s52 .page-title-row {
  padding-top: 10px;
}
.xt-page.xt-s52 .ttl {
  display: flex;
  align-items: center;
  gap: 9px;
}

/* 柱状标签过长时省略 */
.xt-page.xt-s52 .bars .bl {
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
