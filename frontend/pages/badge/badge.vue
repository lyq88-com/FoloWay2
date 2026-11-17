<template>
  <view class="xt-page xt-s28">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">我的徽章</view>
          <view class="page-sub">{{ unlockedCount }} 枚已获得 · 还有 {{ badges.length - unlockedCount }} 枚在路上</view>
        </view>
        <view class="icon-btn" @click="goGrowthArchive"><xt-icon name="i-archive" /></view>
      </view>

      <view class="badge-grid2">
        <view
          v-for="b in displayBadges"
          :key="b.id"
          class="bdg"
          :class="{ lock: !b.unlocked }"
          @click="showDetail(b)"
        >
          <view class="disc"><xt-icon :name="b.ic" /></view>
          <view class="n">{{ b.name }}</view>
          <view class="d">{{ b.description }}</view>
        </view>
      </view>

      <view v-if="!loading && !badges.length" class="mem-item" style="margin-top:11px">
        <view class="mi tint-peach"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">还没有徽章</view>
          <view class="m">先去完成一次打卡，第一束光就会亮起来。</view>
        </view>
      </view>
      <view v-else class="mem-item" style="margin-top:11px">
        <view class="mi tint-peach"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">{{ nextBadge ? '下一个：' + nextBadge.name : '全部徽章都拿到了' }}</view>
          <view class="m">{{ nextBadge ? nextBadge.description : '她替你把每一枚都收好了。' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 我的徽章（全量页）
 * - 数据：GET /api/v1/badges/my（后端按打卡/正念/情绪记录数实时计算，无需建表）
 * - 入口：profile 页「我的徽章 → 全部 ›」（原来是 showToast「徽章页面开发中」）
 */
import userApi from '@/api/user'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const BADGE_ICONS = {
  first_checkin: 'i-focus',
  streak_7: 'i-moon',
  streak_30: 'i-spark',
  all_done: 'i-heart',
  checkin_100: 'i-archive'
}
const FALLBACK_ICONS = ['i-moon', 'i-book', 'i-water', 'i-heart', 'i-world', 'i-spark', 'i-clock', 'i-focus', 'i-archive']

export default {
  components: { XtIcon },
  data() {
    return {
      badges: [],
      loading: false
    }
  },
  computed: {
    unlockedList() {
      return this.badges.filter(b => b.unlocked)
    },
    lockedList() {
      return this.badges.filter(b => !b.unlocked)
    },
    unlockedCount() {
      return this.unlockedList.length
    },
    progressPercent() {
      if (!this.badges.length) return 0
      return Math.round(this.unlockedCount / this.badges.length * 100)
    },
    nextTip() {
      const next = this.lockedList[0]
      return next ? `下一个：${next.name} · ${next.description}` : '全部徽章都拿到了，厉害！'
    },
    nextBadge() {
      return this.lockedList[0] || null
    },
    displayBadges() {
      return [...this.unlockedList, ...this.lockedList].map((b, i) => ({
        ...b,
        ic: BADGE_ICONS[b.code] || FALLBACK_ICONS[i % FALLBACK_ICONS.length]
      }))
    }
  },
  onLoad() {
    this.loadBadges()
  },
  onPullDownRefresh() {
    this.loadBadges().then(() => uni.stopPullDownRefresh())
  },
  methods: {
    goGrowthArchive() {
      uni.navigateTo({ url: '/pages/growth-archive/growth-archive' })
    },
    async loadBadges() {
      this.loading = true
      try {
        const res = await userApi.getBadges()
        if (res && res.code === 200) {
          this.badges = res.data || []
        }
      } catch (e) {
        uni.showToast({ title: '徽章加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    showDetail(badge) {
      if (!badge) return
      const status = badge.unlocked ? '已解锁' : '未解锁'
      uni.showModal({
        title: `${badge.icon} ${badge.name}`,
        content: `${badge.description}\n${status}`,
        showCancel: false,
        confirmText: '知道了'
      })
    }
  }
}
</script>
