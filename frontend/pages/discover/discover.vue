<template>
  <view class="xt-page xt-s2 v7-page">
    <view class="body">
      <!-- 顶部问候 -->
      <view class="v7-greet">
        <view class="v7-greet-tx">
          <view class="v7-k">DISCOVER</view>
          <view class="v7-t">发现</view>
          <view class="v7-s">今天想和她一起做点什么？</view>
        </view>
        <view class="v7-bell" @click="go('/pages/newfunc/notification-center')">
          <xt-icon name="i-bell" />
          <i></i>
        </view>
      </view>

      <view class="v7-search" @click="onSearch">
        <xt-icon name="i-search" />
        <span>搜索世界、扭蛋剧本、伙伴…</span>
        <em>搜索</em>
      </view>

      <view class="v7-chips">
        <span
          v-for="c in chips"
          :key="c"
          class="v7-chip"
          :class="{ 'v7-on': filter === c }"
          @click="filter = c"
        >{{ c }}</span>
      </view>

      <!-- 大卡：左文右图 -->
      <view class="v7-hero" v-if="showHero" @click="go('/pages/schedule/schedule')">
        <view class="v7-hero-pic">
          <image v-if="heroPhoto" :src="heroPhoto" mode="aspectFill" />
          <view v-else class="v7-partner-fb"><text>{{ heroEmoji }}</text></view>
        </view>
        <view class="v7-hero-fade"></view>
        <view class="v7-hero-tx">
          <view class="v7-htag"><i></i>今日精选 · 她为你挑的</view>
          <view class="v7-htt">{{ heroTitle }}</view>
          <view class="v7-htd">根据你最近的睡眠与打卡，她替你排好了顺序</view>
          <view class="v7-hgo">去看看<xt-icon name="i-arrow" /></view>
        </view>
      </view>

      <view class="v7-sec"><b>为你推荐</b><span @click="onRefresh">换一批 ›</span></view>

      <!-- 四宫格入口 -->
      <view class="v7-quad">
        <view v-for="card in visibleCards" :key="card.key" class="v7-q" @click="go(card.path)">
          <view class="v7-qtop">
            <view class="v7-qico" :class="card.tint"><xt-icon :name="card.icon" /></view>
            <span v-if="card.badge" class="v7-qbdg">{{ card.badge }}</span>
          </view>
          <view class="v7-qtt">{{ card.title }}</view>
          <view class="v7-qds">{{ card.desc }}</view>
        </view>
      </view>

      <!-- 环游世界：环球行走入口（接真实步数/关卡进度） -->
      <view class="v7-journey" v-if="showWalk" @click="go('/pages/walk/walk')">
        <view class="v7-journey-ico"><xt-icon name="i-compass" /></view>
        <view class="v7-journey-tx">
          <view class="v7-journey-head">
            <view class="v7-journey-t">环游世界</view>
            <view class="v7-journey-tag">{{ walkStageName }}</view>
          </view>
          <view class="v7-journey-d">{{ walkDesc }}</view>
          <view class="v7-journey-bar"><i :style="{ width: walkProgress + '%' }"></i></view>
        </view>
        <view class="v7-journey-ar"><xt-icon name="i-right" /></view>
      </view>

      <!-- 列表卡片 -->
      <view class="v7-list">
        <view class="v7-li" v-if="showWorkshop" @click="go('/pages/newfunc/bot-manage')">
          <view class="v7-li-ico v7-ico-green"><xt-icon name="i-tool" /></view>
          <view class="v7-li-tx">
            <view class="v7-li-t">伙伴工坊</view>
            <view class="v7-li-d">20 位可切换</view>
          </view>
          <view class="v7-li-ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="v7-li" v-if="showMoments" @click="go('/pages/moments/moments')">
          <view class="v7-li-ico v7-ico-ochre"><xt-icon name="i-moments" /></view>
          <view class="v7-li-tx">
            <view class="v7-li-t">朋友圈</view>
            <view class="v7-li-d">看看她最近发的</view>
          </view>
          <view class="v7-li-ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="v7-li" v-if="showRecords" @click="go('/pages/records/records')">
          <view class="v7-li-ico v7-ico-green"><xt-icon name="i-edit" /></view>
          <view class="v7-li-tx">
            <view class="v7-li-t">我的记录</view>
            <view class="v7-li-d">写下的每一句都在这里</view>
          </view>
          <view class="v7-li-ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="v7-li" v-if="showRecords" @click="go('/pages/postcard-gallery/postcard-gallery')">
          <view class="v7-li-ico v7-ico-ochre"><xt-icon name="i-compass" /></view>
          <view class="v7-li-tx">
            <view class="v7-li-t">明信片风景</view>
            <view class="v7-li-d">28 张城市风景慢慢看</view>
          </view>
          <view class="v7-li-ar"><xt-icon name="i-right" /></view>
        </view>
      </view>

      <!-- 她的建议 -->
      <view class="v7-ai" v-if="showAi" @click="go('/pages/meditation/meditation')">
        <view class="v7-ai-av">
          <image v-if="partnerAvatar" :src="partnerAvatar" mode="aspectFill" />
          <view v-else class="v7-partner-fb"><text>{{ heroEmoji }}</text></view>
        </view>
        <view class="v7-ai-tx">
          <view class="v7-ai-t">她根据你的记录建议</view>
          <view class="v7-ai-d">今晚 22:40 一起做睡前放松，明早会更容易醒。</view>
        </view>
        <view class="v7-ai-ar"><xt-icon name="i-right" /></view>
      </view>
    </view>
    <v7-tabbar active="discover" />
  </view>
</template>

<script>
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import V7Tabbar from '@/components/v7-tabbar/v7-tabbar.vue'
import { getActivePartner, getPartnerPhoto, getPartnerAvatar } from '@/common/ai-partner'
import focusApi from '@/api/focus'
import gachaApi from '@/api/gacha'

export default {
  components: { XtIcon, V7Tabbar },
  data() {
    return {
      filter: '全部',
      // 四宫格角标改为真实数据（原来写死「3 个 / 免费 2 次 / 今天 2 件 / 25 分钟」）
      stats: { coin: 0, todo: 0, focusMin: 0 },
      statsLoaded: false,
      chips: ['全部', '陪伴', '成长', '玩法', '记录'],
      cards: [
        { key: 'world', cat: '玩法', icon: 'i-world', tint: 'tt-g', badge: '', title: '共创世界', desc: '和她的专属星球', path: '/pages/world-space/world-list' },
        { key: 'gacha', cat: '玩法', icon: 'i-gacha', tint: 'tt-p', badge: '', title: '互动扭蛋', desc: '今天的剧本已更新', path: '/pages/gacha/gacha' },
        { key: 'calendar', cat: '成长', icon: 'i-calendar', tint: 'tt-b', badge: '', title: '成长日历', desc: '她替你排好的小事', path: '/pages/schedule/schedule' },
        { key: 'focus', cat: '陪伴', icon: 'i-focus', tint: 'tt-s', badge: '', title: '一起专注', desc: '她会在旁边陪着', path: '/pages/focus/focus-home' }
      ]
    }
  },
  computed: {
    heroPhoto() {
      return getPartnerPhoto(getActivePartner()) || ''
    },
    partnerAvatar() {
      return getPartnerAvatar(getActivePartner()) || ''
    },
    heroEmoji() {
      return getActivePartner().avatar || '🌿'
    },
    // 筛选真正生效：按 chips 的类目过滤四宫格，其余区块按类目显隐
    visibleCards() {
      const list = this.filter === '全部' ? this.cards : this.cards.filter(c => c.cat === this.filter)
      if (!this.statsLoaded) return list
      return list.map(card => {
        if (card.key === 'gacha') {
          return { ...card, badge: this.stats.coin ? `扭蛋币 ${this.stats.coin}` : '签到领扭蛋币' }
        }
        if (card.key === 'calendar') {
          return { ...card, badge: this.stats.todo ? `今天 ${this.stats.todo} 件事` : '今天暂无待办' }
        }
        if (card.key === 'focus') {
          return { ...card, badge: this.stats.focusMin ? `今天 ${this.stats.focusMin} 分钟` : '今天还没开始' }
        }
        return card
      })
    },
    showHero() {
      return this.filter === '全部' || this.filter === '成长'
    },
    showWorkshop() {
      return this.filter === '全部' || this.filter === '陪伴'
    },
    showMoments() {
      return this.filter === '全部' || this.filter === '记录'
    },
    showRecords() {
      return this.filter === '全部' || this.filter === '记录'
    },
    showAi() {
      return this.filter === '全部' || this.filter === '陪伴'
    },
    // 大卡标题：跟着今日待办数量走，不再写死「3 件」
    heroTitle() {
      if (this.stats.todo > 0) return `今天 ${this.stats.todo} 件她替你排好的小事`
      return '今天想做什么，她陪你一起'
    },
    // === 环游世界（环球行走）入口数据 ===
    walkSteps() {
      return Math.round(this.$store?.state?.walkMap?.totalSteps || 0)
    },
    walkStageName() {
      return this.$store?.getters?.currentStage?.name || '初始起点'
    },
    walkProgress() {
      const p = this.$store?.getters?.stageProgress
      return typeof p === 'number' ? p : 0
    },
    walkDesc() {
      if (!this.walkSteps) return '从第一步开始，和她一起看世界'
      const stage = this.$store?.getters?.currentStage
      const next = stage?.nextThreshold
      if (next === null || next === undefined || next === Infinity) {
        return `已同行 ${this.walkSteps} 步 · 旅途已到终点`
      }
      const remain = Math.max(next - (this.$store?.getters?.totalCheckins || 0), 0)
      return remain > 0
        ? `已同行 ${this.walkSteps} 步 · 还差 ${remain} 次打卡到下一站`
        : `已同行 ${this.walkSteps} 步 · 下一站即将抵达`
    },
    showWalk() {
      return this.filter === '全部' || this.filter === '玩法'
    }
  },
  onShow() {
    try {
      uni.hideTabBar({ animation: false, fail: () => {} })
    } catch (e) {}
    this.loadStats()
  },
  methods: {
    // 四宫格角标：拉取真实的扭蛋币 / 今日待办 / 今日专注分钟，失败则保留静态文案
    async loadStats() {
      if (!this.$store?.state?.token) return
      const [wallet, board, stat] = await Promise.allSettled([
        gachaApi.getWallet(), focusApi.getTasks(), focusApi.getStat('day')
      ])
      if (wallet.status === 'fulfilled' && wallet.value?.code === 200) {
        this.stats.coin = wallet.value.data?.coin_balance || 0
      }
      if (board.status === 'fulfilled' && board.value?.code === 200) {
        const list = board.value.data?.list || []
        this.stats.todo = list.filter(t => t.status !== 2).length
      }
      if (stat.status === 'fulfilled' && stat.value?.code === 200) {
        this.stats.focusMin = stat.value.data?.total_minutes || 0
      }
      this.statsLoaded = true
    },
    go(url) {
      uni.navigateTo({ url })
    },
    onSearch() {
      uni.navigateTo({ url: '/pages/idea/idea-landing' })
    },
    onRefresh() {
      // 无推荐接口：用真实的顺序轮换来产生“换一批”效果，至少不是纯 toast
      if (this.cards.length > 1) {
        this.cards.push(this.cards.shift())
      }
      uni.showToast({ title: '已为你换一批', icon: 'none', duration: 800 })
    }
  }
}
</script>

<style lang="scss" scoped>
/* ===== V7 纸感手帐 · 发现页 ===== */
.xt-page.v7-page {
  background: #F8F4EC;
  background-image: none;
  color: #24493A;
}

/* 底部为悬浮 dock 留出空间 */
.xt-page.xt-s2.v7-page .body {
  padding: calc(14px + env(safe-area-inset-top)) 18px calc(90px + env(safe-area-inset-bottom));
}

/* 顶部问候 */
.v7-greet {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 2px 2px 12px;
}
.v7-greet-tx { flex: 1; min-width: 0; }
.v7-k {
  font-size: 8.5px;
  font-weight: 800;
  letter-spacing: 1.6px;
  color: #A2AAA3;
}
.v7-t {
  margin-top: 5px;
  font-size: 23px;
  font-weight: 900;
  line-height: 1.1;
  letter-spacing: -.8px;
  color: #24493A;
}
.v7-s {
  margin-top: 6px;
  font-size: 8.5px;
  letter-spacing: .2px;
  color: #6A776E;
}
.v7-bell {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #24493A;
  background: #FFFDFA;
  border: 1px solid rgba(30, 42, 36, .10);
  flex-shrink: 0;
}
.v7-bell .ic { width: 15px; height: 15px; }
.v7-bell i {
  position: absolute;
  top: 7px;
  right: 8px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #B2793F;
  box-shadow: 0 0 0 2px #F8F4EC;
}

/* 搜索 */
.v7-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 6px 0 13px;
  border-radius: 14px;
  background: #FFFDFA;
  border: 1px solid rgba(30, 42, 36, .10);
  box-shadow: 0 14px 26px -26px rgba(36, 73, 58, .6);
}
.v7-search .ic {
  width: 14px;
  height: 14px;
  color: #B2793F;
  flex-shrink: 0;
}
.v7-search span {
  flex: 1;
  font-size: 8.5px;
  color: #A2AAA3;
}
.v7-search em {
  font-style: normal;
  font-size: 8px;
  font-weight: 900;
  color: #F8F4EC;
  background: #24493A;
  padding: 6px 12px;
  border-radius: 10px;
}

/* 筛选 chips */
.v7-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0;
}
.v7-chip {
  font-size: 8px;
  font-weight: 700;
  color: #6A776E;
  padding: 6px 11px;
  border-radius: 999px;
  background: rgba(255, 253, 250, .72);
  border: 1px solid rgba(30, 42, 36, .10);
  transition: background-color .2s, color .2s, border-color .2s;
}
.v7-chip.v7-on {
  color: #F8F4EC;
  background: #24493A;
  border-color: #24493A;
}

/* 大卡：左文右图 */
.v7-hero {
  position: relative;
  height: 176px;
  border-radius: 24px;
  overflow: hidden;
  background: linear-gradient(120deg, #F6EFE2 0%, #EFE3D0 58%, #DFCEB2 100%);
  border: 1px solid rgba(30, 42, 36, .10);
  box-shadow: 0 22px 40px -34px rgba(36, 73, 58, .75);
}
.v7-hero-pic {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 52%;
}
.v7-hero-pic uni-image,
.v7-hero-pic :deep(uni-image > div),
.v7-hero-pic :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.v7-hero-pic :deep(uni-image > div) {
  background-size: contain;
  background-position: right center;
  background-repeat: no-repeat;
}
.v7-hero-pic :deep(uni-image img) {
  object-fit: contain;
  object-position: right center;
}
.v7-hero-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #F6EFE2 0%, rgba(246, 239, 226, .86) 30%, rgba(246, 239, 226, 0) 62%);
}
.v7-hero-tx {
  position: relative;
  z-index: 2;
  width: 66%;
  padding: 15px 14px;
}
.v7-htag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: .2px;
  color: #24493A;
  background: rgba(255, 253, 250, .82);
  border: 1px solid rgba(30, 42, 36, .08);
  padding: 4px 8px;
  border-radius: 999px;
}
.v7-htag i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #B2793F;
}
.v7-htt {
  margin-top: 9px;
  font-size: 17px;
  font-weight: 900;
  line-height: 1.35;
  letter-spacing: .1px;
  color: #24493A;
}
.v7-htd {
  margin-top: 7px;
  font-size: 8px;
  line-height: 1.65;
  color: #6A776E;
}
.v7-hgo {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 8px;
  font-weight: 900;
  color: #F8F4EC;
  background: #24493A;
  padding: 6px 11px;
  border-radius: 999px;
}
.v7-hgo .ic { width: 10px; height: 10px; }

/* 小节标题 */
.v7-sec {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 18px 3px 9px;
}
.v7-sec b {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .2px;
  color: #24493A;
}
.v7-sec span {
  font-size: 7.5px;
  color: #A2AAA3;
}

/* 四宫格入口 */
.v7-quad {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
}
.v7-q {
  padding: 12px;
  border-radius: 18px;
  background: #FFFDFA;
  border: 1px solid rgba(30, 42, 36, .10);
  box-shadow: 0 16px 30px -30px rgba(36, 73, 58, .8);
}
.v7-qtop {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 6px;
}
.v7-qico {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #EBF2EC;
  color: #24493A;
  flex-shrink: 0;
}
.v7-qico .ic { width: 14px; height: 14px; }
.v7-qbdg {
  font-size: 6.2px;
  font-weight: 900;
  color: #6B5939;
  background: #F1ECE2;
  padding: 2.5px 6px;
  border-radius: 999px;
  white-space: nowrap;
}
.v7-qtt {
  margin-top: 9px;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: -.1px;
  color: #24493A;
}
.v7-qds {
  margin-top: 3px;
  font-size: 8px;
  line-height: 1.4;
  color: #A2AAA3;
}
.v7-q:nth-child(1) .v7-qico { background: #EBF2EC; color: #24493A; }
.v7-q:nth-child(2) .v7-qico { background: #F7EDE1; color: #B2793F; }
.v7-q:nth-child(3) .v7-qico { background: #F1ECE2; color: #7C5A33; }
.v7-q:nth-child(4) .v7-qico { background: #EBF2EC; color: #24493A; }

/* 环游世界入口卡 */
.v7-journey {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: 9px;
  padding: 12px 13px;
  border-radius: 18px;
  background: linear-gradient(135deg, #FFFDFA 0%, #F7F1E8 100%);
  border: 1px solid rgba(30, 42, 36, .10);
  box-shadow: 0 16px 30px -30px rgba(36, 73, 58, .8);
  transition: transform .18s;
}
.v7-journey:active { transform: scale(.99); }
.v7-journey-ico {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #F8F4EC;
  background: linear-gradient(140deg, #44705A 0%, #24493A 100%);
}
.v7-journey-ico .ic { width: 17px; height: 17px; }
.v7-journey-tx { flex: 1; min-width: 0; }
.v7-journey-head {
  display: flex;
  align-items: center;
  gap: 7px;
}
.v7-journey-t {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: -.1px;
  color: #24493A;
}
.v7-journey-tag {
  font-size: 6.2px;
  font-weight: 900;
  color: #6B5939;
  background: #F1ECE2;
  padding: 2.5px 6px;
  border-radius: 999px;
  white-space: nowrap;
}
.v7-journey-d {
  margin-top: 3px;
  font-size: 8px;
  line-height: 1.4;
  color: #6A776E;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.v7-journey-bar {
  height: 3px;
  margin-top: 7px;
  border-radius: 999px;
  background: rgba(36, 73, 58, .10);
  overflow: hidden;
}
.v7-journey-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #8FB79E, #24493A);
}
.v7-journey-ar {
  flex-shrink: 0;
  color: #A2AAA3;
}
.v7-journey-ar .ic { width: 12px; height: 12px; }

/* 列表卡片 */
.v7-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
.v7-li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 16px;
  background: #FFFDFA;
  border: 1px solid rgba(30, 42, 36, .10);
  box-shadow: 0 14px 26px -28px rgba(36, 73, 58, .8);
}
.v7-li-ico {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.v7-li-ico .ic { width: 14px; height: 14px; }
.v7-ico-green { background: #EBF2EC; color: #24493A; }
.v7-ico-ochre { background: #F7EDE1; color: #B2793F; }
.v7-li-tx { flex: 1; min-width: 0; }
.v7-li-t {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: -.1px;
  color: #24493A;
}
.v7-li-d {
  margin-top: 2px;
  font-size: 8px;
  color: #6A776E;
}
.v7-li-ar {
  flex-shrink: 0;
  color: #A2AAA3;
}
.v7-li-ar .ic { width: 12px; height: 12px; }

/* 她的建议 */
.v7-ai {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 11px 12px;
  border-radius: 16px;
  background: #FFFDFA;
  border: 1px solid rgba(30, 42, 36, .10);
  border-left: 2px solid #B2793F;
  box-shadow: 0 16px 30px -30px rgba(36, 73, 58, .8);
}
.v7-ai-av {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #F1ECE2;
  box-shadow: 0 0 0 2px #F8F4EC, 0 0 0 3px rgba(178, 121, 63, .28);
}
.v7-ai-av uni-image,
.v7-ai-av :deep(uni-image > div),
.v7-ai-av :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.v7-ai-av :deep(uni-image img) {
  object-fit: cover;
}
/* 无立绘伙伴回退（自定义伙伴未上传头像时） */
.v7-partner-fb {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  font-size: 15px;
  line-height: 1;
  border-radius: inherit;
}
.v7-hero-pic .v7-partner-fb { font-size: 46px; }
.v7-ai-tx { flex: 1; min-width: 0; }
.v7-ai-t {
  font-size: 8px;
  font-weight: 900;
  letter-spacing: .2px;
  color: #B2793F;
}
.v7-ai-d {
  margin-top: 3px;
  font-size: 8px;
  line-height: 1.55;
  color: #6A776E;
}
.v7-ai-ar {
  flex-shrink: 0;
  color: #A2AAA3;
}
.v7-ai-ar .ic { width: 12px; height: 12px; }
</style>
