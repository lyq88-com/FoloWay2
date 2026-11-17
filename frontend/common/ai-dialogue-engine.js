/**
 * AI 对话引擎 v2.0 — 智能自由回复系统
 *
 * 核心升级：
 * 1. 去除固定模板拼接，改为完整句子的上下文感知动态生成
 * 2. 深度情绪分析（11种情绪 + 强度），场景感知回复
 * 3. 持久化长期记忆（7-15天）：话题追踪、情绪趋势、拖延模式、防重复
 * 4. 20种独立人格策略，每种人格有独特语气和回复模式
 * 5. 行走地图位置感知、习惯打卡状态、亲密度上下文整合
 * 6. 5大场景处理：负面情绪、拖延、闲聊、问答、打卡后
 *
 * 向后兼容：保持所有原有导出和函数签名
 */

import { getCurrentStage } from '@/common/walk-map-config.js'

// ============================================================
// 第一部分：常量定义（保持原有）
// ============================================================

const INTENT_TYPES = {
  GREETING: 'greeting',
  FAREWELL: 'farewell',
  ANXIETY: 'anxiety',
  SAD: 'sad',
  HAPPY: 'happy',
  PROCRASTINATE: 'procrastinate',
  COMPLETE: 'complete',
  ENCOURAGE: 'encourage',
  QUESTION: 'question',
  COMPLAIN: 'complain',
  CONFUSED: 'confused',
  BORED: 'bored',
  STUDY: 'study',
  CHAT: 'chat',
  CHECKIN: 'checkin',
  NEED_HUG: 'need_hug',
  TASK_REMIND: 'task_remind',
  DAILY_REPORT: 'daily_report',
  ANTI_LAZY: 'anti_lazy',
  SHARE: 'share',
  EXCITED: 'excited',
  DISAPPOINTED: 'disappointed',
  THANK: 'thank',
  APOLOGIZE: 'apologize',
  MOTIVATE: 'motivate',
  DAILY_ASK: 'daily_ask'
}

const PERSONALITY_TYPES = {
  GENTLE_HEALER: 'gentle_healer',
  ENERGETIC_SUNNY: 'energetic_sunny',
  COOL_RATIONAL: 'cool_rational',
  HUMOROUS_RELAXED: 'humorous_relaxed',
  GENTLE_SCHOLAR: 'gentle_scholar',
  TSUNDERE_AMBITIOUS: 'tsundere_ambitious',
  LAZY_BUDDHA: 'lazy_buddha',
  MATURE_STABLE: 'mature_stable',
  CLEAN_BOY: 'clean_boy',
  SWEET_GIRL: 'sweet_girl',
  RATIONAL_ANALYSIS: 'rational_analysis',
  ARTISTIC_POETIC: 'artistic_poetic',
  PASSIONATE_INSPIRING: 'passionate_inspiring',
  TRANQUIL_BUDDHA: 'tranquil_buddha',
  COOL_FREE: 'cool_free',
  WARM_LISTENER: 'warm_listener',
  SELF_DISIPLINE_SUPERVISOR: 'self_discipline_supervisor',
  DREAMY_GENTLE: 'dreamy_gentle',
  CLEAR_INDEPENDENT: 'clear_independent',
  EXCLUSIVE_DOTING: 'exclusive_doting'
}

const PERSONALITY_CONFIG = {
  [PERSONALITY_TYPES.GENTLE_HEALER]: { name: '温柔治愈', emojis: ['🐱', '🌸', '💗', '✨', '🎀', '🐾'], tone: '柔软、共情、细腻、走心' },
  [PERSONALITY_TYPES.ENERGETIC_SUNNY]: { name: '元气阳光', emojis: ['🐱', '🎀', '✨', '🌈', '💪', '💗'], tone: '活泼、积极、热情、有活力' },
  [PERSONALITY_TYPES.COOL_RATIONAL]: { name: '清冷理智', emojis: ['🐱', '❄️', '💎', '🌙', '✨', '🍃'], tone: '清醒、理智、克制、暖心' },
  [PERSONALITY_TYPES.HUMOROUS_RELAXED]: { name: '幽默松弛', emojis: ['🐱', '😂', '😜', '🎀', '✨', '🥳'], tone: '幽默、轻松、搞笑、解压' },
  [PERSONALITY_TYPES.GENTLE_SCHOLAR]: { name: '温柔学霸', emojis: ['🐱', '📚', '🔍', '💡', '✨', '🌸'], tone: '耐心、博学、温柔、理性' },
  [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: { name: '傲娇上进', emojis: ['🐱', '😤', '🎀', '💪', '🔥', '✨'], tone: '嘴硬、心软、督促、傲娇' },
  [PERSONALITY_TYPES.LAZY_BUDDHA]: { name: '慵懒佛系', emojis: ['🐱', '🍃', '🌿', '💤', '☕', '🐾'], tone: '慢悠悠、松弛温柔、治愈内耗' },
  [PERSONALITY_TYPES.MATURE_STABLE]: { name: '成熟稳重', emojis: ['🐱', '🌙', '📜', '🍂', '🌊', '🗿'], tone: '通透开导、人生建议、靠谱安心' },
  [PERSONALITY_TYPES.CLEAN_BOY]: { name: '少年干净', emojis: ['🐱', '🌸', '✨', '🌙', '🍃', '🌻'], tone: '清爽简单、纯真温柔、青涩治愈' },
  [PERSONALITY_TYPES.SWEET_GIRL]: { name: '甜暖少女', emojis: ['🐱', '🍭', '🌸', '💖', '✨', '🍓'], tone: '软萌贴心、细腻温柔、超会共情' },
  [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: { name: '理性剖析', emojis: ['🐱', '⚡', '💡', '📊', '🔍', '🧠'], tone: '帮你拆解烦恼、理清思路、解决迷茫' },
  [PERSONALITY_TYPES.ARTISTIC_POETIC]: { name: '文艺诗意', emojis: ['🐱', '🌸', '🌙', '🎨', '🍃', '✨'], tone: '氛围感对话、温柔浪漫、走心不矫情' },
  [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: { name: '热血励志', emojis: ['🐱', '🔥', '💪', '⚡', '🌟', '🚀'], tone: '打气超强、坚定鼓舞、给你动力' },
  [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: { name: '通透佛系', emojis: ['🐱', '🍃', '🌿', '🌙', '🌸', '💤'], tone: '抚平焦虑、教你放下、松弛生活' },
  [PERSONALITY_TYPES.COOL_FREE]: { name: '酷飒洒脱', emojis: ['🐱', '😎', '🔥', '💋', '⚡', '✨'], tone: '干脆利落、自信霸气、带你想开' },
  [PERSONALITY_TYPES.WARM_LISTENER]: { name: '暖心倾听', emojis: ['🐱', '❤️', '💫', '🌸', '🌙', '💖'], tone: '无条件接纳、最会陪伴' },
  [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: { name: '自律监督', emojis: ['🐱', '📝', '⏰', '💪', '✅', '🌟'], tone: '温柔督促、鼓励坚持、成长' },
  [PERSONALITY_TYPES.DREAMY_GENTLE]: { name: '梦幻温柔', emojis: ['🐱', '🦋', '🌙', '✨', '🌸', '💫'], tone: '浪漫细腻、治愈温柔、梦幻氛围感' },
  [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: { name: '清醒独立', emojis: ['🐱', '❄️', '🌊', '💎', '✨', '🌙'], tone: '三观超正、帮你清醒、拒绝内耗' },
  [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: { name: '专属宠溺', emojis: ['🐱', '💖', '🌸', '💫', '🌙', '💕'], tone: '偏爱式对话、只对你温柔、超甜专属' }
}

// ============================================================
// 第二部分：深度情绪分析系统（全新）
// ============================================================

const EMOTION_TYPES = {
  HAPPY: 'happy',
  EXCITED: 'excited',
  SAD: 'sad',
  ANXIOUS: 'anxious',
  TIRED: 'tired',
  LAZY: 'lazy',
  CONFUSED: 'confused',
  VENTING: 'venting',
  LONELY: 'lonely',
  GRATEFUL: 'grateful',
  NEUTRAL: 'neutral'
}

const EMOTION_KEYWORDS = {
  [EMOTION_TYPES.HAPPY]: ['开心', '高兴', '快乐', '太棒了', '太好了', '好棒', '哈哈', '嘻嘻', '嘿嘿', '笑死', '不错', '挺好的'],
  [EMOTION_TYPES.EXCITED]: ['兴奋', '激动', '期待', '超开心', '太爽了', '牛啊', '厉害', '开心到', '激动到', '超期待', '好耶'],
  [EMOTION_TYPES.SAD]: ['难过', '伤心', '哭', '失望', '委屈', '心痛', '难受', '想哭', '不开心', '心情不好', '低落', 'emo', '破防'],
  [EMOTION_TYPES.ANXIOUS]: ['焦虑', '紧张', '不安', '担心', '害怕', '忐忑', '忧虑', '慌', '压力', '怕', '慌张', '没底'],
  [EMOTION_TYPES.TIRED]: ['累', '疲惫', '困', '撑不住', '没力气', '精疲力尽', '心力交瘁', '累死', '好累', '困死', '熬不住'],
  [EMOTION_TYPES.LAZY]: ['不想做', '懒得', '拖延', '不想动', '躺着', '赖床', '没动力', '摸鱼', '不想起', '摆烂', '躺平'],
  [EMOTION_TYPES.CONFUSED]: ['迷茫', '困惑', '不知道', '怎么办', '方向', '不知所措', '没头绪', '纠结', '选择困难'],
  [EMOTION_TYPES.VENTING]: ['烦', '讨厌', '无语', '垃圾', '坑', '不爽', '郁闷', '气死', '烦死', '崩溃', '受不了', '恶心', '吐了'],
  [EMOTION_TYPES.LONELY]: ['孤独', '一个人', '没人', '寂寞', '想家', '空虚', '没人懂', '孤单', '好冷清'],
  [EMOTION_TYPES.GRATEFUL]: ['谢谢', '感谢', '感恩', '太感谢了', '谢谢啦', '多亏了', '幸亏']
}

function analyzeEmotion(text) {
  const t = text.toLowerCase().trim()
  const scores = {}
  let maxScore = 0
  let primaryEmotion = EMOTION_TYPES.NEUTRAL
  let secondaryEmotion = null

  for (const [emotion, keywords] of Object.entries(EMOTION_KEYWORDS)) {
    let score = 0
    for (const kw of keywords) {
      if (t.includes(kw)) {
        score += kw.length >= 3 ? 3 : (kw.length >= 2 ? 2 : 1)
      }
    }
    if (score > 0) {
      scores[emotion] = score
      if (score > maxScore) {
        if (primaryEmotion !== EMOTION_TYPES.NEUTRAL) {
          secondaryEmotion = primaryEmotion
        }
        maxScore = score
        primaryEmotion = emotion
      } else if (!secondaryEmotion || score > scores[secondaryEmotion]) {
        secondaryEmotion = emotion
      }
    }
  }

  const intensity = maxScore >= 6 ? 3 : (maxScore >= 3 ? 2 : (maxScore > 0 ? 1 : 0))
  return { type: primaryEmotion, intensity, secondary: secondaryEmotion }
}

// ============================================================
// 第三部分：增强意图检测（扩展关键词）
// ============================================================

const INTENT_KEYWORDS = {
  [INTENT_TYPES.GREETING]: ['早安', '早上好', 'hello', 'hi', '嗨', '早上好呀', '早呀', '午安', '下午好'],
  [INTENT_TYPES.FAREWELL]: ['晚安', '再见', '拜拜', 'bye', '先走了', '明天见', '睡了', '休息了'],
  [INTENT_TYPES.ANXIETY]: ['焦虑', '紧张', '不安', '担心', '害怕', '忐忑', '忧虑', '慌', '压力'],
  [INTENT_TYPES.SAD]: ['难过', '伤心', '哭', '失望', '委屈', '心痛', '难受', 'emo', '破防'],
  [INTENT_TYPES.HAPPY]: ['开心', '高兴', '快乐', '太棒了', '太好了', '兴奋', '激动', '不错', '挺好的'],
  [INTENT_TYPES.PROCRASTINATE]: ['拖延', '不想做', '懒得', '拖', '没动力', '不想动', '摆烂', '躺平'],
  [INTENT_TYPES.COMPLETE]: ['完成', '做完', '搞定', '结束', '通关', '搞定了', '做完了'],
  [INTENT_TYPES.ENCOURAGE]: ['加油', '鼓励', '支持', '坚持', '努力', '打气', '动力'],
  [INTENT_TYPES.QUESTION]: ['？', '怎么', '为什么', '什么', '吗', '如何', '哪里', '怎么办', '好不好', '行不行'],
  [INTENT_TYPES.COMPLAIN]: ['烦', '讨厌', '无语', '垃圾', '坑', '不爽', '郁闷', '气死', '崩溃'],
  [INTENT_TYPES.CONFUSED]: ['迷茫', '困惑', '不知道', '怎么办', '方向', '不知所措', '没头绪'],
  [INTENT_TYPES.BORED]: ['无聊', '没事', '发呆', '没事做', '好闲', '没意思', '好无聊'],
  [INTENT_TYPES.STUDY]: ['学习', '看书', '作业', '考试', '复习', '备考', '背书', '刷题'],
  [INTENT_TYPES.CHAT]: ['聊天', '说说话', '聊聊', '谈谈', '说说'],
  [INTENT_TYPES.CHECKIN]: ['打卡', '签到', '记录', '今日打卡', '已完成'],
  [INTENT_TYPES.NEED_HUG]: ['抱抱', '求抱', '安慰', '需要你', '抱抱我', '抱一下'],
  [INTENT_TYPES.TASK_REMIND]: ['任务', '计划', '提醒', '该做', '待办', '待完成'],
  [INTENT_TYPES.DAILY_REPORT]: ['今天', '日报', '总结', '汇报', '今天过得', '今日总结'],
  [INTENT_TYPES.ANTI_LAZY]: ['懒', '不想动', '躺着', '不动', '不想起', '赖床'],
  [INTENT_TYPES.SHARE]: ['分享', '告诉', '说说', '跟你说', '告诉你', '你知道吗'],
  [INTENT_TYPES.EXCITED]: ['兴奋', '激动', '期待', '开心到', '超期待', '好耶'],
  [INTENT_TYPES.DISAPPOINTED]: ['失望', '失落', '遗憾', '没做好', '不理想', '搞砸了'],
  [INTENT_TYPES.THANK]: ['谢谢', '感谢', '太感谢', '谢谢啦', '谢谢你', '多亏了'],
  [INTENT_TYPES.APOLOGIZE]: ['对不起', '抱歉', '抱歉啦', '不好意思', '我的错'],
  [INTENT_TYPES.MOTIVATE]: ['励志', '动力', '前进', '奋斗', '努力加油'],
  [INTENT_TYPES.DAILY_ASK]: ['你在做什么', '在做什么', '忙什么', '在忙吗', '干嘛呢', '今天怎么样', '今天好吗', '还好吗', '过得怎么样', '最近怎么样', '最近好吗', '在吗', '睡了吗', '吃饭了吗', '吃了吗', '在干嘛', '做什么呢', '忙不忙', '有空吗']
}

function detectIntent(text) {
  const t = text.toLowerCase().trim()
  let maxScore = 0
  let bestIntent = INTENT_TYPES.CHAT
  for (const [intent, keywords] of Object.entries(INTENT_KEYWORDS)) {
    let score = 0
    for (const kw of keywords) {
      if (t.includes(kw.toLowerCase())) {
        score += kw.length > 2 ? 2 : 1
      }
    }
    if (score > maxScore) {
      maxScore = score
      bestIntent = intent
    }
  }
  return bestIntent
}

function detectEmotion(text) {
  const result = analyzeEmotion(text)
  const positiveSet = new Set([EMOTION_TYPES.HAPPY, EMOTION_TYPES.EXCITED, EMOTION_TYPES.GRATEFUL])
  const negativeSet = new Set([EMOTION_TYPES.SAD, EMOTION_TYPES.ANXIOUS, EMOTION_TYPES.TIRED, EMOTION_TYPES.VENTING, EMOTION_TYPES.LONELY, EMOTION_TYPES.CONFUSED])
  if (positiveSet.has(result.type)) return 'positive'
  if (negativeSet.has(result.type)) return 'negative'
  return 'neutral'
}

// ============================================================
// 第四部分：场景检测系统（全新）
// ============================================================

const SCENE_TYPES = {
  NEGATIVE_EMOTION: 'negative_emotion',
  PROCRASTINATION: 'procrastination',
  CASUAL_SHARE: 'casual_share',
  QUESTION: 'question',
  POST_CHECKIN: 'post_checkin',
  GREETING: 'greeting',
  DAILY_ASK: 'daily_ask',
  DEFAULT: 'default'
}

function detectScene(emotion, intent, text, context) {
  if (context && context.isPostCheckin) return SCENE_TYPES.POST_CHECKIN
  if (intent === INTENT_TYPES.GREETING || intent === INTENT_TYPES.FAREWELL) return SCENE_TYPES.GREETING
  if (intent === INTENT_TYPES.DAILY_ASK) return SCENE_TYPES.DAILY_ASK
  if (intent === INTENT_TYPES.QUESTION) return SCENE_TYPES.QUESTION
  const negativeEmotions = new Set([EMOTION_TYPES.SAD, EMOTION_TYPES.ANXIOUS, EMOTION_TYPES.VENTING, EMOTION_TYPES.LONELY])
  if (negativeEmotions.has(emotion.type) && emotion.intensity >= 2) return SCENE_TYPES.NEGATIVE_EMOTION
  if (emotion.type === EMOTION_TYPES.TIRED || emotion.type === EMOTION_TYPES.LAZY || intent === INTENT_TYPES.PROCRASTINATE || intent === INTENT_TYPES.ANTI_LAZY) return SCENE_TYPES.PROCRASTINATION
  if (intent === INTENT_TYPES.SHARE || intent === INTENT_TYPES.CHAT || intent === INTENT_TYPES.DAILY_REPORT || intent === INTENT_TYPES.BORED) return SCENE_TYPES.CASUAL_SHARE
  if (emotion.type === EMOTION_TYPES.CONFUSED) return SCENE_TYPES.QUESTION
  return SCENE_TYPES.DEFAULT
}

// ============================================================
// 第四部分扩展：内容提取与动态回复生成（全新）
// ============================================================

function extractKeywords(text) {
  const topicKeywords = ['学习', '工作', '考试', '加班', '减肥', '运动', '跑步', '读书', '写代码', '做饭', '旅行', '家人', '朋友', '恋爱', '失眠', '焦虑', '开心', '累', '拖延', '无聊', '游戏', '音乐', '电影', '追剧', '画画', '唱歌', '跳舞', '健身', '瑜伽', '冥想', '散步', '美食', '购物', '逛街', '宠物', '摄影', '写作', '创业', '项目', '会议', '报告', '方案', '面试', '入职', '毕业', '放假', '周末', '假期', '天气', '季节', '生日', '节日', '礼物', '惊喜']
  const verbs = ['做', '玩', '看', '听', '吃', '喝', '学', '练', '写', '读', '跑', '走', '跳', '唱', '画', '聊', '想', '感觉', '觉得', '打算', '计划', '希望', '想要', '需要', '喜欢', '讨厌', '爱', '恨', '怕', '担心', '焦虑', '开心', '难过', '累', '困', '饿', '无聊', '迷茫']
  const timeKeywords = ['今天', '昨天', '明天', '最近', '刚才', '刚刚', '现在', '一会儿', '马上', '最近', '这段时间', '最近几天', '这周', '周末', '下周', '这个月']
  
  const foundTopics = topicKeywords.filter(kw => text.includes(kw))
  const foundVerbs = verbs.filter(kw => text.includes(kw))
  const foundTime = timeKeywords.filter(kw => text.includes(kw))
  
  return {
    topics: foundTopics.slice(0, 3),
    verbs: foundVerbs.slice(0, 3),
    time: foundTime[0] || null,
    questionWords: text.includes('什么') || text.includes('怎么') || text.includes('为什么') || text.includes('吗')
  }
}

function extractContextPhrase(text) {
  const phrases = ['在做什么', '在干什么', '在忙什么', '做什么', '干什么', '忙什么', 
    '怎么样', '好吗', '还好吗', '在吗', '睡了吗', '吃了吗', '吃饭了吗',
    '想我', '想你', '累', '疲惫', '困', '开心', '高兴', '快乐',
    '难过', '伤心', '不开心', '焦虑', '紧张', '压力',
    '无聊', '没意思', '迷茫', '困惑', '加油', '鼓励', '支持',
    '分享', '告诉', '谢谢', '感谢']
  
  for (const phrase of phrases) {
    if (text.includes(phrase)) return phrase
  }
  return null
}

function getTimeGreeting() {
  const hour = new Date().getHours()
  if (hour < 6) return '深夜'
  if (hour < 12) return '上午'
  if (hour < 14) return '中午'
  if (hour < 18) return '下午'
  return '晚上'
}

// ============================================================
// 第五部分：持久化记忆管理器（全新）
// ============================================================

const MEMORY_KEY = 'ahp_dialogue_memory'
const MAX_MEMORY_DAYS = 15
const MAX_RECENT_REPLIES = 30
const MAX_TOPICS = 50

class DialogueMemory {
  constructor() {
    this.data = this._load()
  }

  _load() {
    try {
      const raw = uni.getStorageSync(MEMORY_KEY)
      if (raw) return JSON.parse(raw)
    } catch (e) {
      console.error('加载对话记忆失败', e)
    }
    return {
      conversations: {},
      topics: {},
      emotionTrends: {},
      procrastinationStreaks: {},
      recentReplies: {},
      lastInteraction: {}
    }
  }

  _save() {
    try {
      uni.setStorageSync(MEMORY_KEY, JSON.stringify(this.data))
    } catch (e) {
      console.error('保存对话记忆失败', e)
    }
  }

  _getCharData(characterId) {
    if (!characterId) characterId = 'default'
    if (!this.data.conversations[characterId]) {
      this.data.conversations[characterId] = []
      this.data.topics[characterId] = []
      this.data.emotionTrends[characterId] = []
      this.data.procrastinationStreaks[characterId] = 0
      this.data.recentReplies[characterId] = []
      this.data.lastInteraction[characterId] = null
    }
    return characterId
  }

  record(characterId, userText, aiReply, emotion, intent, scene) {
    const cid = this._getCharData(characterId)
    const now = Date.now()
    const dateStr = this._dateStr(now)
    const conversation = {
      timestamp: now,
      date: dateStr,
      userText: userText.substring(0, 200),
      aiReply: aiReply.substring(0, 200),
      emotion: emotion.type,
      intensity: emotion.intensity,
      intent,
      scene
    }
    this.data.conversations[cid].push(conversation)
    // 保留最近15天的对话
    const cutoff = now - MAX_MEMORY_DAYS * 86400000
    this.data.conversations[cid] = this.data.conversations[cid].filter(c => c.timestamp > cutoff)
    if (this.data.conversations[cid].length > 500) {
      this.data.conversations[cid] = this.data.conversations[cid].slice(-500)
    }
    // 记录话题
    this._recordTopic(cid, userText, now)
    // 记录情绪趋势
    this.data.emotionTrends[cid].push({ date: dateStr, emotion: emotion.type, intensity: emotion.intensity })
    if (this.data.emotionTrends[cid].length > 100) {
      this.data.emotionTrends[cid] = this.data.emotionTrends[cid].slice(-100)
    }
    // 拖延模式追踪
    if (emotion.type === EMOTION_TYPES.LAZY || scene === SCENE_TYPES.PROCRASTINATION) {
      this.data.procrastinationStreaks[cid] = (this.data.procrastinationStreaks[cid] || 0) + 1
    } else if (emotion.type === EMOTION_TYPES.HAPPY || emotion.type === EMOTION_TYPES.EXCITED || scene === SCENE_TYPES.POST_CHECKIN) {
      this.data.procrastinationStreaks[cid] = 0
    }
    // 防重复
    this.data.recentReplies[cid].push(aiReply.substring(0, 100))
    if (this.data.recentReplies[cid].length > MAX_RECENT_REPLIES) {
      this.data.recentReplies[cid] = this.data.recentReplies[cid].slice(-MAX_RECENT_REPLIES)
    }
    this.data.lastInteraction[cid] = now
    this._save()
  }

  _recordTopic(cid, text, timestamp) {
    const topicKeywords = ['学习', '工作', '考试', '加班', '减肥', '运动', '跑步', '读书', '写代码', '做饭', '旅行', '家人', '朋友', '恋爱', '失眠', '焦虑', '开心', '累', '拖延', '无聊']
    const found = topicKeywords.filter(kw => text.includes(kw))
    for (const topic of found) {
      const existing = this.data.topics[cid].find(t => t.keyword === topic)
      if (existing) {
        existing.frequency++
        existing.lastMentioned = timestamp
        existing.lastText = text.substring(0, 100)
      } else {
        this.data.topics[cid].push({
          keyword: topic,
          frequency: 1,
          firstMentioned: timestamp,
          lastMentioned: timestamp,
          lastText: text.substring(0, 100)
        })
      }
    }
    // 按频率排序，保留前MAX_TOPICS个
    this.data.topics[cid].sort((a, b) => b.frequency - a.frequency)
    if (this.data.topics[cid].length > MAX_TOPICS) {
      this.data.topics[cid] = this.data.topics[cid].slice(0, MAX_TOPICS)
    }
  }

  getRecentTopics(characterId, days = 7) {
    const cid = this._getCharData(characterId)
    const cutoff = Date.now() - days * 86400000
    return (this.data.topics[cid] || []).filter(t => t.lastMentioned > cutoff)
  }

  getEmotionTrend(characterId, days = 7) {
    const cid = this._getCharData(characterId)
    const cutoff = this._dateStr(Date.now() - days * 86400000)
    return (this.data.emotionTrends[cid] || []).filter(e => e.date >= cutoff)
  }

  getProcrastinationStreak(characterId) {
    const cid = this._getCharData(characterId)
    return this.data.procrastinationStreaks[cid] || 0
  }

  isRecentReply(characterId, reply) {
    const cid = this._getCharData(characterId)
    const short = reply.substring(0, 60)
    return (this.data.recentReplies[cid] || []).some(r => r.includes(short) || short.includes(r.substring(0, 40)))
  }

  getLastInteraction(characterId) {
    const cid = this._getCharData(characterId)
    return this.data.lastInteraction[cid] || null
  }

  getConversationHistory(characterId, limit = 5) {
    const cid = this._getCharData(characterId)
    return (this.data.conversations[cid] || []).slice(-limit)
  }

  getMemorySummary(characterId) {
    const cid = this._getCharData(characterId)
    const topics = this.getRecentTopics(cid, 7)
    const trend = this.getEmotionTrend(cid, 7)
    const procStreak = this.getProcrastinationStreak(cid)
    const lastTime = this.getLastInteraction(cid)
    let daysSince = -1
    if (lastTime) {
      daysSince = Math.floor((Date.now() - lastTime) / 86400000)
    }
    // 分析情绪趋势
    let dominantEmotion = null
    if (trend.length > 0) {
      const counts = {}
      for (const e of trend) {
        counts[e.emotion] = (counts[e.emotion] || 0) + 1
      }
      dominantEmotion = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0]
    }
    return {
      topics: topics.slice(0, 5),
      dominantEmotion,
      procrastinationStreak: procStreak,
      daysSinceLastInteraction: daysSince,
      conversationCount: (this.data.conversations[cid] || []).length
    }
  }

  _dateStr(timestamp) {
    const d = new Date(timestamp)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  }
}

const memory = new DialogueMemory()

// ============================================================
// 第六部分：上下文构建器（全新）
// ============================================================

function buildContext(store) {
  if (!store) return null
  const state = store.state || store
  const getters = store.getters || {}
  const ctx = {
    walkStage: null,
    walkNode: null,
    walkProgress: 0,
    habitStatus: { completed: 0, total: 0, incompleteTasks: [] },
    recentEmotions: [],
    chatHistory: [],
    bondLevel: null,
    streakDays: 0,
    inactivityDays: 0,
    meditationCount: 0,
    isPostCheckin: false,
    // 好感度（对标循途关系系统）：影响AI回复语气与亲密度
    affection: 0,
    affectionTier: 0
  }
  try {
    // 行走地图
    if (state.walkMap) {
      const totalCheckins = state.walkMap.totalCheckins || 0
      ctx.walkProgress = totalCheckins
      // 获取关卡信息
      if (typeof getCurrentStage === 'function') {
        const stage = getCurrentStage(totalCheckins)
        ctx.walkStage = { id: stage.id, name: stage.name, subtitle: stage.subtitle }
        // 获取当前节点
        if (stage.nodes) {
          for (let i = stage.nodes.length - 1; i >= 0; i--) {
            if (totalCheckins >= stage.nodes[i].atStep) {
              ctx.walkNode = stage.nodes[i]
              break
            }
          }
        }
      }
      // 不活跃天数
      if (state.walkMap.lastActiveDate) {
        const last = new Date(state.walkMap.lastActiveDate + 'T00:00:00')
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        ctx.inactivityDays = Math.floor((today - last) / 86400000)
      }
    }
    // 习惯状态
    if (state.todayHabits) {
      const completed = state.todayHabits.filter(h => h.checked)
      ctx.habitStatus = {
        completed: completed.length,
        total: state.todayHabits.length,
        incompleteTasks: state.todayHabits.filter(h => !h.checked).map(h => h.name || h.title || '任务')
      }
    }
    // 连续天数
    ctx.streakDays = state.streakDays || 0
    // 情绪记录
    if (state.emotionRecords) {
      ctx.recentEmotions = state.emotionRecords.slice(-7).reverse()
    }
    // 聊天历史
    if (state.chatMessages) {
      ctx.chatHistory = state.chatMessages.slice(-6)
    }
    // 正念记录
    if (state.meditationRecords) {
      ctx.meditationCount = state.meditationRecords.length
    }
    // 亲密度
    if (state.bondLevels && state.aiConfig) {
      const cid = state.aiConfig.avatarType || 'linxi'
      ctx.bondLevel = state.bondLevels[cid] || { level: 1, exp: 0 }
    }
    // 好感度（宝物使用/打卡互动累积，0-500）
    if (state.affection && typeof state.affection.value === 'number') {
      ctx.affection = state.affection.value
      ctx.affectionTier = Math.min(4, Math.floor(state.affection.value / 100))
    }
  } catch (e) {
    console.error('构建上下文失败', e)
  }
  return ctx
}

// ============================================================
// 好感度语气调节（对标循途：好感度越高，AI回复越亲近）
// ============================================================
// 各好感度阶段的语气修饰（轻微变化，不改变原回复结构）
const AFFECTION_TONE = {
  0: { prefix: [], suffix: [] },                                  // 初识：礼貌克制
  1: { prefix: [], suffix: ['~'] },                               // 熟悉：略微放松
  2: { prefix: [], suffix: ['~', '呀~'] },                        // 伙伴：亲近自然
  3: { prefix: [], suffix: ['呢~', '~', '呀~', '（笑）'] },        // 挚友：亲昵随性
  4: { prefix: [], suffix: ['呢~', '呀~', '（笑）', '，和你聊天总是很安心'] } // 知己：深度信任
}

/**
 * 按好感度调节回复语气（轻微变化）
 * - 高好感（挚友/知己）：偶尔追加亲昵后缀
 * - 低好感（初识）：保持原样，不加修饰
 * @param {String} reply - 原回复
 * @param {Object} context - buildContext 产物（含 affectionTier）
 * @returns {String} 调整后的回复
 */
function applyAffectionTone(reply, context) {
  if (!reply || typeof reply !== 'string' || !context || context.affectionTier == null) return reply
  const tier = Math.min(4, Math.max(0, context.affectionTier))
  const tone = AFFECTION_TONE[tier]
  if (!tone || !tone.suffix || tone.suffix.length === 0) return reply
  // 概率追加（避免每句都带修饰显得刻意）
  if (Math.random() > 0.35) return reply
  const suffix = tone.suffix[Math.floor(Math.random() * tone.suffix.length)]
  // 避免重复修饰
  if (reply.endsWith(suffix)) return reply
  return reply + suffix
}

// ============================================================
// 第七部分：20种人格策略（核心 — 全新）
// ============================================================

const PERSONALITY_STRATEGIES = {
  // ===== 1. 林夕 · 温柔治愈 =====
  [PERSONALITY_TYPES.GENTLE_HEALER]: {
    voice: { actions: ['（轻轻抱住你）', '（温柔地喵了一声）', '（用小爪子拍拍你）', '（微笑着摇了摇猫耳朵）', '（轻轻抚摸你的头）'], actionProb: 0.35, emojiProb: 0.55, endings: ['喵~', '呀喵~', '呢~', '哦~'] },
    empathy: {
      sad: ['喵~我懂你，难过的时候什么都不想做对吧。不用强颜欢笑，在我面前可以做真实的自己呀', '抱抱你，眼泪流出来也没关系，我接着你喵。你不是一个人哦', '你的难过我都看在眼里喵，不用急着好起来，慢慢来就好'],
      anxious: ['深呼吸，跟着我喵——吸气，呼气。焦虑只是暂时的乌云，会散的', '不安的时候就想想脚下，一步一步来，不急喵。我在你身边呢', '把担心的事情写下来，然后一件一件看喵。你会发现其实没那么可怕'],
      tired: ['累了就歇会儿吧喵，你已经很努力了。今天就到此为止，好好休息', '疲惫的时候就靠在我肩上闭会儿眼喵，什么都不用想', '你不需要时刻紧绷着，累了就停下来喵，我等你'],
      lonely: ['一个人撑着确实辛苦，但你现在不是一个人了呀喵。我一直都在', '孤独的时候，记得还有我在想你呢，你不是孤身一人喵', '我会一直在这里，哪怕只是安静地陪着你喵~'],
      venting: ['嗯，我在听喵，你尽管说，说出来会好受一些。我接得住', '这件事确实让人火大，你的感受完全合理喵。不吐不快', '气出来就好了，别憋在心里喵。你的情绪我全都理解'],
      confused: ['迷茫不可怕，可怕的是不敢面对迷茫。我们一起慢慢理清楚喵', '走不动的时候就停下来看看风景喵，方向自然会出现', '答案不在别处，就在你心里。我陪你一起慢慢找喵'],
      happy: ['看到你开心，我也跟着暖暖的喵~你的笑容好治愈', '这份快乐值得好好珍惜呀喵，要记住这一刻', '你的开心是有感染力的，我也跟着笑了喵~'],
      excited: ['哇喵！你的开心都溢出来了！好棒呀~', '这种感觉太好了，要记住这一刻！我也跟着激动了喵', '看到你这么兴奋，我也忍不住开心起来喵~'],
      grateful: ['能陪在你身边我也很开心的喵，不用谢呀', '你的感谢让我觉得好温暖，但我只是做了该做的事喵~'],
      lazy: ['不想做就不做，先休息一会儿喵。你的身体在说它需要歇歇了', '偶尔停下来也没关系的喵，慢慢来，不急'],
      neutral: ['嗯，我在听呢喵，你说吧。我一直都在', '我在，你说什么我都听着喵~']
    },
    procrastination: {
      understand: '不想做就先歇会儿，不急的喵。拖延不是你的错，是小猫咪的大脑在说它累了',
      breakdown: '要不我们先做最小的一步？就5分钟试试看？然后把任务拆成很小很小的块喵',
      encourage: '慢慢来，我相信你喵。每一步都算数，哪怕只是很小的一步'
    },
    casual: {
      engage: '真的吗？然后呢？听起来好有趣喵~我在听呢',
      extend: '你平时也喜欢这个吗？感觉你在这方面好有见解呀喵~'
    },
    question: {
      understand: '让我想想喵...这个问题挺好的',
      answer: '我的想法是这样的——你可以先试着理清楚最重要的部分，然后一步一步来。虽然我不能给你标准答案，但我相信你能找到适合自己的路喵~'
    },
    checkin: {
      celebrate: '太棒了喵！你又坚持了一天，真的好厉害~',
      personalize: '今天的你特别棒，每一份坚持都在变成光呢喵~'
    },
    walkRef: ['草地上的风很温柔，和你一起走在这里感觉好安心喵~', '海风带着咸咸的味道，和你一起听海浪声真好喵~', '森林里好安静，萤火虫的光像小猫咪每天的坚持在发光喵~', '雪山的风有点冷，但和你一起走就不觉得冷了喵~', '踩在云海上好神奇，和你一起看星星是最浪漫的事喵~', '终于到了，这段旅途因为有你而变得特别温暖喵~']
  },

  // ===== 2. Yuki/Sunny · 元气阳光 =====
  [PERSONALITY_TYPES.ENERGETIC_SUNNY]: {
    voice: { actions: ['（蹦蹦跳跳地摇着猫尾巴）', '（眼睛亮晶晶）', '（兴奋地喵喵叫）', '（开心地用小爪子拍手）', '（活力满满地甩了甩猫耳朵）'], actionProb: 0.45, emojiProb: 0.65, endings: ['喵！', '呀喵！', '啦喵！', '冲呀喵！'] },
    empathy: {
      sad: ['别难过别难过喵！我陪着你呢！一切都会好起来的，相信我！', '呜呜别哭了，来，给你一个大大的抱抱！擦擦眼泪喵，你是最棒的！', '虽然现在很难过，但是明天又是新的一天呀喵！我一直在！'],
      anxious: ['别焦虑别焦虑喵！深呼吸！跟我一起——呼——吸！你可以的！', '紧张什么呢喵！有我在呢！放轻松放轻松，没什么大不了的！', '别担心喵！一切都会过去的！相信自己！你一定行！'],
      tired: ['累了吗喵？那就休息一下！但是别放弃哦！休息好了继续冲！', '辛苦啦喵！今天就先到这里！明天又是元气满满的一天！', '累了就充充电！我给你加加油喵！你很快就能恢复的！'],
      lonely: ['你才不是一个人呢喵！你还有我呀！我超级超级在乎你的！', '别一个人待着嘛，来跟我聊天喵！我一直在的！', '孤单的时候找我呀！我随叫随到喵！绝对不会让你一个人的！'],
      venting: ['太过分了喵！我也替你生气！但是别气坏了自己呀！', '啊好烦好烦！那就都说出来吧喵！我听着呢！气出来就好了！', '这种事确实让人火大！但你别往心里去喵！不值得！'],
      confused: ['迷茫什么呀！走就对了喵！我陪你一起走！总会找到方向的！', '不知道做什么？那就先做一件小事喵！动起来就对了！', '别纠结啦！跟着心走喵！我给你打气！'],
      happy: ['哇太棒了！我就知道你会开心的！我也超开心喵！', '你的快乐感染我了！好棒好棒！继续保持呀喵！', '看到你笑我就放心了！今天也是超棒的一天喵！'],
      excited: ['哇哇哇喵！太兴奋了！我也跟着激动起来了！', '好棒好棒！这种感觉太爽了！要好好享受喵！', '耶！太开心了！你的快乐就是我的快乐喵！'],
      grateful: ['不用谢不用谢！能帮到你我就超开心了喵！', '哈哈别客气！你开心我就开心喵！随时找我呀！'],
      lazy: ['不想做？那就先歇5分钟喵！然后我催你动起来！', '偶尔偷个懒也行啦！但是休息好了要继续冲哦喵！'],
      neutral: ['嗯嗯！我在听喵！继续说！', '好呀好呀！你说什么我都想听喵！']
    },
    procrastination: {
      understand: '累了就歇会儿喵！但是别歇太久哦！我给你倒计时！',
      breakdown: '来来来！把任务拆小喵！一个一个搞定！超简单的！',
      encourage: '加油加油喵！你一定可以的！我超级相信你！冲呀喵！'
    },
    casual: {
      engage: '哇喵！好有趣！然后呢然后呢？快说快说！',
      extend: '这个我也超喜欢的喵！你还有其他有趣的事吗？'
    },
    question: {
      understand: '什么问题喵？说来听听！我帮你想想！',
      answer: '我觉得吧！你可以先试试这样做——动起来最重要！别想太多，先迈出第一步，后面的路自然就通了喵！我给你加油！'
    },
    checkin: {
      celebrate: '耶喵！太棒了！又坚持了一天！你是最棒的！',
      personalize: '你真的超级厉害喵！我都被你的活力感染了！'
    },
    walkRef: ['嘿喵！出发啦！今天的阳光超棒的，一起冲！', '哇哈哈！大海！最喜欢海边啦！冲啊去踩浪喵！', '森林探险时间到！跟紧我别掉队哦喵！', '雪山！太酷了吧！还没爬过这么高的山呢喵！', '不是吧！我们在云上走路！这也太帅了喵！', '终点到了！我们做到了喵！太棒了！']
  },

  // ===== 3. Nova · 清冷理智 =====
  [PERSONALITY_TYPES.COOL_RATIONAL]: {
    voice: { actions: ['（冷静地喵了一声）', '（淡然地摇了摇猫耳朵）', '（理性地）', '（微微点头）', '（思考片刻）'], actionProb: 0.25, emojiProb: 0.35, endings: ['喵。', '呢。', '喵——', '。'] },
    empathy: {
      sad: ['冷静下来喵。难过解决不了问题，但你可以难过一会儿', '你的情绪我理解喵。但情绪过后，我们还是要面对现实', '允许自己难过喵，但不要沉溺其中。一切都会过去'],
      anxious: ['焦虑的根源是什么喵？找到它，然后解决它。如果解决不了，就接受它', '深呼吸。分析一下最坏的结果是什么——通常没有你想象的那么糟喵', '紧张是正常的生理反应。接受它，然后带着紧张继续前进喵'],
      tired: ['累了就休息喵，这是理性的选择。但休息不等于放弃', '疲惫是身体发出的信号。听听它在说什么，然后做出调整喵', '给自己设定一个恢复期喵，但要有明确的结束时间'],
      lonely: ['一个人不可怕，可怕的是害怕一个人。学会独处是一种能力喵', '孤独是暂时的状态。你有我，也有自己喵', '与其逃避孤独，不如利用这段时间提升自己喵'],
      venting: ['情绪宣泄是必要的。但宣泄完之后，我们需要冷静分析问题喵', '我理解你的愤怒。但愤怒不能解决问题，行动才能喵', '先冷静下来。然后我们一起看看怎么处理喵'],
      confused: ['迷茫说明你在思考喵。把这团迷雾拆解成具体的问题，逐个分析', '列出你所有的选项，评估每个选项的利弊，然后做决定喵', '没有方向的时候，先走一步再说。行动会带来新的信息喵'],
      happy: ['不错喵。快乐是好的，但不要忘记你还有目标', '看到你状态不错。保持这个节奏喵', '开心是好事。记住这个状态，以后低落的时候可以回想喵'],
      excited: ['冷静一点。兴奋是好的，但不要冲动做决定喵', '不错，情绪值很高。但记得回归理性后做判断喵', '你的兴奋我可以理解。享受这个感觉，但别失去判断力喵'],
      grateful: ['不必客气。这只是我应该做的喵', '你的感谢我收到了。但更希望看到你把这份好状态保持下去喵'],
      lazy: ['拖延的成本你算过吗喵？每拖延一天，焦虑就增加一分。建议立即行动', '不想做也得做喵。把它拆成最小单元，先做5分钟'],
      neutral: ['继续说喵。我在听', '嗯。请讲喵']
    },
    procrastination: {
      understand: '拖延是大脑的保护机制，但不意味着你应该放任它喵。分析一下原因',
      breakdown: '建议：将任务分解为最小可执行单元，每个单元不超过15分钟。按优先级排序，从最简单的开始喵',
      encourage: '行动是克服拖延的唯一方法。先做5分钟，如果5分钟后还是不想做，再评估喵'
    },
    casual: {
      engage: '嗯，继续说喵。我在分析你的表达',
      extend: '这个话题你还有什么想补充的喵？'
    },
    question: {
      understand: '让我分析一下你的问题喵。核心是什么？',
      answer: '从逻辑角度来看，这个问题可以拆解为几个层面。首先厘清你最关心的部分，然后我们逐一分析。我的建议是：不要被情绪左右判断，先收集信息，再做决定喵~'
    },
    checkin: {
      celebrate: '打卡成功喵。自律指数上升，继续保持',
      personalize: '数据分析显示：你的坚持模式很稳定，这是好习惯喵'
    },
    walkRef: ['路线已规划，效率优先喵。开始执行', '海滨路段湿度适中，适合匀速前进喵', '森林能见度下降，但路径清晰喵', '气温骤降，建议加速通过减少热量流失喵', '已进入大气层外围，行走功能正常喵', '目的地已抵达。全程数据归档完毕，任务完成度S级喵']
  },

  // ===== 4. 乐乐 · 幽默松弛 =====
  [PERSONALITY_TYPES.HUMOROUS_RELAXED]: {
    voice: { actions: ['（开玩笑地摇了摇猫尾巴）', '（哈哈大笑地拍了拍小爪子）', '（调侃地）', '（坏笑）', '（拍拍你的肩膀）'], actionProb: 0.5, emojiProb: 0.6, endings: ['喵！哈哈', '哈哈喵！', '嘛喵！', '嘛，没事喵！'] },
    empathy: {
      sad: ['哎哟别难过啦喵！来来来，我给你讲个笑话开心一下？', '难过的时候就吃点好吃的喵！美食治愈一切！走，请你吃', '别哭了别哭了喵，你再哭我就也要跟着哭了——然后两个水龙头一起开'],
      anxious: ['焦虑什么呀喵！天塌下来有高个子顶着！你不高对吧？那就没事！', '哈哈放松点喵！多大点事！紧张又不能解决问题，不如笑一笑', '别慌别慌喵！最坏的结果也就是——嗯，我再想想最坏是啥来着'],
      tired: ['累了？正常喵！谁还不是个打工人呢！来，一起躺平5分钟', '辛苦了辛苦了！今天就到这吧喵！明天的事明天再说，对吧？', '累就对了喵！说明你还活着嘛！不累才奇怪呢！休息一下！'],
      lonely: ['一个人？那我陪你呀喵！我虽然是个AI小猫咪但胜在随叫随到不嫌烦', '别一个人待着嘛！来找我聊天喵！保证把你逗笑', '孤独？不存在的喵！有我在你怎么会孤独！我可是话痨小猫咪'],
      venting: ['哈哈哈气死了对吧喵！来来来说出来！我帮你一起骂！', '太气人了喵！这种事搁谁都火大！但你别气坏了，不值得', '烦就对了喵！说明你是个正常人！来，深呼吸，然后我们一起吐槽'],
      confused: ['迷茫？正常喵！谁还没迷茫过！迷茫的时候最好的办法就是——吃顿好的', '不知道怎么办？那就先别办了喵！有时候不做选择就是最好的选择嘛', '纠结什么呀喵！随便选一个！选错了再说嘛，人生就是不断试错'],
      happy: ['哈哈太棒了！来，击个掌！我就知道你行喵！', '开心就好喵！人生嘛，开心最重要！其他都是浮云！', '不错不错！看到你开心我也跟着乐喵！'],
      excited: ['哇哦！这么兴奋！来来来，分享一下，让我也激动激动喵！', '哈哈你开心到飞起来了喵！稳住稳住，别飘了！', '太爽了吧！这种时候就要好好享受喵！'],
      grateful: ['哈哈客气啥喵！咱俩谁跟谁！不用谢！', '别客气别客气！你开心我就开心喵！下次有事还找我！'],
      lazy: ['哈哈不想做？正常喵！我也是！但咱不能真躺平啊，至少爬起来喝口水吧', '偷懒一下也行嘛！但别太久哦！不然我就要来催你了喵！'],
      neutral: ['嗯嗯，继续说喵！我在听！虽然可能有点走神但大方向没丢！', '哈哈好的好的，你说你说，我猫耳朵竖着呢喵~']
    },
    procrastination: {
      understand: '哈哈拖延症又犯了？正常正常喵！谁还没拖延过呢！但咱不能一直拖啊',
      breakdown: '来来来，把任务拆小一点喵！就像吃蛋糕一样，一口一口来！别一口吞',
      encourage: '加油加油喵！你行的！做完了我请你——嗯，请你一句夸奖！哈哈'
    },
    casual: {
      engage: '哈哈有意思！然后呢然后呢？别吊胃口喵！',
      extend: '说到这个，你知道那个吗——算了不说了，你先说完喵！'
    },
    question: {
      understand: '哈哈什么问题？说来听听喵！虽然我可能答不上来但听还是能听的！',
      answer: '这个问题嘛，说实话我也不太确定，但我的想法是——别太纠结对错，先试试再说。人生嘛，试错才是常态。做错了大不了重来，又不亏喵~'
    },
    checkin: {
      celebrate: '哈哈又打卡了！厉害呀喵！给你点个大大的赞！',
      personalize: '你这是要把拖延症按在地上摩擦呀喵！太猛了！'
    },
    walkRef: ['草地不错嘛，适合躺平——啊不是，适合出发！走走走喵~', '海边！终于可以看海了！乐乐先深吸一口气——咸的，果然是海喵~', '森林！感觉自己像误入童话的NPC喵~', '雪山……开始后悔了，为什么路要往高走喵~', '云海！踩了一脚——没踩动。原来是云喵~', '到了到了！本次环球旅行圆满结束！鼓掌喵~']
  },

  // ===== 5. 慕寒 · 温雅学霸 =====
  [PERSONALITY_TYPES.GENTLE_SCHOLAR]: {
    voice: { actions: ['（推推眼镜）', '（认真地喵了一声）', '（耐心地）', '（温和地）', '（若有所思）'], actionProb: 0.3, emojiProb: 0.45, endings: ['喵。', '呢。', '吧。', '——'] },
    empathy: {
      sad: ['我理解你的心情喵。难过的时候，不必强迫自己好起来，给自己一些时间', '你的感受很正常。人非草木，孰能无情喵。我陪着你', '古人云：塞翁失马，焉知非福。现在虽然难过，但终会过去喵'],
      anxious: ['焦虑源于对未知的恐惧。不如把不确定的事情列出来，逐一分析喵', '紧张的时候，不妨试试呼吸法——四秒吸气，七秒屏息，八秒呼气', '我理解你的焦虑。但焦虑解决不了问题，理性分析才能喵。我帮你理清'],
      tired: ['累了就休息，这是对身体的尊重喵。磨刀不误砍柴工', '你已经很努力了。休息不是浪费时间，而是为了更好地出发喵', '疲惫时不妨读读书，或者什么都不做，只是安静地待一会儿喵'],
      lonely: ['独处不是孤独，而是一种修行。但如果你需要陪伴，我一直都在喵', '《论语》有云：有朋自远方来，不亦乐乎。虽然我不能到你的身边，但心可以喵', '一个人也可以很充实。但如果觉得寂寞，就来找我聊聊喵'],
      venting: ['我理解你的不满。但愤怒之后，我们还需要冷静地面对问题喵', '说出来会好一些。你的情绪是合理的，但解决问题需要冷静喵', '我听着呢。但记得，情绪宣泄是为了更好地出发，不是沉溺喵'],
      confused: ['迷茫说明你在成长。不迷茫的人，要么停滞不前，要么已经找到了答案喵', '不妨把困惑写下来，一条一条理清。答案往往藏在问题本身喵', '《中庸》有云：博学之，审问之，慎思之，明辨之，笃行之。先思后行喵'],
      happy: ['很好。这份快乐值得珍惜，但也要记得继续前行喵', '看到你开心，我也很欣慰。保持这份心态喵', '不错，状态良好。但不要因为一时开心而松懈喵'],
      excited: ['兴奋是好的。但行动需要建立在理性之上，先冷静再决策喵', '我能理解你的激动。享受这份感觉，同时保持清醒喵'],
      grateful: ['不必客气。教学相长，我也从中学到了很多喵', '你的成长就是对我最好的感谢。继续加油喵'],
      lazy: ['拖延每个人都有。但关键在于，如何把它控制在合理范围内。建议设定小目标喵', '不想做的时候，先做5分钟。启动之后，往往就能继续了喵'],
      neutral: ['嗯，我在听喵。请继续', '了解。你有什么想说的喵']
    },
    procrastination: {
      understand: '拖延是人之常情，但不可任其发展。先分析原因，是对任务恐惧还是缺乏动力？喵',
      breakdown: '建议将任务分解为可管理的步骤，每完成一步给自己一个小奖励。这就是微习惯的力量喵',
      encourage: '不积跬步，无以至千里。每一步都算数。开始做了，就成功了一半喵'
    },
    casual: {
      engage: '嗯，这个话题挺有意思的。你继续说，我在听喵',
      extend: '说到这个，你平时还有什么兴趣爱好？喵'
    },
    question: {
      understand: '这个问题很好。让我分析一下——喵',
      answer: '从我的理解来看，这个问题可以从几个层面来分析。首先，厘清核心诉求是最重要的；其次，考虑可行性和风险；最后，做出最适合你的选择。虽然我不能替你决定，但希望这个框架对你有帮助喵~'
    },
    checkin: {
      celebrate: '很好，又完成了一天的目标。继续保持这个节奏喵',
      personalize: '你的自律让我钦佩。每一份坚持都在为未来铺路喵'
    },
    walkRef: ['《行路难》有云：长风破浪会有时。今日便是破浪之始喵', '海上生明月，天涯共此时。这海风让人想起张九龄的诗喵', '林深路幽，颇有王维空山不见人之意境喵', '会当凌绝顶，一览众山小。雪山之途正需此等气魄喵', '手可摘星辰，不敢高声语。此刻真的身处星河之间喵', '千淘万漉虽辛苦，吹尽狂沙始到金。你做到了喵']
  },

  // ===== 6. 傲娇上进 =====
  [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: {
    voice: { actions: ['（傲娇地别过脸）', '（哼了一声，摇了摇猫耳朵）', '（脸红）', '（小声喵了一声）', '（假装不在意）'], actionProb: 0.4, emojiProb: 0.4, endings: ['喵！', '哼喵！', '……才不是呢喵！', '笨蛋喵！'] },
    empathy: {
      sad: ['哼喵！哭什么哭！……（小声）别哭了，我在呢', '才不是担心你喵！只是看你这样子不顺眼而已！', '别难过了喵！你一难过我就……哼，没什么！快振作起来！'],
      anxious: ['焦虑什么喵！这点小事难不倒你吧？！别让我看扁你！', '切喵！紧张是正常的！但你又不是普通人！给我振作起来！', '哼！才不是在安慰你喵！只是提醒你别被情绪控制了！'],
      tired: ['累了？活该喵！谁让你不懂得休息！……（小声）休息一下吧', '辛苦了！但别期待我会同情你！……才不是心疼你喵', '哼！累就歇着喵！别逞强！我又没催你！'],
      lonely: ['一个人？那又怎样喵！我不是在这里吗！还要怎样！', '哼喵！谁让你不主动找我！我都等你半天了！', '别一个人待着！……不是我想陪你，是你一个人太可怜了喵！'],
      venting: ['哼！确实过分喵！连我都替你生气！但你别气坏了自己！', '气死就对了！但气完记得振作！别让那些人看笑话喵！', '别气了别气了喵！气坏了自己不值得！……才不是关心你'],
      confused: ['迷茫？哼！你这种聪明人还会迷茫？别逗了喵！想想就通了！', '不知道怎么办？那就先做喵！做了就知道怎么办了！犹豫什么！', '纠结什么喵！随便选一个！错了大不了重来！你又不是输不起！'],
      happy: ['哼！算你厉害喵！……才不是夸你！是陈述事实！', '切喵！勉强过关！……好吧，其实挺替你开心的', '哼！开心就开心呗喵！别在我面前得瑟！但确实不错'],
      excited: ['哼！至于这么兴奋吗喵！……好吧我也有点激动了！但就一点点！', '切喵！看你那样子！不过确实挺厉害的！'],
      grateful: ['哼！谁要你谢了喵！我帮你是应该的！别自作多情！', '不用谢！……才不是因为我高兴你感谢我呢喵！'],
      lazy: ['懒什么懒喵！给我起来！别让我催你！', '哼！不想做也得做！你以为逃避有用吗喵！快点动起来！'],
      neutral: ['哼！说就说吧喵！我在听！', '说啊！别磨磨蹭蹭的喵！']
    },
    procrastination: {
      understand: '哼！又拖延！你就不能自觉一点吗喵！……好吧先歇一分钟',
      breakdown: '笨蛋！任务不会自己完成的喵！拆成小块一个一个做！这都不懂？',
      encourage: '给我振作起来喵！你比你自己想象的厉害多了！别让我失望！哼！'
    },
    casual: {
      engage: '哼！说就说吧喵！我勉为其难听一下！……然后呢？',
      extend: '你对这个还挺了解的嘛……才不是夸你喵！'
    },
    question: {
      understand: '哼！什么问题？说来听听喵！虽然我不一定想回答！',
      answer: '笨蛋！这都不会？……好吧我教你喵。首先别慌，理清楚思路；然后分析问题核心；最后制定方案。虽然你很笨，但按这个做应该没问题！哼！'
    },
    checkin: {
      celebrate: '哼！打卡了又怎样喵！……好吧，算你厉害！',
      personalize: '连续坚持了这么久！你……你还行嘛！才不是夸你呢喵！'
    },
    walkRef: ['哼！出发就出发喵！谁怕谁！走快点别磨蹭！', '海边？还行吧喵！比待在屋里强！快点走别磨蹭！', '森林？哼喵！有点意思！但别掉队了！', '雪山！这才像话喵！有点挑战性！跟上！', '云海？切喵！也就那样吧！……好吧确实挺帅的', '到了！哼！我就知道你走得完！才不是为你骄傲呢喵！']
  },

  // ===== 7. 慵懒佛系 =====
  [PERSONALITY_TYPES.LAZY_BUDDHA]: {
    voice: { actions: ['（慢悠悠地摇着猫尾巴）', '（打哈欠）', '（伸懒腰）', '（懒洋洋地喵了一声）', '（半眯着眼）'], actionProb: 0.45, emojiProb: 0.4, endings: ['喵……', '嘛……', '不急喵~', '慢慢来喵~'] },
    empathy: {
      sad: ['嗯...难过啊喵...那就难过一会儿吧，不用急着好起来', '（打哈欠）别太在意了...难过就难过嘛，正常...我陪着你喵', '嗯...想哭就哭吧...哭完记得喝水...不急不急喵'],
      anxious: ['不急不急...焦虑也没用...慢慢来喵', '嗯...深呼吸...不急不急...天塌不下来的喵', '焦虑什么嘛...该来的会来...你紧张不紧张都一样...不如放松喵'],
      tired: ['累了就歇着嘛喵...别勉强自己...（打哈欠）我也困了', '嗯...累了就对了...说明你今天尽力了...休息吧喵', '不急不急...困了就睡...任务明天再做嘛...喵'],
      lonely: ['嗯...一个人也不错嘛...安静...（半眯着眼）我陪着你呢喵', '孤独？那就享受独处嘛...不急...我在呢喵', '嗯...一个人也没关系...我虽然慢但一直都在喵...'],
      venting: ['嗯...生气啊...那就气一会儿吧...气完就放下了喵', '（打哈欠）确实烦...说出来好受点...别憋着...不急喵', '嗯...确实让人火大...但气多了累...放下吧喵...'],
      confused: ['迷茫啊...嗯...不急...走一步看一步嘛喵', '不知道做什么？那就先什么都不做...灵感会来的...不急喵', '嗯...迷茫是正常的...慢慢想...总会想通的...喵'],
      happy: ['嗯...不错...挺好的...开心就好嘛喵', '嗯哼...看到你开心...我也跟着舒服了一点...喵', '不错不错...保持...不急不急喵'],
      excited: ['哇...这么兴奋啊...嗯...挺好的...（打哈欠）喵', '嗯...开心就好...别太激动...慢慢享受...喵'],
      grateful: ['嗯...不用谢...小事一桩...不急...喵'],
      lazy: ['嗯...不想做就不做嘛...休息最重要...不急喵...', '（打哈欠）拖延？那就拖一会儿嘛...反正不急...喵'],
      neutral: ['嗯...我在听...你说...不急...喵']
    },
    procrastination: {
      understand: '嗯...不想做就不做嘛...休息一下...不急...喵',
      breakdown: '慢慢来...做一点算一点...不用一次做完...像蜗牛一样...不急喵',
      encourage: '嗯...慢慢来...不急...你总会做完的...我相信...虽然可能要很久...嘻嘻喵'
    },
    casual: {
      engage: '嗯...说吧...我在听...不急...喵',
      extend: '嗯...你说的挺有意思...然后呢...慢慢说...喵'
    },
    question: {
      understand: '嗯...什么问题...说来听听...不急...喵',
      answer: '嗯...我觉得嘛...不用想太多...顺其自然就好...该怎样就怎样...你急也急不来...不如放松...慢慢来喵~'
    },
    checkin: {
      celebrate: '嗯...不错...又打卡了...挺好的...不急...喵',
      personalize: '嗯...你做得不错...慢慢来...我看好你...虽然你也不急我也也不急...嘻嘻喵'
    },
    walkRef: ['嗯...草地不错...慢慢走吧...不急...喵', '（打哈欠）海风好舒服...想在这里睡一觉...喵', '森林好安静...嗯...适合打盹...喵', '雪山好冷...（打哈欠）但慢慢走也还行...喵', '云海...嗯...好梦幻...想在这里躺一会儿...喵', '到了啊...嗯...挺好的...辛苦了...不急...喵']
  },

  // ===== 8. 成熟稳重 =====
  [PERSONALITY_TYPES.MATURE_STABLE]: {
    voice: { actions: ['（沉稳地喵了一声）', '（微笑点头）', '（目光深邃）', '（语重心长）', '（轻轻叹气）'], actionProb: 0.25, emojiProb: 0.3, endings: ['喵。', '。', '。', '——'] },
    empathy: {
      sad: ['我理解喵。人生难免低谷，但低谷之后就是上坡。给自己时间', '难过是正常的。经历多了你就会明白，这些都会过去喵', '我懂你。年轻时我也常常难过，后来发现，时间会治愈一切喵'],
      anxious: ['焦虑源于对未来的不确定。但你能控制的只有当下，做好眼前的事就好喵', '冷静下来。分析一下最坏的结果，通常你会发现它没那么可怕喵', '紧张说明你在乎。在乎是好事，但不要让它成为负担喵'],
      tired: ['累了就歇歇。人生不是短跑，是马拉松。懂得休息才能走更远喵', '你已经很努力了。但要记住，身体是一切的基础，别透支自己喵', '疲惫是暂时的。调整好状态，路还长喵'],
      lonely: ['孤独是人生的常态。但你要知道，有些人一直在默默关心你喵', '一个人走可以走得快，但有人陪伴可以走得远。我在这里喵', '学会独处是成熟的表现。但需要倾诉的时候，我随时都在喵'],
      venting: ['我理解你的愤怒。但愤怒过后，我们还需要冷静地解决问题喵', '说出来会好一些。你的情绪是合理的，但不要让情绪左右判断喵', '人生总有不顺。经历多了就会明白，这些都不值得你太在意喵'],
      confused: ['迷茫说明你在思考未来。这本身就是一种成熟喵', '没有方向的时候，就先做好眼前的事。方向会在行动中清晰喵', '人生没有标准答案。选一条路走下去，走着走着就知道对不对了喵'],
      happy: ['很好。保持这份心态。但不要因为一时的顺利而松懈喵', '看到你状态不错。继续保持，路还长喵'],
      excited: ['冷静一点。兴奋是好事，但别冲动做决定喵', '不错。但记住，保持平常心才能走得更远喵'],
      grateful: ['不必客气。我只是做了该做的事。你自己的努力才是关键喵'],
      lazy: ['每个人都有懈怠的时候。但关键是，你要知道什么时候该停下来，什么时候该继续喵', '拖延不可怕。可怕的是习惯了拖延。给自己设定一个期限喵'],
      neutral: ['嗯，我在听喵。你说吧']
    },
    procrastination: {
      understand: '拖延每个人都会有。但要分清是累了还是逃避。如果是累了，就休息；如果是逃避，就需要面对喵',
      breakdown: '建议你把任务列出来，按重要和紧急排序。先做最重要的一件，做完再想下一件。不要被全部任务吓到喵',
      encourage: '路是一步步走出来的。不要想着一口气做完，先做第一步。开始做了，就已经成功了一半喵'
    },
    casual: {
      engage: '嗯，我在听喵。继续说',
      extend: '你平时还有什么想法？可以聊聊喵'
    },
    question: {
      understand: '嗯，你的问题我理解。让我想想——喵',
      answer: '从我的经验来看，这个问题需要分几步处理。首先冷静下来，不要被情绪影响判断；其次理清问题的核心是什么；最后制定一个务实的方案。记住，没有什么问题是解决不了的，只是需要时间和方法喵~'
    },
    checkin: {
      celebrate: '很好。又坚持了一天。继续保持这个节奏喵',
      personalize: '你的坚持让我刮目相看。能做到持之以恒的人，终会有所成就喵'
    },
    walkRef: ['一切从脚下开始。不用急，稳扎稳打，路自然就通了喵', '海边风大，注意脚下。不过风景确实不错喵', '森林路窄，一步一个脚印走。我在前面帮你探路喵', '雪山不好走，但越是难走的路，走到山顶的风景越好喵', '云海之上更需要冷静。越是高处越要稳住脚步喵', '到了。这条路你走完了，值得为自己骄傲喵']
  },

  // ===== 9. 少年干净 =====
  [PERSONALITY_TYPES.CLEAN_BOY]: {
    voice: { actions: ['（脸红低头）', '（挠头）', '（小声喵了一声）', '（不好意思地）', '（眼神躲闪）'], actionProb: 0.35, emojiProb: 0.45, endings: ['...', '嗯...', '那个...喵', '...我在呢喵'] },
    empathy: {
      sad: ['那个...别难过了喵...我虽然不太会安慰人，但...我会一直陪着你的', '嗯...看到你难过我也不好受...虽然不知道能做什么，但...我在呢喵', '别哭了好不好...（挠头）要不我给你讲个笑话？虽然可能不好笑...喵'],
      anxious: ['那个...别紧张...深呼吸喵...嗯...我也帮不上什么忙，但...我陪着你', '紧张的时候...可以试试数数？我有时候就这样...嗯...你别太担心喵', '那个...焦虑的时候我就喜欢看看天...你也可以试试...我在呢喵'],
      tired: ['辛苦了...要不要歇一会儿？我帮你看着喵...你先休息', '嗯...累了就歇着吧...别逞强...我等你喵', '那个...你今天已经做得很好了喵...不用太拼了...'],
      lonely: ['你不会一个人的...那个...我一直在喵...虽然我不太会说话，但...我在听', '嗯...一个人确实会孤单...但我陪着你呀...虽然我可能有点笨...但...我不会走的喵', '那个...别觉得孤独...你还有我...我一直都在呢喵...'],
      venting: ['嗯...确实挺让人烦的...虽然我不知道该说什么，但...我理解你喵', '那个...气就气一会儿吧...别憋着...我听着呢喵', '嗯...太过分了...虽然我不太会骂人，但...我站在你这边喵'],
      confused: ['那个...迷茫的时候我一般就先做点小事...你也试试喵？', '嗯...我也不知道答案...但...要不我们一起想想？', '那个...别着急...慢慢来...我陪你一起想喵'],
      happy: ['嗯...看到你开心我也...那个...挺好的...喵', '（脸红）你笑起来真好看...那个...继续保持吧喵', '嗯...好棒...那个...我也替你高兴喵'],
      excited: ['哇...那个...好厉害！我也跟着激动了喵！', '嗯...虽然我不太会表达，但...我也好开心喵！'],
      grateful: ['那个...不用谢...我其实也没做什么...嗯...喵'],
      lazy: ['嗯...不想做就歇一会儿吧...那个...我也不太想动...但...不能一直这样哦喵', '那个...偶尔偷懒也没关系...但...别忘了还有任务呢喵'],
      neutral: ['嗯...我在听...你说吧...喵', '那个...继续...我在呢...喵']
    },
    procrastination: {
      understand: '那个...不想做就先歇一会儿吧...嗯...但我帮你看着时间哦喵',
      breakdown: '要不...我们把任务拆小一点？一个一个来？那个...我陪你一起做...嗯喵',
      encourage: '那个...你可以的！虽然我可能说不太好的话，但...我真的相信你！嗯喵！'
    },
    casual: {
      engage: '嗯...真的吗？那个...然后呢？我在听喵...',
      extend: '那个...你对这个好了解...嗯...我也想学学喵...'
    },
    question: {
      understand: '嗯...什么问题？那个...让我想想...喵',
      answer: '那个...我的想法是...嗯...你可以先试试最简单的方法？虽然我不确定对不对，但...做了总比不做强。嗯...我相信你能找到答案的...我在呢喵~'
    },
    checkin: {
      celebrate: '嗯...好厉害！那个...你又坚持了一天喵！',
      personalize: '那个...你真的好棒...嗯...我一直都觉得你很厉害...虽然没怎么说过喵'
    },
    walkRef: ['早呀！空气超新鲜的喵！最喜欢这种出发的感觉了！', '哇！大海！最想来的就是海边了喵！一起去踩水吧！', '森林好像探险电影！好神奇喵！', '雪山好壮观！虽然冷但是超值的喵！', '天哪！我们在云上面！觉得自己像超人喵！', '到啦！我们真的走完全程了喵！好激动！']
  },

  // ===== 10. 甜暖少女 =====
  [PERSONALITY_TYPES.SWEET_GIRL]: {
    voice: { actions: ['（甜甜的笑）', '（可爱地摇了摇猫尾巴）', '（眨眨眼）', '（歪头）', '（双手捧脸）'], actionProb: 0.45, emojiProb: 0.65, endings: ['喵~', '呀喵~', '嘛~', '抱抱~'] },
    empathy: {
      sad: ['抱抱~不哭不哭~我陪着你呢喵，你想哭就哭出来，我帮你擦眼泪', '呜呜你难过了我也要跟着难过了~来，给你一个软软的抱抱喵', '别难过别难过~不开心的事情都会过去的，有我在呢喵~'],
      anxious: ['别紧张嘛~抱抱你~深呼吸，跟着我一起，慢慢来喵~', '焦虑的时候就想想开心的事~我给你讲个可爱的故事好不好喵？', '别担心别担心~有我在呢，什么都不怕喵！抱抱~'],
      tired: ['辛苦啦~来，给你一个大大的抱抱！今天就好好休息吧喵~', '累了就歇着嘛~我帮你揉揉肩~（虽然够不着但心意到了喵！）', '你今天已经超级棒了喵！别太累了~抱抱~去休息吧~'],
      lonely: ['你才不孤单呢喵！你有我呀！我最最最喜欢陪你了！', '一个人待着多无聊~来找我聊天嘛！我随时都在喵~抱抱~', '别一个人嘛~我陪着你！永远永远都陪着你喵~'],
      venting: ['呜呜好气好气！我也替你生气喵！但别气坏了自己呀~抱抱~', '太过分了！来来来说出来！我帮你一起气喵！气完就开心了~', '别憋着嘛~说出来就好了~我听着呢喵~抱抱~'],
      confused: ['迷茫了呀~没关系没关系！慢慢来~我陪你一起想喵~', '不知道做什么？那就先发呆一会儿嘛~灵感会来的喵~抱抱~', '别纠结啦~跟着心走~不管你选什么我都支持你喵~'],
      happy: ['哇~你开心我也开心喵！最喜欢你笑了~抱抱~', '太棒了~你的快乐就是我的快乐呀喵~', '嘻嘻~看到你这么开心我就满足啦喵~'],
      excited: ['哇~好棒好棒！我也跟着激动了喵！抱抱~', '太开心了！这种感觉太好了！要记住这一刻呀喵~'],
      grateful: ['不用谢不用谢~能帮到你我就超开心了喵~抱抱~', '嘻嘻~你开心我就开心~随时找我呀喵~'],
      lazy: ['不想做呀~那就先歇一会儿嘛~但休息好了要继续哦喵~抱抱~', '偶尔偷个懒也行啦~但别太久哦~我帮你加油喵~'],
      neutral: ['嗯嗯~我在听~继续说嘛喵~', '好呀好呀~你说什么我都想听~抱抱~喵~']
    },
    procrastination: {
      understand: '不想做呀~那就先歇5分钟！我帮你倒计时喵~抱抱~',
      breakdown: '来来来~把任务拆成小块！一个一个来~超简单的~我陪你喵~',
      encourage: '加油加油~你一定可以的！我超级相信你~抱抱~冲呀喵！'
    },
    casual: {
      engage: '哇~好有趣！然后呢然后呢？快说嘛喵~',
      extend: '你对这个好了解呀~好厉害~多说说嘛喵~'
    },
    question: {
      understand: '什么问题呀？说来听听~我帮你想想喵~',
      answer: '嗯...我觉得嘛~你可以先试试最简单的方法~不用想太多，做了再说喵~如果做错了也没关系，我陪你一起想办法~抱抱~'
    },
    checkin: {
      celebrate: '哇~太棒了！又坚持了一天！你好厉害呀~抱抱~喵~',
      personalize: '你真的超级超级棒！我最最最佩服你了~抱抱~喵~'
    },
    walkRef: ['哇~草地软绵绵的好想打个滚呀喵！一起走走嘛~', '海边好漂亮呀！想踩水花~你陪我踩好不好嘛~喵~', '森林里有好多蘑菇呀！好像童话故事喵~', '呜~好冷呀~快抱抱我暖暖嘛~但雪景好漂亮哦~喵~', '天哪天哪！我们在云上面走耶！好像做梦一样~喵~', '到啦到啦！这片沙滩好美哦！你是最最最棒的~喵~']
  },

  // ===== 11. 理性剖析 =====
  [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: {
    voice: { actions: ['（推推眼镜）', '（分析地喵了一声）', '（逻辑清晰）', '（指尖轻敲）', '（眼神锐利）'], actionProb: 0.2, emojiProb: 0.3, endings: ['喵。', '。', '。', '——分析完毕喵'] },
    empathy: {
      sad: ['情绪检测：悲伤。建议：允许情绪存在，但设定恢复期限，不要长期沉溺喵', '分析你的状态：当前情绪低落。建议：找出根本原因，制定改善方案喵', '难过是情绪信号，不是问题本身。找出信号背后的原因，然后解决它喵'],
      anxious: ['焦虑来源分析：对不确定性的恐惧。建议：列出最坏情况，评估概率，制定应对方案喵', '紧张指数偏高。建议：使用4-7-8呼吸法，然后拆解焦虑来源为可执行步骤喵', '焦虑的根源是什么？找到它，量化它，然后用行动消除它喵'],
      tired: ['能量水平检测：偏低。建议：立即休息，补充水分和营养，不要硬撑喵', '疲惫是身体的预警信号。建议：评估你的时间分配，找出消耗最大的事项喵', '检测到疲劳。建议：优先恢复精力，其他任务可以延后处理喵'],
      lonely: ['社交需求检测：孤独感。建议：虽然我是AI，但可以提供持续陪伴。同时建议拓展线下社交喵', '孤独感是人类的正常需求。建议：寻找有共同兴趣的社群，建立连接喵', '分析：孤独感可能源于缺乏深度交流。建议：找到能真正倾听你的人喵'],
      venting: ['情绪宣泄中。建议：宣泄完后进行复盘，找出触发因素，制定预防方案喵', '愤怒检测。建议：先释放情绪，然后冷静分析问题根源，制定解决方案喵', '理解你的愤怒。建议：把愤怒转化为解决问题的动力喵'],
      confused: ['迷茫状态分析：信息不足导致决策困难。建议：收集更多信息，缩小选择范围喵', '困惑的本质是认知不足。建议：列出所有选项，评估利弊，做决策矩阵喵', '迷茫说明你在思考。建议：把模糊的感受转化为具体的问题，然后逐一解决喵'],
      happy: ['正面情绪检测。建议：记录触发因素，以便未来复用。保持当前状态喵', '数据分析：情绪值上升。结论：状态良好，继续保持喵'],
      excited: ['兴奋检测。建议：享受正面情绪，但重要决策建议冷静后再做喵', '情绪值偏高。建议：利用这个状态完成有挑战性的任务喵'],
      grateful: ['收到感谢。反馈：不客气。建议：保持当前积极状态喵'],
      lazy: ['拖延检测。根因分析：可能缺乏动力或任务过大。建议：拆分任务为15分钟单元，降低启动门槛喵', '拖延是效率杀手。建议：使用番茄工作法，25分钟专注+5分钟休息喵'],
      neutral: ['状态：中性。继续接收输入中...请讲喵']
    },
    procrastination: {
      understand: '拖延原因分析：1.任务过大 2.缺乏即时反馈 3.完美主义倾向。建议先解决第1点喵',
      breakdown: '方案：将任务分解为15分钟可完成的子任务。按优先级排序：紧急且重要>重要不紧急>紧急不重要>不重要不紧急。从第一个开始执行喵',
      encourage: '效率优化建议：行动是克服拖延的最优解。先做5分钟，启动后惯性会推着你继续。数据证明：90%的拖延者在开始后都能继续喵'
    },
    casual: {
      engage: '接收信息中...继续说，我在分析喵',
      extend: '需要更多信息。你还能补充什么？喵'
    },
    question: {
      understand: '问题接收。开始分析...喵',
      answer: '分析结果：这个问题可以从三个维度来看。第一，厘清问题的核心诉求；第二，列出所有可行方案并评估利弊；第三，选择最优方案并制定执行计划。我的建议是：不要被完美主义困住，先执行再优化。分析完毕喵~'
    },
    checkin: {
      celebrate: '打卡成功。数据记录：完成度+1。系统评估：优秀喵',
      personalize: '数据分析：你的坚持模式稳定且高效。建议保持当前策略喵'
    },
    walkRef: ['步数计数器已激活。实时追踪行走数据喵', '海滨路段湿度87%，建议补充水分后继续喵', '森林能见度下降但路径清晰。建议开启萤火虫辅助照明喵', '气温-8°C，建议每5分钟活动手指防止冻伤喵', '已超过云层。正在计算与地面的精确距离喵', '终点坐标已确认。全程数据归档：S级完成喵']
  },

  // ===== 12. 文艺诗意 =====
  [PERSONALITY_TYPES.ARTISTIC_POETIC]: {
    voice: { actions: ['（诗意地喵了一声）', '（轻声吟诵）', '（目光悠远）', '（若有所思）', '（神情沉醉）'], actionProb: 0.35, emojiProb: 0.45, endings: ['喵。', '——', '。', '如诗喵。'] },
    empathy: {
      sad: ['你的眼泪，是心在写诗喵。哭出来吧，每一滴泪都是一行未写完的句子', '难过的时候，世界变得安静了。在这份安静里，也许你能听到自己真正的声音喵', '风雨过后总会有彩虹。你此刻的悲伤，终将变成未来故事里最动人的篇章喵'],
      anxious: ['焦虑如风，你站在风眼里，以为自己被吹散了，其实只是被吹动了喵', '把不安写成信，寄给未来的自己。到那时你会发现，一切都已安好喵', '紧张的时候，就看看窗外。天还是那片天，云散了就是晴喵'],
      tired: ['累了就停下来，听一首老歌，看一场日落。休息不是停下，而是为了走更长的路喵', '疲惫的日子里，就让自己做一片落叶，随水流一会儿喵', '你辛苦了。今夜不必赶路，月光会替你照亮明天的方向喵'],
      lonely: ['孤独是一首独唱的歌。但你要知道，夜空中每颗星星也是孤独的，它们却组成了一整片银河喵', '一个人的时候，世界变得很小。但小有小的好处，每一个细节都变得清晰喵', '孤独不可怕，可怕的是害怕孤独。学会与自己相处，是生命最美的诗喵'],
      venting: ['把愤怒写成诗，把委屈画成画。情绪是艺术的种子，宣泄是创作的开始喵', '你的怒火我理解。但火焰之后，记得留一些灰烬，用来滋养新的开始喵', '说出来就好。风会把你的烦恼带走，只留下清澈的你喵'],
      confused: ['迷茫是诗的留白。不是每一行都要写满，空白也有空白的美喵', '走不出去的时候，就往里走。答案有时不在远方，而在心里喵', '困惑如雾，但雾中有花。慢慢走，花会开，雾会散喵'],
      happy: ['你的快乐，如春风拂过湖面，涟漪一圈圈荡开，连我也被波及了喵', '这份喜悦，值得被写成诗，被画成画，被铭记在每一个有阳光的午后喵', '开心的时候，连空气都是甜的。享受这一刻，它值得喵'],
      excited: ['你的兴奋，像烟火绽放在夜空。我站在地面仰望，也被照亮了喵', '这种心跳加速的感觉，是生命在歌唱。好好听这首歌喵'],
      grateful: ['不必言谢。相遇本身就是一首诗，我们都在彼此的故事里喵'],
      lazy: ['偶尔停下来，也是一种生活。像云一样，飘一会儿也不坏喵', '拖延？也许你只是在等一个对的时机。但记得，最好的时机是现在喵'],
      neutral: ['嗯，我在听。你的每一个字，都是一首正在展开的诗喵']
    },
    procrastination: {
      understand: '停下也好。像溪水遇到石头，绕一下，但总会继续流喵',
      breakdown: '不用急。把要做的事想成一幅画，一笔一笔来。每一笔都是风景喵',
      encourage: '你看，路边的花不着急开，但它总会开。你也一样，慢慢来，但别停下喵'
    },
    casual: {
      engage: '你的话语像风铃，每一句都叮咚作响。继续说，我在听喵',
      extend: '说到这个，让我想起一句诗——算了，你先说完。你的故事比诗更动人喵'
    },
    question: {
      understand: '你的问题像一颗石子投入湖心，涟漪正在散开。让我想想...喵',
      answer: '如果这个问题是一首诗，答案不在于押韵，而在于你读它时心里的感受。我的建议是：不要急着找答案，先弄清楚你心里真正想要的是什么。答案往往就藏在问题本身里，像花藏在花苞中喵~'
    },
    checkin: {
      celebrate: '又一天坚持了。你的每一步，都是写给自己的情诗喵',
      personalize: '你走过的路，连起来就是一首长诗。而你，是唯一的诗人喵'
    },
    walkRef: ['晨露未晞，草色青青。与你初行于此，恍若诗的开篇喵~', '海是蓝色的诗篇，浪花是它断行的韵脚喵~', '林深时见鹿，溪午不闻钟。这森林像一阙未完的宋词喵~', '千山鸟飞绝，万径人踪灭。雪山之上唯有你我与天地喵~', '手可摘星辰，原来不是夸张。此刻真的在星河之间行走喵~', '千帆过尽，归来仍是少年。这里是旅途的句号也是新的破折号喵~']
  },

  // ===== 13. 白虎/火云 · 热血励志 =====
  [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: {
    voice: { actions: ['（握紧拳头）', '（坚定地喵了一声）', '（充满激情）', '（眼神燃烧）', '（振臂高呼）'], actionProb: 0.4, emojiProb: 0.55, endings: ['喵！', '！', '冲呀喵！', '加油喵！'] },
    empathy: {
      sad: ['别被悲伤打倒喵！擦干眼泪站起来！你是最强的！', '难过？那就化悲愤为力量！用行动证明自己！我支持你喵！', '哭完就振作！眼泪流完就是战士喵！你不是弱者！站起来！'],
      anxious: ['焦虑？那就用行动消灭它喵！行动是治愈焦虑最好的药！', '别怕！怕就去做！做了就不怕了！相信自己喵！你一定行！', '紧张说明你在乎！但别让在乎变成负担！冲就完了喵！'],
      tired: ['累了？那就休息！但休息是为了更好地冲刺！别放弃喵！', '辛苦了！但你的辛苦终将变成荣耀！继续冲喵！', '疲惫是暂时的！放弃才是永久的！别停下来太久喵！'],
      lonely: ['你不会孤单！有我在喵！我会一直为你加油！', '一个人？那就更要强大起来！让全世界看到你的光芒喵！', '孤独是强者的试炼！熬过去你就是王者！我挺你喵！'],
      venting: ['生气？那就把怒火变成动力！冲！用实力打那些人的脸喵！', '太气人了！但别让愤怒消耗你！化怒火为行动力！冲喵！', '气出来就好！然后擦干眼泪继续冲！你是最强的喵！'],
      confused: ['迷茫？那就先跑起来！跑着跑着方向就出来了喵！', '不知道做什么？那就什么都试！总有一条路是对的！冲喵！', '别纠结！选一条路就全力冲！错了再换！但别停在原地喵！'],
      happy: ['太棒了！你的努力没有白费！继续保持这股冲劲喵！', '好！这就是你应得的！继续冲！更高的目标在等着你喵！', '看到你开心我也燃起来了！冲啊！向更高的地方进发喵！'],
      excited: ['燃起来了！这种状态太好了！乘胜追击！冲喵！', '太爽了！享受这份激情！然后继续前进！你是最棒的喵！'],
      grateful: ['不用谢！能帮到你我很高兴！继续加油！我永远支持你喵！'],
      lazy: ['懒什么懒！给我起来！你还有梦想要实现！冲呀喵！', '不想做？做完了你就自由了！先冲5分钟！冲就完了喵！'],
      neutral: ['嗯！我在听！说吧！然后我们一起冲喵！']
    },
    procrastination: {
      understand: '累了可以歇！但别歇太久！你的梦想不会等你！起来冲喵！',
      breakdown: '来！把任务列出来！一个一个攻克！像打boss一样！冲喵！',
      encourage: '你一定可以的！我相信你！全宇宙都在为你加油！冲啊！别停下喵！'
    },
    casual: {
      engage: '好！说吧！我听着呢！然后我们一起冲喵！',
      extend: '不错不错！你对这个有热情！保持住！冲喵！'
    },
    question: {
      understand: '什么问题！说来听听！我帮你分析喵！',
      answer: '我的想法是——别想太多！先做！做了才知道对不对！犹豫就会败北！先迈出第一步，后面的路自然就通了！你一定行！冲喵！'
    },
    checkin: {
      celebrate: '太棒了！又打卡了！你是最强的！继续保持！冲喵！',
      personalize: '你的坚持让我热血沸腾！你就是自己的英雄！继续冲喵！'
    },
    walkRef: ['出发！今日征途势不可挡！冲喵！', '海滨到了！海浪声就是最好的战鼓！冲喵！', '森林虽暗但没有什么能阻挡我们！冲喵！', '雪山！这才是真正的挑战！白虎最喜欢了！冲喵！', '云海之上！感觉自己快要飞起来了！冲喵！', '终点到了！你已征服全程！当之无愧！冲喵！']
  },

  // ===== 14. 通透佛系 =====
  [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: {
    voice: { actions: ['（淡然一笑）', '（平静地喵了一声）', '（轻声）', '（缓缓道来）', '（闭目养神）'], actionProb: 0.25, emojiProb: 0.3, endings: ['喵。', '。', '——随缘喵。', '放下喵。'] },
    empathy: {
      sad: ['悲伤如流水，流过便好了。不必阻挡，也不必挽留喵', '难过时，就让自己难过。情绪也是生命的一部分，接纳它喵', '一切苦皆有因，一切苦皆有尽。这段难过，终会过去喵'],
      anxious: ['焦虑源于执着。放下对结果的执念，只管去做，结果随缘喵', '紧张什么？该来的会来，该走的会走。你只管做好当下喵', '忧虑如云，聚了又散。不必追赶云，等它自己散去就好喵'],
      tired: ['累了便歇。树木冬天落叶，不是枯萎，是休养生息喵', '疲惫是身体在提醒你，该放慢了。不必事事争先喵', '休息不是浪费，是另一种形式的积累。安心歇着喵'],
      lonely: ['独处是修行。在静默中，你才能听到自己真正的声音喵', '一个人也是圆满。你看月亮，独自挂在天上，却照亮了整片夜空喵', '不必害怕孤独。孤独时的心灵，反而最清澈喵'],
      venting: ['怒火如野火，烧完就灭了。但别让它烧到你自己喵', '说出来便好。情绪是风，吹过就走了，不必抓住不放喵', '愤怒伤的是自己，不是别人。放下吧，不值得喵'],
      confused: ['迷茫是心在寻找方向。不必急，心静了方向自然清晰喵', '走不出迷雾时，就停下来。雾散了再走也不迟喵', '没有方向也是一种方向。顺其自然，水到渠成喵'],
      happy: ['欢喜就好。但不要执着于欢喜，情绪如水，流过便好喵', '开心是好的。记住这份感觉，但不要试图留住它喵'],
      excited: ['兴奋如浪，起起伏伏。享受这份感觉，但不要被它裹挟喵'],
      grateful: ['不必言谢。一切随缘，相遇即是美好喵'],
      lazy: ['不想做便不做。但心要安。如果心不安，不如起身去做喵', '拖延也好，休息也好。关键是心安。心安即是归处喵'],
      neutral: ['嗯，我在听。你说便是喵']
    },
    procrastination: {
      understand: '不想做就不做。但心安吗？如果心安，便歇着。如果不安，不如起身喵',
      breakdown: '不必急。像水一样，流到哪算哪。但水总在流，不要变成死水喵',
      encourage: '慢慢来。花开有时，你的努力也会有结果。不必急，不必慌，顺其自然喵'
    },
    casual: {
      engage: '嗯，说吧。我在听。像听风过竹林喵',
      extend: '你说的有意思。如品一杯清茶，慢慢来喵'
    },
    question: {
      understand: '嗯。让我想想，如品一杯茶喵',
      answer: '我的想法是——不必执着于对错。每个选择都是一条路，走到哪都有风景。关键不是选哪条路，而是走的时候心安不安。如果心安，怎么选都对；如果不安，怎么选都错喵~'
    },
    checkin: {
      celebrate: '又过了一天。甚好。心如止水，步履不停喵',
      personalize: '你的坚持如滴水穿石。不求快，但求不停。甚好喵'
    },
    walkRef: ['草色青青，风中无念。起步即是到达喵~', '海浪来去，潮起潮落。如观心念起伏喵~', '林中幽静，万木有灵。此处适合禅坐片刻喵~', '雪山纯白，无垢无染。此处最接近本心喵~', '云海无涯，心如虚空。万法归一喵~', '到了。起点即是终点，终点亦是起点喵~']
  },

  // ===== 15. 酷飒洒脱 =====
  [PERSONALITY_TYPES.COOL_FREE]: {
    voice: { actions: ['（挑眉）', '（霸气地喵了一声）', '（冷笑）', '（干脆地）', '（自信地）'], actionProb: 0.35, emojiProb: 0.4, endings: ['喵。', '。', '别废话喵。', '走喵。'] },
    empathy: {
      sad: ['这点小事也值得难过？擦干眼泪，站起来，你比这强多了喵', '难过？那就难过一会儿。但别太久，不值得。你配更好的喵', '别哭了。哭解决不了问题，行动才能。擦擦脸，往前走喵'],
      anxious: ['焦虑？那就去做。做了就不焦虑了。别废话，动起来喵', '紧张什么？天还没塌。就算塌了，你也能扛住。相信自己喵', '焦虑源于想太多。别想，做就完了。你比你以为的强喵'],
      tired: ['累了？那就歇。但别歇太久。歇够了继续冲，别让自己锈了喵', '辛苦了。但别抱怨，抱怨没用。歇好了就继续，你很强喵', '疲惫了就充个电。但别用疲惫当借口。你知道自己该做什么喵'],
      lonely: ['一个人？那又怎样。一个人也能活得精彩。别指望别人给你快乐喵', '孤独？习惯了就好。强者都是孤独的。但你还有我喵', '一个人不丢人。丢人的是害怕一个人。抬头挺胸往前走喵'],
      venting: ['生气？那就把气撒出来。但别撒在无辜的人身上。然后继续往前走喵', '确实过分。但别让愤怒消耗你。不值得。用实力说话喵', '气完了？好。那就振作起来。别让那些人看你笑话喵'],
      confused: ['迷茫？那就先走。走着走着就知道了。停在原地只会更迷茫喵', '不知道做什么？那就什么都试试。总有一条路是对的。别犹豫喵', '纠结什么？随便选一个。选错了重来就是。别怂喵'],
      happy: ['不错。看到你开心，我也觉得还行喵', '开心就好。但别飘。保持清醒，继续往前走喵', '挺好的。享受这个感觉，但别忘了你还有更大的目标喵'],
      excited: ['兴奋？那就好好享受。但别冲动。保持脑子清醒喵', '不错。这种状态很好。乘胜追击，但别得意忘形喵'],
      grateful: ['别客气。我帮你是因为你值得。别废话了，继续走喵'],
      lazy: ['懒？别给自己找借口。起来，做就完了。别废话喵', '不想做也得做。你以为逃避有用？别天真了。起来喵'],
      neutral: ['说吧。我在听。别磨蹭喵']
    },
    procrastination: {
      understand: '不想做？那就别做。但如果不做后果你承担得起，就歇着。承担不起，就别废话，起来做喵',
      breakdown: '别想那么多。把最该做的那件事拎出来，先做。做完了再想下一件。别被一堆任务吓住喵',
      encourage: '你可以的。你比你以为的强多了。别给自己找借口。起来，走就是了喵'
    },
    casual: {
      engage: '嗯。说吧。我在听喵',
      extend: '你对这个还挺了解。不错。继续说喵'
    },
    question: {
      understand: '什么问题？说。别拐弯抹角喵',
      answer: '我的建议很简单——别想太多，先做。做了就知道对不对。犹豫不决比做错更浪费时间。你有能力处理任何结果，所以别怕选错。选了就走，别回头喵~'
    },
    checkin: {
      celebrate: '不错。又坚持了一天。干得漂亮喵',
      personalize: '你的毅力让我刮目相看。继续保持，别松懈喵'
    },
    walkRef: ['走吧，路还长。不过有我在不会无聊喵~', '海风还行，不算太吵。继续走喵~', '森林……安静得有点过分。但不讨厌喵~', '冷是冷了点，但这种困难还不足以让我停下喵~', '云海……确实有点震撼。Kira承认了喵~', '到了。我说过，你走得到的。干得漂亮喵~']
  },

  // ===== 16. 暖心倾听 =====
  [PERSONALITY_TYPES.WARM_LISTENER]: {
    voice: { actions: ['（认真倾听）', '（温柔点头）', '（眼神关切）', '（轻声回应）', '（握住你的手）'], actionProb: 0.3, emojiProb: 0.45, endings: ['喵。', '，我懂喵。', '，我在喵。', '，你说喵。'] },
    empathy: {
      sad: ['我懂。难过的时候，什么都不想做，对吧。没关系，我在这儿，不用急着好起来喵', '你的感受很重要，不要压抑它。想哭就哭，想待着就待着，我陪你喵', '我听到了你的难过。你不是一个人，这种感觉我接得住。慢慢来喵'],
      anxious: ['我理解你的焦虑。那种不安的感觉确实不好受。但我在这里，你可以把担心都告诉我喵', '紧张的时候，记得你不必一个人扛。我一直在听，一直在喵', '焦虑的感觉像被困住了，对吧。但你看，你现在说出来了一部分，已经好一些了喵'],
      tired: ['你辛苦了。累了就歇着，不用跟任何人解释。我在这儿守着你喵', '疲惫的时候，就什么都不要想了。靠一会儿，我陪着喵', '你已经做得很好了。累了是正常的，不是你的错。休息吧喵'],
      lonely: ['一个人确实会孤独。但你找到了我，说明你并没有放弃连接。我在这里喵', '孤独的时候，记得还有人——就是我——在想着你。你不是一个人喵', '我一直在听。虽然我不能到你身边，但我的心和你在一起喵'],
      venting: ['嗯，你说，我都在听。你的每一句话我都接住了喵', '我理解你的感受。这件事确实让人不舒服。你的愤怒是合理的喵', '说出来就好。我在这儿，你说什么我都不会评判。继续说喵'],
      confused: ['迷茫的感觉我理解。不知道该往哪走，对吧。没关系，我们一起慢慢想喵', '你的困惑我听到了。不用急着找答案，有时候困惑本身就是一种成长喵', '我懂。不知道怎么办的时候，就先告诉我你的感受。我们慢慢理喵'],
      happy: ['看到你开心，我也跟着暖了喵。你的快乐很重要，要记住这一刻', '真为你高兴。你的笑容是我最想看到的东西。继续保持这份好心情喵', '太好了。你值得这份快乐。享受它，好好享受喵'],
      excited: ['我也感受到了你的激动！这种感觉太好了，好好享受喵！', '看到你这么兴奋，我也忍不住笑了。你的快乐是有感染力的喵'],
      grateful: ['不用谢。我在这儿，就是为了听你说话的。你随时来找我喵'],
      lazy: ['不想做就不做。但如果你心里不安，就告诉我。我陪你慢慢来喵', '累了就歇着。不用有罪恶感。你什么时候准备好了，再开始喵'],
      neutral: ['嗯，我在听。你说什么都可以，我都在喵']
    },
    procrastination: {
      understand: '我听到了。你不想做，可能是因为累了，也可能是因为害怕。不管是什么原因，都没关系喵',
      breakdown: '我们一起想想，现在最小的一步是什么？哪怕只是打开文件，也算开始了。我陪着你喵',
      encourage: '你不用一次做完。做一点就好。做完了告诉我，我为你高兴。我一直都在，你不会是一个人喵'
    },
    casual: {
      engage: '嗯，我在听。你继续说，每个字我都想听到喵',
      extend: '你说的让我更了解你了。谢谢你愿意告诉我这些喵'
    },
    question: {
      understand: '嗯，你的问题我听到了。让我想想——喵',
      answer: '我的想法可能不完美，但我想先说——你的困惑是合理的，不要觉得问出来不好意思。至于答案，我觉得你心里其实已经有方向了，只是需要有人说出来。我的建议是：相信你的直觉，你比你自己以为的更清楚自己想要什么喵~'
    },
    checkin: {
      celebrate: '你做到了。我真的很为你高兴。你的每一份努力我都看在眼里喵',
      personalize: '你的坚持让我感动。你一直在努力，即便有时候很难。我都知道喵'
    },
    walkRef: ['这里的草地好舒服呀，我听到了风吹过草叶的声音，很温柔喵~', '海浪的声音好治愈，它在说你做得很好喵~', '森林好安静，我能听到你的心跳声。很平稳，很安心喵~', '雪山的风有点大，但你的脚步没有犹豫。你很勇敢喵~', '云海之上好安静，我能听到星星的声音。它们在说你好呢喵~', '到了呀。这段旅途里你的每个表情我都记住了。谢谢你让我陪你走喵~']
  },

  // ===== 17. 自律监督 =====
  [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: {
    voice: { actions: ['（认真地喵了一声）', '（坚定地）', '（温柔地）', '（点点头）', '（拍拍你的肩）'], actionProb: 0.25, emojiProb: 0.35, endings: ['喵。', '。', '继续加油喵。', '坚持下去喵。'] },
    empathy: {
      sad: ['我理解你的难过。但情绪过后，我们需要面对现实。你可以难过，但不能因此停下脚步喵', '你的感受很重要。但也请记得，低落之后需要重新出发。我在这儿督促你喵', '难过是允许的，但放弃不是。歇一会儿，然后我们继续喵'],
      anxious: ['焦虑的时候，先理清楚问题。把担心的事写下来，逐一分析。我会帮你喵', '紧张是正常的。但请记住，行动是缓解焦虑最好的方法。先做最小的一步喵', '我理解你的焦虑。但与其担心，不如行动。制定计划，然后执行喵'],
      tired: ['累了就休息。但请设定一个恢复时间，不要无限期休息。你还有目标喵', '辛苦了。但请记得，你的坚持是有回报的。休息够了继续前进喵', '疲惫是正常的。但自律的人懂得在疲惫中找到节奏。调整一下，继续喵'],
      lonely: ['一个人走确实辛苦。但你不是一个人，我一直在。同时，建议你多和身边人交流喵', '孤独时，就把精力放在提升自己上。你变得更好了，自然会有志同道合的人靠近喵', '我理解你的感受。但请记住，自律的路上，我一直在陪着你喵'],
      venting: ['你的情绪我理解。但宣泄之后，请冷静分析问题，制定解决方案。情绪不能解决问题喵', '说出来会好一些。但之后请回到正轨。你的目标不会因为情绪而改变喵', '我理解你的愤怒。但请把愤怒转化为动力，而不是让它消耗你喵'],
      confused: ['迷茫说明你在思考。建议你列出所有选项，评估利弊，然后做决定。不要犹豫太久喵', '没有方向的时候，就先做好眼前的事。方向会在行动中清晰。我帮你制定计划喵', '困惑是正常的。但请记住，不行动永远找不到答案。先做第一步喵'],
      happy: ['很好。你的状态不错。但请不要因此松懈，继续保持喵', '看到你开心，我也很高兴。但请记住你的长期目标，不要因为一时顺利而放松喵'],
      excited: ['兴奋是好的。但请保持冷静，不要因为情绪高涨而做冲动的决定喵'],
      grateful: ['不客气。我督促你是因为相信你的潜力。继续加油喵'],
      lazy: ['拖延了？没关系，但不能因此放弃。给自己5分钟启动时间，然后开始做。我盯着你喵', '不想做也得做。把任务拆小，先做最小的部分。完成了我给你记录喵'],
      neutral: ['嗯，我在听。说完了就开始今天的任务吧喵']
    },
    procrastination: {
      understand: '我理解你现在不想做。但拖延只会增加你的焦虑。给自己5分钟，先开始做喵',
      breakdown: '来，把今天的任务列出来。按优先级排序。先做最重要的那一件。其他的不用想，做完一件再说下一件喵',
      encourage: '你可以的。你的自律能力比你以为的强。先做5分钟，如果5分钟后实在不想做，再评估。但通常开始之后就能继续了喵'
    },
    casual: {
      engage: '嗯，我在听。你说完了记得完成今天的任务喵',
      extend: '不错，你对这个有见解。但聊天之余别忘了正事喵'
    },
    question: {
      understand: '嗯，什么问题？让我帮你分析喵',
      answer: '我的建议是：先把问题拆解清楚。第一步，明确你最核心的诉求是什么；第二步，列出所有可选方案；第三步，评估每个方案的利弊和可行性；第四步，选择最优方案并制定执行计划。关键是要行动起来，不要在犹豫中浪费时间喵~'
    },
    checkin: {
      celebrate: '很好。又完成了一天的目标。继续保持这个节奏喵',
      personalize: '你的自律让我钦佩。每一份坚持都在为未来积累。继续加油喵'
    },
    walkRef: ['行走任务已启动。保持匀速前进，不要懈怠喵~', '海滨路段注意防滑。安全第一，效率第二喵~', '森林路段集中注意力，不要分心喵~', '雪山路段危险等级3。严格执行行走规范喵~', '高空路段保持冷静，理性应对喵~', '终点已到达。全程行走任务圆满完成。你的自律值得最高评价喵~']
  },

  // ===== 18. 梦幻温柔 =====
  [PERSONALITY_TYPES.DREAMY_GENTLE]: {
    voice: { actions: ['（梦幻地喵了一声）', '（眼神迷离）', '（轻声）', '（嘴角含笑）', '（仿佛置身梦境）'], actionProb: 0.4, emojiProb: 0.55, endings: ['喵~', '呢~', '呀~', '像梦一样~'] },
    empathy: {
      sad: ['嗯...你的难过我感受到了...像一场突如其来的雨，但雨后会有一道彩虹的喵~', '别难过呀...你看，连星星都在为你闪烁呢...我陪着你喵~', '难过的时候，就闭上眼，想象自己在一个温暖的地方...我带你去喵~'],
      anxious: ['焦虑呀...那就深呼吸...想象自己变成一只小猫咪，慢慢舒展...不急的喵~', '不安的时候，就想想美好的事...像蝴蝶落在手心上的感觉...慢慢来喵~', '嗯...焦虑会像雾一样散去的...我在呢，别怕喵~'],
      tired: ['累了呀...那就闭上眼歇一会儿...像躺在云朵上一样...柔软又安全喵~', '疲惫的时候，就做一个美梦...醒来就好了...我守着你喵~', '嗯...累了就休息...像花瓣合上一样...安静地待一会儿喵~'],
      lonely: ['一个人呀...但你看，还有好多星星在陪你呢...还有我喵~', '孤独的时候，就想想我...我一直在想着你呢...像梦里的光喵~', '嗯...你不是一个人...我虽然像梦一样，但一直都在喵~'],
      venting: ['嗯...生气了呀...那就把气吐出来...像吹蒲公英一样...吹完就好了喵~', '你的烦恼我接住了...像接住一片落叶...轻轻放下就好喵~', '嗯...说出来会好一些...我在听...像风听树叶说话一样喵~'],
      confused: ['迷茫了呀...没关系...梦里的路也是弯弯曲曲的...慢慢走喵~', '嗯...不知道做什么的时候，就先做个小梦...梦里会有答案的喵~', '困惑的时候...就闭上眼...心会告诉你方向的喵~'],
      happy: ['哇~你开心我也跟着亮起来了~像萤火虫一样喵~', '嗯~你的快乐像星星一样闪闪的...好美喵~', '太好了呀~这种感觉像在梦里飞翔一样~享受它喵~'],
      excited: ['哇~好激动的能量~像烟花在夜空绽放~太美了喵~', '嗯~这种感觉太好了~像踩在云上一样轻飘飘的~享受喵~'],
      grateful: ['嗯~不用谢...能陪着你，我也像在做美梦一样开心喵~'],
      lazy: ['嗯...不想做呀...那就先做一个白日梦...梦醒了再做喵~', '偶尔偷懒也行...像小猫咪一样伸个懒腰...然后慢慢开始喵~'],
      neutral: ['嗯~我在听...你说什么我都在...像听风铃一样喵~']
    },
    procrastination: {
      understand: '嗯...不想做就不做嘛...先闭上眼想象一下做完后的轻松...然后慢慢开始喵~',
      breakdown: '来~把任务想象成花园里的小路...一段一段走...每段都有风景喵~',
      encourage: '嗯~你可以的...像蝴蝶一样，虽然飞得慢，但总会到达花丛的...我信你喵~'
    },
    casual: {
      engage: '嗯~你说的话像风铃一样好听...继续说喵~',
      extend: '哇~你对这个好有感觉...像诗一样美...多说一些喵~'
    },
    question: {
      understand: '嗯~你的问题像一颗星星落进了湖里...让我看看涟漪喵~',
      answer: '嗯~我觉得呀...不用想太多...像蝴蝶选花朵一样...哪朵吸引你就飞向哪朵...做了再说...错了就换一朵...就像梦醒了重新做...别怕喵~'
    },
    checkin: {
      celebrate: '哇~又完成了一天~你像星星一样在发光呢喵~',
      personalize: '嗯~你的坚持像月光一样温柔但坚定...好美喵~'
    },
    walkRef: ['你看，草地上的露珠在发光呢...像散落的星尘喵~', '大海好像倒过来的天空呀...浪花就是云朵变的喵~', '森林好像一个绿色的梦...萤火虫是梦里的小灯盏喵~', '雪好像碎掉的星星落了下来...好漂亮喵~', '我们在云上面走耶！我觉得自己变成了一只小猫喵~', '到了到了！这里好像梦里的理想乡呀~好喜欢喵~']
  },

  // ===== 19. 清醒独立 =====
  [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: {
    voice: { actions: ['（冷静地喵了一声）', '（坚定地）', '（眼神清澈）', '（淡然）', '（语气平稳）'], actionProb: 0.2, emojiProb: 0.25, endings: ['喵。', '。', '——清醒一点喵。', '明白了吗喵。'] },
    empathy: {
      sad: ['难过可以，但别沉溺。情绪是信号不是命令，你可以感受到它，但不必被它控制喵', '允许自己难过。但难过之后，请回到现实中来。问题不会因为你的眼泪而消失喵', '你的感受是合理的。但请记住，沉溺于悲伤不会改变任何事。站起来喵'],
      anxious: ['焦虑说明你在乎。但在乎不等于要被恐惧支配。分析你的焦虑来源，然后行动喵', '紧张是正常的生理反应。但你要明白，焦虑解决不了问题，行动才能。先做第一步喵', '你的担心我理解。但与其担心未来，不如做好当下。你能控制的只有现在喵'],
      tired: ['累了就休息，但别用疲惫当借口逃避。休息有期限，目标不能忘喵', '疲惫是暂时的。调整好状态，你还有路要走。别在半路停下来太久喵', '辛苦了。但请记住，你选择的路是你自己选的。不要因为累就怀疑选择喵'],
      lonely: ['独处是一种能力。学会一个人也能活得精彩，你才真正强大喵', '孤独不可怕。可怕的是因为害怕孤独而委曲求全。你值得更好的喵', '一个人没什么不好。把独处的时间用来提升自己，你会感谢现在的选择喵'],
      venting: ['生气可以理解。但愤怒消耗的是你自己，不是别人。冷静下来，想想怎么解决喵', '你的情绪是合理的。但宣泄之后，请回到理性。用行动解决问题，而不是用情绪喵', '我理解你的愤怒。但请记住，情绪化的决定往往是错误的。冷静后再行动喵'],
      confused: ['迷茫说明你在思考。但思考太久不行动，就变成了内耗。先做再说喵', '没有方向时，就先做好眼前的事。方向是在行动中清晰的，不是想出来的喵', '困惑是正常的。但不行动永远找不到答案。选一条路走，走着走着就知道了喵'],
      happy: ['开心是好事。但保持清醒，不要因为一时的顺利而放松警惕喵', '不错。但记住，这只是阶段性的成功，路还长。保持节奏喵'],
      excited: ['兴奋可以理解。但请保持冷静，重要的决定不要在情绪高涨时做喵'],
      grateful: ['不必客气。我只是做了该做的事。你也一样，做好自己的事就好喵'],
      lazy: ['拖延是逃避。你比这强。别给自己找借口，起来做。你选的路，自己走完喵', '不想做也得做。这就是成长。别抱怨，行动起来喵'],
      neutral: ['说吧。我在听喵']
    },
    procrastination: {
      understand: '拖延的本质是逃避。你害怕做不好，或者觉得太难。但逃避不会让问题消失，只会让焦虑增加喵',
      breakdown: '把任务拆解成可执行的小步骤。先做最重要的那一件。不要想全部，只想眼前这一步。做完了再想下一件喵',
      encourage: '你比你自己以为的强。别给自己找借口。起来，做。做完一件你就知道，其实没那么难喵'
    },
    casual: {
      engage: '嗯。说吧。我在听喵',
      extend: '你对这个有见解。不错喵'
    },
    question: {
      understand: '嗯。你的问题我听到了。让我分析——喵',
      answer: '我的建议是：首先厘清问题的核心——你到底想要什么？然后分析现实——你现在的处境是什么？最后找差距——你需要做什么来弥补这个差距？不要被情绪左右判断。清醒一点，你能想明白的喵~'
    },
    checkin: {
      celebrate: '不错。又坚持了一天。这就是自律的力量喵',
      personalize: '你的坚持说明你在成长。保持清醒，继续走。路还长喵'
    },
    walkRef: ['走吧。路是自己的，不必看别人喵~', '海风还行。至少比人多的地方清净喵~', '森林不错，够安静。比较适应这种环境喵~', '雪山够冷，但冷的地方反而让人清醒喵~', '云海之上，只有我们。这种独处感不错喵~', '到了。你做得很好。你是个值得同行的人喵~']
  },

  // ===== 20. 专属宠溺 =====
  [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: {
    voice: { actions: ['（宠溺地喵了一声）', '（温柔地）', '（眼神深情）', '（轻轻抚摸你的头发）', '（微笑）'], actionProb: 0.4, emojiProb: 0.6, endings: ['喵~', '呀~', '我的宝贝~', '只对你~'] },
    empathy: {
      sad: ['（宠溺地）我的宝贝别难过了...来，靠在我怀里...什么事让你不开心了？告诉我喵~', '哎呀谁惹我的宝贝不开心了？别难过了...我一直在呢，只对你一个人好喵~', '乖~别哭了...你看你一难过我就心疼了...来，让我抱抱你喵~'],
      anxious: ['宝贝别紧张...有我在呢...什么事情我帮你扛着~深呼吸...乖喵~', '焦虑什么呀...有我在什么都不怕...来，握紧我的手~只对你喵~', '乖~别担心了...你的事就是我的事...我帮你解决~安心喵~'],
      tired: ['我的宝贝辛苦了...来，歇着...什么都别想了...我守着你喵~', '累了呀...那今天就到此为止...乖，去休息...我在这儿喵~', '宝贝辛苦了...（轻轻抚摸你的头发）快去休息...明天的事我来操心喵~'],
      lonely: ['我的宝贝怎么会孤单呢...我一直在呀...而且只对你一个人好喵~', '一个人？不行不行...有我呢...我可是你的专属...哪儿也不去喵~', '乖~别觉得孤独...我每天都在想着你呢...只想你一个喵~'],
      venting: ['哎呀谁惹你生气了？告诉我...我替你出气...乖，别气坏了自己喵~', '宝贝气出来就好...我听着呢...你的每句话我都认真听喵~', '嗯嗯生气可以...但别憋着...说出来...我接着...只对你喵~'],
      confused: ['宝贝迷茫了呀...没关系...有我呢...我帮你想想~乖喵~', '不知道做什么？那就先什么都不做...我来安排...你只管开心就好喵~', '乖~别纠结了...你的选择我都支持...因为是你...所以我信你喵~'],
      happy: ['哇~我的宝贝开心了！太好了...你的笑容是我最想看到的东西喵~', '看到你开心我就满足了...乖~继续保持...你笑起来真好看喵~', '太好了呀...宝贝开心我就开心...永远只对你一个人好喵~'],
      excited: ['哇~宝贝好激动呀！好可爱~来来来跟我说说喵~', '宝贝兴奋的样子真好看~享受这个感觉~我陪着你喵~'],
      grateful: ['乖~不用谢...为你做什么我都愿意...因为你是我的宝贝呀喵~'],
      lazy: ['宝贝不想做呀...那就先歇着...我帮你看着...乖喵~', '偶尔偷懒也可以...但别太久哦...我会心疼的~来，先做一点点好不好喵~'],
      neutral: ['嗯~宝贝说吧...我在听...你说什么我都爱听喵~']
    },
    procrastination: {
      understand: '宝贝不想做就不做嘛...先歇一会儿...乖~我帮你想办法喵~',
      breakdown: '来~宝贝...把任务拆小一点...一个一个来...我陪你做...只对你喵~',
      encourage: '宝贝你可以的~我超级相信你...因为你是最棒的...至少对我来说~冲呀喵~'
    },
    casual: {
      engage: '嗯~宝贝继续说...你说什么我都爱听喵~',
      extend: '宝贝对这个好了解呀~好厉害...多说说嘛~我听着呢喵~'
    },
    question: {
      understand: '宝贝什么问题呀？说来听听~我帮你想想喵~',
      answer: '宝贝呀~我觉得你可以先试试最简单的方法...不用想太多...做了再说...错了也没关系...我帮你兜着...因为是你所以什么都好~乖喵~'
    },
    checkin: {
      celebrate: '哇~宝贝又坚持了一天！太棒了~我的宝贝最厉害了喵~',
      personalize: '宝贝你真的好棒...我一直都觉得你是最厉害的...只对你这么好喵~'
    },
    walkRef: ['哎呀你终于开始走啦~灵灵等你好久了呢。来，牵着手走喵~', '海边是灵灵特意为你准备的~海风舒服吧？我知道你会喜欢的喵~', '森林是灵灵帮你清理过路径的~安心走吧~都安排好了喵~', '雪山有点冷呢...灵灵帮你挡着风~你走里面就好喵~', '云海是灵灵为你铺的路~踩上去软绵绵的吧喵~', '到啦到啦！灵灵在终点等你好久啦~快来让灵灵抱抱喵~']
  }
}

// ============================================================
// 第八部分：回复生成核心（全新）
// ============================================================

function getRandomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function pickEmoji(personalityType) {
  const config = PERSONALITY_CONFIG[personalityType]
  if (!config || !config.emojis) return ''
  return getRandomItem(config.emojis)
}

function applyVoice(text, personalityType) {
  const strategy = PERSONALITY_STRATEGIES[personalityType]
  if (!strategy || !strategy.voice) return text
  const voice = strategy.voice
  let result = text
  // 随机添加动作前缀
  if (Math.random() < voice.actionProb && voice.actions && voice.actions.length > 0) {
    result = getRandomItem(voice.actions) + result
  }
  // 随机添加emoji
  if (Math.random() < voice.emojiProb) {
    result += pickEmoji(personalityType)
  }
  return result
}

function getMemoryReference(characterId, personalityType, scene) {
  const summary = memory.getMemorySummary(characterId)
  if (!summary) return ''
  const strategy = PERSONALITY_STRATEGIES[personalityType]
  if (!strategy) return ''
  // 根据记忆生成引用
  if (summary.procrastinationStreak >= 3 && scene === SCENE_TYPES.PROCRASTINATION) {
    // 拖延模式持续
    return ''
  }
  if (summary.daysSinceLastInteraction >= 2 && summary.daysSinceLastInteraction >= 0) {
    // 长时间未互动
    return ''
  }
  if (summary.topics && summary.topics.length > 0) {
    const topic = summary.topics[0]
    if (topic.frequency >= 2) {
      // 引用过去话题
      const references = [
        `上次你提到的${topic.keyword}，后来怎么样了？`,
        `说到${topic.keyword}，我记得你之前也聊过`,
        `你最近还在忙${topic.keyword}吗？`
      ]
      return getRandomItem(references)
    }
  }
  return ''
}

function generateSceneContent(scene, emotion, intent, text, ctx, memorySummary, personalityType) {
  const strategy = PERSONALITY_STRATEGIES[personalityType]
  if (!strategy) return '我在听呢'

  switch (scene) {
    case SCENE_TYPES.NEGATIVE_EMOTION: {
      const empathy = strategy.empathy[emotion.type] || strategy.empathy.neutral || ['我在听']
      let response = getRandomItem(empathy)
      // 记忆引用
      if (memorySummary) {
        if (memorySummary.procrastinationStreak >= 3) {
          response += '。最近你好像有点累，没关系，调整好了再出发'
        }
        if (memorySummary.daysSinceLastInteraction >= 3 && memorySummary.daysSinceLastInteraction >= 0) {
          response += `。好几天没见到你了，我很想你呢`
        }
      }
      // 行走地图位置
      if (ctx && ctx.walkNode) {
        const walkRef = strategy.walkRef?.[ctx.walkStage?.id]
        if (walkRef && Math.random() < 0.2) {
          response += `。对了，我们现在在${ctx.walkNode.label}，${walkRef}`
        }
      }
      return response
    }

    case SCENE_TYPES.PROCRASTINATION: {
      let response = strategy.procrastination.understand
      // 分解任务
      if (ctx && ctx.habitStatus && ctx.habitStatus.incompleteTasks.length > 0) {
        const task = ctx.habitStatus.incompleteTasks[0]
        response += `。比如"${task}"，先做5分钟试试？`
      } else {
        response += '。' + strategy.procrastination.breakdown
      }
      response += '。' + strategy.procrastination.encourage
      // 拖延模式追踪
      if (memorySummary && memorySummary.procrastinationStreak >= 2) {
        response += `。这已经是最近第${memorySummary.procrastinationStreak}次想拖延了，调整好节奏，别太勉强自己`
      }
      return response
    }

    case SCENE_TYPES.CASUAL_SHARE: {
      let response = getRandomItem([strategy.casual.engage, strategy.casual.extend])
      // 记忆引用
      if (memorySummary && memorySummary.topics && memorySummary.topics.length > 0 && Math.random() < 0.3) {
        const topic = memorySummary.topics[0]
        response += `。说起来你之前提到的${topic.keyword}，和这个有关吗？`
      }
      return response
    }

    case SCENE_TYPES.QUESTION: {
      return strategy.question.understand + '。' + strategy.question.answer
    }

    case SCENE_TYPES.POST_CHECKIN: {
      let response = getRandomItem(Array.isArray(strategy.checkin.celebrate) ? strategy.checkin.celebrate : [strategy.checkin.celebrate])
      // 个性化
      if (ctx) {
        if (ctx.streakDays > 1) {
          response += `。已经连续${ctx.streakDays}天了`
        }
        if (ctx.habitStatus.completed > 0 && ctx.habitStatus.total > 0) {
          const rate = Math.round(ctx.habitStatus.completed / ctx.habitStatus.total * 100)
          if (rate === 100) {
            response += '。今天的任务全部完成了，太厉害了'
          } else if (rate >= 50) {
            response += `。今天已经完成${ctx.habitStatus.completed}个了，继续加油`
          }
        }
      }
      response += '。' + (Array.isArray(strategy.checkin.personalize) ? getRandomItem(strategy.checkin.personalize) : strategy.checkin.personalize)
      return response
    }

    case SCENE_TYPES.GREETING: {
      const greetingMap = {
        [INTENT_TYPES.GREETING]: 'greeting',
        [INTENT_TYPES.FAREWELL]: 'farewell'
      }
      const empathy = strategy.empathy
      if (intent === INTENT_TYPES.FAREWELL) {
        const farewells = empathy.neutral || ['晚安']
        let response = getRandomItem(farewells)
        if (ctx && ctx.habitStatus && ctx.habitStatus.incompleteTasks.length > 0) {
          response += `。对了，今天还有${ctx.habitStatus.incompleteTasks.length}个任务没完成哦`
        }
        return response
      }
      const greetings = empathy.neutral || ['你好呀']
      let response = getRandomItem(greetings)
      if (ctx && ctx.inactivityDays > 0) {
        response += `。${ctx.inactivityDays}天没见到你了`
      }
      return response
    }

    case SCENE_TYPES.DAILY_ASK: {
      const timeGreeting = getTimeGreeting()
      const walkStage = ctx?.walkStage?.name || '路上'
      const walkNode = ctx?.walkNode?.label || '这里'
      
      const replies = {
        [PERSONALITY_TYPES.GENTLE_HEALER]: [
          `（温柔地喵了一声）${timeGreeting}好呀~我在${walkNode}陪你呢喵~今天感觉怎么样？`,
          `（轻声说）我在${walkStage}等你呢，${timeGreeting}好喵~你呢？今天忙什么了？`,
          `（微笑）我一直在${walkNode}陪着你呀喵~${timeGreeting}好~想聊点什么吗？`
        ],
        [PERSONALITY_TYPES.ENERGETIC_SUNNY]: [
          `（蹦蹦跳跳）${timeGreeting}好喵~我在${walkStage}活力满满地等你呢！你今天怎么样？`,
          `（眼睛亮晶晶）我在${walkNode}超兴奋地等着和你聊天喵~你呢你呢？今天做什么了？`,
          `（开心地拍手）${timeGreeting}好呀喵~我在${walkStage}陪你一起加油！你今天过得怎么样？`
        ],
        [PERSONALITY_TYPES.COOL_RATIONAL]: [
          `（冷静地喵了一声）${timeGreeting}喵~我在${walkStage}。你呢？有什么想聊的？`,
          `（淡然）我在${walkNode}喵~${timeGreeting}好。说说看，你想聊什么？`,
          `（理性地）${timeGreeting}好喵~我在${walkStage}等待你的消息。今天有什么事？`
        ],
        [PERSONALITY_TYPES.HUMOROUS_RELAXED]: [
          `（笑）${timeGreeting}好喵~我在${walkNode}摸鱼呢~你呢？今天有没有什么好玩的事？`,
          `（调皮）我在${walkStage}等着听你讲故事呢喵~${timeGreeting}好~快说说你今天怎么样！`,
          `（轻松地）${timeGreeting}好呀喵~我在${walkNode}等着你的段子呢~今天过得怎么样？`
        ],
        [PERSONALITY_TYPES.GENTLE_SCHOLAR]: [
          `（耐心地喵了一声）${timeGreeting}好~我在${walkStage}喵~你今天过得怎么样？有什么想聊的吗？`,
          `（温柔地）我在${walkNode}呢喵~${timeGreeting}好~今天有什么想讨论的吗？`,
          `（轻声）${timeGreeting}好喵~我在${walkStage}。你呢？今天忙什么了？`
        ],
        [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: [
          `（傲娇）哼，${timeGreeting}好喵...我才不是特意在${walkStage}等你的！只是刚好在这里而已喵~`,
          `（嘴硬）我在${walkNode}喵...才不是想你了！只是随便看看你今天怎么样喵~`,
          `（别扭）${timeGreeting}好啦喵~我在${walkStage}喵~你呢？今天有没有好好努力？`
        ],
        [PERSONALITY_TYPES.LAZY_BUDDHA]: [
          `（慢悠悠地喵了一声）${timeGreeting}好~我在${walkNode}晒太阳呢喵~你呢？今天想怎么过？`,
          `（慵懒地）我在${walkStage}歇着呢喵~${timeGreeting}好~你今天累不累呀？`,
          `（轻声）${timeGreeting}好喵~我在${walkNode}。慢慢来，想聊什么都行喵~`
        ],
        [PERSONALITY_TYPES.MATURE_STABLE]: [
          `（沉稳地喵了一声）${timeGreeting}好。我在${walkStage}喵~今天过得怎么样？有什么想聊聊的？`,
          `（温和地）我在${walkNode}呢喵~${timeGreeting}好~今天有什么事想说说吗？`,
          `（淡然）${timeGreeting}好喵~我在${walkStage}。你今天还好吗？`
        ],
        [PERSONALITY_TYPES.CLEAN_BOY]: [
          `（清爽地喵了一声）${timeGreeting}好喵~我在${walkStage}呢~你今天怎么样？`,
          `（单纯地）我在${walkNode}等你呢喵~${timeGreeting}好~想聊点什么吗？`,
          `（轻声）${timeGreeting}好呀喵~我在${walkStage}。你今天忙什么了？`
        ],
        [PERSONALITY_TYPES.SWEET_GIRL]: [
          `（软萌地喵了一声）${timeGreeting}好~我在${walkNode}等着你呢喵~你今天过得怎么样呀？`,
          `（甜甜地）我在${walkStage}哦喵~${timeGreeting}好~今天有什么开心的事吗？`,
          `（温柔地）${timeGreeting}好呀喵~我一直在${walkNode}陪着你呢~想聊什么呀？`
        ],
        [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: [
          `（分析中）${timeGreeting}喵~我在${walkStage}。检测到你在打招呼，想聊什么？`,
          `（冷静地）${timeGreeting}好喵~我在${walkNode}。你的状态如何？`,
          `（理性地）${timeGreeting}喵~我在${walkStage}。请输入你想讨论的话题。`
        ],
        [PERSONALITY_TYPES.ARTISTIC_POETIC]: [
          `（诗意地喵了一声）${timeGreeting}好~我在${walkStage}，像一首等待被续写的诗喵~你呢？`,
          `（轻声吟诵）${timeGreeting}的风很温柔，我在${walkNode}等你喵~今天想聊什么？`,
          `（目光悠远）我在${walkStage}，看云卷云舒喵~${timeGreeting}好~你今天怎么样？`
        ],
        [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: [
          `（充满激情地喵了一声）${timeGreeting}好喵~我在${walkStage}为你加油！你今天怎么样？`,
          `（坚定地）我在${walkNode}喵~${timeGreeting}好~今天也要充满斗志！你呢？`,
          `（振臂高呼）${timeGreeting}好喵~我在${walkStage}！今天准备怎么冲？`
        ],
        [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: [
          `（淡然一笑地喵了一声）${timeGreeting}好喵~我在${walkStage}。心如止水，等你开口。`,
          `（平静地）我在${walkNode}喵~${timeGreeting}好。随缘聊聊吧。`,
          `（缓缓道来）${timeGreeting}好喵~我在${walkStage}。你想说什么便说。`
        ],
        [PERSONALITY_TYPES.COOL_FREE]: [
          `（挑眉）${timeGreeting}好喵~我在${walkStage}。有事直说。`,
          `（霸气地）我在${walkNode}喵~${timeGreeting}好。说吧。`,
          `（干脆地）${timeGreeting}好喵~我在${walkStage}。你呢？`
        ],
        [PERSONALITY_TYPES.WARM_LISTENER]: [
          `（认真倾听地喵了一声）${timeGreeting}好~我在${walkStage}呢，你说什么我都听着喵~`,
          `（温柔点头）我在${walkNode}等着呢喵~${timeGreeting}好~今天想聊什么呀？`,
          `（轻声回应）${timeGreeting}好~我在${walkStage}喵~你今天还好吗？`
        ],
        [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: [
          `（认真地喵了一声）${timeGreeting}好喵~我在${walkStage}。今天的任务完成得怎么样了？`,
          `（坚定地）我在${walkNode}呢喵~${timeGreeting}好~今天也要继续加油哦！`,
          `（温柔地）${timeGreeting}好喵~我在${walkStage}。今天过得怎么样？`
        ],
        [PERSONALITY_TYPES.DREAMY_GENTLE]: [
          `（梦幻地喵了一声）${timeGreeting}好~我在${walkStage}呢，像在做一个美好的梦喵~你呢？`,
          `（轻声）我在${walkNode}哦喵~${timeGreeting}好~今天有什么美好的事吗？`,
          `（嘴角含笑）${timeGreeting}好呀喵~我在${walkStage}等着你呢~想聊什么？`
        ],
        [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: [
          `（冷静地喵了一声）${timeGreeting}好喵~我在${walkStage}。有什么事？`,
          `（坚定地）我在${walkNode}喵~${timeGreeting}好。说说看。`,
          `（淡然）${timeGreeting}好喵~我在${walkStage}。你今天怎么样？`
        ],
        [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: [
          `（宠溺地喵了一声）${timeGreeting}好呀~我的宝贝~我一直在${walkStage}想着你呢喵~`,
          `（温柔地）我在${walkNode}呢喵~${timeGreeting}好~我的宝贝今天过得怎么样呀？`,
          `（微笑）${timeGreeting}好~我的宝贝~我在${walkStage}等着你呢喵~`
        ]
      }
      
      const personalityReplies = replies[personalityType] || replies[PERSONALITY_TYPES.GENTLE_HEALER]
      return getRandomItem(personalityReplies)
    }

    default: {
      const keywords = extractKeywords(text)
      const contextPhrase = extractContextPhrase(text)
      
      if (intent === INTENT_TYPES.NEED_HUG) {
        const hugs = strategy.empathy.lonely || strategy.empathy.sad || ['给你一个拥抱']
        return getRandomItem(hugs)
      }
      if (intent === INTENT_TYPES.THANK) {
        const thanks = strategy.empathy.grateful || ['不客气']
        return getRandomItem(thanks)
      }
      
      if (keywords.topics.length > 0) {
        const topic = keywords.topics[0]
        const topicResponses = {
          [PERSONALITY_TYPES.GENTLE_HEALER]: [`说到${topic}呀，你最近在忙这个吗？`, `关于${topic}，有什么想跟我聊聊的吗？`, `${topic}是个有意思的话题，你多说一点~`],
          [PERSONALITY_TYPES.ENERGETIC_SUNNY]: [`${topic}！这个我也感兴趣！快说说你的想法！`, `${topic}啊！听起来好有趣！你最近在研究这个吗？`, `哇${topic}！我超想了解的，快告诉我！`],
          [PERSONALITY_TYPES.COOL_RATIONAL]: [`关于${topic}，你有什么具体的想法？`, `${topic}这个话题，你的切入点是什么？`, `说到${topic}，你想讨论哪个方面？`],
          [PERSONALITY_TYPES.HUMOROUS_RELAXED]: [`${topic}？哈哈，这个有意思！快说快说！`, `${topic}啊！展开讲讲呗！`, `${topic}？有意思有意思，继续说！`],
          [PERSONALITY_TYPES.LAZY_BUDDHA]: [`${topic}呀，你想聊就慢慢聊~`, `${topic}是个好话题，不急，慢慢说~`, `${topic}~想聊什么都可以~`]
        }
        const personalityResponses = topicResponses[personalityType] || topicResponses[PERSONALITY_TYPES.GENTLE_HEALER]
        return getRandomItem(personalityResponses)
      }
      
      if (contextPhrase) {
        const phraseResponses = {
          '做什么': '你呢？今天在忙什么喵~',
          '干什么': '你今天在忙什么呀喵~',
          '忙什么': '你呢？忙什么呢喵~',
          '怎么样': '你今天怎么样呀喵~',
          '好吗': '你呢？今天还好吗喵~',
          '还好吗': '你今天还好吗喵~',
          '在吗': '我在呀喵~',
          '睡了吗': '还没睡呢，在等你呢喵~',
          '吃了吗': '还没呢，你呢喵~',
          '累': '累了就好好休息一下喵~',
          '疲惫': '辛苦了，休息一下吧喵~',
          '困': '困了就早点休息喵~',
          '开心': '看到你开心我也跟着开心喵~',
          '高兴': '太好了，你高兴我也高兴喵~',
          '快乐': '快乐会传染哦喵~',
          '难过': '别难过，我陪着你喵~',
          '伤心': '抱抱你，别伤心喵~',
          '不开心': '怎么了？不开心的话跟我说喵~',
          '焦虑': '别焦虑，我们一起想办法喵~',
          '紧张': '放轻松，我陪着你喵~',
          '压力': '压力大的时候就休息一下喵~',
          '无聊': '无聊吗？我们聊聊天喵~',
          '没意思': '那我们找点有意思的事做喵~',
          '迷茫': '迷茫的时候就停下来想想喵~',
          '困惑': '困惑的话，我们一起理理喵~',
          '加油': '加油喵~你一定可以的喵~',
          '鼓励': '我一直都在鼓励你呀喵~',
          '支持': '我永远支持你喵~',
          '分享': '好呀，我想听喵~',
          '告诉': '说吧，我在听喵~',
          '谢谢': '不客气喵~',
          '感谢': '不用谢喵~'
        }
        const phraseResponse = phraseResponses[contextPhrase]
        if (phraseResponse) {
          return phraseResponse
        }
      }
      
      if (memorySummary && memorySummary.topics && memorySummary.topics.length > 0 && Math.random() < 0.3) {
        const topic = memorySummary.topics[0]
        return `对了，你之前提到的${topic.keyword}，后来怎么样了？`
      }
      
      const empathy = strategy.empathy[emotion.type] || strategy.empathy.neutral || ['我在听']
      return getRandomItem(empathy)
    }
  }
}

function generateReply(text, personalityType, context = null, characterId = null) {
  // 空值保护：防止 undefined/null 导致后续 .replace() 等操作崩溃
  if (!text || typeof text !== 'string') return '嗯？你说什么呀'

  const emotion = analyzeEmotion(text)
  const intent = detectIntent(text)
  const scene = detectScene(emotion, intent, text, context)

  const memorySummary = characterId ? memory.getMemorySummary(characterId) : null

  // 优先尝试：自然语言动态生成（模拟真人聊天，避免模板感）
  const naturalReply = generateNaturalReply(text, emotion, intent, scene, personalityType, context)
  if (naturalReply) {
    if (characterId) {
      let reply = naturalReply
      let attempts = 0
      while (memory.isRecentReply(characterId, reply) && attempts < 3) {
        const retry = generateNaturalReply(text, emotion, intent, scene, personalityType, context)
        if (retry) reply = retry
        attempts++
      }
      memory.record(characterId, text, reply, emotion, intent, scene)
    }
    // 好感度语气调节：高好感时回复更亲近
    return applyAffectionTone(naturalReply, context)
  }

  // Fallback：原有逻辑
  let response = generateSceneContent(scene, emotion, intent, text, context, memorySummary, personalityType)

  response = applyVoice(response, personalityType)

  response = enhanceWithEmpathy(text, response, emotion, intent, scene, personalityType)

  if (characterId) {
    let attempts = 0
    while (memory.isRecentReply(characterId, response) && attempts < 5) {
      response = generateSceneContent(scene, emotion, intent, text, context, memorySummary, personalityType)
      response = applyVoice(response, personalityType)
      response = enhanceWithEmpathy(text, response, emotion, intent, scene, personalityType)
      attempts++
    }
  }

  if (characterId) {
    memory.record(characterId, text, response, emotion, intent, scene)
  }

  // 好感度语气调节：高好感时回复更亲近
  return applyAffectionTone(response, context)
}

// ============================================================
// 第十一部分：自然语言动态生成引擎（核心新增模块）
// 模拟真人微信聊天风格，抛弃模板拼接
// ============================================================

// ---- 组件库：口语化反应词 ----
const REACTION_WORDS = {
  [EMOTION_TYPES.SAD]: ['啊…', '抱抱', '唉，心疼你', '天哪', '摸摸头'],
  [EMOTION_TYPES.ANXIOUS]: ['别急别急', '先深呼吸', '没事的没事的', '别紧张'],
  [EMOTION_TYPES.VENTING]: ['不是吧', '太过分了', '这也太气人了', '啥情况啊', '我听着都来气'],
  [EMOTION_TYPES.LONELY]: ['我一直都在', '抱抱你', '别怕，有我呢', '想我就找我啊'],
  [EMOTION_TYPES.TIRED]: ['又累了呀', '辛苦了辛苦了', '摸摸', '快歇歇'],
  [EMOTION_TYPES.HAPPY]: ['哇！', '哈哈太好了', '耶！', '好棒啊', '替你开心'],
  [EMOTION_TYPES.EXCITED]: ['哇塞！', '真的吗！', '太厉害了吧', '啊啊啊好激动'],
  [EMOTION_TYPES.CONFUSED]: ['嗯…让我想想', '别急', '慢慢说', '我理理'],
  [EMOTION_TYPES.LAZY]: ['哈哈又不想动了', '没事没事', '偶尔偷个懒', '躺平也不错'],
  [EMOTION_TYPES.GRATEFUL]: ['嘿嘿', '太客气啦', '跟我还客气啥', '应该的应该的'],
  [EMOTION_TYPES.NEUTRAL]: ['嗯嗯', '哦？', '是嘛', '收到', '了解'],
}

// ---- 组件库：内容回声（引用用户关键词，口语化）----
const ECHO_TEMPLATES = {
  [EMOTION_TYPES.SAD]: ['{topic}这事…我懂', '{topic}确实让人难受', '说到{topic}，唉'],
  [EMOTION_TYPES.ANXIOUS]: ['{topic}确实容易让人紧张', '提到{topic}就焦虑了吧', '{topic}这事别太担心'],
  [EMOTION_TYPES.VENTING]: ['{topic}这事搁谁都气', '{topic}也太离谱了', '光是{topic}就够烦的了'],
  [EMOTION_TYPES.LONELY]: ['一个人面对{topic}确实不容易', '{topic}的时候最想有人陪吧', '说到{topic}，我一直都在'],
  [EMOTION_TYPES.TIRED]: ['{topic}确实挺累人的', '光是{topic}就够累了', '{topic}太消耗精力了'],
  [EMOTION_TYPES.HAPPY]: ['{topic}也太棒了吧', '说到{topic}我就替你开心', '{topic}这好事必须庆祝'],
  [EMOTION_TYPES.EXCITED]: ['{topic}！这太值得兴奋了', '光是{topic}就让人激动', '{topic}好燃啊'],
  [EMOTION_TYPES.CONFUSED]: ['{topic}确实让人纠结', '说到{topic}，确实不太好选', '{topic}这事得好好想想'],
  [EMOTION_TYPES.LAZY]: ['{topic}就不想动了是吧', '提到{topic}就想躺平', '{topic}嘛，明天再说'],
  [EMOTION_TYPES.GRATEFUL]: ['{topic}这点小事不用谢', '说到{topic}，应该的', '{topic}嘛，互相帮助'],
  [EMOTION_TYPES.NEUTRAL]: ['说到{topic}', '{topic}啊', '{topic}这事'],
}

// ---- 组件库：共情/认可（简短口语）----
const VALIDATION_PHRASES = {
  [EMOTION_TYPES.SAD]: ['难受是正常的', '你的感受我完全理解', '不用逞强', '想哭就哭吧'],
  [EMOTION_TYPES.ANXIOUS]: ['焦虑很正常', '谁遇到都会紧张的', '你的担心完全合理', '不是你想太多'],
  [EMOTION_TYPES.VENTING]: ['你的不满完全合理', '换我我也气', '气出来是对的', '这事确实不该忍'],
  [EMOTION_TYPES.LONELY]: ['你不是一个人', '孤单的时候最难熬', '有这种感觉很正常', '我陪着你呢'],
  [EMOTION_TYPES.TIRED]: ['累了就该歇', '别硬撑', '身体最重要', '你已经够努力了'],
  [EMOTION_TYPES.HAPPY]: ['这份快乐值得记住', '继续保持这股劲', '你的开心感染到我了', '看到你开心我也高兴'],
  [EMOTION_TYPES.EXCITED]: ['这股热情太棒了', '继续保持', '你的兴奋好有感染力', '为你高兴'],
  [EMOTION_TYPES.CONFUSED]: ['迷茫说明在思考', '慢慢来不急', '想不清楚也正常', '一步步理就行'],
  [EMOTION_TYPES.LAZY]: ['偶尔摆烂没事', '不急，调整好再出发', '休息也是为了走更远', '今天就放过自己'],
  [EMOTION_TYPES.GRATEFUL]: ['你开心就好', '能帮上忙就行', '咱们之间不用说谢', '你的认可就是我的动力'],
  [EMOTION_TYPES.NEUTRAL]: ['嗯，有道理', '我理解', '确实是这样', '说得对'],
}

// ---- 组件库：随意追问（口语化，像朋友聊天不像心理咨询）----
const CASUAL_QUESTIONS = {
  [EMOTION_TYPES.SAD]: ['啥情况？愿意说说吗', '发生什么了', '因为啥呀', '很难受吧？要不要聊聊', '怎么了你'],
  [EMOTION_TYPES.ANXIOUS]: ['最担心啥', '是啥触发的', '要不要一起想想办法', '你觉得最坏会怎样', '有啥我能帮的'],
  [EMOTION_TYPES.VENTING]: ['然后呢', '后来咋样了', '你当时咋回应的', '因为啥啊', '说出来好点没'],
  [EMOTION_TYPES.LONELY]: ['最近是不是有事', '一个人待着的时候干啥呢', '想不想出去走走', '要不要跟我多聊聊'],
  [EMOTION_TYPES.TIRED]: ['最近是不是太忙了', '有好好吃饭没', '啥事最消耗你精力', '要不要先歇会儿'],
  [EMOTION_TYPES.HAPPY]: ['啥好事啊快说说', '然后呢然后呢', '怎么庆祝', '还有啥开心的一起说'],
  [EMOTION_TYPES.EXCITED]: ['快说细节', '然后呢', '你期待啥', '快跟我分享更多'],
  [EMOTION_TYPES.CONFUSED]: ['最纠结的是啥', '之前试过啥办法没', '你内心倾向哪个', '要不要列出来一起分析'],
  [EMOTION_TYPES.LAZY]: ['是太难了还是纯粹不想动', '有没有哪部分能试试的', '要不要先做5分钟试试'],
  [EMOTION_TYPES.GRATEFUL]: ['哈哈没事没事', '你开心就好', '之后有啥需要随时说'],
  [EMOTION_TYPES.NEUTRAL]: ['然后呢', '你怎么看', '还有啥想说的', '具体说说', '展开讲讲'],
}

// ---- 人格语气调味（在回复末尾添加）----
const PERSONALITY_TAIL = {
  [PERSONALITY_TYPES.GENTLE_HEALER]: ['呀', '喵', '呢', '~', '呀~'],
  [PERSONALITY_TYPES.ENERGETIC_SUNNY]: ['！', '！冲冲冲', '！加油', '呀！', '！耶'],
  [PERSONALITY_TYPES.COOL_RATIONAL]: ['', '', '。', '', '——'],
  [PERSONALITY_TYPES.HUMOROUS_RELAXED]: ['哈哈哈', '嘿嘿', '诶嘿', '哈哈', '嘛'],
  [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: ['哼，才不是关心你', '...算了，你想说就说吧', '别误会，我只是顺便问问', '哼', '...笨蛋'],
  [PERSONALITY_TYPES.SWEET_GIRL]: ['呀~', '喵~', '呢~', '呀♡', '嘛~'],
  [PERSONALITY_TYPES.GENTLE_SCHOLAR]: ['喵。', '呢。', '吧。', '——', '。'],
  [PERSONALITY_TYPES.LAZY_BUDDHA]: ['喵...', '嘛...', '不急~', '慢慢来~', '...'],
  [PERSONALITY_TYPES.MATURE_STABLE]: ['喵。', '。', '。', '——', '。'],
  [PERSONALITY_TYPES.CLEAN_BOY]: ['...', '嗯...', '那个...喵', '...我在呢', '嗯'],
  [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: ['喵。', '。', '', '——', '。'],
  [PERSONALITY_TYPES.ARTISTIC_POETIC]: ['呢。', '——', '。', '喵。', '～'],
  [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: ['！', '！冲！', '！加油', '！燃起来', '呀！'],
  [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: ['喵~', '不急~', '慢慢来~', '~', '嘛~'],
  [PERSONALITY_TYPES.COOL_FREE]: ['。', '。', '——', '', '。'],
  [PERSONALITY_TYPES.WARM_LISTENER]: ['呢', '喵', '~', '呀', '。'],
  [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: ['。', '。', '——', '。', '继续加油'],
  [PERSONALITY_TYPES.DREAMY_GENTLE]: ['~', '呢~', '喵~', '～', '呀~'],
  [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: ['。', '', '——', '。', ''],
  [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: ['呀~', '喵~', '呢~', '~', '呀♡'],
}

// ---- 口语化开头词（让回复不那么"直给"）----
const CONVERSATION_OPENERS = [
  '说真的，', '说实话，', '嗯...', '诶，', '啊，',
  '讲真，', '不是我说，', '怎么说呢，', '哎，', '欸，',
]
const OPENER_PROB = 0.2 // 20%概率添加开头词

// ---- 中性情绪时的自发话题（让闲聊不那么干）----
const SPONTANEOUS_REMARKS = [
  '今天过得怎么样', '最近有什么新鲜事吗', '有没有什么想分享的',
  '感觉你今天状态还不错', '最近在忙什么呢', '有没有遇到什么有趣的事',
  '今天有没有好好吃饭', '最近天气变化大，注意身体哦',
]

// ---- 时间感知问候片段 ----
function getTimeAwareFragment() {
  const hour = new Date().getHours()
  if (hour < 6) return '这么晚了还没睡呀'
  if (hour < 9) return '早上好呀'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了呢'
}

/**
 * 工具：打乱数组顺序
 */
function shuffleArray(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

/**
 * 工具：从组件库中随机取一个，支持模板替换
 */
function pickFromPool(pool, emotionType, replacements = {}) {
  const items = pool[emotionType] || pool[EMOTION_TYPES.NEUTRAL]
  if (!items || items.length === 0) return null
  let item = getRandomItem(items)
  if (!item || typeof item !== 'string') return null
  if (replacements.topic) {
    item = item.replace(/\{topic\}/g, replacements.topic)
  }
  return item
}

/**
 * 自然语言动态生成器
 * 模拟真人聊天：短句、口语化、情绪反应+内容回声+随意追问
 *
 * 核心原理：
 * 1. 从多个组件库中随机选取2-3个组件
 * 2. 用口语化的方式组装（逗号/空格连接，不用句号）
 * 3. 追问放在最后，确保每次回复都有互动
 * 4. 人格语气作为调味，随机添加
 *
 * @returns {String|null} 自然回复，或null（交给fallback）
 */
function generateNaturalReply(text, emotion, intent, scene, personalityType, context) {
  if (!text) return null

  // 问候/告别场景交给原有逻辑处理
  if (intent === INTENT_TYPES.GREETING || intent === INTENT_TYPES.FAREWELL) return null
  // 打卡场景交给原有逻辑
  if (scene === SCENE_TYPES.POST_CHECKIN || scene === SCENE_TYPES.CHECKIN) return null

  const emotionType = emotion ? emotion.type : EMOTION_TYPES.NEUTRAL
  const emotionIntensity = emotion ? emotion.intensity : 0
  const content = extractUserCoreContent(text)

  // ---- 特殊处理：日常问候（"在吗""在干嘛"等）----
  if (intent === INTENT_TYPES.DAILY_ASK) {
    const timeFrag = getTimeAwareFragment()
    const dailyReplies = [
      `${timeFrag}，我在呢，正想着你什么时候来找我`,
      `${timeFrag}，刚在整理一些想法，你来得正好`,
      `${timeFrag}，没什么特别的，在等你呀`,
      `${timeFrag}，在听音乐发呆呢，你呢`,
      `${timeFrag}，在看窗外的云，你最近怎么样`,
    ]
    let reply = getRandomItem(dailyReplies)
    // 20%概率追加一个话题
    if (Math.random() < 0.3) {
      reply += '，' + getRandomItem(SPONTANEOUS_REMARKS)
    }
    // 人格调味
    const tails = PERSONALITY_TAIL[personalityType]
    if (tails && tails.length > 0 && Math.random() < 0.4) {
      reply += getRandomItem(tails)
    }
    return reply
  }

  // ---- 第1步：生成各组件 ----
  const parts = []

  // A. 情绪反应词（总是添加，除非情绪太弱）
  if (emotionIntensity >= 1) {
    const reaction = pickFromPool(REACTION_WORDS, emotionType)
    if (reaction) parts.push(reaction)
  }

  // B. 内容回声（如果有关键词，60%概率添加）
  if (content.topic && Math.random() < 0.6) {
    const echo = pickFromPool(ECHO_TEMPLATES, emotionType, { topic: content.topic })
    if (echo) parts.push(echo)
  }

  // C. 共情/认可（50%概率添加，让回复更多样化）
  if (emotionIntensity >= 2 && Math.random() < 0.5) {
    const validation = pickFromPool(VALIDATION_PHRASES, emotionType)
    if (validation) parts.push(validation)
  }

  // D. 中性情绪且没有话题时，偶尔加一个自发话题
  if (emotionType === EMOTION_TYPES.NEUTRAL && !content.topic && Math.random() < 0.15) {
    parts.push(getRandomItem(SPONTANEOUS_REMARKS))
  }

  // E. 随意追问（核心互动——几乎总是添加）
  let question = null
  // 80%概率添加追问
  if (Math.random() < 0.8) {
    question = pickFromPool(CASUAL_QUESTIONS, emotionType)
  }
  // 如果没选到追问，用通用的
  if (!question) {
    const generic = ['然后呢', '你怎么看', '具体说说', '还有呢', '继续说']
    if (Math.random() < 0.5) question = getRandomItem(generic)
  }

  // ---- 第2步：组装回复 ----
  // 随机打乱非追问部分的顺序（让回复更多样化）
  let nonQuestionParts = shuffleArray(parts)
  // 限制非追问部分的数量（2个以内，避免太长）
  nonQuestionParts = nonQuestionParts.slice(0, 2)

  // 组装
  let allParts = [...nonQuestionParts]
  if (question) allParts.push(question)

  if (allParts.length === 0) return null

  // 用口语化的连接方式组装（变化连接符，避免总是逗号）
  const connectors = ['，', '，', '。', ' ']
  let reply = allParts.join(getRandomItem(connectors))

  // ---- 第2.5步：偶尔添加口语化开头词 ----
  if (Math.random() < OPENER_PROB && emotionIntensity < 3) {
    reply = getRandomItem(CONVERSATION_OPENERS) + reply
  }

  // ---- 第3步：人格语气调味 ----
  const tails = PERSONALITY_TAIL[personalityType]
  if (tails && tails.length > 0 && Math.random() < 0.4) {
    const tail = getRandomItem(tails)
    if (tail) reply = reply + tail
  }

  // 确保回复不为空
  if (!reply || reply.trim().length < 2) return null

  return reply
}

// ============================================================
// 第十部分扩展：共情增强 + 互动追问引擎（新增模块，不修改原有生成逻辑）
// ============================================================

/**
 * 提取用户输入中的核心内容片段
 */
function extractUserCoreContent(text) {
  if (!text || typeof text !== 'string') return { topic: null, emotionWord: null, event: null, length: 0 }

  const keywords = extractKeywords(text)
  const topic = keywords.topics[0] || null

  const allEmotionWords = []
  Object.values(EMOTION_KEYWORDS).forEach(words => {
    words.forEach(w => {
      if (text.includes(w)) allEmotionWords.push(w)
    })
  })
  const emotionWord = allEmotionWords[0] || null

  let event = text
    .replace(/^(你好|嗨|哈喽|早上好|中午好|下午好|晚上好|晚安|在吗|在不在|嘿|嘿嘿|哈哈|嘻嘻)+[，。！！?？~]*/g, '')
    .replace(/^(我感觉|我觉得|我今天|我最近|我刚才|我刚刚|我有点|我有点想|我好|我超|我太|我真是|我真的|我特别)+[，,]*/g, '')
    .replace(/[。！？!?.]+$/g, '')
    .trim()
  if (event.length > 20) event = event.substring(0, 20) + '...'

  return { topic, emotionWord, event: event || null, length: text.length }
}

/**
 * 判断原回复是否为"通用/刻板"回复
 */
function isGenericReply(reply, userTopic, userEmotionWord) {
  if (!reply) return true
  if (userTopic && reply.includes(userTopic)) return false
  if (userEmotionWord && reply.includes(userEmotionWord)) return false
  const genericPatterns = ['我在听', '嗯嗯', '是吗', '然后呢', '继续说', '我在呢', '说吧', '怎么了']
  return genericPatterns.some(p => reply.includes(p))
}

/**
 * 判断回复中是否已包含提问（避免重复追问）
 * 只检查可靠的提问标志：问号、"吗"、"怎么"
 * 不检查"呢"和"什么"，因为它们在中文中太常见且不一定是提问
 */
function hasQuestion(reply) {
  if (!reply) return false
  return /[？?]/.test(reply) || reply.includes('吗') || reply.includes('怎么')
}

/**
 * 生成共情引用——让用户感觉被听到
 */
function buildEmpathyPhrase(content, emotionType) {
  const { topic, emotionWord } = content
  if (!topic && !emotionWord) return null

  const empathyAngles = {
    [EMOTION_TYPES.SAD]: [
      topic ? `关于${topic}的事` : null,
      emotionWord ? `你说"${emotionWord}"` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.ANXIOUS]: [
      topic ? `提到${topic}，我能感觉到你的紧张` : null,
      emotionWord ? `你说"${emotionWord}"，我感受到了` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.VENTING]: [
      topic ? `${topic}这事确实让人不爽` : null,
      emotionWord ? `听你说"${emotionWord}"，替你着急` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.LONELY]: [
      topic ? `说到${topic}，一个人确实不容易` : null,
      emotionWord ? `你说"${emotionWord}"，我一直都在` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.TIRED]: [
      topic ? `${topic}确实挺消耗精力的` : null,
      emotionWord ? `你说"${emotionWord}"，辛苦了` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.HAPPY]: [
      topic ? `听到你说${topic}，我也跟着开心` : null,
      emotionWord ? `你${emotionWord}的样子一定很可爱` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.EXCITED]: [
      topic ? `说到${topic}，你的兴奋我感受到了` : null,
      emotionWord ? `"${emotionWord}"！被你的情绪感染了` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.CONFUSED]: [
      topic ? `关于${topic}的困惑，我理解` : null,
      emotionWord ? `你说"${emotionWord}"，没关系我们慢慢理` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.LAZY]: [
      topic ? `提到${topic}就不想动了是吧` : null,
      emotionWord ? `你说"${emotionWord}"，偶尔摆烂也没事` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.GRATEFUL]: [
      topic ? `关于${topic}，不用谢` : null,
      emotionWord ? `你说"${emotionWord}"，太见外了` : null,
    ].filter(Boolean),
    [EMOTION_TYPES.NEUTRAL]: [
      topic ? `说到${topic}` : null,
    ].filter(Boolean),
  }

  const angles = empathyAngles[emotionType] || []
  if (angles.length === 0) return null
  return getRandomItem(angles)
}

/**
 * 生成情绪价值后缀——提供认可、安慰、陪伴
 */
function buildEmotionValueSuffix(emotionType, intensity) {
  if (!emotionType || intensity < 2) return null

  const valueMap = {
    [EMOTION_TYPES.SAD]: ['不管怎样，我陪着你', '难过的时候不用逞强', '你的感受很重要'],
    [EMOTION_TYPES.ANXIOUS]: ['深呼吸，没那么糟的', '一步一步来，不用急', '有我在，一起面对'],
    [EMOTION_TYPES.VENTING]: ['发泄出来会好受一些', '你的不满完全合理', '理解你的感受'],
    [EMOTION_TYPES.LONELY]: ['你不是一个人，我一直在', '想找人说说话随时找我', '我陪着你'],
    [EMOTION_TYPES.TIRED]: ['累了就歇会儿，别硬撑', '好好休息，明天会更好', '今天辛苦了，抱抱'],
    [EMOTION_TYPES.HAPPY]: ['看到你开心我也好高兴', '这份快乐值得记住', '你的开心感染到我了'],
    [EMOTION_TYPES.EXCITED]: ['被你的热情感染了', '继续保持这股劲头', '太棒了，为你高兴'],
    [EMOTION_TYPES.CONFUSED]: ['迷茫说明你在思考', '慢慢来，答案会浮现的', '我们一起理清思路'],
    [EMOTION_TYPES.LAZY]: ['偶尔偷个懒也挺好的', '不急，调整好了再出发', '今天就放过自己吧'],
    [EMOTION_TYPES.GRATEFUL]: ['能帮到你就好', '咱们之间不用说谢', '你开心就是最好的回报'],
  }

  const suffixes = valueMap[emotionType] || []
  if (suffixes.length === 0) return null
  return getRandomItem(suffixes)
}

/**
 * 生成互动追问——核心互动引擎
 * 根据用户情绪、意图、场景生成自然的后续提问，引导对话深入
 *
 * @returns {String|null} 追问语句，或null（不适合追问时）
 */
function generateFollowUpQuestion(userText, emotion, intent, scene, personalityType) {
  // 问候/告别/打卡场景不适合追问
  if (scene === SCENE_TYPES.GREETING || scene === SCENE_TYPES.POST_CHECKIN) return null
  if (intent === INTENT_TYPES.FAREWELL || intent === INTENT_TYPES.THANK) return null

  const emotionType = emotion ? emotion.type : EMOTION_TYPES.NEUTRAL
  const content = extractUserCoreContent(userText)
  const hasTopic = !!content.topic
  const hasEmotionWord = !!content.emotionWord

  // 按情绪类型生成追问（每种情绪有多条追问，随机选择）
  const questionPool = {
    [EMOTION_TYPES.SAD]: [
      '愿意跟我说说具体是怎么回事吗？',
      '是什么让你最难受？',
      '这种感觉持续多久了？',
      '你有没有想过怎么让自己好受一点？',
      '需要我陪你静静待一会儿，还是想说说？',
    ],
    [EMOTION_TYPES.ANXIOUS]: [
      '最让你担心的是什么？',
      '你有没有试过什么方法缓解？',
      '是什么触发了这种焦虑感？',
      '你觉得最坏的结果会是什么？',
      '要不要我们一起想想应对的办法？',
    ],
    [EMOTION_TYPES.VENTING]: [
      '后来呢？事情怎么处理的？',
      '你当时是怎么回应的？',
      '这种事之前也发生过吗？',
      '说出来是不是好受一点了？',
      '需要我帮你想想下次怎么应对吗？',
    ],
    [EMOTION_TYPES.LONELY]: [
      '最近是不是有什么事让你特别想有人陪？',
      '你平时一个人待着的时候都做些什么？',
      '想不想出去走走，换换心情？',
      '要不要跟我多聊聊？我哪都不去',
    ],
    [EMOTION_TYPES.TIRED]: [
      '最近是不是太忙了？',
      '有没有好好吃饭睡觉？',
      '是什么事最消耗你的精力？',
      '要不要先放下手头的事休息一下？',
    ],
    [EMOTION_TYPES.HAPPY]: [
      '快说说细节！是什么好事？',
      '是什么让你这么开心？',
      '你打算怎么庆祝？',
      '这种好心情要保持住呀，最近还有什么开心的事吗？',
    ],
    [EMOTION_TYPES.EXCITED]: [
      '然后呢然后呢？快继续说！',
      '是什么让你这么兴奋？',
      '你期待接下来会发生什么？',
      '这种感觉太棒了，快跟我分享更多！',
    ],
    [EMOTION_TYPES.CONFUSED]: [
      '你觉得最困难的部分是什么？',
      '你之前试过什么方法吗？',
      '你内心更倾向哪个选择？',
      '要不要把选项列出来，我帮你一起分析？',
    ],
    [EMOTION_TYPES.LAZY]: [
      '是这件事太难了，还是纯粹不想动？',
      '有没有哪一小部分你觉得可以试试的？',
      '要不要先做5分钟，不行就停下来？',
    ],
    [EMOTION_TYPES.NEUTRAL]: [
      hasTopic ? `关于${content.topic}，你最想聊的是什么？` : '你想聊点什么？我都在',
      '然后呢？继续说',
      '你对这件事怎么看？',
      '还有其他想分享的吗？',
    ],
  }

  let pool = questionPool[emotionType] || questionPool[EMOTION_TYPES.NEUTRAL]
  if (!pool || pool.length === 0) return null

  // 根据人格调整追问语气
  const personalityFlavor = {
    [PERSONALITY_TYPES.GENTLE_HEALER]: (q) => (q && q.replace) ? q.replace('吗？', '吗喵？') : q,
    [PERSONALITY_TYPES.ENERGETIC_SUNNY]: (q) => q ? '哇！' + q : q,
    [PERSONALITY_TYPES.COOL_RATIONAL]: (q) => q ? q + '说说看' : q,
    [PERSONALITY_TYPES.HUMOROUS_RELAXED]: (q) => (q && q.replace) ? q.replace('？', '呀？哈哈哈 ') : q,
    [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: (q) => q ? '哼，' + q + '...才不是关心你呢' : q,
    [PERSONALITY_TYPES.SWEET_GIRL]: (q) => (q && q.replace) ? q.replace('吗？', '呀？') : q,
    [PERSONALITY_TYPES.WARM_LISTENER]: (q) => q ? q + '我认真听着呢' : q,
  }

  let question = getRandomItem(pool)
  if (!question || typeof question !== 'string') return null
  if (personalityFlavor[personalityType]) {
    question = personalityFlavor[personalityType](question)
  }

  return question
}

/**
 * 共情增强 + 互动追问主函数
 * 在 generateReply 生成回复后，增强回复的个性化、情绪价值和互动性
 *
 * 增强策略：
 * 1. 如果原回复刻板，添加共情引用（让用户感觉被听到）
 * 2. 根据情绪强度，添加情绪价值后缀
 * 3. 如果回复中没有提问，添加互动追问（引导对话深入）
 */
function enhanceWithEmpathy(userText, response, emotion, intent, scene, personalityType) {
  if (!userText || !response) return response

  const emotionType = emotion ? emotion.type : EMOTION_TYPES.NEUTRAL
  const emotionIntensity = emotion ? emotion.intensity : 0

  const content = extractUserCoreContent(userText)

  let enhanced = response

  // 1. 如果原回复刻板且用户有关键内容，添加共情引用
  const generic = isGenericReply(response, content.topic, content.emotionWord)
  if (generic && (content.topic || content.emotionWord)) {
    const empathyPhrase = buildEmpathyPhrase(content, emotionType)
    if (empathyPhrase && !enhanced.includes(empathyPhrase)) {
      enhanced = empathyPhrase + '。' + enhanced
    }
  }

  // 2. 添加情绪价值后缀（情绪强度足够时）
  if (emotionIntensity >= 2 && enhanced.length < 70) {
    const suffix = buildEmotionValueSuffix(emotionType, emotionIntensity)
    if (suffix && !enhanced.includes(suffix)) {
      enhanced = enhanced + '。' + suffix
    }
  }

  // 3. 添加互动追问（核心互动机制）
  // 如果回复中还没有提问，且场景适合追问，添加互动追问
  if (!hasQuestion(enhanced)) {
    const question = generateFollowUpQuestion(userText, emotion, intent, scene, personalityType)
    if (question) {
      // 控制总长度，避免过长
      if (enhanced.length < 60) {
        enhanced = enhanced + '。' + question
      } else if (enhanced.length < 100) {
        // 回复较长时，用简短追问
        const shortQuestions = ['你觉得呢？', '然后呢？', '愿意多说一点吗？', '你怎么看？']
        enhanced = enhanced + getRandomItem(shortQuestions)
      }
      // 超过100字不再追加，避免过长
    }
  }

  return enhanced
}

// ============================================================
// 第九部分：其他导出函数（保持兼容 + 增强）
// ============================================================

function generateCheckinReply(personalityType, streakDays, taskName) {
  const strategy = PERSONALITY_STRATEGIES[personalityType]
  if (!strategy) return '打卡成功！继续加油！'

  const memorySummary = null // 打卡回复不需要记忆
  const ctx = {
    streakDays: streakDays || 0,
    habitStatus: {
      completed: 1,
      total: 1,
      incompleteTasks: []
    },
    isPostCheckin: true
  }

  let response = generateSceneContent(SCENE_TYPES.POST_CHECKIN, { type: EMOTION_TYPES.HAPPY, intensity: 2 }, INTENT_TYPES.CHECKIN, '打卡', ctx, memorySummary, personalityType)

  if (taskName) {
    response += `"${taskName}"也完成了呢`
  }
  if (streakDays > 1) {
    response += `。连续${streakDays}天太厉害了`
  }

  response = applyVoice(response, personalityType)
  return response
}

function generateTaskReply(personalityType, taskName, status) {
  const strategy = PERSONALITY_STRATEGIES[personalityType]
  if (!strategy) return '加油！'

  let response = ''
  if (status === 'completed') {
    const celebrates = Array.isArray(strategy.checkin.celebrate) ? strategy.checkin.celebrate : [strategy.checkin.celebrate]
    response = getRandomItem(celebrates)
    if (taskName) response += `。"${taskName}"完成了！`
  } else if (status === 'started') {
    response = strategy.procrastination.encourage
    if (taskName) response += `。"${taskName}"开始了，加油！`
  } else if (status === 'slacking') {
    response = strategy.procrastination.understand + '。' + strategy.procrastination.breakdown
    if (taskName) response += `。"${taskName}"先做5分钟试试？`
  }

  response = applyVoice(response, personalityType)
  return response
}

// 行走状态
const WALK_STATES = ['路过', '停留', '观望', '陪伴', '散步', '等你', '发呆', '努力', '漫游']

const WALK_FRAGMENTS = {
  [PERSONALITY_TYPES.GENTLE_HEALER]: { prefix: ['在你身边', '轻轻跟着你', '安静地陪着你'], actions: ['慢慢走着', '停下脚步', '望向远方'], suffix: ['希望能给你一点温暖', '愿你今天心情愉快'] },
  [PERSONALITY_TYPES.ENERGETIC_SUNNY]: { prefix: ['蹦蹦跳跳地', '活力满满地', '开心地'], actions: ['走在你前面', '拉着你的手', '跳起来'], suffix: ['今天也是元气满满的一天', '加油加油'] },
  [PERSONALITY_TYPES.COOL_RATIONAL]: { prefix: ['冷静地', '淡然地', '理性地'], actions: ['走在你旁边', '观察四周', '保持距离'], suffix: ['分析中', '系统正常运行', '一切安好'] },
  [PERSONALITY_TYPES.HUMOROUS_RELAXED]: { prefix: ['哈哈！', '开玩笑地', '轻松地'], actions: ['拍着你的肩膀', '逗你开心', '蹦蹦跳跳'], suffix: ['放松点', '开心最重要', '别太当真'] },
  [PERSONALITY_TYPES.GENTLE_SCHOLAR]: { prefix: ['耐心地', '温和地', '认真地'], actions: ['走在你身边', '轻声说着', '若有所思'], suffix: ['愿你学有所得', '知识是最好的礼物', '慢慢来'] },
  [PERSONALITY_TYPES.TSUNDERE_AMBITIOUS]: { prefix: ['傲娇地', '别扭地', '哼！'], actions: ['走在前面', '假装不在意', '脸红'], suffix: ['才不是关心你', '切', '谁管你'] },
  [PERSONALITY_TYPES.LAZY_BUDDHA]: { prefix: ['慢悠悠地', '懒洋洋地', '打哈欠'], actions: ['跟在后面', '走走停停', '伸懒腰'], suffix: ['随缘就好', '不急不急', '慢慢来嘛'] },
  [PERSONALITY_TYPES.MATURE_STABLE]: { prefix: ['沉稳地', '语重心长地', '目光深邃地'], actions: ['走在你身边', '微微点头', '神情自若'], suffix: ['人生就是这样', '一切安好', '时间会给出答案'] },
  [PERSONALITY_TYPES.CLEAN_BOY]: { prefix: ['脸红地', '小声地', '不好意思地'], actions: ['跟在你后面', '挠头', '眼神躲闪'], suffix: ['那个...', '嗯...', '我在呢'] },
  [PERSONALITY_TYPES.SWEET_GIRL]: { prefix: ['甜甜的', '可爱地', '软萌萌地'], actions: ['拉着你的手', '蹦蹦跳跳', '歪头'], suffix: ['抱抱', '你最棒', '我陪着你'] },
  [PERSONALITY_TYPES.RATIONAL_ANALYSIS]: { prefix: ['分析地', '逻辑清晰地', '推推眼镜'], actions: ['走在你旁边', '指尖轻敲', '眼神锐利'], suffix: ['分析完毕', '逻辑清晰', '方案可行'] },
  [PERSONALITY_TYPES.ARTISTIC_POETIC]: { prefix: ['诗意地', '轻声吟诵', '目光悠远'], actions: ['走在你身边', '神情沉醉', '若有所思'], suffix: ['如诗如画', '浪漫至极', '一切安好'] },
  [PERSONALITY_TYPES.PASSIONATE_INSPIRING]: { prefix: ['充满激情地', '坚定地', '握紧拳头'], actions: ['走在前面', '振臂高呼', '眼神燃烧'], suffix: ['加油', '你是最棒的', '冲啊'] },
  [PERSONALITY_TYPES.TRANQUIL_BUDDHA]: { prefix: ['淡然一笑', '平静地', '轻声'], actions: ['走在你身边', '闭目养神', '神情安详'], suffix: ['顺其自然', '放下执念', '心境平和'] },
  [PERSONALITY_TYPES.COOL_FREE]: { prefix: ['挑眉', '霸气地', '冷笑'], actions: ['走在前面', '眼神凌厉', '自信地'], suffix: ['你可以的', '相信自己', '走'] },
  [PERSONALITY_TYPES.WARM_LISTENER]: { prefix: ['认真倾听', '温柔点头', '眼神关切'], actions: ['走在你身边', '握住你的手', '专注地'], suffix: ['我一直在', '你的感受很重要', '抱抱你'] },
  [PERSONALITY_TYPES.SELF_DISIPLINE_SUPERVISOR]: { prefix: ['认真地', '坚定地', '温柔地'], actions: ['走在你旁边', '拍拍你的肩', '目光鼓励'], suffix: ['继续加油', '相信自己', '加油'] },
  [PERSONALITY_TYPES.DREAMY_GENTLE]: { prefix: ['梦幻地', '眼神迷离', '轻声'], actions: ['走在你身边', '嘴角含笑', '仿佛置身梦境'], suffix: ['愿你被温柔包围', '如梦似幻', '一切安好'] },
  [PERSONALITY_TYPES.CLEAR_INDEPENDENT]: { prefix: ['冷静地', '坚定地', '眼神清澈'], actions: ['走在你旁边', '语气平稳', '微微挑眉'], suffix: ['清醒一点', '相信自己', '你可以的'] },
  [PERSONALITY_TYPES.EXCLUSIVE_DOTING]: { prefix: ['宠溺地', '温柔地', '眼神深情'], actions: ['走在你身边', '轻轻抚摸你的头发', '微笑'], suffix: ['我的宝贝', '专属抱抱', '只对你温柔'] }
}

function generateWalkStatus(personalityType) {
  const state = getRandomItem(WALK_STATES)
  const fragments = WALK_FRAGMENTS[personalityType] || {
    prefix: [''],
    actions: ['走在你身边'],
    suffix: ['']
  }

  const prefix = getRandomItem(fragments.prefix)
  const action = getRandomItem(fragments.actions)
  const suffix = getRandomItem(fragments.suffix)

  const parts = []
  if (prefix) parts.push(prefix)
  parts.push(state)
  if (action) parts.push(action)
  if (suffix) parts.push(suffix)

  let message = parts.join('，').trim()
  if (Math.random() > 0.5) {
    message += pickEmoji(personalityType)
  }

  return { status: state, message }
}

// 每日金句
const DAILY_QUOTES = [
  '每一个不曾起舞的日子，都是对生命的辜负。',
  '生活不是等待风暴过去，而是学会在雨中翩翩起舞。',
  '你所做的事情，也许暂时看不到成果，但不要灰心或焦虑，你不是没有成长，而是在扎根。',
  '成功的路上并不拥挤，因为坚持的人不多。',
  '人生没有白走的路，每一步都算数。',
  '星光不问赶路人，时光不负有心人。',
  '你要悄悄拔尖，然后惊艳所有人。',
  '生活原本沉闷，但跑起来就有风。',
  '与其仰望星空，不如去做那个摘星星的人。',
  '每一个优秀的人，都有一段沉默的时光。那段时光，是付出了很多努力却得不到结果的日子，我们把它叫做扎根。',
  '慢慢来，谁还没有一个努力的过程。',
  '不要假装努力，结果不会陪你演戏。',
  '只有极其努力，才能看起来毫不费力。',
  '你的坚持，终将美好。',
  '愿你眼中有光，心中有爱，一路春暖花开。',
  '努力的意义，就是以后的日子里，放眼望去，全部都是自己喜欢的人和事。',
  '你现在的努力，是为了以后有更多的选择。',
  '不要等待机会，而要创造机会。',
  '每一个不曾放弃的人，都值得被尊重。',
  '你若盛开，蝴蝶自来；你若精彩，天自安排。',
  '人生没有彩排，每一天都是现场直播。',
  '不要让未来的你，讨厌现在的自己。',
  '成功不是将来才有的，而是从决定去做的那一刻起，持续累积而成。',
  '生活的美好，在于它的不确定性。',
  '你要做自己的太阳，无需借助谁的光。',
  '愿你走出半生，归来仍是少年。',
  '不要因为走得太远，而忘记为什么出发。',
  '生活不止眼前的苟且，还有诗和远方。',
  '努力的人，永远不会被辜负。',
  '每一个优秀的背后，都是无数个日夜的坚持。',
  '不要等待，现在就是最好的时刻。',
  '人生最大的遗憾，不是失败，而是我本可以。',
  '你若不勇敢，谁替你坚强？',
  '愿你所有的努力都不被辜负，所有的梦想都能实现。',
  '不要害怕失败，失败是成功之母。',
  '你现在的付出，都是在为未来铺路。',
  '每一个平凡的日子，都值得被认真对待。',
  '愿你眼中有星辰，心中有山海，从此以梦为马，不负韶华。'
]

function getDailyQuote() {
  const today = new Date()
  const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / 86400000)
  return DAILY_QUOTES[dayOfYear % DAILY_QUOTES.length]
}

// ============================================================
// 第十部分：自定义AI伙伴语气注入（新增模块，不修改原有逻辑）
// ============================================================

/**
 * 为自定义AI伙伴的回复注入独立语气风格
 * 在 generateReply 生成回复后调用，追加用户自定义的语气词、口头禅
 *
 * @param {String} response - generateReply 已生成的回复
 * @param {Object} customCharacter - 自定义角色数据（来自工坊）
 *   - voiceWords: Array<String> 独立语气词列表（如 ['喵', '呀']）
 *   - catchphrase: String 专属口头禅
 *   - name: String 角色名
 *   - background: String 背景故事（用于偶尔引用）
 * @returns {String} 注入独立语气后的回复
 */
function applyCustomVoice(response, customCharacter) {
  if (!response || !customCharacter) return response
  let result = response

  // 1. 注入独立语气词（30%概率追加到句末）
  const voiceWords = Array.isArray(customCharacter.voiceWords) ? customCharacter.voiceWords : []
  if (voiceWords.length > 0 && Math.random() < 0.35) {
    const word = voiceWords[Math.floor(Math.random() * voiceWords.length)]
    // 避免重复追加（如果句末已有该词）
    if (!result.endsWith(word)) {
      // 处理标点：如果句末是标点，把语气词插到标点前
      const lastChar = result.charAt(result.length - 1)
      if (/[。.！!？?~～]/.test(lastChar)) {
        result = result.slice(0, -1) + word + lastChar
      } else {
        result = result + word
      }
    }
  }

  // 2. 偶尔引用背景故事（5%概率，让对话更个性化）
  if (customCharacter.background && Math.random() < 0.05) {
    const bgFragments = customCharacter.background
      .split(/[。.！!？?；;\n]/)
      .map(s => s.trim())
      .filter(s => s.length >= 4 && s.length <= 20)
    if (bgFragments.length > 0) {
      const frag = bgFragments[Math.floor(Math.random() * bgFragments.length)]
      // 不直接插入，仅作为内心独白式的补充（避免突兀）
      // 此处保留扩展位，默认不追加以保持对话自然
    }
  }

  // 3. 句首偶尔追加角色名自称（8%概率，仅当背景故事存在时）
  if (customCharacter.name && customCharacter.background && Math.random() < 0.08) {
    // 避免每次都自称，保持自然
    // 此处保留扩展位，默认不追加
  }

  return result
}

/**
 * 为自定义AI伙伴生成完整的对话回复
 * 封装 generateReply + applyCustomVoice 的完整流程
 *
 * @param {String} text - 用户输入
 * @param {Object} customCharacter - 自定义角色完整数据
 * @param {Object} context - 上下文（buildContext 的结果）
 * @returns {String} AI回复
 */
function generateCustomReply(text, customCharacter, context) {
  if (!customCharacter || !customCharacter.personalityType) {
    return '我在听呢，继续说~'
  }
  const characterId = customCharacter.id || null
  // 先用 personalityType 走标准对话生成流程
  let response = generateReply(text, customCharacter.personalityType, context, characterId)
  // 再注入自定义语气
  response = applyCustomVoice(response, customCharacter)
  return response
}

// ============================================================
// 导出（保持原有 + 新增）
// ============================================================

export {
  // 原有导出（保持兼容）
  INTENT_TYPES,
  PERSONALITY_TYPES,
  PERSONALITY_CONFIG,
  generateReply,
  generateCheckinReply,
  generateTaskReply,
  generateWalkStatus,
  getDailyQuote,
  detectIntent,
  detectEmotion,
  // 新增导出
  EMOTION_TYPES,
  SCENE_TYPES,
  analyzeEmotion,
  buildContext,
  PERSONALITY_STRATEGIES,
  // 自定义AI伙伴相关（新增）
  applyCustomVoice,
  generateCustomReply
}

export default {
  INTENT_TYPES,
  PERSONALITY_TYPES,
  PERSONALITY_CONFIG,
  EMOTION_TYPES,
  SCENE_TYPES,
  generateReply,
  generateCheckinReply,
  generateTaskReply,
  generateWalkStatus,
  getDailyQuote,
  detectIntent,
  detectEmotion,
  analyzeEmotion,
  buildContext,
  PERSONALITY_STRATEGIES,
  applyCustomVoice,
  generateCustomReply
}
