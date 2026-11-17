/**
 * ai-test-data.js
 * AI 联动测试数据注入工具
 * 
 * 用于本地开发测试时快速填充模拟数据：
 * - 打卡历史数据 (习惯列表、连续打卡天数)
 * - 情绪记录 (最近7天情绪轨迹)
 * - 环球行走地图进度
 * - AI 角色设定
 * 
 * 使用方式：
 *   import { injectMockData } from '@/common/ai-test-data'
 *   injectMockData(store)
 */

// ==================== 模拟打卡数据 ====================

const today = new Date()
const todayStr = today.toISOString().split('T')[0]

const mockHabits = [
  {
    id: 101,
    type: 'read',
    name: '阅读30分钟',
    icon: '📚',
    color: '#FFD93D',
    target: '阅读30分钟',
    difficulty: 'medium',
    multiplier: 1.5,
    reminderTime: '21:00',
    streak: 7,
    completed: true,
    completedDate: todayStr,
    checkInTime: new Date().toISOString()
  },
  {
    id: 102,
    type: 'sport',
    name: '运动30分钟',
    icon: '🏃',
    color: '#FF6B6B',
    target: '运动30分钟',
    difficulty: 'medium',
    multiplier: 1.5,
    reminderTime: '18:00',
    streak: 5,
    completed: true,
    completedDate: todayStr,
    checkInTime: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 103,
    type: 'meditate',
    name: '冥想10分钟',
    icon: '🧘',
    color: '#BA68C8',
    target: '冥想10分钟',
    difficulty: 'easy',
    multiplier: 1.0,
    reminderTime: '22:00',
    streak: 3,
    completed: false,
    completedDate: null
  },
  {
    id: 104,
    type: 'sleep',
    name: '23点前睡觉',
    icon: '😴',
    color: '#7986CB',
    target: '23:00前入睡',
    difficulty: 'hard',
    multiplier: 2.0,
    reminderTime: '22:30',
    streak: 2,
    completed: false,
    completedDate: null
  },
  {
    id: 105,
    type: 'morning',
    name: '早起一杯水',
    icon: '💧',
    color: '#4FC3F7',
    target: '喝200ml温水',
    difficulty: 'easy',
    multiplier: 1.0,
    reminderTime: '07:30',
    streak: 10,
    completed: true,
    completedDate: todayStr,
    checkInTime: new Date(Date.now() - 36000000).toISOString()
  }
]

// ==================== 模拟情绪记录 ====================

const mockEmotionRecords = [
  {
    id: 1,
    date: todayStr,
    emotion: 'happy',
    emotionLabel: '开心',
    intensity: 4,
    tags: ['成就感', '完成目标'],
    note: '今天一口气完成了3个打卡，超有成就感！',
    createdAt: new Date(Date.now() - 7200000).toISOString()
  },
  {
    id: 2,
    date: new Date(Date.now() - 86400000).toISOString().split('T')[0],
    emotion: 'anxious',
    emotionLabel: '焦虑',
    intensity: 3,
    tags: ['工作压力', ' deadline'],
    note: '项目快到截止日期了，还有很多没做完...',
    createdAt: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: 3,
    date: new Date(Date.now() - 86400000 * 2).toISOString().split('T')[0],
    emotion: 'tired',
    emotionLabel: '疲惫',
    intensity: 4,
    tags: ['睡眠不足', '加班'],
    note: '连续加班3天了，身体有点吃不消',
    createdAt: new Date(Date.now() - 86400000 * 2).toISOString()
  },
  {
    id: 4,
    date: new Date(Date.now() - 86400000 * 3).toISOString().split('T')[0],
    emotion: 'sad',
    emotionLabel: '难过',
    intensity: 3,
    tags: ['被批评', '自我怀疑'],
    note: '今天被领导说了一顿，感觉自己好没用...',
    createdAt: new Date(Date.now() - 86400000 * 3).toISOString()
  },
  {
    id: 5,
    date: new Date(Date.now() - 86400000 * 4).toISOString().split('T')[0],
    emotion: 'neutral',
    emotionLabel: '平静',
    intensity: 2,
    tags: ['冥想', '散步'],
    note: '冥想之后感觉好多了，明天继续加油',
    createdAt: new Date(Date.now() - 86400000 * 4).toISOString()
  },
  {
    id: 6,
    date: new Date(Date.now() - 86400000 * 5).toISOString().split('T')[0],
    emotion: 'happy',
    emotionLabel: '满足',
    intensity: 5,
    tags: ['家人陪伴', '美食'],
    note: '和家人一起吃了顿大餐，幸福满满的一天',
    createdAt: new Date(Date.now() - 86400000 * 5).toISOString()
  },
  {
    id: 7,
    date: new Date(Date.now() - 86400000 * 6).toISOString().split('T')[0],
    emotion: 'angry',
    emotionLabel: '烦躁',
    intensity: 3,
    tags: ['交通堵塞', '迟到'],
    note: '早上堵车迟到了，一整天心情都不好',
    createdAt: new Date(Date.now() - 86400000 * 6).toISOString()
  }
]

// ==================== 模拟行走地图 ====================

const mockWalkMap = {
  totalSteps: 1280,
  totalCheckins: 18,
  lastActiveDate: todayStr,
  walkHistory: [
    { date: todayStr, time: '08:00', type: 'habit', description: '早起打卡', emotion: 'happy', stageId: 2, stepCount: 100 },
    { date: todayStr, time: '12:00', type: 'emotion', description: '记录开心情绪', emotion: 'happy', stageId: 2, stepCount: 20 },
    { date: todayStr, time: '19:00', type: 'habit', description: '运动打卡', emotion: 'energetic', stageId: 2, stepCount: 150 },
    { date: new Date(Date.now() - 86400000).toISOString().split('T')[0], time: '21:00', type: 'meditation', description: '10分钟正念', emotion: 'peaceful', stageId: 2, stepCount: 50 }
  ],
  currentStage: 2,
  unlockedEnding: false,
  lastStageId: 2
}

// ==================== 主注入函数 ====================

/**
 * 注入全套模拟测试数据
 * @param {Object} store - Vuex store 实例
 * @param {Object} options - 可选配置
 * @param {Boolean} options.includeHabits - 是否注入习惯数据 (默认 true)
 * @param {Boolean} options.includeEmotions - 是否注入情绪记录 (默认 true)
 * @param {Boolean} options.includeWalkMap - 是否注入行走地图 (默认 true)
 * @param {Boolean} options.includeUserInfo - 是否注入用户信息 (默认 true)
 * @param {Boolean} options.includeAIChat - 是否注入 AI 聊天记录 (默认 true)
 */
function injectMockData(store, options = {}) {
  const {
    includeHabits = true,
    includeEmotions = true,
    includeWalkMap = true,
    includeUserInfo = true,
    includeAIChat = true
  } = options
  
  console.log('[AI Test] 开始注入模拟测试数据...')
  
  try {
    // 1. 用户信息
    if (includeUserInfo) {
      store.commit('setUserInfo', {
        nickname: '测试用户',
        avatar: '',
        phone: '138****8888',
        registerTime: '2026-07-01 10:30:00'
      })
      console.log('[AI Test] ✓ 用户信息已注入')
    }
    
    // 2. 习惯数据
    if (includeHabits) {
      store.commit('setHabits', mockHabits)
      store.commit('setTodayHabits', mockHabits)
      
      // 设置连续打卡天数
      const maxStreak = Math.max(...mockHabits.map(h => h.streak))
      store.commit('setStreakDays', maxStreak)
      console.log(`[AI Test] ✓ 习惯数据已注入 (${mockHabits.length} 个习惯, 最长连续 ${maxStreak} 天)`)
    }
    
    // 3. 情绪记录
    if (includeEmotions) {
      store.commit('setEmotionRecords', mockEmotionRecords)
      console.log(`[AI Test] ✓ 情绪记录已注入 (${mockEmotionRecords.length} 条记录)`)
    }
    
    // 4. 行走地图
    if (includeWalkMap) {
      store.commit('setWalkMap', mockWalkMap)
      console.log(`[AI Test] ✓ 行走地图已注入 (关卡 ${mockWalkMap.currentStage}, 步数 ${mockWalkMap.totalSteps})`)
    }
    
    // 5. AI 角色配置
    store.commit('setAiConfig', {
      avatarType: 'linxi',
      name: '林夕',
      interactionFrequency: 'medium'
    })
    console.log('[AI Test] ✓ AI 角色配置已注入 (林夕)')
    
    // 6. 示例聊天记录
    if (includeAIChat) {
      const mockChatMessages = [
        {
          role: 'assistant',
          content: `嗨~ 我是林夕。看到你已经连续打卡${store.state.streakDays || 7}天了呢，真的超厉害！🌸`,
          time: new Date(Date.now() - 3600000).toISOString()
        },
        {
          role: 'user',
          content: '今天工作压力好大，有点焦虑',
          time: new Date(Date.now() - 3000000).toISOString()
        },
        {
          role: 'assistant',
          content: `焦虑的时候深呼吸，你已经在面对它了。连续${store.state.streakDays || 7}天的打卡习惯，会给你力量的。要不要跟我聊聊是什么让你焦虑呢？`,
          time: new Date(Date.now() - 2400000).toISOString()
        }
      ]
      
      mockChatMessages.forEach(msg => {
        store.commit('addChatMessage', msg)
      })
      console.log(`[AI Test] ✓ AI 聊天记录已注入 (${mockChatMessages.length} 条消息)`)
    }
    
    console.log('[AI Test] ✅ 模拟数据注入完成！')
    console.log('[AI Test] 现在可以测试以下场景：')
    console.log('  · AI 情绪识别 (发送"我好难过"/"太开心了")')
    console.log('  · 打卡成功联动 (完成一个打卡)')
    console.log('  · 打卡失败联动 (标记一个未完成)')
    console.log('  · 情绪记录联动 (记录一条情绪)')
    console.log('  · 地图解锁联动 (积累打卡步数)')
    
  } catch (error) {
    console.error('[AI Test] ❌ 数据注入失败:', error)
  }
}

// ==================== 快速测试触发器 ====================

/**
 * 在控制台快速触发 AI 测试
 * 打开浏览器控制台执行: runAITests()
 */
function runAITests() {
  console.log('========================================')
  console.log('  AI 联动功能测试套件')
  console.log('========================================')
  
  const tests = [
    { name: '情绪识别-悲伤', input: '今天好难过，什么都不想做', expected: 'sad' },
    { name: '情绪识别-开心', input: '太棒了！我完成了所有目标！', expected: 'happy' },
    { name: '情绪识别-焦虑', input: '我好焦虑啊，压力好大', expected: 'anxious' },
    { name: '情绪识别-疲惫', input: '今天好累，什么都不想动', expected: 'tired' },
    { name: '情绪识别-中性', input: '你好', expected: 'neutral' }
  ]
  
  tests.forEach(test => {
    console.log(`\n[测试] ${test.name}`)
    console.log(`  输入: "${test.input}"`)
    console.log(`  期望情绪: ${test.expected}`)
  })
  
  console.log('\n执行测试...')
  console.log('请在聊天页面发送对应消息查看 AI 响应效果')
  console.log('========================================')
}

// ==================== 便捷方法 ====================

/**
 * 快速添加一条打卡 (用于测试打卡成功联动)
 */
function addTestCheckin(store, habitName = '测试习惯') {
  const habit = {
    id: Date.now(),
    type: 'custom',
    name: habitName,
    icon: '⭐',
    color: '#6B8E7B',
    target: '测试目标',
    difficulty: 'easy',
    multiplier: 1.0,
    reminderTime: new Date().toTimeString().substr(0, 5),
    streak: 1,
    completed: true,
    completedDate: todayStr,
    checkInTime: new Date().toISOString()
  }
  
  const habits = [...store.state.habits, habit]
  store.commit('setHabits', habits)
  store.commit('setTodayHabits', habits)
  
  const newStreak = (store.state.streakDays || 0) + 1
  store.commit('setStreakDays', newStreak)
  
  console.log(`[AI Test] ✓ 测试打卡已添加: ${habitName} (连续 ${newStreak} 天)`)
  return habit
}

/**
 * 快速添加一条情绪记录 (用于测试情绪联动)
 */
function addTestEmotion(store, emotion = 'sad') {
  const emotionMap = {
    sad: { emotion: 'sad', emotionLabel: '难过', intensity: 4, tags: ['委屈', '失落'], note: '测试：我好难过...' },
    happy: { emotion: 'happy', emotionLabel: '开心', intensity: 5, tags: ['成就感'], note: '测试：太开心啦！' },
    anxious: { emotion: 'anxious', emotionLabel: '焦虑', intensity: 3, tags: ['压力'], note: '测试：我好焦虑...' },
    tired: { emotion: 'tired', emotionLabel: '疲惫', intensity: 4, tags: ['累'], note: '测试：今天好累...' }
  }
  
  const data = emotionMap[emotion] || emotionMap.sad
  const record = {
    id: Date.now(),
    date: todayStr,
    ...data,
    createdAt: new Date().toISOString()
  }
  
  const records = [...store.state.emotionRecords, record]
  store.commit('setEmotionRecords', records)
  
  console.log(`[AI Test] ✓ 测试情绪已添加: ${data.emotionLabel} (强度 ${data.intensity})`)
  return record
}

// ==================== 场景模拟 (将 AI 互动注入聊天窗口) ====================

/**
 * 模拟打卡完成场景，AI 互动回复将直接显示在聊天窗口中
 * @param {String} habitName - 习惯名称
 * @param {Object} store - Vuex store
 * @param {Object} aiService - AI 服务模块
 * @returns {Promise<String>} AI 回复
 */
async function simulateCheckinSuccess(habitName = '阅读30分钟', store, aiService) {
  console.log('[AI Test] 🎬 开始模拟打卡完成场景...')
  
  // 1. 构造打卡习惯数据
  const habit = {
    id: Date.now(),
    type: 'read',
    name: habitName,
    icon: '📚',
    color: '#FFD93D',
    target: '阅读30分钟',
    difficulty: 'medium',
    multiplier: 1.5,
    streak: (store.state.streakDays || 0) + 1
  }
  
  // 2. 更新 store 数据 (模拟打卡完成)
  const todayDate = new Date().toISOString().split('T')[0]
  const habits = store.state.habits.map(h => 
    h.name === habitName 
      ? { ...h, completed: true, completedDate: todayDate, checkInTime: new Date().toISOString() }
      : h
  )
  if (!habits.find(h => h.name === habitName)) {
    habits.push({ ...habit, completed: true, completedDate: todayDate, checkInTime: new Date().toISOString() })
  }
  store.commit('setHabits', habits)
  
  const newStreak = (store.state.streakDays || 0) + 1
  store.commit('setStreakDays', newStreak)
  
  // 3. 同步行走地图步数
  store.commit('addWalkStep', {
    steps: 100,
    type: 'habit',
    description: `${habitName} 打卡`,
    emotion: 'happy'
  })
  
  console.log(`[AI Test] ✓ 打卡数据已更新: ${habitName}, 连续 ${newStreak} 天`)
  
  // 4. 触发 AI 互动
  try {
    const aiReply = await aiService.onCheckinSuccess(habit)
    console.log('[AI Test] 🤖 AI 回复:', aiReply)
    
    // 5. 将 AI 回复注入聊天窗口
    const aiMessage = {
      role: 'assistant',
      content: `【打卡成功】${aiReply}`,
      emotion: 'happy',
      time: new Date().toISOString()
    }
    store.commit('addChatMessage', aiMessage)
    
    // 6. 同时添加一条"用户行为"消息，记录打卡事件
    const userActionMessage = {
      role: 'user',
      content: `✅ 我完成了「${habitName}」打卡`,
      emotion: 'achievement',
      time: new Date(Date.now() - 1000).toISOString()
    }
    // 插入到 AI 回复之前
    const currentMessages = store.state.chatMessages
    const reordered = [
      ...currentMessages.slice(0, -1),
      userActionMessage,
      aiMessage
    ]
    store.commit('clearChatMessages')
    reordered.forEach(msg => store.commit('addChatMessage', msg))
    
    console.log('[AI Test] ✅ AI 互动已注入聊天窗口，请切到聊天页面查看！')
    return aiReply
  } catch (e) {
    console.error('[AI Test] ❌ AI 互动失败:', e)
    return null
  }
}

/**
 * 模拟打卡失败场景
 */
async function simulateCheckinFail(habitName = '运动30分钟', store, aiService) {
  console.log('[AI Test] 🎬 开始模拟打卡失败场景...')
  
  const habit = {
    id: Date.now(),
    type: 'sport',
    name: habitName,
    icon: '🏃',
    streak: store.state.streakDays || 0
  }
  
  try {
    const aiReply = await aiService.onCheckinFail(habit)
    console.log('[AI Test] 🤖 AI 回复:', aiReply)
    
    const userActionMessage = {
      role: 'user',
      content: `😔 今天没能完成「${habitName}」`,
      emotion: 'sad',
      time: new Date(Date.now() - 1000).toISOString()
    }
    const aiMessage = {
      role: 'assistant',
      content: `【打卡未完成】${aiReply}`,
      emotion: 'comfort',
      time: new Date().toISOString()
    }
    store.commit('addChatMessage', userActionMessage)
    store.commit('addChatMessage', aiMessage)
    
    console.log('[AI Test] ✅ 失败场景已注入聊天窗口')
    return aiReply
  } catch (e) {
    console.error('[AI Test] ❌ AI 互动失败:', e)
    return null
  }
}

/**
 * 模拟情绪记录场景
 */
async function simulateEmotionRecord(emotion = 'sad', store, aiService) {
  console.log('[AI Test] 🎬 开始模拟情绪记录场景...')
  
  const emotionMap = {
    sad: { label: '难过', intensity: 4, tags: ['委屈', '失落'], note: '今天感觉好委屈...' },
    happy: { label: '开心', intensity: 5, tags: ['成就感'], note: '今天超开心！' },
    anxious: { label: '焦虑', intensity: 3, tags: ['压力'], note: '工作压力好大...' },
    tired: { label: '疲惫', intensity: 4, tags: ['累'], note: '今天好累啊...' }
  }
  
  const data = emotionMap[emotion] || emotionMap.sad
  
  // 添加情绪记录到 store
  const record = {
    id: Date.now(),
    date: todayStr,
    emotion,
    emotionLabel: data.label,
    intensity: data.intensity,
    tags: data.tags,
    note: data.note,
    createdAt: new Date().toISOString()
  }
  const records = [...store.state.emotionRecords, record]
  store.commit('setEmotionRecords', records)
  
  // 同步行走地图步数
  store.commit('addWalkStep', {
    steps: 20,
    type: 'emotion',
    description: `记录${data.label}情绪`,
    emotion
  })
  
  try {
    const aiReply = await aiService.onEmotionRecord(data.label, data.intensity, data.tags)
    console.log('[AI Test] 🤖 AI 回复:', aiReply)
    
    const userActionMessage = {
      role: 'user',
      content: `📝 记录心情：${data.note}`,
      emotion,
      time: new Date(Date.now() - 1000).toISOString()
    }
    const aiMessage = {
      role: 'assistant',
      content: `【情绪疏导】${aiReply}`,
      emotion: 'comfort',
      time: new Date().toISOString()
    }
    store.commit('addChatMessage', userActionMessage)
    store.commit('addChatMessage', aiMessage)
    
    console.log('[AI Test] ✅ 情绪记录场景已注入聊天窗口')
    return aiReply
  } catch (e) {
    console.error('[AI Test] ❌ AI 互动失败:', e)
    return null
  }
}

/**
 * 模拟地图节点解锁场景
 */
async function simulateMapUnlock(stageName = '杭州西湖', store, aiService) {
  console.log('[AI Test] 🎬 开始模拟地图解锁场景...')
  
  // 更新行走地图数据
  const walkMap = { ...store.state.walkMap }
  walkMap.totalSteps = (walkMap.totalSteps || 0) + 200
  walkMap.currentStage = (walkMap.currentStage || 0) + 1
  store.commit('setWalkMap', walkMap)
  
  try {
    const aiReply = await aiService.onMapStageUnlock(stageName, walkMap.currentStage)
    console.log('[AI Test] 🤖 AI 回复:', aiReply)
    
    const userActionMessage = {
      role: 'user',
      content: `🗺️ 我解锁了新地标：${stageName}！`,
      emotion: 'excited',
      time: new Date(Date.now() - 1000).toISOString()
    }
    const aiMessage = {
      role: 'assistant',
      content: `【地标解锁】${aiReply}`,
      emotion: 'celebration',
      time: new Date().toISOString()
    }
    store.commit('addChatMessage', userActionMessage)
    store.commit('addChatMessage', aiMessage)
    
    console.log('[AI Test] ✅ 地图解锁场景已注入聊天窗口')
    return aiReply
  } catch (e) {
    console.error('[AI Test] ❌ AI 互动失败:', e)
    return null
  }
}

/**
 * 模拟正念练习完成场景
 */
async function simulateMeditationComplete(meditationName = '10分钟呼吸冥想', store, aiService) {
  console.log('[AI Test] 🎬 开始模拟正念练习完成场景...')
  
  try {
    const aiReply = await aiService.onMeditationComplete(meditationName)
    console.log('[AI Test] 🤖 AI 回复:', aiReply)
    
    const userActionMessage = {
      role: 'user',
      content: `🧘 完成了「${meditationName}」`,
      emotion: 'peaceful',
      time: new Date(Date.now() - 1000).toISOString()
    }
    const aiMessage = {
      role: 'assistant',
      content: `【正念完成】${aiReply}`,
      emotion: 'comfort',
      time: new Date().toISOString()
    }
    store.commit('addChatMessage', userActionMessage)
    store.commit('addChatMessage', aiMessage)
    
    console.log('[AI Test] ✅ 正念练习场景已注入聊天窗口')
    return aiReply
  } catch (e) {
    console.error('[AI Test] ❌ AI 互动失败:', e)
    return null
  }
}

/**
 * 运行全套场景模拟测试
 */
async function runAllScenarios(store, aiService) {
  console.log('========================================')
  console.log('  AI 场景联动全套测试')
  console.log('========================================\n')
  
  console.log('▶ 测试 1/5: 打卡成功联动')
  await simulateCheckinSuccess('阅读30分钟', store, aiService)
  await new Promise(r => setTimeout(r, 1500))
  
  console.log('\n▶ 测试 2/5: 打卡失败联动')
  await simulateCheckinFail('运动30分钟', store, aiService)
  await new Promise(r => setTimeout(r, 1500))
  
  console.log('\n▶ 测试 3/5: 情绪记录联动 (悲伤)')
  await simulateEmotionRecord('sad', store, aiService)
  await new Promise(r => setTimeout(r, 1500))
  
  console.log('\n▶ 测试 4/5: 地图节点解锁联动')
  await simulateMapUnlock('杭州西湖', store, aiService)
  await new Promise(r => setTimeout(r, 1500))
  
  console.log('\n▶ 测试 5/5: 正念练习完成联动')
  await simulateMeditationComplete('10分钟呼吸冥想', store, aiService)
  
  console.log('\n========================================')
  console.log('  ✅ 全套场景测试完成！')
  console.log('  请切到聊天页面查看所有 AI 互动回复')
  console.log('========================================')
}

// ==================== 导出 ====================

export {
  injectMockData,
  runAITests,
  addTestCheckin,
  addTestEmotion,
  simulateCheckinSuccess,
  simulateCheckinFail,
  simulateEmotionRecord,
  simulateMapUnlock,
  simulateMeditationComplete,
  runAllScenarios,
  mockHabits,
  mockEmotionRecords,
  mockWalkMap
}

export default {
  injectMockData,
  runAITests,
  addTestCheckin,
  addTestEmotion,
  simulateCheckinSuccess,
  simulateCheckinFail,
  simulateEmotionRecord,
  simulateMapUnlock,
  simulateMeditationComplete,
  runAllScenarios
}
