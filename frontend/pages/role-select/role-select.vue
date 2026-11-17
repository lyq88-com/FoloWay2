<template>
  <view class="xt-page xt-s22">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view>
          <view class="page-title">选择伙伴</view>
          <view class="page-sub">之后可以随时更换，记忆会为她保留</view>
        </view>
        <view class="icon-btn" @click="toggleSearch"><xt-icon name="i-search" /></view>
      </view>

      <!-- 搜索（点右上角放大镜展开） -->
      <view v-if="showSearch" style="margin-bottom:10px">
        <input
          v-model="keyword"
          :focus="showSearch"
          placeholder="搜索伙伴名字 / 性格"
          placeholder-style="color:#BFC7BF"
          style="height:36px;padding:0 12px;border-radius:12px;background:#FFFDFA;border:1px solid rgba(30,42,36,.10);font-size:9px;color:#22302A"
        />
      </view>

      <!-- 推荐提示 -->
      <view class="ai-rec" style="margin-bottom:11px">
        <view class="sp"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <text class="k">根据你的测试结果</text>
          <text class="p">{{ selectedRole ? `已选中 ${selectedRole.name}，确认后开始陪伴。` : '先选一位最想让她陪着你的人，之后随时可以更换。' }}</text>
        </view>
      </view>

      <!-- 角色网格 -->
      <view class="role-grid">
        <view
          v-for="role in filteredRoles"
          :key="role.id"
          class="role"
          :class="{ on: selectedId === role.id }"
          @click="chooseRole(role)"
        >
          <view class="role-ph">
            <image
              v-if="rolePhoto(role.id)"
              :src="rolePhoto(role.id)"
              mode="aspectFill"
            />
            <view v-else class="role-fallback" :style="{ background: avatarBg(role.roleType) }">
              <text>{{ role.avatar }}</text>
            </view>
          </view>
          <view class="role-meta">
            <text class="rname">{{ role.name }}</text>
            <text class="rtag">{{ shortTraits(role) }}</text>
          </view>
        </view>
      </view>

      <!-- 随机匹配 -->
      <view class="custom-role" @click="randomMatch">
        <view class="ci"><xt-icon name="i-plus" /></view>
        <view class="tx">
          <text class="t">随机匹配一位</text>
          <text class="m">让系统根据你的情绪状态来选</text>
        </view>
        <view class="ar" style="color:#CFD6CE"><xt-icon name="i-right" /></view>
      </view>

      <!-- 确认 -->
      <view
        class="auth-btn"
        :class="{ disabled: !selectedRole }"
        style="margin-top:12px"
        @click="confirmSelect"
      >
        {{ selectedRole ? `就选 ${selectedRole.name} 了` : '请选择一位伙伴' }}
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 角色选择页（陪伴模式）
 * - 数据源改为项目的 20 个具名 AI 伙伴：common/ai-characters.js 的 CHARACTERS（含自定义角色）
 * - 通过 EventChannel「selectRole」回传给 companion 页
 *
 * 【2026-10-27 改造】原先读 GET /chat/personas，那个接口只返回 ai_roles 的 4 个「人格类型」
 * （可爱型/温柔型/认真型/活力型），与画廊里的 20 个具名角色不是一套数据。
 * 现已统一到 20 个具名角色；ai_roles 保留给「虚拟世界」模块继续使用。
 */
import { getAllCharacters } from '@/common/ai-characters'
import { getPartnerPhoto, getActivePartnerId, saveActivePartner } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

// 8 种 style 全覆盖（原来只有 5 个 key，cyber/artsy/energetic/mythical 会落到兜底色）
const TYPE_BG = {
  relaxed: 'linear-gradient(135deg, #3D5A4E, #26382F)',
  y2k: 'linear-gradient(135deg, #5E4A6E, #3A2D4E)',
  chinese: 'linear-gradient(135deg, #6E4A48, #46302E)',
  cyber: 'linear-gradient(135deg, #2F4F52, #1C3235)',
  artsy: 'linear-gradient(135deg, #5C5340, #38332A)',
  cool: 'linear-gradient(135deg, #3F4A5E, #28303E)',
  energetic: 'linear-gradient(135deg, #6E5A38, #443822)',
  mythical: 'linear-gradient(135deg, #4A3F6B, #2E2742)'
}

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      roles: [],
      selectedId: null,
      showSearch: false,
      keyword: '',
      loading: false
    }
  },
  computed: {
    selectedRole() {
      return this.roles.find(r => r.id === this.selectedId) || null
    },
    filteredRoles() {
      const k = this.keyword.trim()
      if (!k) return this.roles
      return this.roles.filter(r => (r.name + ' ' + (r.personality || '') + ' ' + (r.traits || []).join(' ')).includes(k))
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    this.loadRoles()
  },
  methods: {
    async loadRoles() {
      this.loading = true
      try {
        // ↓↓↓ 改造：数据源从 /chat/personas（4 个抽象人格）换成 20 个具名角色 ↓↓↓
        const list = getAllCharacters() || []
        const presets = list.map(c => ({
          id: c.id,                 // 字符串 id，如 'linxi'
          name: c.name,
          avatar: c.avatar,
          personality: c.personality,
          traits: c.traits || [],
          roleType: c.style         // 8 种 style，用于头像背景，已与 TYPE_BG 对齐
        }))
        // ↓↓↓ 兼容自定义 AI 伙伴：与预设角色一起参与选择 ↓↓↓
        const customs = (this.$store.state.customCharacters || [])
          .filter(c => c && c.id)
          .map(c => ({
            id: c.id,
            name: c.name || '自定义伙伴',
            avatar: c.avatar || '🌟',
            personality: c.personality || c.description || '自定义角色',
            traits: c.traits || [],
            roleType: c.style || 'relaxed',
            isCustom: true
          }))
        this.roles = [...customs, ...presets]
        // ↑↑↑ 改造结束 ↑↑↑
        // 进页面时默认选中当前生效的伙伴，避免"选了 A 却高亮 B"
        const activeId = getActivePartnerId()
        if (activeId && this.roles.some(r => r.id === activeId)) {
          this.selectedId = activeId
        }
      } catch (e) {
        uni.showToast({ title: '角色加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    rolePhoto(id) {
      // 角色卡片要展示完整立绘（含肩颈与背景），不再裁成只剩头部
      return getPartnerPhoto(id)
    },
    avatarBg(roleType) {
      return TYPE_BG[roleType] || TYPE_BG.relaxed
    },
    shortTraits(role) {
      const t = role.traits || []
      return t.length ? t[0] : (role.personality || '').split('、')[0] || '贴心伙伴'
    },
    chooseRole(role) {
      this.selectedId = role.id
    },
    toggleSearch() {
      this.showSearch = !this.showSearch
      if (!this.showSearch) this.keyword = ''
    },
    randomMatch() {
      const pool = this.filteredRoles
      if (!pool.length) {
        uni.showToast({ title: '没有可匹配的伙伴', icon: 'none' })
        return
      }
      const pick = pool[Math.floor(Math.random() * pool.length)]
      this.selectedId = pick.id
      uni.showToast({ title: `为你选中 ${pick.name}`, icon: 'none' })
    },
    goBack() {
      uni.navigateBack()
    },
    confirmSelect() {
      if (!this.selectedRole) return
      const pages = getCurrentPages()
      const current = pages[pages.length - 1]
      const eventChannel = current.getOpenerEventChannel && current.getOpenerEventChannel()

      // 全局落库：所有页面（首页/聊天/陪伴/群聊）都从 aiConfig 读取伙伴，
      // 只靠 EventChannel 回传会导致其他页面形象不同步。
      saveActivePartner(this.selectedRole.id, this.selectedRole.name)

      const payload = {
        id: this.selectedRole.id,
        // ↓↓↓ 新增：把字符串角色标识单独传出去，companion 页用它当 role_key 落库 ↓↓↓
        roleKey: this.selectedRole.id,
        // ↑↑↑ 新增结束 ↑↑↑
        name: this.selectedRole.name,
        avatar: this.selectedRole.avatar,
        personality: this.selectedRole.personality,
        roleType: this.selectedRole.roleType
      }

      if (eventChannel && eventChannel.emit) {
        eventChannel.emit('selectRole', payload)
      }
      // ↓↓↓ 新增：同时发全局事件，供非陪伴入口（profile 的「AI角色」）接收 ↓↓↓
      uni.$emit('roleSelected', payload)
      // ↑↑↑ 新增结束 ↑↑↑
      uni.navigateBack()
    }
  }
}
</script>

<style lang="scss" scoped>
.xt-page.xt-s22 {
  background: #F8F4EC;
  background-image: radial-gradient(420px 300px at 90% -6%, rgba(156,191,170,.18), transparent 62%),
    radial-gradient(360px 300px at 0% 104%, rgba(192,138,86,.12), transparent 60%);
  min-height: 100vh;
}
/* 底部呼吸空间 */
.xt-page.xt-s22 .body {
  padding: 0 16px calc(20px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

/* 角色卡片：方框立绘 + 名字；列数跟随容器宽度自动增减，卡片比例恒定 */
.xt-page.xt-s22 .role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
  gap: 10px 9px;
}
.xt-page.xt-s22 .role {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 0;
  overflow: hidden;
  background: #FFFDFA;
  border-radius: 16px;
  box-shadow: 0 12px 26px -22px rgba(34,48,42,.55), inset 0 0 0 1px var(--v7-line);
  transition: all 0.15s ease;
}
.xt-page.xt-s22 .role.on {
  background: #F4F8F4;
  box-shadow: inset 0 0 0 1.5px rgba(68,112,90,.6), 0 8px 20px -16px rgba(68,112,90,.4);
}

/* 立绘框：3:4 与素材原始构图一致，任何屏宽都等比缩放、不裁头不拉变形 */
.xt-page.xt-s22 .role-ph {
  position: relative;
  width: 100%;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: #EFE9DD;
}
.xt-page.xt-s22 .role-ph uni-image,
.xt-page.xt-s22 .role-ph :deep(uni-image > div),
.xt-page.xt-s22 .role-ph :deep(uni-image img) {
  display: block;
  width: 100%;
  height: 100%;
}
.xt-page.xt-s22 .role-ph :deep(uni-image img) {
  object-fit: cover;
}
.xt-page.xt-s22 .role.on .role-ph {
  box-shadow: inset 0 0 0 2px var(--v7-green);
}

/* 无照片角色的兜底头像 */
.xt-page.xt-s22 .role-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
}

.xt-page.xt-s22 .role-meta {
  padding: 8px 8px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.xt-page.xt-s22 .role .rname {
  display: block;
  font-size: 10.5px;
  font-weight: 900;
  color: #22302A;
  text-align: center;
  line-height: 1.35;
}
.xt-page.xt-s22 .role .rtag {
  display: block;
  font-size: 8px;
  color: #A6B0A9;
  text-align: center;
  line-height: 1.3;
}

/* 大屏浏览器上适当放大文字，保证电脑端可读性 */
@media (min-width: 560px) {
  .xt-page.xt-s22 .role .rname { font-size: 12px; }
  .xt-page.xt-s22 .role .rtag { font-size: 9.5px; }
}

/* 未选择时置灰 */
.xt-page.xt-s22 .auth-btn.disabled {
  opacity: 0.45;
  pointer-events: none;
}
</style>
