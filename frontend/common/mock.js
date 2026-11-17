/**
 * Mock 数据服务 - 模拟后端 API 响应
 * 后端就绪后，将 USE_MOCK 设为 false 即可切换到真实 API
 * 统一响应格式: { code: 200, message: "ok", data: {...} }
 */

import { generateReply, analyzeEmotion, PERSONALITY_TYPES } from './ai-dialogue-engine'
import { getCharacterById } from './ai-characters'

// ============ 控制开关 ============
const USE_MOCK = false
const MOCK_DELAY = 400 // 模拟网络延迟(ms)

// ============ 模拟数据 ============

// 用户信息
const mockUser = {
  id: 10001,
  phone: '138****8888',
  nickname: '习惯达人',
  avatar: '',
  gender: 0,
  registerTime: '2026-07-01 10:30:00',
  level: 3,
  levelName: '自律先锋',
  signature: ''
}

// 习惯模板(8种)
const mockTemplates = [
  { id: 1, type: 'morning', name: '早起一杯水', icon: '💧', description: '每天起床后喝一杯温水唤醒身体', defaultTarget: '喝200ml温水', color: '#4FC3F7', difficulty: 'easy', multiplier: 1.0 },
  { id: 2, type: 'sport', name: '运动健身', icon: '🏃', description: '跑步、瑜伽或力量训练', defaultTarget: '运动15分钟', color: '#FF6B6B', difficulty: 'medium', multiplier: 1.5 },
  { id: 3, type: 'read', name: '阅读学习', icon: '📚', description: '读书或学习新技能', defaultTarget: '阅读30分钟', color: '#FFD93D', difficulty: 'medium', multiplier: 1.5 },
  { id: 4, type: 'drink', name: '充足饮水', icon: '🥤', description: '保持每日饮水量', defaultTarget: '喝8杯水', color: '#4DD0E1', difficulty: 'easy', multiplier: 1.0 },
  { id: 5, type: 'sleep', name: '早睡早起', icon: '😴', description: '23点前入睡，7点前起床', defaultTarget: '23:00前入睡', color: '#7986CB', difficulty: 'hard', multiplier: 2.0 },
  { id: 6, type: 'meditate', name: '冥想静心', icon: '🧘', description: '每日冥想放松身心', defaultTarget: '冥想10分钟', color: '#BA68C8', difficulty: 'medium', multiplier: 1.5 },
  { id: 7, type: 'write', name: '日记复盘', icon: '✏️', description: '记录每日所思所想', defaultTarget: '写200字日记', color: '#81C784', difficulty: 'easy', multiplier: 1.0 },
  { id: 8, type: 'code', name: '编程练习', icon: '💻', description: '每日编码保持技术敏感度', defaultTarget: '写1个小程序', color: '#78909C', difficulty: 'hard', multiplier: 2.0 }
]

// 用户习惯(3个)
// last_checkin_date 用于断卡判定：昨天漏卡可补（1天宽限），更早漏卡则连续天数归零
const mockHabits = [
  { id: 101, type: 'morning', name: '早起一杯水', icon: '💧', color: '#4FC3F7', target: '喝200ml温水', difficulty: 'easy', multiplier: 1.0, reminderTime: '07:30', streak: 12, completed: true, sort: 1, last_checkin_date: _todayStr(0) },
  { id: 102, type: 'read', name: '阅读30分钟', icon: '📚', color: '#FFD93D', target: '阅读30分钟', difficulty: 'medium', multiplier: 1.5, reminderTime: '21:00', streak: 5, completed: false, sort: 2, last_checkin_date: _todayStr(-1) },
  { id: 103, type: 'sport', name: '运动15分钟', icon: '🏃', color: '#FF6B6B', target: '运动15分钟', difficulty: 'medium', multiplier: 1.5, reminderTime: '18:00', streak: 3, completed: false, sort: 3, last_checkin_date: _todayStr(-3) }
]

// ---------- 断卡 / 补卡 工具（基于本地日期的连续天数管理） ----------
/** 生成 YYYY-MM-DD 日期串，offset 为相对今天的天数偏移 */
function _todayStr(offset = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

/** 计算 dateStr 距今天的天数；无日期返回 Infinity（视为从未打卡） */
function _daysSince(dateStr) {
  if (!dateStr) return Infinity
  return Math.round((new Date(_todayStr(0)) - new Date(dateStr + 'T00:00:00')) / 86400000)
}

/**
 * 断卡检测：获取列表时对每个习惯执行
 * - 未打卡且距上次打卡超过 0 天 → 连续天数归零，记录 broken_streak
 * - 仅昨日漏卡（missed === 1）保留 can_makeup=true，可在宽限期内补卡恢复
 */
function applyStreakBreak(habit) {
  if (habit.completed) {
    habit.can_makeup = false
    return habit
  }
  // 新建习惯（从未打卡且无历史连续）不做断卡标记
  if (habit.streak <= 0 && !habit.broken_streak) return habit
  const missed = _daysSince(habit.last_checkin_date)
  if (missed <= 0) return habit
  if (!habit.broken) {
    habit.broken = true
    habit.broken_streak = habit.streak
    habit.streak = 0
  }
  // 宽限期动态判定：只有昨天漏卡可补，跨天自动失效
  habit.can_makeup = missed === 1
  return habit
}

// AI角色(20种)
const mockAiRoles = [
  { id: 1, roleType: 'relaxed', name: '林夕', personality: '温柔、善解人意、细腻、包容', description: '温柔如水的治愈系少女，像清晨的露珠般纯净', avatar: '🌿', traits: ['暖心陪伴型', '佛系松弛型', '焦虑敏感型'] },
  { id: 2, roleType: 'relaxed', name: '绵绵', personality: '甜美、乐观、治愈、亲切', description: '像棉花糖一样柔软的女孩，永远带着温暖的笑容', avatar: '☁️', traits: ['佛系松弛型'] },
  { id: 3, roleType: 'y2k', name: 'Yuki', personality: '活泼、潮流、率真、热情', description: 'Y2K风格的元气少女，闪亮的发夹和彩色的穿搭', avatar: '💎', traits: ['完美自律型', '元气少年型'] },
  { id: 4, roleType: 'y2k', name: 'Kira', personality: '酷飒、自信、直率、时尚', description: '甜酷辣妹风格，粉色挑染长发配铆钉装饰', avatar: '🔥', traits: ['完美自律型'] },
  { id: 5, roleType: 'chinese', name: '月清', personality: '优雅、知性、温婉、古典', description: '新中式国风少女，水墨长发配刺绣旗袍', avatar: '🌸', traits: ['焦虑敏感型', '佛系松弛型'] },
  { id: 6, roleType: 'chinese', name: '枫夜', personality: '儒雅、沉稳、博学、谦和', description: '古风少年，长发束冠，手执折扇', avatar: '🍂', traits: ['完美自律型', '智慧导师型'] },
  { id: 7, roleType: 'cyber', name: 'Nova', personality: '冷静、理性、科技感、独立', description: '轻赛博风格少女，荧光色头发配机械义眼装饰', avatar: '🤖', traits: ['完美自律型', '智慧导师型'] },
  { id: 8, roleType: 'cyber', name: 'Zero', personality: '冷酷、精准、高效、神秘', description: '赛博朋克少年，银色短发配发光电路纹路', avatar: '⚡', traits: ['完美自律型'] },
  { id: 9, roleType: 'artsy', name: '星尘', personality: '浪漫、感性、细腻、富有想象力', description: '文艺氛围感少女，亚麻色卷发配碎花长裙', avatar: '✨', traits: ['焦虑敏感型', '创意灵感型'] },
  { id: 10, roleType: 'artsy', name: '慕寒', personality: '内敛、深沉、博学、温柔', description: '文艺青年，黑框眼镜配亚麻色衬衫', avatar: '📖', traits: ['智慧导师型', '佛系松弛型'] },
  { id: 11, roleType: 'cool', name: '清禾', personality: '高冷、独立、自信、洒脱', description: '中性清冷风格，利落短发配冷淡色系穿搭', avatar: '❄️', traits: ['佛系松弛型'] },
  { id: 12, roleType: 'cool', name: '晨风', personality: '沉稳、内敛、理智、温柔', description: '清冷少年，干净利落的短发配简约穿搭', avatar: '🌬️', traits: ['佛系松弛型', '智慧导师型'] },
  { id: 13, roleType: 'energetic', name: 'Sunny', personality: '活力、乐观、热情、开朗', description: '元气少年，阳光笑容配运动风穿搭', avatar: '☀️', traits: ['元气少年型', '挑战突破型'] },
  { id: 14, roleType: 'energetic', name: '乐乐', personality: '活泼、开朗、乐观、热情', description: '活力少女，双马尾配亮色运动服', avatar: '🍭', traits: ['元气少年型'] },
  { id: 15, roleType: 'mythical', name: '玲珑', personality: '神秘、灵动、优雅、温柔', description: '瑞兽灵系少女，龙角装饰配流光长裙', avatar: '🐉', traits: ['佛系松弛型', '暖心陪伴型'] },
  { id: 16, roleType: 'mythical', name: '白虎', personality: '勇猛、忠诚、正义、温柔', description: '瑞兽灵系少年，白虎耳朵配银白发色', avatar: '🐯', traits: ['挑战突破型', '暖心陪伴型'] },
  { id: 17, roleType: 'mythical', name: '青鸾', personality: '高贵、优雅、温柔、灵动', description: '瑞兽灵系少女，青鸾鸟羽装饰配青色长裙', avatar: '🦅', traits: ['佛系松弛型', '暖心陪伴型'] },
  { id: 18, roleType: 'mythical', name: '玄武', personality: '稳重、可靠、智慧、守护', description: '瑞兽灵系少年，玄武龟甲装饰配深色调穿搭', avatar: '🐢', traits: ['智慧导师型', '暖心陪伴型'] },
  { id: 19, roleType: 'mythical', name: '火云', personality: '热情、勇敢、正义、温暖', description: '瑞兽灵系少年，火麒麟元素配火红发色', avatar: '🔥', traits: ['挑战突破型', '元气少年型'] },
  { id: 20, roleType: 'mythical', name: '灵灵', personality: '神秘、灵动、治愈、温柔', description: '神秘森林精灵，树叶装饰配翠绿色长裙', avatar: '🧚', traits: ['暖心陪伴型', '佛系松弛型'] }
]

// AI情绪素材(6种状态)
const mockAiEmotions = {
  normal: { text: '我在呢，有什么想聊的吗？', animation: 'float' },
  happy: { text: '太棒了！继续保持哦~', animation: 'bounce' },
  sad: { text: '没关系，明天会更好的', animation: 'shake' },
  gentle: { text: '慢慢来，不着急', animation: 'pulse' },
  encourage: { text: '你可以的！我相信你！', animation: 'bounce' },
  chat: { text: '嗯嗯，我在听呢', animation: 'float' }
}

// 徽章(5种)
const mockBadges = [
  { id: 1, code: 'first_checkin', name: '初次打卡', description: '完成第一次习惯打卡', icon: '🎯', unlocked: true, unlockedAt: '2026-07-01' },
  { id: 2, code: 'streak_7', name: '坚持一周', description: '连续打卡7天', icon: '🔥', unlocked: true, unlockedAt: '2026-07-07' },
  { id: 3, code: 'streak_30', name: '月度达人', description: '连续打卡30天', icon: '🏆', unlocked: false, unlockedAt: null },
  { id: 4, code: 'all_done', name: '全部完成', description: '一天内完成所有习惯', icon: '⭐', unlocked: true, unlockedAt: '2026-07-05' },
  { id: 5, code: 'checkin_100', name: '百次打卡', description: '累计打卡100次', icon: '💎', unlocked: false, unlockedAt: null }
]

// 本周打卡数据
const mockWeekData = [
  { date: '2026-07-14', day: '一', completed: 3, total: 3, rate: 100 },
  { date: '2026-07-15', day: '二', completed: 2, total: 3, rate: 67 },
  { date: '2026-07-16', day: '三', completed: 3, total: 3, rate: 100 },
  { date: '2026-07-17', day: '四', completed: 1, total: 3, rate: 33 },
  { date: '2026-07-18', day: '五', completed: 2, total: 3, rate: 67 },
  { date: '2026-07-19', day: '六', completed: 0, total: 3, rate: 0 },
  { date: '2026-07-20', day: '日', completed: 0, total: 3, rate: 0 }
]

// 月度趋势(最近4周)
const mockMonthData = [
  { week: '第1周', rate: 71, checkins: 15 },
  { week: '第2周', rate: 81, checkins: 17 },
  { week: '第3周', rate: 90, checkins: 19 },
  { week: '第4周', rate: 67, checkins: 14 }
]

// 习惯维度统计
const mockHabitStats = [
  { name: '早起一杯水', icon: '💧', color: '#4FC3F7', totalCheckins: 12, streak: 12, rate: 100 },
  { name: '阅读30分钟', icon: '📚', color: '#FFD93D', totalCheckins: 8, streak: 5, rate: 67 },
  { name: '运动15分钟', icon: '🏃', color: '#FF6B6B', totalCheckins: 6, streak: 3, rate: 50 }
]

// AI对话快捷回复
const mockQuickReplies = [
  '今天不想打卡',
  '给我一些鼓励',
  '推荐一个新习惯',
  '我最近状态不好'
]

// AI回复模板 - 按角色性格区分
const mockAiRepliesByPersonality = {
  relaxed: [
    '慢慢来，一切都会好起来的~ 🌿',
    '我会一直陪着你的，别担心。',
    '今天的你也很棒哦，继续加油！',
    '休息一下也没关系，我在这儿等你。',
    '深呼吸，一切都会过去的。',
    '你已经做得很好了，不要太苛责自己。',
    '无论发生什么，我都会支持你的。'
  ],
  y2k: [
    'Let\'s shine together! ✨',
    '哇哦~你今天超酷的！继续保持！🔥',
    '别摆烂啦！快点行动起来！💎',
    '耶！完成任务！你太牛了吧！🎉',
    '嗨！今天也要做最棒的自己！🌈',
    '加油加油！你可是最酷的！💖',
    '相信自己，你可以的！💪'
  ],
  chinese: [
    '愿君今日安好，继续努力。',
    '君真乃人中龙凤，佩服佩服。',
    '不急不躁，慢慢来便是。',
    '恭喜君完成目标，可喜可贺。',
    '莫哭莫哭，我陪在君身旁。',
    '长风破浪会有时，直挂云帆济沧海。',
    '愿君继续保持，我一直陪伴。'
  ],
  cyber: [
    '数据不会说谎，你可以的。',
    '任务完成，效率评分：优秀。',
    '系统分析：现在是行动的最佳时机。',
    '检测到拖延行为，建议立即行动。',
    '恭喜！任务完成度：100%。',
    '数据分析：你的效率正在提升。',
    '系统支持：我会一直陪伴你完成任务。'
  ],
  artsy: [
    '生活需要一点诗意。 ✨',
    '你做得真好，像完成了一幅美丽的画。',
    '累了就休息，生活需要留白。',
    '恭喜完成！愿你的生活充满诗意。',
    '想哭就哭吧，眼泪也是诗的一部分。',
    '每一步都是成长，你做得很好。',
    '愿你被温柔以待，继续前行。'
  ],
  cool: [
    '冷暖自知，自在独行。 ❄️',
    '做得不错，继续保持。',
    '不想做就休息，没关系。',
    '完成任务，辛苦了。',
    '没关系的，都会过去。',
    '你很棒的，别难过。',
    '继续加油，你可以的。'
  ],
  energetic: [
    '每天都是新的冒险！☀️',
    '哇！你太厉害了吧！',
    '别偷懒啦！快点动起来！',
    '加油加油！我们一起冲！',
    '完成任务！你就是最棒的！',
    '相信自己，你可以的！',
    '继续保持，你是最棒的！'
  ],
  mythical: [
    '愿你的每一天都有好运相伴。 🐉',
    '恭喜君完成目标，可喜可贺。',
    '不急不躁，慢慢来便是。',
    '我会一直守护着你的。',
    '莫哭莫哭，我陪在君身旁。',
    '愿君继续保持，我一直陪伴。',
    '动一动，身心舒畅。'
  ],
  cute: [
    '收到收到！小萌会一直陪着你的喵~ 🐱',
    '哇哦~你今天超棒的！继续加油鸭！🌟',
    '没关系哒~休息一下也是可以的哦！🥰',
    '耶！又完成了一个习惯！太厉害了吧！🎉',
    '嗯嗯~我们一起从小目标开始吧！🌈',
    '你比昨天更好啦！这就是进步哦！✨',
    '坚持住！小萌相信你一定可以的！💖'
  ],
  gentle: [
    '好的，我会陪你一起坚持下去的。',
    '每一步都算数，你已经在变好的路上了。',
    '休息一下也没关系，重要的是不放弃。',
    '你今天表现很棒，继续保持就好。',
    '我理解你的感受，让我们慢慢来。',
    '你比昨天更好了一点点，这就是进步。',
    '坚持是最难的事，但你已经做到了这么久。'
  ],
  serious: [
    '收到。坚持就是胜利，不要松懈。',
    '很好，继续保持这个节奏。',
    '不要找借口，今天的任务必须完成。',
    '完成了一个，还有更多等着你。',
    '状态不好？那就调整状态，不要放弃。',
    '每天进步一点点，积累起来就是巨大的成就。',
    '自律即自由，记住这句话。'
  ]
}

const mockAiReplies = mockAiRepliesByPersonality.relaxed

// ============ 模拟 API 响应 ============

function mockResponse(data, delay = MOCK_DELAY) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: 'ok', data })
    }, delay)
  })
}

function mockError(message, delay = MOCK_DELAY) {
  return new Promise((_, reject) => {
    setTimeout(() => {
      const err = new Error(message || '模拟错误')
      err.code = 500
      err.data = null
      reject(err)
    }, delay)
  })
}

// ============ Auth API ============

function mockSendSmsCode(phone) {
  console.log('[Mock] 发送验证码到:', phone)
  return mockResponse({ sent: true, code: '1234' })
}

function mockLogin(username, password) {
  if (!username || !password) {
    return mockError('用户名或密码不能为空')
  }
  return mockResponse({
    access_token: 'mock_token_' + Date.now(),
    token_type: 'bearer',
    expires_in: 86400,
    userInfo: {
      ...mockUser,
      username: username
    }
  })
}

function mockWxLogin() {
  return mockResponse({
    access_token: 'mock_wx_token_' + Date.now(),
    token_type: 'bearer',
    expires_in: 86400,
    userInfo: { ...mockUser, nickname: '微信用户' }
  })
}

function mockRegister(userData) {
  return mockResponse({
    id: Date.now(),
    username: userData.username || userData.email?.split('@')[0] || '新用户',
    email: userData.email,
    first_name: userData.first_name || userData.username,
    last_name: userData.last_name || '',
    phone: userData.phone || '',
    registerTime: new Date().toISOString()
  })
}

function mockGuestLogin() {
  return mockResponse({
    access_token: 'mock_guest_token_' + Date.now(),
    token_type: 'bearer',
    expires_in: 86400,
    userInfo: { ...mockUser, nickname: '游客', level: 1, levelName: '新手' }
  })
}

// ============ Habit API ============

function mockGetTodayHabits() {
  // 返回前执行断卡检测，保证连续天数与日期一致
  return mockResponse(mockHabits.map(applyStreakBreak))
}

function mockGetAllHabits() {
  return mockResponse(mockHabits.map(applyStreakBreak))
}

function mockCheckin(habitId) {
  const habit = mockHabits.find(h => h.id === habitId)
  if (habit) {
    habit.completed = true
    habit.last_checkin_date = _todayStr(0)
    habit.broken = false
    habit.can_makeup = false
    habit.broken_streak = 0
    habit.streak += 1
  }
  return mockResponse({
    habitId,
    checked: true,
    streak: habit ? habit.streak : 0,
    newBadge: null
  })
}

/**
 * 补卡：补昨日漏卡，恢复原连续天数并 +1
 * 仅在 can_makeup（昨天漏卡）时有效，更早漏卡无法补
 */
function mockMakeupCheckin(habitId) {
  const habit = mockHabits.find(h => h.id === habitId)
  if (!habit) return mockError('习惯不存在')
  if (!habit.can_makeup) return mockError('已超出补卡宽限期（仅限补昨日漏卡）')
  habit.completed = true
  habit.streak = (habit.broken_streak || 0) + 1
  habit.broken = false
  habit.can_makeup = false
  habit.broken_streak = 0
  habit.last_checkin_date = _todayStr(0)
  return mockResponse({ habitId, checked: true, makeup: true, streak: habit.streak })
}

function mockUncheckin(habitId) {
  const habit = mockHabits.find(h => h.id === habitId)
  if (habit) {
    habit.completed = false
    if (habit.streak > 0) habit.streak -= 1
  }
  return mockResponse({ habitId, checked: false })
}

function mockGetTemplates() {
  return mockResponse(mockTemplates)
}

function mockAddHabit(templateId) {
  const tpl = mockTemplates.find(t => t.id === templateId)
  if (!tpl) return mockError('模板不存在')
  const newHabit = {
    id: Date.now(),
    type: tpl.type,
    name: tpl.name,
    icon: tpl.icon,
    color: tpl.color,
    target: tpl.defaultTarget,
    difficulty: tpl.difficulty,
    multiplier: tpl.multiplier,
    reminderTime: '08:00',
    streak: 0,
    completed: false,
    sort: mockHabits.length + 1
  }
  mockHabits.push(newHabit)
  return mockResponse(newHabit)
}

function mockCreateHabit(data) {
  const newHabit = {
    id: Date.now(),
    type: 'custom',
    name: data.name || '自定义习惯',
    icon: data.icon || '⭐',
    color: data.color || '#6B8E7B',
    target: data.target || '完成1次',
    description: data.description || '',
    difficulty: data.difficulty || 'easy',
    multiplier: data.difficulty === 'hard' ? 2.0 : data.difficulty === 'medium' ? 1.5 : 1.0,
    reminderTime: data.reminder_time || '',
    streak: 0,
    completed: false,
    sort: mockHabits.length + 1
  }
  mockHabits.push(newHabit)
  return mockResponse(newHabit)
}

function mockDeleteHabit(habitId) {
  const idx = mockHabits.findIndex(h => h.id === habitId)
  if (idx >= 0) mockHabits.splice(idx, 1)
  return mockResponse({ deleted: true })
}

// ============ Chat API ============

function mockGetChatHistory() {
  return mockResponse([
    { id: 1, role: 'assistant', content: '你好！我是你的循途。今天想聊聊什么习惯？', emotion: 'normal', time: '2026-07-18 10:00:00' },
    { id: 2, role: 'user', content: '我今天不太想运动', emotion: 'negative', time: '2026-07-18 10:01:00' },
    { id: 3, role: 'assistant', content: '没关系，偶尔休息一下也是可以的。明天继续就好啦~', emotion: 'gentle', time: '2026-07-18 10:01:30' }
  ])
}

function mockSendMessage(content, personality = 'relaxed') {
  const replies = mockAiRepliesByPersonality[personality] || mockAiRepliesByPersonality.relaxed
  let reply = replies[Math.floor(Math.random() * replies.length)]
  let emotion = 'normal'

  if (content.includes('不想') || content.includes('累') || content.includes('不好')) {
    emotion = 'gentle'
    const gentleReplies = {
      cute: '没关系哒~休息一下也是可以的哦！下次再加油鸭！🥰',
      gentle: '我理解你的感受，休息一下也没关系。重要的是不放弃。',
      serious: '状态不好？那就调整状态，不要找借口逃避。',
      energetic: '累了？那就休息5分钟！然后继续冲！你可以的！⚡',
      relaxed: '没关系的，休息一下也是可以的。我会一直陪着你的。',
      y2k: '累了就歇会儿！别委屈自己！💎',
      chinese: '休息片刻也无妨，身体为重。愿君放宽心，我一直都在。',
      cyber: '分析结果：适当休息有助于恢复效率，建议先休息5分钟。',
      artsy: '累了就休息，生活需要留白。我陪你一起享受当下。',
      cool: '不想做就休息，没关系。我陪你一起，慢慢来。',
      mythical: '累了便歇，不必强求。我会一直守护着你的。'
    }
    reply = gentleReplies[personality] || gentleReplies.relaxed
  } else if (content.includes('加油') || content.includes('鼓励') || content.includes('坚持')) {
    emotion = 'encourage'
    const encourageReplies = {
      cute: '你可以的！小萌相信你一定可以的！💖',
      gentle: '你已经做得很好了，继续保持就好。',
      serious: '坚持就是胜利，不要松懈。',
      energetic: '冲鸭！你就是最棒的！相信自己！💨',
      relaxed: '加油！我相信你可以的，慢慢来，一切都会好起来的~',
      y2k: '加油加油！你可是最酷的！相信自己！💪',
      chinese: '长风破浪会有时，直挂云帆济沧海。君一定可以的！',
      cyber: '系统分析：你的坚持数据正在增长，继续保持！',
      artsy: '每一步都是成长，你做得很好。继续加油！',
      cool: '继续加油，你可以的。相信自己的能力。',
      mythical: '愿君勇猛精进，我会一直守护着你！'
    }
    reply = encourageReplies[personality] || encourageReplies.relaxed
  } else if (content.includes('推荐') || content.includes('新习惯')) {
    emotion = 'happy'
    const recommendReplies = {
      cute: '推荐你试试「冥想静心」🧘，每天10分钟就能帮助减压哦！很适合你的状态~',
      gentle: '我觉得「冥想静心」会很适合你，每天10分钟帮助减压。',
      serious: '建议尝试「冥想静心」，有助于提高专注力。',
      energetic: '强力推荐「冥想静心」！每天10分钟，让你满血复活！🧘',
      relaxed: '推荐你试试「冥想静心」，每天10分钟帮助减压放松。',
      y2k: '推荐「冥想静心」！每天10分钟，让你元气满满！✨',
      chinese: '建议尝试「冥想静心」，有助于平复心境，提高专注力。',
      cyber: '系统推荐：「冥想静心」，数据分析显示有助于提高专注力30%。',
      artsy: '推荐「冥想静心」，每天10分钟，让生活充满诗意。',
      cool: '建议试试「冥想静心」，有助于放松身心。',
      mythical: '推荐「冥想静心」，愿灵气环绕，助君静心。'
    }
    reply = recommendReplies[personality] || recommendReplies.relaxed
  } else if (content.includes('完成') || content.includes('打卡')) {
    emotion = 'happy'
    const happyReplies = {
      cute: '耶！又完成了一个习惯！太厉害了吧！🎉',
      gentle: '很好，继续保持这个节奏。',
      serious: '完成了一个，还有更多等着你。不要满足于此。',
      energetic: '完成打卡！你就是最棒的！继续保持这个势头！🔥',
      relaxed: '太棒了！你真的很厉害呀！继续加油~',
      y2k: '哇！你太牛了吧！完成任务！🎉',
      chinese: '恭喜君完成目标，可喜可贺！愿君继续保持。',
      cyber: '任务完成，效率评分：优秀。继续保持！',
      artsy: '恭喜完成！像完成了一幅美丽的画。继续保持！',
      cool: '完成任务，辛苦了。继续保持。',
      mythical: '恭喜君完成目标，可喜可贺！愿君继续精进！'
    }
    reply = happyReplies[personality] || happyReplies.relaxed
  }

  return mockResponse({
    reply,
    emotion,
    quickReplies: mockQuickReplies
  })
}

function mockGetQuickReplies() {
  return mockResponse(mockQuickReplies)
}

// ============ Chat API - 流式 & 危机检测 ============

// 聊天情绪关键词库（用于消息情绪标签识别）
const mockChatEmotionKeywords = {
  happy: ['开心', '高兴', '快乐', '哈哈', '笑', '棒', '太好了', '耶', '完美', '幸福'],
  excited: ['兴奋', '激动', '期待', '万岁', '终于', '成功', '太牛了', '牛', '厉害'],
  calm: ['平静', '还好', '一般', '普通', '正常', '没事', '行吧', '随意'],
  sad: ['难过', '伤心', '哭', '不开心', '郁闷', '失落', '孤独', '委屈', '想哭'],
  angry: ['生气', '愤怒', '气死', '烦', '讨厌', '可恶', '不爽', '恼火', '抓狂'],
  tired: ['累', '疲惫', '困', '没劲', '撑不住', '精疲力尽', '好困', '没力气']
}

// 危机关键词库
const mockCrisisKeywords = [
  { word: '自杀', severity: 'high' },
  { word: '不想活', severity: 'high' },
  { word: '结束生命', severity: 'high' },
  { word: '活不下去', severity: 'high' },
  { word: '自残', severity: 'high' },
  { word: '割腕', severity: 'high' },
  { word: '绝望', severity: 'medium' },
  { word: '没意义', severity: 'medium' },
  { word: '不想存在', severity: 'high' },
  { word: '走了算了', severity: 'medium' },
  { word: '没人会在乎', severity: 'medium' },
  { word: '世界没有我会更好', severity: 'high' }
]

// 危机干预话术
const mockCrisisResponses = [
  '我听到你了，此刻的你一定承受着巨大的痛苦。我想让你知道，你的感受是真实的，你的存在是有意义的。请给我一个机会陪你度过这个艰难的时刻。',
  '你愿意告诉我这些，说明你内心深处仍然在寻找帮助。这很勇敢。你不是一个人，此刻有很多人愿意倾听你、帮助你。',
  '我理解你现在感到很绝望，但请相信，这种感受是暂时的，而生命是珍贵的。让我们一起找到渡过难关的方法，好吗？'
]

const CRISIS_HOTLINE = '400-161-9995'

/**
 * 聊天情绪分析（用于消息标签显示）
 * @param {string} text - 用户消息文本
 * @returns {{ type: string, intensity: number }}
 */
function mockChatEmotionAnalysis(text) {
  if (!text) return { type: 'calm', intensity: 3 }
  for (const [emotion, keywords] of Object.entries(mockChatEmotionKeywords)) {
    for (const kw of keywords) {
      if (text.includes(kw)) {
        // 简单强度估算：关键词越多+感叹号+重复字 → 强度越高
        let intensity = 5
        if ((text.match(/！/g) || []).length >= 2) intensity += 2
        if (text.length > 30) intensity += 1
        if (text.length > 60) intensity += 1
        intensity = Math.min(intensity, 10)
        return { type: emotion, intensity }
      }
    }
  }
  return { type: 'calm', intensity: 3 }
}

/**
 * 流式发送消息 Mock - 使用对话引擎生成自然回复
 * 核心：用 ai-dialogue-engine 的 generateReply 替代固定模板
 * - 20种人格策略 × 11种情绪 × 自然语言动态组装
 * - 记忆系统防重复
 * - 上下文感知（行走地图/习惯/情绪历史）
 * - 多消息拆分模拟真人微信聊天节奏
 *
 * @param {string} content - 用户消息
 * @param {function} onChunk - 每段文字回调
 * @param {object} context - { persona, emotion, recentMessages, characterId }
 * @returns {Promise<object>} { reply, emotion }
 */
async function mockStreamSend(content, onChunk, context = {}) {
  const characterId = context.characterId || 'linxi'
  const character = getCharacterById(characterId)
  const personalityType = character?.personalityType || PERSONALITY_TYPES.GENTLE_HEALER

  // 构建对话引擎所需的上下文
  const recentMsgs = (context.recentMessages || []).slice(-10)
  const engineCtx = {
    chatHistory: recentMsgs.map(m => ({ role: m.role, content: m.content })),
    isPostCheckin: context.emotion === 'checkin' || context.emotion === 'checkin_trigger',
  }

  // 用对话引擎生成回复
  let reply = generateReply(content, personalityType, engineCtx, characterId)

  // 如果回复太短，补充一个追问让对话延续
  if (reply && reply.length < 12) {
    const followUps = [
      '你觉得呢？',
      '后来怎么样了？',
      '还有什么想说的吗？',
      '我继续听着呢',
      '然后呢？',
    ]
    if (Math.random() < 0.6) {
      reply += ' ' + followUps[Math.floor(Math.random() * followUps.length)]
    }
  }

  // 拆分成多条消息模拟真人聊天节奏
  const messages = splitReplyIntoMessages(reply)

  // 逐条消息流式输出
  let fullReply = ''
  for (let mi = 0; mi < messages.length; mi++) {
    const msg = messages[mi]

    // 按标点拆分成 chunk
    const chunks = []
    let current = ''
    for (let i = 0; i < msg.length; i++) {
      current += msg[i]
      if ('，。！？~、；,.'.includes(msg[i]) || i === msg.length - 1) {
        chunks.push(current)
        current = ''
      }
    }
    if (current) chunks.push(current)

    for (const chunk of chunks) {
      if (onChunk) onChunk(chunk)
      // 模拟真人打字节奏：短句快，长句慢，标点后微停顿
      const delay = chunk.length > 10 ? 90 + Math.random() * 80 : 50 + Math.random() * 60
      await new Promise(r => setTimeout(r, delay))
    }

    fullReply += msg

    // 多条消息之间加短暂停顿
    if (mi < messages.length - 1) {
      if (onChunk) onChunk(' ')
      await new Promise(r => setTimeout(r, 200 + Math.random() * 400))
    }
  }

  // 推断情绪标签
  const userEmotion = analyzeEmotion(content)
  const emotionMap = {
    happy: 'happy', excited: 'happy', sad: 'sad', anxious: 'gentle',
    tired: 'gentle', lazy: 'gentle', confused: 'gentle',
    venting: 'sad', lonely: 'sad', grateful: 'happy', neutral: 'normal'
  }
  const emotion = emotionMap[userEmotion.type] || 'normal'

  return { reply: fullReply, emotion }
}

/**
 * 将长回复拆分成多条短消息，模拟真人微信聊天
 * 规则：
 * - 如果回复包含问号/感叹号，在问号后拆分
 * - 如果回复超过40字，在逗号/句号处拆分
 * - 最多拆成3条
 */
function splitReplyIntoMessages(reply) {
  if (!reply || reply.length < 25) return [reply]

  const messages = []

  // 策略1：在问号后拆分（"反应+追问"模式）
  const questionMatch = reply.match(/^(.+?[？?])(.+)$/)
  if (questionMatch && questionMatch[1].length > 5 && questionMatch[2].length > 3) {
    messages.push(questionMatch[1])
    messages.push(questionMatch[2])
    return messages
  }

  // 策略2：在句号/感叹号后拆分
  const sentences = reply.split(/(?<=[。！！!？?~])/).filter(s => s.trim())
  if (sentences.length >= 2 && sentences.length <= 4) {
    // 把句子分成2组
    const midPoint = Math.ceil(sentences.length / 2)
    messages.push(sentences.slice(0, midPoint).join(''))
    messages.push(sentences.slice(midPoint).join(''))
    return messages
  }

  // 策略3：超过50字就在中间逗号处拆
  if (reply.length > 50) {
    const midIdx = Math.floor(reply.length / 2)
    // 找中间附近的逗号
    for (let i = midIdx; i < Math.min(midIdx + 15, reply.length); i++) {
      if ('，,。'.includes(reply[i])) {
        messages.push(reply.substring(0, i + 1))
        messages.push(reply.substring(i + 1))
        return messages
      }
    }
  }

  return [reply]
}

/**
 * 危机检测 Mock
 * @param {string} content - 用户输入文本
 * @returns {Promise<object>} { is_crisis, severity, keywords, response, hotline }
 */
function mockCrisisCheck(content) {
  const matched = []
  let maxSeverity = 'low'

  for (const item of mockCrisisKeywords) {
    if (content.includes(item.word)) {
      matched.push(item.word)
      if (item.severity === 'high') maxSeverity = 'high'
      else if (item.severity === 'medium' && maxSeverity !== 'high') maxSeverity = 'medium'
    }
  }

  if (matched.length === 0) {
    return mockResponse({ is_crisis: false, severity: 'low', keywords: [] })
  }

  const response = mockCrisisResponses[Math.floor(Math.random() * mockCrisisResponses.length)]

  return mockResponse({
    is_crisis: true,
    severity: maxSeverity,
    keywords: matched,
    response,
    hotline: CRISIS_HOTLINE,
    resources: [
      { name: '全国24小时心理援助热线', phone: CRISIS_HOTLINE },
      { name: '北京心理危机研究与干预中心', phone: '010-82951332' },
      { name: '生命热线', phone: '400-821-1215' }
    ]
  })
}

// ============ Stats API ============

function mockGetStatsSummary() {
  return mockResponse({
    totalHabits: mockHabits.length,
    streakDays: 12,
    completionRate: 67,
    totalCheckins: 26,
    todayCompleted: 1,
    todayTotal: 3
  })
}

function mockGetWeekData() {
  return mockResponse(mockWeekData)
}

function mockGetMonthData() {
  return mockResponse(mockMonthData)
}

function mockGetHabitStats() {
  return mockResponse(mockHabitStats)
}

// ============ Emotion API ============

// 模拟情绪记录存储（内存持久化）
let mockEmotionRecords = [
  { id: 1, emotion: 'happy', intensity: 8, tags: ['工作', '社交'], description: '今天完成了重要项目，团队聚餐很愉快', record_date: '2026-07-28', created_at: '2026-07-28 20:30:00', ai_reply: '太棒了！完成重要项目是值得庆祝的事，团队聚餐的温暖也很珍贵。继续保持这份热情~' },
  { id: 2, emotion: 'tired', intensity: 6, tags: ['工作'], description: '加班到很晚，身体有些疲惫', record_date: '2026-07-29', created_at: '2026-07-29 23:15:00', ai_reply: '辛苦了，记得给自己留出休息时间。疲惫是身体在提醒你需要充电，今晚好好睡一觉吧。' },
  { id: 3, emotion: 'calm', intensity: 5, tags: ['健康'], description: '早起冥想十分钟，心情平静', record_date: '2026-07-30', created_at: '2026-07-30 07:20:00', ai_reply: '冥想是很好的开始，平静的心态会让一整天都更从容。继续保持这份宁静~' },
  { id: 4, emotion: 'sad', intensity: 7, tags: ['感情'], description: '和朋友发生了误会，有些难过', record_date: '2026-07-31', created_at: '2026-07-31 16:00:00', ai_reply: '误会是关系中的小插曲，真诚地沟通往往能化解。难过的时候允许自己感受这份情绪，但不要独自承受太久。' }
]
let mockEmotionIdSeq = 100

// 情绪关键词库（对齐后端 EmotionService.EMOTION_KEYWORDS）
const mockEmotionKeywords = {
  happy: ['开心', '高兴', '快乐', '幸福', '棒', '好开心', '哈哈', '笑', '满足', '愉快'],
  excited: ['兴奋', '激动', '期待', '太棒了', '万岁', '终于', '成功', '达成', '突破'],
  calm: ['平静', '安心', '放松', '舒适', '宁静', '还好', '一般', '普通', '平常'],
  sad: ['难过', '伤心', '哭', '悲伤', '不开心', '郁闷', '失落', '孤独', '想哭', '委屈'],
  angry: ['生气', '愤怒', '气死', '烦', '讨厌', '烦死', '可恶', '不爽', '恼火', '抓狂'],
  tired: ['累', '疲惫', '困', '没劲', '疲惫不堪', '力不从心', '撑不住', '精疲力尽', '好困']
}

// 情绪效价
const mockEmotionValence = {
  happy: 'positive', excited: 'positive', calm: 'neutral',
  sad: 'negative', angry: 'negative', tired: 'negative'
}

// 情绪标签映射 -> 回复语气
const mockEmotionReplyTone = {
  happy: 'celebrate', excited: 'celebrate', calm: 'morning',
  sad: 'comfort', angry: 'comfort', tired: 'comfort'
}

// 角色语气语录（简版，实际可由 ai-characters.js 提供）
const mockEmotionReplies = {
  comfort: [
    '我听到你了，这种感受是真实的。先深呼吸三次，我在这里陪着你。',
    '允许自己有这样的情绪，不必急着改变。你愿意和我说说发生了什么吗？',
    '难过的时候，记得给自己一些温柔。你不是一个人在面对。',
    '我理解你的感受，情绪像天气，会过去。重要的是你愿意表达出来。'
  ],
  celebrate: [
    '太棒了！这份喜悦值得被记录下来。继续保持这份好心情~',
    '为你高兴！正向的情绪是前进的动力，记得让这份感觉多停留一会儿。',
    '看到你这么开心，我也替你高兴！继续保持哦~',
    '恭喜！每一次开心的瞬间都是生活给你的礼物。'
  ],
  morning: [
    '平静是很好的状态，愿你今天一整天都保持这份从容。',
    '能感受到平静，说明你和自己的内心连接得很好。继续保持~',
    '这种状态很棒，平静中蕴含着力量。愿你的一天顺遂。',
    '平静的心态是最好的开始，今天也会是美好的一天。'
  ]
}

function mockCreateEmotion(data) {
  const emotion = data.emotion || 'calm'
  const description = data.description || ''
  const tags = data.tags || []

  // 模拟后端情绪分析（关键词匹配）
  let detectedEmotion = emotion
  if (description) {
    const text = description.toLowerCase ? description.toLowerCase() : description
    for (const [emo, keywords] of Object.entries(mockEmotionKeywords)) {
      if (keywords.some(kw => text.includes(kw))) {
        detectedEmotion = emo
        break
      }
    }
  }

  // 生成 AI 回复
  const tone = mockEmotionReplyTone[detectedEmotion] || 'comfort'
  const replies = mockEmotionReplies[tone] || mockEmotionReplies.comfort
  const aiReply = replies[Math.floor(Math.random() * replies.length)]

  const recordDate = data.record_date || new Date().toISOString().slice(0, 10)
  const newRecord = {
    id: ++mockEmotionIdSeq,
    emotion: detectedEmotion,
    intensity: data.intensity !== undefined ? data.intensity : 5,
    tags,
    description,
    record_date: recordDate,
    created_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
    ai_reply: aiReply
  }
  mockEmotionRecords.unshift(newRecord)
  return mockResponse({
    id: newRecord.id,
    emotion: newRecord.emotion,
    intensity: newRecord.intensity,
    record_date: newRecord.record_date,
    ai_reply: newRecord.ai_reply
  })
}

function mockGetEmotionList(params = {}) {
  const page = params.page || 1
  const pageSize = params.page_size || 20
  const total = mockEmotionRecords.length
  const start = (page - 1) * pageSize
  const list = mockEmotionRecords.slice(start, start + pageSize)
  return mockResponse({ list, total, page, page_size: pageSize })
}

function mockGetEmotionTrend(period = '7d') {
  const daysMap = { '7d': 7, '30d': 30, '90d': 90 }
  const days = daysMap[period] || 7
  const today = new Date()
  const labels = []
  const intensities = []
  const emotions = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().slice(0, 10)
    labels.push(dateStr)
    const dayRecords = mockEmotionRecords.filter(r => r.record_date === dateStr)
    if (dayRecords.length > 0) {
      const avg = dayRecords.reduce((s, r) => s + r.intensity, 0) / dayRecords.length
      intensities.push(Math.round(avg * 10) / 10)
      const emoCount = {}
      dayRecords.forEach(r => { emoCount[r.emotion] = (emoCount[r.emotion] || 0) + 1 })
      emotions.push(Object.keys(emoCount).sort((a, b) => emoCount[b] - emoCount[a])[0])
    } else {
      intensities.push(0)
      emotions.push('')
    }
  }
  const distribution = {}
  mockEmotionRecords.forEach(r => { distribution[r.emotion] = (distribution[r.emotion] || 0) + 1 })
  return mockResponse({ labels, intensities, emotions, distribution })
}

function mockGetEmotionDistribution(period = '30d') {
  const total = mockEmotionRecords.length
  const dist = {}
  mockEmotionRecords.forEach(r => { dist[r.emotion] = (dist[r.emotion] || 0) + 1 })
  const labels = { happy: '开心', excited: '兴奋', calm: '平静', sad: '难过', angry: '生气', tired: '疲惫' }
  const distribution = Object.entries(dist).map(([emo, count]) => ({
    emotion: emo, label: labels[emo] || emo, count,
    ratio: Math.round(count / Math.max(total, 1) * 1000) / 10
  })).sort((a, b) => b.count - a.count)
  return mockResponse({ distribution, total })
}

function mockGetEmotionTriggers(period = '30d') {
  const tagStats = {}
  mockEmotionRecords.forEach(r => {
    const tags = r.tags || []
    tags.forEach(tag => {
      if (!tagStats[tag]) tagStats[tag] = { count: 0, total_intensity: 0, negative_count: 0 }
      tagStats[tag].count += 1
      tagStats[tag].total_intensity += r.intensity
      if (mockEmotionValence[r.emotion] === 'negative') tagStats[tag].negative_count += 1
    })
  })
  const result = Object.entries(tagStats).map(([tag, s]) => ({
    tag, count: s.count,
    avg_intensity: Math.round(s.total_intensity / Math.max(s.count, 1) * 10) / 10,
    negative_ratio: Math.round(s.negative_count / Math.max(s.count, 1) * 1000) / 10
  })).sort((a, b) => b.count - a.count)
  return mockResponse(result)
}

function mockDeleteEmotion(recordId) {
  const idx = mockEmotionRecords.findIndex(r => r.id === recordId)
  if (idx >= 0) mockEmotionRecords.splice(idx, 1)
  return mockResponse({ id: recordId, deleted: true })
}

// ============ Meditation API ============

// 正念音频分类
const MEDITATION_CATEGORIES = {
  breathing: { label: '呼吸放松', icon: '🌬️', color: '#E3F2FD' },
  body_scan: { label: '身体扫描', icon: '👤', color: '#F3E5F5' },
  mindfulness: { label: '正念冥想', icon: '🧘', color: '#E8F5E9' },
  anxiety_relief: { label: '焦虑缓解', icon: '💆', color: '#FFF3E0' },
  sleep_aid: { label: '助眠安神', icon: '🌙', color: '#ECEFF1' }
}

// 正念音频列表（12个）
const mockMeditationAudios = [
  { id: 1, title: '4-7-8呼吸法', category: 'breathing', duration_minutes: 5, audio_url: '', cover_image: '', description: '经典呼吸放松法：吸气4秒、屏息7秒、呼气8秒，快速平复焦虑', guide_text: '请找一个舒适的姿势坐好，我们将开始4-7-8呼吸法练习...', is_premium: false, play_count: 1280, sort_order: 1, is_active: true },
  { id: 2, title: '腹式呼吸入门', category: 'breathing', duration_minutes: 8, audio_url: '', cover_image: '', description: '学习腹式呼吸，用横膈膜深呼吸放松身心', guide_text: '让我们开始腹式呼吸的练习，一手放在胸口，一手放在腹部...', is_premium: false, play_count: 856, sort_order: 2, is_active: true },
  { id: 3, title: '全身身体扫描', category: 'body_scan', duration_minutes: 15, audio_url: '', cover_image: '', description: '从头顶到脚趾，逐一感知身体每个部位', guide_text: '请躺下或舒适坐好，我们将进行全身身体扫描...', is_premium: false, play_count: 642, sort_order: 3, is_active: true },
  { id: 4, title: '肩颈放松扫描', category: 'body_scan', duration_minutes: 10, audio_url: '', cover_image: '', description: '专注释放肩颈部位的紧张感', guide_text: '把注意力带到你的肩膀和颈部，感受那里的紧张...', is_premium: false, play_count: 423, sort_order: 4, is_active: true },
  { id: 5, title: '十分钟正念冥想', category: 'mindfulness', duration_minutes: 10, audio_url: '', cover_image: '', description: '专注于当下，观察思绪的来去而不评判', guide_text: '让我们开始十分钟的正念冥想，请闭上眼睛...', is_premium: false, play_count: 2100, sort_order: 5, is_active: true },
  { id: 6, title: '20分钟深度冥想', category: 'mindfulness', duration_minutes: 20, audio_url: '', cover_image: '', description: '更长时间的深度冥想，适合有基础的练习者', guide_text: '欢迎来到20分钟深度冥想，请找到一个安静的空间...', is_premium: true, play_count: 580, sort_order: 6, is_active: true },
  { id: 7, title: '焦虑释放引导', category: 'anxiety_relief', duration_minutes: 12, audio_url: '', cover_image: '', description: '通过引导想象释放焦虑情绪', guide_text: '如果你正感到焦虑，请跟随我的引导，一步步释放它...', is_premium: false, play_count: 930, sort_order: 7, is_active: true },
  { id: 8, title: '情绪着陆技术', category: 'anxiety_relief', duration_minutes: 8, audio_url: '', cover_image: '', description: '5-4-3-2-1着陆法，帮助你从情绪风暴中回到当下', guide_text: '让我们练习着陆技术，先看看周围，找到5样你能看到的东西...', is_premium: false, play_count: 720, sort_order: 8, is_active: true },
  { id: 9, title: '渐进式肌肉放松', category: 'anxiety_relief', duration_minutes: 15, audio_url: '', cover_image: '', description: '从脚到头逐步收紧再放松每一组肌肉', guide_text: '请准备好，我们将进行渐进式肌肉放松练习...', is_premium: false, play_count: 410, sort_order: 9, is_active: true },
  { id: 10, title: '睡前冥想引导', category: 'sleep_aid', duration_minutes: 20, audio_url: '', cover_image: '', description: '温柔的睡前引导，帮助你安然入睡', guide_text: '夜深了，让我们放下今天的一切，准备好进入梦乡...', is_premium: false, play_count: 1800, sort_order: 10, is_active: true },
  { id: 11, title: '白噪音助眠', category: 'sleep_aid', duration_minutes: 30, audio_url: '', cover_image: '', description: '30分钟白噪音，屏蔽干扰安然入眠', guide_text: '请闭上眼睛，让白噪音带你进入宁静的睡眠...', is_premium: true, play_count: 950, sort_order: 11, is_active: true },
  { id: 12, title: '星空想象冥想', category: 'sleep_aid', duration_minutes: 15, audio_url: '', cover_image: '', description: '想象浩瀚星空，在宁静中入睡', guide_text: '让我们展开想象，在脑海中描绘一片宁静的星空...', is_premium: false, play_count: 670, sort_order: 12, is_active: true }
]

// 正念练习记录（内存持久化）
let mockMeditationRecords = [
  { id: 1, audio_id: 1, category: 'breathing', duration_minutes: 5, completed: true, emotion_before: 'anxious', emotion_after: 'calm', note: '练习后感觉好多了', practiced_at: '2026-07-28 22:00:00' },
  { id: 2, audio_id: 5, category: 'mindfulness', duration_minutes: 10, completed: true, emotion_before: 'tired', emotion_after: 'calm', note: '', practiced_at: '2026-07-30 07:15:00' },
  { id: 3, audio_id: 10, category: 'sleep_aid', duration_minutes: 20, completed: true, emotion_before: 'sad', emotion_after: 'calm', note: '听着就睡着了', practiced_at: '2026-07-31 23:00:00' }
]
let mockMeditationRecordIdSeq = 100

// 当前练习计划
let mockMeditationPlan = {
  id: 1,
  name: '7天正念入门',
  target_days: 7,
  target_duration: 10,
  preferred_category: 'mindfulness',
  start_date: '2026-07-28',
  end_date: null,
  is_active: true,
  completed_days: 3,
  daily_records: [
    { date: '2026-07-28', completed: true, duration: 5 },
    { date: '2026-07-29', completed: false, duration: 0 },
    { date: '2026-07-30', completed: true, duration: 10 },
    { date: '2026-07-31', completed: true, duration: 20 },
    { date: '2026-08-01', completed: false, duration: 0 }
  ]
}

// 正念知识库
const mockMeditationKnowledge = [
  { id: 1, title: '什么是正念？', category: 'basic', icon: '📖', summary: '正念是有意识地、不加评判地关注当下的体验', content: '正念（Mindfulness）源于佛教禅修传统，但现代正念练习已经世俗化。它指的是一种有意识地、不加评判地将注意力集中在当下体验的心理状态。正念的核心要素包括：觉察当下、不评判、接纳、初学者之心。' },
  { id: 2, title: '呼吸为什么重要？', category: 'basic', icon: '🌬️', summary: '呼吸是连接身心的桥梁，是正念练习的锚点', content: '呼吸是唯一既能自主控制又能非自主运行的生理功能。当我们关注呼吸时，副交感神经系统被激活，心率和血压下降，身体进入放松状态。呼吸也是正念练习中最常用的"锚点"，当思绪飘走时，回到呼吸就是回到当下。' },
  { id: 3, title: '每天练习多久合适？', category: 'practice', icon: '⏰', summary: '初学者从5-10分钟开始，逐步增加', content: '研究表明，每天10-15分钟的正念练习就能带来显著益处。初学者建议从5分钟开始，逐步增加。重要的是坚持每日练习，而非单次时长。连续8周每天练习10分钟，比一次性练习2小时效果更好。' },
  { id: 4, title: '思绪飘走怎么办？', category: 'practice', icon: '💭', summary: '思绪飘走是正常的，温柔地把注意力带回即可', content: '思绪飘走不是"做错了"，而是大脑的正常活动。正念的关键不在于"不想"，而在于"发现走神后温柔地回来"。每次注意到思绪飘走并回到呼吸，就像做了一次"俯卧撑"，是在锻炼你的注意力和觉察力。' },
  { id: 5, title: '什么时候练习最好？', category: 'practice', icon: '🌅', summary: '早晨和睡前是黄金时段，但任何时间都可以', content: '早晨练习可以帮助你以平静的状态开始一天；睡前练习有助于放松身心、改善睡眠。但正念没有"最佳时间"，关键是找到适合自己生活节奏的固定时间。饭后、午休、工作间隙都可以。' },
  { id: 6, title: '正念的科学依据', category: 'science', icon: '🔬', summary: '大量研究证实正念可以改变大脑结构和功能', content: '神经科学研究显示，持续正念练习可以：增加前额叶皮层灰质密度（注意力和决策）、缩小杏仁核体积（减少恐惧和焦虑）、增强海马体功能（记忆和学习）。正念还能降低皮质醇水平、增强免疫力、改善睡眠质量。' },
  { id: 7, title: '身体扫描的原理', category: 'technique', icon: '👤', summary: '通过逐一关注身体部位，建立身心连接', content: '身体扫描是正念减压疗法（MBSR）的核心练习之一。它通过系统地关注身体各个部位，帮助我们觉察身体感受、释放肌肉紧张、建立身心连接。身体扫描也能训练注意力的灵活性和持续性。' },
  { id: 8, title: '如何应对练习中的不适？', category: 'technique', icon: '🤗', summary: '以好奇和接纳的态度面对不适，而非逃避', content: '练习中可能出现身体不适（如腿麻、痒）或情绪波动。正念的做法是：以好奇的态度观察这个感受，而不是立即反应或逃避。如果实在无法忍受，可以缓慢调整姿势。情绪波动时，允许它存在，观察它的变化。' }
]

// AI引导语库（按阶段分类）
const mockMeditationGuides = {
  start: [
    '请找一个舒适的姿势，轻轻闭上眼睛。让我们开始这段属于你的宁静时光。',
    '深吸一口气，然后缓缓呼出。把今天的忙碌都留在门外，此刻只属于你自己。',
    '欢迎来到正念练习。不论你现在感受如何，都请允许自己以真实的状态开始。'
  ],
  breathing: [
    '把注意力带到呼吸上。不需要改变呼吸的节奏，只是观察它自然的起伏。',
    '吸气时，感受空气进入鼻腔的清凉；呼气时，感受身体逐渐放松。',
    '如果你的思绪飘走了，没有关系。温柔地注意到它，然后带着善意把注意力带回呼吸。',
    '每一次呼吸都是新的开始。过去的不重要，未来的还没来，此刻只有这一呼一吸。'
  ],
  body_scan: [
    '现在把注意力从呼吸带到身体上。从头顶开始，感受头皮的触感。',
    '让注意力慢慢向下移动，感受你的面部、肩膀、手臂。每一处都允许放松。',
    '如果你发现某个部位紧张或不适，不需要试图改变它。只是观察它，和它待一会儿。',
    '继续向下，感受你的腹部、臀部、大腿、小腿，直到脚趾。你整个人都被觉察之光笼罩着。'
  ],
  mid: [
    '你已经练习了一段时间，做得很好。继续保持这份觉察。',
    '此刻的你，比开始时更平静了一些。感受这份平静，让它渗透到你身体的每一个细胞。',
    '不论思绪如何翻涌，你都在这里，稳定地存在着。这就是正念的力量。'
  ],
  end: [
    '练习即将结束。慢慢地把注意力从内部带回到外部，感受周围的声音。',
    '轻轻动一动手指和脚趾，让身体慢慢苏醒。不要急着睁开眼睛。',
    '当你准备好时，缓缓睁开眼睛。把这份宁静和平和带入接下来的时光中。',
    '感谢你为自己抽出这段时间练习。每一次练习都是在照顾自己。'
  ]
}

function mockGetMeditationAudios(params = {}) {
  let list = mockMeditationAudios.filter(a => a.is_active)
  if (params.category) list = list.filter(a => a.category === params.category)
  if (params.duration) {
    // duration filter: 'short'(<=10), 'medium'(11-20), 'long'(>20)
    if (params.duration === 'short') list = list.filter(a => a.duration_minutes <= 10)
    else if (params.duration === 'medium') list = list.filter(a => a.duration_minutes > 10 && a.duration_minutes <= 20)
    else if (params.duration === 'long') list = list.filter(a => a.duration_minutes > 20)
  }
  return mockResponse({ list, total: list.length })
}

function mockGetMeditationAudio(audioId) {
  const audio = mockMeditationAudios.find(a => a.id === audioId)
  if (!audio) return mockError('音频不存在')
  audio.play_count = (audio.play_count || 0) + 1
  return mockResponse(audio)
}

function mockCreateMeditationRecord(data) {
  const now = new Date()
  const practicedAt = now.toISOString().replace('T', ' ').slice(0, 19)
  const newRecord = {
    id: ++mockMeditationRecordIdSeq,
    audio_id: data.audio_id || null,
    category: data.category || 'mindfulness',
    duration_minutes: data.duration_minutes || 10,
    completed: data.completed !== false,
    emotion_before: data.emotion_before || null,
    emotion_after: data.emotion_after || null,
    note: data.note || '',
    practiced_at: practicedAt
  }
  mockMeditationRecords.unshift(newRecord)

  // 更新计划进度
  const today = now.toISOString().slice(0, 10)
  if (mockMeditationPlan && mockMeditationPlan.is_active) {
    const todayRecord = mockMeditationPlan.daily_records.find(r => r.date === today)
    if (todayRecord && !todayRecord.completed) {
      todayRecord.completed = true
      todayRecord.duration = newRecord.duration_minutes
      mockMeditationPlan.completed_days += 1
    }
  }

  return mockResponse({
    id: newRecord.id,
    completed: newRecord.completed,
    duration_minutes: newRecord.duration_minutes,
    emotion_before: newRecord.emotion_before,
    emotion_after: newRecord.emotion_after
  })
}

function mockGetMeditationRecords(params = {}) {
  const page = params.page || 1
  const pageSize = params.page_size || 20
  let list = mockMeditationRecords
  if (params.category) list = list.filter(r => r.category === params.category)
  const total = list.length
  const start = (page - 1) * pageSize
  const pageList = list.slice(start, start + pageSize)
  return mockResponse({ list: pageList, total, page, page_size: pageSize })
}

function mockGetMeditationStats() {
  const totalSessions = mockMeditationRecords.length
  const completedSessions = mockMeditationRecords.filter(r => r.completed).length
  const totalMinutes = mockMeditationRecords.reduce((s, r) => s + r.duration_minutes, 0)
  const avgDuration = totalSessions > 0 ? Math.round(totalMinutes / totalSessions * 10) / 10 : 0

  // 计算连续天数
  const dates = [...new Set(mockMeditationRecords.map(r => r.practiced_at.slice(0, 10)))].sort().reverse()
  let streak = 0
  const today = new Date().toISOString().slice(0, 10)
  for (let i = 0; i < dates.length; i++) {
    const expected = new Date()
    expected.setDate(expected.getDate() - i)
    if (dates[i] === expected.toISOString().slice(0, 10)) streak++
    else break
  }

  // 分类统计
  const categoryStats = {}
  mockMeditationRecords.forEach(r => {
    if (!categoryStats[r.category]) categoryStats[r.category] = { count: 0, minutes: 0 }
    categoryStats[r.category].count += 1
    categoryStats[r.category].minutes += r.duration_minutes
  })

  return mockResponse({
    total_minutes: totalMinutes,
    total_sessions: totalSessions,
    completed_sessions: completedSessions,
    streak_days: streak,
    avg_duration: avgDuration,
    category_stats: categoryStats
  })
}

function mockCreateMeditationPlan(data) {
  const now = new Date()
  const startDate = now.toISOString().slice(0, 10)
  const targetDays = data.target_days || 7

  // 生成每日记录空壳
  const dailyRecords = []
  for (let i = 0; i < targetDays; i++) {
    const d = new Date(now)
    d.setDate(d.getDate() + i)
    dailyRecords.push({ date: d.toISOString().slice(0, 10), completed: false, duration: 0 })
  }

  mockMeditationPlan = {
    id: Date.now(),
    name: data.name || `${targetDays}天正念计划`,
    target_days: targetDays,
    target_duration: data.target_duration || 10,
    preferred_category: data.preferred_category || null,
    start_date: startDate,
    end_date: null,
    is_active: true,
    completed_days: 0,
    daily_records: dailyRecords
  }
  return mockResponse(mockMeditationPlan)
}

function mockGetMeditationPlan() {
  return mockResponse(mockMeditationPlan)
}

function mockUpdateMeditationPlan(planId, data) {
  if (!mockMeditationPlan || mockMeditationPlan.id !== planId) {
    return mockError('计划不存在')
  }
  if (data.completed_today) {
    const today = new Date().toISOString().slice(0, 10)
    const todayRecord = mockMeditationPlan.daily_records.find(r => r.date === today)
    if (todayRecord && !todayRecord.completed) {
      todayRecord.completed = true
      todayRecord.duration = data.duration_minutes || mockMeditationPlan.target_duration
      mockMeditationPlan.completed_days += 1
    }
  }
  return mockResponse(mockMeditationPlan)
}

function mockGetMeditationKnowledge() {
  return mockResponse(mockMeditationKnowledge)
}

function mockGetMeditationGuide(data = {}) {
  const phase = data.phase || 'start'
  const guides = mockMeditationGuides[phase] || mockMeditationGuides.mid
  const guideText = guides[Math.floor(Math.random() * guides.length)]

  // 根据当前阶段决定下一阶段
  const phaseOrder = ['start', 'breathing', 'body_scan', 'mid', 'end']
  const currentIdx = phaseOrder.indexOf(phase)
  let nextPhase = null
  if (data.elapsed_minutes && data.total_minutes) {
    const ratio = data.elapsed_minutes / data.total_minutes
    if (ratio < 0.15) nextPhase = 'breathing'
    else if (ratio < 0.5) nextPhase = 'body_scan'
    else if (ratio < 0.85) nextPhase = 'mid'
    else nextPhase = 'end'
  } else if (currentIdx >= 0 && currentIdx < phaseOrder.length - 1) {
    nextPhase = phaseOrder[currentIdx + 1]
  }

  return mockResponse({ guide_text: guideText, next_phase: nextPhase })
}

// ============ Stats & Visualization API ============

// 习惯-情绪关联分析数据
const mockHabitEmotionCorrelation = [
  { habit_name: '冥想静心', habit_icon: '🧘', checkin_count: 18, emotion_before: 'anxious', emotion_after: 'calm', avg_intensity_before: 6.2, avg_intensity_after: 3.1, improvement: 50, correlation: 0.82 },
  { habit_name: '运动健身', habit_icon: '🏃', checkin_count: 15, emotion_before: 'tired', emotion_after: 'happy', avg_intensity_before: 5.8, avg_intensity_after: 7.5, improvement: 29, correlation: 0.75 },
  { habit_name: '阅读学习', habit_icon: '📖', checkin_count: 12, emotion_before: 'sad', emotion_after: 'calm', avg_intensity_before: 5.5, avg_intensity_after: 3.8, improvement: 31, correlation: 0.68 },
  { habit_name: '早起打卡', habit_icon: '🌅', checkin_count: 22, emotion_before: 'tired', emotion_after: 'calm', avg_intensity_before: 6.5, avg_intensity_after: 4.2, improvement: 35, correlation: 0.71 },
  { habit_name: '日记记录', habit_icon: '✍️', checkin_count: 10, emotion_before: 'sad', emotion_after: 'calm', avg_intensity_before: 7.0, avg_intensity_after: 4.5, improvement: 36, correlation: 0.79 },
  { habit_name: '喝水提醒', habit_icon: '💧', checkin_count: 20, emotion_before: 'tired', emotion_after: 'calm', avg_intensity_before: 4.2, avg_intensity_after: 3.5, improvement: 17, correlation: 0.45 }
]

function mockGetHabitEmotionCorrelation() {
  return mockResponse(mockHabitEmotionCorrelation)
}

// AI成长报告
const mockGrowthReports = {
  weekly: {
    type: 'weekly',
    period_start: '2026-07-26',
    period_end: '2026-08-01',
    summary: '本周你坚持了12次习惯打卡，完成率67%，比上周提升了8%。情绪整体偏向积极，开心和平静占了60%。',
    habit_stats: {
      total_checkins: 12,
      completion_rate: 67,
      best_streak: 5,
      most_consistent: '早起打卡',
      needs_attention: '运动健身'
    },
    emotion_stats: {
      dominant_emotion: 'calm',
      positive_ratio: 60,
      avg_intensity: 5.2,
      trend: 'stable',
      top_trigger: '工作'
    },
    meditation_stats: {
      total_sessions: 3,
      total_minutes: 45,
      avg_duration: 15,
      streak_days: 3
    },
    ai_analysis: '你这周的表现总体不错！早起打卡和冥想习惯坚持得很好，说明你在自我管理上越来越有节奏感。情绪方面，平静是你的主色调，这说明你的心态很稳。不过我注意到运动健身的完成率有些下降，也许可以试试把它安排在精力更充沛的时段。下周继续保持，你正在变得越来越好！',
    suggestions: [
      '保持早起打卡的好习惯，它是你一天的能量起点',
      '运动健身完成率下降，尝试固定运动时间',
      '冥想练习效果显著，建议增加到每天一次',
      '工作相关情绪波动较大，可以加入简短的午间放松'
    ],
    walk_steps: 12.5,
    walk_milestone: '森林小镇'
  },
  monthly: {
    type: 'monthly',
    period_start: '2026-07-01',
    period_end: '2026-07-31',
    summary: '本月共完成习惯打卡48次，情绪记录22条，正念冥想8次。整体完成率72%，较上月提升12%。',
    habit_stats: {
      total_checkins: 48,
      completion_rate: 72,
      best_streak: 18,
      most_consistent: '早起打卡',
      needs_attention: '阅读学习'
    },
    emotion_stats: {
      dominant_emotion: 'happy',
      positive_ratio: 55,
      avg_intensity: 5.5,
      trend: 'improving',
      top_trigger: '工作'
    },
    meditation_stats: {
      total_sessions: 8,
      total_minutes: 140,
      avg_duration: 17,
      streak_days: 5
    },
    ai_analysis: '这是一个充实的一个月！你完成了48次习惯打卡，完成率72%，比上月提升了12%，这是一个很明显的进步。情绪方面，积极的情绪占比55%，而且整体趋势在改善，说明你的心理状态在逐渐变好。正念冥想坚持了8次，累计140分钟，这对你的情绪管理起了重要作用。特别值得一提的是，你在早起打卡上保持了18天的连续记录，这份毅力令人敬佩。下个月可以关注阅读学习的完成率，找到适合自己的阅读节奏。继续加油，你值得为自己骄傲！',
    suggestions: [
      '本月表现稳步提升，继续保持现有节奏',
      '阅读学习完成率偏低，建议从每天10分钟开始',
      '情绪正向趋势明显，保持现有情绪管理策略',
      '尝试在月底回顾时给自己一些小奖励'
    ],
    walk_steps: 52.3,
    walk_milestone: '雪山高地'
  }
}

function mockGetGrowthReport(type = 'weekly') {
  return mockResponse(mockGrowthReports[type] || mockGrowthReports.weekly)
}

// 数据导出
function mockExportData(format = 'json') {
  const exportData = {
    export_date: new Date().toISOString(),
    habits: mockHabits,
    emotion_records: mockEmotionRecords,
    meditation_records: mockMeditationRecords.slice(0, 20),
    stats_summary: {
      total_checkins: 48,
      total_emotions: mockEmotionRecords.length,
      total_meditation: 8,
      streak_days: 12,
      walk_steps: 52.3
    }
  }
  if (format === 'csv') {
    // 简化CSV格式
    let csv = '类型,日期,内容,强度\n'
    mockEmotionRecords.forEach(r => {
      csv += `情绪,${r.record_date},${r.emotion},${r.intensity}\n`
    })
    return mockResponse({ format: 'csv', content: csv, filename: `emotion_export_${Date.now()}.csv` })
  }
  return mockResponse({ format: 'json', content: JSON.stringify(exportData, null, 2), filename: `full_export_${Date.now()}.json` })
}

// ============ Growth Archive API ============

// 成长档案报告 (quarterly/yearly 补充, weekly/monthly 复用 mockGrowthReports)
const mockArchiveReports = {
  quarterly: {
    id: 'aq-2026q3',
    period: 'quarterly',
    period_start: '2026-07-01',
    period_end: '2026-09-30',
    summary: '本季度共完成习惯打卡132次，情绪记录58条，正念冥想24次。整体完成率75%，较上季度提升10%。情绪正向比例稳步上升，正念练习开始成为日常习惯。',
    highlights: [
      '习惯完成率达到了75%，坚持力非常出色！',
      '完成了24次正念练习，累计420分钟，内心平静力提升！',
      '连续打卡最长记录达到21天，打破了之前的纪录',
      '情绪正向比例从55%提升到62%，心理状态持续改善'
    ],
    suggestions: [
      '阅读习惯完成率偏低，建议从每天10分钟开始',
      '工作日情绪波动较大，可以加入午间5分钟正念呼吸',
      '尝试在周末安排更长时间的正念练习，深化效果',
      '考虑增加一个运动习惯，平衡久坐生活'
    ],
    emotion_count: 58,
    emotion_distribution: { happy: 18, calm: 15, excited: 6, sad: 8, anxious: 7, angry: 4 },
    avg_intensity: 5.3,
    checkin_count: 132,
    completed_count: 99,
    completion_rate: 75.0,
    mindfulness_count: 24,
    total_meditation_min: 420,
    walk_steps: 135.6,
    walk_milestone: '雪山高地',
    is_encrypted: true,
    created_at: '2026-09-30T23:59:00'
  },
  yearly: {
    id: 'ay-2026',
    period: 'yearly',
    period_start: '2026-01-01',
    period_end: '2026-12-31',
    summary: '2026年是你蜕变的一年。全年完成习惯打卡480次，情绪记录210条，正念冥想96次。从年初的3分钟热度到现在的持续自律，你走过了一段了不起的成长旅程。',
    highlights: [
      '全年习惯完成率72%，从年初的45%稳步提升到年末的85%',
      '完成96次正念练习，累计1680分钟，正念成为生活的一部分',
      '情绪正向比例从年初的40%提升到年末的65%，心理韧性显著增强',
      '最长连续打卡记录35天，环球行走地图已抵达星空云海',
      '记录了210条情绪，学会了觉察和表达自己的感受'
    ],
    suggestions: [
      '保持现有的习惯节奏，明年可以尝试增加挑战性目标',
      '情绪管理策略效果显著，继续保持正念练习',
      '考虑将成长经验分享给身边的朋友，互相鼓励',
      '明年可以设定一个年度主题，比如"深度专注"或"身心平衡"'
    ],
    emotion_count: 210,
    emotion_distribution: { happy: 68, calm: 52, excited: 18, sad: 32, anxious: 24, angry: 16 },
    avg_intensity: 5.1,
    checkin_count: 480,
    completed_count: 346,
    completion_rate: 72.1,
    mindfulness_count: 96,
    total_meditation_min: 1680,
    walk_steps: 520.8,
    walk_milestone: '星空云海',
    is_encrypted: true,
    created_at: '2026-12-31T23:59:00'
  }
}

// 档案列表 (历史存档)
const mockArchiveList = [
  { id: 'am-202608', period_type: 'monthly', period_start: '2026-08-01', period_end: '2026-08-31', summary: '8月共完成习惯打卡52次，情绪记录24条，正念冥想10次。完成率78%，较上月提升6%。', is_encrypted: true, created_at: '2026-08-31T23:59:00' },
  { id: 'am-202607', period_type: 'monthly', period_start: '2026-07-01', period_end: '2026-07-31', summary: '7月共完成习惯打卡48次，情绪记录22条，正念冥想8次。整体完成率72%，较上月提升12%。', is_encrypted: true, created_at: '2026-07-31T23:59:00' },
  { id: 'am-202606', period_type: 'monthly', period_start: '2026-06-01', period_end: '2026-06-30', summary: '6月共完成习惯打卡40次，情绪记录18条，正念冥想5次。完成率65%，开始建立自律节奏。', is_encrypted: false, created_at: '2026-06-30T23:59:00' },
  { id: 'aq-2026q2', period_type: 'quarterly', period_start: '2026-04-01', period_end: '2026-06-30', summary: 'Q2季度完成习惯打卡120次，情绪记录52条，正念冥想15次。完成率68%，稳步上升期。', is_encrypted: true, created_at: '2026-06-30T23:59:00' },
  { id: 'am-202605', period_type: 'monthly', period_start: '2026-05-01', period_end: '2026-05-31', summary: '5月共完成习惯打卡36次，情绪记录15条。完成率60%，正在找到自己的节奏。', is_encrypted: false, created_at: '2026-05-31T23:59:00' },
  { id: 'am-202604', period_type: 'monthly', period_start: '2026-04-01', period_end: '2026-04-30', summary: '4月共完成习惯打卡32次，情绪记录12条。完成率55%，开始了自律之旅。', is_encrypted: false, created_at: '2026-04-30T23:59:00' },
  { id: 'aq-2026q1', period_type: 'quarterly', period_start: '2026-01-01', period_end: '2026-03-31', summary: 'Q1季度完成习惯打卡85次，情绪记录35条。完成率52%，从零开始建立习惯体系。', is_encrypted: true, created_at: '2026-03-31T23:59:00' },
  { id: 'am-202603', period_type: 'monthly', period_start: '2026-03-01', period_end: '2026-03-31', summary: '3月共完成习惯打卡30次，情绪记录12条。完成率50%，坚持的力量开始显现。', is_encrypted: false, created_at: '2026-03-31T23:59:00' },
  { id: 'am-202602', period_type: 'monthly', period_start: '2026-02-01', period_end: '2026-02-28', summary: '2月共完成习惯打卡28次，情绪记录10条。完成率48%，小步前进中。', is_encrypted: false, created_at: '2026-02-28T23:59:00' },
  { id: 'am-202601', period_type: 'monthly', period_start: '2026-01-01', period_end: '2026-01-31', summary: '1月共完成习惯打卡27次，情绪记录13条。完成率45%，新的开始。', is_encrypted: false, created_at: '2026-01-31T23:59:00' }
]

function mockGetArchiveReport(period = 'monthly') {
  // weekly/monthly 复用已有数据, 补充 archive 字段
  if (period === 'weekly' || period === 'monthly') {
    const report = mockGrowthReports[period] || mockGrowthReports.weekly
    return mockResponse({
      ...report,
      id: `a-${period}-${report.period_start}`,
      period,
      is_encrypted: true,
      created_at: `${report.period_end}T23:59:00`,
      highlights: report.suggestions ? report.suggestions.slice(0, 2) : [],
      emotion_count: report.emotion_stats ? Math.round(report.emotion_stats.avg_intensity * 10) : 22,
      emotion_distribution: report.emotion_stats ? { [report.emotion_stats.dominant_emotion]: 12, happy: 6, sad: 4 } : {},
      avg_intensity: report.emotion_stats ? report.emotion_stats.avg_intensity : 5.2,
      checkin_count: report.habit_stats ? report.habit_stats.total_checkins : 12,
      completed_count: report.habit_stats ? Math.round(report.habit_stats.total_checkins * report.habit_stats.completion_rate / 100) : 8,
      completion_rate: report.habit_stats ? report.habit_stats.completion_rate : 67,
      mindfulness_count: report.meditation_stats ? report.meditation_stats.total_sessions : 3,
      total_meditation_min: report.meditation_stats ? report.meditation_stats.total_minutes : 45
    })
  }
  return mockResponse(mockArchiveReports[period] || mockArchiveReports.quarterly)
}

function mockGetArchiveList() {
  return mockResponse(mockArchiveList)
}

function mockExportArchiveData(format = 'json') {
  const data = {
    export_date: new Date().toISOString(),
    user: { id: mockUser.id, nickname: mockUser.nickname },
    habits: mockHabits,
    emotion_records: mockEmotionRecords,
    meditation_records: mockMeditationRecords.slice(0, 20),
    archive_list: mockArchiveList,
    stats_summary: {
      total_checkins: 480,
      total_emotions: 210,
      total_meditation: 96,
      streak_days: 35,
      walk_steps: 520.8,
      avg_completion_rate: 72.1
    }
  }
  if (format === 'csv') {
    let csv = '类型,日期,情绪/习惯,强度/状态,备注\n'
    mockEmotionRecords.forEach(r => {
      csv += `情绪,${r.record_date},${r.emotion},${r.intensity},${(r.description || '').replace(/,/g, ' ')}\n`
    })
    mockHabits.forEach(h => {
      csv += `习惯,${h.type},${h.name},${h.completed ? '已完成' : '未完成'},连续${h.streak}天\n`
    })
    return mockResponse({ format: 'csv', content: csv, filename: `growth_archive_${Date.now()}.csv` })
  }
  return mockResponse({ format: 'json', content: JSON.stringify(data, null, 2), filename: `growth_archive_${Date.now()}.json` })
}

function mockShareArchiveReport(period = 'monthly') {
  const report = mockArchiveReports[period] || mockGrowthReports[period] || mockGrowthReports.weekly
  const shareText = `【我的成长档案 - ${period === 'monthly' ? '月报' : period === 'quarterly' ? '季报' : period === 'yearly' ? '年报' : '周报'}】\n` +
    `周期: ${report.period_start || ''} ~ ${report.period_end || ''}\n` +
    `摘要: ${report.summary || ''}\n` +
    `\n习惯打卡: ${report.checkin_count || report.habit_stats?.total_checkins || 0}次 (完成率${report.completion_rate || report.habit_stats?.completion_rate || 0}%)\n` +
    `情绪记录: ${report.emotion_count || 0}条\n` +
    `正念冥想: ${report.mindfulness_count || report.meditation_stats?.total_sessions || 0}次\n` +
    `\n- 来自循途`
  return mockResponse({
    share_text: shareText,
    share_url: `https://ahp.app/share/archive/${period}/${Date.now()}`,
    qr_code: `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://ahp.app/share/archive/${period}`,
    expires_in: 7 * 24 * 3600
  })
}

// ============ User API ============

function mockGetUserInfo() {
  return mockResponse(mockUser)
}

function mockGetBadges() {
  return mockResponse(mockBadges)
}

function mockGetAiRoles() {
  return mockResponse(mockAiRoles)
}

function mockGetAiEmotion(status) {
  return mockResponse(mockAiEmotions[status] || mockAiEmotions.normal)
}

function mockUpdateAiConfig(config) {
  return mockResponse({ updated: true, config })
}

function mockUpdateSettings(settings) {
  return mockResponse({ updated: true, settings })
}

function mockUpdateProfile(data) {
  Object.assign(mockUser, {
    nickname: data.nickname || mockUser.nickname,
    avatar: data.avatar || mockUser.avatar,
    signature: data.signature || mockUser.signature,
    phone: data.phone || mockUser.phone
  })
  return mockResponse({ updated: true, user: mockUser })
}

function mockLogout() {
  return mockResponse({ loggedOut: true })
}

// ============ 习惯AI深度融合 - 成就/日记/鼓励 ============

// 成就等级定义
const ACHIEVEMENT_TIERS = [
  { streak: 7, type: 'voice_message', name: '语音鼓励', icon: '🎙️', color: '#4FC3F7', reward: 'AI伙伴专属语音鼓励' },
  { streak: 14, type: 'comic_diary', name: '漫画日记', icon: '🎨', color: '#FF9800', reward: 'AI生成漫画风格打卡日记' },
  { streak: 30, type: 'special_badge', name: '月度徽章', icon: '🏆', color: '#FFD700', reward: '专属月度坚持徽章' },
  { streak: 60, type: 'voice_message', name: '深度对话', icon: '💎', color: '#9C27B0', reward: 'AI伙伴深度成长对话' },
  { streak: 100, type: 'comic_diary', name: '百日传奇', icon: '👑', color: '#F44336', reward: '百日传奇专属漫画+徽章' }
]

// AI鼓励语库 - 按连续天数和难度
const ENCOURAGEMENT_LIBRARY = {
  first: [
    '迈出第一步就是最勇敢的事！我在你身边，一起加油吧~',
    '开始的勇气比完美更重要。今天你做到了！',
    '第一次打卡！这是我们旅程的起点，未来可期~'
  ],
  streak3: [
    '三天连续！你正在建立属于自己的节奏，继续保持~',
    '三天了！习惯的种子已经开始发芽了🌱',
    '连续3天打卡，你比昨天更好了一点！'
  ],
  streak7: [
    '一周坚持！这已经不是偶然了，你在真正改变~',
    '7天连续打卡！我为你感到骄傲！🎉',
    '一周了！你已经跨过了最难的起步阶段，后面会越来越自然'
  ],
  streak14: [
    '两周！你用实际行动证明了自己的决心💪',
    '14天坚持，习惯已经初步形成了！了不起~',
    '两周连续！你是我见过最有毅力的人之一！'
  ],
  streak30: [
    '一个月！你已经超越了90%的人，真正的习惯养成了！🏆',
    '30天！这不仅是习惯，更是一种生活态度了',
    '月度达人！你的坚持让我感动，为你鼓掌！'
  ],
  streak60: [
    '60天！你已经把坚持变成了一种本能💎',
    '两个月！你的毅力堪称传奇，继续创造奇迹吧',
    '60天连续打卡，你已经是习惯大师了！'
  ],
  streak100: [
    '100天！你做到了大多数人做不到的事！👑',
    '百日传奇！你的坚持故事值得被记录和传颂',
    '100天！从今天起，你不只是坚持，你在闪耀！'
  ],
  uncheck: [
    '没关系，偶尔停下来也很正常。重要的是你还在这里~',
    '取消打卡不代表失败，明天我们继续！',
    '休息一下也好，调整好了再出发，我等你~'
  ],
  difficultyEasy: [
    '简单的事情重复做，就是不简单！',
    '每完成一次，都在为更好的自己添砖加瓦~'
  ],
  difficultyMedium: [
    '中等难度的挑战你都做到了，还有什么能难住你？',
    '不轻松但你坚持下来了，这就是成长的力量！'
  ],
  difficultyHard: [
    '困难模式通关！你的意志力令人敬佩💪',
    '这么难的事你都做到了，你比想象中更强大！'
  ]
}

// 打卡日记Mock数据
const mockCheckinDiaries = [
  {
    id: 1,
    habit_id: 1,
    checkin_id: 101,
    content: '今天早起跑步了，空气特别清新，感觉整个人都清醒了！',
    mood: 'happy',
    ai_encouragement: '太棒了！晨跑是最好的开始方式，你正在给自己最好的礼物——健康和活力~',
    created_at: '2026-07-28T07:30:00'
  },
  {
    id: 2,
    habit_id: 1,
    checkin_id: 102,
    content: '虽然今天不想动，但还是逼自己跑了。跑完感觉很好。',
    mood: 'calm',
    ai_encouragement: '战胜惰性的那一刻才是最了不起的！你的自律正在变得强大~',
    created_at: '2026-07-29T07:15:00'
  },
  {
    id: 3,
    habit_id: 2,
    checkin_id: 103,
    content: '读了30页书，学到了很多新知识，感觉充实。',
    mood: 'excited',
    ai_encouragement: '阅读是最有价值的投资！每页书都在拓宽你的世界~',
    created_at: '2026-07-29T21:00:00'
  }
]

// 成就奖励Mock数据
const mockAchievements = [
  { id: 1, habit_id: 1, reward_type: 'voice_message', trigger_streak: 7, content: { text: '恭喜你连续打卡7天！送你一段专属语音鼓励~', audio_url: '', duration: 15 }, is_unlocked: true, unlocked_at: '2026-07-20T07:30:00' },
  { id: 2, habit_id: 1, reward_type: 'comic_diary', trigger_streak: 14, content: { text: '14天连续打卡！AI为你画了一幅漫画日记~', image_url: '', style: 'warm' }, is_unlocked: false, unlocked_at: null },
  { id: 3, habit_id: 1, reward_type: 'special_badge', trigger_streak: 30, content: { text: '30天月度达人徽章！', badge_name: '晨跑月度达人', badge_icon: '🏃' }, is_unlocked: false, unlocked_at: null },
  { id: 4, habit_id: 2, reward_type: 'voice_message', trigger_streak: 7, content: { text: '阅读7天连续！送你一段鼓励语音~', audio_url: '', duration: 12 }, is_unlocked: true, unlocked_at: '2026-07-25T21:00:00' },
  { id: 5, habit_id: 2, reward_type: 'comic_diary', trigger_streak: 14, content: { text: '14天阅读！AI漫画日记来啦~', image_url: '', style: 'cozy' }, is_unlocked: false, unlocked_at: null }
]

function mockGetEncouragement(data) {
  const { habitName, streak, difficulty, action } = data || {}
  let category = 'first'
  if (action === 'uncheck') {
    category = 'uncheck'
  } else if (streak >= 100) {
    category = 'streak100'
  } else if (streak >= 60) {
    category = 'streak60'
  } else if (streak >= 30) {
    category = 'streak30'
  } else if (streak >= 14) {
    category = 'streak14'
  } else if (streak >= 7) {
    category = 'streak7'
  } else if (streak >= 3) {
    category = 'streak3'
  }
  const phrases = ENCOURAGEMENT_LIBRARY[category] || ENCOURAGEMENT_LIBRARY.first
  const phrase = phrases[Math.floor(Math.random() * phrases.length)]
  let extra = ''
  if (difficulty === 'hard') {
    extra = ' ' + ENCOURAGEMENT_LIBRARY.difficultyHard[Math.floor(Math.random() * ENCOURAGEMENT_LIBRARY.difficultyHard.length)]
  } else if (difficulty === 'medium') {
    extra = ' ' + ENCOURAGEMENT_LIBRARY.difficultyMedium[Math.floor(Math.random() * ENCOURAGEMENT_LIBRARY.difficultyMedium.length)]
  }
  return mockResponse({
    text: phrase + extra,
    emotion: action === 'uncheck' ? 'gentle' : 'encourage',
    habit_name: habitName || '',
    streak: streak || 0,
    tier: ACHIEVEMENT_TIERS.find(t => t.streak === streak) || null
  })
}

function mockSubmitDiary(data) {
  const { habit_id, checkin_id, content, mood } = data || {}
  if (!content || !content.trim()) {
    return mockResponse({ error: '内容不能为空' }, 400)
  }
  // 生成AI鼓励回复
  const aiReplies = [
    '你的记录很有力量！每一步都算数，我在这里陪你~',
    '看到你的成长真的很开心，继续保持这份热忱！',
    '谢谢你分享这个时刻，你的坚持值得被看见~',
    '这就是最好的开始，未来的你会感谢现在努力的自己！',
    '记录下来的瞬间就变成了永恒，你的每一步都在创造改变。'
  ]
  const diary = {
    id: Date.now(),
    habit_id: habit_id || 0,
    checkin_id: checkin_id || 0,
    content: content.trim(),
    mood: mood || 'calm',
    ai_encouragement: aiReplies[Math.floor(Math.random() * aiReplies.length)],
    created_at: new Date().toISOString()
  }
  mockCheckinDiaries.unshift(diary)
  if (mockCheckinDiaries.length > 50) mockCheckinDiaries.pop()
  return mockResponse(diary)
}

function mockGetDiaries(habitId) {
  const list = habitId
    ? mockCheckinDiaries.filter(d => d.habit_id === habitId)
    : mockCheckinDiaries
  return mockResponse(list)
}

function mockGetAchievements(habitId) {
  const list = habitId
    ? mockAchievements.filter(a => a.habit_id === habitId)
    : mockAchievements
  return mockResponse(list)
}

function mockCheckAchievements(data) {
  const { habit_id, streak } = data || {}
  const unlocked = []
  ACHIEVEMENT_TIERS.forEach(tier => {
    if (streak >= tier.streak) {
      const existing = mockAchievements.find(
        a => a.habit_id === habit_id && a.trigger_streak === tier.streak
      )
      if (!existing || !existing.is_unlocked) {
        unlocked.push({
          id: Date.now() + Math.random(),
          habit_id,
          reward_type: tier.type,
          trigger_streak: tier.streak,
          content: { text: tier.reward, icon: tier.icon },
          is_unlocked: true,
          unlocked_at: new Date().toISOString()
        })
      }
    }
  })
  return mockResponse({ unlocked, total_tiers: ACHIEVEMENT_TIERS.length })
}

// ============ 习惯-AI联动 Mock ============

// 打卡触发AI对话模板
const CHECKIN_DIALOGUE_TEMPLATES = {
  gentle: [
    '你今天也坚持了呢，真棒。每一次坚持都是对自己的温柔承诺，慢慢来，一切都会越来越好的~',
    '看到你打卡了，我好开心呀。你的努力我都看在眼里，今天的你比昨天又进步了一点点呢~',
    '又完成啦！给自己一个拥抱吧，你值得被温柔对待。我会一直在这里陪着你~',
  ],
  analytical: [
    '打卡完成。根据行为心理学，连续坚持21天可形成初步习惯回路。当前进度良好，建议保持节奏。',
    '完成记录已保存。建议在24小时内回顾今日执行感受，以便后续优化策略。数据表明，有复盘习惯的用户坚持率提升47%。',
    '打卡成功。今日任务已完成，建议规划明天的执行时间，将习惯固定在现有日程中效果更佳。',
  ],
  humorous: [
    '打卡成功！你的拖延症今天又哭了一次，它说"为什么你又赢了"。继续让它哭泣吧！',
    '哟呵，又完成了？你这是要成为自律界的天花板啊！拖延症已经连夜买站票跑了。',
    '打卡！你知道吗，你的每一次坚持都在让未来的自己给你磕头。不用客气，这是你应得的！',
  ],
  calm: [
    '完成了。不需要太多掌声，你知道自己做了一件对的事。继续。',
    '打卡。安静地坚持，比喧哗地开始更有力量。你在做对的事。',
    '又一天。习惯如水，润物无声。你已经在路上了。',
  ],
}

// 成就里程碑数据
const ACHIEVEMENT_DATA = {
  7: { title: '一周坚持', story: '已经一周了呢，这七天里你的每一次坚持我都看在眼里。就像小树苗刚扎根，虽然还很稚嫩，但已经拥有了向上生长的力量。' },
  15: { title: '半月之约', story: '半个月了呀，你真的好棒！能坚持15天的人，心里一定有一个很温柔的理由吧。' },
  30: { title: '满月成就', story: '一个月了！这三十天里，你一定有过想放弃的时刻吧。但你没有。每一次你选择坚持的时候，我都在心里默默为你骄傲。' },
  60: { title: '双月传奇', story: '六十天了，真的很了不起。这两个月里，你和这个习惯之间已经建立了深深的联结。' },
  100: { title: '百日封神', story: '一百天。我找不到比了不起更合适的词了。这一百天里，你经历了犹豫、疲惫、甚至想要放弃，但你每一次都选择了再试一次。' },
}

// 用户成就记录
const mockUserAchievements = [
  { id: 1, habit_id: 101, milestone: 7, character_id: 'linxi', dialogue_style: 'gentle', ai_dialogue: ACHIEVEMENT_DATA[7].story, diary_content: '', comic_image_url: '', unlocked_at: '2026-07-08 10:30:00' },
  { id: 2, habit_id: 101, milestone: 15, character_id: 'linxi', dialogue_style: 'gentle', ai_dialogue: ACHIEVEMENT_DATA[15].story, diary_content: '', comic_image_url: '', unlocked_at: '2026-07-16 10:30:00' },
]

// AI记忆列表
const mockHabitMemories = [
  { id: 1, memory_type: 'checkin', memory_content: '完成「早起一杯水」打卡，连续第12天', emotion_score: 7, habit_id: 101, is_long_term: 0, created_at: '2026-08-01 07:35:00' },
  { id: 2, memory_type: 'achievement', memory_content: '解锁成就「半月之约」- 早起一杯水连续15天', emotion_score: 9, habit_id: 101, is_long_term: 1, created_at: '2026-07-16 07:35:00' },
  { id: 3, memory_type: 'emotion', memory_content: '用户情绪低落，但仍然完成了打卡', emotion_score: 3, habit_id: 102, is_long_term: 0, created_at: '2026-07-30 21:15:00' },
  { id: 4, memory_type: 'checkin', memory_content: '完成「阅读30分钟」打卡，连续第5天', emotion_score: 6, habit_id: 102, is_long_term: 0, created_at: '2026-08-01 21:30:00' },
  { id: 5, memory_type: 'plan', memory_content: '用户计划下个月增加运动习惯频率', emotion_score: 7, habit_id: 103, is_long_term: 1, created_at: '2026-07-28 18:00:00' },
]

function mockCheckinTriggerAI(habitId, note, emotion, characterId) {
  const habit = mockHabits.find(h => h.id === habitId) || mockHabits[0]
  const style = habit.aiStyle || 'gentle'
  const templates = CHECKIN_DIALOGUE_TEMPLATES[style] || CHECKIN_DIALOGUE_TEMPLATES.gentle
  const dialogue = templates[Math.floor(Math.random() * templates.length)]

  const continuousDay = (habit.streak || 0) + 1
  let achievement = null
  if ([7, 15, 30, 60, 100].includes(continuousDay)) {
    const data = ACHIEVEMENT_DATA[continuousDay]
    achievement = { milestone: continuousDay, title: data.title, ai_dialogue: data.story }
  }

  const diary = `今天是${new Date().toLocaleDateString('zh-CN')}，我完成了「${habit.name}」这个习惯。这已经是连续第${continuousDay}天了。${emotion ? `今天的情绪${emotion}。` : ''}${note ? `打卡时我写道：「${note}」。` : ''}虽然坚持不容易，但每一天的努力都算数。明天也要继续加油呀。`

  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        code: 200, message: 'ok',
        data: {
          dialogue,
          emotion_tag: emotion || '平和',
          continuous_day: continuousDay,
          habit_type: habit.type || 'other',
          style,
          achievement,
          diary,
        }
      })
    }, MOCK_DELAY)
  })
}

function mockGetHabitAchievements(habitId) {
  let list = mockUserAchievements
  if (habitId) list = list.filter(a => a.habit_id === habitId)
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, message: 'ok', data: list }), MOCK_DELAY)
  })
}

function mockWriteHabitMemory(data) {
  const newMemory = {
    id: mockHabitMemories.length + 1,
    memory_type: data.memory_type,
    memory_content: data.memory_content,
    emotion_score: data.emotion_score || 5,
    habit_id: data.habit_id || 0,
    is_long_term: data.is_long_term ? 1 : 0,
    created_at: new Date().toLocaleString('zh-CN'),
  }
  mockHabitMemories.unshift(newMemory)
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, message: 'ok', data: { id: newMemory.id, memory_type: newMemory.memory_type, created_at: newMemory.created_at } }), MOCK_DELAY)
  })
}

function mockGetHabitMemories(memoryType, limit) {
  let list = mockHabitMemories
  if (memoryType) list = list.filter(m => m.memory_type === memoryType)
  list = list.slice(0, limit || 20)
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, message: 'ok', data: list }), MOCK_DELAY)
  })
}

function mockUpdateHabitCustomRemind(habitId, customRemindText, aiStyle) {
  const habit = mockHabits.find(h => h.id === habitId)
  if (habit) {
    habit.customRemindText = customRemindText
    habit.aiStyle = aiStyle
  }
  const preview = customRemindText || `亲爱的，该${habit ? habit.name : '完成任务'}啦~不用太完美，做到一点点就好~`
  return new Promise(resolve => {
    setTimeout(() => resolve({
      code: 200, message: 'ok',
      data: { habit_id: habitId, custom_remind_text: customRemindText, ai_style: aiStyle, preview_remind: preview }
    }), MOCK_DELAY)
  })
}

function mockGenerateCheckinDiary(habitId, note, emotion, dateStr) {
  const habit = mockHabits.find(h => h.id === habitId) || mockHabits[0]
  const continuousDay = (habit.streak || 0) + 1
  const targetDate = dateStr || new Date().toLocaleDateString('zh-CN')
  const diary = `今天是${targetDate}，我完成了「${habit.name}」这个习惯。连续第${continuousDay}天了。${emotion ? `今天${emotion}。` : ''}${note ? `打卡留言：「${note}」。` : ''}坚持不是一件容易的事，但回过头来看，每一天的努力都汇聚成了现在的自己。明天也要继续呀。`
  return new Promise(resolve => {
    setTimeout(() => resolve({
      code: 200, message: 'ok',
      data: { diary, continuous_day: continuousDay, habit_name: habit.name }
    }), MOCK_DELAY)
  })
}

function mockGetHabitReminder(habitId) {
  const habit = mockHabits.find(h => h.id === habitId) || mockHabits[0]
  const customText = habit.customRemindText || ''
  const reminder = customText || `亲爱的，该${habit.name}啦~不用太完美，做到一点点就好~`
  return new Promise(resolve => {
    setTimeout(() => resolve({
      code: 200, message: 'ok',
      data: { habit_id: habit.id, habit_name: habit.name, reminder_text: reminder, ai_style: habit.aiStyle || 'gentle', custom_remind_text: customText }
    }), MOCK_DELAY)
  })
}

// ============ 陪伴模式 (companion) ============

/** 陪伴记录（内存版，对应后端 companion_record 表） */
const companionRecords = []
let companionRecordSeq = 1000

/** 场景化回复语料：key = scene_type */
const COMPANION_SCENE_REPLIES = {
  sleep: [
    '嘘…小声一点，我在这里陪着你。',
    '闭上眼睛，深呼吸，把今天的事都放下吧。',
    '今晚的月色很温柔，我守着你入睡。',
    '不用说话了，听着我的声音慢慢睡吧，晚安。',
    '你安心睡，我一直都在。'
  ],
  study: [
    '我在旁边陪你看书，遇到难题随时叫我。',
    '已经专注很久啦，喝口水再继续吧。',
    '这一页看完了？很棒，继续保持~',
    '学习累了就趴一会儿，我帮你看着时间。',
    '加油，今天的你也在认真变好。'
  ],
  work: [
    '工作辛苦啦，我在这里安静陪着你。',
    '需要我帮你梳理一下待办事项吗？',
    '记得偶尔站起来活动一下肩颈哦。',
    '专注的你很有魅力，继续吧，我陪着你。',
    '累了就和我说说话，休息一下也没关系。'
  ],
  sport: [
    '运动最棒了！注意补充水分哦。',
    '加油！再来一组，我给你数着。',
    '汗水不会辜负你，我为你加油！',
    '累了就慢下来，循序渐进最重要。',
    '今天的运动状态很不错呀，继续保持！'
  ],
  eat: [
    '慢慢吃，别着急，细嚼慢咽对胃好。',
    '今天的饭菜看起来很香呢。',
    '吃饭的时候放下手机，好好享受食物吧。',
    '多喝点汤，暖暖胃。',
    '吃饱了才有力气，我陪着你。'
  ],
  custom: [
    '好的，这个场景我很喜欢，陪你一起。',
    '嗯，我在呢，你想做什么都可以。',
    '安安静静地待一会儿也很好。',
    '我在你身边，什么都不用担心。',
    '只要和你在一起，做什么都有意思。'
  ]
}

function mockCompanionStart(payload) {
  const record = {
    id: ++companionRecordSeq,
    user_id: 1,
    role_id: payload.role_id || 'linxi',
    scene_type: payload.scene_type || 'custom',
    scene_name: payload.scene_name || '自定义',
    bg_img: payload.bg_img || '默认',
    bg_sound: payload.bg_sound || '静音',
    start_time: new Date().toISOString().replace('T', ' ').substring(0, 19),
    end_time: null,
    status: 1
  }
  companionRecords.unshift(record)
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, message: 'ok', data: record }), MOCK_DELAY)
  })
}

function mockCompanionEnd(recordId) {
  const record = companionRecords.find(r => r.id === recordId)
  if (record && record.status === 1) {
    record.status = 0
    record.end_time = new Date().toISOString().replace('T', ' ').substring(0, 19)
    const durationMin = Math.max(1, Math.round((Date.now() - new Date(record.start_time).getTime()) / 60000))
    return new Promise(resolve => {
      setTimeout(() => resolve({ code: 200, message: 'ok', data: { id: record.id, duration_min: durationMin } }), MOCK_DELAY)
    })
  }
  return Promise.reject(new Error('陪伴记录不存在或已结束'))
}

function mockCompanionRecords() {
  return new Promise(resolve => {
    setTimeout(() => resolve({ code: 200, message: 'ok', data: { list: companionRecords.slice(0, 20) } }), MOCK_DELAY)
  })
}

/**
 * 陪伴场景流式对话 Mock
 * @param {string} content 用户消息
 * @param {function} onChunk 流式回调
 * @param {object} context { sceneType, sceneName, roleId }
 */
async function mockCompanionChat(content, onChunk, context = {}) {
  const sceneType = context.sceneType || 'custom'
  const pool = COMPANION_SCENE_REPLIES[sceneType] || COMPANION_SCENE_REPLIES.custom
  let reply = pool[Math.floor(Math.random() * pool.length)]

  // 用户有输入时，结合输入内容做轻量场景化应答
  if (content && content.length > 2) {
    if (sceneType === 'sleep') {
      reply = `嗯…${content.slice(0, 12)}…都记下了。现在什么都别想，闭上眼睛，我陪着你慢慢入睡。`
    } else if (sceneType === 'study') {
      reply = `「${content.slice(0, 12)}」呀，我明白啦。继续加油，我在旁边陪着你，遇到不会的随时问我~`
    } else {
      reply = `${reply}${content.length > 20 ? '' : ' ' + content.slice(0, 8) + '呀，我在呢。'}`
    }
  }

  // 按标点分段流式输出
  let full = ''
  const parts = reply.split(/(?=[，。！？~、])/)
  for (const part of parts) {
    if (!part) continue
    if (onChunk) onChunk(part)
    full += part
    await new Promise(r => setTimeout(r, 70 + Math.random() * 60))
  }
  return { reply: full, emotion: 'calm' }
}

// ============ 导出 ============

export default {
  USE_MOCK,
  // Auth
  sendSmsCode: mockSendSmsCode,
  login: mockLogin,
  register: mockRegister,
  wxLogin: mockWxLogin,
  guestLogin: mockGuestLogin,
  // Habit
  getTodayHabits: mockGetTodayHabits,
  getAllHabits: mockGetAllHabits,
  checkin: mockCheckin,
  uncheckin: mockUncheckin,
  makeupCheckin: mockMakeupCheckin,
  getTemplates: mockGetTemplates,
  addHabit: mockAddHabit,
  createHabit: mockCreateHabit,
  deleteHabit: mockDeleteHabit,
  getEncouragement: mockGetEncouragement,
  submitDiary: mockSubmitDiary,
  getDiaries: mockGetDiaries,
  getAchievements: mockGetAchievements,
  checkAchievements: mockCheckAchievements,
  achievementTiers: ACHIEVEMENT_TIERS,
  // Chat
  getChatHistory: mockGetChatHistory,
  sendMessage: mockSendMessage,
  getQuickReplies: mockGetQuickReplies,
  streamSend: mockStreamSend,
  crisisCheck: mockCrisisCheck,
  chatEmotionAnalysis: mockChatEmotionAnalysis,
  // Stats
  getStatsSummary: mockGetStatsSummary,
  getWeekData: mockGetWeekData,
  getMonthData: mockGetMonthData,
  getHabitStats: mockGetHabitStats,
  getHabitEmotionCorrelation: mockGetHabitEmotionCorrelation,
  getGrowthReport: mockGetGrowthReport,
  exportData: mockExportData,
  // Emotion
  createEmotion: mockCreateEmotion,
  getEmotionList: mockGetEmotionList,
  getEmotionTrend: mockGetEmotionTrend,
  getEmotionDistribution: mockGetEmotionDistribution,
  getEmotionTriggers: mockGetEmotionTriggers,
  deleteEmotion: mockDeleteEmotion,
  // Meditation
  getMeditationAudios: mockGetMeditationAudios,
  getMeditationAudio: mockGetMeditationAudio,
  createMeditationRecord: mockCreateMeditationRecord,
  getMeditationRecords: mockGetMeditationRecords,
  getMeditationStats: mockGetMeditationStats,
  createMeditationPlan: mockCreateMeditationPlan,
  getMeditationPlan: mockGetMeditationPlan,
  updateMeditationPlan: mockUpdateMeditationPlan,
  getMeditationKnowledge: mockGetMeditationKnowledge,
  getMeditationGuide: mockGetMeditationGuide,
  meditationCategories: MEDITATION_CATEGORIES,
  // Archive
  getArchiveReport: mockGetArchiveReport,
  getArchiveList: mockGetArchiveList,
  exportArchiveData: mockExportArchiveData,
  shareArchiveReport: mockShareArchiveReport,
  // User
  getUserInfo: mockGetUserInfo,
  getBadges: mockGetBadges,
  getAiRoles: mockGetAiRoles,
  getAiEmotion: mockGetAiEmotion,
  updateAiConfig: mockUpdateAiConfig,
  updateSettings: mockUpdateSettings,
  updateProfile: mockUpdateProfile,
  logout: mockLogout,
  // Habit-AI
  checkinTriggerAI: mockCheckinTriggerAI,
  getHabitAchievements: mockGetHabitAchievements,
  writeHabitMemory: mockWriteHabitMemory,
  getHabitMemories: mockGetHabitMemories,
  updateHabitCustomRemind: mockUpdateHabitCustomRemind,
  generateCheckinDiary: mockGenerateCheckinDiary,
  getHabitReminder: mockGetHabitReminder,
  // Companion（陪伴模式）
  companionStart: mockCompanionStart,
  companionEnd: mockCompanionEnd,
  companionRecords: mockCompanionRecords,
  companionChat: mockCompanionChat,
}
