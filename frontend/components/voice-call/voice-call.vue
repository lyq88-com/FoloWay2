<template>
  <view class="call-overlay" v-if="visible">
    <view class="call-bg"></view>
    <!-- 波纹动画 -->
    <view class="ripple-wrap">
      <view class="ripple r1"></view>
      <view class="ripple r2"></view>
      <view class="ripple r3"></view>
      <view class="call-avatar" :style="{ background: avatarBg }">
        <text class="call-avatar-emoji">{{ avatarEmoji }}</text>
      </view>
    </view>
    <text class="call-name">{{ name }}</text>
    <text class="call-status">{{ statusText }}</text>
    <text class="call-duration">{{ durationText }}</text>
    <!-- 字幕 -->
    <view class="call-subtitle" v-if="subtitle">
      <text>{{ subtitle }}</text>
    </view>

    <!-- 控制按钮 -->
    <view class="call-controls">
      <view class="ctl-btn" :class="{ off: !muted }" @click="toggleMute">
        <text class="ctl-icon">{{ muted ? '🔇' : '🎙️' }}</text>
        <text class="ctl-label">{{ muted ? '已静音' : '麦克风' }}</text>
      </view>
      <view class="ctl-btn hangup" @click="hangup">
        <text class="ctl-icon">📞</text>
        <text class="ctl-label">挂断</text>
      </view>
      <view class="ctl-btn" :class="{ off: !speaker }" @click="toggleSpeaker">
        <text class="ctl-icon">{{ speaker ? '🔊' : '🔈' }}</text>
        <text class="ctl-label">扬声器</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getVoiceLang, getCallLines, matchSystemVoice } from '@/common/voice-lang'
// ↓↓↓ 陪伴感增强 v3：语气起伏（停顿 / 情绪 / 逐句字幕） ↓↓↓
import { speakExpressive, detectEmotion } from '@/common/voice-prosody'
// ↑↑↑ 新增结束 ↑↑↑

/**
 * 实时语音通话（模拟）：
 * - 全屏通话界面 + 波纹动画
 * - AI轮播"说话"：TTS 播报对话短语，同步显示字幕
 * - 结束后向父组件抛出通话时长，父组件写入聊天记录
 * 多语言：台词与发音都跟随「聊天设置 → 语音多语言」的语种（原来写死 zh-CN）
 */
export default {
  props: {
    visible: { type: Boolean, default: false },
    name: { type: String, default: 'AI伙伴' },
    avatarEmoji: { type: String, default: '🌿' },
    avatarBg: { type: String, default: 'linear-gradient(135deg, #7BA08B, #A5D6A7)' },
    // ↓↓↓ 陪伴感增强 v3：角色音色 soft/bright/warm/cool/husky（不传就 warm） ↓↓↓
    tone: { type: String, default: 'warm' }
  },
  data() {
    return {
      seconds: 0,
      timer: null,
      muted: false,
      speaker: true,
      statusText: '通话中',
      subtitle: '',
      lineTimer: null
    }
  },
  computed: {
    durationText() {
      const m = Math.floor(this.seconds / 60)
      const s = this.seconds % 60
      const pad = n => String(n).padStart(2, '0')
      return `${pad(m)}:${pad(s)}`
    }
  },
  watch: {
    visible(v) {
      if (v) {
        this.start()
      } else {
        this.stop()
      }
    }
  },
  beforeUnmount() {
    this.stop()
  },
  methods: {
    start() {
      this.seconds = 0
      this.subtitle = ''
      this.statusText = '已接通'
      this.timer = setInterval(() => { this.seconds++ }, 1000)
      // ↓↓↓ 陪伴感增强 v3：不再是死板的"每 8 秒一句"，
      // 说完一句后有概率立刻接一句短的（自然接话），否则 5~9 秒后再开口 ↓↓↓
      this.speakNext()
      this.scheduleNextLine(0)
      // ↑↑↑ 新增结束 ↑↑↑
    },
    stop() {
      if (this.timer) clearInterval(this.timer)
      if (this.lineTimer) { clearTimeout(this.lineTimer); clearInterval(this.lineTimer) }
      this.timer = null
      this.lineTimer = null
      // 停止TTS
      // #ifdef H5
      try {
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          window.speechSynthesis.cancel()
        }
      } catch (e) { /* 静默 */ }
      // #endif
    },
    /** 当前语种（读聊天设置，读不到就中文） */
    currentLangCode() {
      try {
        const saved = uni.getStorageSync('chat_settings')
        return (saved && saved.voiceLang) || 'zh-CN'
      } catch (e) {
        return 'zh-CN'
      }
    },
    /** 当前语速/音调（同样读聊天设置） */
    currentVoiceParams() {
      try {
        const saved = uni.getStorageSync('chat_settings') || {}
        return {
          rate: typeof saved.rate === 'number' ? saved.rate : 1.0,
          pitch: typeof saved.pitch === 'number' ? saved.pitch : 1.1
        }
      } catch (e) {
        return { rate: 1.0, pitch: 1.1 }
      }
    },
    /** 排下一句话：刚接完话就 1.2~2.5s 后接着说，否则隔 5~9s */
    scheduleNextLine(depth = 0) {
      if (this.lineTimer) { clearTimeout(this.lineTimer); this.lineTimer = null }
      // 连续接话最多 2 轮，避免变成单口相声
      const followUp = depth < 2 && Math.random() < 0.45
      const delay = followUp ? 1200 + Math.random() * 1300 : 5000 + Math.random() * 4000
      this.lineTimer = setTimeout(() => {
        this.speakNext(depth + 1)
      }, delay)
    },
    /** 接话用的短句：更像"嗯、然后呢、你说"这种自然插话 */
    interjection() {
      const pool = ['嗯。', '然后呢？', '我在听。', '真的假的？', '哈哈，然后呢。', '嗯嗯，你说。', '就这样？']
      return pool[Math.floor(Math.random() * pool.length)]
    },
    speakNext(depth = 0) {
      // 接话轮次里，先来一句短插话，再接正经台词，像真人对话而不是一问一答
      const line = depth > 0 && Math.random() < 0.5
        ? this.interjection() + getCallLines(this.currentLangCode())[Math.floor(Math.random() * getCallLines(this.currentLangCode()).length)]
        : getCallLines(this.currentLangCode())[Math.floor(Math.random() * getCallLines(this.currentLangCode()).length)]
      this.subtitle = `${this.name}：${line}`
      this.statusText = '对方讲话中…'
      setTimeout(() => {
        if (this.statusText === '对方讲话中…') {
          this.statusText = '通话中'
        }
      }, 3000)

      // ↓↓↓ 陪伴感增强 v3：带语气起伏地念，字幕跟着句子逐句走 ↓↓↓
      const self = this
      const langCfg = getVoiceLang(this.currentLangCode())
      const p = this.currentVoiceParams()
      const ok = speakExpressive(line, {
        emotion: detectEmotion(line),
        tone: this.tone || 'warm',
        lang: langCfg.code,
        rate: p.rate,
        pitch: p.pitch,
        onSegment(idx, seg) {
          self.subtitle = `${self.name}：${seg.text}`
        }
      })
      // 环境不支持逐句播报时，退回原来的整段播报
      if (!ok) {
        // #ifdef H5
        try {
          if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
            window.speechSynthesis.cancel()
            const u = new SpeechSynthesisUtterance(line)
            u.lang = langCfg.code
            u.rate = p.rate
            u.pitch = p.pitch
            const v = matchSystemVoice(langCfg.code, window.speechSynthesis.getVoices())
            if (v) u.voice = v
            window.speechSynthesis.speak(u)
          }
        } catch (e) { /* 静默 */ }
        // #endif
      }
      // ↑↑↑ 新增结束 ↑↑↑

      this.scheduleNextLine(depth)
    },
    toggleMute() {
      this.muted = !this.muted
      uni.showToast({ title: this.muted ? '已静音' : '麦克风已开启', icon: 'none' })
    },
    toggleSpeaker() {
      this.speaker = !this.speaker
      uni.showToast({ title: this.speaker ? '扬声器已开启' : '已切换听筒', icon: 'none' })
    },
    hangup() {
      this.$emit('end', { seconds: this.seconds, durationText: this.durationText })
    }
  }
}
</script>

<style lang="scss" scoped>
.call-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 1200;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.call-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(180deg, #1A2340 0%, #0D0D0F 100%);
}
.ripple-wrap {
  position: relative;
  width: 300rpx;
  height: 300rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ripple {
  position: absolute;
  border-radius: 50%;
  border: 2rpx solid rgba(123, 160, 139, 0.4);
  animation: rippleOut 2.4s ease-out infinite;
}
.r1 { width: 220rpx; height: 220rpx; }
.r2 { width: 260rpx; height: 260rpx; animation-delay: 0.5s; }
.r3 { width: 300rpx; height: 300rpx; animation-delay: 1s; }
@keyframes rippleOut {
  0% { transform: scale(0.85); opacity: 0.8; }
  100% { transform: scale(1.25); opacity: 0; }
}
.call-avatar {
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 60rpx rgba(123, 160, 139, 0.5);
}
.call-avatar-emoji {
  font-size: 84rpx;
}
.call-name {
  position: relative;
  margin-top: 48rpx;
  font-size: 40rpx;
  font-weight: 600;
  color: #F5F5F7;
}
.call-status {
  position: relative;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: #8A9B8E;
}
.call-duration {
  position: relative;
  margin-top: 10rpx;
  font-size: 30rpx;
  color: #C8C8CE;
  font-variant-numeric: tabular-nums;
}
.call-subtitle {
  position: relative;
  margin-top: 48rpx;
  max-width: 80%;
  padding: 20rpx 32rpx;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20rpx;
}
.call-subtitle text {
  font-size: 26rpx;
  color: #E8E8EC;
  line-height: 1.6;
}
.call-controls {
  position: absolute;
  bottom: 140rpx;
  left: 0; right: 0;
  display: flex;
  justify-content: center;
  gap: 70rpx;
}
.ctl-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx;
}
.ctl-icon {
  width: 110rpx;
  height: 110rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
}
.ctl-btn:active .ctl-icon { transform: scale(0.92); }
.ctl-btn.off .ctl-icon { background: rgba(255, 255, 255, 0.35); }
.ctl-btn.hangup .ctl-icon {
  background: #E53935;
  transform: rotate(135deg);
}
.ctl-btn.hangup .ctl-icon text { transform: none; }
.ctl-label {
  margin-top: 14rpx;
  font-size: 22rpx;
  color: #B8B8BE;
}
</style>
