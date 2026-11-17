<template>
  <view class="xt-page xt-s10">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">虚拟世界</view>
          <view class="page-sub">打卡推进剧情，她在故事里等你</view>
        </view>
        <view class="icon-btn" @click="goStats"><xt-icon name="i-search" /></view>
      </view>

      <view class="world-hero" @click="openCurrentWorld">
        <text class="wk">NOW PLAYING · {{ heroWorld ? '进行中' : '等待开启' }}</text>
        <view class="h3">{{ heroWorld ? heroWorld.name : '还没有世界' }}</view>
        <view class="p">{{ heroWorld ? (heroWorld.description || '她在故事里等你。') : '去广场找一个世界，或者自己建一个。' }}</view>
        <image v-if="heroPhoto" class="wav" :src="heroPhoto" mode="aspectFill" />
        <view v-else class="wav wav-fb"><text>{{ currentCharacter.avatar }}</text></view>
        <view class="wprog">
          <view class="bar"><view class="fill" :style="{ width: worldProgress + '%' }"></view></view>
          <view class="m">
            <text>剧情进度 {{ worldProgress }}%</text>
            <text>{{ remainCheckins > 0 ? '再打卡 ' + remainCheckins + ' 次解锁' : (heroWorld ? '已抵达终点' : '点这里去发现') }}</text>
          </view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 12px">
        <text class="t">继续探索</text>
        <text class="s">共 {{ worlds.length }} 个世界</text>
      </view>

      <view
        v-for="(w, i) in worlds"
        :key="w.id"
        class="wcard"
        @click="openWorld(w)"
      >
        <view class="wcover" :class="['wc1', 'wc2', 'wc3'][i % 3]"><xt-icon name="i-world" /></view>
        <view class="tx">
          <text class="n">{{ w.name }}</text>
          <text class="m">{{ w.checkin_total || 0 }}/{{ w.checkin_target || 0 }} 次打卡 · {{ w.member_count || 0 }} 位成员</text>
        </view>
        <text class="st">继续</text>
      </view>

      <!-- 空态：没有世界时不再摆 3 张写死的假卡片 -->
      <view v-if="!loading && !worlds.length" class="wcard" @click="goWorldList">
        <view class="wcover wc1"><xt-icon name="i-world" /></view>
        <view class="tx">
          <text class="n">去发现一个世界</text>
          <text class="m">打卡推进剧情，她在故事里等你</text>
        </view>
        <text class="st">去看看</text>
      </view>
    </view>

    <global-ai-assistant />
  </view>
</template>

<script>
/**
 * 世界页（发现 → 世界）
 * 原登录后首页（index）的全部功能迁移至此：
 * 问候头部 / 环球行走地图 / AI伙伴入口 / 每日语录 / 四个快捷入口
 */
import statsApi from '@/api/stats'
import worldApi from '@/api/world'
import { getCharacterById, getRandomPhrase } from '@/common/ai-characters'
import { getDailyQuote } from '@/common/ai-dialogue-engine'
import { getInactivityDialogue } from '@/common/walk-map-config.js'
// ↓↓↓ 新增 ↓↓↓ 统一拼头像地址
import { toAvatarUrl } from '@/common/request'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { getActivePartner, getPartnerPhoto } from '@/common/ai-partner'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      // 「继续探索」改为真实世界列表（原来 3 张卡片与进度都是写死的）
      worlds: [],
      loading: false,
      summary: {
        streakDays: 0,
        bestStreak: 0,
        todayCompleted: 0,
        todayTotal: 0,
        completionRate: 0,
        totalHabits: 0,
        totalCheckins: 0
      }
    }
  },
  computed: {
    greeting() {
      const h = new Date().getHours()
      const nickname = this.$store.state.userInfo.nickname || '朋友'
      if (h < 6) return `夜深了，${nickname}，注意休息`
      if (h < 12) return `早上好，${nickname}`
      if (h < 14) return `中午好，${nickname}，午休一下`
      if (h < 18) return `下午好，${nickname}，继续加油`
      if (h < 22) return `晚上好，${nickname}，回顾今天吧`
      return `夜深了，${nickname}，该睡了`
    },
    today() {
      const d = new Date()
      const weekDays = ['日', '一', '二', '三', '四', '五', '六']
      return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${weekDays[d.getDay()]}`
    },
    userInitial() {
      const name = this.$store.state.userInfo.nickname || '用户'
      return name.charAt(0)
    },
    // ↓↓↓ 新增 ↓↓↓
    userAvatar() {
      return toAvatarUrl(this.$store.state.userInfo.avatar || '')
    },
    currentCharacter() {
      return getActivePartner()
    },
    heroPhoto() {
      return getPartnerPhoto(this.currentCharacter) || ''
    },
    aiGreeting() {
      const characterId = this.currentCharacter.id
      try {
        return getRandomPhrase(characterId, 'morning')
      } catch (e) {
        console.error('获取问候语失败:', e)
        return '你好呀~'
      }
    },
    aiAvatar() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      return character?.avatar || '🌿'
    },
    dailyQuote() {
      return getDailyQuote()
    },
    heroWorld() {
      return this.worlds[0] || null
    },
    worldProgress() {
      const w = this.heroWorld
      if (!w || !w.checkin_target) return 0
      return Math.min(100, Math.round((w.checkin_total || 0) / w.checkin_target * 100))
    },
    remainCheckins() {
      const w = this.heroWorld
      if (!w || !w.checkin_target) return 0
      return Math.max(0, w.checkin_target - (w.checkin_total || 0))
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() {
    this.loadSummary()
    this.loadWorlds()
    this.checkInactivity()
  },
  methods: {
    async loadWorlds() {
      if (!this.$store?.state?.token) return
      this.loading = true
      try {
        const res = await worldApi.getList('mine')
        if (res && res.code === 200) this.worlds = res.data || []
      } catch (e) { /* request 层已提示 */ } finally {
        this.loading = false
      }
    },
    openWorld(w) {
      uni.navigateTo({ url: `/pages/world-space/world-detail?id=${w.id}` })
    },
    openCurrentWorld() {
      if (this.heroWorld) this.openWorld(this.heroWorld)
      else this.goWorldList()
    },
    goWorldList() {
      uni.navigateTo({ url: '/pages/world-space/world-list' })
    },
    async loadSummary() {
      try {
        const res = await statsApi.getSummary()
        const summaryData = res.data || res
        if (summaryData && typeof summaryData === 'object') {
          this.summary = summaryData
          this.$store.commit('setStreakDays', summaryData.streakDays || summaryData.current_streak || 0)
        }
      } catch (e) {
        console.error('加载统计数据失败', e)
      }
    },
    checkInactivity() {
      const inactivityDays = this.$store.getters.walkInactivityDays
      if (inactivityDays >= 3) {
        const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
        const msg = getInactivityDialogue(characterId)
        if (msg) {
          const today = new Date()
          const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
          const existing = this.$store.state.chatMessages.find(
            m => m.type === 'inactivity' && m.date === dateStr
          )
          if (!existing) {
            this.$store.commit('addChatMessage', {
              type: 'inactivity',
              role: 'assistant',
              content: msg,
              date: dateStr,
              time: new Date().getTime()
            })
          }
        }
      }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goChat() {
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    goStats() {
      // ↓↓↓ 修复 ↓↓↓ stats 不是 tabBar 页，switchTab 会静默失败，改成 navigateTo
      uni.navigateTo({ url: '/pages/stats/stats' })
    },
    goProfile() {
      uni.switchTab({ url: '/pages/profile/profile' })
    },
    goBox() {
      uni.navigateTo({ url: '/pages/box/box' })
    },
    goEmotion() {
      uni.navigateTo({ url: '/pages/emotion/emotion' })
    },
    goGrowthTrack() {
      uni.navigateTo({ url: '/pages/growth-track/growth-track' })
    },
    goMeditation() {
      uni.navigateTo({ url: '/pages/meditation/meditation' })
    }
  }
}
</script>

<style scoped>
/* 主形象使用 3:4 完整立绘，底部与进度条保留间距 */
.xt-page.xt-s10 .world-hero uni-image.wav {
  top: 38px;
  width: 72px;
  height: 96px;
  border-radius: 18px;
  overflow: hidden;
  display: block;
}
.xt-page.xt-s10 .world-hero uni-image.wav :deep(div),
.xt-page.xt-s10 .world-hero uni-image.wav :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s10 .world-hero uni-image.wav :deep(img) {
  object-fit: cover;
}
/* 无立绘伙伴回退 */
.xt-page.xt-s10 .world-hero .wav-fb {
  top: 38px;
  width: 72px;
  height: 96px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  font-size: 38px;
  line-height: 1;
}

/* 设计稿 h3 / p 元素选择器的等价 class */
.xt-page.xt-s10 .world-hero .h3 {
  position: relative;
  margin-top: 7px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.3px;
}
.xt-page.xt-s10 .world-hero .p {
  position: relative;
  width: 62%;
  margin-top: 5px;
  font-size: 8.5px;
  line-height: 1.62;
  color: rgba(255, 253, 250, 0.66);
}

/* 设计稿 .bar i 的等价填充条 */
.xt-page.xt-s10 .world-hero .wprog .fill {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9cbfaa, #e7eeeb);
}
</style>
