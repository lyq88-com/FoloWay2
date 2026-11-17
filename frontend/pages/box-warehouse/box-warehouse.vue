<template>
  <view class="xt-page xt-s36">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">我的仓库</view>
          <view class="page-sub">{{ warehouse.length }} 件小东西 · 都能送给她</view>
        </view>
        <view class="icon-btn" @click="toggleSearch"><xt-icon name="i-search" /></view>
      </view>

      <!-- 搜索 -->
      <view v-if="showSearch" style="margin-bottom:10px">
        <input
          v-model="keyword"
          :focus="showSearch"
          placeholder="搜索道具名称"
          placeholder-style="color:#BFC7BF"
          style="height:36px;padding:0 12px;border-radius:12px;background:#FFFDFA;border:1px solid rgba(30,42,36,.10);font-size:9px;color:#22302A"
        />
      </view>

      <view class="chips" style="margin:0 0 10px">
        <text
          v-for="tab in tabs"
          :key="tab.key"
          class="chip"
          :class="{ on: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.name }}</text>
      </view>

      <view v-if="displayRewards.length" class="vault-grid">
        <view
          v-for="item in displayRewards"
          :key="item.type + '|' + item.value"
          class="vitem"
          @click="showRewardDetail(item)"
        >
          <view class="box2" :class="item.tint">
            <xt-icon :name="item.ic" />
          </view>
          <view class="n">{{ item.name }}</view>
          <view class="c">{{ item.isUsed ? '已使用' : '× ' + item.count }}</view>
        </view>
      </view>
      <view v-else class="mem-hero" @click="goToBox">
        <view class="t">暂无{{ activeTabName }}道具</view>
        <view class="m">去开一次盲盒，把小东西都收进来 ›</view>
      </view>

      <view class="cal-sec" style="margin-top:13px">
        <text class="t">可赠送</text>
        <text class="s">她会记得</text>
      </view>

      <view v-for="(g, gi) in giftables" :key="'gift-' + gi" class="mem-item">
        <view class="mi" :class="g.tint"><xt-icon :name="g.ic" /></view>
        <view class="tx">
          <view class="t">{{ g.name }} · {{ g.count }} 个</view>
          <view class="m">{{ g.description || '送给她，她会记得这份心意。' }}</view>
          <view class="d">赠送后提升好感度 +8</view>
        </view>
        <text v-if="gi === 0" class="v" style="font-size:8px;color:var(--v7-green)" @click.stop="giftToAI(g)">送出</text>
      </view>
      <view v-if="!giftables.length" class="mem-item">
        <view class="mi tint-peach"><xt-icon name="i-heart" /></view>
        <view class="tx">
          <view class="t">暂无可赠送的小东西</view>
          <view class="m">去仓库里挑一件，或开盲盒看看。</view>
        </view>
      </view>
    </view>

    <view v-if="selectedReward" class="detail-modal" @click="closeDetail">
      <view class="detail-content" @click.stop>
        <view class="detail-handle"></view>
        <view class="detail-icon">{{ selectedReward.emoji }}</view>
        <text class="detail-title">{{ selectedReward.name }}</text>
        <text class="detail-desc">{{ selectedReward.description }}</text>
        <text class="detail-date">获得时间：{{ formatDate(selectedReward.date) }}</text>
        <view class="detail-actions">
          <view v-if="!selectedReward.isUsed" class="action-btn primary" @click="useReward(selectedReward)">
            <text>使用</text>
          </view>
          <view v-if="!selectedReward.isUsed" class="action-btn gift" @click="giftToAI(selectedReward)">
            <text>送给TA 💜</text>
          </view>
          <view class="action-btn" @click="closeDetail">
            <text>关闭</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { applyTheme } from '@/common/theme'
import economy from '@/common/economy'
import aiSocial from '@/common/ai-social'
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const WAREHOUSE_KEY = 'box_warehouse'

// 设计稿图标 / 底色与道具类型的对应关系
const WAREHOUSE_META = {
  theme: ['i-spark', 'tint-purple'],
  bg: ['i-world', 'tint-blue'],
  avatar: ['i-moon', 'tint-green'],
  quote: ['i-book', 'tint-peach']
}

export default {
  components: { XtIcon },
  data() {
    return {
      activeTab: 'all',
      tabs: [
        { key: 'all', name: '全部', icon: '📦' },
        { key: 'theme', name: '主题', icon: '🎨' },
        { key: 'bg', name: '背景', icon: '🖼️' },
        { key: 'avatar', name: '装饰', icon: '🎩' },
        { key: 'quote', name: '语录', icon: '💬' }
      ],
      warehouse: [],
      selectedReward: null,
      showSearch: false,
      keyword: ''
    }
  },
  computed: {
    filteredRewards() {
      if (this.activeTab === 'all') return this.warehouse
      return this.warehouse.filter(item => item.type === this.activeTab)
    },
    activeTabName() {
      const tab = this.tabs.find(t => t.key === this.activeTab)
      return tab ? tab.name : ''
    },
    uniqueRewards() {
      const counts = {}
      this.warehouse.forEach(w => {
        const k = `${w.type}|${w.value}`
        counts[k] = (counts[k] || 0) + 1
      })
      const seen = {}
      const list = []
      this.warehouse.forEach(item => {
        const k = `${item.type}|${item.value}`
        if (seen[k]) return
        seen[k] = true
        const meta = WAREHOUSE_META[item.type] || ['i-spark', 'tint-green']
        list.push({ ...item, ic: meta[0], tint: meta[1], count: counts[k] })
      })
      return list
    },
    displayRewards() {
      let list = this.uniqueRewards
      if (this.activeTab !== 'all') list = list.filter(item => item.type === this.activeTab)
      const k = this.keyword.trim()
      if (k) list = list.filter(item => (item.name || '').includes(k))
      return list
    },
    giftables() {
      return this.uniqueRewards.filter(item => !item.isUsed).slice(0, 2)
    }
  },
  onShow() {
    this.loadWarehouse()
    // 仓库与盲盒共用同一份云端数据
    playSync.pullKey('box').then(ok => {
      if (ok) this.loadWarehouse()
    })
  },
  methods: {
    toggleSearch() {
      this.showSearch = !this.showSearch
      if (!this.showSearch) this.keyword = ''
    },
    loadWarehouse() {
      try {
        this.warehouse = uni.getStorageSync(WAREHOUSE_KEY) || []
      } catch (e) {
        console.error('加载仓库失败', e)
        this.warehouse = []
      }
    },
    getTabCount(key) {
      if (key === 'all') return this.warehouse.length
      return this.warehouse.filter(item => item.type === key).length
    },
    showRewardDetail(item) {
      this.selectedReward = item
    },
    closeDetail() {
      this.selectedReward = null
    },
    useReward(reward) {
      try {
        if (reward.type === 'theme') {
          applyTheme(reward.value)
          this.markUsed(reward, 'theme')
          uni.showToast({ title: '主题已切换', icon: 'success' })
        } else if (reward.type === 'bg') {
          this.applyBackground(reward.value)
          this.markUsed(reward, 'bg')
          uni.showToast({ title: '背景已设置', icon: 'success' })
        } else if (reward.type === 'avatar') {
          uni.setStorageSync('avatar_decoration', reward.value)
          this.markUsed(reward, 'avatar')
          uni.showToast({ title: '头像装饰已保存', icon: 'success' })
        } else if (reward.type === 'quote') {
          uni.showModal({
            title: '励志语录',
            content: reward.value,
            showCancel: false,
            confirmText: '收下'
          })
        }

        // 好感度联动（对标循途礼物系统）：使用宝物赠予AI伙伴，提升好感度
        this.$store.commit('addAffection', 5)
        setTimeout(() => {
          uni.showToast({ title: '好感度 +5', icon: 'none', duration: 1500 })
        }, 600)

        this.closeDetail()
      } catch (e) {
        console.error('使用道具失败', e)
        uni.showToast({ title: '使用失败', icon: 'none' })
      }
    },
    /**
     * 宝物联动：把宝物作为礼物送给AI伙伴
     * 提升好感度、写入金币账单、AI给出反馈（聊天页主动消息）
     */
    giftToAI(reward) {
      uni.showModal({
        title: '送给AI伙伴',
        content: `确定把「${reward.name}」送给TA吗？TA会很开心的~`,
        confirmText: '送出',
        cancelText: '再想想',
        success: (r) => {
          if (r.confirm) {
            const result = economy.sendTreasure(reward)
            if (result.ok) {
              // 好感度联动
              this.$store.commit('addAffection', result.affection)
              // AI 反馈写入聊天（主动消息）
              try {
                uni.setStorageSync('pending_proactive_message', {
                  content: aiSocial.treasureFeedback(reward),
                  time: Date.now()
                })
              } catch (e) { /* 静默 */ }
              // 检查宝物收集解锁
              const unlocks = economy.checkTreasureUnlocks()
              if (unlocks.length > 0) {
                setTimeout(() => {
                  uni.showModal({
                    title: '🎉 宝物收集解锁！',
                    content: unlocks.map(u => u.name).join('、'),
                    showCancel: false
                  })
                }, 800)
              }
              uni.showToast({ title: `已送出，好感度+${result.affection}`, icon: 'success' })
              playSync.schedulePush('box')
              this.loadWarehouse()
              this.closeDetail()
            } else {
              uni.showToast({ title: result.msg, icon: 'none' })
            }
          }
        }
      })
    },
    markUsed(reward, type) {
      try {
        const idx = this.warehouse.findIndex(w => w.type === reward.type && w.value === reward.value)
        if (idx !== -1) {
          this.warehouse[idx].isUsed = true
          uni.setStorageSync(WAREHOUSE_KEY, this.warehouse)
          playSync.schedulePush('box')
        }
        uni.setStorageSync(`last_used_${type}`, reward.value)
      } catch (e) {
        console.error('标记使用失败', e)
      }
    },
    applyBackground(type) {
      const bgMap = {
        starry: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        forest: 'linear-gradient(135deg, #2d5016 0%, #3d723d 50%, #56ab2f 100%)',
        ocean: 'linear-gradient(135deg, #006994 0%, #0083b0 50%, #00b4db 100%)',
        sakura: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%)'
      }
      const bg = bgMap[type] || '#F8F9FA'
      uni.setStorageSync('custom_bg', bg)
      if (typeof document !== 'undefined' && document.documentElement) {
        const root = document.documentElement
        const page = document.querySelector('page')
        if (root) root.style.background = bg
        if (page) page.style.background = bg
      }
    },
    goBack() {
      uni.navigateBack()
    },
    goToBox() {
      uni.navigateTo({ url: '/pages/box/box' })
    },
    formatDate(timestamp) {
      if (!timestamp) return '未知'
      const date = new Date(timestamp)
      return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
    }
  }
}
</script>

<style lang="scss" scoped>
/* 道具详情弹层：设计稿未覆盖，沿用原有交互样式 */
.detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: rgba(31, 42, 37, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.detail-content {
  width: 100%;
  padding: 22rpx 36rpx calc(44rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  text-align: center;
  background: var(--v7-card);
  border-radius: 32rpx 32rpx 0 0;
}

.detail-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 0 auto 26rpx;
  border-radius: 999rpx;
  background: rgba(46, 86, 67, 0.14);
}

.detail-icon {
  width: 140rpx;
  height: 140rpx;
  margin: 0 auto 20rpx;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(156, 191, 170, 0.18);
  font-size: 72rpx;
}

.detail-title {
  display: block;
  margin-bottom: 14rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: var(--v7-green);
}

.detail-desc {
  display: block;
  margin-bottom: 14rpx;
  font-size: 25rpx;
  line-height: 1.6;
  color: rgba(60, 82, 72, 0.6);
}

.detail-date {
  display: block;
  margin-bottom: 34rpx;
  font-size: 21rpx;
  color: rgba(60, 82, 72, 0.4);
}

.detail-actions {
  display: flex;
}

.action-btn {
  flex: 1;
  margin-right: 14rpx;
  padding: 24rpx;
  border-radius: 999rpx;
  text-align: center;
  background: #fff;
  border: 1rpx solid rgba(46, 86, 67, 0.12);
}

.action-btn:last-child {
  margin-right: 0;
}

.action-btn text {
  font-size: 26rpx;
  color: var(--v7-green);
}

.action-btn.primary {
  background: var(--v7-green);
  border-color: var(--v7-green);
}

.action-btn.primary text {
  color: #F8F3E7;
}

.action-btn.gift {
  background: #C08A56;
  border-color: #C08A56;
}

.action-btn.gift text {
  color: #F8F3E7;
}
</style>
