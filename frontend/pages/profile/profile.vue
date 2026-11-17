<template>
  <view class="xt-page xt-s5">
    <view class="body">
      <view class="mep-hero">
        <view class="mep-bg"></view>
        <text class="mep-lv" @click="goVip">LV.{{ level }} · 同行者</text>
        <view class="mep-row">
          <view class="mep-av" @click="changeAvatar">
            <image v-if="userAvatar" :src="userAvatar" mode="aspectFill" />
            <text v-else class="mep-av-t">{{ userInitial }}</text>
            <i>{{ level }}</i>
          </view>
          <view class="mep-info">
            <view class="mep-name">{{ userInfo.nickname || '循途用户' }}</view>
            <view class="mep-sub">与 <b>{{ currentAiName }}</b> 相伴的第 {{ partnerDays }} 天</view>
          </view>
          <view class="mep-edit" @click="goEditProfile"><xt-icon name="i-edit" /></view>
        </view>
        <view class="mep-stats">
          <view><b>{{ stats.totalCheckins }}</b><span>累计打卡</span></view>
          <view><b>{{ stats.totalDays }}</b><span>连续天数</span></view>
          <view><b>{{ stats.badgeCount }}</b><span>获得徽章</span></view>
        </view>
        <view class="mep-week">
          <view class="wh"><b>最近 7 天</b><span>{{ weekDone }} / 7 天完成</span></view>
          <view class="wb"><i v-for="(c, i) in weekBars" :key="i" :class="c"></i></view>
          <view class="wd">
            <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span>
          </view>
        </view>
      </view>

      <view class="mep-bond" @click="goMemory">
        <image v-if="aiPhoto" :src="aiPhoto" mode="aspectFill" />
        <view v-else class="mep-bond-fb"><text>{{ currentAiAvatar }}</text></view>
        <view class="tx">
          <view class="t">{{ currentAiName }} <em>{{ styleLabel }}</em></view>
          <view class="bar"><i :style="{ width: bondPercent + '%' }"></i></view>
          <view class="m">默契 {{ bondPercent }}% · 她的记忆</view>
        </view>
        <span class="ar"><xt-icon name="i-right" /></span>
      </view>

      <view class="mep-sec"><b>我的伙伴</b><span @click="showAiRoles">{{ partnerTotal }} 位可切换 ›</span></view>
      <view class="mep-ps">
        <view
          v-for="p in railPartners"
          :key="p.id"
          class="mep-p"
          :class="{ on: p.id === currentAiKey }"
          @click="switchRole(p)"
        >
          <span class="pav">
            <image v-if="p.photo" :src="p.photo" mode="aspectFill" />
            <text v-else class="pav-t">{{ p.avatar }}</text>
          </span>
          <span>{{ p.name }}</span>
        </view>
        <view class="mep-p" @click="showAiRoles">
          <span class="mep-more">+{{ moreRoles }}</span>
          <span>全部</span>
        </view>
      </view>

      <view class="mep-sec"><b>最近的成长</b><span @click="showAllBadges">全部徽章 ›</span></view>
      <view class="mep-bs">
        <view
          v-for="(b, i) in recentBadges"
          :key="i"
          class="mep-b"
          :class="{ lock: !b.unlocked }"
          @click="showBadgeDetail(b)"
        >
          <span class="bi" :class="b.unlocked ? b.tint : ''"><xt-icon :name="b.ic" /></span>
          <view class="bn">{{ b.name }}</view>
          <view class="bd">{{ b.unlocked ? '已获得' : '进行中' }}</view>
        </view>
      </view>

      <view class="mep-sec"><b>更多</b></view>
      <view class="mep-mu">
        <view class="mep-r" @click="goRecords">
          <span class="mep-ri s"><xt-icon name="i-edit" /></span>
          <span class="mep-rt">我的记录</span><span class="mep-rv">{{ recordCount }} 条</span>
          <span class="ar"><xt-icon name="i-right" /></span>
        </view>
        <view class="mep-r" @click="go('growth-archive')">
          <span class="mep-ri b"><xt-icon name="i-archive" /></span>
          <span class="mep-rt">成长档案</span><span class="mep-rv">{{ partnerDays }} 天的记录</span>
          <span class="ar"><xt-icon name="i-right" /></span>
        </view>
        <view class="mep-r" @click="goSettings">
          <span class="mep-ri s"><xt-icon name="i-settings" /></span>
          <span class="mep-rt">设置与提醒</span>
          <span class="ar"><xt-icon name="i-right" /></span>
        </view>
        <view class="mep-r" @click="showAbout">
          <span class="mep-ri g"><xt-icon name="i-heart" /></span>
          <span class="mep-rt">关于循途</span><span class="mep-rv">V1.0</span>
          <span class="ar"><xt-icon name="i-right" /></span>
        </view>
        <view class="mep-r" @click="goVip">
          <span class="mep-ri b"><xt-icon name="i-spark" /></span>
          <span class="mep-rt">会员中心</span><span class="mep-rv">{{ vipBadge }}</span>
          <span class="ar"><xt-icon name="i-right" /></span>
        </view>
      </view>

      <view class="mep-logout" @click="handleLogout">退出登录</view>
    </view>
    <v7-tabbar active="profile" />
  </view>
</template>

<script>
import authApi from '@/api/auth'
import userApi from '@/api/user'
import statsApi from '@/api/stats'
// ↓↓↓ 新增 ↓↓↓ 统一拼头像地址（相对路径/后端硬编码 IP 都能处理）
import { toAvatarUrl } from '@/common/request'
// ↓↓↓ 新增 ↓↓↓
import { getVipStatus } from '@/common/wx-vip-api'
// ↑↑↑ 新增结束 ↑↑↑
// ↓↓↓ 新增（2026-10-27 角色体系统一）：AI 角色切换改用 20 个具名角色 ↓↓↓
import { getAllCharacters, getCharacterById, STYLE_LABELS } from '@/common/ai-characters'
import { getActivePartner, getActivePartnerId, getPartnerPhoto, getPickedPartnerId, getSwitchablePartners, saveActivePartner } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import V7Tabbar from '@/components/v7-tabbar/v7-tabbar.vue'
// ↑↑↑ 新增结束 ↑↑↑

export default {
  components: { XtIcon, V7Tabbar },
  data() {
    return {
      userInfo: {},
      badges: [],
      aiRoles: [],
      // 【2026-10-27】roleType 存的是 8 种 style（relaxed/y2k/...），id 才是角色标识（'linxi'）
      currentAiRole: { id: 'linxi', roleType: 'relaxed', name: '林夕', avatar: '🌿' },
      settings: {
        notificationEnabled: true,
        ttsEnabled: true
      },
      // ↓↓↓ 新增 ↓↓↓
      vipBadge: '',
      // ↓↓↓ 安全合规批次 ↓↓↓ 青少年模式（控制VIP入口显隐）
      teenMode: false,
      // ↑↑↑ 新增结束 ↑↑↑
      stats: {
        totalDays: 12,
        totalCheckins: 26,
        badgeCount: 3
      },
      recordCount: 0
    }
  },
  computed: {
    userInitial() {
      const name = this.userInfo.nickname || '用户'
      return name.charAt(0)
    },
    // ↓↓↓ 新增 ↓↓↓ 优先用云端头像数据双方并集里的 avatar
    userAvatar() {
      return this.resolveAvatar(this.userInfo)
    },
    currentAiAvatar() {
      // 统一从 ai-partner 读取，支持自定义伙伴（emoji/上传头像）
      const p = getActivePartner()
      return (p && p.avatar) || this.currentAiRole.avatar || '🌿'
    },
    currentAiName() {
      const p = getActivePartner()
      return this.$store.state.aiConfig.name || (p && p.name) || this.currentAiRole.name || 'AI伙伴'
    },
    // === 好感度（对标循途关系系统）：宝物使用/打卡互动累积 ===
    affectionValue() {
      return this.$store.getters.affectionValue || 0
    },
    affectionTierName() {
      return this.$store.getters.affectionTierName || '初识'
    },
    affectionProgress() {
      return this.$store.getters.affectionProgress || 0
    },
    // ↓↓↓ 设计稿 s5 我的页所需展示数据 ↓↓↓
    currentAiKey() {
      return getActivePartnerId()
    },
    aiPhoto() {
      // 关系卡展示完整立绘（方框全身构图），不再用只剩头部的特写
      return getPartnerPhoto(getActivePartner())
    },
    styleLabel() {
      const c = getCharacterById(this.currentAiKey)
      const k = c && c.style
      return (k && STYLE_LABELS && STYLE_LABELS[k]) || '治愈系'
    },
    level() {
      return Math.max(1, Math.floor((this.stats.totalCheckins || 0) / 7) + 1)
    },
    partnerDays() {
      return this.stats.totalDays || this.$store.state.streakDays || 1
    },
    bondPercent() {
      const v = Number(this.affectionProgress) || 0
      return Math.max(8, Math.min(100, Math.round(v)))
    },
    weekDone() {
      return Math.min(7, Math.max(0, Math.round(this.bondPercent / 100 * 7)))
    },
    weekBars() {
      return [0, 1, 2, 3, 4, 5, 6].map(i => (i < this.weekDone ? 'l2' : i === 6 ? 'td' : 'l1'))
    },
    railPartners() {
      // 当前伙伴 + 其他可切换伙伴（含自定义），头像与首页同源
      return getSwitchablePartners(4).map(p => ({
        id: p.id,
        name: p.name,
        avatar: p.avatar,
        photo: getPartnerPhoto(p) || p.photo || ''
      }))
    },
    moreRoles() {
      const total = getAllCharacters().length + ((this.$store.state.customCharacters || []).length)
      return Math.max(0, total - this.railPartners.length)
    },
    partnerTotal() {
      return getAllCharacters().length + ((this.$store.state.customCharacters || []).length)
    },
    recentBadges() {
      const icons = ['i-spark', 'i-moon', 'i-water']
      const tints = ['g', 'b', 's']
      const list = this.badges.length
        ? this.badges
        : [
            { name: '坚持 7 天', unlocked: false },
            { name: '早睡 3 天', unlocked: false },
            { name: '温柔回应', unlocked: false }
          ]
      return list.slice(0, 3).map((b, i) => ({
        ...b,
        ic: icons[i] || 'i-spark',
        tint: tints[i] || 'g'
      }))
    }
    // ↑↑↑ 新增结束 ↑↑↑
  },
  // ↓↓↓ 新增（2026-10-27）：监听角色选择页回传 ↓↓↓
  onLoad() {
    uni.$on('roleSelected', this.onRoleSelected)
  },
  onUnload() {
    uni.$off('roleSelected', this.onRoleSelected)
  },
  // ↑↑↑ 新增结束 ↑↑↑
  onShow() {
    // ↓↓↓ 安全合规批次：青少年模式读取（控制VIP入口显隐） ↓↓↓
    try {
      this.teenMode = uni.getStorageSync('pref_teen_mode') === 'true'
    } catch (e) { this.teenMode = false }
    // ↑↑↑ 新增结束 ↑↑↑

    this.loadData()
    // ↓↓↓ 新增 ↓↓↓
    this.loadVipBadge()
    // ↑↑↑ 新增结束 ↑↑↑
    // 「+ 记录今天」写在本地存储里的条数（我的记录入口展示）
    try {
      const records = uni.getStorageSync('create_records') || []
      this.recordCount = Array.isArray(records) ? records.length : 0
    } catch (e) {
      this.recordCount = 0
    }
    try {
      uni.hideTabBar({ animation: false, fail: () => {} })
    } catch (e) {}
  },
  methods: {
    /**
     * ↓↓↓ 新增 ↓↓↓
     * 把用户对象里的头像字段解析成可直接给 <image src> 用的地址。
     * blob:/wxfile:// 这类本地临时地址刷新即失效，一律按无头像处理，回退到首字母占位。
     */
    resolveAvatar(user) {
      return toAvatarUrl((user && user.avatar) || '')
    },
    async loadData() {
      try {
        const [userRes, badgeRes, summaryRes] = await Promise.all([
          userApi.getUserInfo(),
          userApi.getBadges(),
          statsApi.getSummary()
        ])
        if (userRes.code === 200) {
          const storeUser = this.$store.state.userInfo || {}
          // ↓↓↓ 修复 ↓↓↓ 原来是 { ...userRes.data, ...storeUser }，store 写在后面会反过来覆盖云端数据，
          // 结果在 profile-edit 改完的资料回到本页又被本地旧值盖回去。现在云端为准，store 只补缺失字段。
          const mergedUser = { ...storeUser, ...userRes.data }
          // 云端存的是相对路径（avatar/xxx.png），store 里可能是完整 URL，统一归一化成可直接用的地址
          mergedUser.avatar = this.resolveAvatar(userRes.data) || this.resolveAvatar(storeUser)
          this.userInfo = mergedUser
          this.$store.commit('setUserInfo', mergedUser)
        }
        if (badgeRes.code === 200) {
          this.badges = badgeRes.data
          this.stats.badgeCount = badgeRes.data.filter(b => b.unlocked).length
        }
        if (summaryRes.code === 200) {
          this.stats.totalCheckins = summaryRes.data.totalCheckins || 0
          this.stats.totalDays = summaryRes.data.streakDays || 0
        }
      } catch (e) {
        this.userInfo = this.$store.state.userInfo
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '最近'
      const d = new Date(dateStr)
      return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
    },
    // ↓↓↓ 修复 ↓↓↓ 原来只弹 toast 说「开发中」，点头像没法进编辑页
    changeAvatar() {
      uni.navigateTo({
        url: '/pages/profile-edit/profile-edit',
        fail: () => {
          uni.showToast({ title: '编辑页面暂不可用', icon: 'none' })
        }
      })
    },
    // ↓↓↓ 陪伴感增强 v3 ↓↓↓ 记忆管理页（查看 / 单条删除 / 一键清空，按角色隔离）
    goMemory() {
      const key = (this.$store.state.aiConfig && this.$store.state.aiConfig.avatarType) || ''
      uni.navigateTo({
        url: '/pages/memory/memory' + (key ? '?roleKey=' + encodeURIComponent(key) : ''),
        fail: () => {
          uni.showToast({ title: '记忆页面暂不可用', icon: 'none' })
        }
      })
    },
    // ↑↑↑ 新增结束 ↑↑↑
    showAllBadges() {
      // ↓↓↓ 改造（2026-10-27）：原来只有一句 toast，现在跳真正的徽章全量页 ↓↓↓
      uni.navigateTo({ url: '/pages/badge/badge' })
      // ↑↑↑ 改造结束 ↑↑↑
    },
    showBadgeDetail(badge) {
      const status = badge.unlocked ? `已解锁\n解锁时间: ${this.formatDate(badge.unlockedAt)}` : '未解锁'
      uni.showModal({
        title: `${badge.icon} ${badge.name}`,
        content: `${badge.description}\n${status}`,
        showCancel: false,
        confirmText: '知道了'
      })
    },
    /**
     * ↓↓↓ 改造（2026-10-27） ↓↓↓
     * 原实现：从 /chat/personas 取 ai_roles 的 4 个人格，用 uni.showActionSheet 选。
     * 两个问题：
     *   1) 20 个具名角色塞不进 ActionSheet（uni 限制最多 6 项）；
     *   2) 把 selected.roleType（cute/gentle…）写进 aiConfig.avatarType，而全项目都拿
     *      avatarType 当 ai-characters.js 的角色 id 用 getCharacterById() 查，结果永远
     *      查不到、静默回退林夕。
     * 现改为跳角色选择页（与陪伴同源的 20 个具名角色），通过全局事件回传。
     */
    showAiRoles() {
      uni.navigateTo({ url: '/pages/role-select/role-select' })
    },
    /** 接收角色选择页的回传（uni.$emit('roleSelected')） */
    onRoleSelected(role) {
      if (!role || !role.id) return
      const saved = saveActivePartner(role.roleKey || role.id, role.name)
      if (!saved) return
      this.currentAiRole = {
        id: saved.id,
        roleType: saved.style || role.roleType || 'relaxed',
        name: saved.name,
        avatar: saved.avatar
      }
      uni.showToast({ title: `已切换为${saved.name}`, icon: 'none' })
    },
    // ↑↑↑ 改造结束 ↑↑↑
    async toggleNotification() {
      this.settings.notificationEnabled = !this.settings.notificationEnabled
      this.$store.commit('setSettings', this.settings)
      try {
        await userApi.updateSettings(this.settings)
      } catch (e) {
        // silent
      }
      uni.showToast({
        title: this.settings.notificationEnabled ? '已开启通知' : '已关闭通知',
        icon: 'none'
      })
    },
    async toggleTts() {
      this.settings.ttsEnabled = !this.settings.ttsEnabled
      this.$store.commit('setSettings', this.settings)
      try {
        await userApi.updateSettings(this.settings)
      } catch (e) {
        // silent
      }
      uni.showToast({
        title: this.settings.ttsEnabled ? '已开启语音' : '已关闭语音',
        icon: 'none'
      })
    },
    goEditProfile() {
      uni.navigateTo({ url: '/pages/profile-edit/profile-edit' })
    },
    // ↓↓↓ 新增：VIP 入口 ↓↓↓
    goVip() {
      uni.navigateTo({ url: '/pages/vip/index' })
    },
    async loadVipBadge() {
      try {
        const res = await getVipStatus()
        this.vipBadge = res && res.isVip ? `剩余 ${res.remainDays} 天` : '立即开通'
      } catch (e) {
        this.vipBadge = '立即开通'
      }
    },
    // ↑↑↑ 新增结束 ↑↑↑
    goSettings() {
      uni.navigateTo({ url: '/pages/settings/settings' })
    },
    /** 设计稿 s5：通用跳转（成长档案等） */
    go(key) {
      const map = {
        'growth-archive': '/pages/growth-archive/growth-archive'
      }
      if (map[key]) uni.navigateTo({ url: map[key] })
    },
    goRecords() {
      uni.navigateTo({ url: '/pages/records/records' })
    },
    /** 设计稿 s5：我的伙伴快捷切换 */
    switchRole(p) {
      if (!p || p.id === this.currentAiKey) return
      const saved = saveActivePartner(p.id, p.name)
      if (!saved) return
      uni.showToast({ title: `已切换为${saved.name}`, icon: 'none' })
    },
    showAbout() {
      uni.showModal({
        title: '关于循途',
        content: '循途 v1.0.0\n\n无论何时何地，与TA共度每时每刻。\n通过AI陪伴让习惯养成更有趣。\n\n© 2026 循途',
        showCancel: false,
        confirmText: '知道了'
      })
    },
    clearCache() {
      uni.showModal({
        title: '清除缓存',
        content: '确定要清除本地缓存吗？',
        success: (r) => {
          if (r.confirm) {
            try {
              uni.removeStorageSync('ahp_user_state')
              uni.showToast({ title: '缓存已清除', icon: 'success' })
            } catch (e) {
              uni.showToast({ title: '清除失败', icon: 'none' })
            }
          }
        }
      })
    },
    goReQuiz() {
      this.$store.commit('setQuizCompleted', false)
      const picked = getPickedPartnerId()
      const url = picked
        ? `/pages/personality-quiz/personality-quiz?roleId=${encodeURIComponent(picked)}`
        : '/pages/personality-quiz/personality-quiz'
      uni.navigateTo({ url })
    },
    goEmotion() {
      uni.navigateTo({ url: '/pages/emotion/emotion' })
    },
    goMeditation() {
      uni.navigateTo({ url: '/pages/meditation/meditation' })
    },
    handleLogout() {
      uni.showModal({
        title: '退出登录',
        content: '确定要退出登录吗？',
        success: async (r) => {
          if (r.confirm) {
            try {
              await authApi.logout()
            } catch (e) {
              // ignore
            }
            this.$store.commit('resetState')
            uni.showToast({ title: '已退出', icon: 'none' })
            setTimeout(() => {
              uni.reLaunch({ url: '/pages/login/login' })
            }, 800)
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部为悬浮 dock 留出空间 */
.xt-page.xt-s5 .body {
  padding-bottom: calc(90px + env(safe-area-inset-bottom));
}

/* 用户头像：有图用图，无图用首字母 */
.mep-av {
  display: flex;
  align-items: center;
  justify-content: center;
}
.mep-av image,
.mep-av uni-image {
  width: 100%;
  height: 100%;
  display: block;
}
/* 关系卡：方框立绘（3:4 完整构图，不再只露头部） */
.xt-page.xt-s5 .mep-bond uni-image {
  width: 45px;
  height: 60px;
  border-radius: 10px;
  flex-shrink: 0;
  overflow: hidden;
}
.xt-page.xt-s5 .mep-bond :deep(uni-image > div),
.xt-page.xt-s5 .mep-bond :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 10px;
  object-fit: cover;
}
/* 无立绘伙伴回退：与 uni-image 同尺寸，避免布局跳动 */
.xt-page.xt-s5 .mep-bond-fb {
  width: 45px;
  height: 60px;
  border-radius: 10px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  font-size: 20px;
  line-height: 1;
}
/* 我的伙伴：方框立绘缩略（随列宽等比缩放，不裁成圆形头部） */
.xt-page.xt-s5 .mep-p .pav {
  width: 100%;
  height: auto;
  aspect-ratio: 3 / 4;
  border-radius: 10px;
  box-sizing: border-box;
  overflow: hidden;
  background: #EFF3EF;
}
.xt-page.xt-s5 .mep-p .pav uni-image {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 8px;
  overflow: hidden;
}
.xt-page.xt-s5 .mep-p .pav :deep(uni-image > div),
.xt-page.xt-s5 .mep-p .pav :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 8px;
  object-fit: cover;
}
.xt-page.xt-s5 .mep-p > span:last-child {
  font-size: 9px;
  line-height: 1.3;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.xt-page.xt-s5 .mep-more {
  width: 100%;
  height: auto;
  aspect-ratio: 3 / 4;
  border-radius: 10px;
  font-size: 10px;
}
.mep-av-t {
  font-size: 18px;
  font-weight: 900;
  color: var(--v7-green);
}

/* 退出登录（设计稿未包含，保留必要功能） */
.mep-logout {
  margin: 14px 0 6px;
  height: 34px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  color: #A2AAA3;
  background: rgba(255, 253, 250, 0.6);
  box-shadow: inset 0 0 0 1px rgba(34, 48, 42, 0.06);
}

/* ===== 视觉精修（增量追加，不改上方任何规则） ===== */
.mep-bond,
.mep-r,
.mep-p,
.mep-b,
.mep-logout {
  -webkit-tap-highlight-color: transparent;
  transition: transform .18s cubic-bezier(.32, .72, .2, 1), box-shadow .18s ease;
}
.mep-bond:active,
.mep-r:active,
.mep-p:active,
.mep-b:active {
  transform: scale(.97);
}
.mep-logout:active { transform: scale(.98); opacity: .9; }
/* 小屏防挤压 */
@media (max-width: 360px) {
  .xt-page.xt-s5 .body { padding-left: 14px; padding-right: 14px; }
}
</style>
