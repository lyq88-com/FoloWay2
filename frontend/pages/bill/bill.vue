<template>
  <view class="xt-page xt-s35">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">金币账单</view>
          <view class="page-sub">{{ monthLabel }}</view>
        </view>
        <picker mode="date" fields="month" :value="viewMonth" @change="onMonthChange">
          <view class="icon-btn">
            <xt-icon name="i-calendar" />
          </view>
        </picker>
      </view>

      <view class="wallet">
        <view class="k">BALANCE</view>
        <view class="vrow">
          <text class="v">{{ balanceText }}</text>
          <text class="u">金币</text>
        </view>
        <view class="sub">本月收入 +{{ monthSummary.income }} · 支出 -{{ monthSummary.expense }}</view>
        <view class="earn" @click="goMall">赚金币</view>
      </view>

      <view class="chips">
        <text class="chip" :class="{ on: filterType === 'all' }" @click="filterType = 'all'">全部</text>
        <text class="chip" :class="{ on: filterType === 'income' }" @click="filterType = 'income'">收入</text>
        <text class="chip" :class="{ on: filterType === 'expense' }" @click="filterType = 'expense'">支出</text>
      </view>

      <view v-for="(g, gi) in groups" :key="g.key">
        <view class="cal-sec" :style="gi > 0 ? 'margin-top:10px' : ''">
          <text class="t">{{ g.label }}</text>
          <text class="s">{{ g.summary }}</text>
        </view>
        <view v-for="(bill, idx) in g.items" :key="idx" class="set-row">
          <view class="si" :class="bill.tint">
            <xt-icon :name="bill.icon" />
          </view>
          <view class="tx">
            <view class="t">{{ bill.desc || sourceLabel(bill.source) }}</view>
            <view class="m">{{ (bill.time || '').slice(11, 16) }} · {{ sourceLabel(bill.source) }}</view>
          </view>
          <text class="v" :style="{ color: bill.color }">{{ bill.sign }}{{ bill.amount }}</text>
        </view>
      </view>

      <view v-if="groups.length === 0" class="mem-hero">
        <view class="t">暂无账单记录</view>
        <view class="m">完成打卡、赠送礼物后这里会出现明细</view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 虚拟货币账单：完整的收入、支出明细记录
 */
import economy from '@/common/economy'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const SOURCE_LABELS = {
  checkin: '打卡奖励',
  gift_drop: '礼物掉落',
  gacha_ticket: '扭蛋券',
  welcome: '系统发放',
  mall: '商城购物',
  gift: '赠送礼物',
  gacha: '扭蛋抽奖',
  treasure_gift: '宝物赠送',
  task: '任务奖励'
}

// 设计稿流水图标与底色：[图标, 底色 class]
const BILL_META = {
  checkin: ['i-check', 'tint-green'],
  task: ['i-check', 'tint-green'],
  welcome: ['i-spark', 'tint-green'],
  gift_drop: ['i-heart', 'tint-peach'],
  mall: ['i-heart', 'tint-peach'],
  gift: ['i-heart', 'tint-sand'],
  treasure_gift: ['i-archive', 'tint-sand'],
  gacha: ['i-gacha', 'tint-purple'],
  gacha_ticket: ['i-gacha', 'tint-blue']
}

function pad2(n) {
  return String(n).padStart(2, '0')
}

function dayKey(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function dayLabel(key) {
  if (!key) return ''
  const now = new Date()
  if (key === dayKey(now)) return '今天'
  if (key === dayKey(new Date(now.getTime() - 86400000))) return '昨天'
  return key.slice(5).replace('-', '/')
}

export default {
  components: { XtIcon },
  data() {
    return {
      bills: [],
      filterType: 'all',
      viewMonth: ''   // YYYY-MM，右上角日历用于切换查看月份
    }
  },
  computed: {
    summary() {
      // 依赖 bills，避免 computed 缓存导致余额不刷新
      this.bills
      return economy.getSummary()
    },
    filteredBills() {
      const list = [...this.bills].reverse()
        .filter(b => !this.viewMonth || String(b.time || '').slice(0, 7) === this.viewMonth)
      if (this.filterType === 'all') return list
      return list.filter(b => b.type === this.filterType)
    },
    // 按日期分组，并给出当日收支小结（设计稿的「今天 / 昨天」分组）
    groups() {
      const map = {}
      const order = []
      this.filteredBills.forEach(b => {
        const key = String(b.time || '').slice(0, 10)
        if (!map[key]) {
          map[key] = { key, label: dayLabel(key), income: 0, expense: 0, items: [], summary: '' }
          order.push(key)
        }
        const g = map[key]
        if (b.type === 'income') g.income += b.amount
        else g.expense += b.amount
        const meta = BILL_META[b.source] || (b.type === 'income' ? ['i-spark', 'tint-green'] : ['i-archive', 'tint-sand'])
        g.items.push(Object.assign({}, b, {
          icon: meta[0],
          tint: meta[1],
          sign: b.type === 'income' ? '+' : '-',
          color: b.type === 'income' ? '#24493A' : '#C08A56'
        }))
      })
      return order.map(k => {
        const g = map[k]
        if (g.income && g.expense) g.summary = `+${g.income} / -${g.expense}`
        else if (g.income) g.summary = `+${g.income}`
        else if (g.expense) g.summary = `-${g.expense}`
        return g
      })
    },
    monthLabel() {
      const d = new Date()
      if (!this.viewMonth) return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`
      const [y, m] = this.viewMonth.split('-')
      return `${y} 年 ${Number(m)} 月`
    },
    monthSummary() {
      const prefix = this.viewMonth || `${new Date().getFullYear()}-${pad2(new Date().getMonth() + 1)}`
      let income = 0
      let expense = 0
      this.bills.forEach(b => {
        if (String(b.time || '').slice(0, 7) !== prefix) return
        if (b.type === 'income') income += b.amount
        else expense += b.amount
      })
      return { income, expense }
    },
    balanceText() {
      return Number(this.summary.balance || 0).toLocaleString('en-US')
    }
  },
  onShow() {
    this.bills = economy.getBills()
    if (!this.viewMonth) {
      const d = new Date()
      this.viewMonth = `${d.getFullYear()}-${pad2(d.getMonth() + 1)}`
    }
    uni.$on('economy-updated', this.refresh)
  },
  onHide() {
    uni.$off('economy-updated', this.refresh)
  },
  onUnload() {
    uni.$off('economy-updated', this.refresh)
  },
  methods: {
    onMonthChange(e) {
      this.viewMonth = e.detail.value
    },
    refresh() {
      this.bills = economy.getBills()
    },
    sourceLabel(source) {
      return SOURCE_LABELS[source] || source || '其他'
    },
    billIcon(bill) {
      if (bill.source === 'checkin') return '✅'
      if (bill.source === 'gift' || bill.source === 'treasure_gift') return '🎁'
      if (bill.source === 'mall') return '🛍️'
      if (bill.source === 'gacha' || bill.source === 'gacha_ticket') return '🎰'
      if (bill.source === 'gift_drop') return '🎈'
      if (bill.source === 'welcome') return '🎉'
      return bill.type === 'income' ? '💰' : '💳'
    },
    goMall() {
      uni.navigateTo({ url: '/pages/mall/mall' })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 流水较多时在内容区滚动 */
.xt-page.xt-s35 .body {
  overflow-y: auto;
}
</style>
