<template>
  <view class="xt-page xt-s17">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">消息通知</view>
          <view class="page-sub">{{ unreadCount }} 条未读 · 她都替你收好了</view>
        </view>
        <view class="icon-btn" @click="readAll"><xt-icon name="i-check" /></view>
      </view>

      <!-- 类型筛选 -->
      <view class="chips" style="margin: 0 0 2px">
        <view class="chip" :class="{ on: filter === '' }" @click="setFilter('')">全部</view>
        <view class="chip" :class="{ on: filter === 'checkin_remind' }" @click="setFilter('checkin_remind')">提醒</view>
        <view class="chip" :class="{ on: filter === 'todo_due' }" @click="setFilter('todo_due')">待办</view>
        <view class="chip" :class="{ on: filter === 'ai_companion' }" @click="setFilter('ai_companion')">伙伴</view>
      </view>

      <!-- 今天 / 更早 -->
      <template v-for="g in recordGroups" :key="g.label">
        <view class="n-group-t" v-if="g.list.length">{{ g.label }}</view>
        <view class="notice" v-for="r in g.list" :key="r.id" @click="onTapRecord(r)">
          <view class="ni" :class="typeTints[r.push_type] || 'tint-sand'">
            <xt-icon :name="typeIcons[r.push_type] || 'i-bell'" />
          </view>
          <view class="tx">
            <view class="t">{{ r.title }}</view>
            <view class="m">{{ r.content }}</view>
            <view class="tm">
              {{ typeMeta(r.push_type).name }} · {{ r.created_at }}
              <text v-if="r.jump_page"> · 查看详情 ›</text>
            </view>
          </view>
          <view class="unread" v-if="!r.is_read"></view>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="mem-item" v-if="records.length === 0" style="margin-top: 12px">
        <view class="mi tint-sand"><xt-icon name="i-bell" /></view>
        <view class="tx">
          <view class="t">暂无通知</view>
          <view class="m">推送记录会保存在这里，点击可跳转对应页面</view>
        </view>
      </view>

      <view class="ntf-foot">少一条推送，多一点想念。</view>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】消息通知中心：保存全部推送记录，点击跳转对应页面
 * 纯新增页面，不改动任何既有页面逻辑
 */
import api from '@/api/newfunc'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const TYPE_META = {
  checkin_remind: { icon: '✅', name: '打卡提醒' },
  todo_due: { icon: '⏰', name: '待办到期' },
  ai_companion: { icon: '💚', name: 'AI陪伴' },
  test: { icon: '🧪', name: '测试' }
}

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      records: [],
      unread: 0,
      filter: '',
      page: 1,
      total: 0
    }
  },
  computed: {
    typeIcons() {
      return {
        checkin_remind: 'i-clock',
        todo_due: 'i-calendar',
        ai_companion: 'i-heart',
        test: 'i-spark'
      }
    },
    typeTints() {
      return {
        checkin_remind: 'tint-green',
        todo_due: 'tint-peach',
        ai_companion: 'tint-peach',
        test: 'tint-blue'
      }
    },
    unreadCount() {
      return this.unread || this.records.filter(r => !r.is_read).length
    },
    /** 按「今天 / 更早」分组，仅用于展示 */
    recordGroups() {
      const now = new Date()
      const isToday = (v) => {
        if (!v) return false
        const d = typeof v === 'number'
          ? new Date(v)
          : new Date(String(v).replace('T', ' ').replace(/-/g, '/'))
        if (isNaN(d.getTime())) return false
        return d.getFullYear() === now.getFullYear() &&
          d.getMonth() === now.getMonth() &&
          d.getDate() === now.getDate()
      }
      return [
        { label: '今天', list: this.records.filter(r => isToday(r.created_at)) },
        { label: '更早', list: this.records.filter(r => !isToday(r.created_at)) }
      ]
    }
  },
  onShow() {
    this.load()
  },
  onReachBottom() {
    if (this.records.length < this.total) {
      this.page += 1
      this.load(true)
    }
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    typeMeta(t) {
      return TYPE_META[t] || { icon: '📩', name: '通知' }
    },
    setFilter(f) {
      this.filter = f
      this.page = 1
      this.records = []
      this.load()
    },
    async load(append = false) {
      try {
        const res = await api.pushRecords({
          type: this.filter, page: this.page, size: 20
        })
        const data = res.data || {}
        this.total = data.total || 0
        this.unread = data.unread || 0
        this.records = append ? this.records.concat(data.list || []) : (data.list || [])
      } catch (e) {
        if (!append) this.records = []
      }
    },
    async onTapRecord(r) {
      if (!r.is_read) {
        try { await api.pushRead(r.id) } catch (e) { /* 静默 */ }
        r.is_read = 1
      }
      if (r.jump_page) {
        uni.navigateTo({
          url: r.jump_page,
          fail: () => uni.showToast({ title: '页面不可达', icon: 'none' })
        })
      }
    },
    async readAll() {
      try {
        await api.pushReadAll()
        this.records.forEach(r => { r.is_read = 1 })
        uni.showToast({ title: '已全部标为已读', icon: 'success' })
      } catch (e) { /* request 层已提示 */ }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 通知列表可能分页，改为整页滚动以保留 onReachBottom 触底加载 */
.xt-page.xt-s17 { height: auto; min-height: 100vh; overflow: visible; }
.xt-page.xt-s17 .body {
  overflow: visible;
  padding-bottom: calc(28px + env(safe-area-inset-bottom));
}
.xt-page.xt-s17 .notice { align-items: flex-start; }
.xt-page.xt-s17 .notice .tx { padding-right: 8px; }
.xt-page.xt-s17 .notice .t { display: block; line-height: 1.4; }
.xt-page.xt-s17 .notice .tm { display: block; margin-top: 3px; }
.xt-page.xt-s17 .ntf-foot {
  margin-top: 14px; text-align: center;
  font-size: 8px; color: #BFC7BF; letter-spacing: .4px;
}
</style>
