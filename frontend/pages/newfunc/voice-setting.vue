<template>
  <view class="xt-page xt-s58">
    <view class="body">
      <view class="chat-head" style="padding:2px 2px 12px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">她的声音</view>
          <view class="chat-st">先听听看，再决定</view>
        </view>
        <view class="icon-btn" @click="currentPack && preview(currentPack)"><xt-icon name="i-call" /></view>
      </view>

      <view class="mem-hero" style="padding:14px;display:flex;align-items:center;gap:11px">
        <view style="width:42px;height:42px;border-radius:50%;background:#FFFDFA;color:#24493A;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 8px 18px -12px rgba(62,93,74,.5)">
          <xt-icon name="i-call" />
        </view>
        <view style="flex:1;min-width:0">
          <view style="font-size:10px;font-weight:900">"我在。今天想聊点什么？"</view>
          <view style="font-size:7.5px;color:#8E9A91;margin-top:2px">当前音色 · {{ voiceName(currentVoiceId) }}</view>
        </view>
        <text class="chip on" style="font-size:7.5px" @click="currentPack && preview(currentPack)">试听</text>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">音色</text><text class="s">每个都可以试听</text></view>
      <view v-for="(t, i) in timbres" :key="t.voice_id" class="mem-item" @click="chooseVoice(t.pack, t)">
        <view
          class="mi"
          :class="i % 3 === 0 ? 'tint-green' : (i % 3 === 1 ? 'tint-peach' : 'tint-blue')"
          style="border-radius:50%"
        ><xt-icon name="i-call" /></view>
        <view class="tx">
          <text class="t">{{ t.pack.name }} · {{ t.name }}</text>
          <text class="m">{{ t.pack.langTag }} · {{ t.gender === 'male' ? '男声' : '女声' }}{{ t.is_default ? ' · 默认' : '' }}</text>
        </view>
        <text
          class="v"
          :style="currentVoiceId === t.voice_id ? 'font-size:7px;color:var(--v7-green)' : 'font-size:7px;color:#BFC7BF'"
          @click.stop="preview(t.pack)"
        >{{ currentVoiceId === t.voice_id ? '✓ 使用中' : '试听' }}</text>
      </view>
      <view v-if="packs.length === 0" class="mem-item">
        <view class="tx"><text class="m">正在加载音色…</text></view>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">伙伴专属语音</text><text class="s">每个人都不一样</text></view>
      <view v-if="bots.length === 0" class="mem-item">
        <view class="tx"><text class="m">还没有 AI 伙伴，去「AI伙伴工坊」创建一个吧</text></view>
      </view>
      <view v-for="bot in bots" :key="bot.id" class="mem-item">
        <view class="mi tint-sand" style="border-radius:50%"><text style="font-size:13px">{{ bot.avatar }}</text></view>
        <view class="tx">
          <text class="t">{{ bot.name }}</text>
          <text class="m">{{ botVoiceName(bot) }}</text>
        </view>
        <picker
          mode="selector"
          :range="voiceOptions"
          :value="0"
          style="flex-shrink:0"
          @change="e => onPickBotVoice(bot, e.detail.value)"
        >
          <text class="v" style="font-size:7px;color:var(--v7-green)">选声音</text>
        </picker>
        <text v-if="bot.bound_voice_id" class="v" style="font-size:7px;color:#BFC7BF;margin-left:8px" @click="unbindBot(bot)">解绑</text>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">音频缓存</text><text class="s">减少重复请求</text></view>
      <view class="prob" style="padding:11px 12px">
        <view class="pr">
          <view>已缓存</view><text class="b">{{ cacheInfo.count }} 条</text>
        </view>
        <view class="pr">
          <view>命中次数</view><text class="b">{{ cacheInfo.total_hits }} 次</text>
        </view>
        <view class="pr">
          <view>占用空间</view><text class="b">{{ fmtSize(cacheInfo.total_bytes) }}</text>
        </view>
      </view>
      <view class="chips" style="margin-top:11px">
        <text class="chip" @click="currentPack && preview(currentPack)">试听当前音色</text>
        <text class="chip on" @click="clearCache">清空音频缓存</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】语音包设置页：
 * 多语种/方言音色选择 + 试听 + 默认语音设置 + AI 伙伴专属语音绑定 + 缓存管理
 */
import api from '@/api/newfunc'
import aiSpeak from '@/common/ai-speak'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      packs: [],
      bots: [],
      currentVoiceId: '',
      cacheInfo: { count: 0, total_bytes: 0, total_hits: 0 },
      previewing: false
    }
  },
  computed: {
    voiceOptions() {
      const opts = []
      this.packs.forEach(p => p.timbres.forEach(t => opts.push(`${p.name} · ${t.name}`)))
      return opts
    },
    // 设计稿音色列表：所有语音包的音色平铺
    timbres() {
      const list = []
      this.packs.forEach(p => (p.timbres || []).forEach(t => list.push({ ...t, pack: p })))
      return list
    },
    // 当前音色所属语音包（用于试听）
    currentPack() {
      const hit = this.packs.find(p => (p.timbres || []).some(t => t.voice_id === this.currentVoiceId))
      return hit || this.packs[0] || null
    }
  },
  onShow() {
    this.load()
  },
  onUnload() {
    aiSpeak.stop()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    genderIcon(g) { return g === 'male' ? '👨' : '👩' },
    langTag(pack) {
      const map = { 'zh-default': '普通话', 'ko-kr': '한국어', 'ja-jp': '日本語', 'zh-hk': '粤语', 'zh-liaoning': '东北话', 'zh-shaanxi': '陕西话', 'zh-tw': '台湾腔', 'en-us': '英语' }
      return map[pack.pack_code] || pack.lang_code
    },
    voiceName(voiceId) {
      for (const p of this.packs) {
        for (const t of p.timbres) if (t.voice_id === voiceId) return `${p.name} · ${t.name}`
      }
      return voiceId || '默认语音'
    },
    botVoiceName(bot) {
      if (bot.bound_voice_id) return `专属：${this.voiceName(bot.bound_voice_id)}`
      return `跟随默认：${this.voiceName(bot.effective_voice_id)}`
    },
    fmtSize(n) {
      if (!n) return '0 KB'
      return n > 1024 * 1024 ? (n / 1024 / 1024).toFixed(1) + ' MB' : Math.ceil(n / 1024) + ' KB'
    },
    async load() {
      try {
        const [voicesRes, settingRes, botsRes, cacheRes] = await Promise.all([
          api.ttsVoices(), api.ttsGetSetting(), api.botList(), api.ttsCacheStats()
        ])
        if (voicesRes.data) {
          this.packs = voicesRes.data.map(p => ({ ...p, langTag: this.langTag(p) }))
        }
        if (settingRes.data) this.currentVoiceId = settingRes.data.voice_id
        if (botsRes.data) this.bots = botsRes.data.map(b => ({ ...b, bound_voice_id: '', effective_voice_id: '' }))
        if (cacheRes.data) this.cacheInfo = cacheRes.data
      } catch (e) { /* request 层已提示 */ }
      // 伙伴语音状态（单独拉，避免阻塞首屏）
      this.bots.forEach(async bot => {
        try {
          const res = await api.ttsGetBotVoice(bot.id)
          if (res.data) {
            bot.bound_voice_id = res.data.bound_voice_id || ''
            bot.effective_voice_id = res.data.effective_voice_id || ''
            this.bots = [...this.bots]
          }
        } catch (e) { /* 忽略 */ }
      })
    },
    async chooseVoice(pack, t) {
      try {
        await api.ttsSetSetting(t.voice_id)
        this.currentVoiceId = t.voice_id
        uni.showToast({ title: `已切换：${t.name}`, icon: 'none' })
      } catch (e) { /* request 层已提示 */ }
    },
    async preview(pack) {
      if (this.previewing) return
      this.previewing = true
      try {
        // 关键：必须带上“当前语音包”的默认音色，否则会用用户默认音色（如中文音色念韩文）
        const timbres = pack.timbres || []
        const timbre = timbres.find(t => t.is_default) || timbres[0] || {}
        const ok = await aiSpeak.speak(pack.sample_text || '你好，这是语音试听。', {
          voiceId: timbre.voice_id || '',
          fallback: false
        })
        if (!ok) uni.showToast({ title: '试听失败，请检查后端 TTS 服务', icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '试听失败，请检查后端 TTS 服务', icon: 'none' })
      }
      this.previewing = false
    },
    async onPickBotVoice(bot, idx) {
      // voiceOptions 与 packs 平铺顺序一致
      let flat = []
      this.packs.forEach(p => p.timbres.forEach(t => flat.push(t.voice_id)))
      const voiceId = flat[idx]
      if (!voiceId) return
      try {
        const res = await api.ttsBindBotVoice(bot.id, voiceId)
        if (res.data) {
          bot.bound_voice_id = res.data.bound_voice_id || voiceId
          bot.effective_voice_id = res.data.effective_voice_id || voiceId
          this.bots = [...this.bots]
          uni.showToast({ title: '已绑定专属语音', icon: 'success' })
        }
      } catch (e) { /* request 层已提示 */ }
    },
    async unbindBot(bot) {
      try {
        await api.ttsUnbindBotVoice(bot.id)
        bot.bound_voice_id = ''
        const res = await api.ttsGetBotVoice(bot.id)
        if (res.data) bot.effective_voice_id = res.data.effective_voice_id || ''
        this.bots = [...this.bots]
        uni.showToast({ title: '已解绑，回退默认语音', icon: 'none' })
      } catch (e) { /* request 层已提示 */ }
    },
    async clearCache() {
      try {
        const res = await api.ttsCacheClear()
        uni.showToast({ title: `已清理 ${res.data ? res.data.cleared : 0} 条缓存`, icon: 'none' })
        const c = await api.ttsCacheStats()
        if (c.data) this.cacheInfo = c.data
      } catch (e) { /* request 层已提示 */ }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间 */
.xt-page.xt-s58 .body {
  padding-bottom: 24px;
}

/* 设计稿 .prob .pr 依赖 b 元素，改用同名 class 补等价规则 */
.xt-page.xt-s58 .prob .pr .b {
  margin-left: auto;
  font-size: 8.5px;
  color: #22302A;
}
</style>
