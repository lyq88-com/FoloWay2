/**
 * ai-service.js
 * AI 统一服务门面 — 整合云端对话、人设驱动、业务联动
 * 
 * 这是 APP 所有 AI 功能的核心入口：
 * - 普通聊天（云端拟人对话，含记忆和人设）
 * - 打卡事件触发的 AI 互动（成功/失败/提醒）
 * - 地图节点触发的 AI 分享
 * - 情绪/正念触发的 AI 疏导
 * 
 * 设计理念：
 * "AI 不再是独立页面，而是融入每一个业务场景的陪伴者"
 */

import { chatWithAI, buildUserContext, buildTriggerContext, updateHistory, clearHistory, PERSONA_SYSTEM_PROMPTS, setProvider } from './ai-cloud-service.js'

// ==================== 日志工具 ====================

const DEBUG = true
function logSvc(tag, data) {
  if (!DEBUG) return
  console.log(`[AI-Svc][${tag}]`, typeof data === 'object' ? JSON.stringify(data) : data)
}

// ==================== 全局配置 ====================

let store = null
let currentUserId = 'default-user'

/**
 * 初始化 AI 服务 (在 App.vue 的 onLaunch 调用)
 * @param {Object} vuexStore - Vuex store 实例
 */
function initAIService(vuexStore) {
  store = vuexStore
  console.log('[AI Service] 已初始化')
  
  // ↓↓↓ 修改 ↓↓↓
  // 原来：H5 + localhost 时切到 'local-mock'，等于在开发环境把 AI 全变成模板话术。
  // 现在：一律切到 'fastapi'，走真后端 POST /api/v1/chat/quick。
  // 安全性由两层兜底保证：
  //   1) 未登录（无 token）时 callFastAPI 直接返回 null，不打后端；
  //   2) 后端不可达 / 报错时，chatWithAI 的 try-catch 会落回原来的本地降级引擎。
  setProvider('fastapi')
  // ↑↑↑ 修改结束 ↑↑↑
  
  // 获取用户 ID
  if (store.state.userInfo && store.state.userInfo.id) {
    currentUserId = store.state.userInfo.id
  }
}

/**
 * 设置用户 ID
 */
function setUserId(userId) {
  currentUserId = userId
}

// ==================== 核心对话接口 ====================

/**
 * 发送消息给 AI (普通对话)
 * @param {String} message - 用户消息
 * @param {String} characterId - AI 角色 ID
 * @param {Array} history - 可选的历史对话
 * @returns {Promise<String>} AI 回复
 */
async function sendMessage(message, characterId, history = []) {
  if (!store) {
    console.warn('AI Service 未初始化')
    return '系统未就绪，请稍后再试~'
  }
  
  logSvc('sendMessage:enter', { characterId, messagePreview: message?.substring(0, 30), historyLen: history.length })
  
  try {
    // 1. 构建用户上下文 (自动读取打卡、情绪、地图数据)
    const userContext = buildUserContext(store.state)
    logSvc('sendMessage:userContext', {
      nickname: userContext.userProfile?.nickname,
      streakDays: userContext.userProfile?.streakDays,
      todayProgress: `${userContext.todayStatus?.completedHabits}/${userContext.todayStatus?.totalHabits}`
    })
    
    // 2. 调用云端 AI
    const response = await chatWithAI({
      userId: currentUserId,
      characterId,
      message,
      history,
      userContext,
      triggerContext: null
    })
    
    // 3. 更新对话历史
    updateHistory(currentUserId, message, response)
    
    logSvc('sendMessage:exit', { replyPreview: response?.substring(0, 50) })
    return response
  } catch (error) {
    console.error('[AI Service] 对话失败:', error)
    return '嗯...我好像走神了，能再说一次吗？'
  }
}

/**
 * 发送消息 (带业务触发上下文)
 * @param {String} message - 用户消息 (可空)
 * @param {String} characterId - AI 角色 ID
 * @param {String} eventType - 事件类型 (checkin_success/checkin_fail/emotion_record等)
 * @param {Object} eventData - 事件数据
 * @returns {Promise<String>} AI 回复
 */
async function sendMessageWithTrigger(message, characterId, eventType, eventData = {}) {
  if (!store) return '系统未就绪~'
  
  logSvc('sendMessageWithTrigger:enter', { eventType, characterId, eventData: JSON.stringify(eventData) })
  
  try {
    const userContext = buildUserContext(store.state)
    const triggerContext = buildTriggerContext(eventType, eventData)
    
    const finalMessage = message || buildTriggerMessage(eventType, eventData)
    
    logSvc('sendMessageWithTrigger:context', {
      userContextSummary: {
        streakDays: userContext.userProfile?.streakDays,
        todayProgress: `${userContext.todayStatus?.completedHabits}/${userContext.todayStatus?.totalHabits}`,
        walkStage: userContext.walkProgress?.stage
      },
      triggerEvent: triggerContext.event,
      triggerDetail: triggerContext.detail
    })
    
    const response = await chatWithAI({
      userId: currentUserId,
      characterId,
      message: finalMessage,
      history: [],
      userContext,
      triggerContext
    })
    
    updateHistory(currentUserId, finalMessage, response)
    
    logSvc('sendMessageWithTrigger:exit', { eventType, replyPreview: response?.substring(0, 50) })
    return response
  } catch (error) {
    console.error('[AI Service] 触发对话失败:', error)
    const fallback = generateFallbackResponse(eventType)
    logSvc('sendMessageWithTrigger:fallback', { eventType, fallback })
    return fallback
  }
}

// ==================== 事件触发接口 ====================

/**
 * 打卡成功事件
 * @param {Object} habit - 打卡的习惯对象
 * @returns {Promise<String>} AI 庆祝语
 */
async function onCheckinSuccess(habit) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  const streakDays = store.state.streakDays || 0
  
  logSvc('onCheckinSuccess', { habitName: habit?.name, habitType: habit?.type, streakDays })
  
  return sendMessageWithTrigger('', characterId, 'checkin_success', {
    habitName: habit?.name || '习惯',
    habitType: habit?.type || 'default',
    streakDays
  })
}

/**
 * 打卡失败事件 (未完成)
 */
async function onCheckinFail(habit) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  logSvc('onCheckinFail', { habitName: habit?.name })
  return sendMessageWithTrigger('', characterId, 'checkin_fail', {
    habitName: habit?.name || '习惯',
    reason: '今日未完成'
  })
}

/**
 * 打卡提醒事件 (到达时间提醒)
 */
async function onCheckinReminder(habit) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  return sendMessageWithTrigger('', characterId, 'checkin_reminder', {
    habitName: habit?.name || '习惯'
  })
}

/**
 * 情绪记录事件
 */
async function onEmotionRecord(emotion, intensity, tags = []) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  logSvc('onEmotionRecord', { emotion, intensity, tags })
  return sendMessageWithTrigger('', characterId, 'emotion_record', {
    emotion,
    intensity,
    tags
  })
}

/**
 * 地图节点解锁事件
 */
async function onMapStageUnlock(stageName, stageIndex) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  logSvc('onMapStageUnlock', { stageName, stageIndex })
  return sendMessageWithTrigger('', characterId, 'map_unlock', {
    location: stageName,
    stageName,
    stageIndex
  })
}

/**
 * 正念练习完成事件
 */
async function onMeditationComplete(meditationName) {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  logSvc('onMeditationComplete', { meditationName })
  return sendMessageWithTrigger('', characterId, 'meditation_complete', {
    meditationName
  })
}

/**
 * 每日复盘事件 (所有打卡完成后)
 */
async function onDailyReview() {
  const characterId = store.state.aiConfig.avatarType || 'linxi'
  return sendMessageWithTrigger('', characterId, 'daily_review', {})
}

// ==================== 辅助函数 ====================

/**
 * 根据事件类型构建触发消息 (用于无用户输入时)
 */
function buildTriggerMessage(eventType, eventData) {
  const messages = {
    checkin_success: `我完成了"${eventData.habitName}"的打卡，连续${eventData.streakDays}天啦`,
    checkin_fail: `今天没能完成"${eventData.habitName}"`,
    checkin_reminder: `该打卡"${eventData.habitName}"了`,
    emotion_record: `我记录了${eventData.emotion}情绪，强度${eventData.intensity}`,
    map_unlock: `我解锁了新地标：${eventData.stageName}`,
    meditation_complete: `我完成了"${eventData.meditationName}"正念练习`,
    daily_review: `今天完成了所有打卡，进行复盘吧`
  }
  return messages[eventType] || '你好'
}

/**
 * 本地降级回复 (云端失败时)
 */
function generateFallbackResponse(eventType) {
  const fallbacks = {
    checkin_success: '打卡成功啦！你的坚持真的很棒~',
    checkin_fail: '没关系，明天再来~',
    checkin_reminder: '该打卡咯，我陪着你~',
    emotion_record: '谢谢你记录心情，我会陪着你的~',
    map_unlock: '新的旅程开始了~',
    meditation_complete: '深呼吸，你做得很好~',
    daily_review: '今天的你超棒的~'
  }
  return fallbacks[eventType] || '我在听~'
}

/**
 * 获取 AI 人设信息
 */
function getPersonaInfo(characterId) {
  return PERSONA_SYSTEM_PROMPTS[characterId] || PERSONA_SYSTEM_PROMPTS.default
}

/**
 * 清空对话历史
 */
function clearConversation(userId = currentUserId) {
  clearHistory(userId)
}

/**
 * 获取用户上下文 (供页面展示)
 */
function getCurrentUserContext() {
  if (!store) return {}
  return buildUserContext(store.state)
}

// ==================== 统一导出 ====================

export default {
  initAIService,
  setUserId,
  sendMessage,
  sendMessageWithTrigger,
  onCheckinSuccess,
  onCheckinFail,
  onCheckinReminder,
  onEmotionRecord,
  onMapStageUnlock,
  onMeditationComplete,
  onDailyReview,
  getPersonaInfo,
  clearConversation,
  getCurrentUserContext
}

export {
  initAIService,
  sendMessage,
  sendMessageWithTrigger,
  onCheckinSuccess,
  onCheckinFail,
  onCheckinReminder,
  onEmotionRecord,
  onMapStageUnlock,
  onMeditationComplete,
  onDailyReview,
  getPersonaInfo,
  clearConversation,
  getCurrentUserContext
}
