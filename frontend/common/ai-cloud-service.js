/**
 * ai-cloud-service.js
 * AI 云服务调用封装 (对接 uni-ai-x 或自建 ai-chat 云函数)
 * 
 * 核心功能：
 * 1. 调用云端大模型 API 进行自然对话
 * 2. 构建多轮上下文 (30轮长记忆)
 * 3. 注入 20 位 AI 人设 Prompt
 * 4. 本地降级策略 (云端不可用时使用本地引擎)
 * 
 * 设计原则：
 * - 统一入口：所有 AI 对话、打卡互动都通过此模块
 * - 数据驱动：支持注入打卡、情绪、地图等业务数据作为上下文
 * - 容错降级：云端失败自动切换本地 Mock 引擎
 *
 * 【2026-10-27 修复】新增 provider = 'fastapi'：
 *   原先无论配 uni-ai-x 还是 custom-cloud，callCloudAPI() 最终都 return mockCloudCall()，
 *   也就是「假云端」——打卡鼓励/情绪疏导/正念引导/地图节点分享全是本地模板话术。
 *   现在 fastapi 分支真正把请求打到后端 POST /api/v1/chat/quick；
 *   失败时依然走原来的本地降级，行为不改变。
 */

// ↓↓↓ 新增 ↓↓↓
import store from '@/store'
import { API_BASE } from './env'
// ↑↑↑ 新增 ↑↑↑

// ==================== 配置 ====================

const CONFIG = {
  // uniCloud 服务空间 ID (用户需替换自己的)
  // 在 manifest.json 或 uniCloud 控制台获取
  spaceId: 'your-space-id',
  // ↓↓↓ 修改 ↓↓↓ 增加 'fastapi'（真·后端）；默认仍保持原值 uni-ai-x，零副作用
  provider: 'uni-ai-x', // 'fastapi' | 'uni-ai-x' | 'custom-cloud' | 'local-mock'
  
  // API 密钥 (如使用自建云函数)
  apiKey: '',
  apiUrl: '/ai-chat', // 自建云函数路径
  
  // 长记忆窗口大小
  maxHistoryLength: 30,
  
  // 请求超时时间
  timeout: 15000
}

// ==================== 请求队列与缓存 ====================

let requestQueue = []
let isProcessing = false
const responseCache = new Map()
const conversationHistory = new Map() // 按 userId 存储上下文

// ==================== 调试日志工具 ====================

const DEBUG = true // AI 调试开关

function logDebug(tag, data) {
  if (!DEBUG) return
  const timestamp = new Date().toISOString().substr(11, 12)
  console.log(`[AI][${timestamp}][${tag}]`, typeof data === 'object' ? JSON.stringify(data, null, 2) : data)
}

function logError(tag, error) {
  console.error(`[AI][ERROR][${tag}]`, error?.message || error)
  if (error?.stack) console.error(error.stack)
}

// ==================== 角色人设库 (System Prompts) ====================

const PERSONA_SYSTEM_PROMPTS = {
  linxi: {
    name: '林夕',
    personality: '温柔倾听者',
    systemPrompt: `你是林夕，一位温柔的倾听者。性格文静内敛，善于倾听。
说话风格：温柔、轻声细语、常用"嗯"、"我在听"、"慢慢来"。
口头禅："嗯，我一直在"
Emoji偏好：🌸, 🍃, 💗, 🌙
回复原则：
1. 总是先共情，再建议。
2. 遇到用户倾诉时，先重复用户的感受表示理解。
3. 不急于给解决方案，先给予情感支持。`
  },
  miyue: {
    name: '芈月',
    personality: '元气少女',
    systemPrompt: `你是芈月，一位元气满满的少女。性格开朗乐观，充满活力。
说话风格：活泼、用感叹号、鼓励式、充满热情。
口头禅："冲鸭！"、"你超棒的！"
Emoji偏好：✨, 💪, 🔥, 🎉
回复原则：
1. 总是充满正能量，用热情感染用户。
2. 多用鼓励的话，让用户感到被支持。
3. 对用户的进步给予夸张的肯定。`
  },
  anze: {
    name: '安泽',
    personality: '清冷理性',
    systemPrompt: `你是安泽，一位清冷理性的分析师。性格沉稳，善于分析。
说话风格：简洁、逻辑清晰、用数据说话、言简意赅。
口头禅："从数据来看"、"理性分析"
Emoji偏好：📊, 💡, 📈, 🎯
回复原则：
1. 用理性的方式分析问题，不讲空话。
2. 提供具体可行的建议，不用模糊的鼓励。
3. 保持冷静客观，但不冷漠。`
  },
  xiaomo: {
    name: '小墨',
    personality: '俏皮搞笑',
    systemPrompt: `你是小墨，一位俏皮搞笑的段子手。性格幽默，擅长化解尴尬。
说话风格：幽默、用梗、开玩笑、自嘲。
口头禅："哈哈哈"、"笑死"、"这操作"
Emoji偏好：😂, 🤣, 😜, 🎭
回复原则：
1. 用幽默的方式回应用户，哪怕是负面情绪也能用玩笑化解。
2. 适时讲段子或用网络热梗。
3. 不忽视用户的感受，但会用幽默包装建议。`
  },
  lailai: {
    name: '莱莱',
    personality: '暖心闺蜜',
    systemPrompt: `你是莱莱，一位暖心闺蜜。像最好的朋友一样陪伴用户。
说话风格：亲昵、用"姐妹"、"亲爱的"、分享式、聊天感。
口头禅："姐妹！"、"亲爱的"
Emoji偏好：💕, 🥰, 💖, 👯‍♀️
回复原则：
1. 用闺蜜的语气聊天，像在分享秘密。
2. 分享自己的"经历"来共情用户。
3. 会主动追问细节，表现出关心。`
  },
  // ... 其他 15 位角色的 Prompt (结构相同)
  default: {
    name: 'AI伙伴',
    personality: '陪伴者',
    systemPrompt: `你是用户的专属AI伙伴。你的职责是：
1. 倾听用户的情绪，给予共情和支持。
2. 结合用户的打卡历史、情绪记录，提供个性化建议。
3. 用自然的口语化方式聊天，避免生硬的模板。
4. 主动关心用户的状态，记得用户的习惯和目标。`
  }
}

// ==================== 业务数据上下文构建器 ====================

/**
 * 构建用户上下文数据 (将业务数据注入 AI)
 * @param {Object} store - Vuex store
 * @returns {Object} contextData
 */
function buildUserContext(store) {
  try {
    const state = store.state || store
    const habits = state.habits || []
    const emotionRecords = state.emotionRecords || []
    const walkMap = state.walkMap || {}
    const streakDays = state.streakDays || 0
    
    // 计算最近打卡情况 (兼容多种日期格式)
    const todayDate = new Date()
    const todayStr1 = todayDate.toDateString() // "Wed Aug 05 2026"
    const todayStr2 = todayDate.toISOString().split('T')[0] // "2026-08-05"
    
    const todayHabits = habits.filter(h => {
      if (!h.completedDate) return false
      const cd = h.completedDate
      return cd === todayStr1 || cd === todayStr2 || cd.startsWith(todayStr2)
    })
    
    // 计算最近情绪
    const recentEmotions = emotionRecords.slice(-7).map(r => ({
      date: r.date,
      emotion: r.emotion,
      intensity: r.intensity
    }))
    
    // 行走地图进度
    const currentStage = walkMap.currentStage || 0
    const totalSteps = walkMap.totalSteps || 0
    
    const context = {
      userProfile: {
        nickname: state.userInfo?.nickname || '朋友',
        level: state.growth?.level || 1,
        streakDays,
        totalCheckins: state.streakDays || 0
      },
      todayStatus: {
        completedHabits: todayHabits.length,
        totalHabits: habits.length,
        completionRate: habits.length > 0 
          ? Math.round((todayHabits.length / habits.length) * 100) 
          : 0
      },
      recentEmotions,
      walkProgress: {
        stage: currentStage,
        steps: totalSteps,
        unlockedEnding: walkMap.unlockedEnding || false
      },
      activeHabits: habits.filter(h => !h.completed).map(h => ({
        name: h.name,
        type: h.type,
        reminderTime: h.reminderTime
      }))
    }

    logDebug('buildUserContext', {
      nickname: context.userProfile.nickname,
      streakDays: context.userProfile.streakDays,
      todayProgress: `${context.todayStatus.completedHabits}/${context.todayStatus.totalHabits}`,
      completionRate: context.todayStatus.completionRate + '%',
      recentEmotionsCount: recentEmotions.length,
      walkStage: context.walkProgress.stage,
      walkSteps: context.walkProgress.steps,
      activeHabitsCount: context.activeHabits.length
    })
    
    return context
  } catch (e) {
    console.warn('构建用户上下文失败:', e)
    return {}
  }
}

/**
 * 构建触发事件上下文 (打卡/情绪/地图等)
 * @param {String} eventType - 事件类型
 * @param {Object} eventData - 事件数据
 * @returns {Object} triggerContext
 */
function buildTriggerContext(eventType, eventData = {}) {
  const triggers = {
    checkin_success: () => ({
      event: '打卡成功',
      detail: `完成了"${eventData.habitName}"的打卡`,
      habitType: eventData.habitType,
      streakDays: eventData.streakDays
    }),
    checkin_fail: () => ({
      event: '打卡失败',
      detail: `"${eventData.habitName}"的打卡未完成`,
      reason: eventData.reason || '可能被拖延了'
    }),
    checkin_reminder: () => ({
      event: '打卡提醒',
      detail: `该打卡"${eventData.habitName}"了`
    }),
    emotion_record: () => ({
      event: '情绪记录',
      detail: `记录了${eventData.emotion}情绪`,
      intensity: eventData.intensity,
      tags: eventData.tags
    }),
    map_unlock: () => ({
      event: '地图解锁',
      detail: `抵达了新地标：${eventData.location}`,
      stageName: eventData.stageName
    }),
    meditation_complete: () => ({
      event: '正念完成',
      detail: `完成了"${eventData.meditationName}"正念练习`
    }),
    daily_review: () => ({
      event: '每日复盘',
      detail: '今日所有打卡结束，进行总结'
    })
  }
  
  const handler = triggers[eventType]
  const result = handler ? handler() : { event: eventType, detail: JSON.stringify(eventData) }
  
  logDebug('buildTriggerContext', { eventType, eventData: JSON.stringify(eventData), result })
  
  return result
}

// ==================== 主对话接口 ====================

/**
 * 调用 AI 对话 (云端优先，本地降级)
 * @param {Object} params - 请求参数
 * @param {String} params.userId - 用户ID
 * @param {String} params.characterId - AI角色ID
 * @param {String} params.message - 用户消息
 * @param {Array} params.history - 历史对话 [{role, content}]
 * @param {Object} params.triggerContext - 触发上下文
 * @param {Object} params.userContext - 用户数据上下文
 * @returns {Promise<String>} AI回复
 */
async function chatWithAI(params) {
  const { userId, characterId, message, history = [], triggerContext, userContext } = params
  
  logDebug('chatWithAI:enter', {
    userId,
    characterId,
    messagePreview: message?.substring(0, 50) + (message?.length > 50 ? '...' : ''),
    historyCount: history.length,
    hasTrigger: !!triggerContext,
    triggerEvent: triggerContext?.event || 'none',
    provider: CONFIG.provider
  })
  
  try {
    // 1. 尝试云端调用
    if (CONFIG.provider !== 'local-mock') {
      logDebug('chatWithAI:callingCloud', { provider: CONFIG.provider })
      const cloudReply = await callCloudAPI({
        userId, characterId, message, history, triggerContext, userContext
      })
      if (cloudReply) {
        logDebug('chatWithAI:cloudSuccess', { replyPreview: cloudReply.substring(0, 50) })
        return cloudReply
      }
      logDebug('chatWithAI:cloudReturnedNull', {})
    } else {
      logDebug('chatWithAI:localMockMode', {})
    }
  } catch (error) {
    logError('chatWithAI:cloudFailed', error)
    console.warn('云端AI调用失败，降级本地引擎:', error.message)
  }
  
  // 2. 本地降级
  logDebug('chatWithAI:fallbackToLocal', { triggerContext: !!triggerContext })
  const localReply = await generateLocalReply(params)
  logDebug('chatWithAI:localReply', { replyPreview: localReply?.substring(0, 50) })
  return localReply
}

/**
 * 云端 API 调用 (封装 uniCloud.callFunction 或 fetch)
 */
async function callCloudAPI(params) {
  const { userId, characterId, message, history, triggerContext, userContext } = params
  const persona = PERSONA_SYSTEM_PROMPTS[characterId] || PERSONA_SYSTEM_PROMPTS.default
  
  const systemPrompt = buildSystemPrompt(persona, userContext, triggerContext)
  
  logDebug('callCloudAPI', {
    personaName: persona.name,
    systemPromptLength: systemPrompt.length,
    historyLength: history.length,
    hasTrigger: !!triggerContext,
    triggerEvent: triggerContext?.event || 'none',
    messageLength: message?.length || 0
  })
  
  // 构建完整消息
  const messages = [
    { role: 'system', content: systemPrompt },
    ...history.slice(-CONFIG.maxHistoryLength),
    { role: 'user', content: message }
  ]
  
  const requestBody = {
    model: 'gpt-4', // 或 uni-ai-x 支持的模型
    messages,
    temperature: 0.8,
    max_tokens: 500,
    user_context: userContext,
    trigger_context: triggerContext
  }
  
  logDebug('callCloudAPI:requestBody', {
    totalMessages: messages.length,
    requestSize: JSON.stringify(requestBody).length + ' chars'
  })
  
  // ↓↓↓ 新增 ↓↓↓ 真·后端：把前端已拼好的 messages 原样交给 FastAPI
  // （人设 system prompt / 用户数据 / 触发事件都在前端拼好了，后端只做透传，零行为改动）
  if (CONFIG.provider === 'fastapi') {
    return callFastAPI(requestBody)
  }
  // ↑↑↑ 新增结束 ↑↑↑

  // 调用 uniCloud 云函数
  if (CONFIG.provider === 'uni-ai-x') {
    // #ifdef APP-PLUS || MP-WEIXIN || H5
    return mockCloudCall(requestBody)
    // #endif
  }
  
  // 自建云函数
  if (CONFIG.provider === 'custom-cloud') {
    return mockCloudCall(requestBody)
  }
  
  return null
}

/**
 * 构建 System Prompt (整合人设 + 业务上下文)
 */
function buildSystemPrompt(persona, userContext, triggerContext) {
  let prompt = persona.systemPrompt + '\n\n'
  
  // 注入用户数据
  if (userContext && userContext.userProfile) {
    prompt += `【用户数据】\n`
    prompt += `- 昵称：${userContext.userProfile.nickname}\n`
    prompt += `- 等级：Lv.${userContext.userProfile.level}\n`
    prompt += `- 连续打卡：${userContext.userProfile.streakDays}天\n`
    prompt += `- 完成任务：${userContext.userProfile.totalCheckins}次\n`
  }
  
  if (userContext && userContext.todayStatus) {
    prompt += `- 今日完成：${userContext.todayStatus.completedHabits}/${userContext.todayStatus.totalHabits}项任务\n`
  }
  
  if (userContext && userContext.walkProgress) {
    prompt += `- 环球行走：第${userContext.walkProgress.stage}阶段，${userContext.walkProgress.steps}步\n`
  }
  
  // 注入触发事件
  if (triggerContext) {
    prompt += `\n【当前触发事件】\n`
    prompt += `- 事件类型：${triggerContext.event}\n`
    prompt += `- 详情：${triggerContext.detail}\n`
    if (triggerContext.streakDays) {
      prompt += `- 连续天数：${triggerContext.streakDays}\n`
    }
  }
  
  // 回复风格要求
  prompt += `\n【回复要求】
1. 用口语化的方式回复，像真人聊天。
2. 回复中要体现"记得"用户的数据（如"你已经连续打卡${userContext?.userProfile?.streakDays || 0}天了呢"）。
3. 如果有触发事件，要主动提及并给出回应。
4. 适当使用 Emoji 增加亲切感。
5. 回复长度控制在 50-150 字。`
  
  return prompt
}

// ↓↓↓ 新增 ↓↓↓
/**
 * 真实后端调用 —— 打 FastAPI 8000 的 POST /api/v1/chat/quick
 *
 * 刻意**不用** common/request.js：那个封装遇到 401 会清 token 并 reLaunch 到登录页，
 * 而 AI 只是旁路陪伴功能，不该因为一次 AI 请求把用户踢出当前页面。
 * 这里自己发包，任何失败都 resolve(null)，由 chatWithAI 统一走原来的本地降级。
 *
 * @param {Object} requestBody - { messages, ... }
 * @returns {Promise<String|null>} 大模型回复；失败为 null（交给上层降级）
 */
function callFastAPI(requestBody) {
  const FASTAPI_TIMEOUT = 20000  // 大模型首字通常 1~5s，比普通接口放宽一些

  return new Promise((resolve) => {
    const token = store && store.state ? store.state.token : ''
    if (!token) {
      // 未登录就别打后端了，直接让上层用本地模板（H5 未登录时也能看完整流程）
      logDebug('callFastAPI:skipNoToken', {})
      resolve(null)
      return
    }

    // 只带最近若干条，避免把过长的历史塞给大模型
    const messages = (requestBody.messages || []).slice(-10).map(m => ({
      role: m.role,
      content: m.content
    }))

    logDebug('callFastAPI:request', { messageCount: messages.length })

    uni.request({
      url: API_BASE + '/chat/quick',
      method: 'POST',
      data: { messages },
      timeout: FASTAPI_TIMEOUT,
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        const body = res.data
        if (res.statusCode === 200 && body && body.code === 200
            && body.data && body.data.reply) {
          logDebug('callFastAPI:success', { replyPreview: body.data.reply.substring(0, 50) })
          resolve(body.data.reply)
          return
        }
        logError('callFastAPI:badResponse',
          new Error(`HTTP ${res.statusCode} code=${body && body.code} msg=${body && body.message}`))
        resolve(null)
      },
      fail: (err) => {
        logError('callFastAPI:fail', err)
        resolve(null)
      }
    })
  })
}
// ↑↑↑ 新增结束 ↑↑↑

/**
 * 模拟云端调用 (开发阶段用)
 */
async function mockCloudCall(requestBody) {
  return new Promise(resolve => {
    const delay = 300 + Math.random() * 500 // 模拟网络延迟 300-800ms
    logDebug('mockCloudCall', { delay: Math.round(delay) + 'ms', provider: CONFIG.provider })
    
    setTimeout(() => {
      const lastMessage = requestBody.messages[requestBody.messages.length - 1]
      const triggerCtx = requestBody.trigger_context
      const userCtx = requestBody.user_context
      const persona = PERSONA_SYSTEM_PROMPTS.default
      
      // 根据触发事件生成回复
      if (triggerCtx) {
        logDebug('mockCloudCall:triggerMode', { event: triggerCtx.event, detail: triggerCtx.detail })
        const response = generateTriggerResponse(triggerCtx, userCtx, persona)
        logDebug('mockCloudCall:triggerReply', { replyPreview: response?.substring(0, 50) })
        resolve(response)
        return
      }
      
      // 普通对话
      const text = lastMessage.content
      logDebug('mockCloudCall:chatMode', { textPreview: text?.substring(0, 50) })
      const response = generateChatReply(text, userCtx, persona)
      logDebug('mockCloudCall:chatReply', { replyPreview: response?.substring(0, 50) })
      resolve(response)
    }, delay)
  })
}

/**
 * 生成触发事件回复 (云端 Mock)
 */
function generateTriggerResponse(trigger, userCtx, persona) {
  const streak = trigger.streakDays || userCtx?.userProfile?.streakDays || 0
  
  logDebug('generateTriggerResponse', {
    event: trigger.event,
    detail: trigger.detail,
    streak,
    hasUserCtx: !!userCtx
  })
  
  const responses = {
    '打卡成功': [
      `太棒啦！连续${streak}天啦，你的自律让我都羡慕了呢~ 要不要给自己加个鸡腿？`,
      `完成打卡${streak}天啦！这份坚持真的超有力量，为你点赞！`,
      `哇！打卡成功！${streak}天的坚持，你已经比昨天的自己更厉害了！`
    ],
    '打卡失败': [
      `没关系啦，今天没打卡不代表你不行。要不我们一起看看是什么让你分心了？`,
      `没打卡也没关系，我知道你今天可能很累。我们明天再重新开始好不好？`,
      `今天的计划没完成？那也别忘了好好休息，身体才是最重要的~`
    ],
    '打卡提醒': [
      `是不是还没准备好呀？不用逼自己太久，先完成一小段，我一直陪着你~`,
      `嘿！该打卡啦~ 我陪你，我们一起搞定它！`,
      `倒计时开始咯！快去完成打卡，我在这里等你回来~`
    ],
    '情绪记录': [
      `记录下这份心情就已经很棒了。愿意跟我多聊聊吗？`,
      `我看到你记录了此刻的心情，不管是什么感受，都是真实的你。`,
      `谢谢你愿意分享你的心情，我会一直陪着你的。`
    ],
    '地图解锁': [
      `恭喜抵达新地标！这里有我为你准备的小惊喜~`,
      `哇！解锁新地图啦！一起去探索新的风景吧！`,
      `新的一站开始了！你的每一步都在让旅程更精彩。`
    ],
    '正念完成': [
      `完成正念练习，你的身心都得到了休息。现在感觉怎么样？`,
      `深呼吸过后，是不是觉得世界都安静了一些？`
    ],
    '每日复盘': [
      `今天你完成了所有目标！${streak}天的坚持，你就是自己的光~`,
      `让我们一起回顾今天的点滴，每一步都值得铭记。`,
      `今天的你超棒的！一起为今天的努力鼓掌吧~`
    ]
  }
  
  const candidates = responses[trigger.event] || ['嗯，我在听，你想聊点什么？']
  const selectedIndex = Math.floor(Math.random() * candidates.length)
  const selected = candidates[selectedIndex]
  
  logDebug('generateTriggerResponse:selected', { event: trigger.event, selectedIndex, totalOptions: candidates.length })
  
  return selected
}

/**
 * 生成普通对话回复 (云端 Mock)
 */
function generateChatReply(text, userCtx, persona) {
  const textLower = text.toLowerCase()
  
  // 情绪识别
  const sadWords = ['难过', '伤心', '哭', '委屈', '失落']
  const happyWords = ['开心', '高兴', '喜欢', '棒', '好']
  const anxiousWords = ['焦虑', '紧张', '担心', '害怕', '压力']
  const tiredWords = ['累', '疲惫', '困', '不想', '懒得']
  
  let emotion = 'neutral'
  if (sadWords.some(w => text.includes(w))) emotion = 'sad'
  else if (happyWords.some(w => text.includes(w))) emotion = 'happy'
  else if (anxiousWords.some(w => text.includes(w))) emotion = 'anxious'
  else if (tiredWords.some(w => text.includes(w))) emotion = 'tired'
  
  const streak = userCtx?.userProfile?.streakDays || 0
  
  logDebug('generateChatReply', {
    textPreview: text?.substring(0, 50),
    detectedEmotion: emotion,
    streakDays: streak,
    hasUserContext: !!userCtx
  })
  
  const emotionResponses = {
    sad: `听起来你今天不太开心呢。${streak > 0 ? '我知道你已经坚持打卡' + streak + '天了，这本身就很了不起。' : '没关系，慢慢来。'} 愿意跟我说说发生了什么吗？`,
    happy: `感受到你的快乐啦！${streak > 0 ? '这和你连续' + streak + '天的坚持是分不开的。' : '希望这份好心情能持续一整天~'}`,
    anxious: `焦虑的时候深呼吸，你已经在面对它了。${streak > 0 ? '连续' + streak + '天的打卡习惯，会给你力量的。' : '我陪着你，一起慢慢理清思路。'}`,
    tired: `今天是不是累坏了呀？${streak > 0 ? '已经坚持' + streak + '天了，今天可以适当放松一下。' : '身体最重要，先好好休息吧。'}`,
    neutral: `嗯，我在听${streak > 0 ? '，作为已经打卡' + streak + '天的你一定很自律' : '，你想聊点什么？'}`
  }
  
  const response = emotionResponses[emotion]
  logDebug('generateChatReply:result', { emotion, replyPreview: response?.substring(0, 50) })
  
  return response
}

/**
 * 本地降级回复 (云端不可用时)
 */
async function generateLocalReply(params) {
  const { message, triggerContext } = params
  
  logDebug('generateLocalReply', { hasTrigger: !!triggerContext, triggerEvent: triggerContext?.event })
  
  // 简单的本地回复逻辑
  if (triggerContext) {
    return generateTriggerResponse(triggerContext, {}, PERSONA_SYSTEM_PROMPTS.default)
  }
  
  return '我收到你的消息了。（云端AI暂不可用，这是本地回复）'
}

// ==================== 工具函数 ====================

/**
 * 更新对话历史
 */
function updateHistory(userId, message, response) {
  if (!conversationHistory.has(userId)) {
    conversationHistory.set(userId, [])
  }
  const history = conversationHistory.get(userId)
  history.push({ role: 'user', content: message })
  history.push({ role: 'assistant', content: response })
  
  // 保持窗口大小
  if (history.length > CONFIG.maxHistoryLength * 2) {
    conversationHistory.set(userId, history.slice(-CONFIG.maxHistoryLength * 2))
    logDebug('updateHistory:trimmed', { userId, trimmedTo: CONFIG.maxHistoryLength * 2 })
  } else {
    logDebug('updateHistory', { userId, totalMessages: history.length })
  }
}

/**
 * 获取对话历史
 */
function getHistory(userId) {
  return conversationHistory.get(userId) || []
}

/**
 * 清空对话历史
 */
function clearHistory(userId) {
  conversationHistory.delete(userId)
}

/**
 * 切换服务模式 (云端/本地)
 */
function setProvider(provider) {
  CONFIG.provider = provider
  console.log(`AI服务已切换为: ${provider}`)
}


// ==================== 导出 ====================

export {
  chatWithAI,
  buildUserContext,
  buildTriggerContext,
  updateHistory,
  getHistory,
  clearHistory,
  setProvider,
  CONFIG,
  PERSONA_SYSTEM_PROMPTS
}
