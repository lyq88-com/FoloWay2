<template>
  <view class="xt-page xt-s55">
    <view class="body">
      <view class="chat-head" style="padding:2px 2px 12px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">设置</view>
          <view class="chat-st">按你舒服的方式来</view>
        </view>
        <view class="icon-btn"></view>
      </view>

      <view class="cal-sec"><text class="t">陪伴体验</text><text class="s">会影响她怎么出现</text></view>
      <view class="set-row" @click="toggleAutoMode">
        <view class="si tint-green"><xt-icon name="i-moon" /></view>
        <view class="tx">
          <view class="t">夜间模式</view>
          <view class="m">22:00 后自动变暗，她的声音也会放轻</view>
        </view>
        <view class="switch2" :class="{ on: autoModeEnabled }"></view>
      </view>
      <view class="set-row" @click="toggleTts">
        <view class="si tint-blue"><xt-icon name="i-call" /></view>
        <view class="tx">
          <view class="t">语音回复</view>
          <view class="m">她的消息会同时用语音读出来</view>
        </view>
        <view class="switch2" :class="{ on: settings.ttsEnabled }"></view>
      </view>
      <view class="set-row" @click="toggleProactiveMsg">
        <view class="si tint-peach"><xt-icon name="i-heart" /></view>
        <view class="tx">
          <view class="t">主动关心</view>
          <view class="m">察觉你三天没来时，她会先发一条消息</view>
        </view>
        <view class="switch2" :class="{ on: allowProactiveMsg }"></view>
      </view>
      <view class="set-row" @click="toggleEyeCare">
        <view class="si tint-sand"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">定时护眼休息</view>
          <view class="m">到点轻轻提醒你远眺</view>
        </view>
        <view class="switch2" :class="{ on: eyeCareEnabled }"></view>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">通知</text><text class="s">随时可关</text></view>
      <view class="set-row" @click="toggleNotification">
        <view class="si tint-blue"><xt-icon name="i-chat" /></view>
        <view class="tx">
          <view class="t">消息通知</view>
          <view class="m">她给你发消息时提醒</view>
        </view>
        <view class="switch2" :class="{ on: settings.notificationEnabled }"></view>
      </view>
      <view class="set-row">
        <view class="si tint-green"><xt-icon name="i-clock" /></view>
        <view class="tx">
          <view class="t">休息间隔</view>
          <view class="m">每 {{ eyeCareInterval }} 分钟提醒一次</view>
        </view>
        <text class="v">{{ eyeCareInterval }} 分钟</text>
      </view>
      <view v-if="eyeCareEnabled" style="padding:0 12px 8px">
        <slider
          :value="eyeCareInterval"
          :min="15"
          :max="90"
          :step="15"
          activeColor="#24493A"
          backgroundColor="#F0F3F2"
          block-size="12"
          @change="onEyeCareIntervalChange"
        />
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">数据与账号</text><text class="s">只属于你</text></view>
      <view class="set-row" @click="exportMyData">
        <view class="si tint-sand"><xt-icon name="i-archive" /></view>
        <view class="tx">
          <view class="t">聊天与记忆</view>
          <view class="m">保存在本地，可随时导出</view>
        </view>
        <text class="v">›</text>
      </view>
      <view class="set-row" @click="toggleTeenMode">
        <view class="si tint-peach"><xt-icon name="i-user" /></view>
        <view class="tx">
          <view class="t">青少年模式</view>
          <view class="m">隐藏VIP入口，并定时提醒休息</view>
        </view>
        <view class="switch2" :class="{ on: teenMode }"></view>
      </view>
      <view class="set-row" @click="goDisclaimer">
        <view class="si" style="background:#F5F2EF;color:#C08A56"><xt-icon name="i-edit" /></view>
        <view class="tx">
          <view class="t">免责声明与协议</view>
          <view class="m">关于 AI 陪伴的边界说明</view>
        </view>
        <text class="v">›</text>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">更多</text><text class="s">都可以再调</text></view>
      <view class="set-row" @click="showThemeOptions">
        <view class="si tint-green"><xt-icon name="i-moon" /></view>
        <view class="tx">
          <view class="t">外观主题</view>
          <view class="m">浅色 / 深色 / 跟随日夜</view>
        </view>
        <text class="v">{{ currentThemeName }}</text>
      </view>
      <view class="set-row">
        <view class="si tint-blue"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">屏幕亮度</view>
          <view class="m">拖动下方滑杆调节</view>
        </view>
        <text class="v">{{ Math.round(brightness * 100) }}%</text>
      </view>
      <view style="padding:0 12px 8px">
        <slider
          :value="brightnessValue"
          :min="0"
          :max="100"
          :step="1"
          activeColor="#24493A"
          backgroundColor="#F0F3F2"
          block-size="12"
          @change="onBrightnessChange"
        />
      </view>
      <view class="set-row" @click="goCharacterGallery">
        <view class="si tint-peach"><xt-icon name="i-user" /></view>
        <view class="tx">
          <view class="t">更换陪伴伙伴</view>
          <view class="m">换一个人陪你走这段路</view>
        </view>
        <text class="v">{{ $store.state.aiConfig.name || '林夕' }}</text>
      </view>
      <view class="set-row" @click="reTakeQuiz">
        <view class="si tint-teal"><xt-icon name="i-brain" /></view>
        <view class="tx">
          <view class="t">重新性格测评</view>
          <view class="m">更新后会影响她的相处方式</view>
        </view>
        <text class="v">›</text>
      </view>
      <view class="set-row" @click="clearCache">
        <view class="si tint-sand"><xt-icon name="i-archive" /></view>
        <view class="tx">
          <view class="t">清除缓存</view>
          <view class="m">释放本地临时空间</view>
        </view>
        <text class="v">›</text>
      </view>
      <view class="set-row" @click="showAbout">
        <view class="si tint-green"><xt-icon name="i-heart" /></view>
        <view class="tx">
          <view class="t">关于循途</view>
          <view class="m">为什么做循途</view>
        </view>
        <text class="v">v1.0.0</text>
      </view>
    </view>
  </view>
</template>

<script>
import { applyTheme, getCurrentTheme, themes, isAutoMode, setAutoMode, getBrightness, setBrightness } from '@/common/theme'
import userApi from '@/api/user'
import { resetQuiz } from '@/common/personality-quiz'
// ↓↓↓ 新增（2026-10-27）：语音播报（H5 用 Web Speech API） ↓↓↓
import tts from '@/common/tts'
// ↑↑↑ 新增结束 ↑↑↑
// ↓↓↓ 安全合规批次：设置扩展接口（主动消息/青少年模式/数据导出） ↓↓↓
import settingsExtraApi from '@/api/settings-extra'
// ↑↑↑ 新增结束 ↑↑↑
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      currentTheme: '',
      brightness: 0.8,
      autoModeEnabled: false,
      settings: {
        notificationEnabled: true,
        ttsEnabled: true
      },
      eyeCareEnabled: false,
      eyeCareInterval: 45,
      // ↓↓↓ 安全合规批次 ↓↓↓
      allowProactiveMsg: true,   // 允许AI主动消息
      teenMode: false,           // 青少年模式
      // ↑↑↑ 新增结束 ↑↑↑
    }
  },
  computed: {
    currentThemeName() {
      if (this.autoModeEnabled) return '自动模式'
      return themes[this.currentTheme]?.name || '浅色主题'
    },
    brightnessValue() {
      // 统一使用 theme.js 中的 getBrightness() 返回的 0-100 整数值
      return Math.round(this.brightness * 100)
    }
  },
  onShow() {
    this.loadSettings()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/profile/profile' }) })
    },
    // ↓↓↓ 新增 ↓↓↓ 系统亮度调节：H5 / 非 App 端不支持，直接跳过而不是抛未捕获的 Promise
    applyScreenBrightness(value) {
      if (typeof uni.setScreenBrightness !== 'function') return
      const v = value === undefined ? this.brightness : value
      const p = uni.setScreenBrightness({ value: v })
      if (p && typeof p.catch === 'function') {
        p.catch(() => { /* 不支持时忽略 */ })
      }
    },
    loadSettings() {
      this.currentTheme = getCurrentTheme()
      this.autoModeEnabled = isAutoMode()
      try {
        // 使用 theme.js 统一的 getBrightness 返回 0-100 整数
        const b = getBrightness()
        this.brightness = b / 100  // 模板显示用 0.xx 小数（Math.round(x*100)用于百分比展示）
        // ↓↓↓ 修复 ↓↓↓ H5 端 uni.setScreenBrightness 是 unimplemented 的，调用会返回 rejected Promise，
        // try/catch 抓不到 → 控制台刷 "[全局捕获] Promise未捕获"。改成先判断 API 是否存在。
        this.applyScreenBrightness()
      } catch (e) {
        this.brightness = 0.8
      }
      this.settings = { ...this.$store.state.settings }
      
      this.eyeCareEnabled = uni.getStorageSync('eye_care_enabled') === 'true'
      this.eyeCareInterval = parseInt(uni.getStorageSync('eye_care_interval')) || 45

      // ↓↓↓ 新增（2026-10-27）：进页面时把开关状态同步给播报模块 ↓↓↓
      try { tts.setEnabled(this.settings.ttsEnabled !== false) } catch (e) {}
      // ↑↑↑ 新增结束 ↑↑↑

      // ↓↓↓ 安全合规批次：读取云端偏好（失败回退本地缓存） ↓↓↓
      this.loadExtraPrefs()
      // ↑↑↑ 新增结束 ↑↑↑
    },

    // ↓↓↓ 安全合规批次：偏好读写 / 数据导出 / 免责声明 ↓↓↓
    async loadExtraPrefs() {
      // 本地缓存先兜底展示，云端读取成功后覆盖
      try {
        this.allowProactiveMsg = uni.getStorageSync('pref_allow_proactive_msg') !== 'false'
        this.teenMode = uni.getStorageSync('pref_teen_mode') === 'true'
      } catch (e) { /* 静默 */ }
      try {
        const res = await settingsExtraApi.getPrefs()
        const d = (res && res.data) || {}
        if (typeof d.allow_proactive_msg === 'number') {
          this.allowProactiveMsg = d.allow_proactive_msg === 1
          uni.setStorageSync('pref_allow_proactive_msg', this.allowProactiveMsg ? 'true' : 'false')
        }
        if (typeof d.teen_mode === 'number') {
          this.teenMode = d.teen_mode === 1
          uni.setStorageSync('pref_teen_mode', this.teenMode ? 'true' : 'false')
        }
      } catch (e) { /* 未登录/游客：保留本地缓存值 */ }
    },
    async toggleProactiveMsg() {
      const next = !this.allowProactiveMsg
      this.allowProactiveMsg = next
      uni.setStorageSync('pref_allow_proactive_msg', next ? 'true' : 'false')
      uni.showToast({ title: next ? '已允许AI主动消息' : '已关闭AI主动消息', icon: 'none' })
      try {
        await settingsExtraApi.savePrefs({ allow_proactive_msg: next ? 1 : 0 })
      } catch (e) {
        console.warn('[settings] 保存主动消息开关失败（已存本地）:', e)
      }
    },
    toggleTeenMode() {
      const next = !this.teenMode
      const apply = () => {
        this.teenMode = next
        uni.setStorageSync('pref_teen_mode', next ? 'true' : 'false')
        settingsExtraApi.savePrefs({ teen_mode: next ? 1 : 0 }).catch(() => {})
        if (next) {
          uni.showToast({ title: '青少年模式已开启，注意休息哦', icon: 'none', duration: 2500 })
        } else {
          uni.showToast({ title: '已退出青少年模式', icon: 'none' })
        }
      }
      if (next) {
        uni.showModal({
          title: '开启青少年模式',
          content: '开启后将隐藏VIP等付费入口，并每30分钟提醒你休息。确定开启吗？',
          success: (r) => { if (r.confirm) apply() }
        })
      } else {
        apply()
      }
    },
    async exportMyData() {
      uni.showLoading({ title: '正在打包数据...', mask: true })
      try {
        const res = await settingsExtraApi.exportMyData()
        uni.hideLoading()
        const d = (res && res.data) || {}
        const summary = d.summary || {}
        const lines = Object.keys(summary).map(k => `${summary[k]} 条`).join(' · ')
        // 演示版：弹窗展示摘要，并提供复制完整 JSON 的入口
        uni.showModal({
          title: '数据导出成功',
          content: `导出时间：${d.exported_at || ''}\n包含：${lines || '暂无数据'}\n\n完整数据已留档，可复制到剪贴板保存。`,
          confirmText: '复制数据',
          cancelText: '关闭',
          success: (r) => {
            if (r.confirm) {
              try {
                uni.setClipboardData({
                  data: JSON.stringify(d.data || {}, null, 2),
                  success: () => uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
                })
              } catch (e) {
                uni.showToast({ title: '复制失败', icon: 'none' })
              }
            }
          }
        })
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: (e && e.message) || '导出失败，请稍后再试', icon: 'none' })
      }
    },
    goDisclaimer() {
      uni.navigateTo({ url: '/pages/disclaimer/disclaimer' })
    },
    // ↑↑↑ 安全合规批次新增结束 ↑↑↑

    showThemeOptions() {
      const items = ['浅色', '深色', '自动']
      uni.showActionSheet({
        itemList: items,
        success: (res) => {
          const index = res.tapIndex
          if (index === 0) {
            setAutoMode(false)
            this.autoModeEnabled = false
            this.currentTheme = 'light'
            applyTheme('light')
            uni.showToast({ title: '已切换为浅色主题', icon: 'none' })
          } else if (index === 1) {
            setAutoMode(false)
            this.autoModeEnabled = false
            this.currentTheme = 'dark'
            applyTheme('dark')
            uni.showToast({ title: '已切换为深色主题', icon: 'none' })
          } else if (index === 2) {
            setAutoMode(true)
            this.autoModeEnabled = true
            const hour = new Date().getHours()
            const sunriseHour = 6
            const sunsetHour = 19
            const newTheme = hour >= sunriseHour && hour < sunsetHour ? 'light' : 'dark'
            this.currentTheme = newTheme
            applyTheme(newTheme)
            uni.showToast({ title: '已开启自动模式', icon: 'none' })
          }
        }
      })
    },
    onBrightnessChange(e) {
      // slider 现在是 0-100 整数
      const percent = Number(e.detail.value) || 0
      const value = percent / 100
      this.brightness = value
      // ↓↓↓ 修复 ↓↓↓ 同上：原来直接调 uni.setScreenBrightness 会在 H5 抛未捕获 Promise
      this.applyScreenBrightness(value)
      // 使用 theme.js 统一 setBrightness，写入 CSS 变量+持久化
      setBrightness(percent)
    },
    toggleNotification() {
      this.settings.notificationEnabled = !this.settings.notificationEnabled
      this.$store.commit('setSettings', this.settings)
      try {
        userApi.updateSettings(this.settings)
      } catch (e) {}
      uni.showToast({
        title: this.settings.notificationEnabled ? '已开启通知' : '已关闭通知',
        icon: 'none'
      })
    },
    toggleTts() {
      this.settings.ttsEnabled = !this.settings.ttsEnabled
      this.$store.commit('setSettings', this.settings)
      try {
        userApi.updateSettings(this.settings)
      } catch (e) {}
      // ↓↓↓ 新增（2026-10-27）：开关真正作用到播报模块 ↓↓↓
      // 之前这里只改了个布尔值，没有任何地方发声
      try {
        tts.setEnabled(this.settings.ttsEnabled)
        if (this.settings.ttsEnabled) {
          tts.speak('语音播报已开启')
        }
      } catch (e) { /* 不支持 TTS 时静默 */ }
      // ↑↑↑ 新增结束 ↑↑↑
      uni.showToast({
        title: this.settings.ttsEnabled ? '已开启语音' : '已关闭语音',
        icon: 'none'
      })
    },
    toggleAutoMode() {
      this.autoModeEnabled = !this.autoModeEnabled
      setAutoMode(this.autoModeEnabled)
      if (this.autoModeEnabled) {
        const hour = new Date().getHours()
        const sunriseHour = 6
        const sunsetHour = 19
        const newTheme = hour >= sunriseHour && hour < sunsetHour ? 'light' : 'dark'
        this.currentTheme = newTheme
        applyTheme(newTheme)
        uni.showToast({ title: '已开启自动日夜切换', icon: 'none' })
      } else {
        uni.showToast({ title: '已关闭自动日夜切换', icon: 'none' })
      }
    },
    showAbout() {
      uni.showModal({
        title: '关于循途',
        content: '循途 v1.0.0\n\n无论何时何地，与TA共度每时每刻。\n通过AI陪伴让习惯养成更有趣。\n\n© 2026 循途',
        showCancel: false,
        confirmText: '知道了'
      })
    },
    goCharacterGallery() {
      uni.navigateTo({ url: '/pages/character-gallery/character-gallery' })
    },
    reTakeQuiz() {
      uni.showModal({
        title: '重新测评',
        content: '确定要重新进行性格测评吗？测评结果将更新你的AI伙伴匹配。',
        success: (r) => {
          if (r.confirm) {
            resetQuiz()
            const picked = uni.getStorageSync('ai_partner_id')
            uni.navigateTo({ url: picked ? `/pages/personality-quiz/personality-quiz?roleId=${encodeURIComponent(picked)}` : '/pages/personality-quiz/personality-quiz' })
          }
        }
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
              uni.removeStorageSync('custom_bg')
              uni.removeStorageSync('screen_brightness')
              uni.removeStorageSync('app_theme')
              uni.showToast({ title: '缓存已清除', icon: 'success' })
            } catch (e) {
              uni.showToast({ title: '清除失败', icon: 'none' })
            }
          }
        }
      })
    },
    toggleEyeCare() {
      this.eyeCareEnabled = !this.eyeCareEnabled
      uni.setStorageSync('eye_care_enabled', this.eyeCareEnabled ? 'true' : 'false')
      if (this.eyeCareEnabled) {
        uni.showToast({ title: '护眼提醒已开启', icon: 'none' })
      } else {
        uni.showToast({ title: '护眼提醒已关闭', icon: 'none' })
      }
    },
    onEyeCareIntervalChange(e) {
      this.eyeCareInterval = e.detail.value
      uni.setStorageSync('eye_care_interval', this.eyeCareInterval)
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间，避免最后一行贴边 */
.xt-page.xt-s55 .body {
  padding-bottom: 24px;
}
</style>
