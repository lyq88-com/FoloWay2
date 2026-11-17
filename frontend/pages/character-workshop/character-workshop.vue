<template>
  <view class="xt-page xt-s11">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">角色图鉴</view>
          <view class="page-sub">{{ roleTotal }} 位现成角色 · 记忆彼此隔离</view>
        </view>
        <view class="icon-btn" @click="startCreate"><xt-icon name="i-plus" /></view>
      </view>

      <view class="role-hero">
        <image v-if="heroPhoto" :src="heroPhoto" mode="aspectFill" />
        <view v-else class="role-emoji"><text>{{ currentRole.avatar }}</text></view>
        <view class="tx">
          <view class="h3">{{ currentRole.name }}</view>
          <view class="p">{{ heroDesc }}</view>
          <view class="chips">
            <text v-for="(c, i) in heroChips" :key="i" class="chip">{{ c }}</text>
          </view>
        </view>
      </view>

      <view class="role-grid">
        <view
          v-for="r in roleCards"
          :key="r.id"
          class="role"
          :class="{ on: r.id === currentRole.id }"
          @click="selectRole(r)">
          <image v-if="r.photo" :src="r.photo" mode="aspectFill" />
          <view v-else class="role-ph"><text>{{ r.avatar }}</text></view>
          <text>{{ r.name }}</text>
        </view>
      </view>

      <view class="custom-role" @click="startCreate">
        <view class="ci"><xt-icon name="i-plus" /></view>
        <view class="tx">
          <view class="t">创建自定义伙伴</view>
          <view class="m">设定性格、说话方式与专属记忆</view>
        </view>
        <view class="ar"><xt-icon name="i-right" /></view>
      </view>

      <view class="ai-rec" style="margin-top: 9px">
        <view class="sp"><xt-icon name="i-brain" /></view>
        <view class="tx">
          <view class="k">记忆隔离已开启</view>
          <view class="p">每位伙伴只记得与你单独发生的事，不会串线。</view>
        </view>
      </view>
    </view>

    <!-- ===== 创作 / 编辑面板 ===== -->
    <view v-if="editorOpen" class="ws-editor">
      <view class="ws-top">
        <view class="ws-back" @click="closeEditor"><xt-icon name="i-left" /></view>
        <view class="ws-title">
          <text class="ws-t">{{ isEditMode ? '编辑这位伙伴' : '创造另一个她' }}</text>
          <text class="ws-s">先选性格底色，再给她一个声音与一句话</text>
        </view>
        <view v-if="isEditMode" class="ws-del" @click="confirmDelete"><text class="delete-icon">🗑</text></view>
      </view>

      <scroll-view scroll-y class="ws-scroll">
        <view class="workshop-body">
          <!-- 实时预览卡 -->
          <view class="preview-section" :style="{ background: previewBg }">
            <view class="preview-top">
              <view class="preview-tag"><text class="preview-tag-text">实时预览</text></view>
              <view class="preview-mode-tabs">
                <view class="mode-tab" :class="{ active: previewMode === 'head' }" @click="previewMode = 'head'">
                  <text>头像</text>
                </view>
                <view class="mode-tab" :class="{ active: previewMode === 'fullbody' }" @click="previewMode = 'fullbody'">
                  <text>立绘</text>
                </view>
              </view>
            </view>

            <view class="preview-stage">
              <view class="preview-canvas">
                <view v-if="useCustomAvatar" class="custom-avatar-preview">
                  <image :src="customAvatarUrl" class="custom-avatar-img" mode="aspectFill" />
                </view>
                <view v-else class="preview-sprite-wrap" :class="{ 'preview-bounce': previewBounce }">
                  <view v-if="previewMode === 'head'" class="sprite-head-render" v-html="previewHeadSVG"></view>
                  <view v-else class="sprite-fullbody-render" v-html="previewFullBodySVG"></view>
                </view>
              </view>

              <view class="preview-name-wrap">
                <text class="preview-name">{{ form.name || '未命名伙伴' }}</text>
                <text class="preview-catchphrase" v-if="form.catchphrase">"{{ form.catchphrase }}"</text>
              </view>
            </view>

            <view class="avatar-upload-row">
              <view class="upload-btn" @click="chooseAvatarImage">
                <text class="upload-icon">📷</text>
                <text class="upload-text">{{ useCustomAvatar ? '更换图片头像' : '上传图片头像' }}</text>
              </view>
              <view v-if="useCustomAvatar" class="reset-sprite-btn" @click="resetCustomAvatar">
                <text class="reset-text">改用DIY形象</text>
              </view>
            </view>
          </view>

          <!-- 主 Tab -->
          <view class="main-tabs">
            <view class="main-tab" :class="{ active: activeTab === 'diy' }" @click="activeTab = 'diy'">
              <text>形象 DIY</text>
            </view>
            <view class="main-tab" :class="{ active: activeTab === 'persona' }" @click="activeTab = 'persona'">
              <text>人设设定</text>
            </view>
          </view>

          <!-- 形象DIY面板 -->
          <view v-if="activeTab === 'diy'" class="diy-panel panel-card">
            <view class="panel-head">
              <text class="sec-title">形象 DIY</text>
              <text class="sec-more">细节决定像不像</text>
            </view>

            <view class="diy-group">
              <text class="group-title">脸型</text>
              <view class="option-row">
                <view
                  v-for="opt in faceShapeOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.faceShape === opt.value }"
                  @click="updateDiy('faceShape', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">肤色</text>
              <view class="color-row">
                <view
                  v-for="color in skinColorOptions"
                  :key="color.value"
                  class="color-dot"
                  :class="{ active: diy.skinColor === color.value }"
                  :style="{ background: color.value }"
                  @click="updateDiy('skinColor', color.value)"></view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">眼型</text>
              <view class="option-row">
                <view
                  v-for="opt in eyeStyleOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.eyeStyle === opt.value }"
                  @click="updateDiy('eyeStyle', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">瞳色</text>
              <view class="color-row">
                <view
                  v-for="color in eyeColorOptions"
                  :key="color.value"
                  class="color-dot"
                  :class="{ active: diy.eyeColor === color.value }"
                  :style="{ background: color.value }"
                  @click="updateDiy('eyeColor', color.value)"></view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">眉毛</text>
              <view class="option-row">
                <view
                  v-for="opt in eyebrowOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.eyebrowStyle === opt.value }"
                  @click="updateDiy('eyebrowStyle', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">嘴巴</text>
              <view class="option-row">
                <view
                  v-for="opt in mouthOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.mouthStyle === opt.value }"
                  @click="updateDiy('mouthStyle', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">发型</text>
              <view class="option-row option-row-wrap">
                <view
                  v-for="opt in hairStyleOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.hairStyle === opt.value }"
                  @click="updateDiy('hairStyle', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">发色</text>
              <view class="color-row">
                <view
                  v-for="color in hairColorOptions"
                  :key="color.value"
                  class="color-dot"
                  :class="{ active: diy.hairColor === color.value }"
                  :style="{ background: color.value }"
                  @click="updateDiy('hairColor', color.value)"></view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">服装</text>
              <view class="option-row option-row-wrap">
                <view
                  v-for="opt in outfitOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.outfitStyle === opt.value }"
                  @click="updateDiy('outfitStyle', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">服装颜色</text>
              <view class="color-row">
                <view
                  v-for="color in outfitColorOptions"
                  :key="color.value"
                  class="color-dot"
                  :class="{ active: diy.outfitColor === color.value }"
                  :style="{ background: color.value }"
                  @click="updateDiy('outfitColor', color.value)"></view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">配饰</text>
              <view class="option-row option-row-wrap">
                <view
                  v-for="opt in accessoryOptions"
                  :key="opt.value"
                  class="option-chip"
                  :class="{ active: diy.accessory === opt.value }"
                  @click="updateDiy('accessory', opt.value)">
                  <text>{{ opt.label }}</text>
                </view>
              </view>
            </view>

            <view class="diy-group">
              <text class="group-title">腮红</text>
              <view class="color-row">
                <view
                  v-for="color in blushColorOptions"
                  :key="color.value"
                  class="color-dot"
                  :class="{ active: diy.blushColor === color.value }"
                  :style="{ background: color.value }"
                  @click="updateDiy('blushColor', color.value)"></view>
              </view>
            </view>
          </view>

          <!-- 人设设定面板 -->
          <view v-if="activeTab === 'persona'" class="persona-panel panel-card">
            <view class="panel-head">
              <text class="sec-title">人设设定</text>
              <text class="sec-more">写得越具体，TA 越像 TA 自己</text>
            </view>

            <view class="form-group">
              <text class="form-label">伙伴昵称 <text class="required">*</text></text>
              <input class="form-input" v-model="form.name" placeholder="给你的伙伴起个名字" maxlength="12" />
            </view>

            <view class="form-group">
              <text class="form-label">专属口头禅</text>
              <input class="form-input" v-model="form.catchphrase" placeholder="一句最能代表TA的话" maxlength="30" />
            </view>

            <view class="form-group">
              <text class="form-label">说话语气风格 <text class="required">*</text></text>
              <text class="form-hint">选择TA最核心的说话风格，决定对话的语气和措辞</text>
              <view class="persona-grid">
                <view
                  v-for="opt in personalityOptions"
                  :key="opt.value"
                  class="persona-card"
                  :class="{ active: form.personalityType === opt.value }"
                  @click="selectPersonality(opt.value)">
                  <text class="persona-emoji">{{ opt.emoji }}</text>
                  <text class="persona-name">{{ opt.label }}</text>
                  <text class="persona-desc">{{ opt.desc }}</text>
                </view>
              </view>
            </view>

            <view class="form-group">
              <text class="form-label">性格标签</text>
              <text class="form-hint">选择1-4个标签，让TA的形象更立体</text>
              <view class="trait-pool">
                <view
                  v-for="trait in traitPool"
                  :key="trait"
                  class="trait-chip"
                  :class="{ active: form.traits.includes(trait) }"
                  @click="toggleTrait(trait)">
                  <text>{{ trait }}</text>
                </view>
              </view>
            </view>

            <view class="form-group">
              <text class="form-label">独立语气词</text>
              <text class="form-hint">TA说话时常用的语气词，让对话更独特（例如：喵~、呀、嘻嘻）</text>
              <input class="form-input" v-model="form.voiceWords" placeholder="用逗号分隔，如：喵,呀,嘻嘻" maxlength="40" />
            </view>

            <view class="form-group">
              <text class="form-label">角色简介</text>
              <textarea class="form-textarea" v-model="form.description" placeholder="一句话描述TA是谁" maxlength="60" />
            </view>

            <view class="form-group">
              <text class="form-label">人物背景故事</text>
              <textarea
                class="form-textarea form-textarea-lg"
                v-model="form.background"
                placeholder="TA从哪里来？有什么经历？这会影响TA的说话内容"
                maxlength="200" />
              <text class="form-counter">{{ (form.background || '').length }}/200</text>
            </view>

            <view class="advanced-title">
              <text class="adv-title-text">高级设定</text>
              <text class="adv-sub">写得越具体，TA 越像 TA 自己</text>
            </view>

            <view class="form-group">
              <text class="form-label">TA 怎么称呼你</text>
              <input class="form-input" v-model="form.nickname" placeholder="留空就称呼「你」，例如：笨蛋 / 小七" maxlength="20" />
              <text class="form-hint">填了之后 TA 会稳定用这个称呼，不会换来换去</text>
            </view>

            <view class="form-group">
              <text class="form-label">雷区 · 说话禁忌</text>
              <textarea
                class="form-textarea form-textarea-lg"
                v-model="form.taboos"
                placeholder="绝对不能提的事、不能说的话。例：不许提它的体重；不要说「猫就是高冷」"
                maxlength="200" />
              <text class="form-hint">这些是硬约束，TA 任何情况下都不会碰</text>
            </view>

            <view class="form-group">
              <text class="form-label">表达习惯</text>
              <textarea
                class="form-textarea"
                v-model="form.expressionHabits"
                placeholder="句式、语气词、口头禅。例：句子短，结尾爱带「哼」"
                maxlength="150" />
            </view>

            <view class="form-group">
              <text class="form-label">TA 生气时是什么样子</text>
              <textarea class="form-textarea" v-model="form.angryStyle" placeholder="例：背过身去不看你，但尾巴还在晃" maxlength="150" />
            </view>

            <view class="form-group">
              <text class="form-label">TA 开心时是什么样子</text>
              <textarea class="form-textarea" v-model="form.happyStyle" placeholder="例：会蹭你的手，话变多，语速变快" maxlength="150" />
            </view>

            <view class="form-group">
              <text class="form-label">音色</text>
              <text class="form-hint">音色会跟着人设走，通话和语音消息都用这个声音</text>
              <view class="emoji-row">
                <view
                  v-for="t in voiceToneOptions"
                  :key="t.key"
                  class="tone-chip"
                  :class="{ active: form.voiceTone === t.key }"
                  @click="form.voiceTone = t.key">
                  <text class="tone-label">{{ t.label }}</text>
                  <text class="tone-desc">{{ t.desc }}</text>
                </view>
              </view>
            </view>

            <view class="form-group">
              <text class="form-label">当前心情状态</text>
              <text class="form-hint">状态会影响 TA 此刻说话的情绪，之后在角色页也能改</text>
              <view class="emoji-row">
                <view
                  v-for="m in moodOptions"
                  :key="m.key"
                  class="emoji-chip mood-chip"
                  :class="{ active: form.mood === m.key }"
                  @click="form.mood = m.key">
                  <text>{{ m.emoji }} {{ m.label }}</text>
                </view>
              </view>
            </view>

            <view class="form-group">
              <text class="form-label">Emoji标识</text>
              <text class="form-hint">用于地图、聊天的辅助显示</text>
              <view class="emoji-row">
                <view
                  v-for="emo in emojiOptions"
                  :key="emo"
                  class="emoji-chip"
                  :class="{ active: form.avatar === emo }"
                  @click="form.avatar = emo">
                  <text>{{ emo }}</text>
                </view>
              </view>
            </view>

            <view class="preview-chat">
              <view class="pc-head">
                <text class="pc-title">试聊一句</text>
                <text class="pc-sub">设定完整度 {{ personaCompleteness }}% · 创建前先看看 TA 像不像</text>
              </view>
              <view class="pc-row">
                <input
                  class="pc-input"
                  v-model="testMessage"
                  placeholder="比如：今天好累啊 / 你觉得我是什么样的人"
                  maxlength="60" />
                <view class="pc-btn" :class="{ 'pc-btn-busy': previewLoading }" @click="runPreview">
                  <text>{{ previewLoading ? '想想…' : '试聊' }}</text>
                </view>
              </view>
              <view v-if="previewReply" class="pc-bubble">
                <text class="pc-name">{{ form.name || 'TA' }}</text>
                <text class="pc-text">{{ previewReply }}</text>
              </view>
              <view v-if="previewError" class="pc-err">
                <text>{{ previewError }}</text>
              </view>
              <text class="pc-tip">试聊用的是和正式聊天同一套人设规则，所以像不像一眼就知道</text>
            </view>
          </view>

          <view class="bottom-safe-area"></view>
        </view>
      </scroll-view>

      <view class="ws-save">
        <view class="save-btn" :class="{ disabled: !canSave }" @click="saveCharacter">
          <text>{{ isEditMode ? '保存修改' : '创建伙伴' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import {
  FACE_SHAPES,
  EYE_STYLES,
  HAIR_STYLES,
  OUTFIT_STYLES,
  buildSpriteFromConfig,
  registerCustomSprite,
  renderHeadSVG,
  renderFullBodySVG
} from '@/common/character-sprites.js'
import { PERSONALITY_TYPES, PERSONALITY_CONFIG } from '@/common/ai-dialogue-engine.js'
import { syncCustomCharacter, removeCustomCharacterSync } from '@/common/custom-character-init.js'
// ↓↓↓ 陪伴感增强 v3：自捏角色上云（雷区/禁忌/表达习惯/生气开心/音色） ↓↓↓
import personaApi from '@/api/persona'
// ↑↑↑ 新增结束 ↑↑↑
import { CHARACTERS, STYLE_LABELS, getCharacterById } from '@/common/ai-characters'
import { getActivePartner, getPartnerAvatar, getPartnerPhoto } from '@/common/ai-partner'

export default {
  data() {
    return {
      isEditMode: false,
      editId: null,
      editorOpen: false,
      activeTab: 'diy',
      previewMode: 'head',
      previewBounce: false,
      useCustomAvatar: false,
      customAvatarUrl: '',
      // DIY形象配置
      diy: {
        faceShape: FACE_SHAPES.OVAL,
        skinColor: '#FEF0E0',
        eyeStyle: EYE_STYLES.ALMOND,
        eyeColor: '#6B8E6B',
        eyebrowStyle: 'soft-arch',
        mouthStyle: 'gentle',
        hairStyle: HAIR_STYLES.MEDIUM_WAVE,
        hairColor: '#7BA08B',
        outfitStyle: OUTFIT_STYLES.DRESS,
        outfitColor: '#7BA08B',
        accessory: '',
        blushColor: '#FFB6B0'
      },
      // 人设表单
      form: {
        name: '',
        catchphrase: '',
        personalityType: PERSONALITY_TYPES.GENTLE_HEALER,
        traits: [],
        voiceWords: '',
        description: '',
        background: '',
        avatar: '🌟',
        // ↓↓↓ 陪伴感增强 v3：高级设定 ↓↓↓
        nickname: '',          // TA 怎么称呼用户
        taboos: '',            // 雷区 / 说话禁忌
        expressionHabits: '',  // 表达习惯
        angryStyle: '',        // 生气时是什么样子
        happyStyle: '',        // 开心时是什么样子
        voiceTone: 'warm',     // 音色
        mood: 'normal'         // 当前心情状态
      },
      voiceToneOptions: [
        { key: 'soft', label: '轻柔', desc: '轻声慢语' },
        { key: 'bright', label: '清亮', desc: '明快上扬' },
        { key: 'warm', label: '温润', desc: '中低柔和' },
        { key: 'cool', label: '清冷', desc: '克制平稳' },
        { key: 'husky', label: '低沉', desc: '磁性气声' }
      ],
      moodOptions: [
        { key: 'normal', label: '平常', emoji: '🌿' },
        { key: 'happy', label: '开心', emoji: '☀️' },
        { key: 'tired', label: '疲惫', emoji: '🌙' },
        { key: 'sad', label: '低落', emoji: '🌧️' },
        { key: 'angry', label: '不高兴', emoji: '⚡' },
        { key: 'quiet', label: '想静静', emoji: '🫧' }
      ],
      cloudRoleId: 0,  // 后端 ai_roles.id（上云成功后回填）
      saving: false,   // 防重复提交（上云是 async，连点会创建两个角色）
      // ↓↓↓ v3.1：创建前试聊 ↓↓↓
      testMessage: '',
      previewLoading: false,
      previewReply: '',
      previewError: ''
    }
  },
  computed: {
    currentRole() {
      return getActivePartner()
    },
    heroPhoto() {
      return getPartnerPhoto(this.currentRole) || ''
    },
    heroDesc() {
      return this.currentRole.description || this.currentRole.personality || ''
    },
    heroChips() {
      const c = this.currentRole
      const chips = []
      const label = STYLE_LABELS[c.style]
      if (label) chips.push(label)
      ;(c.personality || '').split('、').slice(0, 2).forEach(t => {
        if (t) chips.push(t)
      })
      return chips
    },
    roleCards() {
      const presets = CHARACTERS.slice(0, 10).map(c => ({
        id: c.id,
        name: c.name,
        avatar: c.avatar,
        photo: getPartnerAvatar(c) || ''
      }))
      const customs = (this.$store.state.customCharacters || [])
        .filter(c => c && c.id)
        .slice(0, 4)
        .map(c => ({
          id: c.id,
          name: c.name,
          avatar: c.avatar || '🌟',
          photo: getPartnerAvatar(c) || ''
        }))
      return [...presets, ...customs]
    },
    roleTotal() {
      return CHARACTERS.length + ((this.$store.state.customCharacters || []).length)
    },
    canSave() {
      return !!(this.form.name && this.form.name.trim() && this.form.personalityType)
    },
    /**
     * 设定完整度：让用户直观看到"还差什么"。
     * 只统计人设维度（形象 DIY 不算），因为决定 TA 像不像人的就是这些文字设定。
     */
    personaCompleteness() {
      const f = this.form || {}
      const checks = [
        !!(f.name || '').trim(),
        !!(f.catchphrase || '').trim(),
        !!f.personalityType,
        Array.isArray(f.traits) && f.traits.length > 0,
        !!(f.voiceWords || '').trim(),
        !!(f.description || '').trim(),
        !!(f.background || '').trim(),
        !!(f.nickname || '').trim(),
        !!(f.taboos || '').trim(),
        !!(f.expressionHabits || '').trim(),
        !!(f.angryStyle || '').trim(),
        !!(f.happyStyle || '').trim()
      ]
      const ok = checks.filter(Boolean).length
      return Math.round((ok / checks.length) * 100)
    },
    // 当前 DIY 配置对应的 spriteData（响应式，DIY 变化时自动重算）
    currentSpriteData() {
      return buildSpriteFromConfig(this.diy)
    },
    // 预览头部 SVG（响应式）
    previewHeadSVG() {
      try {
        return renderHeadSVG(this.currentSpriteData, { size: 200 })
      } catch (e) {
        console.error('渲染头部SVG失败', e)
        return ''
      }
    },
    // 预览全身 SVG（响应式）
    previewFullBodySVG() {
      try {
        return renderFullBodySVG(this.currentSpriteData, { width: 200, height: 250 })
      } catch (e) {
        console.error('渲染全身SVG失败', e)
        return ''
      }
    },
    previewBg() {
      // 根据发色和服装色生成柔和渐变背景
      const c1 = this.diy.hairColor
      const c2 = this.diy.outfitColor
      return `linear-gradient(135deg, ${c1}22 0%, ${c2}22 100%)`
    },
    // 选项数据
    faceShapeOptions() {
      return [
        { value: FACE_SHAPES.ROUND, label: '圆脸' },
        { value: FACE_SHAPES.OVAL, label: '鹅蛋脸' },
        { value: FACE_SHAPES.CHUBBY, label: '婴儿肥' },
        { value: FACE_SHAPES.SOFT_SQUARE, label: '柔和方' }
      ]
    },
    eyeStyleOptions() {
      return [
        { value: EYE_STYLES.ROUND, label: '大圆眼' },
        { value: EYE_STYLES.ALMOND, label: '杏仁眼' },
        { value: EYE_STYLES.DROOPY, label: '垂眼' },
        { value: EYE_STYLES.CAT, label: '猫眼' },
        { value: EYE_STYLES.SPARKLE, label: '星星眼' },
        { value: EYE_STYLES.NARROW, label: '细长眼' }
      ]
    },
    eyebrowOptions() {
      return [
        { value: 'soft-arch', label: '柔和弧' },
        { value: 'straight', label: '平直' },
        { value: 'angled', label: '上扬' },
        { value: 'thick', label: '浓眉' }
      ]
    },
    mouthOptions() {
      return [
        { value: 'small-smile', label: '浅笑' },
        { value: 'wide-smile', label: '大笑' },
        { value: 'gentle', label: '温柔' },
        { value: 'neutral', label: '平静' }
      ]
    },
    hairStyleOptions() {
      return [
        { value: HAIR_STYLES.SHORT_BOB, label: '齐耳短发' },
        { value: HAIR_STYLES.LONG_STRAIGHT, label: '长直发' },
        { value: HAIR_STYLES.CURLY, label: '卷发' },
        { value: HAIR_STYLES.TWIN_TAILS, label: '双马尾' },
        { value: HAIR_STYLES.PIXIE, label: '精灵短发' },
        { value: HAIR_STYLES.MEDIUM_WAVE, label: '中长波浪' },
        { value: HAIR_STYLES.LONG_BRAID, label: '长辫子' },
        { value: HAIR_STYLES.HALF_UP, label: '半扎发' },
        { value: HAIR_STYLES.SPIKY, label: '刺头' },
        { value: HAIR_STYLES.MESSY, label: '蓬松乱发' },
        { value: HAIR_STYLES.NEAT_SIDE, label: '侧分短发' },
        { value: HAIR_STYLES.ANCIENT_BUN, label: '古风发髻' }
      ]
    },
    outfitOptions() {
      return [
        { value: OUTFIT_STYLES.DRESS, label: '连衣裙' },
        { value: OUTFIT_STYLES.HOODIE, label: '卫衣' },
        { value: OUTFIT_STYLES.SHIRT, label: '衬衫' },
        { value: OUTFIT_STYLES.HANFU, label: '汉服' },
        { value: OUTFIT_STYLES.TECH_SUIT, label: '科技装' },
        { value: OUTFIT_STYLES.SWEATER, label: '针织衫' },
        { value: OUTFIT_STYLES.SPORTSWEAR, label: '运动服' },
        { value: OUTFIT_STYLES.CROP_JACKET, label: '短夹克' },
        { value: OUTFIT_STYLES.TURTLENECK, label: '高领' },
        { value: OUTFIT_STYLES.MAGIC_ROBE, label: '法袍' },
        { value: OUTFIT_STYLES.ARMOR, label: '轻甲' },
        { value: OUTFIT_STYLES.CARDIGAN, label: '开衫' }
      ]
    },
    accessoryOptions() {
      return [
        { value: '', label: '无' },
        { value: 'leaf-crown', label: '叶冠' },
        { value: 'star-hairpin', label: '星发夹' },
        { value: 'glasses', label: '眼镜' },
        { value: 'cat-ears', label: '猫耳' },
        { value: 'ribbon', label: '丝带' },
        { value: 'choker', label: '颈链' },
        { value: 'headband', label: '头带' },
        { value: 'hair-clips', label: '发卡' },
        { value: 'visor', label: '面罩' },
        { value: 'flower-clip', label: '花夹' },
        { value: 'fan', label: '折扇' }
      ]
    },
    skinColorOptions() {
      return [
        { value: '#FEF0E0', label: '暖白' },
        { value: '#FFF5EE', label: '粉白' },
        { value: '#FFF8ED', label: '蜜白' },
        { value: '#FFEFD5', label: '麦色' },
        { value: '#F5DEB3', label: '小麦' },
        { value: '#F5F7FA', label: '冷白' }
      ]
    },
    eyeColorOptions() {
      return [
        { value: '#6B8E6B', label: '青绿' },
        { value: '#7B4A3A', label: '棕' },
        { value: '#4682B4', label: '蓝' },
        { value: '#9B59B6', label: '紫' },
        { value: '#CC5599', label: '粉' },
        { value: '#363636', label: '黑' },
        { value: '#FF6B9D', label: '樱粉' },
        { value: '#00CED1', label: '青' }
      ]
    },
    hairColorOptions() {
      return [
        { value: '#7BA08B', label: '青绿' },
        { value: '#FFB7B2', label: '樱粉' },
        { value: '#FF6B9D', label: '亮粉' },
        { value: '#DDA0DD', label: '丁香' },
        { value: '#FFA500', label: '橙' },
        { value: '#4A3728', label: '深棕' },
        { value: '#2C2C2C', label: '黑' },
        { value: '#C0C0C0', label: '银' },
        { value: '#8B0000', label: '酒红' },
        { value: '#00CED1', label: '青' },
        { value: '#228B22', label: '森绿' },
        { value: '#7B68EE', label: '紫罗兰' }
      ]
    },
    outfitColorOptions() {
      return [
        { value: '#7BA08B', label: '青绿' },
        { value: '#FFB7B2', label: '粉' },
        { value: '#FF6B9D', label: '亮粉' },
        { value: '#C44DFF', label: '紫' },
        { value: '#FFA500', label: '橙' },
        { value: '#4A3728', label: '棕' },
        { value: '#4682B4', label: '蓝' },
        { value: '#8B6914', label: '金棕' },
        { value: '#191970', label: '深蓝' },
        { value: '#FF4500', label: '红' },
        { value: '#2E8B57', label: '森绿' },
        { value: '#708090', label: '灰' }
      ]
    },
    blushColorOptions() {
      return [
        { value: '#FFB6B0', label: '粉' },
        { value: '#FF9EC1', label: '樱粉' },
        { value: '#FFB347', label: '橙' },
        { value: '#FFD700', label: '金' },
        { value: '#B0C4DE', label: '蓝' },
        { value: '#90EE90', label: '绿' }
      ]
    },
    personalityOptions() {
      const map = {
        [PERSONALITY_TYPES.GENTLE_HEALER]: { emoji: '🌿', desc: '柔软共情细腻' },
        [PERSONALITY_TYPES.ENERGETIC_SUNNY]: { emoji: '☀️', desc: '活泼积极热情' },
        [PERSONALITY_TYPES.COOL_RATIONAL]: { emoji: '❄️', desc: '清醒理智克制' },
        [PERSONALITY_TYPES.HUMOROUS_RELAXED]: { emoji: '😜', desc: '幽默轻松搞笑' },
        [PERSONALITY_TYPES.GENTLE_SCHOLAR]: { emoji: '📚', desc: '耐心博学温柔' },
        [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: { emoji: '😤', desc: '嘴硬心软督促' },
        [PERSONALITY_TYPES.LAZY_BUDDHA]: { emoji: '🍃', desc: '慢悠悠松弛' },
        [PERSONALITY_TYPES.MATURE_STABLE]: { emoji: '🌙', desc: '通透开导靠谱' },
        [PERSONALITY_TYPES.CLEAN_BOY]: { emoji: '🌸', desc: '清爽纯真治愈' },
        [PERSONALITY_TYPES.SWEET_GIRL]: { emoji: '🍭', desc: '软萌贴心细腻' },
        [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: { emoji: '⚡', desc: '拆解烦恼理清' },
        [PERSONALITY_TYPES.ARTISTIC_POETIC]: { emoji: '🎨', desc: '氛围浪漫走心' },
        [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: { emoji: '🔥', desc: '打气超强坚定' },
        [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: { emoji: '🍃', desc: '抚平焦虑放下' },
        [PERSONALITY_TYPES.COOL_FREE]: { emoji: '😎', desc: '干脆利落自信' },
        [PERSONALITY_TYPES.WARM_LISTENER]: { emoji: '❤️', desc: '无条件接纳陪伴' },
        [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: { emoji: '📝', desc: '温柔督促坚持' },
        [PERSONALITY_TYPES.DREAMY_GENTLE]: { emoji: '🦋', desc: '浪漫梦幻治愈' },
        [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: { emoji: '💎', desc: '三观正帮你清醒' },
        [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: { emoji: '💖', desc: '偏爱式专属甜' }
      }
      return Object.keys(PERSONALITY_CONFIG).map(key => {
        const cfg = PERSONALITY_CONFIG[key]
        const extra = map[key] || { emoji: '✨', desc: cfg.tone }
        return {
          value: key,
          label: cfg.name,
          emoji: extra.emoji,
          desc: extra.desc
        }
      })
    },
    traitPool() {
      return [
        '温柔', '元气', '理智', '幽默', '细腻', '阳光', '高冷', '可爱',
        '成熟', '少年', '神秘', '开朗', '内向', '外向', '感性', '理性',
        '治愈', '热血', '佛系', '傲娇', '贴心', '独立', '梦幻', '清醒',
        '包容', '严格', '浪漫', '务实', '乐观', '悲观', '好奇', '沉稳'
      ]
    },
    emojiOptions() {
      return ['🌟', '🌿', '🌸', '💫', '🌙', '✨', '🐱', '🦋', '🔥', '💧', '🍃', '💖']
    }
  },
  watch: {
    // DIY变化时触发弹跳动画反馈（预览SVG通过computed自动更新）
    diy: {
      handler() {
        this.previewBounce = true
        clearTimeout(this._bounceTimer)
        this._bounceTimer = setTimeout(() => {
          this.previewBounce = false
        }, 400)
      },
      deep: true,
      immediate: false
    }
  },
  onLoad(options) {
    // 编辑模式
    if (options && options.editId) {
      this.editorOpen = true
      this.initEditMode(options.editId)
    }
  },
  beforeDestroy() {
    if (this._bounceTimer) {
      clearTimeout(this._bounceTimer)
    }
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    startCreate() {
      this.editorOpen = true
    },
    closeEditor() {
      this.editorOpen = false
      if (this.isEditMode) {
        uni.navigateBack()
      }
    },
    selectRole(role) {
      this.$store.commit('setAiConfig', { avatarType: role.id })
      uni.showToast({ title: `已切换到 ${role.name}`, icon: 'none' })
    },
    updateDiy(key, value) {
      this.diy[key] = value
    },
    selectPersonality(value) {
      this.form.personalityType = value
    },
    toggleTrait(trait) {
      const idx = this.form.traits.indexOf(trait)
      if (idx >= 0) {
        this.form.traits.splice(idx, 1)
      } else {
        if (this.form.traits.length >= 4) {
          uni.showToast({ title: '最多选4个标签', icon: 'none' })
          return
        }
        this.form.traits.push(trait)
      }
    },
    chooseAvatarImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (path) {
            this.customAvatarUrl = path
            this.useCustomAvatar = true
          }
        },
        fail: () => {
          uni.showToast({ title: '取消选择', icon: 'none' })
        }
      })
    },
    resetCustomAvatar() {
      this.useCustomAvatar = false
      this.customAvatarUrl = ''
    },
    initEditMode(editId) {
      const list = this.$store.state.customCharacters || []
      const target = list.find(c => c.id === editId)
      if (!target) {
        uni.showToast({ title: '未找到该角色', icon: 'none' })
        return
      }
      this.isEditMode = true
      this.editId = editId
      // 恢复DIY
      if (target.diy) {
        this.diy = { ...this.diy, ...target.diy }
      }
      // 恢复人设
      this.form = {
        name: target.name || '',
        catchphrase: target.catchphrase || '',
        personalityType: target.personalityType || PERSONALITY_TYPES.GENTLE_HEALER,
        traits: Array.isArray(target.traits) ? [...target.traits] : [],
        voiceWords: target.voiceWords || '',
        description: target.description || '',
        background: target.background || '',
        avatar: target.avatar || '🌟',
        // ↓↓↓ v3.1：高级设定也要能回显，否则"编辑"等于把上次填的雷区/称呼全清空 ↓↓↓
        nickname: target.nickname || '',
        taboos: target.taboos || '',
        expressionHabits: target.expressionHabits || '',
        angryStyle: target.angryStyle || '',
        happyStyle: target.happyStyle || '',
        voiceTone: target.voiceTone || 'warm',
        mood: target.mood || 'normal'
      }
      // 云端角色 id（编辑时走 update，不再重复创建一条）
      this.cloudRoleId = target.roleId || 0
      // 恢复自定义头像
      if (target.useCustomAvatar && target.customAvatarUrl) {
        this.useCustomAvatar = true
        this.customAvatarUrl = target.customAvatarUrl
      }
    },
    buildCharacterData() {
      // 构建sprite
      const sprite = buildSpriteFromConfig(this.diy)
      // 解析语气词
      const voiceWords = (this.form.voiceWords || '')
        .split(/[，,、\s]+/)
        .map(w => w.trim())
        .filter(Boolean)
      // 颜色配置（用于画廊卡片背景）
      const colors = {
        primary: this.diy.outfitColor,
        secondary: this.diy.hairColor,
        accent: sprite.hair.highlight,
        light: this.lightenHex(this.diy.outfitColor, 0.5),
        dark: this.diy.outfitColor
      }
      // phrases（占位，对话引擎会根据 personalityType 动态生成）
      const phrases = {
        morning: [this.form.catchphrase || '早安~'],
        comfort: ['我在呢~'],
        celebrate: ['太棒了！'],
        catchphrase: this.form.catchphrase || ''
      }
      const id = this.isEditMode ? this.editId : ('custom_' + Date.now() + '_' + Math.floor(Math.random() * 1000))
      return {
        id,
        name: this.form.name.trim(),
        style: 'custom',
        gender: 'unknown',
        description: this.form.description || `自定义AI伙伴`,
        personality: this.form.traits.join('、') || '自定义',
        personalityType: this.form.personalityType,
        avatar: this.form.avatar || '🌟',
        colors,
        catchphrase: this.form.catchphrase || '',
        traits: this.form.traits.length ? this.form.traits : ['自定义'],
        voiceStyle: PERSONALITY_CONFIG[this.form.personalityType]?.name || '自定义',
        voiceWords,
        background: this.form.background || '',
        phrases,
        // 视觉与DIY配置
        diy: { ...this.diy },
        sprite,
        // 自定义头像
        useCustomAvatar: this.useCustomAvatar,
        customAvatarUrl: this.customAvatarUrl,
        isCustom: true,
        createdAt: Date.now(),
        // ↓↓↓ 陪伴感增强 v3：高级设定随角色一起带出去 ↓↓↓
        nickname: this.form.nickname || '',
        taboos: this.form.taboos || '',
        expressionHabits: this.form.expressionHabits || '',
        angryStyle: this.form.angryStyle || '',
        happyStyle: this.form.happyStyle || '',
        voiceTone: this.form.voiceTone || 'warm',
        mood: this.form.mood || 'normal'
      }
    },
    /**
     * ↓↓↓ 陪伴感增强 v3 ↓↓↓
     * 把自捏角色同步到后端 ai_roles（雷区/禁忌/表达习惯/生气开心/音色/心情）
     * 只有上云后，聊天链路才能读到这些设定；失败时静默降级，
     * 本地角色照常可用，绝不影响原有创建流程。
     *
     * v3.1 补充：
     * 1. 口头禅 / 语气词 / 语气风格说明也一起上云（否则模型只知道"性格标签"，不知道 TA 怎么说话）
     * 2. 返回 roleKey 并由调用方写进本地角色 —— 聊天时用它才能查到角色、隔离记忆
     *    （本地 id 是前端造的 custom_时间戳，云端是 custom_用户id，两者不是一回事）
     */
    buildCloudPayload(data) {
      const cfg = PERSONALITY_CONFIG[this.form.personalityType] || {}
      const traits = (data.traits || []).filter(t => t && t !== '自定义')
      return {
        name: data.name,
        avatar: data.avatar,
        personality: traits.length ? traits.join('、') : (data.personality || ''),
        description: data.description || '',
        backstory: data.background || '',
        speechStyle: cfg.name || data.voiceStyle || '',
        speechTone: cfg.tone || '',
        catchphrase: data.catchphrase || '',
        voiceWords: (data.voiceWords || []).join('、'),
        taboos: data.taboos || '',
        expressionHabits: data.expressionHabits || '',
        angryStyle: data.angryStyle || '',
        happyStyle: data.happyStyle || '',
        voiceTone: data.voiceTone || 'warm',
        nickname: data.nickname || '',
        mood: data.mood || 'normal'
      }
    },

    async syncRoleToCloud(data) {
      try {
        const payload = this.buildCloudPayload(data)
        const call = this.cloudRoleId
          ? personaApi.updateRole(this.cloudRoleId, payload)
          : personaApi.createRole(payload)
        // 6 秒兜底：网络卡住也不能把"保存"按钮焊死
        const timeout = new Promise(resolve => setTimeout(() => resolve(null), 6000))
        const res = await Promise.race([call, timeout])
        const d = res && res.data
        if (d && d.id) {
          this.cloudRoleId = d.id
          data.roleId = d.id
          if (d.roleKey) data.roleKey = d.roleKey
          return d.roleKey || ''
        }
      } catch (e) {
        console.log('角色上云失败（本地仍可用）:', e && e.message)
      }
      return ''
    },

    /**
     * 创建前试聊：用当前表单让 TA 回一句。
     * 走的是后端 /persona/preview，与正式聊天共用同一套人设 prompt，
     * 所以这里像，正式聊天就像；这里不像，说明设定还太薄，可以继续补。
     */
    async runPreview() {
      if (this.previewLoading) return
      if (!this.canSave) {
        uni.showToast({ title: '先给 TA 起个名字、选个语气', icon: 'none' })
        return
      }
      this.previewLoading = true
      this.previewError = ''
      try {
        const data = this.buildCharacterData()
        const payload = this.buildCloudPayload(data)
        payload.testMessage = this.testMessage || ''
        const res = await personaApi.previewRole(payload)
        const d = res && res.data
        if (d && d.reply) {
          this.previewReply = d.reply
        } else {
          this.previewError = (res && res.message) || '试聊失败，确认后端服务已启动'
        }
      } catch (e) {
        this.previewError = '试聊失败：' + ((e && e.message) || '网络异常')
      } finally {
        this.previewLoading = false
      }
    },

    async saveCharacter() {
      if (!this.canSave) {
        uni.showToast({ title: '请填写昵称和语气风格', icon: 'none' })
        return
      }
      if (this.saving) return
      this.saving = true
      try {
        const data = this.buildCharacterData()
        // 注册到sprite运行时表
        registerCustomSprite(data.id, data.sprite)
        // ↓↓↓ v3.1：先上云拿到 roleKey，再写本地 ↓↓↓
        // 顺序很重要：roleKey 要跟着角色一起进 store，否则聊天时后端查不到角色
        const roleKey = await this.syncRoleToCloud(data)
        // 同步到 ai-characters 运行时注册表（带上 roleKey，使对话/地图/聊天立即可用）
        syncCustomCharacter(data)
        // 保存到store（持久化）
        this.$store.commit('addCustomCharacter', data)
        this.saving = false
        uni.showToast({
          title: this.isEditMode ? '修改成功' : (roleKey ? '创建成功' : '已保存到本地'),
          icon: roleKey || !this.isEditMode ? 'success' : 'none'
        })
        setTimeout(() => {
          uni.navigateBack()
        }, 800)
      } catch (e) {
        this.saving = false
        console.error('保存自定义角色失败', e)
        uni.showToast({ title: '保存失败：' + (e.message || '未知错误'), icon: 'none' })
      }
    },
    confirmDelete() {
      uni.showModal({
        title: '删除角色',
        content: `确定要删除"${this.form.name}"吗？此操作不可恢复。`,
        confirmColor: '#FF6B6B',
        success: (res) => {
          if (res.confirm) {
            // 同步移除运行时注册表
            removeCustomCharacterSync(this.editId)
            this.$store.commit('removeCustomCharacter', this.editId)
            uni.showToast({ title: '已删除', icon: 'success' })
            setTimeout(() => {
              uni.navigateBack()
            }, 600)
          }
        }
      })
    },
    lightenHex(hex, amount) {
      try {
        const num = parseInt(hex.replace('#', ''), 16)
        const r = Math.min(255, (num >> 16) + Math.floor(255 * amount))
        const g = Math.min(255, ((num >> 8) & 0x00FF) + Math.floor(255 * amount))
        const b = Math.min(255, (num & 0x000000FF) + Math.floor(255 * amount))
        return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
      } catch (e) {
        return hex
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.workshop-page {
  box-sizing: border-box;
  min-height: 100vh;
  background-color: var(--v7-card);
  background-image:
    radial-gradient(660rpx 460rpx at 4% -6%, rgba(156, 191, 170, 0.22) 0%, transparent 58%),
    radial-gradient(620rpx 460rpx at 100% 0%, rgba(192, 138, 86, 0.10) 0%, transparent 55%);
  display: flex;
  flex-direction: column;
}

/* 页头 */
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 28rpx 30rpx 16rpx;
}
.head-left { display: flex; align-items: flex-start; flex: 1; min-width: 0; }
.back-btn {
  width: 64rpx;
  height: 64rpx;
  margin-right: 18rpx;
  border-radius: 50%;
  background: rgba(255, 253, 250, 0.78);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.back-icon { font-size: 44rpx; color: var(--v7-green); line-height: 1; margin-top: -6rpx; }
.head-text { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.eyebrow {
  align-self: flex-start;
  padding: 5rpx 16rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
  color: #7F978C;
  background: var(--v7-line);
}
.page-title {
  margin-top: 14rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: #22302A;
}
.page-sub { margin-top: 6rpx; font-size: 20rpx; color: #AEB6AE; }
.head-actions { display: flex; align-items: center; }
.delete-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #F7F1EB;
  display: flex;
  align-items: center;
  justify-content: center;
}
.delete-icon { font-size: 30rpx; line-height: 1; }

.workshop-scroll { flex: 1; min-height: 0; }
.workshop-body { padding: 0 30rpx; }

/* 实时预览卡 */
.preview-section {
  margin-top: 12rpx;
  padding: 22rpx 22rpx 20rpx;
  border-radius: 32rpx;
  box-shadow: 0 10rpx 24rpx -22rpx rgba(34, 48, 42, 0.6), inset 0 0 0 1rpx var(--v7-line);
}
.preview-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.preview-tag {
  padding: 5rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.82);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.preview-tag-text { font-size: 17rpx; font-weight: 800; letter-spacing: 1rpx; color: #6E9B81; }
.preview-mode-tabs {
  display: flex;
  padding: 4rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.82);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.mode-tab {
  padding: 8rpx 22rpx;
  border-radius: 999rpx;
  transition: all 0.25s ease;
}
.mode-tab text { font-size: 20rpx; color: #6A776E; }
.mode-tab.active { background: var(--v7-green); }
.mode-tab.active text { color: #F8F3E7; font-weight: 700; }

.preview-stage {
  display: flex;
  align-items: center;
  padding: 8rpx 4rpx 0;
}
.preview-canvas {
  width: 240rpx;
  height: 240rpx;
  border-radius: 26rpx;
  background: rgba(255, 253, 250, 0.66);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.custom-avatar-preview { width: 100%; height: 100%; overflow: hidden; border-radius: 26rpx; }
.custom-avatar-img { width: 100%; height: 100%; }
.custom-avatar-img :deep(img) { width: 100%; height: 100%; object-fit: cover; }
.preview-sprite-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10rpx;
  box-sizing: border-box;
}
.sprite-head-render, .sprite-fullbody-render {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
.sprite-head-render :deep(svg), .sprite-fullbody-render :deep(svg) {
  width: 100%; height: 100%;
}
.preview-bounce { animation: bounceIn 0.5s ease; }
@keyframes bounceIn {
  0% { transform: scale(0.9); opacity: 0.6; }
  60% { transform: scale(1.04); }
  100% { transform: scale(1); opacity: 1; }
}

.preview-name-wrap {
  flex: 1;
  min-width: 0;
  padding: 0 24rpx;
  display: flex;
  flex-direction: column;
}
.preview-name {
  font-size: 34rpx;
  font-weight: 800;
  color: #22302A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-catchphrase {
  margin-top: 10rpx;
  font-size: 21rpx;
  line-height: 1.5;
  color: #6E9B81;
  font-style: italic;
}

.avatar-upload-row {
  display: flex;
  align-items: center;
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid var(--v7-line);
}
.upload-btn {
  display: flex;
  align-items: center;
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.86);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.upload-btn:active { transform: scale(0.96); }
.upload-icon { font-size: 22rpx; }
.upload-text { margin-left: 8rpx; font-size: 20rpx; color: var(--v7-green); font-weight: 700; }
.reset-sprite-btn { margin-left: 14rpx; padding: 10rpx 20rpx; }
.reset-text { font-size: 20rpx; color: #8A5D33; }

/* 主 Tab */
.main-tabs {
  display: flex;
  margin-top: 22rpx;
  padding: 6rpx;
  border-radius: 999rpx;
  background: rgba(255, 253, 250, 0.8);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.main-tab {
  flex: 1;
  height: 74rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
}
.main-tab text { font-size: 25rpx; color: #6A776E; }
.main-tab.active { background: var(--v7-green); }
.main-tab.active text { color: #F8F3E7; font-weight: 800; }

/* 面板 */
.panel-card {
  margin-top: 20rpx;
  padding: 26rpx 24rpx 30rpx;
  border-radius: 32rpx;
  background: var(--v7-card);
  box-shadow: 0 10rpx 24rpx -22rpx rgba(34, 48, 42, 0.6), inset 0 0 0 1rpx var(--v7-line);
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 18rpx;
  border-bottom: 1rpx solid var(--v7-line);
}
.sec-title { font-size: 27rpx; font-weight: 800; color: #22302A; }
.sec-more { font-size: 19rpx; color: #AEB6AE; }

/* DIY */
.diy-group {
  padding: 22rpx 0;
  border-bottom: 1rpx solid var(--v7-line);

  &:last-child { border-bottom: none; padding-bottom: 4rpx; }
}
.group-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 23rpx;
  font-weight: 800;
  letter-spacing: 1rpx;
  color: var(--v7-green);
}
.option-row { display: flex; flex-wrap: nowrap; overflow-x: auto; }
.option-row-wrap { flex-wrap: wrap; overflow: visible; }
.option-chip {
  padding: 12rpx 26rpx;
  margin: 0 12rpx 10rpx 0;
  border-radius: 999rpx;
  background: #F7F3EA;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.option-chip text { font-size: 22rpx; color: #6A776E; }
.option-chip.active { background: var(--v7-green); box-shadow: none; }
.option-chip.active text { color: #F8F3E7; font-weight: 700; }

.color-row { display: flex; flex-wrap: wrap; }
.color-dot {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  margin: 0 18rpx 10rpx 0;
  box-shadow: inset 0 0 0 1rpx rgba(34, 48, 42, 0.10);
  transition: all 0.2s ease;
}
.color-dot.active {
  box-shadow: 0 0 0 4rpx var(--v7-card), 0 0 0 7rpx var(--v7-green);
}

/* 人设表单 */
.form-group {
  position: relative;
  margin-top: 26rpx;
}
.form-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 23rpx;
  font-weight: 800;
  letter-spacing: 1rpx;
  color: var(--v7-green);
}
.required { color: #C08A56; }
.form-hint {
  display: block;
  margin: -4rpx 0 12rpx;
  font-size: 19rpx;
  line-height: 1.5;
  color: #AEB6AE;
}
.form-input {
  width: 100%;
  height: 88rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  background: #F7F3EA;
  font-size: 25rpx;
  color: #22302A;
}
.form-textarea {
  width: 100%;
  height: 150rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  background: #F7F3EA;
  font-size: 25rpx;
  line-height: 1.6;
  color: #22302A;
}
.form-textarea-lg { height: 200rpx; }
.form-counter {
  position: absolute;
  right: 20rpx;
  bottom: 12rpx;
  font-size: 18rpx;
  color: #BFC7BF;
}

.persona-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
}
.persona-card {
  padding: 20rpx 12rpx;
  border-radius: 22rpx;
  background: #F7F3EA;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.2s ease;
}
.persona-card.active {
  background: rgba(156, 191, 170, 0.16);
  box-shadow: inset 0 0 0 2rpx var(--v7-green);
}
.persona-emoji { font-size: 34rpx; line-height: 1; }
.persona-name {
  margin-top: 10rpx;
  font-size: 22rpx;
  font-weight: 800;
  color: #22302A;
}
.persona-desc {
  margin-top: 6rpx;
  font-size: 17rpx;
  line-height: 1.4;
  color: #AEB6AE;
  text-align: center;
}

.trait-pool { display: flex; flex-wrap: wrap; }
.trait-chip {
  padding: 10rpx 24rpx;
  margin: 0 12rpx 12rpx 0;
  border-radius: 999rpx;
  background: #F7F3EA;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.trait-chip text { font-size: 22rpx; color: #6A776E; }
.trait-chip.active { background: var(--v7-green); }
.trait-chip.active text { color: #F8F3E7; font-weight: 700; }

.advanced-title {
  margin: 34rpx -24rpx 0;
  padding: 22rpx 24rpx;
  background: linear-gradient(135deg, #F3EFE5, var(--v7-card));
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.adv-title-text {
  display: block;
  font-size: 25rpx;
  font-weight: 800;
  color: var(--v7-green);
}
.adv-sub { display: block; margin-top: 6rpx; font-size: 19rpx; color: #AEB6AE; }

.emoji-row { display: flex; flex-wrap: wrap; }
.tone-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14rpx 24rpx;
  margin: 0 12rpx 12rpx 0;
  border-radius: 20rpx;
  background: #F7F3EA;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.tone-label { font-size: 22rpx; font-weight: 700; color: #22302A; }
.tone-desc { margin-top: 4rpx; font-size: 17rpx; color: #AEB6AE; }
.tone-chip.active { background: var(--v7-green); }
.tone-chip.active .tone-label { color: #F8F3E7; }
.tone-chip.active .tone-desc { color: rgba(248, 243, 231, 0.72); }

.emoji-chip {
  padding: 12rpx 22rpx;
  margin: 0 12rpx 12rpx 0;
  border-radius: 999rpx;
  background: #F7F3EA;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.emoji-chip text { font-size: 22rpx; color: #6A776E; }
.emoji-chip.active { background: rgba(156, 191, 170, 0.16); box-shadow: inset 0 0 0 2rpx var(--v7-green); }
.emoji-chip.active text { color: var(--v7-green); font-weight: 700; }

/* 试聊 */
.preview-chat {
  margin-top: 30rpx;
  padding: 24rpx;
  border-radius: 26rpx;
  background: linear-gradient(135deg, #F3EFE5, var(--v7-card));
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.pc-head { display: flex; flex-direction: column; }
.pc-title { font-size: 25rpx; font-weight: 800; color: var(--v7-green); }
.pc-sub { margin-top: 6rpx; font-size: 18rpx; line-height: 1.5; color: #AEB6AE; }
.pc-row { display: flex; align-items: center; margin-top: 16rpx; }
.pc-input {
  flex: 1;
  height: 76rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: var(--v7-card);
  font-size: 22rpx;
  color: #22302A;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.pc-btn {
  margin-left: 12rpx;
  min-width: 118rpx;
  height: 76rpx;
  border-radius: 999rpx;
  background: var(--v7-green);
  display: flex;
  align-items: center;
  justify-content: center;
}
.pc-btn text { font-size: 22rpx; font-weight: 700; color: #F8F3E7; }
.pc-btn-busy { opacity: 0.6; }
.pc-bubble {
  margin-top: 18rpx;
  padding: 18rpx 22rpx;
  border-radius: 20rpx;
  border-top-left-radius: 6rpx;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.pc-name { display: block; margin-bottom: 6rpx; font-size: 19rpx; font-weight: 800; color: #6E9B81; }
.pc-text { font-size: 24rpx; line-height: 1.65; color: #26332C; }
.pc-err {
  margin-top: 14rpx;
  padding: 14rpx 18rpx;
  border-radius: 16rpx;
  background: #F7F1EB;
}
.pc-err text { font-size: 20rpx; color: #B8874E; }
.pc-tip {
  display: block;
  margin-top: 14rpx;
  font-size: 17rpx;
  line-height: 1.5;
  color: #BFC7BF;
}

.bottom-safe-area { height: 180rpx; }

/* 底部保存栏 */
.save-bar {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  padding: 16rpx 30rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(255, 253, 250, 0.97);
  border-top: 1rpx solid var(--v7-line);
}
.save-btn {
  height: 92rpx;
  border-radius: 999rpx;
  background: linear-gradient(140deg, #4E7A64, #24493A);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14rpx 28rpx -18rpx rgba(36, 73, 58, 0.75);
}
.save-btn text { font-size: 28rpx; font-weight: 700; color: #FFFDFA; letter-spacing: 2rpx; }
.save-btn.disabled { opacity: 0.42; box-shadow: none; }
.save-btn:active { transform: scale(0.99); }
</style>

<style scoped>
/* ===== s11 伙伴工坊首屏 ===== */
.xt-page.xt-s11 .page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: -0.4px;
  color: #22302A;
}
.xt-page.xt-s11 .page-sub {
  margin-top: 3px;
  font-size: 8.5px;
  color: #A2AAA3;
}
.xt-page.xt-s11 .role-hero uni-image {
  width: 72px;
  height: 96px;
  border-radius: 18px;
  overflow: hidden;
  flex-shrink: 0;
  border: 3px solid var(--v7-card);
  box-shadow: 0 10px 22px -12px rgba(62, 93, 74, 0.5);
}
.xt-page.xt-s11 .role-hero :deep(uni-image > div),
.xt-page.xt-s11 .role-hero :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s11 .role-hero :deep(uni-image img) {
  object-fit: cover;
}
.xt-page.xt-s11 .role-emoji {
  width: 72px;
  height: 96px;
  border-radius: 18px;
  background: #EDF3F0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  flex-shrink: 0;
}
.xt-page.xt-s11 .role-hero .h3 {
  font-size: 16px;
  font-weight: 900;
  letter-spacing: -0.2px;
  color: #22302A;
  line-height: 1.2;
}
.xt-page.xt-s11 .role uni-image {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
}
.xt-page.xt-s11 .role.on uni-image { box-shadow: 0 0 0 2px var(--v7-green); }
.xt-page.xt-s11 .role > text {
  font-size: 6.5px;
  color: #A2AAA3;
}
.xt-page.xt-s11 .role.on > text {
  color: #3C6B55;
  font-weight: 800;
}
.xt-page.xt-s11 .role-ph {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #EDF3F0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.xt-page.xt-s11 .role:active { transform: scale(0.96); }

/* ===== 创作 / 编辑面板 ===== */
.ws-editor {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 150;
  background: var(--v7-card);
  display: flex;
  flex-direction: column;
}
.ws-top {
  display: flex;
  align-items: flex-start;
  padding: 14px 18px 10px;
  flex-shrink: 0;
}
.ws-back {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 253, 250, 0.78);
  box-shadow: inset 0 0 0 1px var(--v7-line);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ws-title {
  flex: 1;
  min-width: 0;
  margin-left: 10px;
  display: flex;
  flex-direction: column;
}
.ws-t { font-size: 16px; font-weight: 900; color: #22302A; line-height: 1.2; }
.ws-s { margin-top: 3px; font-size: 8.5px; color: #AEB6AE; }
.ws-del {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #F7F1EB;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 8px;
}
.ws-scroll { flex: 1; height: 0; min-height: 0; }
.ws-editor .workshop-body { padding: 0 18px; }
.ws-editor .preview-section { margin-top: 2px; }
.ws-save {
  flex-shrink: 0;
  padding: 8px 18px 14px;
  background: rgba(255, 253, 250, 0.97);
  border-top: 1px solid var(--v7-line);
}
</style>
