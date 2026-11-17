<template>
  <view class="xt-page xt-s14">
    <view class="body">
      <view class="medit">
        <view class="mhead">
          <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
          <span class="mk">MINDFUL · {{ isPracticing ? formatTime(practiceTimer) : '正念' }}</span>
        </view>

        <view class="medit-title">{{ currentAudio && currentAudio.title && currentAudio.title !== '快速练习' ? currentAudio.title : '把呼吸放慢一点' }}</view>

        <view class="breath" @click="isPracticing ? endPractice(false) : startQuickPractice(chosenMinutes)">{{ isPracticing ? breathText.replace('...', '') : '开始' }}</view>
        <view class="steps"><span>吸气 4 秒</span><span>停留 4 秒</span><span>呼气 6 秒</span></view>

        <view class="choose">
          <template v-if="!isPracticing">
            <span
              v-for="m in quickTimes"
              :key="m"
              :class="{ on: chosenMinutes === m }"
              @click="startQuickPractice(m)"
            >{{ m }} 分钟</span>
          </template>
          <template v-else>
            <span @click="endPractice(false)">提前结束</span>
            <span
              v-if="practiceTimer <= practiceDuration * 60 - minPracticeSeconds"
              class="on"
              @click="endPractice(true)"
            >完成练习</span>
          </template>
        </view>

        <view class="quote">
          <view>{{ currentGuide || '她也在呼吸。' }}</view>
          <view v-if="!currentGuide">你不需要做得很好，只需要在这里。</view>
        </view>
      </view>
    </view>

    <!-- 练习完成弹窗 -->
    <view class="modal-overlay" v-if="showCompleteDialog" @click="showCompleteDialog = false">
      <view class="complete-dialog" @click.stop>
        <text class="dialog-title">练习完成 🎉</text>
        <text class="complete-duration">本次练习 {{ practiceDuration }} 分钟</text>

        <!-- 情绪对比 -->
        <emotion-compare
          v-model="emotionCompare"
          @change="onEmotionChange"
        />

        <!-- 练习笔记 -->
        <view class="dialog-section">
          <text class="dialog-label">练习感受（可选）</text>
          <textarea
            class="dialog-textarea"
            v-model="practiceNote"
            placeholder="记录本次练习的感受..."
            maxlength="200"
          />
        </view>

        <view class="dialog-actions">
          <view class="dialog-btn cancel" @click="showCompleteDialog = false">
            <text>跳过</text>
          </view>
          <view class="dialog-btn confirm" @click="savePracticeRecord">
            <text>保存记录</text>
          </view>
        </view>
      </view>
    </view>

    <!-- AI 正念疏导弹窗 -->
    <ai-interaction-modal
      :visible="showAIModal"
      type="reminder"
      :characterId="$store.state.aiConfig.avatarType || 'linxi'"
      :message="aiModalMessage"
      :loading="aiModalLoading"
      @close="closeAIModal"
      @chat="goChatFromModal"
      @primary="closeAIModal"
    />
  </view>
</template>

<script>
import { getCharacterById, getRandomPhrase } from '@/common/ai-characters'
import meditationApi from '@/api/meditation'
import mock from '@/common/mock'
import EmotionCompare from '@/components/emotion-compare.vue'
import AIInteractionModal from '@/components/ai-interaction-modal/ai-interaction-modal.vue'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import aiService from '@/common/ai-service.js'
// ↓↓↓ 模块2 新增：呼吸检测的 TTS 语音提醒 ↓↓↓
import aiSpeak from '@/common/ai-speak.js'
// ↓↓↓ 新增 ↓↓↓ 正念音频 URL 统一走 request.js 的 toStaticUrl（H5 用相对路径过 vite 代理）
import { toStaticUrl } from '@/common/request'

// ↓↓↓ 新增 ↓↓↓ 后端 audio_type 与页面 tab 的 key 不一致（breath / meditation / anxiety），
// 不映射的话「呼吸放松 / 正念冥想 / 焦虑缓解」三个 tab 永远筛不出内容。
const CATEGORY_ALIAS = {
  breath: 'breathing',
  body_scan: 'body_scan',
  meditation: 'mindfulness',
  anxiety: 'anxiety_relief',
  sleep_aid: 'sleep_aid'
}

export default {
  components: { EmotionCompare, AIInteractionModal, XtIcon },
  data() {
    return {
      activeTab: 'practice',
      tabs: [
        { key: 'practice', label: '练习', icon: '🧘' },
        { key: 'plan', label: '计划', icon: '📋' },
        { key: 'knowledge', label: '知识库', icon: '📚' }
      ],
      // 统计
      stats: {},
      // 音频
      audioList: [],
      selectedCategory: 'all',
      categories: mock.meditationCategories || {},
      // 练习
      isPracticing: false,
      practiceTimer: 0,
      practiceDuration: 0,
      breathText: '准备开始',
      currentGuide: '',
      currentAudio: null,
      // ↓↓↓ 新增 ↓↓↓ 练习中的音频上下文（音床是 30 秒循环，需循环播放铺满整个练习时长）
      practiceAudio: null,
      audioErrorNotified: false,
      minPracticeSeconds: 30,
      practiceInterval: null,
      breathPhase: 0,
      // ↓↓↓ 时间戳驱动的精确计时 ↓↓↓
      _practiceEndTime: 0,          // 练习结束的绝对时间戳(Date.now)
      _breathPhaseStartTime: 0,     // 当前呼吸阶段的开始时间戳
      _breathPhaseIndex: 0,         // 当前呼吸阶段索引(与 breathPhase 解耦)
      quickTimes: [3, 5, 10, 15],
      // 完成弹窗
      showCompleteDialog: false,
      emotionCompare: { before: null, after: null },
      practiceNote: '',
      // 计划
      currentPlan: null,
      showPlanDialog: false,
      newPlan: {
        name: '',
        target_days: 7,
        target_duration: 10,
        preferred_category: null
      },
      // 历史
      historyList: [],
      // 知识库
      knowledgeList: [],
      expandedKnowledge: null,
      // AI正念弹窗
      showAIModal: false,
      aiModalMessage: '',
      aiModalLoading: false,
      // ↓↓↓ 模块2 新增：呼吸节奏检测（麦克风 AudioContext） ↓↓↓
      // 单一状态源：总开关 → 从 localStorage 读（user_settings 持久化）
      // 任何异常都自动降级为纯动画引导，不打断练习
      breathMonitorEnabled: false,       // 总开关
      breathMonitorActive: false,        // 正在监听
      breathMonitorUnavailable: false,   // 麦克风不可用降级标志
      _breathAudioCtx: null,             // AudioContext
      _breathAnalyser: null,             // AnalyserNode
      _breathStream: null,               // MediaStream
      _breathDetectTimer: null,          // 采样定时器
      _breathAnomalyCooldown: {},        // 异常冷却 { type: lastTriggeredAt }
      _breathInhaleSamples: [],          // 吸气时长采样（秒）
      _breathExhaleSamples: [],          // 呼气时长采样
      _breathApneaSamples: [],           // 憋气时长采样
      _breathLastPeakTime: 0,            // 上次呼吸峰值时间
      _breathCurrentPhase: 'idle',       // idle / inhale / exhale / apnea
      // ↑↑↑ 模块2 新增结束 ↑↑↑
    }
  },
  computed: {
    aiName() {
      return this.$store.state.aiConfig.name || '林夕'
    },
    aiAvatar() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      return character?.avatar || '🌿'
    },
    currentCharacter() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      return getCharacterById(characterId)
    },
    filteredAudios() {
      if (this.selectedCategory === 'all') return this.audioList
      // 后端暂无独立的 sleep_aid 资源，这里复用最舒缓的几条环境音床，
      // 避免「助眠安神」tab 点进去是空的（无声音）。
      if (this.selectedCategory === 'sleep_aid') {
        const picks = ['med_30', 'anxiety_25', 'med_15']
        return picks
          .map(k => this.audioList.find(a => String(a.audio_url || '').indexOf(k) >= 0))
          .filter(Boolean)
      }
      return this.audioList.filter(a => a.category === this.selectedCategory)
    },
    chosenMinutes() {
      return this.practiceDuration || 10
    }
  },
  onLoad() {
    this.loadAll()
  },
  onShow() {
    this.loadStats()
  },
  onUnmounted() {
    this.stopPracticeTimers()
    // ↓↓↓ 模块2 双保险：页面卸载时确保呼吸检测彻底销毁 ↓↓↓
    this.destroyBreathMonitor()
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    async loadAll() {
      this.loadAudios()
      this.loadStats()
      this.loadPlan()
      this.loadHistory()
      this.loadKnowledge()
    },
    // ↓↓↓ 新增 ↓↓↓ 后端 /mindfulness/audio/list 返回的是**裸数组**（不是 {list:[]}），
    // 且字段叫 duration_min / audio_type，页面模板用的是 duration_minutes / category，
    // 不转换的话列表永远是空、时长和分类显示成 undefined。这里统一归一化。
    normalizeAudio(a) {
      if (!a) return a
      return {
        ...a,
        category: CATEGORY_ALIAS[a.audio_type] || a.category || 'mindfulness',
        duration_minutes: a.duration_minutes != null ? a.duration_minutes : (a.duration_min || 0),
        play_count: a.play_count || 0,
        is_premium: !!a.is_premium
      }
    },
    // ↓↓↓ 新增 ↓↓↓ 练习记录同样对齐：后端是 session_type / duration_min / session_date
    normalizeRecord(r) {
      if (!r) return r
      return {
        ...r,
        category: r.category || r.session_type || 'meditation',
        duration_minutes: r.duration_minutes != null ? r.duration_minutes : (r.duration_min || 0),
        practiced_at: r.practiced_at || r.session_date || ''
      }
    },
    async loadAudios() {
      try {
        const res = await meditationApi.getAudios()
        const raw = Array.isArray(res?.data) ? res.data : (res?.data?.list || [])
        this.audioList = raw.map(a => this.normalizeAudio(a))
        this.$store.commit('setMeditationAudios', this.audioList)
      } catch (e) {
        console.error('加载音频列表失败', e)
      }
    },
    async loadStats() {
      try {
        const res = await meditationApi.getStats()
        this.stats = res.data || {}
      } catch (e) {
        console.error('加载统计失败', e)
      }
    },
    async loadPlan() {
      try {
        const res = await meditationApi.getPlan()
        // ↓↓↓ 修复 ↓↓↓ /mindfulness/plan/list 返回的是**计划数组**，页面当单个对象用，
        // 于是 currentPlan.id 是 undefined，保存记录时 updatePlan(undefined) 必然失败。
        // 这里取第一条（有启用态的优先）。
        const list = Array.isArray(res?.data) ? res.data : []
        this.currentPlan = list.find(p => p && p.active) || list[0] || null
        this.$store.commit('setMeditationPlan', this.currentPlan)
      } catch (e) {
        console.error('加载计划失败', e)
      }
    },
    async loadHistory() {
      try {
        const res = await meditationApi.getRecords({ page: 1, page_size: 20 })
        // ↓↓↓ 修复 ↓↓↓ 后端字段名是 session_type/duration_min/session_date，模板读的是
        // category/duration_minutes/practiced_at，不归一化就全是 undefined
        const rows = res?.data?.list || []
        this.historyList = rows.map(r => this.normalizeRecord(r))
        this.$store.commit('setMeditationRecords', this.historyList)
      } catch (e) {
        console.error('加载历史失败', e)
      }
    },
    async loadKnowledge() {
      try {
        const res = await meditationApi.getKnowledge()
        this.knowledgeList = res.data || []
      } catch (e) {
        console.error('加载知识库失败', e)
      }
    },

    // === 练习控制 ===
    startAudioPractice(audio) {
      this.currentAudio = audio
      this.startPractice(audio.duration_minutes, audio.category, audio.id)
    },
    startQuickPractice(minutes) {
      // 原来 currentAudio = null，快速练习全程静音；这里挂一条中性的棕噪音音床
      this.currentAudio = {
        id: 0,
        title: '快速练习',
        audio_url: '/uploads/audio/med_30min.wav',
        category: 'mindfulness',
        duration_minutes: minutes
      }
      this.startPractice(minutes, 'mindfulness', null)
    },
    startPractice(minutes, category, audioId) {
      this.isPracticing = true
      this.practiceDuration = minutes
      this.practiceTimer = minutes * 60
      this.breathText = '吸气...'
      this.breathPhase = 0

      // ↓↓↓ 时间戳驱动：记录结束时刻，而非依赖 tick 次数递减 ↓↓↓
      // 浏览器后台/休眠时 setInterval 会被严重节流，但 Date.now() 始终真实
      this._practiceEndTime = Date.now() + minutes * 60 * 1000

      // 初始引导语
      this.updateGuide('start')

      // ↓↓↓ 新增 ↓↓↓ 播放正念音床（原来整页只走了呼吸圈+倒计时，全程静音）
      this.startPracticeAudio()

      // 呼吸引导循环
      this.startBreathingCycle()

      // AI引导定时更新
      this.startGuideUpdates(minutes, category)

      // ↓↓↓ 模块2 新增：启动呼吸节奏检测（如果总开关开着） ↓↓↓
      this.initBreathMonitor()

      // ↓↓↓ 精确倒计时：每次 tick 都用 Date.now() 重新算剩余时间 ↓↓↓
      // 后台被节流唤醒后，第一次 tick 就能直接跳到正确的剩余秒数
      // 同时在同一个 tick 里驱动呼吸阶段切换和引导语更新（全部时间戳驱动）
      this._guidePhaseEndTimes = {
        breathing: Date.now() + 10000,                            // 10秒后切到呼吸引导
        mid:       Date.now() + Math.min(minutes * 30 * 1000, 120000), // 中段
        end:       Date.now() + Math.max(minutes * 60 * 1000 - 30000, 60000) // 最后30秒
      }
      this._guidePhaseFired = { breathing: false, mid: false, end: false }

      this.practiceInterval = setInterval(() => {
        // 1. 倒计时（时间戳驱动，后台唤醒立即纠正）
        const remaining = Math.max(
          0,
          Math.round((this._practiceEndTime - Date.now()) / 1000)
        )
        this.practiceTimer = remaining

        // 2. 呼吸阶段切换（时间戳驱动，可能一次跳过多个阶段）
        this._tickBreathPhase()

        // 3. 引导语阶段切换（时间戳驱动）
        this._tickGuidePhase()

        if (remaining <= 0) {
          this.endPractice(true)
        }
      }, 1000)
    },
    startBreathingCycle() {
      // ↓↓↓ 时间戳驱动的呼吸阶段切换 ↓↓↓
      // 不再用 setTimeout 循环（后台节流后会乱掉），而是记录阶段开始时间戳
      // 在 practiceInterval 的 tick 里检查是否需要切换阶段
      this._breathPhases = [
        { text: '吸气...', duration: 4000 },
        { text: '保持...', duration: 4000 },
        { text: '呼气...', duration: 6000 },
        { text: '放松...', duration: 2000 }
      ]
      this._breathPhaseIndex = 0
      this._breathPhaseStartTime = Date.now()
      this.breathText = this._breathPhases[0].text
    },
    // ↓↓↓ 与倒计时共用 tick 的呼吸阶段检查 ↓↓↓
    // 由 practiceInterval 每秒调用一次，也能被节流唤醒后立即纠正
    _tickBreathPhase() {
      if (!this.isPracticing || !this._breathPhases) return
      const now = Date.now()
      while (true) {
        const phase = this._breathPhases[this._breathPhaseIndex]
        if (now - this._breathPhaseStartTime >= phase.duration) {
          // 跳到下一阶段（后台唤醒后可能一次跳过多个阶段）
          this._breathPhaseIndex = (this._breathPhaseIndex + 1) % this._breathPhases.length
          this._breathPhaseStartTime += phase.duration
          this.breathPhase++
          this.breathText = this._breathPhases[this._breathPhaseIndex].text
        } else {
          break
        }
      }
    },
    startGuideUpdates(minutes, category) {
      // 引导语阶段切换已改为 practiceInterval tick 中的时间戳驱动
      // 这里保留空方法体以兼容原有调用（实际逻辑在 _tickGuidePhase 中）
    },
    // ↓↓↓ 引导语阶段切换（时间戳驱动，与倒计时/呼吸阶段共用 tick） ↓↓↓
    _tickGuidePhase() {
      if (!this.isPracticing) return
      const now = Date.now()
      const phases = ['breathing', 'mid', 'end']
      for (const phase of phases) {
        if (!this._guidePhaseFired[phase] && now >= this._guidePhaseEndTimes[phase]) {
          this._guidePhaseFired[phase] = true
          this.updateGuide(phase)
        }
      }
    },
    async updateGuide(phase) {
      try {
        const elapsed = this.practiceDuration * 60 - this.practiceTimer
        const res = await meditationApi.getGuide({
          phase,
          elapsed_minutes: Math.floor(elapsed / 60),
          total_minutes: this.practiceDuration
        })
        if (res.data?.guide_text) {
          this.currentGuide = res.data.guide_text
        }
      } catch (e) {
        // 降级：使用角色语录
        this.currentGuide = getRandomPhrase(this.$store.state.aiConfig.avatarType || 'linxi', 'comfort')
      }
    },
    endPractice(completed) {
      this.stopPracticeTimers()
      this.isPracticing = false
      this.breathText = '准备开始'
      this.currentGuide = ''

      if (completed) {
        this.showCompleteDialog = true
      } else {
        // 提前结束也保存记录
        const elapsed = this.practiceDuration * 60 - this.practiceTimer
        if (elapsed >= this.minPracticeSeconds) {
          this.showCompleteDialog = true
        } else {
          uni.showToast({ title: '练习已结束', icon: 'none' })
        }
      }
    },
    stopPracticeTimers() {
      if (this.practiceInterval) {
        clearInterval(this.practiceInterval)
        this.practiceInterval = null
      }
      // 清理所有时间戳驱动的状态（旧的 guideInterval/呼吸循环已废弃）
      this._practiceEndTime = 0
      this._breathPhaseStartTime = 0
      this._breathPhaseIndex = 0
      this._breathPhases = null
      this._guidePhaseEndTimes = null
      this._guidePhaseFired = null
      // ↓↓↓ 新增 ↓↓↓ 练习结束/提前结束时一并停掉音床，否则会一直在后台响
      this.stopPracticeAudio()
      // ↓↓↓ 模块2 新增：练习结束时彻底销毁呼吸检测，避免后台继续采样耗电 ↓↓↓
      this.destroyBreathMonitor()
    },
    // ↓↓↓ 新增 ↓↓↓ 练习音床播放
    // 背景：audio_resources.audio_url 原来指向 /static/audio/*.mp3，文件从不存在 →
    // 页面全程静音。现已由 /uploads/audio/*.wav 提供 30 秒无缝循环音床，
    // 这里的职责是：选了具体音频就循环播它，播不出来就静音继续（不打断练习）。
    startPracticeAudio() {
      const raw = this.currentAudio && this.currentAudio.audio_url
      if (!raw) return  // 快速练习没有选具体音频，保持静音
      try {
        this.stopPracticeAudio()
        const ctx = uni.createInnerAudioContext()
        ctx.src = toStaticUrl(raw)
        ctx.loop = true            // 音床只有 30 秒，循环才能铺满 5~30 分钟的练习
        ctx.volume = 0.6           // 留点余量，别盖过 AI 引导
        ctx.onError((err) => {
          console.error('正念音床播放失败', err)
          if (!this.audioErrorNotified) {
            this.audioErrorNotified = true
            uni.showToast({ title: '背景音加载失败，可继续练习', icon: 'none' })
          }
          this.stopPracticeAudio() // 降级：静音继续练习
        })
        ctx.play()
        this.practiceAudio = ctx
      } catch (e) {
        console.error('创建音频上下文失败', e)
        this.practiceAudio = null
      }
    },
    stopPracticeAudio() {
      if (!this.practiceAudio) return
      try {
        this.practiceAudio.stop()
        this.practiceAudio.destroy()
      } catch (e) {
        console.error('停止音床失败', e)
      }
      this.practiceAudio = null
    },

    // ============ 模块2：呼吸节奏检测（AudioContext + AnalyserNode） ============
    // 单一状态源：breathMonitorEnabled（总开关） → 从 localStorage 读
    // 任何异常自动降级为纯动画引导，不打断练习
    async initBreathMonitor() {
      // 1. 总开关是否开
      try {
        this.breathMonitorEnabled = !!uni.getStorageSync('meditation_breath_monitor')
      } catch (e) {
        this.breathMonitorEnabled = false
      }
      if (!this.breathMonitorEnabled) return

      // 2. 浏览器/平台支持检查
      const hasMediaDevices = typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia
      const hasAudioCtx = typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined'
      if (!hasMediaDevices || !hasAudioCtx) {
        this.breathMonitorUnavailable = true
        return
      }

      // 3. 请求麦克风权限
      let stream = null
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
      } catch (e) {
        // 用户拒绝权限 → 静默降级，继续正常练习
        this.breathMonitorUnavailable = true
        return
      }
      if (!stream) { this.breathMonitorUnavailable = true; return }

      // 4. 创建 AudioContext + AnalyserNode
      try {
        const AC = typeof AudioContext !== 'undefined' ? AudioContext : webkitAudioContext
        const ctx = new AC()
        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 1024
        analyser.smoothingTimeConstant = 0.5
        source.connect(analyser)

        this._breathAudioCtx = ctx
        this._breathAnalyser = analyser
        this._breathStream = stream
        this._breathMonitorActive = true
        this._breathLastPeakTime = performance.now() / 1000
        this._breathCurrentPhase = 'idle'

        // 5. 启动 300ms 采样循环
        this._breathDetectTimer = setInterval(() => {
          this._breathTick()
        }, 300)
      } catch (e) {
        this.breathMonitorUnavailable = true
        this.destroyBreathMonitor()
      }
    },
    destroyBreathMonitor() {
      // 停采样定时器
      if (this._breathDetectTimer) {
        clearInterval(this._breathDetectTimer)
        this._breathDetectTimer = null
      }
      // 关 MediaStream track
      if (this._breathStream) {
        try { this._breathStream.getTracks().forEach(t => t.stop()) } catch (e) {}
        this._breathStream = null
      }
      // 关 AudioContext
      if (this._breathAudioCtx) {
        try { this._breathAudioCtx.close() } catch (e) {}
        this._breathAudioCtx = null
      }
      this._breathAnalyser = null
      this.breathMonitorActive = false
      // 保留采样数据给 savePracticeRecord 用（breathAnomalies 汇总）
    },
    _breathTick() {
      // 采样音量包络（RMS）→ 检测吸气/呼气相位转换
      try {
        const analyser = this._breathAnalyser
        if (!analyser) return
        const buf = new Uint8Array(analyser.frequencyBinCount)
        analyser.getByteTimeDomainData(buf)

        // 算 RMS（音量包络）
        let sum = 0
        for (let i = 0; i < buf.length; i++) {
          const v = (buf[i] - 128) / 128.0
          sum += v * v
        }
        const rms = Math.sqrt(sum / buf.length)
        const now = performance.now() / 1000
        const dt = now - this._breathLastPeakTime

        // 音量阈值：大于 0.03 视为活跃呼吸（吸气或呼气声）
        const isActive = rms > 0.03

        if (!isActive) {
          // 静音区 → 可能是呼气结束（进入憋气）
          if (this._breathCurrentPhase === 'inhale' && dt > 0.5) {
            // 吸气刚结束 → 记录吸气时长
            this._breathInhaleSamples.push(dt)
            this._breathLastPeakTime = now
            this._breathCurrentPhase = 'apnea'
          } else if (this._breathCurrentPhase === 'exhale' && dt > 0.5) {
            // 呼气刚结束 → 记录呼气时长
            this._breathExhaleSamples.push(dt)
            this._breathLastPeakTime = now
            this._breathCurrentPhase = 'apnea'
          } else if (this._breathCurrentPhase === 'apnea' && dt > 12) {
            // 憋气超过 12 秒 → 记录
            this._breathApneaSamples.push(dt)
          }
          return
        }

        // 活跃呼吸 → 判断相位
        if (this._breathCurrentPhase === 'idle') {
          this._breathCurrentPhase = 'inhale'
          this._breathLastPeakTime = now
        } else if (this._breathCurrentPhase === 'apnea') {
          // 憋气结束 → 新吸气开始
          this._breathCurrentPhase = 'inhale'
          this._breathLastPeakTime = now
        } else if (this._breathCurrentPhase === 'inhale' && dt > 3 && rms < 0.05) {
          // 吸气后音量下降 → 进入呼气
          this._breathInhaleSamples.push(dt)
          this._breathCurrentPhase = 'exhale'
          this._breathLastPeakTime = now
        } else if (this._breathCurrentPhase === 'exhale' && dt > 3 && rms > 0.04) {
          // 呼气后音量回升 → 进入下一轮吸气
          this._breathExhaleSamples.push(dt)
          this._breathCurrentPhase = 'inhale'
          this._breathLastPeakTime = now
        }

        // 实时异常检测（滑动时间窗 20 秒内的平均值）
        this._checkBreathAnomalies()
      } catch (e) {
        // 采样异常静默，不打断练习
      }
    },
    _checkBreathAnomalies() {
      const now = Date.now()
      const windowStart = this._breathInhaleSamples.length > 5
        ? Math.max(0, this._breathInhaleSamples.length - 10) : 0

      const avgInhale = this._breathInhaleSamples.slice(windowStart).reduce((a, b) => a + b, 0) / Math.max(1, this._breathInhaleSamples.slice(windowStart).length)
      const avgExhale = this._breathExhaleSamples.slice(windowStart).reduce((a, b) => a + b, 0) / Math.max(1, this._breathExhaleSamples.slice(windowStart).length)
      const maxApnea = Math.max(0, ...this._breathApneaSamples)

      const cooldown = this._breathAnomalyCooldown

      // 吸气过快：avgInhale < 2.5s 且已有 3 个样本
      if (this._breathInhaleSamples.length >= 3 && avgInhale > 0 && avgInhale < 2.5) {
        if (!cooldown.inhale_fast || now - cooldown.inhale_fast > 20000) {
          cooldown.inhale_fast = now
          this._speakBreathRemind('慢一点吸气，感受空气慢慢充盈肺部～')
        }
      }

      // 呼气过快：avgExhale < 3s
      if (this._breathExhaleSamples.length >= 3 && avgExhale > 0 && avgExhale < 3) {
        if (!cooldown.exhale_fast || now - cooldown.exhale_fast > 20000) {
          cooldown.exhale_fast = now
          this._speakBreathRemind('慢慢呼气，把紧张都放出去～')
        }
      }

      // 憋气过长：maxApnea > 10s
      if (maxApnea > 10) {
        if (!cooldown.apnea_long || now - cooldown.apnea_long > 20000) {
          cooldown.apnea_long = now
          this._speakBreathRemind('慢慢呼出来，别憋着，没关系的～')
        }
      }
    },
    _speakBreathRemind(text) {
      // 复用项目已有 ai-speak（全语音包），失败静默降级
      try {
        aiSpeak.speak(text).catch(() => {})
      } catch (e) {}
    },
    _computeBreathRate() {
      // 练习结束时算平均呼吸频率（次/分钟）
      const totalBreaths = this._breathInhaleSamples.length
      if (totalBreaths === 0) return null
      const avgCycle = (
        this._breathInhaleSamples.reduce((a, b) => a + b, 0) +
        this._breathExhaleSamples.reduce((a, b) => a + b, 0)
      ) / Math.max(1, totalBreaths)
      if (avgCycle <= 0) return null
      return Math.round(60 / avgCycle * 10) / 10
    },
    _summarizeBreathAnomalies() {
      // 把检测到的异常类型汇总成 JSON 字符串，存进 emotion_records
      const types = []
      if (this._breathInhaleSamples.some(t => t < 2.5)) types.push('inhale_fast')
      if (this._breathExhaleSamples.some(t => t < 3)) types.push('exhale_fast')
      if (this._breathApneaSamples.some(t => t > 10)) types.push('apnea_long')
      if (types.length === 0) return null
      try { return JSON.stringify({ types, total_breaths: this._breathInhaleSamples.length }, ensure_ascii = false) } catch (e) { return null }
    },
    // ↑↑↑ 模块2 结束 ↑↑↑

    // === 保存练习记录 ===
    async savePracticeRecord() {
      const elapsed = this.practiceDuration * 60 - this.practiceTimer
      const actualMinutes = Math.max(1, Math.round(elapsed / 60))

      try {
        // 字段对齐后端 MindfulnessSessionCreate schema：
        // session_type / duration_min / audio_id / emotion_before / emotion_after / completed
        const session_type = this.currentAudio?.category || 'meditation'
        const data = {
          audio_id: this.currentAudio?.id || 0,
          session_type,
          duration_min: actualMinutes,
          completed: 1,
          emotion_before: this.emotionCompare.before || '',
          emotion_after: this.emotionCompare.after || '',
          // ↓↓↓ 模块2 新增：呼吸节奏采集结果（可选，没有检测就为 null） ↓↓↓
          breath_rate: this._computeBreathRate(),
          breath_anomalies: this._summarizeBreathAnomalies(),
          // ↑↑↑ 模块2 新增结束 ↑↑↑
        }

        await meditationApi.createRecord(data)

        // 更新计划进度：updatePlan 已降级为 PUT /mindfulness/plan/toggle/{id}，
        // 仅切换激活状态，不再传 completed_today/duration_minutes 等参数。
        if (this.currentPlan) {
          await meditationApi.updatePlan(this.currentPlan.id)
        }

        // 添加到本地Store
        this.$store.commit('addMeditationRecord', {
          name: this.currentAudio?.title || '快速练习',
          time: actualMinutes,
          icon: this.getCategoryIcon(session_type),
          date: new Date().toISOString()
        })

        // 行走成长地图：正念冥想增加 0.5 步
        this.$store.commit('addWalkStep', {
          steps: 0.5,
          type: 'meditation',
          description: this.currentAudio?.title || `${actualMinutes}分钟正念练习`
        })

        // 检查是否有"冥想静心"习惯可同步打卡
        this.syncMeditationHabit()

        uni.showToast({ title: '练习记录已保存', icon: 'success' })
        
        // AI 正念疏导联动
        this.triggerMeditationAI(this.currentAudio?.title || '正念练习')
        
        this.showCompleteDialog = false
        this.resetPracticeState()
        this.loadStats()
        this.loadPlan()
        this.loadHistory()
      } catch (e) {
        console.error('保存练习记录失败', e)
        uni.showToast({ title: '保存失败，请重试', icon: 'none' })
      }
    },
    syncMeditationHabit() {
      // 尝试同步到"冥想静心"习惯打卡
      const habits = this.$store.state.todayHabits
      const meditateHabit = habits.find(h => h.type === 'meditate' && !h.checked)
      if (meditateHabit) {
        this.$store.commit('updateHabitCheckIn', { habitId: meditateHabit.id, checked: true })
        this.$store.commit('addWalkStep', { steps: 1, type: 'habit', description: meditateHabit.name })
        uni.showToast({ title: '已自动完成"冥想静心"打卡', icon: 'none', duration: 2000 })
      }
    },
    resetPracticeState() {
      this.currentAudio = null
      this.practiceTimer = 0
      this.practiceDuration = 0
      this.emotionCompare = { before: null, after: null }
      this.practiceNote = ''
    },
    // AI 正念疏导联动
    async triggerMeditationAI(meditationName) {
      this.aiModalLoading = true
      this.showAIModal = true
      
      try {
        const response = await aiService.onMeditationComplete(meditationName)
        this.aiModalMessage = response || '练习完成，愿你心中平静~'
      } catch (e) {
        console.error('AI正念联动失败:', e)
        this.aiModalMessage = '深呼吸，你做得很好~'
      } finally {
        this.aiModalLoading = false
      }
    },
    closeAIModal() {
      this.showAIModal = false
      this.aiModalMessage = ''
    },
    goChatFromModal() {
      this.closeAIModal()
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    onEmotionChange(val) {
      this.emotionCompare = val
    },

    // === 创建计划 ===
    async createPlan() {
      if (!this.newPlan.name.trim()) {
        uni.showToast({ title: '请输入计划名称', icon: 'none' })
        return
      }
      try {
        await meditationApi.createPlan(this.newPlan)
        uni.showToast({ title: '计划创建成功', icon: 'success' })
        this.showPlanDialog = false
        this.newPlan = { name: '', target_days: 7, target_duration: 10, preferred_category: null }
        this.loadPlan()
      } catch (e) {
        console.error('创建计划失败', e)
        uni.showToast({ title: '创建失败', icon: 'none' })
      }
    },

    // === 知识库 ===
    toggleKnowledge(id) {
      this.expandedKnowledge = this.expandedKnowledge === id ? null : id
    },

    // === 工具方法 ===
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    },
    formatDateTime(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr.replace(' ', 'T'))
      return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    },
    formatPlayCount(count) {
      if (!count) return '0'
      if (count >= 10000) return (count / 10000).toFixed(1) + '万'
      if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
      return count.toString()
    },
    getCategoryIcon(category) {
      const cat = this.categories[category]
      return cat?.icon || '🧘'
    },
    getCategoryColor(category) {
      const colors = {
        breathing: '#E3F2FD',
        body_scan: '#F3E5F5',
        mindfulness: '#E8F5E9',
        anxiety_relief: '#FFF3E0',
        sleep_aid: '#ECEFF1'
      }
      return colors[category] || '#E8F5E9'
    },
    getCategoryLabel(category) {
      return this.categories[category]?.label || '正念练习'
    },
    getEmotionLabel(emotion) {
      const labels = {
        happy: '😊开心', excited: '🤩兴奋', calm: '😌平静',
        sad: '😢难过', angry: '😠生气', tired: '😴疲惫'
      }
      return labels[emotion] || '—'
    }
  }
}
</script>

<style lang="scss" scoped>
/* 满屏深色容器含内边距，避免 100% 高度溢出裁切底部文案 */
.xt-page.xt-s14 .medit {
  box-sizing: border-box;
}

/* 设计稿 h3 元素选择器在模板中替换为 view，这里补同效果标题样式 */
.xt-page.xt-s14 .medit-title {
  position: relative;
  margin-top: 8px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: .2px;
}

/* 练习完成弹窗：设计稿未覆盖的既有交互，沿用原样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx 32rpx;
  background: rgba(14, 22, 18, 0.64);
  box-sizing: border-box;
}

.complete-dialog {
  width: 100%;
  max-height: 82vh;
  padding: 40rpx 32rpx 32rpx;
  box-sizing: border-box;
  border-radius: 34rpx;
  background: var(--v7-card);
  color: #26332C;
  overflow-y: auto;
}

.dialog-title {
  display: block;
  font-size: 33rpx;
  font-weight: 800;
  color: #26332C;
}

.complete-duration {
  display: block;
  margin-top: 12rpx;
  margin-bottom: 22rpx;
  font-size: 23rpx;
  color: #8B978D;
}

.dialog-section {
  margin-top: 26rpx;
}

.dialog-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 23rpx;
  font-weight: 700;
  color: #3C5248;
}

.dialog-textarea {
  width: 100%;
  height: 180rpx;
  padding: 20rpx;
  box-sizing: border-box;
  border-radius: 18rpx;
  background: #F5F2E9;
  font-size: 24rpx;
  line-height: 1.6;
  color: #26332C;
}

.dialog-actions {
  display: flex;
  margin-top: 32rpx;
}

.dialog-btn {
  flex: 1;
  height: 90rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.dialog-btn + .dialog-btn {
  margin-left: 16rpx;
}

.dialog-btn.cancel {
  background: #F0EEE5;
  color: #78837A;
}

.dialog-btn.confirm {
  background: linear-gradient(135deg, #3C6B55, var(--v7-green));
  color: #F8F3E7;
  font-weight: 700;
  box-shadow: 0 18rpx 34rpx -22rpx rgba(46, 86, 67, 0.8);
}
</style>