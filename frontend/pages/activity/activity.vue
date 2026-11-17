<template>
  <view class="xt-page xt-s44">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">心流天地</view>
          <view class="page-sub">挑一件此刻做得动的小事</view>
        </view>
        <view class="icon-btn" @click="doSignin">
          <xt-icon name="i-clock" />
        </view>
      </view>

      <view class="pills">
        <view class="pill">
          <view style="font-size: 8px; font-weight: 900">现在</view>
          <view style="font-size: 6.5px; color: #AEB6AE; margin-top: 2px">{{ signin.signed_today ? '今天已签到' : '今天还没签到' }}</view>
        </view>
        <view class="pill">
          <view style="font-size: 8px; font-weight: 900">{{ signin.total_days }} 天</view>
          <view style="font-size: 6.5px; color: #AEB6AE; margin-top: 2px">累计签到</view>
        </view>
        <view class="pill">
          <view style="font-size: 8px; font-weight: 900; color: var(--v7-green)">{{ signin.streak }} 天</view>
          <view style="font-size: 6.5px; color: #AEB6AE; margin-top: 2px">连续签到</view>
        </view>
      </view>

      <view class="cal-sec">
        <span class="t">15 分钟就能做完</span>
        <span class="s">不用准备</span>
      </view>

      <view
        v-for="(t, i) in tasks"
        :key="t.id"
        class="event-card"
        :class="{ done: t.done }"
        style="margin: 0 0 8px"
      >
        <span class="ev-ic" :class="['', 'tint-peach', 'tint-blue'][i % 3]"><xt-icon name="i-focus" /></span>
        <span class="ev-tx">
          <span class="ev-t">{{ t.name }}</span>
          <span class="ev-m">{{ t.description }} · {{ Math.min(t.current, t.target) }}/{{ t.target }}</span>
        </span>
        <span class="ev-ok" style="font-weight: 900; font-size: 8px; color: var(--v7-green)">{{ t.done ? '已完成' : '+' + t.reward }}</span>
      </view>

      <view class="event-card" style="margin: 0 0 8px" @click="goIdea">
        <span class="ev-ic tint-green"><xt-icon name="i-spark" /></span>
        <span class="ev-tx">
          <span class="ev-t">写下一个小想法，遇见同频的人</span>
          <span class="ev-m">3 分钟 · 她会认真读</span>
        </span>
        <span class="ev-ok" style="font-weight: 900; font-size: 8px; color: var(--v7-green)">去写</span>
      </view>

      <view class="cal-sec" style="margin-top: 13px">
        <span class="t">有人正在做</span>
        <span class="s">可以加入</span>
      </view>

      <view class="wcard">
        <span class="wcover tint-green"><xt-icon name="i-moon" /></span>
        <span class="tx">
          <span class="n">深夜写作局 · 23:00</span>
          <span class="m">6 人 · 安静模式 · 只剩键盘声</span>
        </span>
        <span class="ar"><xt-icon name="i-right" /></span>
      </view>
      <view class="wcard">
        <span class="wcover tint-peach"><xt-icon name="i-calendar" /></span>
        <span class="tx">
          <span class="n">早起共读 · 07:30</span>
          <span class="m">18 人 · 每天 · 可只看不回</span>
        </span>
        <span class="ar"><xt-icon name="i-right" /></span>
      </view>
      <view class="wcard">
        <span class="wcover tint-blue"><xt-icon name="i-focus" /></span>
        <span class="tx">
          <span class="n">一起把事做完 · 随时</span>
          <span class="m">42 人 · 25 分钟一轮 · 番茄钟</span>
        </span>
        <span class="ar"><xt-icon name="i-right" /></span>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 心愿岛页（原「小活动」，2026-11-09 改名并内置小想法共鸣匹配入口）
 *
 * 【2026-10-27 改造】原来只有一句「功能建设中 · 敬请期待」。
 * 现在提供两块真实内容：
 *   1) 每日签到 —— 后端 /activity/signin 按自然日判定，重复点不会重复发奖；
 *      奖励金币由前端 economy.addCoins() 入账，与商城/账单共用同一套账本
 *   2) 活跃任务 —— /activity/tasks 只读统计（打卡/正念/情绪记录），展示进度
 */
import activityApi from '@/api/activity'
import economy from '@/common/economy'

const WEEK_LABELS = ['日', '一', '二', '三', '四', '五', '六']

export default {
  data() {
    return {
      statusBarHeight: 20,
      signin: {
        signed_today: false,
        last_date: '',
        streak: 0,
        max_streak: 0,
        total_days: 0,
        today_reward: 10
      },
      tasks: [],
      loading: false,
      signing: false
    }
  },
  computed: {
    navBodyTop() {
      return this.statusBarHeight + 44
    },
    /** 最近 7 天的签到状态：从 last_date 往前推 streak 天 */
    weekDays() {
      const doneMap = {}
      const last = this.signin.last_date ? new Date(this.signin.last_date) : null
      const streak = this.signin.streak || 0
      if (last && !isNaN(last.getTime()) && streak > 0) {
        for (let i = 0; i < streak; i++) {
          const d = new Date(last)
          d.setDate(d.getDate() - i)
          doneMap[d.toDateString()] = true
        }
      }
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const out = []
      for (let i = 6; i >= 0; i--) {
        const d = new Date(today)
        d.setDate(d.getDate() - i)
        out.push({
          label: WEEK_LABELS[d.getDay()],
          done: !!doneMap[d.toDateString()],
          isToday: i === 0
        })
      }
      return out
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() {
    this.loadAll()
  },
  onPullDownRefresh() {
    this.loadAll().then(() => uni.stopPullDownRefresh())
  },
  methods: {
    async loadAll() {
      this.loading = true
      try {
        await Promise.all([this.loadSignin(), this.loadTasks()])
      } finally {
        this.loading = false
      }
    },
    async loadSignin() {
      try {
        const res = await activityApi.getSignin()
        if (res && res.code === 200 && res.data) {
          this.signin = Object.assign({}, this.signin, res.data)
        }
      } catch (e) { /* 静默：保留默认值 */ }
    },
    async loadTasks() {
      try {
        const res = await activityApi.getTasks()
        if (res && res.code === 200 && res.data) {
          this.tasks = res.data.list || []
        }
      } catch (e) { /* 静默 */ }
    },
    async doSignin() {
      if (this.signin.signed_today || this.signing) return
      this.signing = true
      try {
        const res = await activityApi.signin()
        const data = (res && res.data) || {}
        if (res && res.code === 200 && data.signed) {
          const reward = data.reward || 0
          if (reward > 0) {
            economy.addCoins(reward, 'signin', `每日签到（连续${data.streak}天）`)
          }
          uni.showToast({ title: `签到成功 +${reward} 金币`, icon: 'none', duration: 2000 })
        } else {
          uni.showToast({ title: data.message || '今天已经签到过了', icon: 'none', duration: 2000 })
        }
        await this.loadSignin()
      } catch (e) {
        uni.showToast({ title: '签到失败，请稍后再试', icon: 'none' })
      } finally {
        this.signing = false
      }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    /* 心愿玩法：进入小想法模块（独立 idea 模块，不侵入既有业务） */
    goIdea() {
      uni.navigateTo({ url: '/pages/idea/idea-landing' })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿里 .ev-t/.ev-m 为内联 span，补块级排列 */
.xt-page.xt-s44 .event-card .ev-t,
.xt-page.xt-s44 .event-card .ev-m {
  display: block;
}
.xt-page.xt-s44 .wcard .ar {
  color: #cfd6ce;
}
.xt-page.xt-s44 .wcard .ar .ic {
  width: 12px;
  height: 12px;
}
</style>
