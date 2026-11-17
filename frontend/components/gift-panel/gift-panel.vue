<template>
  <view class="gift-mask" v-if="visible" @click="$emit('close')">
    <view class="gift-panel" @click.stop>
      <view class="panel-header">
        <text class="panel-title">🎁 送礼物 / 转账</text>
        <view class="panel-coin">
          <text class="coin-num">🪙 {{ coins }}</text>
        </view>
        <text class="panel-close" @click="$emit('close')">✕</text>
      </view>

      <!-- 分类 -->
      <view class="panel-tabs">
        <view class="ptab" :class="{ active: activeTab === 'gift' }" @click="activeTab = 'gift'">
          <text>🎁 金币礼物</text>
        </view>
        <view class="ptab" :class="{ active: activeTab === 'treasure' }" @click="activeTab = 'treasure'">
          <text>💎 宝物礼物</text>
        </view>
      </view>

      <scroll-view scroll-y class="gift-scroll">
        <!-- 金币礼物：背包有货优先消耗背包，否则扣金币（转账式） -->
        <view v-if="activeTab === 'gift'" class="gift-grid">
          <view v-for="gift in gifts" :key="gift.id" class="gift-card" @click="chooseGift(gift)">
            <view class="gift-badge" v-if="inventory[gift.id] > 0">×{{ inventory[gift.id] }}</view>
            <text class="gift-icon">{{ gift.icon }}</text>
            <text class="gift-name">{{ gift.name }}</text>
            <view class="gift-price">
              <text>{{ inventory[gift.id] > 0 ? '背包有货' : '🪙 ' + gift.price }}</text>
            </view>
          </view>
        </view>

        <!-- 宝物礼物：来自宝物仓库 -->
        <view v-else>
          <view v-if="treasures.length > 0" class="treasure-list">
            <view v-for="t in treasures" :key="t.key" class="treasure-item" @click="chooseTreasure(t)">
              <text class="t-icon">{{ t.emoji }}</text>
              <view class="t-info">
                <text class="t-name">{{ t.name }}</text>
                <text class="t-desc">来自宝物仓库 · 好感度+10</text>
              </view>
              <text class="t-arrow">›</text>
            </view>
          </view>
          <view v-else class="empty-tip">
            <text>宝物仓库里还没有可赠送的宝物</text>
            <text class="empty-sub">去开盲盒收集宝物，送给TA会提升好感度</text>
          </view>
        </view>

        <view class="tip-bar">
          <text>💡 礼物可通过打卡任务随机掉落，也可在商城购买</text>
        </view>
        <view class="bottom-safe"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
/**
 * 送礼物面板：金币礼物 + 宝物礼物
 * 赠送逻辑在父组件（chat.vue）处理：扣费 → 动画 → AI反馈
 */
import economy, { GIFT_CATALOG } from '@/common/economy'

export default {
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      coins: 0,
      inventory: {},
      treasures: [],
      activeTab: 'gift'
    }
  },
  computed: {
    gifts() {
      return GIFT_CATALOG
    }
  },
  watch: {
    visible(v) {
      if (v) this.refresh()
    }
  },
  methods: {
    refresh() {
      this.coins = economy.getCoins()
      this.inventory = economy.getGiftInventory()
      this.treasures = economy.getGiftableTreasures()
    },
    chooseGift(gift) {
      this.$emit('send-gift', gift)
    },
    chooseTreasure(t) {
      this.$emit('send-treasure', t)
    }
  }
}
</script>

<style lang="scss" scoped>
.gift-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: flex;
  align-items: flex-end;
}
.gift-panel {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  align-items: center;
  padding: 30rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.panel-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
  flex: 1;
}
.panel-coin {
  padding: 8rpx 22rpx;
  background: #FFF7E6;
  border-radius: 999rpx;
  margin-right: 20rpx;
}
.coin-num {
  font-size: 24rpx;
  color: #F57C00;
  font-weight: 700;
}
.panel-close {
  font-size: 34rpx;
  color: #999;
  padding: 8rpx;
}
.panel-tabs {
  display: flex;
  padding: 20rpx 32rpx 0;
  gap: 16rpx;
}
.ptab {
  padding: 12rpx 30rpx;
  border-radius: 999rpx;
  background: #F5F6F7;
}
.ptab text { font-size: 26rpx; color: #666; }
.ptab.active { background: linear-gradient(135deg, #FFB74D, #FB8C00); }
.ptab.active text { color: #fff; font-weight: 600; }

.gift-scroll {
  flex: 1;
  max-height: 52vh;
}
.gift-grid {
  display: flex;
  flex-wrap: wrap;
  padding: 24rpx 20rpx 0;
}
.gift-card {
  position: relative;
  width: calc((100% - 60rpx) / 4);
  margin: 10rpx;
  padding: 26rpx 8rpx 20rpx;
  box-sizing: border-box;
  background: #FAFAFA;
  border-radius: 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.gift-card:active { background: #FFF3E0; transform: scale(0.95); }
.gift-badge {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  padding: 2rpx 12rpx;
  background: #4CAF50;
  color: #fff;
  font-size: 18rpx;
  border-radius: 8rpx;
}
.gift-icon { font-size: 56rpx; }
.gift-name {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #333;
}
.gift-price {
  margin-top: 8rpx;
}
.gift-price text {
  font-size: 20rpx;
  color: #F57C00;
}

/* 宝物 */
.treasure-list {
  padding: 24rpx 32rpx 0;
}
.treasure-item {
  display: flex;
  align-items: center;
  padding: 24rpx 28rpx;
  margin-bottom: 16rpx;
  background: #FAFAFA;
  border-radius: 20rpx;
}
.treasure-item:active { background: #F3E8FF; }
.t-icon { font-size: 44rpx; margin-right: 20rpx; }
.t-info { flex: 1; }
.t-name { font-size: 28rpx; color: #333; display: block; }
.t-desc { font-size: 22rpx; color: #999; margin-top: 6rpx; display: block; }
.t-arrow { font-size: 36rpx; color: #CCC; }

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 40rpx;
}
.empty-tip text { font-size: 26rpx; color: #999; }
.empty-sub { font-size: 22rpx; color: #BBB; margin-top: 12rpx; }

.tip-bar {
  padding: 20rpx 32rpx;
}
.tip-bar text {
  font-size: 22rpx;
  color: #BBB;
}
.bottom-safe { height: calc(env(safe-area-inset-bottom) + 20rpx); }
</style>
