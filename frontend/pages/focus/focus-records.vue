<template>
  <view class="xt-page xt-s51">
    <view class="body">
      <!-- 页头 -->
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">专注记录</view>
          <view class="chat-st">{{ periodLabel }}共 {{ filteredList.length }} 次坐下来</view>
        </view>
        <view class="icon-btn" @click="load"><xt-icon name="i-calendar" /></view>
      </view>

      <!-- 周期：本周 / 本月 / 全部（按 create_time 前端筛选） -->
      <view class="seg" style="margin: 11px 0">
        <span
          v-for="p in periods"
          :key="p.key"
          :class="{ on: period === p.key }"
          @click="period = p.key"
        >{{ p.label }}</span>
      </view>

      <!-- 搜索 -->
      <view class="search">
        <xt-icon name="i-search" />
        <input v-model="keyword" class="rec-input" placeholder="搜索任务关键词" @confirm="load" />
        <text class="rec-go" @click="load">搜索</text>
      </view>

      <!-- 记录时间轴 -->
      <view class="tl" v-if="filteredList.length">
        <view v-for="r in filteredList" :key="r.id" class="tl-item" @click="openDetail(r)">
          <view class="d">{{ r.create_time }}</view>
          <view class="t">{{ r.origin_prompt }} · {{ Math.round(r.duration_seconds / 60) }} 分钟</view>
          <view class="m">{{ r.mode === 'simple' ? '简单模式' : '心流模式' }} · {{ r.step_count }} 步 · 点开可回放</view>
          <view class="rec-ops">
            <text class="rec-del" @click.stop="removeRecord(r)">删除</text>
            <text class="rec-more">回放 ›</text>
          </view>
        </view>
      </view>

      <!-- 空态 -->
      <view class="mem-hero" v-if="!loading && !filteredList.length" style="margin-top: 12px; text-align: center">
        <view class="t">{{ list.length ? periodLabel + '还没有记录' : '还没有引导记录' }}</view>
        <view class="m">每次分步引导都会留在这里，可回放、可导出</view>
      </view>

      <!-- 底部说明 -->
      <view class="mem-hero" style="margin-top: 4px; display: flex; align-items: center; gap: 9px">
        <view class="mi tint-green" style="width: 28px; height: 28px; border-radius: 9px; display: flex; align-items: center; justify-content: center">
          <xt-icon name="i-book" />
        </view>
        <view>
          <view class="t" style="font-size: 8.5px">这些记录会被写进你的成长档案</view>
          <view class="m">月底她会整理成一封信给你</view>
        </view>
      </view>

      <view style="height: 18px"></view>
    </view>

    <!-- 回放 / 导出弹层 -->
    <view v-if="detail" class="rec-mask" @click="detail = null">
      <view class="rec-sheet" @click.stop>
        <view class="rec-grip"></view>
        <text class="rec-kicker">专注回放</text>
        <text class="rec-title">{{ detail.origin_prompt }}</text>
        <text class="rec-meta">{{ detail.mode === 'simple' ? '简单' : '心流' }}模式 · 全程 {{ Math.round(detail.duration_seconds / 60) }} 分钟 · {{ detail.create_time }}</text>
        <scroll-view class="rec-steps" scroll-y>
          <view v-for="(s, i) in detail.steps" :key="i" class="rec-step">
            <text class="rec-idx">{{ i + 1 }}</text>
            <text class="rec-content">{{ s.content }}（约 {{ s.minutes }} 分钟）</text>
          </view>
        </scroll-view>
        <view class="rec-btns">
          <view class="auth-btn" style="flex: 1; margin-top: 0" @click="exportText">
            <text>导出文本</text>
          </view>
          <view class="rec-close" @click="detail = null">
            <text>关闭</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 引导记录列表 / 回放 / 导出
 * -------------------------------
 * - 列表支持关键词搜索（POST 存的 origin_prompt like 查询）
 * - 点击记录弹出回放：完整步骤 + 全程计时
 * - 导出：把 export_text 复制到剪贴板（uni.setClipboardData，多端可用）
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      keyword: '',
      period: 'week',
      periods: [
        { key: 'week', label: '本周' },
        { key: 'month', label: '本月' },
        { key: 'all', label: '全部' }
      ],
      list: [],
      loading: false,
      detail: null
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    periodLabel() {
      const p = this.periods.find(x => x.key === this.period)
      return this.period === 'all' || !p ? '' : p.label
    },
    // 周期筛选：create_time 形如 "2026-11-15 12:00:00"，按日期前缀比较即可
    filteredList() {
      const list = this.list || []
      if (this.period === 'all') return list
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      if (this.period === 'week') {
        // 周一为一周起点
        start.setDate(start.getDate() - ((start.getDay() + 6) % 7))
      } else {
        start.setDate(1)
      }
      const startKey = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}`
      return list.filter(r => String(r.create_time || '').slice(0, 10) >= startKey)
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() { this.load() },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await focusApi.getRecords(this.keyword)
        if (res && res.code === 200) this.list = res.data.list || []
      } catch (e) { /* noop */ } finally { this.loading = false }
    },
    async openDetail(r) {
      try {
        const res = await focusApi.getRecordDetail(r.id)
        if (res && res.code === 200) this.detail = res.data
      } catch (e) { /* noop */ }
    },
    exportText() {
      if (!this.detail || !this.detail.export_text) return
      uni.setClipboardData({
        data: this.detail.export_text,
        success: () => uni.showToast({ title: '已复制，可粘贴导出', icon: 'none' })
      })
    },
    removeRecord(r) {
      uni.showModal({
        title: '删除记录', content: '确定删除这条引导记录吗？',
        success: async (m) => {
          if (!m.confirm) return
          await focusApi.deleteRecord(r.id).catch(() => {})
          this.load()
        }
      })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 记录较多时在内容区滚动 */
.xt-page.xt-s51 .body {
  overflow-y: auto;
  padding-bottom: 18px;
}
.xt-page.xt-s51 .chat-head {
  padding-top: 8px;
}

/* 搜索行 */
.xt-page.xt-s51 .rec-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 9.5px;
  color: #22302A;
  background: transparent;
}
.xt-page.xt-s51 .rec-go {
  flex-shrink: 0;
  font-size: 8.5px;
  font-weight: 900;
  color: var(--v7-green);
}

/* 时间轴操作行 */
.xt-page.xt-s51 .rec-ops {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
}
.xt-page.xt-s51 .rec-del {
  font-size: 7px;
  color: #B57F4C;
}
.xt-page.xt-s51 .rec-more {
  font-size: 7px;
  font-weight: 800;
  color: #6E9B81;
}

/* 回放弹层 */
.xt-page.xt-s51 .rec-mask {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  background: rgba(34, 48, 42, 0.42);
}
.xt-page.xt-s51 .rec-sheet {
  width: 100%;
  max-height: 78%;
  padding: 15px;
  border-radius: 20px;
  background: var(--v7-card);
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 48px -24px rgba(34, 48, 42, 0.5);
}
.xt-page.xt-s51 .rec-grip {
  width: 36px;
  height: 4px;
  margin: 0 auto;
  border-radius: 999px;
  background: var(--v7-line);
}
.xt-page.xt-s51 .rec-kicker {
  display: block;
  margin-top: 11px;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 1.6px;
  color: #AEB6AE;
}
.xt-page.xt-s51 .rec-title {
  display: block;
  margin-top: 5px;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.45;
  color: #22302A;
}
.xt-page.xt-s51 .rec-meta {
  display: block;
  margin-top: 5px;
  font-size: 7.5px;
  color: #AEB6AE;
}
.xt-page.xt-s51 .rec-steps {
  margin-top: 10px;
  max-height: 46vh;
}
.xt-page.xt-s51 .rec-step {
  display: flex;
  align-items: flex-start;
  padding: 8px 0;
  border-top: 1px solid var(--v7-line);
}
.xt-page.xt-s51 .rec-step:first-child {
  border-top: none;
}
.xt-page.xt-s51 .rec-idx {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(156, 191, 170, 0.2);
  color: var(--v7-green);
  font-size: 7.5px;
  font-weight: 900;
  text-align: center;
  line-height: 18px;
}
.xt-page.xt-s51 .rec-content {
  flex: 1;
  margin-left: 8px;
  font-size: 9px;
  line-height: 1.65;
  color: #4B5A51;
}
.xt-page.xt-s51 .rec-btns {
  display: flex;
  align-items: center;
  margin-top: 13px;
}
.xt-page.xt-s51 .rec-close {
  flex: 0 0 32%;
  margin-left: 8px;
  padding: 13px 0;
  border-radius: 999px;
  text-align: center;
  font-size: 11px;
  font-weight: 900;
  color: #6A776E;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
</style>
