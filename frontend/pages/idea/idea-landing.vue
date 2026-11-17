<template>
  <view class="xt-page xt-s37">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">小想法</view>
          <view class="page-sub">不必完整，半句话也值得被听见</view>
        </view>
        <view class="icon-btn" @click="goPublish"><xt-icon name="i-edit" /></view>
      </view>

      <!-- 【修复】搜索框原来只是静态占位，现在可按关键词过滤下方示例 -->
      <view class="search">
        <xt-icon name="i-search" size="15" />
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜一个此刻的心情"
          placeholder-class="search-ph"
          confirm-type="search"
          @confirm="onSearch"
        />
        <text v-if="keyword" class="search-clear" @click="clearKeyword">清除</text>
      </view>

      <!-- 今日共鸣 -->
      <view class="feature" style="height:auto;padding:16px;display:block;background:linear-gradient(145deg,#FFFDFA,#F8F3EF)">
        <view style="display:flex;align-items:center;gap:6px;font-size:7px;color:#8E9A91">
          <text style="background:#EEF4F1;color:#3C6B55">今日共鸣</text>
          <text>匿名 · 2 小时前</text>
        </view>
        <view style="margin-top:9px;font-size:13px;line-height:1.72;font-weight:800;color:#22302A">
          “也许我不是懒，我只是需要一个一起开始的人。”
        </view>
        <view style="display:flex;align-items:center;justify-content:space-between;margin-top:12px">
          <view style="display:flex;align-items:center;font-size:7.5px;color:#8E9A91">
            <text>已有</text>
            <text style="margin:0 3px;font-weight:700;color:var(--v7-green)">128</text>
            <text>人和你有同感</text>
          </view>
          <text class="chip on" style="font-size:7.5px;padding:5px 12px" @click="goPublish">我也这样想</text>
        </view>
      </view>

      <view class="cal-sec" style="margin-top:14px">
        <text class="t">相似的半句</text>
        <text class="s">来自和你相似的人</text>
      </view>

      <!-- 【修复】示例卡片改为可点击 + 可由搜索过滤 -->
      <view class="wcard" v-for="(c, i) in visibleCards" :key="i" @click="goResonance">
        <view class="wcover" :class="c.tint"><xt-icon :name="c.icon" /></view>
        <view class="tx">
          <text class="n">{{ c.text }}</text>
          <text class="m">{{ c.meta }}</text>
        </view>
        <view class="ar"><xt-icon name="i-right" /></view>
      </view>

      <view v-if="!visibleCards.length" class="empty-tip">
        <text>没搜到相似的心情，换个词试试，或者写下你自己的</text>
      </view>

      <view class="auth-btn" style="margin-top:13px" @click="goPublish">写下此刻的一句</view>
      <text v-if="welcomed" class="auth-alt" @click="goResonance">看看我的共鸣 ›</text>
    </view>
  </view>
</template>

<script>
/**
 * 小想法 · 引导着陆页
 * 新用户第一次进入展示引导；老用户直接跳到「共鸣列表」。
 * 入口：心愿岛 / 发现页内的「小想法」卡片。
 */
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      welcomed: false,
      keyword: '',
      // 引导页示例内容（本地数据，搜索只过滤这里的示例）
      cards: [
        { text: '“我把闹钟调早了十分钟，只想有个不被催促的早晨。”', meta: '匿名 · 共鸣 46 · 3 条回应', icon: 'i-spark', tint: 'tint-green' },
        { text: '“今天没有变好，但我没有放弃变好。”', meta: '夜猫 · 共鸣 89 · 12 条回应', icon: 'i-heart', tint: 'tint-peach' },
        { text: '“想找个人一起，安静地把事情做完。”', meta: '小满 · 共鸣 31 · 5 条回应', icon: 'i-moon', tint: 'tint-blue' }
      ]
    }
  },
  computed: {
    visibleCards() {
      const k = (this.keyword || '').trim()
      if (!k) return this.cards
      return this.cards.filter(c => (c.text + c.meta).indexOf(k) > -1)
    }
  },
  onLoad() {
    const w = uni.getStorageSync('idea_welcomed')
    this.welcomed = w === '1'
    // 老用户：直接进入共鸣列表（首次进入才停留在此页做引导）
    if (this.welcomed) {
      uni.redirectTo({ url: '/pages/idea/idea-resonance' })
    }
  },
  methods: {
    onSearch() {
      if (!this.visibleCards.length) {
        uni.showToast({ title: '没有相似的心情，换个词试试', icon: 'none' })
      }
    },
    clearKeyword() {
      this.keyword = ''
    },
    goPublish() {
      uni.setStorageSync('idea_welcomed', '1')
      uni.navigateTo({ url: '/pages/idea/idea-publish' })
    },
    goResonance() {
      uni.redirectTo({ url: '/pages/idea/idea-resonance' })
    }
  }
}
</script>

<style scoped>
/* 设计稿内联元素在 H5 的等价补充 */
.xt-page.xt-s37 .auth-alt {
  display: block;
}
/* 【新增】搜索框：输入区铺满剩余宽度，去掉默认输入框外观 */
.xt-page.xt-s37 .search-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 12px;
  color: #22302A;
}
.xt-page.xt-s37 .search-ph {
  color: #8E9A91;
  font-size: 12px;
}
.xt-page.xt-s37 .search-clear {
  font-size: 10px;
  color: #6B8E7B;
}
.xt-page.xt-s37 .empty-tip {
  margin-top: 12px;
  padding: 18px 14px;
  border-radius: 14px;
  background: #F8F6F1;
  font-size: 11px;
  line-height: 1.7;
  color: #8E9A91;
  text-align: center;
}
</style>
