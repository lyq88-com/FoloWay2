<template>
  <view class="xt-page xt-s47">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">循途画廊</view>
          <view class="page-sub">你们一起看过的 {{ galleryCount }} 个画面</view>
        </view>
        <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
      </view>

      <view class="chips" style="margin-bottom:7px">
        <text class="chip" :class="{ on: currentSource === 'official' }" @click="switchSource('official')">官方角色</text>
        <text class="chip" :class="{ on: currentSource === 'gacha' }" @click="switchSource('gacha')">我抽到的{{ gachaCharacters.length ? ' ' + gachaCharacters.length : '' }}</text>
      </view>

      <scroll-view v-if="currentSource === 'official'" scroll-x style="white-space:nowrap">
        <view class="chips" style="display:inline-flex;margin:0 0 11px">
          <text
            v-for="(label, key) in styleLabels"
            :key="key"
            class="chip"
            :class="{ on: currentStyle === key }"
            @click="switchStyle(key)"
          >{{ label }}</text>
        </view>
      </scroll-view>

      <!-- ===== 官方角色 ===== -->
      <view v-if="currentSource === 'official'" class="gal-grid">
        <view
          v-for="character in filteredCharacters"
          :key="character.id"
          class="gal-card"
          @click="showCharacterDetail(character)"
        >
          <image
            v-if="rolePhoto(character.id)"
            :src="rolePhoto(character.id)"
            mode="aspectFill"
            class="gal-photo"
          />
          <view
            v-else
            class="gal-photo gal-photo-fallback"
          >
            <CharacterHead :characterId="character.id" size="medium" :disableBlink="true" />
          </view>
          <view class="gal-info">
            <view class="gal-name">{{ character.name }}</view>
            <view class="gal-desc">{{ character.description }}</view>
          </view>
          <view v-if="currentCharacterId === character.id" class="select-indicator">
            <text class="select-icon">✓</text>
          </view>
        </view>

        <!-- 已创建的自定义角色 -->
        <view
          v-for="custom in customCharacters"
          :key="custom.id"
          class="gal-card"
          @click="showCustomCharacterDetail(custom)"
        >
          <image
            v-if="rolePhoto(custom.id)"
            :src="rolePhoto(custom.id)"
            mode="aspectFill"
            class="gal-photo"
          />
          <view
            v-else
            class="gal-photo gal-photo-fallback"
          >
            <CharacterHead :characterId="custom.id" size="medium" :disableBlink="true" />
          </view>
          <view class="gal-info">
            <view class="gal-name">{{ custom.name }}</view>
            <view class="gal-desc">{{ custom.description }}</view>
          </view>
          <view v-if="currentCharacterId === custom.id" class="select-indicator">
            <text class="select-icon">✓</text>
          </view>
        </view>

        <!-- 创建自定义伙伴入口 -->
        <view
          class="gal-create"
          @click="goToWorkshop"
        >
          <view class="gal-create-plus">＋</view>
          <view class="gal-create-title">创建自定义伙伴</view>
          <view class="gal-create-desc">打造专属于你的形象</view>
        </view>
      </view>

      <!-- ===== 我抽到的 ===== -->
      <view v-if="currentSource === 'gacha'">
        <view v-if="!gachaCharacters.length" class="mem-hero gallery-empty">
          <view class="empty-title">还没抽到伙伴哦</view>
          <view class="empty-desc">去扭蛋机试试运气吧，说不定能遇到命中注定的 TA～</view>
          <view class="chip on" style="display:inline-block;margin-top:12px" @click="goToGacha">去扭蛋</view>
        </view>
        <view v-else class="gal-grid">
          <view
            v-for="gacha in gachaCharacters"
            :key="gacha.roleKey"
            class="gal-card"
            @click="showGachaCharacterDetail(gacha)"
          >
            <image
              v-if="rolePhoto(gacha.roleKey)"
              :src="rolePhoto(gacha.roleKey)"
              mode="aspectFill"
              class="gal-photo"
            />
            <view
              v-else
              class="gal-photo gal-photo-fallback gal-photo-gacha"
            >{{ gacha.avatar }}</view>
            <view class="gal-info">
              <view class="gal-name-row">
                <text class="gal-name">{{ gacha.name }}</text>
                <text class="gal-badge">{{ gacha.rarity }}</text>
              </view>
              <view class="gal-desc">{{ gacha.description }}</view>
            </view>
            <view v-if="currentCharacterId === gacha.roleKey" class="select-indicator">
              <text class="select-icon">✓</text>
            </view>
          </view>
        </view>
      </view>

      <view class="mem-hero gallery-tip">
        <view class="mi tint-green gallery-tip-icon"><xt-icon name="i-call" /></view>
        <view>
          <view class="t">点开任意画面，可以设为陪伴伙伴</view>
          <view class="m">你们一起看过的画面，都留在这里</view>
        </view>
      </view>
    </view>

    <!-- 详情弹窗（固定角色） -->
    <view class="detail-modal" v-if="selectedCharacter && !selectedCustomCharacter" @click="closeDetail">
      <view class="modal-content" @click.stop>
        <view class="modal-bar"></view>
        <view class="modal-header">
          <view class="modal-avatar-wrapper">
            <CharacterHead
              :characterId="selectedCharacter.id"
              size="xlarge"
              :disableBlink="true"
            />
          </view>
          <text class="modal-name">{{ selectedCharacter.name }}</text>
          <text class="modal-catchphrase">{{ selectedCharacter.catchphrase }}</text>
        </view>

        <view class="modal-body">
          <view class="detail-section">
            <text class="detail-title">角色简介</text>
            <text class="detail-text">{{ selectedCharacter.description }}</text>
          </view>

          <view class="detail-section">
            <text class="detail-title">性格特质</text>
            <view class="traits-wrap">
              <view
                v-for="trait in selectedCharacter.traits"
                :key="trait"
                class="trait-tag"
              >
                <text class="trait-text">{{ trait }}</text>
              </view>
            </view>
          </view>

          <view class="detail-section">
            <text class="detail-title">专属话术</text>
            <view class="phrases-wrap">
              <view
                v-for="(phrases, type) in samplePhrases"
                :key="type"
                class="phrase-item"
              >
                <text class="phrase-type">{{ getPhraseTypeName(type) }}</text>
                <text class="phrase-text">{{ phrases }}</text>
              </view>
            </view>
          </view>

          <view class="detail-section">
            <text class="detail-title">视觉风格</text>
            <view class="colors-wrap">
              <view
                v-for="(color, key) in selectedCharacter.colors"
                :key="key"
                class="color-item"
              >
                <view class="color-dot" :style="{ background: color }"></view>
                <text class="color-name">{{ getColorName(key) }}</text>
              </view>
            </view>
          </view>

          <!-- 羁绊碎片区域 -->
          <view class="bond-section" v-if="bondData">
            <text class="detail-title">💫 羁绊碎片</text>
            <view class="bond-progress">
              <view class="progress-bar">
                <view class="progress-fill" :style="{ width: bondProgressPct + '%' }"></view>
              </view>
              <text class="progress-text">与TA聊过 {{ bondData.totalChatCount }} 次 · 解锁 {{ bondData.currentChapter }}/4</text>
            </view>
            <view class="bond-chapters">
              <view
                v-for="ch in bondData.chapters"
                :key="ch.idx"
                class="bond-chapter"
                :class="{ locked: !ch.unlocked, unlocked: ch.unlocked }"
              >
                <view v-if="ch.unlocked && ch.content" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text">{{ ch.content }}</text>
                </view>
                <view v-else-if="ch.unlocked" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text italic">✨ 碎片生成中...</text>
                </view>
                <view v-else class="chapter-locked">
                  <text class="lock-icon">🔒</text>
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-hint">{{ ch.hint }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view class="modal-footer">
          <view class="modal-btn cancel" @click="closeDetail">
            <text>取消</text>
          </view>
          <view
            class="modal-btn confirm"
            :class="{ selected: currentCharacterId === selectedCharacter.id }"
            @click="selectCharacter(selectedCharacter)"
          >
            <text>{{ currentCharacterId === selectedCharacter.id ? '已选择' : '设为陪伴伙伴' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 详情弹窗（自定义角色） -->
    <view class="detail-modal" v-if="selectedCustomCharacter" @click="closeDetail">
      <view class="modal-content" @click.stop>
        <view class="modal-bar"></view>
        <view class="modal-header">
          <view class="modal-avatar-wrapper">
            <CharacterHead
              :characterId="selectedCustomCharacter.id"
              size="xlarge"
              :disableBlink="true"
            />
          </view>
          <text class="modal-name">{{ selectedCustomCharacter.name }}</text>
          <text class="modal-catchphrase">{{ selectedCustomCharacter.catchphrase }}</text>
        </view>

        <view class="modal-body">
          <view class="detail-section">
            <text class="detail-title">角色简介</text>
            <text class="detail-text">{{ selectedCustomCharacter.description }}</text>
          </view>

          <view class="detail-section">
            <text class="detail-title">性格特质</text>
            <view class="traits-wrap">
              <view
                v-for="trait in selectedCustomCharacter.traits"
                :key="trait"
                class="trait-tag"
              >
                <text class="trait-text">{{ trait }}</text>
              </view>
            </view>
          </view>

          <!-- 羁绊碎片区域（与官方角色共用 bondData） -->
          <view class="bond-section" v-if="bondData">
            <text class="detail-title">💫 羁绊碎片</text>
            <view class="bond-progress">
              <view class="progress-bar">
                <view class="progress-fill" :style="{ width: bondProgressPct + '%' }"></view>
              </view>
              <text class="progress-text">与TA聊过 {{ bondData.totalChatCount }} 次 · 解锁 {{ bondData.currentChapter }}/4</text>
            </view>
            <view class="bond-chapters">
              <view
                v-for="ch in bondData.chapters"
                :key="ch.idx"
                class="bond-chapter"
                :class="{ locked: !ch.unlocked, unlocked: ch.unlocked }"
              >
                <view v-if="ch.unlocked && ch.content" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text">{{ ch.content }}</text>
                </view>
                <view v-else-if="ch.unlocked" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text italic">✨ 碎片生成中...</text>
                </view>
                <view v-else class="chapter-locked">
                  <text class="lock-icon">🔒</text>
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-hint">{{ ch.hint }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view class="modal-footer">
          <view class="modal-btn cancel" @click="closeDetail">
            <text>取消</text>
          </view>
          <view
            class="modal-btn edit-btn"
            @click="editCustomCharacter(selectedCustomCharacter)"
          >
            <text>编辑</text>
          </view>
          <view
            class="modal-btn confirm"
            :class="{ selected: currentCharacterId === selectedCustomCharacter.id }"
            @click="selectCustomCharacter(selectedCustomCharacter)"
          >
            <text>{{ currentCharacterId === selectedCustomCharacter.id ? '已选择' : '设为陪伴伙伴' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 详情弹窗（扭蛋角色） -->
    <view class="detail-modal" v-if="selectedGachaCharacter" @click="closeDetail">
      <view class="modal-content" @click.stop>
        <view class="modal-bar"></view>
        <view class="modal-header">
          <text class="gacha-modal-avatar">{{ selectedGachaCharacter.avatar }}</text>
          <text class="modal-name">{{ selectedGachaCharacter.name }}</text>
          <text class="gacha-rarity-big" :class="'rarity-' + selectedGachaCharacter.rarity">{{ selectedGachaCharacter.rarity }} · 扭蛋伙伴</text>
        </view>

        <view class="modal-body">
          <view class="detail-section">
            <text class="detail-title">性格简介</text>
            <text class="detail-text">{{ selectedGachaCharacter.description }}</text>
          </view>
          <view class="detail-section" v-if="selectedGachaCharacter.catchphrase">
            <text class="detail-title">口头禅</text>
            <text class="detail-text italic">"{{ selectedGachaCharacter.catchphrase }}"</text>
          </view>

          <!-- 羁绊碎片区域（扭蛋角色共用 bondData） -->
          <view class="bond-section" v-if="bondData">
            <text class="detail-title">💫 羁绊碎片</text>
            <view class="bond-progress">
              <view class="progress-bar">
                <view class="progress-fill" :style="{ width: bondProgressPct + '%' }"></view>
              </view>
              <text class="progress-text">与TA聊过 {{ bondData.totalChatCount }} 次 · 解锁 {{ bondData.currentChapter }}/4</text>
            </view>
            <view class="bond-chapters">
              <view
                v-for="ch in bondData.chapters"
                :key="ch.idx"
                class="bond-chapter"
                :class="{ locked: !ch.unlocked, unlocked: ch.unlocked }"
              >
                <view v-if="ch.unlocked && ch.content" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text">{{ ch.content }}</text>
                </view>
                <view v-else-if="ch.unlocked" class="chapter-content">
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-text italic">✨ 碎片生成中...</text>
                </view>
                <view v-else class="chapter-locked">
                  <text class="lock-icon">🔒</text>
                  <text class="chapter-title">{{ ch.title }}</text>
                  <text class="chapter-hint">{{ ch.hint }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view class="modal-footer">
          <view class="modal-btn cancel" @click="closeDetail">
            <text>取消</text>
          </view>
          <view
            class="modal-btn chat-btn"
            @click="chatWithGacha(selectedGachaCharacter)"
          >
            <text>去聊天</text>
          </view>
          <view
            class="modal-btn confirm"
            :class="{ selected: currentCharacterId === selectedGachaCharacter.roleKey }"
            @click="selectGachaCharacter(selectedGachaCharacter)"
          >
            <text>{{ currentCharacterId === selectedGachaCharacter.roleKey ? '已选择' : '设为陪伴伙伴' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { CHARACTERS, STYLE_LABELS, getCharactersByStyle } from '@/common/ai-characters'
import { getPartnerPhoto, saveActivePartner } from '@/common/ai-partner'
import CharacterHead from '@/components/character-sprite/character-head.vue'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import personaApi from '@/api/persona'

export default {
  components: { CharacterHead, XtIcon },
  data() {
    return {
      currentSource: 'official',   // 'official' 官方角色 | 'gacha' 我抽到的
      currentStyle: 'all',
      styleLabels: { all: '全部', ...STYLE_LABELS },
      currentCharacterId: '',
      selectedCharacter: null,
      selectedCustomCharacter: null,
      selectedGachaCharacter: null,
      samplePhrases: {},
      gachaCharacters: [],   // 后端拉的扭蛋角色（origin='gacha', creator_id=当前用户）
      bondData: null         // 当前选中角色的羁绊进度（从 /api/v1/persona/bond/{role_key} 拉）
    }
  },
  computed: {
    filteredCharacters() {
      if (this.currentSource !== 'official') return []
      if (this.currentStyle === 'all') {
        return CHARACTERS
      }
      return getCharactersByStyle(this.currentStyle)
    },
    customCharacters() {
      return this.$store.state.customCharacters || []
    },
    galleryCount() {
      if (this.currentSource === 'gacha') return this.gachaCharacters.length
      return this.filteredCharacters.length + this.customCharacters.length
    },
    bondProgressPct() {
      if (!this.bondData) return 0
      const thresholds = [10, 30, 60, 120]
      const max = thresholds[thresholds.length - 1]
      return Math.min(100, Math.round((this.bondData.totalChatCount / max) * 100))
    }
  },
  onLoad() {
    const aiConfig = this.$store.state.aiConfig || {}
    this.currentCharacterId = aiConfig.avatarType || ''
  },
  onShow() {
    const aiConfig = this.$store.state.aiConfig || {}
    this.currentCharacterId = aiConfig.avatarType || ''
    this.loadGachaCharacters()
  },
  methods: {
    /** 角色照片（含自定义伙伴上传的头像） */
    rolePhoto(id) {
      return getPartnerPhoto(id)
    },
    /** 拉当前用户自己抽到的扭蛋角色（后端已做 creator_id 过滤） */
    async loadGachaCharacters() {
      try {
        const res = await personaApi.getRoles('gacha', false)
        const d = res && res.data ? res.data : (Array.isArray(res) ? res : [])
        this.gachaCharacters = (d || []).map(r => ({
          id: r.roleKey || r.role_type || String(r.id),
          roleKey: r.roleKey || r.role_type || String(r.id),
          name: r.name,
          avatar: r.avatar || '🎁',
          description: r.personality || r.description || '扭蛋抽到的伙伴',
          catchphrase: r.catchphrase || '',
          rarity: r.rarity || 'R',
          colors: {
            light: '#FFF5E6',
            secondary: '#FFD8A8',
            primary: '#FF9F43',
            accent: '#FF6B9D'
          }
        }))
      } catch (e) {
        this.gachaCharacters = []
      }
    },
    switchSource(src) {
      this.currentSource = src
      this.closeDetail()
    },
    goBack() {
      uni.navigateBack()
    },
    goToWorkshop() {
      uni.navigateTo({ url: '/pages/character-workshop/character-workshop' })
    },
    goToGacha() {
      uni.navigateTo({ url: '/pages/gacha/gacha' })
    },
    switchStyle(style) {
      this.currentStyle = style
    },
    showCharacterDetail(character) {
      this.selectedCharacter = character
      this.selectedCustomCharacter = null
      this.selectedGachaCharacter = null
      this.samplePhrases = {
        morning: character.phrases.morning[0],
        comfort: character.phrases.comfort[0],
        celebrate: character.phrases.celebrate[0],
        catchphrase: character.catchphrase
      }
      this.loadBondStatus(character.id)
    },
    showCustomCharacterDetail(custom) {
      this.selectedCustomCharacter = custom
      this.selectedCharacter = null
      this.selectedGachaCharacter = null
      this.loadBondStatus(custom.id)
    },
    /** 拉羁绊进度（失败静默，bondData 保持 null 不影响弹窗） */
    async loadBondStatus(roleKey) {
      this.bondData = null
      if (!roleKey) return
      try {
        const res = await personaApi.getBond(roleKey)
        if (res && res.code === 200 && res.data) {
          this.bondData = res.data
        }
      } catch (e) {
        // bond 路由或表未就绪时静默降级
      }
    },
    closeDetail() {
      this.selectedCharacter = null
      this.selectedCustomCharacter = null
      this.selectedGachaCharacter = null
      this.samplePhrases = {}
      this.bondData = null
    },
    showGachaCharacterDetail(gacha) {
      this.selectedGachaCharacter = gacha
      this.selectedCharacter = null
      this.selectedCustomCharacter = null
      this.loadBondStatus(gacha.roleKey)
    },
    selectGachaCharacter(gacha) {
      saveActivePartner(gacha.roleKey, gacha.name, { profile: { ...gacha, id: gacha.roleKey } })
      this.currentCharacterId = gacha.roleKey
      uni.showToast({ title: `${gacha.name}成为你的伙伴！`, icon: 'success' })
      this.closeDetail()
    },
    chatWithGacha(gacha) {
      saveActivePartner(gacha.roleKey, gacha.name, { profile: { ...gacha, id: gacha.roleKey } })
      uni.navigateTo({ url: '/pages/chat/chat' })
    },
    selectCharacter(character) {
      saveActivePartner(character.id, character.name)
      this.currentCharacterId = character.id
      uni.showToast({ title: `${character.name}成为你的伙伴！`, icon: 'success' })
      this.closeDetail()
    },
    selectCustomCharacter(custom) {
      saveActivePartner(custom.id, custom.name)
      this.currentCharacterId = custom.id
      uni.showToast({ title: `${custom.name}成为你的伙伴！`, icon: 'success' })
      this.closeDetail()
    },
    editCustomCharacter(custom) {
      uni.navigateTo({ url: `/pages/character-workshop/character-workshop?editId=${custom.id}` })
    },
    getPhraseTypeName(type) {
      const names = {
        morning: '早安问候',
        comfort: '安慰话语',
        celebrate: '庆祝鼓励',
        catchphrase: '口头禅'
      }
      return names[type] || type
    },
    getColorName(key) {
      const names = {
        primary: '主色调',
        secondary: '次色调',
        accent: '强调色',
        light: '浅色',
        dark: '深色'
      }
      return names[key] || key
    }
  }
}
</script>

<style lang="scss" scoped>
/* H5 下 <image> 渲染为 <uni-image>，补设计稿 img 的宽度 */
.xt-page.xt-s47 .gal-card uni-image {
  display: block;
  width: 100%;
}

.gallery-page {
  box-sizing: border-box;
  min-height: 100vh;
  background-color: var(--v7-card);
  background-image:
    radial-gradient(660rpx 460rpx at 4% -6%, rgba(156, 191, 170, 0.22) 0%, transparent 58%),
    radial-gradient(620rpx 460rpx at 100% 0%, rgba(192, 138, 86, 0.10) 0%, transparent 55%);
  display: flex;
  flex-direction: column;
}

/* 数据源胶囊 */
.source-tabs { padding: 4rpx 30rpx 14rpx; }
.source-tabs-inner { display: flex; }
.pill {
  display: flex;
  align-items: center;
  padding: 12rpx 28rpx;
  margin-right: 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.78);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  transition: all 0.25s ease;
}
.pill-text { font-size: 24rpx; color: #6A776E; }
.pill.active { background: var(--v7-green); box-shadow: none; }
.pill.active .pill-text { color: #F8F3E7; font-weight: 800; }
.gacha-count {
  margin-left: 10rpx;
  padding: 0 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.24);
  color: #F8F3E7;
  font-size: 18rpx;
  line-height: 28rpx;
}

/* 风格筛选 */
.style-tabs {
  height: 82rpx;
  white-space: nowrap;
  padding-left: 30rpx;
}
.tabs-inner { display: inline-flex; align-items: center; padding-right: 30rpx; }
.pill-sm { padding: 10rpx 22rpx; margin-right: 12rpx; }
.pill-sm .pill-text { font-size: 21rpx; }

/* 角色网格 */
.character-list { flex: 1; padding: 0 30rpx; box-sizing: border-box; }
.list-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18rpx;
  padding-bottom: 50rpx;
}
.character-card {
  border-radius: 28rpx;
  transition: all 0.25s ease;
}
.character-card:active { transform: scale(0.98); }
.card-bg {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 18rpx 22rpx;
  border-radius: 28rpx;
  background: var(--v7-card);
  box-shadow: 0 10rpx 24rpx -22rpx rgba(34, 48, 42, 0.6), inset 0 0 0 1rpx var(--v7-line);
}
.character-card.selected .card-bg {
  box-shadow: inset 0 0 0 2rpx var(--v7-green), 0 10rpx 24rpx -22rpx rgba(34, 48, 42, 0.6);
}
.character-avatar-wrapper {
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F3EFE5;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.character-info {
  width: 100%;
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.character-name {
  font-size: 26rpx;
  font-weight: 800;
  color: #22302A;
  text-align: center;
}
.character-desc {
  width: 100%;
  margin-top: 6rpx;
  font-size: 19rpx;
  line-height: 1.45;
  color: #AEB6AE;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.select-indicator {
  position: absolute;
  top: 14rpx;
  right: 14rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: var(--v7-green);
  display: flex;
  align-items: center;
  justify-content: center;
}
.select-icon { font-size: 20rpx; font-weight: 700; color: #F8F3E7; line-height: 1; }

/* 自定义角色入口 */
.custom-card-bg {
  background: rgba(255, 253, 250, 0.6);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.custom-avatar { background: #F3EFE5; }
.custom-avatar-inner {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 2rpx dashed #9CBFAA;
  display: flex;
  align-items: center;
  justify-content: center;
}
.custom-avatar-plus { font-size: 42rpx; font-weight: 300; color: var(--v7-green); line-height: 1; }

/* 弹窗 */
.detail-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(20, 32, 26, 0.45);
  display: flex;
  align-items: flex-end;
  z-index: 1000;
}
.modal-content {
  width: 100%;
  box-sizing: border-box;
  background: var(--v7-card);
  border-radius: 34rpx 34rpx 0 0;
  padding: 16rpx 36rpx calc(36rpx + env(safe-area-inset-bottom));
  animation: slideUp 0.3s ease;
}
@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
.modal-bar {
  width: 72rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #E0E6E1;
  margin: 0 auto 20rpx;
}
.modal-header {
  text-align: center;
  margin-bottom: 30rpx;
}
.modal-avatar-wrapper {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 18rpx;
  background: #F3EFE5;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.modal-name { font-size: 36rpx; font-weight: 800; color: #22302A; display: block; }
.modal-catchphrase { margin-top: 10rpx; font-size: 24rpx; color: #6E9B81; font-style: italic; }

.modal-body { max-height: 58vh; overflow-y: auto; margin-bottom: 26rpx; }
.detail-section { margin-bottom: 28rpx; }
.detail-title {
  font-size: 24rpx;
  font-weight: 800;
  color: var(--v7-green);
  display: block;
  margin-bottom: 14rpx;
}
.detail-text { font-size: 26rpx; color: #6A776E; line-height: 1.7; }

.traits-wrap { display: flex; flex-wrap: wrap; }
.trait-tag {
  padding: 8rpx 20rpx;
  margin: 0 12rpx 12rpx 0;
  border-radius: 999rpx;
  background: #F3EFE5;
}
.trait-text { font-size: 22rpx; color: var(--v7-green); }

.phrases-wrap { display: flex; flex-direction: column; }
.phrase-item {
  background: var(--v7-card);
  border-radius: 20rpx;
  padding: 18rpx 20rpx;
  margin-bottom: 12rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.phrase-type { font-size: 19rpx; color: #AEB6AE; display: block; margin-bottom: 6rpx; }
.phrase-text { font-size: 25rpx; color: #26332C; }

.colors-wrap { display: flex; flex-wrap: wrap; }
.color-item { display: flex; align-items: center; margin: 0 24rpx 12rpx 0; }
.color-dot {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1rpx rgba(34, 48, 42, 0.12);
}
.color-name { margin-left: 10rpx; font-size: 20rpx; color: #AEB6AE; }

.modal-footer { display: flex; }
.modal-btn {
  flex: 1;
  padding: 24rpx 0;
  border-radius: 999rpx;
  text-align: center;
  transition: all 0.2s ease;
}
.modal-btn.cancel { background: #F3EFE5; }
.modal-btn.cancel text { color: #6A776E; font-size: 26rpx; }
.modal-btn.confirm {
  margin-left: 16rpx;
  background: linear-gradient(140deg, #4E7A64, #24493A);
  box-shadow: 0 12rpx 24rpx -16rpx rgba(36, 73, 58, 0.7);
}
.modal-btn.confirm text { color: #FFFDFA; font-size: 26rpx; font-weight: 700; }
.modal-btn.confirm.selected { background: #F3EFE5; box-shadow: inset 0 0 0 1rpx var(--v7-line); }
.modal-btn.confirm.selected text { color: var(--v7-green); }
.modal-btn.edit-btn { background: #F3EFE5; margin-left: 16rpx; }
.modal-btn.edit-btn text { color: #8A5D33; font-size: 26rpx; font-weight: 700; }
.modal-btn:active { transform: scale(0.96); }

/* 扭蛋角色 */
.gacha-empty {
  grid-column: 1 / -1;
  padding: 70rpx 40rpx;
  text-align: center;
  background: var(--v7-card);
  border-radius: 30rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.empty-seal {
  width: 132rpx;
  height: 132rpx;
  border-radius: 40rpx;
  background: #F3EFE5;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}
.empty-emoji { font-size: 60rpx; line-height: 1; }
.empty-title { margin-top: 24rpx; font-size: 28rpx; font-weight: 800; color: #22302A; display: block; }
.empty-desc { margin-top: 10rpx; font-size: 21rpx; line-height: 1.6; color: #AEB6AE; display: block; }
.empty-btn {
  display: inline-block;
  margin-top: 32rpx;
  padding: 16rpx 46rpx;
  border-radius: 999rpx;
  background: linear-gradient(140deg, #4E7A64, #24493A);
}
.empty-btn-text { font-size: 24rpx; font-weight: 700; color: #FFFDFA; }

.gacha-avatar-wrapper { background: #F3EFE5; }
.gacha-avatar-emoji { font-size: 56rpx; line-height: 1; }
.gacha-name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}
.gacha-rarity {
  margin-left: 8rpx;
  padding: 2rpx 10rpx;
  border-radius: 999rpx;
  font-size: 17rpx;
  font-weight: 800;
}
.rarity-R { background: #EEF4F1; color: #3C6B55; }
.rarity-SR { background: #EFF3F5; color: #74919F; }
.rarity-SSR { background: #F7F1EB; color: #B8874E; }
.rarity-UR { background: #F6E9DD; color: #A9773F; }

.gacha-modal-avatar { font-size: 84rpx; display: block; margin-bottom: 14rpx; }
.gacha-rarity-big {
  display: inline-block;
  margin-top: 10rpx;
  padding: 4rpx 18rpx;
  border-radius: 999rpx;
  font-size: 19rpx;
  font-weight: 800;
}

.modal-btn.chat-btn { background: #EEF4F1; margin-left: 16rpx; }
.modal-btn.chat-btn text { color: var(--v7-green); font-size: 26rpx; font-weight: 700; }

.detail-text.italic { font-style: italic; color: #8E9A91; }

/* 羁绊碎片 */
.bond-section {
  padding-top: 20rpx;
  margin-top: 20rpx;
  border-top: 1rpx dashed var(--v7-line);
}
.bond-progress { margin-bottom: 18rpx; }
.progress-bar {
  height: 8rpx;
  background: rgba(34, 48, 42, 0.07);
  border-radius: 999rpx;
  overflow: hidden;
  margin-bottom: 10rpx;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #A9C6B4, #24493A);
  border-radius: 999rpx;
  transition: width 0.5s ease;
}
.progress-text { font-size: 19rpx; color: #AEB6AE; }
.bond-chapters { display: flex; flex-direction: column; }
.bond-chapter {
  border-radius: 20rpx;
  padding: 18rpx 20rpx;
  margin-bottom: 12rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.bond-chapter.locked {
  background: rgba(255, 253, 250, 0.5);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.bond-chapter.unlocked { background: #F3EFE5; }
.chapter-content .chapter-title {
  font-size: 24rpx;
  font-weight: 800;
  color: var(--v7-green);
  margin-bottom: 8rpx;
  display: block;
}
.chapter-content .chapter-text { font-size: 22rpx; color: #6A776E; line-height: 1.6; display: block; }
.chapter-locked { text-align: center; padding: 6rpx 0; }
.lock-icon { font-size: 28rpx; display: block; margin-bottom: 6rpx; }
.chapter-locked .chapter-title { font-size: 22rpx; color: #BFC7BF; display: block; margin-bottom: 4rpx; }
.chapter-locked .chapter-hint { font-size: 18rpx; color: #CFD6CE; display: block; }

/* ============================================================
   移动端适配（增量覆盖）：统一卡片比例、可读字号、等高质量
   - 原卡片图片高度按 i%2 在 112/150 间切换，同行卡片内部留白不齐
   - 名称/描述字号为 8px/6.5px，真机上几乎不可读
   ============================================================ */
.xt-page.xt-s47 .page-sub { font-size: 12px; line-height: 1.5; }
.xt-page.xt-s47 .chips { gap: 8px; }
.xt-page.xt-s47 .chip { font-size: 12px; padding: 7px 14px; line-height: 1.2; }
.xt-page.xt-s47 .body { padding-bottom: calc(20px + env(safe-area-inset-bottom)); }

.gal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
  gap: 10px;
  align-items: start;
}
.gal-card {
  border-radius: 14px;
  overflow: hidden;
  background: #FFFDFA;
  box-shadow: 0 0 0 1px rgba(30, 42, 36, .10);
  position: relative;
  transition: transform .18s ease;
}
.gal-card:active { transform: scale(.985); }
/* 立绘框：3:4 与素材构图一致，完整人物在框内等比缩放 */
.gal-photo {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 3 / 4;
}
.xt-page.xt-s47 .gal-card uni-image {
  width: 100%;
  height: 100%;
}
.xt-page.xt-s47 .gal-card :deep(uni-image > div),
.xt-page.xt-s47 .gal-card :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.gal-photo-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #F1F6F4, #E7EFEA);
}
.gal-photo-gacha {
  background: linear-gradient(145deg, #B5C7BF, #24493A);
  font-size: 30px;
  color: #FFFDFA;
}
.gal-info { padding: 8px 10px 10px; }
.gal-name { font-size: 14px; font-weight: 800; color: #22302A; line-height: 1.3; }
.gal-name-row { display: flex; align-items: center; gap: 5px; }
.gal-badge {
  flex-shrink: 0;
  font-size: 9.5px;
  font-weight: 800;
  color: #B8874E;
  background: #F7F1EB;
  padding: 1px 5px;
  border-radius: 99px;
}
.gal-desc {
  margin-top: 3px;
  min-height: 2.9em;
  font-size: 11.5px;
  line-height: 1.45;
  color: #AEB6AE;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.gal-create {
  min-height: 196px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 253, 250, .6);
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, .10);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.gal-create-plus {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px dashed #9CBFAA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #24493A;
}
.gal-create-title { margin-top: 8px; font-size: 13px; font-weight: 800; color: #22302A; }
.gal-create-desc { margin-top: 3px; font-size: 11px; color: #AEB6AE; text-align: center; }

.gallery-tip { margin-top: 12px; display: flex; align-items: center; gap: 10px; }
.gallery-tip-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.gallery-tip .t { font-size: 13px; font-weight: 800; line-height: 1.4; }
.gallery-tip .m { margin-top: 2px; font-size: 11.5px; line-height: 1.5; }

.gallery-empty { text-align: center; padding: 26px 16px; }
.gallery-empty .empty-title { font-size: 15px; font-weight: 800; color: #26332C; }
.gallery-empty .empty-desc { margin-top: 6px; font-size: 12px; line-height: 1.65; color: #7C877E; }

@media (max-width: 350px) {
  .gal-name { font-size: 13px; }
  .gal-desc { font-size: 11px; }
  .gal-create { min-height: 180px; }
}
</style>
