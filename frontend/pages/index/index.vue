<template>
  <view class="xt-page v7-home">
    <view class="v7-body">
      <!-- 关系状态条 -->
      <view class="topbar">
        <view class="tb-left">
          <view class="tb-dot"></view>
          <text class="tb-t">相伴第 {{ companionDays || 1 }} 天 · 她一直在</text>
        </view>
      </view>

      <!-- 角色切换轨 -->
      <view class="rail">
        <view
          v-for="role in railRoles"
          :key="role.id"
          class="rail-role"
          :class="{ on: role.id === currentCharacter.id }"
          @click="switchRole(role.id)"
        >
          <view class="rail-av">
            <image v-if="role.photo" :src="role.photo" mode="aspectFill" />
            <text v-else class="rail-fb">{{ role.name.slice(0, 1) }}</text>
          </view>
          <text class="rail-name">{{ role.name }}</text>
        </view>
        <view class="rail-role" @click="goGallery">
          <view class="rail-more">+{{ moreCount }}</view>
          <text class="rail-name">全部</text>
        </view>
      </view>

      <!-- 立绘主视觉 -->
      <view class="hero" @click="goChat">
        <view class="hero-img" :style="heroPhoto ? { backgroundImage: 'url(' + heroPhoto + ')' } : {}"></view>
        <view v-if="!heroPhoto" class="hero-fallback"><text class="hero-emoji">{{ aiAvatar }}</text></view>
        <view class="hero-tx">
          <view class="lb"><view class="dot"></view>{{ styleLabel }}型 · 在线</view>
          <view class="ttl">{{ aiGreeting }}</view>
          <view class="hp">{{ currentCharacter.catchphrase }}</view>
          <view class="go">和她说句话 <xt-icon name="i-arrow" :size="12" /></view>
        </view>
        <view class="hero-score">
          <text class="v">{{ affectionProgress }}%</text>
          <text class="k">默契温度</text>
        </view>
      </view>

      <!-- 三格数据 -->
      <view class="stat3">
        <view class="c" @click="goStats">
          <text class="b">{{ companionDays }}</text>
          <text class="l">连续陪伴 · 天</text>
        </view>
        <view class="c" @click="goStats">
          <text class="b">{{ summary.todayCompleted || 0 }}/{{ summary.todayTotal || 0 }}</text>
          <text class="l">今天的小事</text>
        </view>
        <view class="c" @click="goStats">
          <text class="b">{{ summary.totalCheckins || 0 }}</text>
          <text class="l">累计打卡 · 次</text>
        </view>
      </view>

      <!-- 今日习惯打卡（复用 /habit 接口，直接点选） -->
      <view class="hb-card" v-if="habits.length">
        <view class="hb-head">
          <text class="hb-t">今天的习惯</text>
          <text class="hb-s">{{ habitDoneCount }}/{{ habits.length }}</text>
        </view>
        <view class="hb-row" v-for="h in habits" :key="h.id" @click="toggleHabit(h)">
          <view class="hb-ic" :class="{ 'is-done': h.completed }">
            <text>{{ h.completed ? '✓' : '+' }}</text>
          </view>
          <view class="hb-tx">
            <text class="hb-n" :class="{ 'is-done': h.completed }">{{ h.name }}</text>
            <text class="hb-m">{{ h.completed ? '今天已完成' : (h.streak ? '已连续 ' + h.streak + ' 天' : '还没打卡') }}</text>
          </view>
        </view>
      </view>

      <!-- 今天只剩一件 -->
      <view class="sect"><text class="h">今天只剩一件</text><text class="s">她陪你做</text></view>
      <view class="task3" @click="goEmotion">
        <view class="ic-box"><xt-icon name="i-heart" :size="16" /></view>
        <view class="tx">
          <text class="n">记下今天的心情</text>
          <text class="m">大约 1 分钟 · 写完她会说一句话</text>
        </view>
        <view class="ck">✓</view>
      </view>

      <!-- 她看见你的变化 -->
      <view class="change">
        <view class="ch-top">
          <text class="ch-t">她看见你的变化</text>
          <text class="ch-badge">第 {{ weekNo }} 周</text>
        </view>
        <view class="ch-p">
          今天完成了 <text class="num">{{ summary.todayCompleted || 0 }}</text> 件小事，已经连续陪伴
          <text class="num">{{ companionDays }}</text> 天。
        </view>
        <view class="ch-bottom">
          <view class="spark">
            <view
              v-for="(h, i) in barHeights"
              :key="'bar-' + i"
              class="bar"
              :class="{ hi: i === activeBars - 1 }"
              :style="{ height: h + 'px' }"
            ></view>
          </view>
          <view class="ch-num"><text class="b">{{ companionDays }}</text><text class="u"> 天连续</text></view>
        </view>
      </view>

      <!-- 世界入口 -->
      <view class="world-row">
        <view class="w dark" @click="goWorld">
          <view class="icbox"><xt-icon name="i-world" :size="14" /></view>
          <view class="tx">
            <text class="n">星轨小筑</text>
            <text class="m">她在那儿等你</text>
          </view>
        </view>
        <view class="w" @click="goNotes">
          <view class="icbox"><xt-icon name="i-spark" :size="14" /></view>
          <view class="tx">
            <text class="n">Bot 记忆</text>
            <text class="m">她的分身记得的事</text>
          </view>
        </view>
      </view>

      <!-- 底部快捷：V7 纸感 2x2 卡片 -->
      <view class="v7-quick-grid">
        <view class="v7-qcard" @click="goMemory">
          <view class="v7-qic v7-tic-brain"><xt-icon name="i-brain" :size="16" /></view>
          <view class="v7-qtx">
            <text class="v7-qn">她的记忆</text>
            <text class="v7-qm">三层都记得</text>
          </view>
        </view>
        <view class="v7-qcard" @click="goFocus">
          <view class="v7-qic v7-tic-focus"><xt-icon name="i-focus" :size="16" /></view>
          <view class="v7-qtx">
            <text class="v7-qn">一起专注</text>
            <text class="v7-qm">她陪着你</text>
          </view>
        </view>
        <view class="v7-qcard" @click="goMeditation">
          <view class="v7-qic v7-tic-moon"><xt-icon name="i-moon" :size="16" /></view>
          <view class="v7-qtx">
            <text class="v7-qn">正念</text>
            <text class="v7-qm">放松一下</text>
          </view>
        </view>
        <view class="v7-qcard" @click="goGrowth">
          <view class="v7-qic v7-tic-grow"><xt-icon name="i-archive" :size="16" /></view>
          <view class="v7-qtx">
            <text class="v7-qn">她的成长</text>
            <text class="v7-qm">本周报告</text>
          </view>
        </view>
      </view>
    </view>

    <global-ai-assistant />
    <v7-tabbar active="home" />
  </view>
</template>

<script>
import statsApi from '@/api/stats'
import habitApi from '@/api/habit'
import { CHARACTERS, STYLE_LABELS, getCharacterById, getRandomPhrase } from '@/common/ai-characters'
import { getDailyQuote } from '@/common/ai-dialogue-engine'
import { getInactivityDialogue } from '@/common/walk-map-config.js'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import V7Tabbar from '@/components/v7-tabbar/v7-tabbar.vue'
import { toAvatarUrl } from '@/common/request'
import api from '@/api/newfunc'
import { getActivePartner, getPartnerPhoto, getSwitchablePartners, saveActivePartner } from '@/common/ai-partner'

export default {
  components: { XtIcon, V7Tabbar },
  data() {
    return {
      summary: {
        streakDays: 0,
        bestStreak: 0,
        todayCompleted: 0,
        todayTotal: 0,
        completionRate: 0,
        totalHabits: 0,
        totalCheckins: 0
      },
      barHeights: [8, 13, 18, 11, 21, 24, 15],
      habits: [],
      habitBusy: false
    }
  },
  computed: {
    // 连续陪伴天数：优先用后端真实陪伴统计（companion_records 去重日期）
    // 兼容旧缓存/旧接口：缺失时回落到 streakDays，避免首页出现 undefined
    companionDays() {
      const v = this.summary ? this.summary.companionDays : undefined
      return typeof v === 'number' ? v : (this.summary.streakDays || 0)
    },
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
    userAvatar() {
      return toAvatarUrl(this.$store.state.userInfo.avatar || '')
    },
    /* V7 纸感手帐：日期行 / 短问候 / 用户名 */
    dateLine() {
      const d = new Date()
      const weeks = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
      return `${weeks[d.getDay()]} · ${d.getMonth() + 1} 月 ${d.getDate()} 日`
    },
    greetShort() {
      const h = new Date().getHours()
      if (h < 6) return '夜深了'
      if (h < 11) return '早上好'
      if (h < 14) return '中午好'
      if (h < 18) return '下午好'
      return '晚上好'
    },
    nickname() {
      return this.$store.state.userInfo.nickname || '朋友'
    },
    currentCharacter() {
      // 统一从 store 校正后的伙伴读取（含自定义/扭蛋角色），不再只查预设表
      return getActivePartner()
    },
    heroPhoto() {
      // 主视觉使用完整立绘，在容器内等比显示，不裁头、不拉伸
      return getPartnerPhoto(this.currentCharacter)
    },
    styleLabel() {
      return STYLE_LABELS[this.currentCharacter.style] || '温柔'
    },
    affectionProgress() {
      return this.$store.getters.affectionProgress || 0
    },
    railRoles() {
      // 切换轨用完整立绘（方框全身），与角色卡保持同一套形象
      return getSwitchablePartners(4).map(p => ({ ...p, photo: getPartnerPhoto(p) || p.photo }))
    },
    moreCount() {
      const total = CHARACTERS.length + ((this.$store.state.customCharacters || []).length)
      return Math.max(total - this.railRoles.length, 0)
    },
    weekNo() {
      return Math.max(Math.ceil((this.companionDays || 0) / 7), 1)
    },
    activeBars() {
      return Math.min(this.summary.todayCompleted || 0, 7)
    },
    aiGreeting() {
      try {
        return getRandomPhrase(this.currentCharacter.id, 'morning')
      } catch (e) {
        console.error('获取问候语失败:', e)
        return '你好呀~'
      }
    },
    aiAvatar() {
      return this.currentCharacter.avatar || '🌿'
    },
    dailyQuote() {
      return getDailyQuote()
    },
    habitDoneCount() {
      return this.habits.filter(h => h.completed).length
    }
  },
  onShow() {
    try {
      uni.hideTabBar({ animation: false, fail: () => {} })
    } catch (e) {}
    this.loadSummary()
    this.loadHabits()
    this.checkInactivity()
  },
  onPullDownRefresh() {
    this.loadSummary().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  methods: {
    async loadSummary() {
      try {
        const res = await statsApi.getSummary()
        const summaryData = res.data || res
        if (summaryData && typeof summaryData === 'object') {
          this.summary = summaryData
          this.$store.commit('setStreakDays', summaryData.streakDays || summaryData.current_streak || 0)
          // 【修复】用服务端累计打卡数校准行走地图计数，避免老用户/换设备后一直显示 0
          this.$store.commit('setWalkTotalCheckins', summaryData.totalCheckins || 0)
        }
      } catch (e) {
        console.error('加载统计数据失败', e)
      }
    },
    /** 今日习惯列表（只读展示 + 支持点选打卡） */
    async loadHabits() {
      try {
        const res = await habitApi.getAllHabits()
        const list = (res && res.data) || []
        this.habits = Array.isArray(list) ? list : []
      } catch (e) {
        console.error('加载习惯失败', e)
      }
    },
    /** 点选习惯：未完成则打卡，已完成则取消 */
    async toggleHabit(h) {
      if (this.habitBusy) return
      this.habitBusy = true
      try {
        const res = h.completed
          ? await habitApi.uncheckin(h.id)
          : await habitApi.checkin(h.id)
        if (res && res.code && res.code !== 200) {
          throw new Error(res.message || '操作失败')
        }
        h.completed = h.completed ? 0 : 1
        if (h.completed) {
          // 与日程页保持一致：打卡推进行走地图
          this.$store.commit('addWalkStep', {
            steps: 1, type: 'habit', description: `完成习惯：${h.name}`
          })
        }
        uni.showToast({ title: h.completed ? '打卡成功' : '已取消打卡', icon: 'none' })
        this.loadSummary()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '操作失败', icon: 'none' })
      } finally {
        this.habitBusy = false
      }
    },
    checkInactivity() {
      const inactivityDays = this.$store.getters.walkInactivityDays
      if (inactivityDays >= 3) {
        const characterId = this.currentCharacter.id
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
    goChat() {
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    goStats() {
      uni.navigateTo({ url: '/pages/stats/stats' })
    },
    goEmotion() {
      uni.navigateTo({ url: '/pages/emotion/emotion' })
    },
    goFocus() {
      uni.navigateTo({ url: '/pages/focus/focus-home' })
    },
    goMeditation() {
      uni.navigateTo({ url: '/pages/meditation/meditation' })
    },
    goGallery() {
      uni.navigateTo({ url: '/pages/character-gallery/character-gallery' })
    },
    goWorld() {
      uni.navigateTo({ url: '/pages/world/world' })
    },
    async goNotes() {
      // 修复：记忆是和某个伙伴一对一的，必须带 bot_id。
      // 0 个伙伴 → 引导去创建；1 个 → 直达她的记忆；多个 → 先去伙伴管理选一个。
      try {
        const res = await api.botList()
        const bots = (res && res.data && res.data.list) || []
        if (!bots.length) {
          uni.showToast({ title: '还没有 AI 伙伴，先去创建一个吧', icon: 'none' })
          uni.navigateTo({ url: '/pages/newfunc/bot-manage' })
          return
        }
        if (bots.length === 1) {
          uni.navigateTo({
            url: `/pages/newfunc/bot-memory?id=${bots[0].id}&name=${encodeURIComponent(bots[0].name)}`
          })
          return
        }
        uni.navigateTo({ url: '/pages/newfunc/bot-manage' })
      } catch (e) {
        uni.navigateTo({ url: '/pages/newfunc/bot-manage' })
      }
    },
    goMemory() {
      uni.navigateTo({ url: '/pages/memory/memory' })
    },
    goGrowth() {
      uni.navigateTo({ url: '/pages/growth-archive/growth-archive' })
    },
    switchRole(id) {
      if (!id || id === this.currentCharacter.id) return
      const character = getCharacterById(id)
      const saved = saveActivePartner(id, character?.name || '')
      if (!saved) return
      uni.showToast({ title: `已切换为${saved.name}`, icon: 'none', duration: 1200 })
    }
  }
}
</script>

<style scoped>
/* ===== V7 纸感手帐 · 首页 ===== */
.v7-home {
  min-height: 100vh;
  background:
    radial-gradient(420px 300px at 88% -4%, rgba(196, 205, 189, 0.24), transparent 62%),
    radial-gradient(380px 320px at 4% 102%, rgba(228, 211, 187, 0.22), transparent 60%),
    #f8f4ec;
  color: #18231d;
}
.v7-body {
  padding: 10px 17px calc(92px + env(safe-area-inset-bottom));
}

/* 关系状态条 */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 2px 10px;
}
.tb-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tb-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #44705a;
}
.tb-t {
  font-size: 10px;
  color: #6a776e;
  letter-spacing: 0.2px;
}
.tb-r {
  display: flex;
  gap: 6px;
}
.tb-ib {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 253, 250, 0.8);
  border: 1px solid rgba(30, 42, 36, 0.1);
}

/* 角色切换轨 */
.rail {
  display: flex;
  gap: 10px;
  padding: 0 2px 12px;
  overflow-x: auto;
  scrollbar-width: none;
}
.rail::-webkit-scrollbar { display: none; }
.rail-role {
  flex: 0 0 auto;
  width: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
/* 方框立绘：3:4 比例随屏宽等比缩放，完整展示人物而不是只裁头部 */
.rail-av,
.rail-more {
  width: 100%;
  height: auto;
  aspect-ratio: 3 / 4;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #efe9dd;
  border: 1.5px solid transparent;
}
.rail-av image,
.rail-av uni-image,
.rail-av :deep(uni-image > div),
.rail-av :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.rail-fb {
  font-size: 14px;
  color: #6a776e;
}
.rail-role.on .rail-av {
  border-color: #24493a;
}
.rail-more {
  border: 1px dashed rgba(30, 42, 36, 0.24);
  font-size: 11px;
  font-weight: 800;
  color: #24493a;
  background: transparent;
}
.rail-name {
  font-size: 8.5px;
  color: #6a776e;
  max-width: 50px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rail-role.on .rail-name {
  color: #24493a;
  font-weight: 800;
}

/* 立绘 */
.hero {
  position: relative;
  height: 206px;
  border-radius: 24px;
  overflow: hidden;
  background: #ede7da;
}
.hero-img {
  position: absolute;
  right: 4px;
  top: 0;
  width: 46%;
  height: 100%;
  background-size: contain;
  background-position: 100% 50%;
  background-repeat: no-repeat;
}
.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    100deg,
    rgba(245, 242, 234, 0.97) 0%,
    rgba(245, 242, 234, 0.88) 42%,
    rgba(245, 242, 234, 0) 76%
  );
}
.hero-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(140deg, #acc2b8, #44705a);
}
.hero-emoji { font-size: 56px; }
.hero-tx {
  position: relative;
  z-index: 3;
  padding: 17px 16px;
  width: 72%;
}
.lb {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 8px;
  font-weight: 800;
  color: #7c5a33;
  background: rgba(255, 253, 250, 0.7);
  padding: 4px 9px;
  border-radius: 99px;
}
.lb .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #b2793f;
}
.ttl {
  margin-top: 11px;
  font-size: 17px;
  line-height: 1.5;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
  font-weight: 700;
  letter-spacing: -0.4px;
}
.hp {
  margin-top: 7px;
  font-size: 9px;
  line-height: 1.75;
  color: #68746c;
}
.go {
  margin-top: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 9.5px;
  font-weight: 900;
  color: #24493a;
}
.hero-score {
  position: absolute;
  right: 13px;
  bottom: 13px;
  z-index: 4;
  padding: 6px 10px;
  border-radius: 12px;
  background: rgba(255, 253, 250, 0.78);
  border: 1px solid rgba(30, 42, 36, 0.08);
  text-align: right;
}
.hero-score .v {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: #24493a;
}
.hero-score .k {
  display: block;
  margin-top: 1px;
  font-size: 7.5px;
  color: #6a776e;
}

/* 三格数据 */
.stat3 {
  display: flex;
  gap: 9px;
  margin-top: 10px;
}
.stat3 .c {
  flex: 1;
  padding: 11px 12px;
  border-radius: 17px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 18px 34px -30px rgba(24, 35, 29, 0.5);
}
.stat3 .b {
  display: block;
  font-size: 16px;
  font-weight: 900;
  color: #24493a;
}
.stat3 .c:nth-child(2) .b { color: #b2793f; }
.stat3 .l {
  display: block;
  margin-top: 3px;
  font-size: 7.5px;
  color: #a2aaa3;
}

/* 小节标题 */
.sect {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 15px 2px 8px;
}
.sect .h { font-size: 12px; font-weight: 900; }
.sect .s { font-size: 8px; color: #a2aaa3; }

/* 今天只剩一件 */
.task3 {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 18px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 18px 34px -30px rgba(24, 35, 29, 0.5);
}
.task3 .ic-box {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: #f7ede1;
  color: #24493a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.task3 .tx { flex: 1; min-width: 0; }
.task3 .n {
  display: block;
  font-size: 10.5px;
  font-weight: 800;
}
.task3 .m {
  display: block;
  margin-top: 3px;
  font-size: 8px;
  color: #a2aaa3;
}
.task3 .ck {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: #24493a;
  color: #fffdfa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}

/* 她看见你的变化 */
.change {
  margin-top: 12px;
  padding: 13px 14px;
  border-radius: 19px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 18px 34px -30px rgba(24, 35, 29, 0.5);
}
.ch-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ch-t {
  font-size: 10.5px;
  font-weight: 900;
  color: #18231d;
}
.ch-badge {
  font-size: 8px;
  font-weight: 800;
  color: #8a6231;
  background: rgba(178, 121, 63, 0.12);
  padding: 3px 8px;
  border-radius: 99px;
}
.ch-p {
  margin-top: 8px;
  font-size: 9.5px;
  line-height: 1.75;
  color: #6a776e;
}
.ch-p .num {
  font-size: 11px;
  font-weight: 900;
  color: #24493a;
}
.ch-bottom {
  margin-top: 10px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}
.spark {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 26px;
}
.spark .bar {
  width: 7px;
  border-radius: 3px;
  background: #dfe5da;
}
.spark .bar.hi {
  background: #24493a;
}
.ch-num .b {
  font-size: 16px;
  font-weight: 900;
  color: #24493a;
}
.ch-num .u {
  font-size: 8px;
  color: #a2aaa3;
}

/* 世界入口 */
.world-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 10px;
}
.world-row .w {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px;
  border-radius: 15px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
}
.world-row .w.dark {
  background: #22302a;
  border-color: #22302a;
}
.world-row .icbox {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0ece1;
  flex-shrink: 0;
}
.world-row .dark .icbox {
  background: rgba(255, 255, 255, 0.12);
}
.world-row .n {
  display: block;
  font-size: 10px;
  font-weight: 900;
  color: #18231d;
}
.world-row .m {
  display: block;
  margin-top: 2px;
  font-size: 7.5px;
  color: #a2aaa3;
}
.world-row .dark .n { color: #f6f2e8; }
.world-row .dark .m { color: #b9c4bc; }

/* 快捷：V7 纸感 2x2 卡片网格 */
.v7-quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin: 16px 0 0;
}
.v7-qcard {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 10px;
  background: #FFFDFA;
  border-radius: 15px;
  box-shadow: 0 12px 26px -22px rgba(34,48,42,.55), inset 0 0 0 1px var(--v7-line);
}
.v7-qic {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.v7-tic-brain { background: #EEF2EA; color: var(--v7-green); }
.v7-tic-focus { background: #EEF2F4; color: #557786; }
.v7-tic-moon { background: #F4EFE4; color: #96814F; }
.v7-tic-grow { background: #F3EFE5; color: #3C6B55; }
.v7-qtx { flex: 1; min-width: 0; }
.v7-qn {
  display: block;
  font-size: 12px;
  font-weight: 800;
  color: #22302A;
  line-height: 1.2;
}
.v7-qm {
  display: block;
  margin-top: 2px;
  font-size: 9px;
  color: #AEB6AE;
  line-height: 1.2;
}

/* ===== 视觉精修（增量追加，不改上方任何规则） ===== */
.stat3 .c,
.task3,
.world-row .w,
.v7-qcard,
.rail-role,
.hero {
  -webkit-tap-highlight-color: transparent;
}
.stat3 .c,
.task3,
.world-row .w,
.v7-qcard,
.rail-role {
  transition: transform .18s cubic-bezier(.32, .72, .2, 1), box-shadow .18s ease;
}
.stat3 .c:active,
.task3:active,
.world-row .w:active,
.v7-qcard:active,
.rail-role:active {
  transform: scale(.97);
}
/* 小屏防挤压：360px 以下收紧横向留白与三格间距 */
@media (max-width: 360px) {
  .v7-body { padding-left: 14px; padding-right: 14px; }
  .stat3 { gap: 7px; }
  .stat3 .c { padding: 10px 9px; }
  .stat3 .b { font-size: 15px; }
  .v7-qcard { gap: 8px; padding: 10px 9px; }
}

/* 今日习惯打卡（首页内联，样式与 stat3 卡片保持一致） */
.hb-card {
  margin-top: 10px;
  padding: 12px;
  border-radius: 17px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 18px 34px -30px rgba(24, 35, 29, 0.5);
}
.hb-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 4px;
}
.hb-t { font-size: 11px; font-weight: 900; color: #24493a; }
.hb-s { font-size: 8px; color: #a2aaa3; }
.hb-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-top: 1px dashed rgba(30, 42, 36, 0.08);
}
.hb-ic {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  border: 1px solid rgba(30, 42, 36, 0.22);
  color: #a2aaa3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  flex-shrink: 0;
}
.hb-ic.is-done { background: #24493a; border-color: #24493a; color: #fffdfa; }
.hb-tx { flex: 1; min-width: 0; }
.hb-n { font-size: 10.5px; font-weight: 800; color: #1e2a24; }
.hb-n.is-done { color: #b6bcb7; text-decoration: line-through; }
.hb-m { display: block; margin-top: 2px; font-size: 8px; color: #a2aaa3; }
</style>
