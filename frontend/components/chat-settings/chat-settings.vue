<template>
  <view class="cs-mask" v-if="visible" @click="$emit('close')">
    <view class="cs-panel" @click.stop>
      <view class="cs-header">
        <text class="cs-title">⚙️ 聊天设置</text>
        <text class="cs-close" @click="$emit('close')">✕</text>
      </view>

      <scroll-view scroll-y class="cs-body">
        <!-- 气泡样式 -->
        <view class="cs-group">
          <text class="group-title">💬 聊天气泡</text>
          <view class="bubble-options">
            <view
              v-for="b in bubbleOptions"
              :key="b.id"
              class="bubble-opt"
              :class="[
                'bubble-' + b.id,
                { active: settings.bubbleStyle === b.id, locked: b.locked }
              ]"
              @click="selectBubble(b)"
            >
              <text class="bubble-demo">你好呀~</text>
              <text class="bubble-name">{{ b.locked ? '🔒 ' + b.name : b.name }}</text>
            </view>
          </view>
        </view>

        <!-- 聊天背景 -->
        <view class="cs-group">
          <text class="group-title">🖼️ 聊天背景</text>
          <view class="bg-options">
            <view
              v-for="bg in bgOptions"
              :key="bg.id"
              class="bg-opt"
              :class="{ active: settings.chatBackground === bg.id, locked: bg.locked }"
              :style="{ background: bg.css }"
              @click="selectBg(bg)"
            >
              <text v-if="bg.locked" class="bg-lock">🔒</text>
              <text v-if="settings.chatBackground === bg.id" class="bg-check">✓</text>
              <text class="bg-name">{{ bg.name }}</text>
            </view>
            <!-- 自定义上传背景 -->
            <view class="bg-opt upload" @click="uploadBackground">
              <text class="bg-lock">＋</text>
              <text class="bg-name">自定义</text>
            </view>
          </view>
        </view>

        <!-- 音色设置 -->
        <view class="cs-group">
          <text class="group-title">🎙️ AI音色（自定义语音音色）</text>
          <view class="voice-presets">
            <view
              v-for="v in voicePresets"
              :key="v.id"
              class="voice-preset"
              :class="{ active: settings.voiceId === v.id }"
              @click="selectVoice(v)"
            >
              <text class="vp-name">{{ v.name }}</text>
              <text class="vp-desc">{{ v.desc }}</text>
            </view>
          </view>
          <view class="slider-row">
            <text class="slider-label">语速</text>
            <slider
              class="cs-slider"
              :value="settings.rate * 100"
              :min="50" :max="200"
              activeColor="#6B8E7B"
              @change="(e) => settings.rate = e.detail.value / 100"
              @changing="onRateChange"
            />
            <text class="slider-val">{{ settings.rate.toFixed(2) }}x</text>
          </view>
          <view class="slider-row">
            <text class="slider-label">音调</text>
            <slider
              class="cs-slider"
              :value="settings.pitch * 100"
              :min="50" :max="180"
              activeColor="#6B8E7B"
              @change="(e) => settings.pitch = e.detail.value / 100"
            />
            <text class="slider-val">{{ settings.pitch.toFixed(2) }}</text>
          </view>
        </view>

        <!-- 语音多语言 -->
        <view class="cs-group">
          <text class="group-title">🌐 语音多语言</text>
          <view class="lang-options">
            <view
              v-for="l in languages"
              :key="l.code"
              class="lang-opt"
              :class="{ active: settings.voiceLang === l.code, unsupported: l.supported === false }"
              @click="selectLang(l)"
            >
              <text>{{ l.flag }} {{ l.name }}</text>
              <text v-if="l.supported === false" class="lang-warn">缺语音包</text>
            </view>
          </view>
          <view class="lang-actions">
            <view class="lang-preview" @click="previewCurrent">
              <text>🔊 试听当前语种</text>
            </view>
          </view>
          <text class="lang-tip">切换后：语音播报 / 语音通话 / 语音输入 / AI 回复都会切到该语种（AI 回复语种需重新发一条消息生效）</text>
        </view>

        <!-- 动作描述开关 -->
        <view class="cs-group">
          <view class="switch-row">
            <view class="switch-info">
              <text class="switch-title">🎭 动作描述</text>
              <text class="switch-desc">开启后，AI回复会附带角色动作描述（如 *轻轻拍了拍你的头*）</text>
            </view>
            <switch :checked="settings.actionDescEnabled" color="#6B8E7B" @change="(e) => settings.actionDescEnabled = e.detail.value" />
          </view>
        </view>

        <!-- ↓↓↓ 改造（2026-10-27）：「实时视频通话 · 敬请期待」落地为可体验的「动态形象互动」 ↓↓↓
             真正的视频通话需要数字人视频流服务（云端渲染 + RTC），本项目不具备；
             这里用已有能力做等价版：立绘会眨眼呼吸 + AI 回复走流式接口 + TTS 语音播报。 -->
        <view class="cs-group">
          <view class="switch-row" @click="openAvatarLive">
            <view class="switch-info">
              <text class="switch-title">🎬 动态形象互动</text>
              <text class="switch-desc">角色立绘会眨眼呼吸，AI 回复可语音播报</text>
            </view>
            <text class="pending-tag">去体验 ›</text>
          </view>
        </view>
        <!-- ↑↑↑ 改造结束 ↑↑↑ -->

        <view class="cs-bottom-space"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
/**
 * 聊天设置面板：气泡样式 / 聊天背景 / 音色 / 多语言 / 动作描述开关
 * 设置对象由父组件传入（v-model式双向），保存逻辑在父组件
 */
import { BUBBLE_STYLES } from '@/common/economy'
import { getVoiceLangs, getVoiceLang, isVoiceLangSupported, matchSystemVoice } from '@/common/voice-lang'

export default {
  props: {
    visible: { type: Boolean, default: false },
    settings: { type: Object, required: true }
  },
  data() {
    return {
      bubbleOptions: [],
      bgOptions: [
        { id: 'default', name: '默认', css: '#F5F6F7', locked: false },
        { id: 'mint', name: '薄荷', css: 'linear-gradient(180deg, #E0F2F1, #F1F8E9)', locked: false },
        { id: 'sunset', name: '黄昏', css: 'linear-gradient(180deg, #FFF3E0, #FFE0B2)', locked: false },
        { id: 'aurora', name: '极光之夜', css: 'linear-gradient(180deg, #1A2340, #0D0D0F)', locked: true }
      ],
      voicePresets: [
        { id: 'default', name: '默认', desc: '温柔自然', rate: 1.0, pitch: 1.0 },
        { id: 'soft', name: '轻柔', desc: '慢速轻声', rate: 0.85, pitch: 1.1 },
        { id: 'lively', name: '活泼', desc: '元气语速', rate: 1.2, pitch: 1.3 },
        { id: 'deep', name: '沉稳', desc: '低沉温和', rate: 0.95, pitch: 0.8 },
        { id: 'fairy', name: '精灵', desc: '高音灵动（限定）', rate: 1.05, pitch: 1.6, locked: true }
      ],
      // 语种统一从 common/voice-lang 取（含试听文本 / 离线兜底语料 / 语音包匹配别名）
      languages: getVoiceLangs().map(l => ({ ...l, supported: null }))
    }
  },
  watch: {
    visible(v) {
      if (v) this.initOptions()
    }
  },
  methods: {
    // ↓↓↓ 新增（2026-10-27）：打开「动态形象互动」页 ↓↓↓
    openAvatarLive() {
      this.$emit('close')
      uni.navigateTo({ url: '/pages/avatar-live/avatar-live' })
    },
    // ↑↑↑ 新增结束 ↑↑↑
    initOptions() {
      // 语种支持状态：打开面板时探测一次系统语音包（拿不到列表时为 null，不误报）
      this.refreshLangSupport()
      // 气泡解锁状态由父组件通过 settings.unlockedDecos 提供
      const unlocked = this.settings.unlockedDecos || []
      this.bubbleOptions = BUBBLE_STYLES.map(b => ({
        ...b,
        locked: b.needUnlock && !unlocked.includes(b.needUnlock)
      }))
      // 极光背景需商城解锁
      const auroraLocked = !unlocked.includes('deco_bg_aurora')
      const bg = this.bgOptions.find(b => b.id === 'aurora')
      if (bg) bg.locked = auroraLocked
    },
    selectBubble(b) {
      if (b.locked) {
        uni.showToast({ title: '该气泡需在商城解锁', icon: 'none' })
        return
      }
      this.settings.bubbleStyle = b.id
      this.$emit('change', this.settings)
    },
    selectBg(bg) {
      if (bg.locked) {
        uni.showToast({ title: '该背景需在商城解锁', icon: 'none' })
        return
      }
      this.settings.chatBackground = bg.id
      this.$emit('change', this.settings)
    },
    /** 探测每个语种在本机是否有语音包（H5 有效；拿不到列表时保持 null） */
    refreshLangSupport() {
      // #ifdef H5
      try {
        if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
        let voices = window.speechSynthesis.getVoices()
        const apply = (list) => {
          this.languages = this.languages.map(l => ({
            ...l,
            supported: isVoiceLangSupported(l.code, list)
          }))
        }
        if (voices && voices.length) {
          apply(voices)
          return
        }
        // voices 异步加载：监听一次 + 超时兜底
        const onChanged = () => {
          window.speechSynthesis.removeEventListener('voiceschanged', onChanged)
          apply(window.speechSynthesis.getVoices())
        }
        window.speechSynthesis.addEventListener('voiceschanged', onChanged)
        setTimeout(() => {
          window.speechSynthesis.removeEventListener('voiceschanged', onChanged)
          apply(window.speechSynthesis.getVoices())
        }, 1500)
      } catch (e) {
        /* 探测失败不影响选择 */
      }
      // #endif
    },
    /** 选择语种：写回 settings + 通知父组件保存 + 立即试听一句 */
    selectLang(l) {
      this.settings.voiceLang = l.code
      this.$emit('change', this.settings)
      this.$emit('lang-change', l.code)
      this.previewLang(l)
      if (l.supported === false) {
        uni.showToast({
          title: '系统未安装该语种语音包，将尝试用默认发音',
          icon: 'none',
          duration: 2000
        })
      }
    },
    previewCurrent() {
      this.previewLang(getVoiceLang(this.settings.voiceLang))
    },
    /** 试听：让"切了语种"这件事立刻被听见（原实现点了没任何反馈） */
    previewLang(l) {
      // #ifdef H5
      try {
        if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
          uni.showToast({ title: '当前环境不支持语音播放', icon: 'none' })
          return
        }
        window.speechSynthesis.cancel()
        const speak = () => {
          try {
            const u = new SpeechSynthesisUtterance(l.sample || l.name)
            u.lang = l.code
            const v = matchSystemVoice(l.code, window.speechSynthesis.getVoices())
            if (v) u.voice = v
            u.rate = this.settings.rate || 1.0
            u.pitch = this.settings.pitch || 1.0
            window.speechSynthesis.speak(u)
          } catch (e) { /* 静默 */ }
        }
        const voices = window.speechSynthesis.getVoices()
        if (!voices || !voices.length) {
          const onChanged = () => {
            window.speechSynthesis.removeEventListener('voiceschanged', onChanged)
            speak()
          }
          window.speechSynthesis.addEventListener('voiceschanged', onChanged)
          setTimeout(() => {
            window.speechSynthesis.removeEventListener('voiceschanged', onChanged)
            speak()
          }, 1500)
        } else {
          speak()
        }
      } catch (e) { /* 静默 */ }
      // #endif
      // #ifndef H5
      uni.showToast({ title: '当前环境暂不支持语音播报', icon: 'none', duration: 1500 })
      // #endif
    },
    selectVoice(v) {
      if (v.locked) {
        uni.showToast({ title: '限定音色需在商城解锁', icon: 'none' })
        return
      }
      this.settings.voiceId = v.id
      this.settings.rate = v.rate
      this.settings.pitch = v.pitch
      this.$emit('change', this.settings)
    },
    onRateChange(e) {
      this.settings.rate = e.detail.value / 100
    },
    uploadBackground() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths[0]) {
            this.settings.chatBackgroundImage = res.tempFilePaths[0]
            this.settings.chatBackground = 'custom'
            this.$emit('change', this.settings)
            uni.showToast({ title: '背景已设置', icon: 'success' })
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.cs-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: flex;
  align-items: flex-end;
}
.cs-panel {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  max-height: 82vh;
  display: flex;
  flex-direction: column;
}
.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.cs-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
}
.cs-close {
  font-size: 34rpx;
  color: #999;
  padding: 8rpx;
}
.cs-body {
  flex: 1;
  padding: 8rpx 32rpx 0;
  max-height: 70vh;
  box-sizing: border-box;
}

.cs-group {
  margin: 28rpx 0;
}
.group-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

/* 气泡 */
.bubble-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.bubble-opt {
  padding: 20rpx 24rpx;
  border-radius: 20rpx;
  border: 3rpx solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.bubble-demo {
  font-size: 24rpx;
  padding: 10rpx 20rpx;
  border-radius: 14rpx;
  background: #6B8E7B;
  color: #fff;
}
.bubble-opt.bubble-mint .bubble-demo { background: #4DB6AC; }
.bubble-opt.bubble-sakura .bubble-demo { background: #F48FB1; }
.bubble-opt.bubble-galaxy .bubble-demo { background: linear-gradient(135deg, #7986CB, #512DA8); }
.bubble-opt.active { border-color: #6B8E7B; }
.bubble-opt.locked { opacity: 0.55; }
.bubble-name {
  margin-top: 10rpx;
  font-size: 20rpx;
  color: #666;
}

/* 背景 */
.bg-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.bg-opt {
  position: relative;
  width: calc((100% - 48rpx) / 4);
  height: 120rpx;
  border-radius: 20rpx;
  border: 3rpx solid transparent;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  overflow: hidden;
}
.bg-opt.active { border-color: #6B8E7B; }
.bg-opt.locked { opacity: 0.6; }
.bg-lock {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 36rpx;
}
.bg-check {
  position: absolute;
  top: 8rpx; right: 12rpx;
  font-size: 24rpx;
  color: #fff;
  font-weight: 700;
  text-shadow: 0 1rpx 4rpx rgba(0,0,0,0.4);
}
.bg-name {
  font-size: 20rpx;
  color: #666;
  background: rgba(255, 255, 255, 0.75);
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  margin-bottom: 10rpx;
}
.bg-opt.upload {
  background: #F5F6F7;
  border: 2rpx dashed #CCC;
  align-items: center;
}
.bg-opt.upload .bg-lock {
  position: static;
  transform: none;
  margin-top: 16rpx;
}

/* 音色 */
.voice-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.voice-preset {
  padding: 18rpx 26rpx;
  background: #F5F6F7;
  border-radius: 18rpx;
  border: 3rpx solid transparent;
}
.voice-preset.active { border-color: #6B8E7B; background: #E8F4EC; }
.vp-name {
  font-size: 26rpx;
  color: #333;
  display: block;
}
.vp-desc {
  font-size: 20rpx;
  color: #999;
  margin-top: 4rpx;
  display: block;
}
.slider-row {
  display: flex;
  align-items: center;
  margin-top: 20rpx;
}
.slider-label {
  font-size: 24rpx;
  color: #666;
  width: 80rpx;
}
.cs-slider { flex: 1; margin: 0 10rpx; }
.slider-val {
  font-size: 22rpx;
  color: #6B8E7B;
  width: 90rpx;
  text-align: right;
}

/* 语言 */
.lang-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.lang-opt {
  padding: 14rpx 28rpx;
  background: #F5F6F7;
  border-radius: 999rpx;
  border: 2rpx solid transparent;
}
.lang-opt {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.lang-opt.active { border-color: #6B8E7B; background: #E8F4EC; }
.lang-opt.unsupported { opacity: 0.62; }
.lang-opt text { font-size: 24rpx; color: #333; }
.lang-warn {
  font-size: 18rpx;
  color: #C0704F;
  background: rgba(192, 112, 79, 0.1);
  padding: 2rpx 10rpx;
  border-radius: 999rpx;
}
.lang-actions {
  display: flex;
  margin-top: 18rpx;
}
.lang-preview {
  padding: 12rpx 28rpx;
  background: #F5F6F7;
  border-radius: 999rpx;
  border: 2rpx solid #E6E6E6;
}
.lang-preview text { font-size: 22rpx; color: #6B8E7B; }
.lang-tip {
  display: block;
  margin-top: 16rpx;
  font-size: 20rpx;
  color: #BBB;
  line-height: 1.5;
}

/* 开关 */
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.switch-info { flex: 1; margin-right: 20rpx; }
.switch-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
}
.switch-desc {
  font-size: 22rpx;
  color: #999;
  margin-top: 6rpx;
  display: block;
  line-height: 1.5;
}
.switch-row.pending { opacity: 0.6; }
.pending-tag {
  padding: 6rpx 18rpx;
  background: #F5F6F7;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #999;
}
.cs-bottom-space { height: calc(env(safe-area-inset-bottom) + 40rpx); }
</style>
