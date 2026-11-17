<template>
  <view class="xt-page xt-s25">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view>
          <view class="page-title">她的实时形象</view>
          <view class="page-sub">会呼吸、会眨眼，也会看向你</view>
        </view>
        <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
      </view>

      <!-- 形象主屏 -->
      <view class="stage" :class="stageClass">
        <image v-if="photo" class="stage-photo" :src="photo" mode="aspectFill" />
        <view v-else class="stage-fallback"><text>{{ character.avatar || '🌿' }}</text></view>
        <text class="stage-badge" style="left:12px;top:12px">{{ speaking ? '说话中' : '呼吸中' }} · {{ actionName || '自然状态' }}</text>
        <text class="stage-badge" style="right:12px;bottom:12px;left:auto;top:auto">{{ bgName }} · {{ voiceEnabled ? '语音开' : '静音' }}</text>
      </view>

      <!-- 能力 -->
      <view class="chips" style="margin-top:11px">
        <view class="chip on">立绘</view>
        <view class="chip">眨眼</view>
        <view class="chip">呼吸</view>
        <view class="chip" :class="{ on: voiceEnabled }" @click="toggleVoice">语音播报</view>
      </view>

      <!-- 装扮动作 -->
      <view class="mod-grid">
        <view class="mod" @click="doOutfit">
          <view class="mod-ic"><xt-icon name="i-tool" /></view>
          <view class="mod-t">换装</view>
        </view>
        <view class="mod" @click="doAction">
          <view class="mod-ic"><xt-icon name="i-spark" /></view>
          <view class="mod-t">动作</view>
        </view>
        <view class="mod" @click="doBg">
          <view class="mod-ic"><xt-icon name="i-world" /></view>
          <view class="mod-t">背景</view>
        </view>
        <view class="mod" @click="toggleVoice">
          <view class="mod-ic"><xt-icon name="i-call" /></view>
          <view class="mod-t">声音</view>
        </view>
      </view>

      <!-- 她的回复 -->
      <view class="ai-rec" style="margin-top:12px;align-items:flex-start">
        <view class="sp"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <text class="k">{{ character.name || '伙伴' }} 说</text>
          <text class="p">{{ reply || (speaking ? '正在想…' : greeting) }}</text>
        </view>
      </view>

      <!-- 输入 -->
      <view class="send-bar">
        <input
          class="send-input"
          v-model="inputText"
          placeholder="说点什么…"
          placeholder-style="color:#AEB6AE"
          confirm-type="send"
          @confirm="send"
        />
        <view class="send-btn" :class="{ disabled: !inputText.trim() || sending }" @click="send">
          <text class="send-btn-t">{{ sending ? '…' : '发送' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * AI 角色动态互动页
 *
 * 【2026-10-27 新增】落地 chat-settings 里标着「规划中」的「实时视频通话 · AI角色动态视频互动」。
 *
 * 说明：真正的实时视频通话需要数字人视频流服务（云端渲染 + RTC），本项目不具备。
 * 这里用项目已有的能力做一个等价可交付版本：
 *   - 角色形象：设计稿 s25 的角色照片（原 character-sprite 立绘改为照片主视觉）
 *   - 对话能力：复用 /chat/send（companionApi.companionChat，流式）
 *   - 语音：AI 回复用 TTS 播报（common/tts.js，H5 生效）
 * 所以叫「动态互动」而不是「视频通话」——是形象 + 语音的互动，不是视频流。
 */
import companionApi from '@/api/companion'
import { getCharacterById } from '@/common/ai-characters'
import { getActivePartnerId, getPartnerPhoto } from '@/common/ai-partner'
import tts from '@/common/tts'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      characterId: 'linxi',
      character: {},
      inputText: '',
      reply: '',
      sending: false,
      speaking: false,
      greeting: '我在呢，想聊点什么？',
      bgKey: 'mist',
      voiceEnabled: true,
      actionName: '',
      actionClass: '',
      actionTimer: null
    }
  },
  computed: {
    // 设计稿 s25：当前角色照片（与全站同一套伙伴形象）
    photo() {
      return getPartnerPhoto(this.characterId || getActivePartnerId()) || ''
    },
    stageClass() {
      return [
        'bg-' + this.bgKey,
        { 'stage--live': this.speaking },
        this.actionClass
      ]
    },
    bgName() {
      const map = { mist: '雾光', dawn: '晨光', night: '夜航', forest: '森林' }
      return map[this.bgKey] || '雾光'
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20

    const cfg = (this.$store && this.$store.state.aiConfig) || {}
    this.characterId = (options && options.characterId) || cfg.avatarType || 'linxi'
    const c = getCharacterById(this.characterId)
    this.character = c || { name: '伙伴', catchphrase: '我在这里陪着你' }
    if (this.character && this.character.catchphrase) {
      this.greeting = this.character.catchphrase
    }
    const bg = uni.getStorageSync('avatar_live_bg')
    if (bg) this.bgKey = bg
    const voice = uni.getStorageSync('avatar_live_voice')
    if (voice !== '' && voice !== undefined && voice !== null) this.voiceEnabled = voice === '1'
  },
  onUnload() {
    // 离开页面就停止播报，避免念到别的页面去
    try { tts.stop() } catch (e) { /* 静默 */ }
    if (this.actionTimer) clearTimeout(this.actionTimer)
  },
  methods: {
    async send() {
      const text = (this.inputText || '').trim()
      // 空内容不发请求（与 chat.vue 的 BUG-003 修复保持一致）
      if (!text) {
        uni.showToast({ title: '请输入内容后再发送', icon: 'none', duration: 1500 })
        return
      }
      if (this.sending) return

      this.inputText = ''
      this.sending = true
      this.speaking = true
      this.reply = ''

      try {
        await companionApi.companionChat(
          text,
          chunk => { this.reply += chunk || '' },
          {
            roleType: this.characterId,
            sceneType: 'daily',
            sceneName: ''
          }
        )
        if (!this.reply) this.reply = '嗯嗯，我在听呢~'
        // 播报（受「声音」开关控制）
        if (this.voiceEnabled) {
          try { tts.speak(this.reply) } catch (e) { /* 静默 */ }
        }
      } catch (e) {
        this.reply = '（好像走神了，再说一次好不好…）'
      } finally {
        this.sending = false
        this.speaking = false
      }
    },
    doOutfit() {
      uni.navigateTo({
        url: '/pages/character-workshop/character-workshop',
        fail: () => uni.showToast({ title: '形象工坊打开失败', icon: 'none' })
      })
    },
    doAction() {
      uni.showActionSheet({
        itemList: ['呼吸放松', '眨眨眼', '挥挥手'],
        success: (res) => {
          const names = ['呼吸', '眨眼', '挥手']
          const classes = ['act-breathe', 'act-blink', 'act-wave']
          this.playAction(names[res.tapIndex], classes[res.tapIndex])
        }
      })
    },
    playAction(name, cls) {
      if (this.actionTimer) clearTimeout(this.actionTimer)
      this.actionName = name
      this.actionClass = cls
      this.actionTimer = setTimeout(() => {
        this.actionName = ''
        this.actionClass = ''
        this.actionTimer = null
      }, 1800)
    },
    doBg() {
      uni.showActionSheet({
        itemList: ['雾光', '晨光', '夜航', '森林'],
        success: (res) => {
          const keys = ['mist', 'dawn', 'night', 'forest']
          this.bgKey = keys[res.tapIndex] || 'mist'
          try { uni.setStorageSync('avatar_live_bg', this.bgKey) } catch (e) { /* 静默 */ }
          uni.showToast({ title: '背景已切换', icon: 'none' })
        }
      })
    },
    toggleVoice() {
      this.voiceEnabled = !this.voiceEnabled
      try { uni.setStorageSync('avatar_live_voice', this.voiceEnabled ? '1' : '0') } catch (e) { /* 静默 */ }
      if (!this.voiceEnabled) {
        try { tts.stop() } catch (e) { /* 静默 */ }
      }
      uni.showToast({
        title: this.voiceEnabled ? '语音播报已开启' : '语音播报已关闭',
        icon: 'none'
      })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/chat/chat' }) })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿 img 尺寸同步到 uni-image 包装层 */
.xt-page.xt-s25 .stage {
  position: relative;
  height: 300px;
  border-radius: 24px;
  overflow: hidden;
  background: linear-gradient(160deg, #F3F7F5, #F7F1EB);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* 说话中：主屏描边提亮 */
.xt-page.xt-s25 .stage--live {
  box-shadow: inset 0 0 0 2px rgba(192, 138, 86, 0.45);
}

.xt-page.xt-s25 .stage-photo {
  display: block;
  width: 100%;
  height: 100%;
}
.xt-page.xt-s25 .stage-photo :deep(div) {
  background-size: contain;
  background-position: center bottom;
  background-repeat: no-repeat;
}
.xt-page.xt-s25 .stage-photo :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center bottom;
}

.xt-page.xt-s25 .stage-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72px;
}

.xt-page.xt-s25 .stage-badge {
  position: absolute;
  font-size: 7px;
  color: #3C6B55;
  background: rgba(255, 253, 250, 0.82);
  padding: 4px 9px;
  border-radius: 999px;
}

/* 输入条：贴在滚动区底部 */
.xt-page.xt-s25 .send-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 0 calc(env(safe-area-inset-bottom) + 10px);
  background: var(--v7-card);
}

.xt-page.xt-s25 .send-input {
  flex: 1;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--v7-card);
  box-shadow: 0 0 0 1px var(--v7-line);
  font-size: 10px;
  color: #22302A;
}
.xt-page.xt-s25 .send-input :deep(input) {
  height: 100%;
  font-size: 10px;
  color: #22302A;
}

.xt-page.xt-s25 .send-btn {
  height: 36px;
  padding: 0 18px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6E9B81, var(--v7-green));
  box-shadow: 0 12px 22px -14px rgba(110, 143, 123, 0.9);
}
.xt-page.xt-s25 .send-btn.disabled {
  background: #EDE8DD;
  box-shadow: none;
}
.xt-page.xt-s25 .send-btn-t {
  font-size: 9px;
  font-weight: 900;
  color: #ffffff;
}
.xt-page.xt-s25 .send-btn.disabled .send-btn-t {
  color: #AEB6AE;
}

/* 背景主题（对应「背景」按钮） */
.xt-page.xt-s25 .stage.bg-dawn {
  background: linear-gradient(160deg, #FDF0E3, #F6E7DA);
}
.xt-page.xt-s25 .stage.bg-night {
  background: linear-gradient(160deg, #2B3942, #465C66);
}
.xt-page.xt-s25 .stage.bg-forest {
  background: linear-gradient(160deg, #E7F2EA, #D5E7DB);
}

/* 动作（对应「动作」按钮）：轻量 CSS 动效，不依赖视频流 */
.xt-page.xt-s25 .stage.act-breathe .stage-photo {
  animation: xt-breathe 1.8s ease-in-out;
}
.xt-page.xt-s25 .stage.act-blink .stage-photo {
  animation: xt-blink 1.2s ease-in-out;
}
.xt-page.xt-s25 .stage.act-wave .stage-photo {
  animation: xt-wave 1.6s ease-in-out;
}

@keyframes xt-breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.035); }
}
@keyframes xt-blink {
  0%, 100% { opacity: 1; }
  45% { opacity: 0.55; }
  55% { opacity: 1; }
}
@keyframes xt-wave {
  0%, 100% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(-3deg) scale(1.02); }
  75% { transform: rotate(3deg) scale(1.02); }
}
</style>
