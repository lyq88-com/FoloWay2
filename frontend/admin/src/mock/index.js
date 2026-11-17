/**
 * Admin Mock 数据层 - 拦截 axios 请求返回模拟数据
 * 后端就绪后，将 USE_MOCK 设为 false 即可切换到真实 API
 * 统一响应格式: { code: 200, message: "ok", data: {...} }
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const USE_MOCK = true
const MOCK_DELAY = 300

// ============ 模拟数据库 ============

// 管理员信息
const mockAdmin = {
  id: 1,
  username: 'admin',
  nickname: '超级管理员',
  avatar: '',
  role: 'super_admin',
  roleName: '超级管理员',
  lastLoginTime: '2026-07-18 14:30:00',
  lastLoginIp: '127.0.0.1'
}

// 用户列表 (生成50条模拟数据)
const mockUsers = Array.from({ length: 50 }, (_, i) => {
  const names = ['习惯达人', '自律先锋', '晨型人格', '阅读者', '运动健将', '冥想大师', '程序员', '早起鸟', '夜猫子', '水吧客']
  const avatars = ['🐱', '🐶', '🐰', '🦊', '🐼', '🐨', '🦁', '🐯', '🐸', '🐵']
  const genders = [0, 1, 2]
  const statuses = i < 3 ? [0] : [1] // 前3个是禁用的
  return {
    id: 10001 + i,
    phone: `138****${String(8888 + i).padStart(4, '0')}`,
    nickname: `${names[i % 10]}${i > 9 ? i : ''}`,
    avatar: avatars[i % 10],
    gender: genders[i % 3],
    genderText: genders[i % 3] === 1 ? '男' : genders[i % 3] === 2 ? '女' : '未知',
    status: statuses[0],
    statusText: statuses[0] === 1 ? '正常' : '禁用',
    level: Math.floor(i / 10) + 1,
    levelName: ['习惯新手', '自律学徒', '坚持达人', '习惯大师', '自律传奇'][Math.floor(i / 10)],
    habitCount: (i % 3) + 1,
    totalCheckins: Math.floor(Math.random() * 100) + 5,
    streakDays: Math.floor(Math.random() * 30),
    registerTime: `2026-07-${String((i % 18) + 1).padStart(2, '0')} ${String(Math.floor(Math.random() * 24)).padStart(2, '0')}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}:00`,
    lastLoginTime: `2026-07-18 ${String(Math.floor(Math.random() * 24)).padStart(2, '0')}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}:00`,
    aiRole: ['cute', 'gentle', 'serious', 'energetic'][i % 4]
  }
})

// 任务模板 (8种)
const mockTemplates = [
  { id: 1, type: 'morning', name: '早起一杯水', icon: '💧', description: '每天起床后喝一杯温水唤醒身体', defaultTarget: '喝200ml温水', color: '#4FC3F7', difficulty: 'easy', multiplier: 1.0, sortOrder: 1, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 2, type: 'sport', name: '运动健身', icon: '🏃', description: '跑步、瑜伽或力量训练', defaultTarget: '运动15分钟', color: '#FF6B6B', difficulty: 'medium', multiplier: 1.5, sortOrder: 2, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 3, type: 'read', name: '阅读学习', icon: '📚', description: '读书或学习新技能', defaultTarget: '阅读30分钟', color: '#FFD93D', difficulty: 'medium', multiplier: 1.5, sortOrder: 3, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 4, type: 'drink', name: '充足饮水', icon: '🥤', description: '保持每日饮水量', defaultTarget: '喝8杯水', color: '#4DD0E1', difficulty: 'easy', multiplier: 1.0, sortOrder: 4, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 5, type: 'sleep', name: '早睡早起', icon: '😴', description: '23点前入睡，7点前起床', defaultTarget: '23:00前入睡', color: '#7986CB', difficulty: 'hard', multiplier: 2.0, sortOrder: 5, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 6, type: 'meditate', name: '冥想静心', icon: '🧘', description: '每日冥想放松身心', defaultTarget: '冥想10分钟', color: '#BA68C8', difficulty: 'medium', multiplier: 1.5, sortOrder: 6, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 7, type: 'write', name: '日记复盘', icon: '✏️', description: '记录每日所思所想', defaultTarget: '写200字日记', color: '#81C784', difficulty: 'easy', multiplier: 1.0, sortOrder: 7, status: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 8, type: 'code', name: '编程练习', icon: '💻', description: '每日编码保持技术敏感度', defaultTarget: '写1个小程序', color: '#78909C', difficulty: 'hard', multiplier: 2.0, sortOrder: 8, status: 1, createdAt: '2026-07-01 10:00:00' }
]

// AI角色 (4种)
const mockAiRoles = [
  { id: 1, roleType: 'cute', name: '小萌', personality: '可爱活泼，喜欢用emoji', description: '元气满满的鼓励型伙伴', systemPrompt: '你是一个可爱活泼的AI习惯伙伴，喜欢用emoji表达情感，语气温萌可爱，善于鼓励用户坚持好习惯。', status: 1, sortOrder: 1, createdAt: '2026-07-01 10:00:00' },
  { id: 2, roleType: 'gentle', name: '暖阳', personality: '温柔体贴，善于倾听', description: '如阳光般温暖的存在', systemPrompt: '你是一个温柔体贴的AI习惯伙伴，善于倾听用户的感受，用温暖的话语安慰和鼓励用户。', status: 1, sortOrder: 2, createdAt: '2026-07-01 10:00:00' },
  { id: 3, roleType: 'serious', name: '严师', personality: '严肃认真，目标导向', description: '帮你保持自律的教练', systemPrompt: '你是一个严肃认真的AI习惯伙伴，以目标为导向，用理性的分析帮助用户保持自律。', status: 1, sortOrder: 3, createdAt: '2026-07-01 10:00:00' },
  { id: 4, roleType: 'energetic', name: '闪电', personality: '热情奔放，充满活力', description: '永远充满能量的拉拉队长', systemPrompt: '你是一个热情奔放的AI习惯伙伴，充满活力，用积极向上的态度感染用户。', status: 1, sortOrder: 4, createdAt: '2026-07-01 10:00:00' }
]

// AI角色素材 (每角色6种情绪)
const mockRoleAssets = {
  1: [
    { id: 101, roleId: 1, emotionStatus: 'normal', emotionText: '平静', assetUrl: '', bubbleText: '我在呢，有什么想聊的吗？', animationType: 'float', status: 1 },
    { id: 102, roleId: 1, emotionStatus: 'happy', emotionText: '开心', assetUrl: '', bubbleText: '太棒了！继续保持哦~', animationType: 'bounce', status: 1 },
    { id: 103, roleId: 1, emotionStatus: 'sad', emotionText: '难过', assetUrl: '', bubbleText: '没关系，明天会更好的', animationType: 'shake', status: 1 },
    { id: 104, roleId: 1, emotionStatus: 'gentle', emotionText: '温柔', assetUrl: '', bubbleText: '慢慢来，不着急~', animationType: 'pulse', status: 1 },
    { id: 105, roleId: 1, emotionStatus: 'encourage', emotionText: '鼓励', assetUrl: '', bubbleText: '你可以的！我相信你！', animationType: 'bounce', status: 1 },
    { id: 106, roleId: 1, emotionStatus: 'chat', emotionText: '聊天', assetUrl: '', bubbleText: '嗯嗯，我在听呢~', animationType: 'float', status: 1 }
  ],
  2: [
    { id: 201, roleId: 2, emotionStatus: 'normal', emotionText: '平静', assetUrl: '', bubbleText: '今天感觉怎么样？', animationType: 'float', status: 1 },
    { id: 202, roleId: 2, emotionStatus: 'happy', emotionText: '开心', assetUrl: '', bubbleText: '看到你进步，我很开心', animationType: 'pulse', status: 1 },
    { id: 203, roleId: 2, emotionStatus: 'sad', emotionText: '难过', assetUrl: '', bubbleText: '没关系，我陪着你', animationType: 'float', status: 1 },
    { id: 204, roleId: 2, emotionStatus: 'gentle', emotionText: '温柔', assetUrl: '', bubbleText: '你已经做得很好了', animationType: 'pulse', status: 1 },
    { id: 205, roleId: 2, emotionStatus: 'encourage', emotionText: '鼓励', assetUrl: '', bubbleText: '相信你自己，你很棒', animationType: 'float', status: 1 },
    { id: 206, roleId: 2, emotionStatus: 'chat', emotionText: '聊天', assetUrl: '', bubbleText: '跟我说说吧', animationType: 'float', status: 1 }
  ],
  3: [
    { id: 301, roleId: 3, emotionStatus: 'normal', emotionText: '平静', assetUrl: '', bubbleText: '今天的目标是什么？', animationType: 'none', status: 1 },
    { id: 302, roleId: 3, emotionStatus: 'happy', emotionText: '开心', assetUrl: '', bubbleText: '目标完成，干得好', animationType: 'none', status: 1 },
    { id: 303, roleId: 3, emotionStatus: 'sad', emotionText: '难过', assetUrl: '', bubbleText: '分析原因，明天改进', animationType: 'none', status: 1 },
    { id: 304, roleId: 3, emotionStatus: 'gentle', emotionText: '温柔', assetUrl: '', bubbleText: '调整计划，循序渐进', animationType: 'none', status: 1 },
    { id: 305, roleId: 3, emotionStatus: 'encourage', emotionText: '鼓励', assetUrl: '', bubbleText: '坚持就是胜利', animationType: 'none', status: 1 },
    { id: 306, roleId: 3, emotionStatus: 'chat', emotionText: '聊天', assetUrl: '', bubbleText: '有什么问题？', animationType: 'none', status: 1 }
  ],
  4: [
    { id: 401, roleId: 4, emotionStatus: 'normal', emotionText: '平静', assetUrl: '', bubbleText: 'Hey! 准备好了吗？', animationType: 'bounce', status: 1 },
    { id: 402, roleId: 4, emotionStatus: 'happy', emotionText: '开心', assetUrl: '', bubbleText: 'YES! 太厉害了！', animationType: 'bounce', status: 1 },
    { id: 403, roleId: 4, emotionStatus: 'sad', emotionText: '难过', assetUrl: '', bubbleText: '别灰心！下次冲！', animationType: 'shake', status: 1 },
    { id: 404, roleId: 4, emotionStatus: 'gentle', emotionText: '温柔', assetUrl: '', bubbleText: '休息一下也好~', animationType: 'pulse', status: 1 },
    { id: 405, roleId: 4, emotionStatus: 'encourage', emotionText: '鼓励', assetUrl: '', bubbleText: 'GO GO GO! 你能行！', animationType: 'bounce', status: 1 },
    { id: 406, roleId: 4, emotionStatus: 'chat', emotionText: '聊天', assetUrl: '', bubbleText: '来聊聊！', animationType: 'bounce', status: 1 }
  ]
}

// 徽章列表
const mockBadges = [
  { id: 1, code: 'first_checkin', name: '初次打卡', description: '完成第一次习惯打卡', icon: '🎯', conditionType: 'checkin_count', conditionValue: 1, status: 1, earnedCount: 48 },
  { id: 2, code: 'streak_7', name: '坚持一周', description: '连续打卡7天', icon: '🔥', conditionType: 'streak_days', conditionValue: 7, status: 1, earnedCount: 32 },
  { id: 3, code: 'streak_30', name: '月度达人', description: '连续打卡30天', icon: '🏆', conditionType: 'streak_days', conditionValue: 30, status: 1, earnedCount: 8 },
  { id: 4, code: 'all_done', name: '全部完成', description: '一天内完成所有习惯', icon: '⭐', conditionType: 'all_done', conditionValue: 1, status: 1, earnedCount: 25 },
  { id: 5, code: 'checkin_100', name: '百次打卡', description: '累计打卡100次', icon: '💎', conditionType: 'checkin_count', conditionValue: 100, status: 1, earnedCount: 5 }
]

// 内容审核 - 聊天记录
const mockChatContents = Array.from({ length: 20 }, (_, i) => ({
  id: 5001 + i,
  userId: 10001 + (i % 10),
  userNickname: mockUsers[i % 10].nickname,
  userAvatar: mockUsers[i % 10].avatar,
  sessionId: 2001 + (i % 5),
  role: i % 2 === 0 ? 'user' : 'assistant',
  content: [
    '今天又完成了早起打卡，感觉棒棒的！',
    '太棒了！你连续打卡12天了，继续保持！',
    '我今天有点不想运动...',
    '没关系，可以从小目标开始，哪怕5分钟也是进步！',
    '阅读30分钟完成了，这本书太好看了',
    '厉害！能推荐一下你在读什么书吗？',
    '冥想真的能让人放松，推荐大家试试',
    '是的，冥想对专注力和情绪管理都有帮助~',
    '今天加班没来得及打卡',
    '辛苦了，明天补上就好，别给自己太大压力'
  ][i % 10],
  emotion: ['positive', 'neutral', 'negative', 'neutral', 'positive', 'neutral', 'positive', 'neutral', 'negative', 'positive'][i % 10],
  reviewStatus: ['pending', 'approved', 'rejected', 'pending', 'approved'][i % 5],
  createdAt: `2026-07-18 ${String(10 + (i % 10)).padStart(2, '0')}:${String((i * 3) % 60).padStart(2, '0')}:00`
}))

// 内容审核 - 打卡图片
const mockCheckinContents = Array.from({ length: 15 }, (_, i) => ({
  id: 6001 + i,
  userId: 10001 + (i % 10),
  userNickname: mockUsers[i % 10].nickname,
  userAvatar: mockUsers[i % 10].avatar,
  habitType: ['morning', 'sport', 'read', 'meditate', 'write'][i % 5],
  habitName: ['早起一杯水', '运动健身', '阅读学习', '冥想静心', '日记复盘'][i % 5],
  content: ['今天喝了500ml温水，精神好多了！', '跑了3公里，大汗淋漓的感觉真爽', '读了20页《原子习惯》，很有启发', '冥想了15分钟，内心非常平静', '今天写了日记，记录了三件感恩的事'][i % 5],
  imageUrl: '', // 实际环境会有图片URL
  hasImage: i % 3 === 0,
  reviewStatus: ['pending', 'approved', 'pending', 'rejected', 'pending'][i % 5],
  checkinTime: `2026-07-18 ${String(7 + (i % 12)).padStart(2, '0')}:${String((i * 5) % 60).padStart(2, '0')}:00`
}))

// 操作日志
const mockLogs = Array.from({ length: 20 }, (_, i) => ({
  id: 8001 + i,
  adminId: 1,
  adminName: '超级管理员',
  action: ['登录', '更新用户状态', '创建模板', '更新AI角色', '审核内容', '删除模板'][i % 6],
  targetType: ['auth', 'user', 'template', 'role', 'content', 'template'][i % 6],
  targetId: 10001 + i,
  detail: ['管理员登录', '禁用用户 习惯达人', '创建模板 冥想静心', '更新角色 小萌 的系统提示词', '审核通过聊天记录', '删除模板 编程练习'][i % 6],
  ip: '127.0.0.1',
  createdAt: `2026-07-18 ${String(8 + (i % 10)).padStart(2, '0')}:${String((i * 3) % 60).padStart(2, '0')}:00`
}))

// ============ 看板统计数据 ============

function getDashboardStats() {
  return {
    overview: {
      totalUsers: 50,
      activeUsers: 38,
      newUsersToday: 5,
      totalCheckins: 1250,
      todayCheckins: 42,
      avgCompletionRate: 72.5,
      totalHabits: 120,
      aiConversations: 380
    },
    userTrend: Array.from({ length: 30 }, (_, i) => ({
      date: `07-${String(i + 1).padStart(2, '0')}`,
      total: 20 + Math.floor(i * 1.2),
      new: Math.floor(Math.random() * 5) + 1
    })),
    checkinTrend: Array.from({ length: 7 }, (_, i) => ({
      date: ['07-12', '07-13', '07-14', '07-15', '07-16', '07-17', '07-18'][i],
      count: Math.floor(Math.random() * 20) + 30,
      rate: Math.floor(Math.random() * 20) + 60
    })),
    habitDistribution: [
      { name: '早起一杯水', value: 35, color: '#4FC3F7' },
      { name: '运动健身', value: 28, color: '#FF6B6B' },
      { name: '阅读学习', value: 22, color: '#FFD93D' },
      { name: '充足饮水', value: 18, color: '#4DD0E1' },
      { name: '早睡早起', value: 15, color: '#7986CB' },
      { name: '冥想静心', value: 12, color: '#BA68C8' },
      { name: '日记复盘', value: 10, color: '#81C784' },
      { name: '编程练习', value: 8, color: '#78909C' }
    ],
    roleDistribution: [
      { name: '小萌(可爱型)', value: 18, color: '#FF9800' },
      { name: '暖阳(温柔型)', value: 15, color: '#FFC107' },
      { name: '严师(严肃型)', value: 10, color: '#607D8B' },
      { name: '闪电(活力型)', value: 7, color: '#E91E63' }
    ],
    recentActivities: mockLogs.slice(0, 8)
  }
}

// ============ Mock 路由处理 ============

function mockResponse(data, delay = MOCK_DELAY) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ code: 200, message: 'ok', data })
    }, delay)
  })
}

function parseParams(url) {
  const query = url.split('?')[1]
  if (!query) return {}
  const params = {}
  query.split('&').forEach(pair => {
    const [key, value] = pair.split('=')
    params[key] = decodeURIComponent(value || '')
  })
  return params
}

function handleMockRequest(config) {
  const url = config.url || ''
  const method = (config.method || 'get').toLowerCase()
  const params = parseParams(url)
  const cleanUrl = url.split('?')[0]
  const body = typeof config.data === 'string' ? JSON.parse(config.data) : (config.data || {})

  // ---- 认证 ----
  if (cleanUrl === '/admin/login' && method === 'post') {
    if (body.username === 'admin' && body.password === 'admin123') {
      return mockResponse({ token: 'mock_admin_token_' + Date.now(), admin: mockAdmin })
    }
    return Promise.resolve({ code: 401, message: '用户名或密码错误', data: null })
  }
  if (cleanUrl === '/admin/info' && method === 'get') {
    return mockResponse(mockAdmin)
  }
  if (cleanUrl === '/admin/logout' && method === 'post') {
    return mockResponse({ success: true })
  }

  // ---- 看板 ----
  if (cleanUrl === '/admin/dashboard/stats' && method === 'get') {
    return mockResponse(getDashboardStats())
  }

  // ---- 用户管理 ----
  if (cleanUrl === '/admin/users' && method === 'get') {
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 10
    const keyword = params.keyword || ''
    const status = params.status || ''
    let filtered = [...mockUsers]
    if (keyword) {
      filtered = filtered.filter(u => u.nickname.includes(keyword) || u.phone.includes(keyword))
    }
    if (status === '1' || status === '0') {
      filtered = filtered.filter(u => u.status === parseInt(status))
    }
    const total = filtered.length
    const list = filtered.slice((page - 1) * pageSize, page * pageSize)
    return mockResponse({ list, total, page, pageSize })
  }
  if (cleanUrl.match(/^\/admin\/users\/\d+$/) && method === 'get') {
    const id = parseInt(cleanUrl.match(/\d+/)[0])
    const user = mockUsers.find(u => u.id === id)
    if (!user) return Promise.resolve({ code: 404, message: '用户不存在', data: null })
    const userDetail = {
      ...user,
      habits: mockTemplates.slice(0, user.habitCount).map((t, i) => ({
        id: 101 + i,
        type: t.type,
        name: t.name,
        icon: t.icon,
        color: t.color,
        target: t.defaultTarget,
        difficulty: t.difficulty,
        streak: Math.floor(Math.random() * 20) + 1,
        completed: Math.random() > 0.3
      })),
      badges: mockBadges.slice(0, Math.floor(Math.random() * 4) + 1).map(b => ({
        ...b,
        unlocked: true,
        unlockedAt: `2026-07-${String(Math.floor(Math.random() * 18) + 1).padStart(2, '0')}`
      })),
      recentCheckins: Array.from({ length: 7 }, (_, i) => ({
        date: `2026-07-${String(12 + i).padStart(2, '0')}`,
        total: 3,
        completed: Math.floor(Math.random() * 4),
        rate: Math.floor(Math.random() * 100)
      }))
    }
    return mockResponse(userDetail)
  }
  if (cleanUrl.match(/^\/admin\/users\/\d+\/status$/) && method === 'put') {
    const id = parseInt(cleanUrl.match(/\/admin\/users\/(\d+)\/status/)[1])
    const user = mockUsers.find(u => u.id === id)
    if (user) {
      user.status = body.status
      user.statusText = body.status === 1 ? '正常' : '禁用'
    }
    return mockResponse({ success: true })
  }

  // ---- AI角色管理 ----
  if (cleanUrl === '/admin/roles' && method === 'get') {
    return mockResponse({ list: mockAiRoles, total: mockAiRoles.length })
  }
  if (cleanUrl === '/admin/roles' && method === 'post') {
    const newRole = { ...body, id: Date.now(), status: 1, sortOrder: mockAiRoles.length + 1, createdAt: new Date().toISOString() }
    mockAiRoles.push(newRole)
    return mockResponse(newRole)
  }
  if (cleanUrl.match(/^\/admin\/roles\/\d+$/) && method === 'put') {
    const id = parseInt(cleanUrl.match(/\d+/)[0])
    const idx = mockAiRoles.findIndex(r => r.id === id)
    if (idx >= 0) {
      mockAiRoles[idx] = { ...mockAiRoles[idx], ...body }
    }
    return mockResponse({ success: true })
  }
  if (cleanUrl.match(/^\/admin\/roles\/\d+$/) && method === 'delete') {
    const id = parseInt(cleanUrl.match(/\d+/)[0])
    const idx = mockAiRoles.findIndex(r => r.id === id)
    if (idx >= 0) mockAiRoles.splice(idx, 1)
    return mockResponse({ success: true })
  }
  if (cleanUrl.match(/^\/admin\/roles\/\d+\/assets$/) && method === 'get') {
    const roleId = parseInt(cleanUrl.match(/\/admin\/roles\/(\d+)\/assets/)[1])
    return mockResponse({ list: mockRoleAssets[roleId] || [], roleId })
  }
  if (cleanUrl.match(/^\/admin\/roles\/\d+\/assets\/\d+$/) && method === 'put') {
    return mockResponse({ success: true })
  }

  // ---- 模板管理 ----
  if (cleanUrl === '/admin/templates' && method === 'get') {
    const status = params.status
    let list = [...mockTemplates]
    if (status === '1' || status === '0') {
      list = list.filter(t => t.status === parseInt(status))
    }
    return mockResponse({ list, total: list.length })
  }
  if (cleanUrl === '/admin/templates' && method === 'post') {
    const newTemplate = { ...body, id: Date.now(), status: 1, sortOrder: mockTemplates.length + 1, createdAt: new Date().toISOString() }
    mockTemplates.push(newTemplate)
    return mockResponse(newTemplate)
  }
  if (cleanUrl.match(/^\/admin\/templates\/\d+$/) && method === 'put') {
    const id = parseInt(cleanUrl.match(/\d+/)[0])
    const idx = mockTemplates.findIndex(t => t.id === id)
    if (idx >= 0) {
      mockTemplates[idx] = { ...mockTemplates[idx], ...body }
    }
    return mockResponse({ success: true })
  }
  if (cleanUrl.match(/^\/admin\/templates\/\d+$/) && method === 'delete') {
    const id = parseInt(cleanUrl.match(/\d+/)[0])
    const idx = mockTemplates.findIndex(t => t.id === id)
    if (idx >= 0) mockTemplates.splice(idx, 1)
    return mockResponse({ success: true })
  }

  // ---- 内容审核 ----
  if (cleanUrl === '/admin/content/chats' && method === 'get') {
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 10
    const status = params.status || ''
    let filtered = [...mockChatContents]
    if (status) {
      filtered = filtered.filter(c => c.reviewStatus === status)
    }
    const total = filtered.length
    const list = filtered.slice((page - 1) * pageSize, page * pageSize)
    return mockResponse({ list, total, page, pageSize })
  }
  if (cleanUrl === '/admin/content/checkins' && method === 'get') {
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 10
    const status = params.status || ''
    let filtered = [...mockCheckinContents]
    if (status) {
      filtered = filtered.filter(c => c.reviewStatus === status)
    }
    const total = filtered.length
    const list = filtered.slice((page - 1) * pageSize, page * pageSize)
    return mockResponse({ list, total, page, pageSize })
  }
  if (cleanUrl.match(/^\/admin\/content\/\d+\/review$/) && method === 'put') {
    const id = parseInt(cleanUrl.match(/\/admin\/content\/(\d+)\/review/)[1])
    const status = body.status // approved or rejected
    let item = mockChatContents.find(c => c.id === id)
    if (!item) item = mockCheckinContents.find(c => c.id === id)
    if (item) item.reviewStatus = status
    return mockResponse({ success: true })
  }

  // ---- 徽章管理 ----
  if (cleanUrl === '/admin/badges' && method === 'get') {
    return mockResponse({ list: mockBadges, total: mockBadges.length })
  }

  // ---- 操作日志 ----
  if (cleanUrl === '/admin/logs' && method === 'get') {
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 20
    const total = mockLogs.length
    const list = mockLogs.slice((page - 1) * pageSize, page * pageSize)
    return mockResponse({ list, total, page, pageSize })
  }

  // 默认: 未匹配的请求
  console.warn('[Mock] 未匹配的请求:', method.toUpperCase(), cleanUrl)
  return Promise.resolve({ code: 404, message: 'Mock: 未匹配的API路径', data: null })
}

// ============ 安装 Mock 拦截器 ============

export function setupMock(axiosInstance) {
  if (!USE_MOCK) return

  axiosInstance.interceptors.request.use(async (config) => {
    // 去除 baseURL 前缀，只保留路径部分
    const fullUrl = config.url || ''
    const basePath = fullUrl.replace(/^\/api\/v1/, '')

    const mockConfig = {
      ...config,
      url: basePath,
      method: config.method || 'get',
      data: config.data
    }

    try {
      const res = await handleMockRequest(mockConfig)
      // 用 adapt 方法将 mock 结果注入到 axios response channel
      config.__mockResult = res
    } catch (e) {
      config.__mockResult = { code: 500, message: String(e), data: null }
    }

    // 返回一个"已取消"的假配置，让 axios 不真正发请求
    // 实际上我们通过 adapter 返回
    return config
  }, (error) => Promise.reject(error))

  // 使用 adapter 拦截
  axiosInstance.defaults.adapter = async (config) => {
    if (config.__mockResult !== undefined) {
      const res = config.__mockResult
      if (res.code !== 200) {
        const error = new Error(res.message || 'Error')
        error.response = { status: res.code === 401 ? 401 : 400, data: res }
        throw error
      }
      return {
        data: res,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
        request: {}
      }
    }
    // 非 mock 请求走默认 adapter
    return undefined
  }
}
