<template>
  <view class="xt-page xt-s30">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">成长档案</view>
          <view class="page-sub">{{ currentYear }} · 你留下的颜色</view>
        </view>
        <view class="icon-btn" @click="refreshAll"><xt-icon name="i-archive" /></view>
      </view>

      <view class="chips" style="margin: 0 0 10px">
        <view
          v-for="p in periods"
          :key="p.key"
          class="chip"
          :class="{ on: selectedPeriod === p.key }"
          @click="switchPeriod(p.key)"
        >{{ p.label }}</view>
      </view>

      <view class="mem-hero" style="padding: 13px">
        <view style="display: flex; align-items: center; justify-content: space-between">
          <text style="font-size: 9px; font-weight: 900">本期打卡 {{ currentReport.checkin_count || 0 }} 天</text>
          <text style="font-size: 7px; color: #8E9A91">完成率 {{ currentReport.completion_rate || 0 }}%</text>
        </view>
        <view class="heat" style="margin-top: 9px">
          <view v-for="(lv, i) in heatCells" :key="'heat-' + i" class="hc" :class="lv"></view>
        </view>
        <view class="heat-legend">
          <text>少</text>
          <view class="lg" style="background: #F3F6F5"></view>
          <view class="lg" style="background: #DEE7E2"></view>
          <view class="lg" style="background: #BBCDC4"></view>
          <view class="lg" style="background: #90A99D"></view>
          <view class="lg" style="background: var(--v7-green)"></view>
          <text>多</text>
        </view>
      </view>

      <view v-if="loading" class="quiz-hint" style="margin-top: 12px; text-align: center">正在生成成长报告…</view>

      <view class="cal-sec" style="margin-top: 12px">
        <text class="t">月度小结</text>
        <text class="s">她写的</text>
      </view>

      <view class="mem-item" v-if="currentReport.summary">
        <view class="mi tint-green"><xt-icon name="i-moon" /></view>
        <view class="tx">
          <view class="t">{{ currentReport.period_start }} ~ {{ currentReport.period_end }}</view>
          <view class="m">“{{ currentReport.summary }}”</view>
          <view class="d">生成于 {{ formatCreatedAt(currentReport.created_at) }} · {{ periodLabel }}</view>
        </view>
      </view>

      <view
        v-for="(h, i) in highlights"
        :key="'hl-' + i"
        class="mem-item"
      >
        <view class="mi" :class="i % 2 ? 'tint-peach' : 'tint-blue'">
          <xt-icon :name="i % 2 ? 'i-heart' : 'i-spark'" />
        </view>
        <view class="tx">
          <view class="t">{{ periodLabel }} · 亮点 {{ i + 1 }}</view>
          <view class="m">{{ h }}</view>
        </view>
      </view>

      <view class="pills" style="margin-top: 12px; margin-bottom: 0">
        <view class="pill">
          <view class="v">{{ currentReport.checkin_count || 0 }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 天</text></view>
          <view class="k">习惯打卡</view>
        </view>
        <view class="pill">
          <view class="v">{{ currentReport.completion_rate || 0 }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700">%</text></view>
          <view class="k">完成率</view>
        </view>
        <view class="pill">
          <view class="v">{{ currentReport.emotion_count || 0 }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 次</text></view>
          <view class="k">情绪记录</view>
        </view>
        <view class="pill">
          <view class="v">{{ currentReport.mindfulness_count || 0 }}<text style="font-size: 7px; color: #AEB6AE; font-weight: 700"> 次</text></view>
          <view class="k">正念练习</view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 14px">
        <text class="t">情绪分布</text>
        <text class="s">平均强度 {{ currentReport.avg_intensity || 0 }}</text>
      </view>
      <view class="prob" v-if="emotionDistEntries.length > 0">
        <view v-for="(item, i) in emotionDistEntries" :key="item.emotion" class="pr">
          <text class="tag" :class="i === 0 ? 'ssr' : (i === 1 ? 'sr' : 'r')">{{ emotionNameMap[item.emotion] || item.emotion }}</text>
          {{ item.count }} 次
          <text style="margin-left: auto; font-size: 8.5px; color: #22302A">{{ item.percent }}%</text>
        </view>
      </view>
      <view class="quiz-hint" v-else style="margin-top: 6px">这段时间还没有情绪记录</view>

      <view class="mem-item" v-if="currentReport.total_meditation_min">
        <view class="mi tint-teal"><xt-icon name="i-moon" /></view>
        <view class="tx">
          <view class="t">正念 {{ currentReport.total_meditation_min }} 分钟</view>
          <view class="m">共 {{ currentReport.mindfulness_count || 0 }} 次 · 平均每次 {{ avgMeditationMin }} 分钟</view>
        </view>
      </view>
      <view class="mem-item" v-if="currentReport.walk_steps">
        <view class="mi tint-sand"><xt-icon name="i-world" /></view>
        <view class="tx">
          <view class="t">环球行走 {{ currentReport.walk_steps }} 步</view>
          <view class="m">已抵达 {{ currentReport.walk_milestone || '初始起点' }}</view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 14px" v-if="suggestions.length > 0">
        <text class="t">她给的建议</text>
        <text class="s">一点点就好</text>
      </view>
      <view v-for="(s, i) in suggestions" :key="'sg-' + i" class="mem-item">
        <view class="mi tint-green"><text style="font-size: 10px; font-weight: 900">{{ i + 1 }}</text></view>
        <view class="tx">
          <view class="m" style="font-size: 8.5px; color: #6A776E">{{ s }}</view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 14px">
        <text class="t">历史档案</text>
        <text class="s">{{ archiveList.length }} 份</text>
      </view>
      <view
        v-for="item in archiveList"
        :key="item.id"
        class="set-row"
        @click="viewArchiveDetail(item)"
      >
        <view class="si tint-green"><xt-icon name="i-archive" /></view>
        <view class="tx">
          <view class="t">{{ periodTypeLabel(item.period_type) }} · {{ item.period_start }} ~ {{ item.period_end }}</view>
          <view class="m">{{ item.summary }}</view>
        </view>
        <text class="v">{{ item.is_encrypted ? '🔒' : '🔓' }} ›</text>
      </view>
      <view v-if="archiveList.length === 0" class="quiz-hint" style="margin-top: 6px">还没有历史档案，坚持打卡，她会替你收好每一段</view>

      <view class="cal-sec" style="margin-top: 14px">
        <text class="t">导出与分享</text>
        <text class="s">仅你可见</text>
      </view>
      <view class="focus-btns" style="margin-top: 0">
        <view class="fbtn ghost" @click="exportData('json')">导出 JSON</view>
        <view class="fbtn ghost" @click="exportData('csv')">导出 CSV</view>
      </view>
      <view class="focus-btns" style="margin-top: 8px">
        <view class="fbtn main" @click="shareReport">生成分享链接</view>
      </view>

      <view class="suggest" v-if="shareContent" style="margin-top: 10px">
        <view class="si"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="k">分享内容</view>
          <view class="m" style="line-height: 1.6">{{ shareContent }}</view>
        </view>
        <view class="add" @click="copyShareText">复制</view>
      </view>
      <view v-if="shareQrUrl" style="margin-top: 10px; text-align: center">
        <image class="share-qr-img" :src="shareQrUrl" mode="aspectFit"></image>
        <view class="quiz-hint" style="margin-top: 4px">扫码查看成长档案 · 链接 7 天内有效</view>
      </view>

      <view class="quiz-hint" style="margin: 12px 0 18px; text-align: center">
        你的数据已加密存储，仅你本人可查看。分享链接将在 7 天后自动失效。
      </view>
    </view>

    <view class="toast" :class="{ show: toastVisible }">{{ toastIcon }} {{ toastMsg }}</view>
  </view>
</template>

<script>
import archiveApi from '@/api/archive'
import statsApi from '@/api/stats'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      loading: false,
      selectedPeriod: 'monthly',
      periods: [
        { key: 'weekly', label: '周报', icon: '📅' },
        { key: 'monthly', label: '月报', icon: '🗓️' },
        { key: 'quarterly', label: '季报', icon: '📊' },
        { key: 'yearly', label: '年报', icon: '🏆' }
      ],
      currentReport: {},
      archiveList: [],
      // 近 30 天打卡数据，用于真实热力图
      monthData: [],
      shareContent: '',
      shareQrUrl: '',
      toastVisible: false,
      toastMsg: '',
      toastIcon: '✅',
      emotionNameMap: {
        happy: '开心',
        sad: '难过',
        anxious: '焦虑',
        angry: '愤怒',
        calm: '平静',
        excited: '兴奋',
        neutral: '一般',
        tired: '疲惫'
      },
      emotionColorMap: {
        happy: '#FFD93D',
        sad: '#5C6BC0',
        anxious: '#FF8A65',
        angry: '#EF5350',
        calm: '#66BB6A',
        excited: '#FF6B9D',
        neutral: '#BDBDBD',
        tired: '#8D6E63'
      }
    }
  },

  computed: {
    currentYear() {
      return new Date().getFullYear()
    },
    heatCells() {
      const rows = this.monthData || []
      if (!rows.length) return new Array(30).fill('')
      return rows.map(d => {
        if (!d || !d.completed) return ''
        const rate = Number(d.rate) || 0
        if (rate >= 80) return 'l4'
        if (rate >= 60) return 'l3'
        if (rate >= 30) return 'l2'
        return 'l1'
      })
    },
    periodLabel() {
      const p = this.periods.find(p => p.key === this.selectedPeriod)
      return p ? p.label : ''
    },
    highlights() {
      return this.currentReport.highlights || []
    },
    suggestions() {
      return this.currentReport.suggestions || []
    },
    emotionDistEntries() {
      const dist = this.currentReport.emotion_distribution || {}
      const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1
      return Object.entries(dist)
        .map(([emotion, count]) => ({
          emotion,
          count,
          percent: Math.round(count / total * 100)
        }))
        .sort((a, b) => b.count - a.count)
    },
    avgMeditationMin() {
      if (!this.currentReport.mindfulness_count || !this.currentReport.total_meditation_min) return 0
      return Math.round(this.currentReport.total_meditation_min / this.currentReport.mindfulness_count)
    },
    totalCheckins() {
      return this.currentReport.checkin_count || 0
    },
    totalMeditation() {
      return this.currentReport.mindfulness_count || 0
    }
  },

  onLoad() {
    this.loadReport()
    this.loadArchiveList()
    this.loadHeatmap()
  },

  methods: {
    async loadHeatmap() {
      try {
        const res = await statsApi.getMonthData()
        if (res && res.code === 200) this.monthData = res.data || []
      } catch (e) {
        console.error('加载打卡热力图失败', e)
      }
    },

    async refreshAll() {
      await Promise.all([this.loadReport(), this.loadArchiveList(), this.loadHeatmap()])
      this.showToast('已刷新', '🔄')
    },

    async loadReport() {
      this.loading = true
      try {
        const res = await archiveApi.getReport(this.selectedPeriod)
        if (res && res.code === 200) {
          this.currentReport = res.data || {}
        }
      } catch (e) {
        console.error('加载成长报告失败', e)
      } finally {
        this.loading = false
      }
    },

    async loadArchiveList() {
      try {
        const res = await archiveApi.getList()
        if (res && res.code === 200) {
          this.archiveList = res.data || []
        }
      } catch (e) {
        console.error('加载档案列表失败', e)
      }
    },

    switchPeriod(period) {
      if (this.selectedPeriod === period) return
      this.selectedPeriod = period
      this.shareContent = ''
      this.shareQrUrl = ''
      this.loadReport()
    },

    async exportData(format) {
      try {
        const res = await archiveApi.exportData(format)
        if (res && res.code === 200) {
          const content = res.data.content || ''
          const filename = res.data.filename || `export_${Date.now()}.${format}`
          // 复制到剪贴板
          // #ifdef H5
          if (navigator.clipboard) {
            await navigator.clipboard.writeText(content)
          }
          // #endif
          // #ifndef H5
          uni.setClipboardData({
            data: content,
            success: () => {}
          })
          // #endif
          this.showToast(`${format.toUpperCase()} 数据已复制到剪贴板`, '📋')
        }
      } catch (e) {
        console.error('导出失败', e)
        this.showToast('导出失败，请重试', '⚠️')
      }
    },

    async shareReport() {
      try {
        const res = await archiveApi.shareReport(this.selectedPeriod)
        if (res && res.code === 200) {
          this.shareContent = res.data.share_text || ''
          this.shareQrUrl = res.data.qr_code || ''
          this.showToast('分享链接已生成', '🔗')
        }
      } catch (e) {
        console.error('生成分享失败', e)
        this.showToast('生成分享失败', '⚠️')
      }
    },

    copyShareText() {
      if (!this.shareContent) return
      // #ifdef H5
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.shareContent)
      }
      // #endif
      // #ifndef H5
      uni.setClipboardData({
        data: this.shareContent,
        success: () => {}
      })
      // #endif
      this.showToast('已复制到剪贴板', '📋')
    },

    viewArchiveDetail(item) {
      // 切换到对应周期并加载
      if (item.period_type === 'weekly' || item.period_type === 'monthly' || item.period_type === 'quarterly' || item.period_type === 'yearly') {
        this.switchPeriod(item.period_type)
        // 滚动到顶部
        uni.pageScrollTo({ scrollTop: 0, duration: 300 })
      }
    },

    periodTypeLabel(type) {
      const map = { weekly: '周报', monthly: '月报', quarterly: '季报', yearly: '年报' }
      return map[type] || type
    },

    formatCreatedAt(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    showToast(msg, icon = '✅') {
      this.toastMsg = msg
      this.toastIcon = icon
      this.toastVisible = true
      setTimeout(() => {
        this.toastVisible = false
      }, 2000)
    }
  }
}
</script>

<style scoped>
/* i 元素选择器的等价 class（热力图 / 图例） */
.heat .hc {
  aspect-ratio: 1;
  border-radius: 3px;
  background: #F3F6F5;
}
.heat .hc.l1 { background: #DEE7E2; }
.heat .hc.l2 { background: #BBCDC4; }
.heat .hc.l3 { background: #90A99D; }
.heat .hc.l4 { background: var(--v7-green); }
.heat-legend .lg { width: 7px; height: 7px; border-radius: 2px; }

/* H5 下 img 尺寸不生效，uni-image 需显式宽高 */
.share-qr-img { width: 110px; height: 110px; border-radius: 10px; }
</style>
