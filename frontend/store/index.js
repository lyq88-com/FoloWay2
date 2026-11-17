import { createStore } from 'vuex'
import { getCurrentStage, checkStageUnlock, isAllCompleted } from '@/common/walk-map-config.js'
import habitAIApi from '@/api/habit-ai.js'

const STORAGE_KEY = 'ahp_user_state'

export default createStore({
  state: {
    token: '',
    // 登录用户名（与用户可改的昵称 nickname 区分，作为性格测评完成标记的稳定键）
    username: '',
    userInfo: {
      nickname: '',
      avatar: '',
      phone: '',
      registerTime: '',
      signature: ''
    },
    habits: [],
    todayHabits: [],
    aiConfig: {
      avatarType: 'linxi',
      name: '林夕',
      interactionFrequency: 'medium'
    },
    chatMessages: [],
    // 流式输出状态
    streamingMessage: '',
    streamingActive: false,
    // 离线消息缓存
    offlineMessages: [],
    // 危机干预弹窗状态
    crisisAlert: null,
    streakDays: 0,
    badges: [],
    settings: {
      notificationEnabled: true,
      remindTime: '08:00',
      ttsEnabled: true,
      habitRemindEnabled: false,
      habitRemindTime: '19:00',
      lastHabitRemindDate: ''
    },
    aiStatus: 'normal',
    personalityResult: null,
    quizCompleted: false,
    bondLevels: {},
    // AI伙伴好感度（对标循途关系系统）：宝物使用/打卡互动累积，影响AI回复语气
    affection: { value: 0 },
    emotionRecords: [],
    emotionTags: [],  // 用户历史使用过的触发标签（按使用频次排序）
    meditationRecords: [],
    meditationAudios: [],   // 正念音频列表缓存
    meditationPlan: null,   // 当前练习计划
    growthArchives: [],     // 成长档案列表缓存
    checkinDiaries: {},     // 打卡日记 { habitId: [diaries] }
    achievementRewards: {}, // 成就奖励 { habitId: [rewards] }
    currentTheme: 'light',
    customBackground: null,
    // 自定义AI伙伴列表
    customCharacters: [],
    // 环球行走成长地图
    walkMap: {
      totalSteps: 0,           // 累计步数（含情绪/正念的小步）
      totalCheckins: 0,        // 累计习惯打卡次数（用于关卡阈值判定）
      lastActiveDate: '',      // 最后活跃日期 YYYY-MM-DD
      walkHistory: [],         // 行走历史 [{ date, time, type, description, emotion, stageId, stepCount }]
      unlockedEnding: false,   // 是否全部通关
      lastStageId: 0           // 上次所在关卡（用于检测解锁）
    },
    // === 阶段J: 习惯-AI全链路融合 ===
    habitAI: {
      currentStyle: 'gentle',          // 当前对话风格 gentle/analytical/humorous/calm
      currentCharacterId: 'linxi',     // 当前AI角色ID
      memories: [],                    // AI记忆列表缓存
      achievements: [],                // 成就列表缓存
      checkinPopup: null,              // 打卡弹窗数据 { dialogue, emotion_tag, continuous_day, habit_name }
      achievementCelebration: null,    // 成就庆祝弹窗数据 { milestone, title, ai_dialogue }
      sessionType: 'chat',             // 当前会话类型 chat/checkin_trigger/emotion_guide/mindfulness
      lastCheckinResult: null,         // 最近一次打卡AI联动结果
    }
  },

  mutations: {
    initFromStorage(state) {
      try {
        const saved = uni.getStorageSync(STORAGE_KEY)
        if (saved) {
          const parsed = JSON.parse(saved)
          // 确保 walkMap 存在且字段完整
          if (!parsed.walkMap) {
            parsed.walkMap = {
              totalSteps: 0, totalCheckins: 0, lastActiveDate: '',
              walkHistory: [], unlockedEnding: false, lastStageId: 0
            }
          }
          // 确保好感度字段存在（兼容旧版本本地缓存）
          if (!parsed.affection || typeof parsed.affection.value !== 'number') {
            parsed.affection = { value: 0 }
          }
          Object.assign(state, parsed)
        }
      } catch (e) {
        console.error('恢复状态失败', e)
      }
    },
    setToken(state, token) {
      state.token = token
      this.commit('saveToStorage')
    },
    // 设置登录用户名（仅登录成功时调用，profile 编辑不会改它）
    setUsername(state, username) {
      state.username = username || ''
      this.commit('saveToStorage')
    },
    clearToken(state) {
      state.token = ''
      this.commit('saveToStorage')
    },
    setUserInfo(state, info) {
      state.userInfo = { ...state.userInfo, ...info }
      this.commit('saveToStorage')
    },
    setHabits(state, habits) {
      state.habits = habits
      this.commit('saveToStorage')
    },
    setTodayHabits(state, habits) {
      state.todayHabits = habits
      this.commit('saveToStorage')
    },
    updateHabitCheckIn(state, { habitId, checked }) {
      const habit = state.todayHabits.find(h => h.id === habitId)
      if (habit) {
        habit.checked = checked
        habit.checkInTime = checked ? new Date().toISOString() : null
      }
      this.commit('saveToStorage')
    },
    setAiConfig(state, config) {
      state.aiConfig = { ...state.aiConfig, ...config }
      this.commit('saveToStorage')
    },
    addChatMessage(state, msg) {
      state.chatMessages.push(msg)
      if (state.chatMessages.length > 200) {
        state.chatMessages = state.chatMessages.slice(-200)
      }
      this.commit('saveToStorage')
    },
    clearChatMessages(state) {
      state.chatMessages = []
      this.commit('saveToStorage')
    },
    /**
     * 整体替换聊天消息列表（用于消息撤回等就地更新场景）
     * @param {Array} messages
     */
    setChatMessages(state, messages) {
      state.chatMessages = Array.isArray(messages) ? messages : []
      if (state.chatMessages.length > 200) {
        state.chatMessages = state.chatMessages.slice(-200)
      }
      this.commit('saveToStorage')
    },
    /**
     * 标记某条AI消息为已撤回（消息撤回模拟）
     * @param {Object} payload - { index, recalled } index 为 chatMessages 下标
     */
    recallChatMessage(state, { index, recalled }) {
      if (state.chatMessages[index]) {
        state.chatMessages[index] = { ...state.chatMessages[index], recalled: !!recalled }
        this.commit('saveToStorage')
      }
    },
    /**
     * 增加AI伙伴好感度（宝物使用/打卡互动调用）
     * @param {Number} delta - 增减值，范围 [0, 500] 封顶
     */
    addAffection(state, delta) {
      if (typeof delta !== 'number' || isNaN(delta)) return
      if (!state.affection) state.affection = { value: 0 }
      state.affection = {
        value: Math.max(0, Math.min(500, (state.affection.value || 0) + delta))
      }
      this.commit('saveToStorage')
    },
    setAffection(state, value) {
      state.affection = { value: Math.max(0, Math.min(500, value || 0)) }
      this.commit('saveToStorage')
    },
    // === 流式输出 ===
    setStreamingActive(state, active) {
      state.streamingActive = active
      if (!active) {
        state.streamingMessage = ''
      }
    },
    appendStreamingChunk(state, chunk) {
      state.streamingMessage += chunk
    },
    setStreamingMessage(state, msg) {
      state.streamingMessage = msg
    },
    resetStreaming(state) {
      state.streamingMessage = ''
      state.streamingActive = false
    },
    // === 危机干预 ===
    setCrisisAlert(state, alert) {
      state.crisisAlert = alert
    },
    // === 离线消息缓存 ===
    addOfflineMessage(state, msg) {
      if (!state.offlineMessages) state.offlineMessages = []
      state.offlineMessages.push(msg)
      this.commit('saveToStorage')
    },
    clearOfflineMessages(state) {
      state.offlineMessages = []
      this.commit('saveToStorage')
    },
    setStreakDays(state, days) {
      state.streakDays = days
      this.commit('saveToStorage')
    },
    setBadges(state, badges) {
      state.badges = badges
      this.commit('saveToStorage')
    },
    addBadge(state, badge) {
      if (!state.badges.find(b => b.id === badge.id)) {
        state.badges.push(badge)
        this.commit('saveToStorage')
      }
    },
    setSettings(state, settings) {
      state.settings = { ...state.settings, ...settings }
      this.commit('saveToStorage')
    },
    setAiStatus(state, status) {
      state.aiStatus = status
    },
    setPersonalityResult(state, result) {
      state.personalityResult = result
      this.commit('saveToStorage')
    },
    setQuizCompleted(state, completed) {
      state.quizCompleted = completed
      this.commit('saveToStorage')
    },
    setBondLevel(state, { characterId, level }) {
      state.bondLevels = { ...state.bondLevels, [characterId]: level }
      this.commit('saveToStorage')
    },
    addBondExp(state, { characterId, exp }) {
      const current = state.bondLevels[characterId] || { level: 1, exp: 0 }
      const newExp = current.exp + exp
      const newLevel = Math.floor(newExp / 100) + 1
      state.bondLevels = {
        ...state.bondLevels,
        [characterId]: { level: newLevel, exp: newExp % 100 }
      }
      this.commit('saveToStorage')
    },
    addEmotionRecord(state, record) {
      state.emotionRecords.push(record)
      if (state.emotionRecords.length > 365) {
        state.emotionRecords = state.emotionRecords.slice(-365)
      }
      this.commit('saveToStorage')
    },
    /**
     * 批量设置情绪记录（从API加载后调用，替换本地缓存）
     * @param {Array} records - 从后端 /emotion/list 返回的记录数组
     */
    setEmotionRecords(state, records) {
      state.emotionRecords = Array.isArray(records) ? records : []
      if (state.emotionRecords.length > 365) {
        state.emotionRecords = state.emotionRecords.slice(-365)
      }
      this.commit('saveToStorage')
    },
    /**
     * 删除单条情绪记录
     * @param {Number} recordId
     */
    removeEmotionRecord(state, recordId) {
      state.emotionRecords = state.emotionRecords.filter(r => r.id !== recordId)
      this.commit('saveToStorage')
    },
    /**
     * 记忆用户历史使用过的触发标签（按使用频次排序）
     * 已存在的标签会移到数组最前（最近使用），最多保留 20 个
     * @param {String|Array} tags - 单个标签字符串或标签数组
     */
    addEmotionTag(state, tags) {
      const tagList = Array.isArray(tags) ? tags : [tags]
      const validTags = tagList.filter(t => t && typeof t === 'string' && t.trim())
      if (validTags.length === 0) return
      if (!state.emotionTags) state.emotionTags = []
      validTags.forEach(tag => {
        const trimmed = tag.trim()
        // 先移除已存在项（去重）
        state.emotionTags = state.emotionTags.filter(t => t !== trimmed)
        // 添加到最前（最近使用优先）
        state.emotionTags.unshift(trimmed)
      })
      // 限制最多 20 个
      if (state.emotionTags.length > 20) {
        state.emotionTags = state.emotionTags.slice(0, 20)
      }
      this.commit('saveToStorage')
    },
    addMeditationRecord(state, record) {
      state.meditationRecords.push(record)
      if (state.meditationRecords.length > 100) {
        state.meditationRecords = state.meditationRecords.slice(-100)
      }
      this.commit('saveToStorage')
    },
    /**
     * 批量设置正念练习记录（从API加载后调用）
     * @param {Array} records
     */
    setMeditationRecords(state, records) {
      state.meditationRecords = Array.isArray(records) ? records : []
      if (state.meditationRecords.length > 100) {
        state.meditationRecords = state.meditationRecords.slice(-100)
      }
      this.commit('saveToStorage')
    },
    /**
     * 设置正念音频列表缓存
     * @param {Array} audios
     */
    setMeditationAudios(state, audios) {
      state.meditationAudios = Array.isArray(audios) ? audios : []
      this.commit('saveToStorage')
    },
    /**
     * 设置当前练习计划
     * @param {Object|null} plan
     */
    setMeditationPlan(state, plan) {
      state.meditationPlan = plan
      this.commit('saveToStorage')
    },
    /**
     * 设置成长档案列表
     * @param {Array} archives
     */
    setGrowthArchives(state, archives) {
      state.growthArchives = Array.isArray(archives) ? archives : []
      this.commit('saveToStorage')
    },
    /**
     * 添加或更新单条成长报告到档案列表
     * @param {Object} report
     */
    addGrowthReport(state, report) {
      if (!state.growthArchives) state.growthArchives = []
      const idx = state.growthArchives.findIndex(a => a.id === report.id)
      if (idx >= 0) {
        state.growthArchives.splice(idx, 1, report)
      } else {
        state.growthArchives.unshift(report)
      }
      this.commit('saveToStorage')
    },
    // === 打卡日记 ===
    /**
     * 设置某习惯的打卡日记列表
     * @param {Object} payload - { habitId, diaries }
     */
    setCheckinDiaries(state, { habitId, diaries }) {
      if (!state.checkinDiaries) state.checkinDiaries = {}
      state.checkinDiaries = { ...state.checkinDiaries, [habitId]: Array.isArray(diaries) ? diaries : [] }
      this.commit('saveToStorage')
    },
    /**
     * 添加单条打卡日记
     * @param {Object} diary - { habit_id, content, mood, ai_encouragement, ... }
     */
    addCheckinDiary(state, diary) {
      if (!state.checkinDiaries) state.checkinDiaries = {}
      const hid = diary.habit_id || 0
      if (!state.checkinDiaries[hid]) {
        state.checkinDiaries[hid] = []
      }
      state.checkinDiaries[hid].unshift(diary)
      if (state.checkinDiaries[hid].length > 50) {
        state.checkinDiaries[hid] = state.checkinDiaries[hid].slice(0, 50)
      }
      this.commit('saveToStorage')
    },
    // === 成就奖励 ===
    /**
     * 设置某习惯的成就奖励列表
     * @param {Object} payload - { habitId, rewards }
     */
    setAchievementRewards(state, { habitId, rewards }) {
      if (!state.achievementRewards) state.achievementRewards = {}
      state.achievementRewards = { ...state.achievementRewards, [habitId]: Array.isArray(rewards) ? rewards : [] }
      this.commit('saveToStorage')
    },
    /**
     * 添加或更新单条成就奖励
     * @param {Object} reward - { habit_id, reward_type, trigger_streak, is_unlocked, ... }
     */
    addAchievementReward(state, reward) {
      if (!state.achievementRewards) state.achievementRewards = {}
      const hid = reward.habit_id || 0
      if (!state.achievementRewards[hid]) {
        state.achievementRewards[hid] = []
      }
      const idx = state.achievementRewards[hid].findIndex(r => r.trigger_streak === reward.trigger_streak)
      if (idx >= 0) {
        state.achievementRewards[hid].splice(idx, 1, reward)
      } else {
        state.achievementRewards[hid].push(reward)
      }
      this.commit('saveToStorage')
    },
    setCurrentTheme(state, theme) {
      state.currentTheme = theme
      this.commit('saveToStorage')
    },
    setCustomBackground(state, background) {
      state.customBackground = background
      this.commit('saveToStorage')
    },
    // === 自定义AI伙伴 ===
    addCustomCharacter(state, character) {
      if (!state.customCharacters) state.customCharacters = []
      // 如果已存在同ID则更新
      const idx = state.customCharacters.findIndex(c => c.id === character.id)
      if (idx >= 0) {
        state.customCharacters.splice(idx, 1, character)
      } else {
        state.customCharacters.push(character)
      }
      this.commit('saveToStorage')
    },
    removeCustomCharacter(state, characterId) {
      if (!state.customCharacters) return
      state.customCharacters = state.customCharacters.filter(c => c.id !== characterId)
      this.commit('saveToStorage')
    },
    // === 环球行走成长地图 ===
    /**
     * 用服务端累计打卡数校准本地计数（只增不减，避免覆盖未同步的新打卡）
     * 修复：老用户本地 walkMap 从 0 开始，导致行走地图/到站数长期显示 0
     */
    setWalkTotalCheckins(state, value) {
      const v = Math.max(0, parseInt(value, 10) || 0)
      if (v > (state.walkMap.totalCheckins || 0)) {
        state.walkMap.totalCheckins = v
        state.walkMap.lastStageId = getCurrentStage(v).id
        this.commit('saveToStorage')
      }
    },
    /**
     * 添加行走步数
     * @param {Number} steps - 步数（习惯=1, 情绪=0.3, 正念=0.5）
     * @param {String} type - 'habit' | 'emotion' | 'meditation'
     * @param {String} description - 描述（习惯名称/情绪标签/正念名称）
     * @param {String} emotion - 情绪数据（可选）
     */
    addWalkStep(state, { steps, type, description, emotion }) {
      const now = new Date()
      const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

      // 更新步数
      state.walkMap.totalSteps += steps

      // 习惯打卡才增加 totalCheckins（用于关卡阈值）
      let stageId = state.walkMap.lastStageId
      if (type === 'habit') {
        const prevCheckins = state.walkMap.totalCheckins
        state.walkMap.totalCheckins += 1

        // 检测关卡解锁
        const unlockResult = checkStageUnlock(prevCheckins, state.walkMap.totalCheckins)
        if (unlockResult.unlocked) {
          state.walkMap.lastStageId = unlockResult.newStage.id
          stageId = unlockResult.newStage.id
        }
        // 检测全部通关
        if (isAllCompleted(state.walkMap.totalCheckins) && !state.walkMap.unlockedEnding) {
          state.walkMap.unlockedEnding = true
        }
      }

      // 获取当前关卡ID
      if (stageId === state.walkMap.lastStageId) {
        stageId = getCurrentStage(state.walkMap.totalCheckins).id
        state.walkMap.lastStageId = stageId
      }

      // 记录行走历史
      state.walkMap.walkHistory.push({
        date: dateStr,
        time: timeStr,
        type,
        description,
        emotion: emotion || '',
        stageId,
        stepCount: state.walkMap.totalSteps,
        timestamp: now.getTime()
      })

      // 限制历史记录长度（最多1000条）
      if (state.walkMap.walkHistory.length > 1000) {
        state.walkMap.walkHistory = state.walkMap.walkHistory.slice(-1000)
      }

      // 更新最后活跃日期
      state.walkMap.lastActiveDate = dateStr

      this.commit('saveToStorage')
    },
    /**
     * 撤销行走步数（取消打卡时调用）
     */
    removeWalkStep(state, { type }) {
      if (type === 'habit' && state.walkMap.totalCheckins > 0) {
        state.walkMap.totalCheckins -= 1
      }
      // 步数回退
      const stepMap = { habit: 1, emotion: 0.3, meditation: 0.5 }
      const step = stepMap[type] || 0
      state.walkMap.totalSteps = Math.max(0, state.walkMap.totalSteps - step)
      // 移除最后一条同类型记录
      const history = state.walkMap.walkHistory
      for (let i = history.length - 1; i >= 0; i--) {
        if (history[i].type === type) {
          history.splice(i, 1)
          break
        }
      }
      this.commit('saveToStorage')
    },
    setWalkMap(state, walkMap) {
      state.walkMap = { ...state.walkMap, ...walkMap }
      this.commit('saveToStorage')
    },
    // === 阶段J: 习惯-AI联动 ===
    setHabitAIStyle(state, { style, characterId }) {
      if (style) state.habitAI.currentStyle = style
      if (characterId) state.habitAI.currentCharacterId = characterId
      this.commit('saveToStorage')
    },
    setSessionType(state, sessionType) {
      state.habitAI.sessionType = sessionType
      this.commit('saveToStorage')
    },
    setHabitMemories(state, memories) {
      state.habitAI.memories = Array.isArray(memories) ? memories : []
      this.commit('saveToStorage')
    },
    addHabitMemory(state, memory) {
      if (!state.habitAI.memories) state.habitAI.memories = []
      state.habitAI.memories.unshift(memory)
      if (state.habitAI.memories.length > 100) {
        state.habitAI.memories = state.habitAI.memories.slice(0, 100)
      }
      this.commit('saveToStorage')
    },
    setHabitAchievements(state, achievements) {
      state.habitAI.achievements = Array.isArray(achievements) ? achievements : []
      this.commit('saveToStorage')
    },
    addHabitAchievement(state, achievement) {
      if (!state.habitAI.achievements) state.habitAI.achievements = []
      const idx = state.habitAI.achievements.findIndex(a => a.id === achievement.id)
      if (idx >= 0) {
        state.habitAI.achievements.splice(idx, 1, achievement)
      } else {
        state.habitAI.achievements.unshift(achievement)
      }
      this.commit('saveToStorage')
    },
    setCheckinPopup(state, data) {
      state.habitAI.checkinPopup = data
    },
    setAchievementCelebration(state, data) {
      state.habitAI.achievementCelebration = data
    },
    setLastCheckinResult(state, result) {
      state.habitAI.lastCheckinResult = result
      this.commit('saveToStorage')
    },
    clearCheckinPopup(state) {
      state.habitAI.checkinPopup = null
    },
    clearAchievementCelebration(state) {
      state.habitAI.achievementCelebration = null
    },
    saveToStorage(state) {
      try {
        uni.setStorageSync(STORAGE_KEY, JSON.stringify(state))
      } catch (e) {
        console.error('保存状态失败', e)
      }
    },
    resetState(state) {
      state.token = ''
      state.username = ''
      state.userInfo = { nickname: '', avatar: '', phone: '', registerTime: '', signature: '' }
      state.habits = []
      state.todayHabits = []
      state.chatMessages = []
      state.streamingMessage = ''
      state.streamingActive = false
      state.offlineMessages = []
      state.crisisAlert = null
      state.streakDays = 0
      state.badges = []
      state.personalityResult = null
      state.quizCompleted = false
      state.bondLevels = {}
      // 修复：重置好感度，避免切换账号后残留上一账号数据
      state.affection = { value: 0 }
      state.emotionRecords = []
      state.emotionTags = []
      state.meditationRecords = []
      state.meditationAudios = []
      state.meditationPlan = null
      state.growthArchives = []
      state.checkinDiaries = {}
      state.achievementRewards = {}
      state.currentTheme = 'light'
      state.customBackground = null
      state.customCharacters = []
      // 修复：重置行走地图，避免退出登录后残留步数与关卡
      state.walkMap = {
        totalSteps: 0, totalCheckins: 0, lastActiveDate: '',
        walkHistory: [], unlockedEnding: false, lastStageId: 0
      }
      // 修复：重置AI配置与全局设置
      state.aiConfig = { avatarType: 'linxi', name: '林夕', interactionFrequency: 'medium' }
      state.settings = {
        notificationEnabled: true, remindTime: '08:00', ttsEnabled: true,
        habitRemindEnabled: false, habitRemindTime: '19:00', lastHabitRemindDate: ''
      }
      state.aiStatus = 'normal'
      state.habitAI = {
        currentStyle: 'gentle',
        currentCharacterId: 'linxi',
        memories: [],
        achievements: [],
        checkinPopup: null,
        achievementCelebration: null,
        sessionType: 'chat',
        lastCheckinResult: null,
      }
      uni.removeStorageSync(STORAGE_KEY)
      // 同步清掉"已选伙伴"记录，避免退出后下个账号继承上一个账号的伙伴
      try {
        uni.removeStorageSync('ai_partner_id')
        uni.removeStorageSync('ai_partner_snapshot')
      } catch (e) { /* 静默 */ }
    }
  },

  getters: {
    isLoggedIn: (state) => !!state.token,
    todayCompletedCount: (state) => state.todayHabits.filter(h => h.checked).length,
    todayCompletionRate: (state) => {
      if (!state.todayHabits.length) return 0
      return Math.round(state.todayHabits.filter(h => h.checked).length / state.todayHabits.length * 100)
    },
    incompleteHabits: (state) => state.todayHabits.filter(h => !h.checked),
    completedHabits: (state) => state.todayHabits.filter(h => h.checked),
    currentBondLevel: (state) => (characterId) => {
      return state.bondLevels[characterId] || { level: 1, exp: 0 }
    },
    // === 好感度系统（对标循途关系体系） ===
    affectionValue: (state) => (state.affection ? state.affection.value : 0),
    // 好感度阶段：0-99 初识 / 100-199 熟悉 / 200-299 伙伴 / 300-399 挚友 / 400+ 知己
    affectionTier: (state) => {
      const v = state.affection ? state.affection.value : 0
      return Math.min(4, Math.floor(v / 100))
    },
    affectionTierName: (state) => {
      const v = state.affection ? state.affection.value : 0
      const tier = Math.min(4, Math.floor(v / 100))
      return ['初识', '熟悉', '伙伴', '挚友', '知己'][tier]
    },
    // 当前阶段内的进度（0-100，用于进度条）
    affectionProgress: (state) => {
      const v = state.affection ? state.affection.value : 0
      if (v >= 400) return 100
      return Math.round(v % 100)
    },
    recentEmotions: (state) => {
      return state.emotionRecords.slice(-7).reverse()
    },
    emotionCount: (state) => {
      return state.emotionRecords.length
    },
    // === 环球行走成长地图 Getters ===
    currentStage: (state) => {
      return getCurrentStage(state.walkMap.totalCheckins)
    },
    stageProgress: (state) => {
      const stage = getCurrentStage(state.walkMap.totalCheckins)
      const { threshold, nextThreshold } = stage
      if (nextThreshold === null || nextThreshold === Infinity) return 100
      return Math.min(100, Math.round((state.walkMap.totalCheckins - threshold) / (nextThreshold - threshold) * 100))
    },
    walkerPosition: (state) => {
      return state.walkMap.totalCheckins
    },
    walkInactivityDays: (state) => {
      if (!state.walkMap.lastActiveDate) return 0
      const last = new Date(state.walkMap.lastActiveDate + 'T00:00:00')
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      return Math.floor((today - last) / (1000 * 60 * 60 * 24))
    },
    walkHistory: (state) => {
      return state.walkMap.walkHistory
    },
    totalCheckins: (state) => {
      return state.walkMap.totalCheckins
    },
    unlockedEnding: (state) => {
      return state.walkMap.unlockedEnding
    },
    // === 成长档案 ===
    growthArchiveList: (state) => {
      return state.growthArchives
    },
    archiveCount: (state) => {
      return state.growthArchives ? state.growthArchives.length : 0
    },
    // === 打卡日记 ===
    checkinDiariesByHabit: (state) => (habitId) => {
      return (state.checkinDiaries && state.checkinDiaries[habitId]) || []
    },
    // === 成就奖励 ===
    achievementsByHabit: (state) => (habitId) => {
      return (state.achievementRewards && state.achievementRewards[habitId]) || []
    },
    unlockedAchievementCount: (state) => {
      if (!state.achievementRewards) return 0
      return Object.values(state.achievementRewards).flat().filter(a => a.is_unlocked).length
    },
    // === 阶段J: 习惯-AI联动 ===
    habitAIStyle: (state) => state.habitAI.currentStyle,
    habitAICharacter: (state) => state.habitAI.currentCharacterId,
    habitMemories: (state) => state.habitAI.memories || [],
    habitAchievements: (state) => state.habitAI.achievements || [],
    checkinPopupData: (state) => state.habitAI.checkinPopup,
    achievementCelebrationData: (state) => state.habitAI.achievementCelebration,
    currentSessionType: (state) => state.habitAI.sessionType,
    lastCheckinResult: (state) => state.habitAI.lastCheckinResult,
  },

  actions: {
    // === 阶段J: 习惯-AI联动 Actions ===
    async checkinTrigger({ commit, state }, { habitId, note, emotion, characterId }) {
      const habitAI = habitAIApi
      try {
        const res = await habitAI.checkinTrigger(habitId, note, emotion, characterId || state.habitAI.currentCharacterId)
        if (res.code === 200 && res.data) {
          const data = res.data
          // 设置打卡弹窗数据
          commit('setCheckinPopup', {
            dialogue: data.dialogue,
            emotion_tag: data.emotion_tag,
            continuous_day: data.continuous_day,
            habit_type: data.habit_type,
            style: data.style,
          })
          // 如果有成就，设置成就庆祝弹窗
          if (data.achievement) {
            commit('setAchievementCelebration', data.achievement)
            commit('addHabitAchievement', {
              id: Date.now(),
              habit_id: habitId,
              milestone: data.achievement.milestone,
              ai_dialogue: data.achievement.ai_dialogue,
              unlocked_at: new Date().toLocaleString('zh-CN'),
            })
          }
          // 保存最近结果
          commit('setLastCheckinResult', data)
          // 添加行走步数
          commit('addWalkStep', { steps: 1, type: 'habit', description: '习惯打卡', emotion })
          return data
        }
        return null
      } catch (e) {
        console.error('checkinTrigger error', e)
        return null
      }
    },

    async loadHabitAchievements({ commit }, habitId = 0) {
      const habitAI = habitAIApi
      try {
        const res = await habitAI.getAchievements(habitId)
        if (res.code === 200) {
          commit('setHabitAchievements', res.data)
          return res.data
        }
      } catch (e) {
        console.error('loadHabitAchievements error', e)
      }
      return []
    },

    async loadHabitMemories({ commit }, { memoryType, limit } = {}) {
      const habitAI = habitAIApi
      try {
        const res = await habitAI.getMemories(memoryType || '', limit || 20)
        if (res.code === 200) {
          commit('setHabitMemories', res.data)
          return res.data
        }
      } catch (e) {
        console.error('loadHabitMemories error', e)
      }
      return []
    },

    async updateCustomRemind({ commit }, { habitId, customRemindText, aiStyle }) {
      const habitAI = habitAIApi
      try {
        const res = await habitAI.updateCustomRemind(habitId, customRemindText, aiStyle)
        if (res.code === 200) {
          commit('setHabitAIStyle', { style: aiStyle })
          return res.data
        }
      } catch (e) {
        console.error('updateCustomRemind error', e)
      }
      return null
    },

    async generateDiary({ commit }, { habitId, note, emotion, dateStr }) {
      const habitAI = habitAIApi
      try {
        const res = await habitAI.generateDiary(habitId, note, emotion, dateStr)
        if (res.code === 200) {
          return res.data
        }
      } catch (e) {
        console.error('generateDiary error', e)
      }
      return null
    },
  }
})
