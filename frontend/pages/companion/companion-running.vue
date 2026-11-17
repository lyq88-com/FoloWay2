<template>
  <view class="xt-page xt-s23" :style="pageStyle">
    <view class="body">
      <view class="run-wrap">
        <view class="run-top">
          <view class="run-status">
            <view class="run-dot"></view>
            <text>陪伴中 · {{ timerText }}</text>
          </view>
          <text>{{ bgSound }}</text>
        </view>

        <view class="run-stage">
          <view class="run-av">
            <image v-if="rolePhoto" class="run-photo" :src="rolePhoto" mode="aspectFill" />
            <text v-else class="run-emoji">{{ roleAvatar }}</text>
          </view>
        </view>

        <view class="run-cap">她 在 旁 边</view>
        <view class="run-name">{{ roleName }}</view>
        <view class="run-line">“{{ currentLine || '正在陪伴中…' }}”</view>

        <view class="chips run-chips">
          <text class="chip on">{{ sceneIcon }} {{ sceneName }}</text>
          <text class="chip">{{ bgSound }}</text>
          <text v-if="musicOn" class="chip on">安眠曲 · 播放中</text>
        </view>

        <view class="run-foot">
          <view class="run-acts">
            <text class="run-act" @click="toggleChat">说说话</text>
            <text class="run-act" :class="{ on: musicOn }" @click="toggleLullaby">
              {{ musicOn ? '安眠曲 · 播放中' : (sceneType === 'sleep' ? '哄睡安眠曲' : '轻音乐') }}
            </text>
          </view>
          <view class="fbtn main run-end" @click="endCompanion">结束陪伴</view>
          <text class="run-tip">结束后会自动生成一条陪伴记录</text>
        </view>
      </view>

      <!-- 聊天抽屉 -->
      <view class="chat-mask" v-if="chatVisible" @click="toggleChat"></view>
      <view class="chat-drawer" :class="{ 'chat-drawer--open': chatVisible }">
        <view class="chat-head dr-head">
          <view class="chat-meta">
            <view class="chat-name">和{{ roleName }}聊天</view>
            <view class="chat-st"><i></i>陪伴中 · {{ timerText }}</view>
          </view>
          <text class="dr-close" @click="toggleChat">✕</text>
        </view>
        <scroll-view class="chat-list" scroll-y :scroll-top="chatScrollTop" :scroll-into-view="scrollInto">
          <view
            v-for="(msg, idx) in messages"
            :key="idx"
            class="msg"
            :class="msg.role === 'user' ? 'me' : 'ai'"
          >
            <view v-if="msg.role === 'ai'" class="mav dr-mav">
              <image v-if="roleAvatarImg" class="dr-mav-img" :src="roleAvatarImg" mode="aspectFill" />
              <text v-else class="dr-mav-t">{{ roleAvatar }}</text>
            </view>
            <view class="bubble" :class="msg.role === 'user' ? 'me' : 'ai'">
              <text class="bubble-t">{{ msg.content }}</text>
            </view>
          </view>
          <view v-if="aiTyping" class="msg ai">
            <view class="mav dr-mav">
              <image v-if="roleAvatarImg" class="dr-mav-img" :src="roleAvatarImg" mode="aspectFill" />
              <text v-else class="dr-mav-t">{{ roleAvatar }}</text>
            </view>
            <view class="bubble ai typing-bubble">
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
            </view>
          </view>
          <view id="chat-bottom" class="chat-bottom-anchor"></view>
        </scroll-view>
        <!-- 输入区 -->
        <view class="inputbar dr-inputbar">
          <view class="in-field">
            <input
              class="dr-input"
              v-model="inputText"
              placeholder="和TA说点什么…"
              placeholder-class="dr-ph"
              confirm-type="send"
              @confirm="sendMessage"
            />
          </view>
          <view class="in-send" :class="{ off: !inputText.trim() }" @click="sendMessage">
            <xt-icon name="i-send" />
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 陪伴模式 - 进行中页面
 * - 进入即开始计时；对话走 companionChat（场景化流式回复）
 * - 结束时调用 endCompanion 归档陪伴记录
 */
import companionApi from '@/api/companion'
import { playLullaby, stopMusic } from '@/common/ai-music'
import { findPartner, getActivePartner, getPartnerPhoto, getPartnerAvatar, DEFAULT_PARTNER_ID } from '@/common/ai-partner'

const SCENE_META = {
  sleep: { icon: '🌙', bg: 'linear-gradient(180deg, #171A2E, #0D0D0F)', line: '闭上眼睛，我守着你入睡。' },
  study: { icon: '📚', bg: 'linear-gradient(180deg, #12241E, #0D0D0F)', line: '我在旁边陪你看书。' },
  work: { icon: '💻', bg: 'linear-gradient(180deg, #1E1A24, #0D0D0F)', line: '工作辛苦啦，我安静陪着你。' },
  sport: { icon: '🏃', bg: 'linear-gradient(180deg, #241A14, #0D0D0F)', line: '加油！我为你数着。' },
  eat: { icon: '🍜', bg: 'linear-gradient(180deg, #241E14, #0D0D0F)', line: '慢慢吃，我陪着你。' },
  custom: { icon: '✨', bg: 'linear-gradient(180deg, #1E1A2E, #0D0D0F)', line: '我在你身边。' }
}

export default {
  data() {
    return {
      statusBarHeight: 20,
      // 参数
      recordId: 0,
      // ↓↓↓ 改造（2026-10-27）：roleId(整型 ai_roles id) → roleKey(20 个具名角色的字符串 id) ↓↓↓
      roleKey: DEFAULT_PARTNER_ID,
      // ↑↑↑ 改造结束 ↑↑↑
      roleName: '',
      roleAvatar: '🌿',
      rolePhoto: '',
      sceneType: 'custom',
      sceneName: '自定义',
      bgSound: '静音',
      // 计时
      seconds: 0,
      timer: null,
      // 氛围语
      currentLine: '',
      lineTimer: null,
      // 聊天
      chatVisible: false,
      messages: [],
      inputText: '',
      aiTyping: false,
      chatScrollTop: 0,
      scrollInto: '',
      sending: false,
      // 安眠曲
      musicOn: false
    }
  },
  computed: {
    // 对话小头像用脸部特写，比大立绘缩到 24px 更清晰
    roleAvatarImg() {
      return getPartnerAvatar(this.roleKey) || ''
    },
    sceneIcon() {
      return (SCENE_META[this.sceneType] || SCENE_META.custom).icon
    },
    pageStyle() {
      return { background: (SCENE_META[this.sceneType] || SCENE_META.custom).bg }
    },
    timerText() {
      const h = Math.floor(this.seconds / 3600)
      const m = Math.floor((this.seconds % 3600) / 60)
      const s = this.seconds % 60
      const pad = n => String(n).padStart(2, '0')
      return h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20

    this.recordId = Number(options.recordId || 0)
    // 注意：角色标识是字符串（如 'linxi'），不能 Number() 强转，否则会变成 NaN
    this.roleKey = options.roleKey || options.roleId || options.characterId || DEFAULT_PARTNER_ID
    // 以角色 id 为准重新解析名称/头像/立绘：路由只传了 emoji，直接信任会与全局形象不同步
    const partner = findPartner(this.roleKey) || getActivePartner()
    this.roleKey = partner.id
    this.roleName = partner.name || decodeURIComponent(options.roleName || '伙伴')
    this.roleAvatar = partner.avatar || decodeURIComponent(options.roleAvatar || '🌿')
    this.rolePhoto = getPartnerPhoto(partner)
    this.sceneType = options.sceneType || 'custom'
    this.sceneName = decodeURIComponent(options.sceneName || '自定义')
    this.bgSound = decodeURIComponent(options.bgSound || '静音')

    this.currentLine = (SCENE_META[this.sceneType] || SCENE_META.custom).line
    this.startTimer()
    this.startAmbientLine()
  },
  onUnload() {
    this.stopTimers()
    stopMusic()
    // 兜底：页面销毁但未手动结束时，静默归档
    if (this.recordId) {
      companionApi.endCompanion(this.recordId).catch(() => {})
    }
  },
  methods: {
    /** 哄睡安眠曲开关（Web Audio 合成摇篮曲，循环播放） */
    toggleLullaby() {
      if (this.musicOn) {
        stopMusic()
        this.musicOn = false
        uni.showToast({ title: '安眠曲已暂停', icon: 'none' })
        return
      }
      const ok = playLullaby()
      if (ok) {
        this.musicOn = true
        this.currentLine = this.sceneType === 'sleep' ? '安眠曲响起，安心睡吧，我守着你。' : '音乐响起，放松一下吧。'
      } else {
        uni.showToast({ title: '当前环境不支持播放', icon: 'none' })
      }
    },
    startTimer() {
      this.timer = setInterval(() => { this.seconds++ }, 1000)
    },
    startAmbientLine() {
      // 每 90 秒随机换一句氛围语
      const lines = [
        '我一直都在。', '累了就歇一会儿。', '有我在，别担心。',
        '和你在一起的时光很安静。', '需要我的时候随时叫我。', '慢慢来，不着急。'
      ]
      this.lineTimer = setInterval(() => {
        this.currentLine = lines[Math.floor(Math.random() * lines.length)]
      }, 90000)
    },
    stopTimers() {
      if (this.timer) clearInterval(this.timer)
      if (this.lineTimer) clearInterval(this.lineTimer)
      this.timer = null
      this.lineTimer = null
    },
    toggleChat() {
      this.chatVisible = !this.chatVisible
    },
    scrollToBottom() {
      this.$nextTick(() => {
        this.scrollInto = ''
        this.$nextTick(() => { this.scrollInto = 'chat-bottom' })
      })
    },
    async sendMessage() {
      const content = this.inputText.trim()
      if (!content || this.sending) return
      this.sending = true
      this.inputText = ''
      this.messages.push({ role: 'user', content })
      this.aiTyping = true
      this.scrollToBottom()

      try {
        // 流式接收：逐段追加为一条 AI 消息
        let aiIdx = this.messages.length
        this.messages.push({ role: 'ai', content: '' })
        await companionApi.companionChat(content, chunk => {
          this.messages[aiIdx].content += chunk
          this.scrollToBottom()
        }, {
          sceneType: this.sceneType,
          sceneName: this.sceneName,
          // ↓↓↓ 改造（2026-10-27）：把具名角色标识传下去当人设（后端未命中会回退默认人设，不会出错） ↓↓↓
          roleType: this.roleKey
          // ↑↑↑ 改造结束 ↑↑↑
        })
      } catch (e) {
        this.messages.push({ role: 'ai', content: '（好像走神了，再说一次好不好…）' })
      } finally {
        this.aiTyping = false
        this.sending = false
        this.scrollToBottom()
      }
    },
    endCompanion() {
      const duration = this.seconds
      uni.showModal({
        title: '结束陪伴',
        content: `本次已陪伴 ${this.timerText}，确定要结束吗？`,
        confirmColor: '#6B8E7B',
        success: async res => {
          if (!res.confirm) return
          this.stopTimers()
          if (this.recordId) {
            try { await companionApi.endCompanion(this.recordId) } catch (e) { /* 忽略归档失败 */ }
          }
          uni.showToast({ title: `陪伴 ${this.timerText} 已记录`, icon: 'none' })
          setTimeout(() => {
            uni.navigateBack({
              fail: () => uni.reLaunch({ url: '/pages/discover/discover' })
            })
          }, 600)
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 第 23 屏 · 陪伴进行中（沉浸深绿，只留"她在"与计时） */
.xt-page.xt-s23 {
  background: #24322C;
}

.xt-page.xt-s23 .body {
  padding: env(safe-area-inset-top) 0 0;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.xt-page.xt-s23 .run-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 22px 26px;
  background: linear-gradient(170deg, rgba(61, 84, 73, 0.94) 0%, rgba(36, 50, 44, 0.97) 48%, rgba(33, 46, 40, 0.98) 100%);
  color: #fff;
}

.xt-page.xt-s23 .run-top {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 8px;
  color: rgba(255, 253, 250, 0.62);
}

.xt-page.xt-s23 .run-status {
  display: flex;
  align-items: center;
}

.xt-page.xt-s23 .run-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #9CBFAA;
  margin-right: 6px;
  animation: runBreath 2.4s ease-in-out infinite;
}

.xt-page.xt-s23 .run-stage {
  margin-top: 34px;
  width: 196px;
  height: 196px;
  border-radius: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 253, 250, 0.05);
  box-shadow: 0 0 0 1px rgba(255, 253, 250, 0.14), 0 0 0 20px rgba(255, 253, 250, 0.03);
}

.xt-page.xt-s23 .run-av {
  width: 144px;
  height: 192px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(255, 253, 250, 0.08);
  box-shadow: 0 20px 40px -18px rgba(0, 0, 0, 0.6);
  animation: runFloat 4.5s ease-in-out infinite;
}

.xt-page.xt-s23 .run-emoji {
  font-size: 72px;
  line-height: 1;
}

/* 陪伴中主形象：与首页/聊天共用同一张伙伴立绘 */
.xt-page.xt-s23 .run-photo {
  width: 100%;
  height: 100%;
  border-radius: 24px;
  display: block;
}
.xt-page.xt-s23 .run-photo :deep(div),
.xt-page.xt-s23 .run-photo :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s23 .run-photo :deep(img) {
  object-fit: cover;
}

.xt-page.xt-s23 .run-cap {
  margin-top: 26px;
  font-size: 9px;
  letter-spacing: 1.4px;
  color: rgba(255, 253, 250, 0.55);
}

.xt-page.xt-s23 .run-name {
  margin-top: 6px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2px;
  color: rgba(255, 253, 250, 0.92);
}

.xt-page.xt-s23 .run-line {
  margin-top: 8px;
  width: 82%;
  text-align: center;
  font-size: 11px;
  line-height: 1.85;
  color: rgba(255, 253, 250, 0.9);
}

.xt-page.xt-s23 .run-chips {
  margin-top: 20px;
  justify-content: center;
}

.xt-page.xt-s23 .run-chips .chip {
  background: rgba(255, 253, 250, 0.1);
  color: rgba(255, 253, 250, 0.72);
  box-shadow: inset 0 0 0 1px rgba(255, 253, 250, 0.12);
}

.xt-page.xt-s23 .run-chips .chip.on {
  background: rgba(255, 253, 250, 0.92);
  color: #24322C;
  font-weight: 800;
}

.xt-page.xt-s23 .run-foot {
  margin-top: auto;
  width: 100%;
}

.xt-page.xt-s23 .run-acts {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.xt-page.xt-s23 .run-act {
  flex: 1;
  text-align: center;
  font-size: 9px;
  font-weight: 800;
  padding: 10px 0;
  border-radius: 999px;
  background: rgba(255, 253, 250, 0.12);
  color: rgba(255, 253, 250, 0.86);
}

.xt-page.xt-s23 .run-act.on {
  background: rgba(156, 191, 170, 0.28);
  box-shadow: inset 0 0 0 1px rgba(156, 191, 170, 0.6);
}

.xt-page.xt-s23 .run-end {
  background: rgba(255, 253, 250, 0.92);
  color: #24322C;
  box-shadow: none;
}

.xt-page.xt-s23 .run-tip {
  display: block;
  margin-top: 9px;
  text-align: center;
  font-size: 7.5px;
  color: rgba(255, 253, 250, 0.4);
}

/* 聊天抽屉 */
.xt-page.xt-s23 .chat-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(12, 22, 17, 0.55);
  z-index: 20;
}

.xt-page.xt-s23 .chat-drawer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 74%;
  display: flex;
  flex-direction: column;
  background: var(--v7-card);
  border-radius: 24px 24px 0 0;
  z-index: 21;
  transform: translateY(105%);
  transition: transform 0.3s ease;
  box-shadow: 0 -20px 60px -30px rgba(0, 0, 0, 0.5);
}

.xt-page.xt-s23 .chat-drawer--open {
  transform: translateY(0);
}

.xt-page.xt-s23 .dr-head {
  padding: 14px 18px 12px;
}

.xt-page.xt-s23 .dr-close {
  font-size: 13px;
  color: #AEB6AE;
  padding: 4px 6px;
}

.xt-page.xt-s23 .chat-list {
  flex: 1;
  min-height: 0;
  padding: 12px 16px 6px;
  box-sizing: border-box;
}

.xt-page.xt-s23 .dr-mav {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #F1EDE3;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.xt-page.xt-s23 .dr-mav-t {
  font-size: 12px;
  line-height: 1;
}

.xt-page.xt-s23 .dr-mav-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}

.xt-page.xt-s23 .bubble-t {
  font-size: 11px;
  line-height: 1.62;
  white-space: pre-wrap;
  word-break: break-all;
}

.xt-page.xt-s23 .chat-bottom-anchor {
  height: 4px;
}

.xt-page.xt-s23 .typing-bubble {
  display: flex;
  align-items: center;
}

.xt-page.xt-s23 .typing-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #9CBFAA;
  margin: 0 3px;
  animation: runTyping 1.2s infinite;
}

.xt-page.xt-s23 .typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.xt-page.xt-s23 .typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

.xt-page.xt-s23 .dr-inputbar {
  flex-shrink: 0;
  padding: 8px 16px calc(env(safe-area-inset-bottom) + 8px);
  border-top: 1px solid var(--v7-line);
  background: var(--v7-card);
}

.xt-page.xt-s23 .dr-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 9px;
  color: #22302A;
  background: transparent;
}

.xt-page.xt-s23 .dr-ph {
  color: #BFC7BF;
}

.xt-page.xt-s23 .in-send.off {
  opacity: 0.45;
}

@keyframes runBreath {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

@keyframes runFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

@keyframes runTyping {
  0%, 100% { opacity: 0.25; }
  50% { opacity: 1; }
}
</style>
