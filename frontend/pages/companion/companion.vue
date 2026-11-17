<template>
  <view class="xt-page xt-s23">
    <view class="body" style="margin:0 -18px;padding:16px 22px 26px;display:flex;flex-direction:column;align-items:center;color:#fff;background:linear-gradient(170deg,#3D5449 0%,#24322C 48%,#212E28 100%)">
      <!-- 状态行 -->
      <view style="width:100%;display:flex;align-items:center;justify-content:space-between;font-size:8px;color:rgba(255,255,255,.62)">
        <text>陪伴中 · {{ sceneName }}</text>
        <text>{{ soundName }}</text>
      </view>

      <!-- 她在这 -->
      <view
        style="position:relative;margin-top:34px;width:196px;height:196px;border-radius:32px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.05);box-shadow:0 0 0 1px rgba(255,255,255,.14),0 0 0 20px rgba(255,255,255,.03)"
        @click="goRoleSelect"
      >
        <image v-if="rolePhoto" class="hero-photo" :src="rolePhoto" mode="aspectFill" />
        <view v-else class="hero-emoji"><text>{{ role.avatar || '🌿' }}</text></view>
      </view>
      <view style="margin-top:26px;font-size:9px;color:rgba(255,255,255,.55);letter-spacing:1.4px">{{ role.name || '她' }} 在 旁 边</view>

      <text style="margin-top:10px;width:82%;text-align:center;font-size:11px;line-height:1.85;color:rgba(255,255,255,.9)">“{{ proactiveText || '我在。你忙你的，不用管我。' }}”</text>

      <!-- 场景：轻量切换 -->
      <view class="chips" style="margin-top:20px;justify-content:center">
        <view
          v-for="scene in scenes"
          :key="scene.type"
          class="chip"
          :class="{ on: sceneType === scene.type }"
          @click="selectScene(scene)"
        >{{ scene.name }}</view>
      </view>

      <!-- 自定义场景名 -->
      <input
        v-if="sceneType === 'custom'"
        v-model="customSceneName"
        class="custom-scene"
        placeholder="例如：一起看星星、发呆…"
        placeholder-style="color:rgba(255,255,255,.45)"
        maxlength="12"
      />

      <view style="margin-top:auto;width:100%;display:flex;gap:8px">
        <view class="fbtn ghost" style="background:rgba(255,255,255,.12);color:#fff;box-shadow:none" @click="bgSound = sounds[(soundIndex + 1) % sounds.length].key">背景音 · {{ soundName }}</view>
        <view class="fbtn main" style="background:rgba(255,255,255,.92);color:#24322C" @click="startCompanion">{{ starting ? '正在开启…' : '开始陪伴' }}</view>
      </view>
      <text style="margin-top:9px;font-size:7.5px;color:rgba(255,255,255,.4)">开始后会生成一条陪伴记录</text>
    </view>
  </view>
</template>

<script>
/**
 * 陪伴模式 - tab首页（原记录页位置）
 * 流程：选角色（role-select）→ 选场景 → 选背景音 → 开始陪伴 → companion-running
 * 同时承载：商城/账单/群聊等陪伴玩法入口
 */
import companionApi from '@/api/companion'
// ↓↓↓ 新增（2026-10-28 P0-1）：伙伴心情气泡取主动消息 ↓↓↓
import proactiveApi from '@/api/proactive'
// ↑↑↑ 新增结束 ↑↑↑
import economy from '@/common/economy'
import aiSocial from '@/common/ai-social'
// ↓↓↓ 新增（2026-10-27 角色体系统一）：陪伴对象改用 20 个具名角色 ↓↓↓
import { getActivePartner, getPartnerPhoto, saveActivePartner, DEFAULT_PARTNER_ID } from '@/common/ai-partner'
// ↑↑↑ 新增结束 ↑↑↑
const DEFAULT_PARTNER = getActivePartner()

export default {
  data() {
    return {
      statusBarHeight: 20,
      starting: false,
      // ↓↓↓ 新增（2026-10-28 P0-1） ↓↓↓
      // 伙伴心情气泡：内容来自 proactive 主动消息，取不到就不显示
      proactiveText: '',
      // ↑↑↑ 新增结束 ↑↑↑
      // 金币
      coins: 0,
      // 陪伴对象（默认林夕，可从 role-select 回传；进入页面后会用全局 AI 配置校正，见 loadDefaultRole）
      // 【2026-10-27】id/roleKey 改为 20 个具名角色的字符串 id（如 'linxi'），不再是 ai_roles 的整型 id
      role: {
        id: DEFAULT_PARTNER.id,
        roleKey: DEFAULT_PARTNER.id,
        name: DEFAULT_PARTNER.name,
        avatar: DEFAULT_PARTNER.avatar,
        personality: DEFAULT_PARTNER.personality || '',
        roleType: DEFAULT_PARTNER.style || 'relaxed',
        photo: DEFAULT_PARTNER.photo || ''
      },
      // ↓↓↓ 新增：用户是否已手动选择过陪伴对象（手动选过就不再被默认值覆盖） ↓↓↓
      rolePicked: false,
      // 场景列表
      sceneType: 'sleep',
      customSceneName: '',
      scenes: [
        { type: 'sleep', name: '哄睡', desc: '温柔守候入睡', icon: '🌙' },
        { type: 'study', name: '学习', desc: '安静陪伴自习', icon: '📚' },
        { type: 'work', name: '工作', desc: '专注并肩作战', icon: '💻' },
        { type: 'sport', name: '运动', desc: '为你打气加油', icon: '🏃' },
        { type: 'eat', name: '用餐', desc: '一起好好吃饭', icon: '🍜' },
        { type: 'custom', name: '自定义', desc: '随心所欲的时光', icon: '✨' }
      ],
      // 背景音
      bgSound: 'quiet',
      sounds: [
        { key: 'quiet', name: '静音', icon: '🔇' },
        { key: 'rain', name: '雨声', icon: '🌧️' },
        { key: 'fire', name: '炉火', icon: '🔥' },
        { key: 'wave', name: '海浪', icon: '🌊' },
        { key: 'forest', name: '森林', icon: '🌲' },
        { key: 'piano', name: '钢琴', icon: '🎹' }
      ]
    }
  },
  computed: {
    navBodyTop() {
      return this.statusBarHeight + 44
    },
    roleAvatarBg() {
      return 'linear-gradient(135deg, #6B8E7B, #8FBC8F)'
    },
    sceneName() {
      if (this.sceneType === 'custom') {
        return this.customSceneName.trim() || '自定义'
      }
      const scene = this.scenes.find(s => s.type === this.sceneType)
      return scene ? scene.name : '自定义'
    },
    // AI伙伴情绪（关联打卡/好感度）
    aiMood() {
      return aiSocial.getAIMood()
    },
    // 设计稿 s23：当前陪伴对象照片（含自定义伙伴上传的头像）
    rolePhoto() {
      return getPartnerPhoto(this.role) || getPartnerPhoto(this.role.id) || ''
    },
    // 设计稿 s23：当前背景音名称
    soundName() {
      const s = this.sounds.find(x => x.key === this.bgSound)
      return s ? s.name : '静音'
    },
    // 设计稿 s23：背景音序号（按钮点一次切到下一个）
    soundIndex() {
      return this.sounds.findIndex(x => x.key === this.bgSound)
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    aiSocial.ensureInit()
  },
  onShow() {
    // === 登录态 + 性格测评守卫 ===
    const token = this.$store.state.token
    if (!token) {
      return uni.reLaunch({ url: '/pages/login/login' })
    }
    const username = this.$store.state.username
      || (this.$store.state.userInfo && this.$store.state.userInfo.nickname)
    if (!username) {
      return uni.reLaunch({ url: '/pages/login/login' })
    }
    const quizDone = uni.getStorageSync('quiz_completed_' + username) === 'true'
    if (!quizDone) {
      const picked = uni.getStorageSync('ai_partner_id')
      const url = picked
        ? `/pages/personality-quiz/personality-quiz?roleId=${encodeURIComponent(this.role.roleKey || picked)}`
        : '/pages/personality-quiz/personality-quiz'
      return uni.reLaunch({ url })
    }

    this.coins = economy.getCoins()
    this.loadProactiveBubble()
    // ↓↓↓ 新增（BUG-001 配套）：先按服务端角色列表校正默认陪伴对象，再套用本地配置 ↓↓↓
    this.loadDefaultRole()
    // ↑↑↑ 新增结束 ↑↑↑
    this.syncRoleFromStore()
    uni.$on('economy-updated', this.onEconomyUpdate)
  },
  onHide() {
    uni.$off('economy-updated', this.onEconomyUpdate)
  },
  onUnload() {
    uni.$off('economy-updated', this.onEconomyUpdate)
  },
  methods: {
    onEconomyUpdate() {
      this.coins = economy.getCoins()
    },
    /**
     * ↓↓↓ 新增（BUG-001 配套） ↓↓↓
     * 原来前端把默认陪伴对象硬编码为「林夕 / 🌿」，与服务端 ai_roles 里的角色（可爱型/温柔型…）
     * 对不上：显示的是林夕，入库的 role_id 却指向库里的第一个角色。
     * 现在从 GET /chat/personas 取真实角色列表，用第一条作为默认，保证展示与入库一致。
     * 用户已在 role-select 里手动选过（rolePicked=true）时不覆盖。
     */
    loadDefaultRole() {
      try {
        if (this.rolePicked) return
        // ↓↓↓ 改造（2026-10-27）：默认对象取自 20 个具名角色，不再请求 /chat/personas ↓↓↓
        // ↓↓↓ 再改造：统一走 ai-partner，支持自定义伙伴/扭蛋角色，不再写死林夕 ↓↓↓
        const p = getActivePartner()
        if (!p) return
        this.role = {
          id: p.id,
          roleKey: p.id,
          name: p.name || this.role.name,
          avatar: p.avatar || '🌿',
          personality: p.personality || '',
          roleType: p.style || p.roleType || 'relaxed',
          photo: p.photo || ''
        }
        // ↑↑↑ 改造结束 ↑↑↑
      } catch (e) {
        // 出错时沿用默认伙伴，不影响使用
        console.warn('[companion] 默认陪伴角色加载失败，沿用默认:', e && e.message)
      }
    },
    /** 从全局AI配置同步当前陪伴对象 */
    syncRoleFromStore() {
      try {
        // 用户已在 role-select 手动选过角色时，不再被全局配置里的旧数据覆盖
        if (this.rolePicked) return
        const p = getActivePartner()
        if (!p) return
        // 名称、头像、照片一起同步，避免"名字换了头像没换"
        this.role = {
          id: p.id,
          roleKey: p.id,
          name: p.name || this.role.name,
          avatar: p.avatar || this.role.avatar,
          personality: p.personality || this.role.personality,
          roleType: p.style || this.role.roleType,
          photo: p.photo || ''
        }
      } catch (e) { /* 静默 */ }
    },
    // ↓↓↓ 新增（2026-10-28 P0-1） ↓↓↓
    // request 封装可能直接返回后端 body，也可能再包一层，这里统一解一层
    unwrapBody(res) {
      if (!res) return {}
      return (res.code !== undefined) ? res : ((res.data !== undefined ? res.data : res) || {})
    },
    /**
     * 伙伴心情气泡 = proactive 主动消息。
     * 后端按「情绪优先」挑内容，前端不做二次挑选；返回空就不硬塞气泡。
     */
    async loadProactiveBubble() {
      try {
        const body = this.unwrapBody(
          await proactiveApi.next(this.role.roleKey || '', 0, true)
        )
        const d = body.data
        this.proactiveText = (d && d.content) ? d.content : ''
      } catch (e) {
        this.proactiveText = ''
      }
    },

    goMall() {
      uni.navigateTo({ url: '/pages/mall/mall' })
    },
    goBill() {
      uni.navigateTo({ url: '/pages/bill/bill' })
    },
    goGroupChat() {
      uni.navigateTo({ url: '/pages/group-chat/group-chat' })
    },
    goMoments() {
      uni.navigateTo({ url: '/pages/moments/moments' })
    },
    goGacha() {
      uni.navigateTo({ url: '/pages/gacha/gacha' })
    },
    goWarehouse() {
      uni.navigateTo({ url: '/pages/box-warehouse/box-warehouse' })
    },
    goRoleSelect() {
      uni.navigateTo({
        url: '/pages/role-select/role-select',
        events: {
          selectRole: role => {
            if (role && role.id) {
              const saved = saveActivePartner(role.roleKey || role.id, role.name)
              const p = saved || getActivePartner()
              this.role = {
                id: p.id,
                roleKey: p.id,
                name: p.name,
                avatar: p.avatar,
                personality: p.personality,
                roleType: p.style || role.roleType,
                photo: p.photo || ''
              }
              // ↓↓↓ 新增：标记为已手动选择，避免被默认角色覆盖 ↓↓↓
              this.rolePicked = true
            }
          }
        }
      })
    },
    selectScene(scene) {
      this.sceneType = scene.type
    },
    async startCompanion() {
      if (this.starting) return
      this.starting = true
      try {
        // ↓↓↓ 改造（2026-10-27）：陪伴主角改用具名角色的字符串标识 ↓↓↓
        const roleKey = this.role.roleKey || this.role.id || DEFAULT_PARTNER_ID
        // ↑↑↑ 改造结束 ↑↑↑
        const payload = {
          // role_id 是历史字段（ai_roles 的 4 个人格），陪伴主角已改由 role_key 决定，此处不再传
          role_key: roleKey,
          role_name: this.role.name || '',
          scene_type: this.sceneType,
          scene_name: this.sceneName,
          bg_img: '默认',
          bg_sound: this.sounds.find(s => s.key === this.bgSound)?.name || '静音'
        }
        const res = await companionApi.startCompanion(payload)
        const record = (res && res.data) || {}
        uni.navigateTo({
          url: `/pages/companion/companion-running?recordId=${record.id || 0}` +
            `&roleKey=${encodeURIComponent(roleKey)}` +
            `&roleName=${encodeURIComponent(this.role.name)}` +
            `&roleAvatar=${encodeURIComponent(this.role.avatar || '🌿')}` +
            `&sceneType=${this.sceneType}` +
            `&sceneName=${encodeURIComponent(this.sceneName)}` +
            `&bgSound=${encodeURIComponent(payload.bg_sound)}`
        })
      } catch (e) {
        // 后端不可达时仍可进入陪伴（本地场景）
        uni.navigateTo({
          url: `/pages/companion/companion-running?recordId=0` +
            `&roleKey=${encodeURIComponent(this.role.roleKey || this.role.id || DEFAULT_PARTNER_ID)}` +
            `&roleName=${encodeURIComponent(this.role.name)}` +
            `&roleAvatar=${encodeURIComponent(this.role.avatar || '🌿')}` +
            `&sceneType=${this.sceneType}` +
            `&sceneName=${encodeURIComponent(this.sceneName)}` +
            `&bgSound=${encodeURIComponent(this.sounds.find(s => s.key === this.bgSound)?.name || '静音')}`
        })
      } finally {
        this.starting = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿 img 尺寸同步到 uni-image 包装层 */
.xt-page.xt-s23 .hero-photo {
  display: block;
  width: 144px;
  height: 192px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 40px -18px rgba(0, 0, 0, 0.6);
}
.xt-page.xt-s23 .hero-photo :deep(div),
.xt-page.xt-s23 .hero-photo :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s23 .hero-photo :deep(img) {
  object-fit: cover;
}

/* 无照片角色的兜底头像 */
.xt-page.xt-s23 .hero-emoji {
  width: 144px;
  height: 192px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 62px;
  background: rgba(255, 253, 250, 0.1);
}

/* 场景 chips 多于设计稿，允许换行 */
.xt-page.xt-s23 .chips {
  flex-wrap: wrap;
}

/* 自定义场景名输入 */
.xt-page.xt-s23 .custom-scene {
  width: 100%;
  height: 34px;
  margin-top: 8px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 253, 250, 0.1);
  font-size: 10px;
  color: #ffffff;
}
</style>
