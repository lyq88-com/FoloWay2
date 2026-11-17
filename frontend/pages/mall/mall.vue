<template>
  <view class="xt-page xt-s7">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">金币商城</view>
          <view class="page-sub">打卡赚金币，换一点小心意</view>
        </view>
        <view class="icon-btn" @click="goBill">
          <xt-icon name="i-clock" />
        </view>
      </view>

      <view class="wallet">
        <view class="k">MY COINS</view>
        <view class="vrow">
          <text class="v">{{ coinsText }}</text>
          <text class="u">金币</text>
        </view>
        <view class="sub">本周通过打卡与陪伴获得 +320</view>
        <view class="earn" @click="goBill">去赚金币</view>
      </view>

      <view class="chips">
        <text
          v-for="tab in tabs"
          :key="tab.key"
          class="chip"
          :class="{ on: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</text>
      </view>

      <view class="shop-grid">
        <view v-for="(goods, i) in filteredGoods" :key="goods.id" class="goods">
          <view class="thumb" :class="shopTints[i % shopTints.length]">
            <xt-icon :name="shopIcons[i % shopIcons.length]" />
          </view>
          <view class="n">{{ goods.name }}</view>
          <view class="d">{{ goods.desc }}</view>
          <view class="prow">
            <view class="price">{{ goods.price }}<text> 金币</text></view>
            <text class="buy" @click.stop="buy(goods)">兑换</text>
          </view>
        </view>
      </view>

      <!-- 【修复】推荐卡片原来只有箭头没有行为：现在点击可换一个 -->
      <view class="ai-rec" @click="nextRec">
        <view class="sp"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="k">她替你挑的</view>
          <view class="p">{{ currentRec.text }}</view>
        </view>
        <view class="arrow"><xt-icon name="i-right" /></view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 虚拟货币商城
 * - 礼物（购买后入背包，可赠送AI伙伴）
 * - 扭蛋券、装扮道具（气泡/背景/音色）
 * - 货币来源：打卡奖励、任务奖励
 */
import economy, { MALL_GOODS } from '@/common/economy'
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      coins: 0,
      giftInventory: {},
      gachaTickets: 0,
      activeTab: 'all',
      // 【新增】本地推荐轮换：暂无推荐接口，用候选池做真实切换
      recIndex: 0,
      recPicks: [
        { text: '桂花乌龙最像你上次说的那家店，要不要换一个？' },
        { text: '今天降温，热可可或许比冰美式更适合你。' },
        { text: '你收藏过的那款「月光灯」，现在兑换正好。' }
      ],
      tabs: [
        { key: 'all', label: '全部' },
        { key: 'gift', label: '礼物' },
        { key: 'deco', label: '装扮' },
        { key: 'ticket', label: '扭蛋券' }
      ]
    }
  },
  computed: {
    filteredGoods() {
      if (this.activeTab === 'all') return MALL_GOODS
      return MALL_GOODS.filter(g => g.kind === this.activeTab)
    },
    currentRec() {
      return this.recPicks[this.recIndex] || { text: '' }
    },
    coinsText() {
      return Number(this.coins || 0).toLocaleString('en-US')
    },
    // 设计稿商品缩略图图标与底色（按列表顺序循环）
    shopIcons() {
      return ['i-heart', 'i-moon', 'i-spark', 'i-book']
    },
    shopTints() {
      return ['tint-peach', 'tint-purple', 'tint-green', 'tint-blue']
    }
  },
  onShow() {
    this.refresh()
    uni.$on('economy-updated', this.refresh)
  },
  onHide() {
    uni.$off('economy-updated', this.refresh)
  },
  onUnload() {
    uni.$off('economy-updated', this.refresh)
  },
  methods: {
    /** 【新增】推荐卡片：点击换一个（本地候选轮换） */
    nextRec() {
      this.recIndex = (this.recIndex + 1) % this.recPicks.length
      uni.showToast({ title: '已换一个推荐', icon: 'none', duration: 800 })
    },
    refresh() {
      this.coins = economy.getCoins()
      this.giftInventory = economy.getGiftInventory()
      this.gachaTickets = economy.getGachaTickets()
    },
    ownedCount(goods) {
      if (goods.kind === 'gift') return this.giftInventory[goods.id] || 0
      if (goods.kind === 'ticket') return this.gachaTickets
      return 0
    },
    buy(goods) {
      if (this.coins < goods.price) {
        uni.showToast({ title: '金币不足，去打卡赚金币吧~', icon: 'none' })
        return
      }
      uni.showModal({
        title: '确认购买',
        content: `花费 ${goods.price} 金币购买「${goods.name}」？`,
        confirmText: '购买',
        success: (r) => {
          if (r.confirm) {
            this.doBuy(goods)
          }
        }
      })
    },
    /**
     * 已登录：先 flush 本地经济到云端 → 服务端定价下单（行锁扣币）
     * 未登录：保持原来的纯本地购买，行为不变
     */
    async doBuy(goods) {
      const token = (this.$store && this.$store.state && this.$store.state.token) || ''
      if (!token) {
        const result = economy.buyGoods(goods.id)
        if (result.ok) {
          uni.showToast({ title: result.msg, icon: 'success' })
          this.refresh()
        } else {
          uni.showToast({ title: result.msg, icon: 'none' })
        }
        return
      }

      uni.showLoading({ title: '购买中...', mask: true })
      const synced = await economy.flushCloud()
      if (!synced) {
        uni.hideLoading()
        uni.showToast({ title: '云端资产同步失败，请检查网络后重试', icon: 'none' })
        return
      }

      const res = await playSync.createShopOrder(goods.id, 1)
      uni.hideLoading()
      const body = res.body || {}
      if (res.ok && body.code === 200) {
        // 服务端已扣币并发放商品，拉回权威状态覆盖本地
        await economy.pullFromCloud()
        this.refresh()
        uni.showToast({ title: body.message || '购买成功', icon: 'success' })
      } else {
        uni.showToast({ title: body.message || '购买失败，请稍后重试', icon: 'none' })
      }
    },
    goBill() {
      uni.navigateTo({ url: '/pages/bill/bill' })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 商品较多时在内容区滚动（商城非 tab 页，无需 tabBar 预留） */
.xt-page.xt-s7 .body {
  overflow-y: auto;
}
</style>
