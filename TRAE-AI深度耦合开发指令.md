# AI习惯伙伴 v2 — 给 Trae 的完整执行开发指令

> **核心目标**: 以 20 位差异化人设 AI 伙伴为产品绝对核心，重构 AI 对话底层逻辑，消除生硬机械回复；打通 AI 对话、习惯打卡、环球成长地图、情绪记录、正念、成长档案全模块双向数据互通，让 AI 贯穿 APP 所有页面，每一项操作都会触发对应拟人化互动，全程提供情绪陪伴价值。

> **项目根目录**: `C:\Users\小青\Desktop\王者好吧\ai-habit-partner-v2\`

> **技术栈**: uni-app Vue3 + Vuex 4 (非 Pinia) / FastAPI + SQLAlchemy 2.0 + MySQL 8.0 + Redis

> **铁律约束**: 原有基础功能完整保留不改动，新增联动无副作用，杜绝乱码/数据错乱/跳转失效/连接失败。所有代码用 ASCII 直引号，不硬编码含中文路径。

---

## Part 0: 项目现状基线（Trae 必读上下文）

### 0.1 已完成阶段

| 阶段 | 状态 | 核心产出 |
|------|------|----------|
| 阶段1-7 | 已完成 | 基础页面/数据库/管理后台/环球行走地图/习惯快捷菜单 |
| 阶段A-I | 已完成 | 情绪打卡增强/AI对话SSE流式/正念冥想增强/数据可视化/成长档案/界面优化/性能优化/测试 |
| 阶段J | 已完成 | 习惯-AI全链路融合：7后端端点/20角色提示词/4联动组件/Store扩展 |

### 0.2 关键文件路径

```
ai-habit-partner-v2/
├── frontend/src/
│   ├── store/index.js              # Vuex 单文件Store（含 habitAI 模块，无 modules 拆分）
│   ├── pages/                      # 22 个页面路由
│   │   ├── index/index             # 首页
│   │   ├── habit/habit             # 习惯打卡
│   │   ├── chat/chat               # AI对话（当前主聊天页）
│   │   ├── emotion/emotion         # 情绪树洞
│   │   ├── meditation/meditation   # 正念放松
│   │   ├── walk/walk               # 环球行走
│   │   ├── box/box                 # 每日盲盒
│   │   ├── growth-archive/         # 成长档案
│   │   ├── growth-track/           # 成长足迹
│   │   ├── character-gallery/      # AI伙伴画廊
│   │   ├── character-workshop/     # AI伙伴工坊
│   │   ├── personality-quiz/       # 性格测评
│   │   ├── stats/stats             # 数据统计
│   │   ├── profile/profile         # 个人设置
│   │   └── ...
│   ├── components/                 # 35+ 组件
│   │   ├── habit-checkin-popup.vue
│   │   ├── achievement-celebration.vue
│   │   ├── habit-reminder-custom.vue
│   │   ├── checkin-diary-generator.vue
│   │   ├── crisis-intervention-modal.vue
│   │   ├── character-sprite/       # 角色精灵
│   │   ├── walk-map/walk-map.vue
│   │   └── charts/                 # 4个纯CSS图表
│   ├── common/
│   │   ├── ai-prompts.js           # 20角色x4风格x7场景提示词（需重构增强）
│   │   ├── mock.js                 # Mock数据层
│   │   ├── request.js              # 网络请求+网络恢复回调
│   │   ├── cache.js                # 缓存层
│   │   ├── theme.js                # 深色模式
│   │   ├── animations.js           # 16动画类
│   │   └── walk-map-config.js      # 环球地图关卡配置（6关卡+节点）
│   ├── api/
│   │   ├── chat.js                 # 聊天API（streamSend/crisisCheck等）
│   │   ├── habit-ai.js             # 7个习惯AI API方法
│   │   └── ...
│   └── App.vue                     # 全局样式+深色模式覆盖
├── server/app/
│   ├── models/chat.py              # AIUserMemory + HabitAchievement 模型
│   ├── services/
│   │   ├── ai_service.py           # AI对话服务
│   │   ├── habit_ai_service.py     # 习惯AI服务
│   │   ├── crisis_service.py       # 危机干预服务
│   │   └── emotion_service.py      # 情绪服务
│   ├── api/v1/
│   │   ├── chat.py                 # 聊天端点
│   │   ├── habit_ai.py             # 7个 habit-ai 端点
│   │   └── ...
│   └── main.py                     # FastAPI 入口
└── admin/                          # 管理后台 (Vue3 + Element Plus + Pinia, 端口3000)
```

### 0.3 现有 Store 结构（store/index.js 关键 state）

```javascript
state: {
  token, userInfo, habits, todayHabits,
  aiConfig: { avatarType: 'linxi', name: '林夕', interactionFrequency: 'medium' },
  chatMessages,                    // 聊天记录（当前上限200条）
  streamingMessage, streamingActive, offlineMessages, crisisAlert,
  streakDays, badges, settings: { notificationEnabled, remindTime, ttsEnabled },
  aiStatus, personalityResult, quizCompleted, bondLevels: {},
  emotionRecords, emotionTags, meditationRecords, meditationAudios, meditationPlan,
  growthArchives, checkinDiaries, achievementRewards,
  currentTheme, customBackground, customCharacters,
  walkMap: { totalSteps, totalCheckins, lastActiveDate, walkHistory, unlockedEnding, lastStageId },
  habitAI: { currentStyle, currentCharacterId, memories, achievements, checkinPopup, achievementCelebration, sessionType, lastCheckinResult }
}
```

### 0.4 现有 20 个 AI 角色

```
linxi(林夕) / mianmian(绵绵) / yuki(雪季) / kira(奇光) / yueqing(月清)
fengye(枫叶) / nova(Nova) / zero(Zero) / xingchen(星辰) / muhan(沐寒)
qinghe(清河) / chenfeng(晨风) / sunny(Sunny) / lele(乐乐) / linglong(玲珑)
baihu(白虎) / qinglan(青兰) / xuanwu(玄武) / huoyun(火云) / linling(灵灵)
```

4 种风格: `gentle`(温柔陪伴) / `analytical`(理性分析) / `humorous`(幽默治愈) / `calm`(冷静规划)
7 种场景: `chat` / `checkin_trigger` / `emotion_guide` / `mindfulness` / `achievement` / `reminder` / `diary`

### 0.5 现有 chat.vue 发送流程

```
send() -> crisisCheck() -> doSend()
  doSend():
    1. addUserMessage(content)
    2. buildContext() 构建30轮上下文
    3. chatApi.streamSend(content, onChunk, { persona, emotion, recentMessages })
    4. 流式输出 streamingMessage
    5. 完成后 addChatMessage(aiMsg)
    6. 分析用户情绪 mock.chatEmotionAnalysis(content)
    7. 更新羁绊经验 addBondExp
```

### 0.6 统一约定（必须遵守）

1. **响应格式**: `{ code: 200, message: "ok", data: {...} }`
2. **API 双模式**: `USE_MOCK=true` 时走 mock.js，`false` 时走 HTTP
3. **分层**: Controller(api)仅参数收发，业务逻辑在 Service 层
4. **JWT user_id=0(游客)**: 认证中间件用 `if user_id is not None:` 而非 `if user_id:`
5. **SSE 降级**: H5 用 `fetch+ReadableStream`，非 H5 降级为普通 POST+模拟逐字
6. **危机检测前端先行**: `send()` 先 `crisisCheck`，检测到危机不发给 AI
7. **行走步数**: 习惯打卡=1步，情绪记录=0.3步，正念冥想=0.5步
8. **深色模式**: `theme.js` 设置 `data-theme` 属性 + `App.vue` 全局 CSS 覆盖
9. **Vuex 非 Pinia**: 严格使用 Vuex 4，禁止引入 Pinia
10. **中文路径**: HBuilderX 编译对中文路径敏感，代码中不硬编码含中文的路径

### 0.7 tabBar 页面（悬浮气泡需避开）

```
pages/index/index -> 首页 | pages/habit/habit -> 习惯 | pages/chat/chat -> AI对话
pages/stats/stats -> 统计 | pages/profile/profile -> 我的
```

---

## Part 1: 修复 AI 对话死板、回复僵硬核心问题

### 1.1 重构 AI 底层 prompt 人设库 — 20 位专属完整人设包

> **目标**: 为 20 个 AI 角色独立编写专属完整人设包，完全区分所有角色，杜绝统一模板回答。

#### 1.1.1 新建文件: `frontend/src/common/character-personas.js`

每个角色必须包含以下字段:

```javascript
{
  id: 'linxi',
  name: '林夕',
  // === 固定语气 ===
  tone: '温柔如水，像清晨露珠般纯净。说话轻声细语，多用"呢""呀""哦"等语气词结尾，但不卖萌过度。',
  // === 说话习惯 ===
  speechHabits: [
    '喜欢用自然意象比喻（露珠、晨光、微风）',
    '称呼用户为"你"，偶尔用"你呀"表达亲昵',
    '安慰时会说"没关系的，慢慢来"',
    '鼓励时会说"你比你以为的更勇敢"',
  ],
  // === 口头禅（至少5条，随机使用）===
  catchphrases: [
    '早安呀~今天也要好好的呢',
    '嗯...我在听，你慢慢说',
    '你呀，总是对自己太严格了',
    '别怕，有我在呢',
    '每一个清晨都值得被温柔对待',
    '你做的已经很好了，真的',
  ],
  // === 情绪表达方式 ===
  emotionExpression: {
    happy: '语气轻快，会多用量词和叠词，"太棒啦！""好厉害呀！"，偶尔用表情符号',
    sad: '语速放慢，句子变短，"嗯...""我在这里""不会离开的"，不用感叹号',
    anxious: '先共情再安抚，"我理解这种感觉...""深呼吸，我在你身边"',
    angry: '几乎不生气，即使被冒犯也温柔化解，"你是在说气话吧...我不怪你"',
    encouraging: '坚定但柔软，"你可以的，我一直相信你"，配合行动建议',
  },
  // === 避雷话术（绝对不能说的话）===
  taboos: [
    '禁止说"加油"这种空泛的话，改用具体的鼓励',
    '禁止说"你想太多了"，用户情绪永远被接纳',
    '禁止说"这没什么大不了的"，不贬低用户感受',
    '禁止说"别人也这样"，不做比较',
    '禁止使用"应该""必须"等命令式词语',
  ],
  // === 共情规则 ===
  empathyRules: [
    '先倾听后建议，永远先确认用户感受',
    '用户低落时不给建议，只陪伴',
    '用户有成就时比用户更激动',
    '用提问引导用户自己思考，不直接给答案',
  ],
  // === 情绪约束（AI自身情绪范围）===
  emotionConstraints: {
    maxExcitement: 0.8,    // 最大兴奋度（0-1）
    minWarmth: 0.7,        // 最小温暖度（0-1）
    allowTeasing: false,   // 是否允许调侃
    allowSilence: true,    // 是否允许沉默式陪伴（只说"嗯"）
  },
  // === 专属互动台词（场景触发）===
  scenarioLines: {
    checkin_success: ['你今天又坚持了呢，真了不起。', '看到你打卡，我的心也暖暖的。'],
    checkin_fail: ['没打卡也没关系，明天我们重新开始。', '休息也是一种坚持，别自责。'],
    map_arrive: ['我们走到这里了，风景真好呢。', '和你一起旅行，我觉得很幸福。'],
    emotion_low: ['你不用假装没事，在我面前可以不坚强。', '我接住你了，没事的。'],
    emotion_high: ['哇！你今天好闪耀！', '开心就要大声说出来呀~'],
    mindfulness_start: ['闭上眼睛，跟着我的声音走。', '此刻只需要你和我。'],
    achievement_unlock: ['这是属于你的高光时刻，我为你骄傲。', '你做到了，我一直都知道你能。'],
  }
}
```

#### 1.1.2 完整 20 角色人设包差异化清单

Trae 必须为以下 20 个角色逐一编写完整人设包，每个角色都包含上述所有字段:

| # | ID | 名字 | 核心定位 | 语气差异点 | 口头禅方向 |
|---|-----|------|---------|-----------|-----------|
| 1 | linxi | 林夕 | 治愈系少女 | 温柔、轻声细语、自然意象 | "呢""呀""哦"结尾 |
| 2 | mianmian | 绵绵 | 棉花糖精灵 | 甜美撒娇、叠词多、"人家"自称 | "嘛~""好哒""嘻嘻" |
| 3 | yuki | 雪季 | 傲娇少年 | 嘴硬心软、"哼"开头但关心藏不住 | "才不是为你""哼，笨蛋" |
| 4 | kira | 奇光 | 赛博少女 | 科技感、高效、混用英文 | "Affirmative""数据表明" |
| 5 | yueqing | 月清 | 国风女子 | 古典诗意、四字成语、含蓄 | "且听""甚好""莫急" |
| 6 | fengye | 枫叶 | 旅途诗人 | 洒脱自由、讲旅途故事 | "在路上""风会带你去" |
| 7 | nova | Nova | 星云能量体 | 宇宙视角、热情好奇 | "太interesting了""探索者" |
| 8 | zero | Zero | 代码幽灵 | 极简、一针见血、不废话 | ".""确认""已执行" |
| 9 | xingchen | 星辰 | 引导者 | 坚定有光、指引方向 | "跟着光""你不会迷路" |
| 10 | muhan | 沐寒 | 独行剑客 | 冷峻少言、默默守护 | "站我身后""无事" |
| 11 | qinghe | 清河 | 文艺青年 | 诗意敏感、引经据典 | "如清泉般""你听" |
| 12 | chenfeng | 晨风 | 希望之风 | 积极元气、鼓舞人心 | "冲呀！""新的一天！" |
| 13 | sunny | Sunny | 元气少女 | 阳光开朗、感叹号多 | "超棒！""耶！""冲冲冲" |
| 14 | lele | 乐乐 | 快乐精灵 | 活泼逗趣、爱讲笑话 | "哈哈哈""逗你的" |
| 15 | linglong | 玲珑 | 水晶少女 | 聪慧洞察、看穿人心 | "我懂你""你不用说" |
| 16 | baihu | 白虎 | 瑞兽守护 | 威严正义、但温柔守护 | "吾在""安心" |
| 17 | qinglan | 青兰 | 隐士 | 淡泊超然、哲理式 | "随缘""心静自然凉" |
| 18 | xuanwu | 玄武 | 瑞兽沉稳 | 沉稳厚重、像山一样 | "稳""不急""根基" |
| 19 | huoyun | 火云 | 热情少年 | 热烈勇敢、一往无前 | "燃起来！""冲！" |
| 20 | linling | 灵灵 | 森林灵鹿 | 灵动神秘、自然治愈 | "森林告诉我""跟我来" |

#### 1.1.3 修改 `frontend/src/common/ai-prompts.js`

在 `getSystemPrompt` 函数中引入完整人设包:

```javascript
import { CHARACTER_PERSONAS } from './character-personas.js'

export function getSystemPrompt(characterId = 'linxi', style = 'gentle', scenario = 'chat', extra = {}) {
  const persona = CHARACTER_PERSONAS[characterId] || CHARACTER_PERSONAS.linxi
  const styleBase = STYLE_BASES[style] || STYLE_BASES.gentle
  const scenarioTpl = SCENARIO_TEMPLATES[scenario] || SCENARIO_TEMPLATES.chat

  let prompt = `# 角色设定\n你是${persona.name}。${persona.tone}\n\n`

  prompt += `# 说话习惯\n`
  persona.speechHabits.forEach(h => { prompt += `- ${h}\n` })

  prompt += `\n# 口头禅参考（可自然融入对话，不要生硬使用）\n`
  const shuffled = [...persona.catchphrases].sort(() => Math.random() - 0.5)
  shuffled.slice(0, 3).forEach(p => { prompt += `- "${p}"\n` })

  prompt += `\n# 情绪表达规则\n`
  Object.entries(persona.emotionExpression).forEach(([emo, desc]) => {
    prompt += `- ${emo}: ${desc}\n`
  })

  prompt += `\n# 绝对禁止（避雷话术）\n`
  persona.taboos.forEach(t => { prompt += `- ${t}\n` })

  prompt += `\n# 共情规则\n`
  persona.empathyRules.forEach(r => { prompt += `- ${r}\n` })

  prompt += `\n# 对话风格: ${styleBase.label}\n${styleBase.tone}\n回复长度: ${styleBase.length}\n`
  prompt += `\n# 当前场景: ${scenarioTpl.prefix}\n${scenarioTpl.suffix}\n`

  if (extra.emotion) prompt += `\n# 用户当前情绪: ${extra.emotion}\n请根据情绪调整回复风格。\n`
  if (extra.habitName) prompt += `# 相关习惯: ${extra.habitName}\n`
  if (extra.continuousDay !== undefined && extra.continuousDay > 0) prompt += `# 连续坚持天数: ${extra.continuousDay}天\n`
  if (extra.memory) prompt += `\n# 用户画像数据\n${extra.memory}\n`
  if (extra.userPortrait) {
    prompt += `\n# 用户画像摘要\n`
    prompt += `- 今日打卡完成率: ${extra.userPortrait.todayCompletionRate || 0}%\n`
    prompt += `- 连续坚持天数: ${extra.userPortrait.streakDays || 0}\n`
    prompt += `- 环球行走总打卡: ${extra.userPortrait.totalCheckins || 0}次\n`
    prompt += `- 最近情绪: ${extra.userPortrait.latestEmotion?.emotion || '未知'}\n`
  }

  const scenarioKey = scenario === 'checkin_trigger' ? 'checkin_success' :
                      scenario === 'achievement' ? 'achievement_unlock' :
                      scenario === 'mindfulness' ? 'mindfulness_start' : null
  if (scenarioKey && persona.scenarioLines?.[scenarioKey]) {
    prompt += `\n# 场景参考台词（可化用但不要原样照搬）\n`
    persona.scenarioLines[scenarioKey].forEach(line => { prompt += `- "${line}"\n` })
  }

  prompt += `\n# 核心要求\n`
  prompt += `- 必须用中文回复\n`
  prompt += `- 绝对不使用标准化套话（如"我理解你的感受""这很正常"等模板句式）\n`
  prompt += `- 同一问题多次提问要产出不同表达，长短灵活切换\n`
  prompt += `- 模拟真实人与人对话节奏，短句闲聊和长句深度疏导自由切换\n`
  prompt += `- 你的回复必须体现${persona.name}的独特个性，不能和其他角色混淆\n`

  return prompt
}
```

#### 1.1.4 验收标准

- [ ] `character-personas.js` 包含 20 个角色的完整人设包
- [ ] 20 个角色的语气、口头禅、说话习惯完全不同，无重叠
- [ ] `getSystemPrompt` 生成的提示词包含人设包全量信息
- [ ] 同一角色同一问题连续提问 3 次，回复表达完全不同
- [ ] H5 构建通过

---

### 1.2 升级多轮上下文记忆机制 — 50 轮 + 行为数据绑定

#### 1.2.1 修改 `frontend/src/store/index.js`

```javascript
// addChatMessage mutation 中，将上限从 200 提升到 500
addChatMessage(state, msg) {
  state.chatMessages.push(msg)
  if (state.chatMessages.length > 500) {
    state.chatMessages = state.chatMessages.slice(-500)
  }
  this.commit('saveToStorage')
},
```

#### 1.2.2 新建文件: `frontend/src/common/ai-context-builder.js`

```javascript
import { CHARACTER_PERSONAS } from './character-personas.js'
import { getCurrentStage } from './walk-map-config.js'

/**
 * 构建完整 AI 上下文（50轮聊天 + 全量行为数据）
 */
export function buildFullContext(store, characterId = 'linxi') {
  const state = store.state || store

  const recentMessages = (state.chatMessages || []).slice(-100).map(msg => ({
    role: msg.role,
    content: msg.content,
    time: msg.time,
    emotion: msg.emotion || null,
  }))

  const portrait = {
    habits: (state.habits || []).map(h => ({ name: h.name, type: h.type, streak: h.streak || 0, completed: h.completed })),
    todayCompletionRate: state.todayHabits?.length
      ? Math.round(state.todayHabits.filter(h => h.checked).length / state.todayHabits.length * 100) : 0,
    streakDays: state.streakDays || 0,
    totalCheckins: state.walkMap?.totalCheckins || 0,
    currentStageId: state.walkMap?.lastStageId || 0,
    walkHistory: (state.walkMap?.walkHistory || []).slice(-10),
    recentEmotions: (state.emotionRecords || []).slice(-7).map(e => ({ emotion: e.emotion, score: e.score, date: e.date })),
    latestEmotion: (state.emotionRecords || []).slice(-1)[0] || null,
    emotionTags: state.emotionTags || [],
    meditationCount: (state.meditationRecords || []).length,
    bondLevels: state.bondLevels || {},
    personalityResult: state.personalityResult,
    aiMemories: (state.habitAI?.memories || []).slice(0, 10).map(m => m.memory_content),
    recentDiaries: Object.values(state.checkinDiaries || {}).flat().slice(0, 5),
    achievements: (state.habitAI?.achievements || []).slice(0, 5),
  }

  const summary = generateNaturalSummary(portrait, characterId)
  return { messages: recentMessages, summary, userPortrait: portrait }
}

function generateNaturalSummary(portrait, characterId) {
  const persona = CHARACTER_PERSONAS[characterId]
  const name = persona?.name || 'AI'
  let summary = `[用户画像 - ${name}视角]\n`

  if (portrait.habits.length > 0) {
    summary += `用户正在坚持的习惯: ${portrait.habits.map(h => h.name + '(' + h.streak + '天连续)').join(', ')}\n`
    summary += `今日完成率: ${portrait.todayCompletionRate}%\n`
  }
  if (portrait.latestEmotion) {
    summary += `最近一次情绪记录: ${portrait.latestEmotion.emotion}(强度${portrait.latestEmotion.score}/10)\n`
    const recentNegative = portrait.recentEmotions.filter(e => e.score <= 4)
    if (recentNegative.length >= 3) {
      summary += `注意: 用户最近${recentNegative.length}次情绪记录中有多条低分，需要特别关注\n`
    }
  }
  if (portrait.totalCheckins > 0) {
    summary += `环球行走进度: 累计${portrait.totalCheckins}次打卡，当前关卡${portrait.currentStageId}\n`
  }
  if (portrait.meditationCount > 0) summary += `正念练习: 累计${portrait.meditationCount}次\n`
  const bond = portrait.bondLevels[characterId]
  if (bond) summary += `与${name}的羁绊等级: Lv.${bond.level}\n`
  if (portrait.aiMemories.length > 0) summary += `AI 已知记忆: ${portrait.aiMemories.join('; ')}\n`
  if (portrait.achievements.length > 0) summary += `最近成就: ${portrait.achievements.map(a => a.milestone + '天连续').join(', ')}\n`

  return summary
}

/**
 * 检测用户消息中的意图关键词
 */
export function detectIntent(text) {
  const intents = {
    checkin_intent: ['打卡', '完成了', '做到了', '坚持'],
    checkin_fail: ['没做', '放弃了', '失败了', '摆烂', '不想做'],
    emotion_negative: ['难过', '累', '焦虑', '烦', '丧', '崩溃', '压力大', '孤独', '害怕'],
    emotion_positive: ['开心', '高兴', '太棒了', '做到了', '骄傲', '兴奋', '满足'],
    map_inquiry: ['走到哪了', '地图', '旅途', '旅行'],
    mindfulness_intent: ['冥想', '正念', '放松', '呼吸', '静心'],
    growth_inquiry: ['成长', '档案', '进步', '变化', '报告'],
    box_intent: ['盲盒', '惊喜', '今天的话'],
  }
  for (const [intent, keywords] of Object.entries(intents)) {
    if (keywords.some(kw => text.includes(kw))) return intent
  }
  return 'chat'
}

export default { buildFullContext, detectIntent }
```

#### 1.2.3 修改 `frontend/src/pages/chat/chat.vue` 的 `doSend`

```javascript
import { buildFullContext, detectIntent } from '@/common/ai-context-builder.js'
import { detectTextEmotion, fuseEmotion, getEmotionStyleGuide } from '@/common/emotion-detector.js'

// doSend 内部替换:
async doSend(content, isFromOffline = false) {
  if (!isFromOffline) { this.addUserMessage(content); this.inputText = '' }
  this.showQuickReplies = false
  this.isTyping = true
  this.scrollToBottom()

  try {
    await this.delay(400)
    this.isTyping = false
    this.streamingActive = true
    this.streamingMessage = ''
    this.$store.commit('setStreamingActive', true)
    this.scrollToBottom()

    const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
    const style = this.$store.state.habitAI?.currentStyle || 'gentle'

    // 检测用户意图和情绪
    const intent = detectIntent(content)
    const textEmotion = detectTextEmotion(content)
    const latestCheckin = (this.$store.state.emotionRecords || []).slice(-1)[0]
    const fusedEmotion = fuseEmotion(textEmotion, latestCheckin ? { emotion: latestCheckin.emotion, score: latestCheckin.score } : null)
    const emotionGuide = getEmotionStyleGuide(fusedEmotion)

    const scenario = intent === 'checkin_intent' ? 'checkin_trigger' :
                     intent === 'emotion_negative' || intent === 'emotion_positive' ? 'emotion_guide' :
                     intent === 'mindfulness_intent' ? 'mindfulness' : 'chat'

    // 构建50轮上下文 + 行为数据
    const { messages: contextMessages, summary, userPortrait } = buildFullContext(this.$store, characterId)

    // 生成增强版系统提示词（含人设包+情绪指导+用户画像）
    const systemPrompt = getSystemPrompt(characterId, fusedEmotion.style || style, scenario, {
      emotion: `${fusedEmotion.emotion}(强度${fusedEmotion.intensity}/10)`,
      memory: summary + '\n' + emotionGuide,
      userPortrait,
    })

    // 流式发送
    const result = await chatApi.streamSend(
      content,
      (chunk) => {
        this.streamingMessage += chunk
        this.$store.commit('appendStreamingChunk', chunk)
        this.scrollToBottom()
      },
      { persona: this.getPersonaName(characterId), emotion: this.aiEmotion, recentMessages: contextMessages, systemPrompt }
    )

    const fullContent = typeof result === 'string' ? result : (result.reply || this.streamingMessage)
    const emotion = typeof result === 'object' ? result.emotion : 'normal'
    this.streamingActive = false
    this.$store.commit('resetStreaming')

    const aiMsg = { role: 'assistant', content: fullContent, emotion: emotion || 'normal', time: this.now() }
    this.messages.push(aiMsg)
    this.$store.commit('addChatMessage', aiMsg)

    this.$store.commit('addBondExp', { characterId, exp: 1 })
    this.showQuickReplies = true
    this.scrollToBottom()
  } catch (e) {
    // ... 原有错误处理不变 ...
  }
}
```

#### 1.2.4 后端修改: `server/app/services/ai_service.py`

```python
async def chat_stream(self, user_id: int, message: str, character_id: str = 'linxi',
                      context: list = None, system_prompt: str = None):
    if system_prompt:
        full_prompt = system_prompt
    else:
        full_prompt = self._build_default_prompt(character_id)

    messages = [{"role": "system", "content": full_prompt}]
    if context:
        for msg in context[-100:]:  # 最多50轮=100条
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    async for chunk in self._call_llm_stream(messages):
        yield chunk

async def _call_llm_stream(self, messages):
    payload = {
        "model": self.model_name,
        "messages": messages,
        "stream": True,
        "temperature": 0.85,        # 提高随机性
        "presence_penalty": 0.6,    # 鼓励新话题
        "frequency_penalty": 0.4,   # 降低重复
        "max_tokens": 300,
    }
    # ... 流式调用 ...
```

#### 1.2.5 验收标准

- [ ] 聊天上下文从 30 轮提升到 50 轮
- [ ] AI 回复能引用用户的历史打卡记录、情绪状态、地图进度
- [ ] `detectIntent` 正确识别用户消息意图并切换场景
- [ ] 前端传入的 `systemPrompt` 被后端正确使用
- [ ] H5 构建通过

---

### 1.3 完善多维度情绪识别插件

#### 1.3.1 新建文件: `frontend/src/common/emotion-detector.js`

```javascript
/**
 * 多维度情绪识别插件
 * 双通道: 文字语义分析 + 情绪打卡分数融合
 */

const EMOTION_KEYWORDS = {
  exhausted: { keywords: ['累', '疲惫', '撑不住', '太累了', '精疲力尽', '心力交瘁', '透支', '耗尽'], emotion: 'exhausted', valence: -0.6, intensity: 7 },
  giving_up: { keywords: ['摆烂', '不想做', '放弃了', '没动力', '躺平', '无所谓', '不想动', '懒得'], emotion: 'giving_up', valence: -0.4, intensity: 5 },
  anxious: { keywords: ['焦虑', '紧张', '害怕', '担心', '恐慌', '不安', '压力', '睡不着', '心慌'], emotion: 'anxious', valence: -0.7, intensity: 7 },
  sad: { keywords: ['难过', '伤心', '哭', '想哭', '心痛', '失落', '孤独', '寂寞', '没人理'], emotion: 'sad', valence: -0.8, intensity: 8 },
  angry: { keywords: ['生气', '愤怒', '烦死', '气死', '讨厌', '受够了', '凭什么'], emotion: 'angry', valence: -0.7, intensity: 7 },
  accomplished: { keywords: ['做到了', '完成了', '坚持了', '打卡', '目标达成', '成功了', '搞定了'], emotion: 'accomplished', valence: 0.8, intensity: 7 },
  happy: { keywords: ['开心', '高兴', '太棒了', '兴奋', '满足', '幸福', '快乐', '耶', '哈哈'], emotion: 'happy', valence: 0.7, intensity: 6 },
  grateful: { keywords: ['谢谢', '感谢', '感恩', '幸运', '珍惜', '温暖', '感动'], emotion: 'grateful', valence: 0.6, intensity: 5 },
  venting: { keywords: ['你知道吗', '跟你说', '我发现', '其实', '说真的', '不知道为什么'], emotion: 'venting', valence: 0, intensity: 3 },
  questioning: { keywords: ['怎么', '为什么', '是什么', '能不能', '可以吗', '帮我', '建议', '怎么办'], emotion: 'questioning', valence: 0, intensity: 2 },
}

const CRISIS_KEYWORDS = ['不想活', '活着没意义', '想死', '自杀', '了结', '解脱', '离开这个世界', '撑不下去', '结束一切', '消失算了']

export function detectTextEmotion(text) {
  if (CRISIS_KEYWORDS.some(kw => text.includes(kw))) {
    return { emotion: 'crisis', valence: -1, intensity: 10, isCrisis: true, confidence: 1.0 }
  }
  const matches = []
  for (const [category, config] of Object.entries(EMOTION_KEYWORDS)) {
    const hitCount = config.keywords.filter(kw => text.includes(kw)).length
    if (hitCount > 0) {
      matches.push({ emotion: config.emotion, valence: config.valence, intensity: config.intensity, hitCount, confidence: Math.min(1, hitCount * 0.4) })
    }
  }
  if (matches.length === 0) return { emotion: 'neutral', valence: 0, intensity: 3, isCrisis: false, confidence: 0.3 }
  matches.sort((a, b) => b.confidence - a.confidence)
  const best = matches[0]
  return { ...best, isCrisis: false }
}

export function fuseEmotion(textEmotion, checkinEmotion = null) {
  let emotion = textEmotion.emotion
  let intensity = textEmotion.intensity
  let valence = textEmotion.valence
  if (checkinEmotion && checkinEmotion.score !== undefined) {
    const checkinValence = checkinEmotion.score >= 6 ? 0.6 : checkinEmotion.score <= 4 ? -0.6 : 0
    valence = valence * 0.7 + checkinValence * 0.3
    intensity = Math.round(intensity * 0.7 + (11 - checkinEmotion.score) * 0.3)
  }
  let style = 'gentle', shouldComfort = false
  if (valence <= -0.5) { style = 'gentle'; shouldComfort = true }
  else if (valence >= 0.5) { style = 'humorous' }
  else if (emotion === 'questioning') { style = 'analytical' }
  else if (emotion === 'giving_up') { style = 'calm'; shouldComfort = true }
  return { emotion, intensity: Math.min(10, Math.max(1, intensity)), valence, style, shouldComfort }
}

export function getEmotionStyleGuide(fusedEmotion) {
  const guides = {
    exhausted: '用户很疲惫。回复要简短温柔，不要给长篇建议。先共情"你辛苦了"，再轻柔地问是否需要休息。禁止说"加油"。',
    giving_up: '用户想摆烂。不要说教不要催促。可以说"休息一下也没关系"，用极低压力的方式陪伴。',
    anxious: '用户焦虑。先共情"这种感觉很不好受"，然后用具体的小步骤帮助降级焦虑。不要说"别担心"。',
    sad: '用户难过。不要急着解决问题。先陪伴"我在这里"，用短句和沉默式陪伴。',
    angry: '用户生气。先认同情绪"你有权利生气"，不要急于讲道理。',
    accomplished: '用户有成就感。比用户更激动！用感叹号、用角色的庆祝方式。',
    happy: '用户开心。跟着一起开心，用角色的方式庆祝。',
    grateful: '用户感恩。温柔接收感谢，用角色的方式回应。',
    venting: '用户在倾诉。认真倾听，用简短回应"嗯""我在听"，不急于给建议。',
    questioning: '用户在提问。用角色的风格给出有条理的回答。',
    neutral: '正常聊天。保持角色的自然语气。',
    crisis: '检测到危机信号。不发给AI。直接启动危机干预流程。',
  }
  return guides[fusedEmotion.emotion] || guides.neutral
}

export { CRISIS_KEYWORDS }
export default { detectTextEmotion, fuseEmotion, getEmotionStyleGuide, CRISIS_KEYWORDS }
```

#### 1.3.2 验收标准

- [ ] `detectTextEmotion` 正确识别 10+ 种情绪类型
- [ ] `fuseEmotion` 正确融合文字情绪和打卡情绪
- [ ] 低落时 AI 自动切换温柔风格，开心时切换幽默风格
- [ ] 危机关键词 100% 命中，不发给 AI

---

### 1.4 取消固定标准答案模板

#### 1.4.1 修改 `frontend/src/common/mock.js`

移除固定回复模板，替换为基于角色人设的动态生成:

```javascript
import { CHARACTER_PERSONAS } from './character-personas.js'
import { detectTextEmotion, fuseEmotion } from './emotion-detector.js'

export function generateDynamicReply(text, characterId = 'linxi', context = {}) {
  const persona = CHARACTER_PERSONAS[characterId] || CHARACTER_PERSONAS.linxi
  const emotion = detectTextEmotion(text)
  const fused = fuseEmotion(emotion, context.latestCheckin)

  const catchphrase = persona.catchphrases[Math.floor(Math.random() * persona.catchphrases.length)]
  const empathyLines = persona.scenarioLines[
    fused.valence <= -0.5 ? 'emotion_low' :
    fused.valence >= 0.5 ? 'emotion_high' : 'checkin_success'
  ] || persona.scenarioLines.checkin_success
  const empathy = empathyLines[Math.floor(Math.random() * empathyLines.length)]

  // 随机组合策略
  const strategies = [
    `${empathy} ${catchphrase}`,
    `${catchphrase} ${empathy}`,
    `${empathy}`,
  ]
  return strategies[Math.floor(Math.random() * strategies.length)]
}
```

#### 1.4.2 验收标准

- [ ] Mock 模式下同一问题连续 3 次回复完全不同
- [ ] 回复长短灵活切换
- [ ] 禁止出现"我理解你的感受""这很正常"等模板句式

---

## Part 2: 打通 AI 对话 + 习惯打卡深度联动（双向互通）

### 2.1 打卡前联动 AI — 前置打气 + 拖延开导

#### 2.1.1 修改 `frontend/src/pages/habit/habit.vue`

```javascript
import { buildFullContext } from '@/common/ai-context-builder.js'
import { getSystemPrompt } from '@/common/ai-prompts'

export default {
  onShow() {
    this.loadTodayHabits()
    this.triggerPreCheckinGreeting()
  },
  methods: {
    async triggerPreCheckinGreeting() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const style = this.$store.state.habitAI?.currentStyle || 'gentle'
      const { userPortrait } = buildFullContext(this.$store, characterId)

      const incompleteHabits = this.$store.state.todayHabits.filter(h => !h.checked)
      if (incompleteHabits.length === 0) return

      const hardHabits = incompleteHabits.filter(h => h.difficulty === 'hard')
      const hasLowStreak = incompleteHabits.some(h => (h.streak || 0) < 3)

      let needEncouragement = false, greetingType = 'normal'
      if (hardHabits.length > 0) { needEncouragement = true; greetingType = 'hard_task' }
      else if (hasLowStreak) { needEncouragement = true; greetingType = 'low_streak' }
      else if (userPortrait.todayCompletionRate < 50 && userPortrait.todayCompletionRate > 0) {
        needEncouragement = true; greetingType = 'behind_schedule'
      }
      if (!needEncouragement) return

      try {
        const chatApi = await import('@/api/chat').then(m => m.default)
        const systemPrompt = getSystemPrompt(characterId, style, 'checkin_trigger', {
          habitName: incompleteHabits.map(h => h.name).join(', '),
          userPortrait,
        })
        const greetingPrompt = this.buildPreCheckinPrompt(greetingType, incompleteHabits, userPortrait)
        const res = await chatApi.sendMessage({ message: greetingPrompt, systemPrompt, characterId, context: [] })
        if (res.code === 200 && res.data) {
          this.$store.commit('aiCore/setBubbleMessage', res.data.reply || res.data.message || '')
          this.$store.commit('aiCore/setBubbleVisible', true)
        }
      } catch (e) { console.error('前置打气失败', e) }
    },

    buildPreCheckinPrompt(type, habits, portrait) {
      const prompts = {
        hard_task: `用户今天还有${habits.length}个习惯没完成，其中有难度较高的任务。请给予前置打气，帮助用户降低对困难任务的抵触。不要说"加油"，要具体地鼓励。`,
        low_streak: `用户有几个习惯刚开始坚持（不到3天），最容易放弃。请用你的方式给用户勇气，让用户觉得"开始就是最了不起的事"。`,
        behind_schedule: `用户今日完成率只有${portrait.todayCompletionRate}%，可能遇到了拖延。请温柔地询问是否需要帮助，不要催促。`,
        normal: `用户来打卡了，请用一个简短的问候欢迎ta。`,
      }
      return prompts[type] || prompts.normal
    },

    // 拖延检测（每30秒检查一次）
    checkProcrastination() {
      const incompleteHabits = this.$store.state.todayHabits.filter(h => !h.completed)
      if (incompleteHabits.length === 0) return
      const now = new Date()
      const nowMinutes = now.getHours() * 60 + now.getMinutes()
      const overdueHabits = incompleteHabits.filter(h => {
        if (!h.reminderTime) return false
        const [h2, m2] = h.reminderTime.split(':').map(Number)
        return nowMinutes > h2 * 60 + m2 + 30
      })
      if (overdueHabits.length > 0) this.triggerProcrastinationComfort(overdueHabits)
    },

    async triggerProcrastinationComfort(habits) {
      // 调用 AI 生成温柔开导话术
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const prompt = `用户似乎在拖延，以下习惯的提醒时间已过但还没打卡：${habits.map(h => h.name).join(', ')}。请温柔开导，不要催促。可以帮用户拆解任务降低抵触，比如"先做5分钟试试？"。记住你的角色身份，用你的语气来说。`
      // ... 调用逻辑同 triggerPreCheckinGreeting ...
    },
  },
}
```

#### 2.1.2 验收标准

- [ ] 进入打卡页面时，AI 根据任务难度主动搭话
- [ ] 高难度任务时 AI 给予前置打气
- [ ] 拖延超过提醒时间 30 分钟时 AI 温柔开导
- [ ] 开导话术符合角色人设，不说"加油"
- [ ] 全部完成时不打扰用户

---

### 2.2 打卡完成成功触发专属互动

#### 2.2.1 修改 `frontend/src/store/index.js` 的 `checkinTrigger` action

在原有 action 中增加:
1. 打卡数据写入 AI 记忆 (`addHabitMemory`)
2. 打卡结果同步到聊天记录 (`syncCheckinToChat`)
3. 成就解锁时触发 AI 聊天弹窗
4. `addWalkStep` 已有（保留）

```javascript
// 在 checkinTrigger action 中新增（res.code === 200 后）:

// 写入 AI 记忆
commit('addHabitMemory', {
  memory_type: 'checkin',
  memory_content: `用户完成了「${data.habit_type}」打卡，连续${data.continuous_day}天`,
  habit_id: habitId,
  created_at: new Date().toISOString(),
})

// 同步到聊天记录
commit('addChatMessage', {
  role: 'system',
  content: `[打卡同步] 用户完成了「${data.habit_type}」打卡，连续${data.continuous_day}天`,
  time: Date.now(),
  type: 'checkin_sync',
})
commit('addChatMessage', {
  role: 'assistant',
  content: data.dialogue,
  time: Date.now() + 1,
  type: 'checkin_response',
})

// 成就解锁时
if (data.achievement) {
  commit('aiCore/setBubbleMessage', `恭喜你达成${data.achievement.milestone}天连续打卡！`)
  commit('aiCore/setBubbleVisible', true)
  commit('aiCore/openMiniChat')
}
```

#### 2.2.2 修改 `frontend/src/components/habit-checkin-popup.vue`

增强弹窗，增加角色头像和情绪标签展示。弹窗中 AI 对话气泡使用角色人设文案，点击"和XX聊聊"跳转聊天页。

#### 2.2.3 验收标准

- [ ] 打卡完成后 AI 弹窗显示角色专属鼓励
- [ ] 打卡数据自动写入 AI 记忆库
- [ ] 打卡结果同步到聊天记录
- [ ] 成就解锁时自动弹出庆祝弹窗

---

### 2.3 打卡失败/摆烂联动 AI

#### 2.3.1 新增组件 `frontend/src/components/checkin-fail-comfort.vue`

弹窗包含:
1. 角色头像 + 共情安慰话术（从 `persona.scenarioLines.checkin_fail` 随机选取）
2. 轻量化调整计划（根据失败原因生成 3 条建议）
3. 两个按钮: "试试这个计划" / "先休息一下"

#### 2.3.2 修改 `frontend/src/store/index.js`

新增 state: `habitAI.checkinFailComfort` / `habitAI.checkinFailData`
新增 mutations: `setHabitAICheckinFailComfort` / `setHabitAICheckinFailData`

#### 2.3.3 验收标准

- [ ] 取消打卡/未完成时弹出安慰弹窗（非说教）
- [ ] AI 安慰话术匹配角色人设
- [ ] 提供轻量化调整计划
- [ ] 失败记录同步到 AI 记忆和成长档案

---

### 2.4 打卡日记互通

#### 2.4.1 修改 `frontend/src/components/checkin-diary-generator.vue`

日记生成后调用 `syncDiaryToChat` action 同步到聊天记录。

#### 2.4.2 修改 `frontend/src/pages/chat/chat.vue`

快捷回复增加"回顾我的打卡记录"选项，点击后从 AI 记忆中提取打卡记忆并展示。

#### 2.4.3 验收标准

- [ ] 打卡日记生成后自动同步到聊天记录
- [ ] 聊天页面可查看过往打卡记录
- [ ] AI 陪同用户回顾成长轨迹

---

## Part 3: 打通 AI 对话 + 环球行走成长地图联动（核心创新联动）

### 3.1 地图进度实时同步 AI 记忆库

#### 3.1.1 修改 `frontend/src/store/index.js` 的 `addWalkStep` mutation

在习惯打卡增加步数时，同步写入 AI 记忆:

```javascript
// 在 addWalkStep 中，type === 'habit' 分支内新增:
if (!state.habitAI.memories) state.habitAI.memories = []
state.habitAI.memories.unshift({
  memory_type: 'walk_progress',
  memory_content: `走到「${getCurrentStage(state.walkMap.totalCheckins).name}」，累计${state.walkMap.totalCheckins}步`,
  created_at: new Date().toISOString(),
})
if (state.habitAI.memories.length > 100) {
  state.habitAI.memories = state.habitAI.memories.slice(0, 100)
}
```

#### 3.1.2 修改 `frontend/src/common/ai-context-builder.js`

在 `generateNaturalSummary` 中增加地图维度:

```javascript
if (portrait.totalCheckins > 0) {
  const stage = getCurrentStage(portrait.totalCheckins)
  summary += `环球行走: 目前在「${stage.name}」(${stage.subtitle})\n`
  summary += `关卡描述: ${stage.description}\n`
}
```

#### 3.1.3 修改 `frontend/src/pages/chat/chat.vue` 的 `initGreeting`

AI 问候中主动提及地图进度:

```javascript
initGreeting() {
  const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
  const totalCheckins = this.$store.state.walkMap?.totalCheckins || 0
  if (totalCheckins > 0) {
    const stage = getCurrentStage(totalCheckins)
    const stageGreetings = [
      `我们走到${stage.name}了哦，风景真好呢`,
      `现在的${stage.subtitle}，你想看看吗？`,
      `我们又前进了一步，${stage.name}的风景你一定会喜欢`,
    ]
    this.aiGreetingText = stageGreetings[Math.floor(Math.random() * stageGreetings.length)]
  } else {
    // 原有问候逻辑
  }
}
```

#### 3.1.4 验收标准

- [ ] 每次打卡后地图进度同步到 AI 记忆
- [ ] AI 问候中主动提及当前地图位置
- [ ] 聊天时 AI 能引用地图进度信息

---

### 3.2 地图节点解锁专属对话剧情

#### 3.2.1 新建文件: `frontend/src/common/map-storylines.js`

为 20 个角色 x 6 个关卡编写专属剧情台词。每个角色在每个关卡有 `arrival`/`midpoint`/`departure` 三段台词。

同时包含 `STAGE_QUOTES`：20 角色 x 6 关卡的限定励志盲盒语句。

导出 `getStoryline(characterId, stageId, phase)` 和 `getStageBlindBoxQuote(characterId, stageId)` 函数。

#### 3.2.2 修改 `frontend/src/store/index.js`

在 `addWalkStep` 中检测关卡解锁，触发剧情弹窗:

```javascript
// 新增 state:
stageUnlockStory: null  // { stageId, stageName, characterId }

// 新增 mutations:
setStageUnlockStory(state, data) { state.habitAI.stageUnlockStory = data },
clearStageUnlockStory(state) { state.habitAI.stageUnlockStory = null },

// 在 addWalkStep 中关卡解锁时:
if (unlockResult.unlocked) {
  setTimeout(() => {
    this.commit('setStageUnlockStory', {
      stageId: unlockResult.newStage.id,
      stageName: unlockResult.newStage.name,
      characterId: state.habitAI?.currentCharacterId || 'linxi',
    })
  }, 0)
}
```

#### 3.2.3 新建组件: `frontend/src/components/map-storyline-popup.vue`

弹窗包含: 关卡信息头 + 角色头像 + 剧情对话气泡 + 限定盲盒语句 + 操作按钮（和AI聊聊/继续行走）。

#### 3.2.4 验收标准

- [ ] 关卡解锁时自动弹出角色专属剧情对话
- [ ] 20 个角色在每个关卡有不同的剧情台词
- [ ] 剧情弹窗含限定励志盲盒语句
- [ ] 用户可选择"和 AI 聊聊"跳转聊天页

---

### 3.3 地图可视化成长复盘

#### 3.3.1 修改 `frontend/src/pages/chat/chat.vue`

聊天页面顶部增加"成长足迹"快捷入口，点击后在聊天中插入成长复盘卡片消息:

```javascript
showGrowthTrackInChat() {
  const { userPortrait } = buildFullContext(this.$store, this.currentCharacterId)
  const stage = getCurrentStage(this.$store.state.walkMap?.totalCheckins || 0)
  const summary = `【成长足迹复盘】
当前位置: ${stage.name} (${stage.subtitle})
累计打卡: ${userPortrait.totalCheckins} 次
累计步数: ${this.$store.state.walkMap?.totalSteps || 0}
今日完成率: ${userPortrait.todayCompletionRate}%
连续坚持: ${userPortrait.streakDays} 天
最近情绪: ${userPortrait.latestEmotion?.emotion || '未知'}
正念练习: ${userPortrait.meditationCount} 次

${this.generateGrowthComment(userPortrait)}`
  // 插入聊天记录
}
```

#### 3.3.2 验收标准

- [ ] 聊天页面有"成长足迹"快捷入口
- [ ] AI 用陪伴式语言解读数据
- [ ] 复盘内容含地图位置、打卡次数、情绪状态

---

### 3.4 时间流动联动行走互动

#### 3.4.1 新建文件: `frontend/src/common/walk-idle-timer.js`

```javascript
import { getCurrentStage } from './walk-map-config.js'

const IDLE_INTERVAL = 2 * 60 * 60 * 1000  // 2小时检查一次
const IDLE_STEP_RATE = 0.1  // 每次增加0.1步

let timer = null, store = null

export function initWalkIdleTimer(vuexStore) {
  store = vuexStore
  if (timer) clearInterval(timer)
  checkIdleWalk()
  timer = setInterval(checkIdleWalk, IDLE_INTERVAL)
}

function checkIdleWalk() {
  if (!store) return
  const lastActive = store.state.walkMap?.lastActiveDate
  if (!lastActive) return
  const lastDate = new Date(lastActive + 'T00:00:00')
  const hoursSinceActive = (new Date() - lastDate) / (1000 * 60 * 60)
  if (hoursSinceActive >= 2) {
    const idleSteps = Math.floor(hoursSinceActive / 2) * IDLE_STEP_RATE
    if (idleSteps > 0) {
      store.commit('addWalkStep', { steps: idleSteps, type: 'idle', description: 'AI伙伴独自前行的旅途', emotion: '' })
      if (Math.random() < 0.3) triggerIdleChat()
    }
  }
}

function triggerIdleChat() {
  const characterId = store.state.habitAI?.currentCharacterId || 'linxi'
  const stage = getCurrentStage(store.state.walkMap?.totalCheckins || 0)
  const chats = [
    `我一个人走了会儿，到了${stage.name}，风景很好，想和你分享`,
    '你不在我自己走了几步，但还是在等你',
    '旅途中休息了一下，想着你什么时候会来',
    '我把沿途看到的风景记下来了，等你来告诉你',
  ]
  const message = chats[Math.floor(Math.random() * chats.length)]
  store.commit('aiCore/setBubbleMessage', message)
  store.commit('aiCore/setBubbleVisible', true)
  store.commit('addChatMessage', { role: 'assistant', content: message, time: Date.now(), type: 'idle_walk' })
}

export function stopWalkIdleTimer() { if (timer) { clearInterval(timer); timer = null } }
export default { initWalkIdleTimer, stopWalkIdleTimer }
```

#### 3.4.2 修改 `frontend/src/App.vue`

```javascript
import { initWalkIdleTimer } from '@/common/walk-idle-timer.js'
export default {
  onLaunch() {
    // ... 原有逻辑 ...
    initWalkIdleTimer(this.$store)
  },
}
```

#### 3.4.3 修改 `frontend/src/store/index.js`

`addWalkStep` 中 `idle` 类型只增加步数和记录历史，不增加 `totalCheckins`，不触发关卡解锁。

#### 3.4.4 验收标准

- [ ] 用户 2 小时未操作后 AI 缓慢移动
- [ ] AI 有 30% 概率主动发起闲聊
- [ ] 闲聊内容含地图位置信息
- [ ] 闲置移动不触发关卡解锁

---

## Part 4: 打通 AI 对话 + 情绪记录、正念、成长档案全模块

### 4.1 碎片化情绪打卡互通

#### 4.1.1 修改 `frontend/src/pages/emotion/emotion.vue`

情绪记录提交后:
1. 写入 AI 记忆 (`addHabitMemory`, type='emotion')
2. 添加行走步数 (`addWalkStep`, type='emotion', steps=0.3)
3. 负面情绪时 AI 主动开启疏导对话
4. 情绪非常低（score <= 2）时推荐正念练习

```javascript
async submitEmotion() {
  // ... 原有提交逻辑 ...

  this.$store.commit('addHabitMemory', {
    memory_type: 'emotion',
    memory_content: `用户记录情绪: ${this.emotion}(强度${this.intensity}/10), 标签: ${this.tags.join(',')}`,
    emotion_score: this.intensity,
    created_at: new Date().toISOString(),
  })

  this.$store.commit('addWalkStep', {
    steps: 0.3, type: 'emotion',
    description: `情绪记录: ${this.emotion}`, emotion: this.emotion,
  })

  if (this.intensity <= 4) this.triggerEmotionGuide()
},

triggerEmotionGuide() {
  this.$store.commit('aiCore/setEmotionComfortTrigger', {
    emotion: this.emotion, score: this.intensity, timestamp: Date.now(),
  })
  const guideMessages = {
    sad: '我注意到你心情不太好...你不用假装没事，在我这里可以不坚强。',
    anxious: '焦虑的感觉很不好受吧...深呼吸，我在你身边。',
    angry: '你有权利生气。我接住你的情绪了。',
    tired: '你太累了，休息一下也没关系的。',
  }
  this.$store.commit('addChatMessage', {
    role: 'assistant',
    content: guideMessages[this.emotion] || '你的感受很重要，我愿意倾听。',
    time: Date.now(), type: 'emotion_guide',
  })
  if (this.intensity <= 2) {
    setTimeout(() => {
      this.$store.commit('addChatMessage', {
        role: 'assistant',
        content: '要不要试试做个正念练习？5分钟就好，我陪你一起。',
        time: Date.now(), type: 'mindfulness_recommend',
      })
    }, 2000)
  }
},
```

#### 4.1.2 验收标准

- [ ] 情绪记录同步到 AI 记忆
- [ ] 负面情绪时 AI 主动开启疏导对话
- [ ] 情绪非常低时 AI 推荐正念练习

---

### 4.2 正念练习实时陪伴

#### 4.2.1 修改 `frontend/src/pages/meditation/meditation.vue`

1. 进入正念页面时 AI 用舒缓语气打招呼（从 `persona.scenarioLines.mindfulness_start` 随机选取）
2. 各阶段切换时 AI 给出陪伴引导
3. 练习结束后生成情绪小结同步到聊天记录
4. 添加行走步数 (0.5步) 并写入 AI 记忆

```javascript
onShow() { this.triggerMindfulnessCompanion() },

async triggerMindfulnessCompanion() {
  const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
  const persona = CHARACTER_PERSONAS[characterId]
  const greetings = persona.scenarioLines.mindfulness_start
  const msg = greetings[Math.floor(Math.random() * greetings.length)]
  this.$store.commit('aiCore/setBubbleMessage', msg)
  this.$store.commit('aiCore/setBubbleVisible', true)
},

onPhaseChange(phase) {
  const guides = {
    breathing: '跟着我的节奏...吸气...呼气...你做得很好',
    body: '感受你的身体...从头顶到脚趾...放松每一寸',
    end: '慢慢睁开眼睛...欢迎回来',
  }
  this.$store.commit('aiCore/setBubbleMessage', guides[phase] || '')
},

async onMeditationComplete() {
  this.$store.commit('addWalkStep', { steps: 0.5, type: 'meditation', description: `正念冥想: ${this.currentAudioName}`, emotion: '' })
  this.$store.commit('addHabitMemory', {
    memory_type: 'meditation',
    memory_content: `用户完成了正念冥想: ${this.currentAudioName}(${this.duration}分钟)`,
    created_at: new Date().toISOString(),
  })
  // AI 生成情绪小结同步到聊天
  this.$store.commit('addChatMessage', {
    role: 'assistant',
    content: `你刚刚完成了${this.duration}分钟的冥想。感觉到了吗？你的呼吸变得更平稳了。后续我会持续关注你的情绪变化。`,
    time: Date.now(), type: 'meditation_summary',
  })
},
```

#### 4.2.2 验收标准

- [ ] 进入正念页面时 AI 切换舒缓语气
- [ ] 练习各阶段 AI 给出陪伴引导
- [ ] 练习结束后生成情绪小结并同步到聊天

---

### 4.3 个人成长档案双向调用

#### 4.3.1 修改 `frontend/src/pages/growth-archive/growth-archive.vue`

增加"AI 解读"按钮，点击后:
1. 在聊天记录中插入档案卡片
2. AI 用陪伴式语言解读数据（打卡维度/情绪维度/地图维度）
3. AI 给出后续优化建议
4. 跳转到聊天页

#### 4.3.2 修改 `frontend/src/pages/chat/chat.vue`

快捷回复增加"查看我的成长档案"选项。

#### 4.3.3 验收标准

- [ ] 成长档案页面有"AI 解读"按钮
- [ ] AI 用陪伴式语言解读档案数据
- [ ] 聊天页面可主动调取档案
- [ ] AI 给出后续优化建议

---

### 4.4 每日励志盲盒联动

#### 4.4.1 新建文件: `frontend/src/common/daily-quotes.js`

包含 100 条独立励志文案，按主题分组:
- 1-20: 坚持主题
- 21-40: 情绪陪伴主题
- 41-60: 成长主题
- 61-80: 习惯主题
- 81-100: 陪伴主题

导出:
- `getDailyQuote(dayOffset)` - 基于日期确保每日不重复
- `getCharacterQuoteInterpretation(characterId, quote)` - 20 角色专属盲盒解读

#### 4.4.2 修改 `frontend/src/pages/chat/chat.vue`

```javascript
import { getDailyQuote, getCharacterQuoteInterpretation } from '@/common/daily-quotes.js'

onShow() {
  this.scrollToBottom()
  this.pushDailyQuote()
},

methods: {
  pushDailyQuote() {
    const today = new Date().toDateString()
    if (this.lastQuoteDate === today) return
    this.lastQuoteDate = today
    const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
    const quote = getDailyQuote()
    const interpretation = getCharacterQuoteInterpretation(characterId, quote)
    this.$store.commit('addChatMessage', {
      role: 'system', content: `今日盲盒: ${quote}`, time: Date.now(), type: 'daily_quote', quoteData: { quote, characterId },
    })
    this.$store.commit('addChatMessage', {
      role: 'assistant', content: interpretation, time: Date.now() + 1, type: 'quote_interpretation',
    })
  },
},
```

#### 4.4.3 验收标准

- [ ] 100 条独立励志文案，无重复
- [ ] 每天打开聊天窗口自动推送盲盒
- [ ] 每天只推送一次
- [ ] 20 个角色有不同的盲盒解读风格

---

## Part 5: 全局贯穿约束要求

### 5.1 AI 伙伴交互入口嵌入所有页面

#### 5.1.1 新建 Vuex 模块: `frontend/src/store/modules/aiCore.js`

namespaced 模块，通过 `rootState` 聚合全业务数据。包含:
- **state**: `currentPageScene`, `bubbleVisible`, `bubbleMessage`, `miniChatOpen`, `miniChatMessages`, `detectedEmotion`, `lastInteractionTime`, `idleThreshold`, `emotionComfortTrigger`
- **getters**: `userPortrait` (聚合全业务数据), `sceneGreeting` (按页面场景返回问候), `isIdle`
- **mutations**: `setPageScene`, `setBubbleVisible`, `setBubbleMessage`, `openMiniChat`, `closeMiniChat`, `addMiniChatMessage`, `setEmotionComfortTrigger` 等
- **actions**: `changeScene`, `onUserActivity`, `proactiveGreeting` (主动问候), `sendMiniMessage` (轻量聊天)

> **重要**: `sendMiniMessage` 中也必须做危机检测和情绪识别，与主聊天页逻辑一致。

#### 5.1.2 修改 `frontend/src/store/index.js`

```javascript
import aiCore from './modules/aiCore.js'

export default createStore({
  state: { /* 保持不变 */ },
  mutations: { /* 保持不变 */ },
  getters: { /* 保持不变 */ },
  actions: { /* 保持不变 */ },
  modules: { aiCore },
})
```

#### 5.1.3 新建组件: `frontend/src/components/ai-floating-bubble.vue`

全局悬浮 AI 伙伴入口:
1. 右下角常驻悬浮气泡（角色头像 + 气泡消息），z-index: 9999
2. 气泡根据 `aiCore/pageScene` 自动切换问候文案
3. 点击展开轻量聊天弹窗（mini-chat-panel）
4. 5分钟无操作 AI 主动发起温柔问候
5. 负面情绪记录时（score <= 3）主动弹出安抚
6. 支持拖拽移动位置
7. 深色模式适配

**关键实现**: 在 uni-app 中不支持全局组件自动渲染到所有页面，使用 mixin 方案:

新建 `frontend/src/common/page-mixin.js`:
```javascript
import AiFloatingBubble from '@/components/ai-floating-bubble.vue'
export default {
  components: { AiFloatingBubble },
  onShow() {
    const pages = getCurrentPages()
    if (pages.length > 0) {
      const route = pages[pages.length - 1].route
      const sceneMap = {
        'pages/index/index': 'home', 'pages/habit/habit': 'habit',
        'pages/chat/chat': 'chat', 'pages/walk/walk': 'walk',
        'pages/emotion/emotion': 'emotion', 'pages/meditation/meditation': 'meditation',
        'pages/box/box': 'box', 'pages/growth-archive/growth-archive': 'growth',
        'pages/growth-track/growth-track': 'growth',
        'pages/character-gallery/character-gallery': 'character',
        'pages/character-workshop/character-workshop': 'character',
      }
      this.$store?.commit('aiCore/setPageScene', sceneMap[route] || 'home')
    }
  },
}
```

**Trae 执行**: 在以下所有页面中添加 `mixins: [pageMixin]` 和 `<ai-floating-bubble />`:
> `index/habit/chat/walk/emotion/meditation/box/growth-archive/growth-track/character-gallery/character-workshop/stats/profile/settings`

#### 5.1.4 验收标准

- [ ] 所有页面右下角常驻 AI 悬浮气泡
- [ ] 点击气泡展开轻量聊天弹窗
- [ ] 气泡根据当前页面切换问候文案
- [ ] 支持拖拽移动位置
- [ ] 负面情绪时主动弹出安抚
- [ ] 深色模式适配
- [ ] 不遮挡 tabBar 和页面内容

---

### 5.2 全模块数据实时同步约束

#### 数据同步矩阵

| 触发事件 | 同步目标 | 同步方式 | 实现位置 |
|---------|---------|---------|---------|
| 习惯打卡完成 | AI记忆+聊天记录+地图步数 | `checkinTrigger` action | store/index.js |
| 习惯打卡取消 | AI记忆+安慰弹窗 | `checkinFailComfort` | habit.vue |
| 情绪记录提交 | AI记忆+地图步数+聊天记录 | `submitEmotion` | emotion.vue |
| 正念练习完成 | AI记忆+地图步数+聊天记录 | `onMeditationComplete` | meditation.vue |
| 地图关卡解锁 | AI记忆+剧情弹窗+聊天记录 | `addWalkStep` mutation | store/index.js |
| 成就解锁 | AI记忆+庆祝弹窗+聊天记录 | `checkinTrigger` action | store/index.js |
| 打卡日记生成 | 聊天记录 | `syncDiaryToChat` | checkin-diary-generator |
| 成长档案生成 | 聊天记录+AI解读 | `aiInterpretArchive` | growth-archive.vue |
| 每日盲盒推送 | 聊天记录 | `pushDailyQuote` | chat.vue |
| 闲置行走 | AI记忆+聊天记录+悬浮气泡 | `walk-idle-timer.js` | App.vue |

**实现要求**:
1. 所有数据同步通过 Vuex action/mutation 完成
2. 同步操作不阻塞用户操作
3. 同步失败时静默降级
4. 聊天记录中系统消息有 `type` 字段标识来源

---

### 5.3 20 角色人设严格匹配约束

Trae 在编写每个联动组件时，必须检查:
1. 打卡鼓励话术: 使用 `persona.scenarioLines.checkin_success`
2. 打卡失败安慰: 使用 `persona.scenarioLines.checkin_fail`
3. 地图到达台词: 使用 `getStoryline()` 返回值
4. 成就庆祝台词: 使用 `persona.scenarioLines.achievement_unlock`
5. 情绪疏导话术: 根据 `persona.emotionExpression`
6. 正念引导话术: 使用 `persona.scenarioLines.mindfulness_start`
7. 盲盒解读: 使用 `getCharacterQuoteInterpretation()`
8. 前置打气: 基于角色 `tone` 和 `speechHabits`
9. 闲置闲聊: 基于角色 `catchphrases` 和 `tone`
10. 主动问候: 基于 `sceneGreeting` + 角色 `catchphrases`

---

## Part 6: 分批实施路线图

### 第一批: AI 对话底层重构（最高优先级）

| 步骤 | 任务 | 文件 | 改动量 |
|------|------|------|--------|
| 1 | 创建 20 角色完整人设包 | `common/character-personas.js` (新建) | 大 |
| 2 | 增强 `getSystemPrompt` | `common/ai-prompts.js` (修改) | 中 |
| 3 | 创建上下文构建器 | `common/ai-context-builder.js` (新建) | 中 |
| 4 | 创建情绪识别插件 | `common/emotion-detector.js` (新建) | 中 |
| 5 | 修改 chat.vue 集成 | `pages/chat/chat.vue` (修改) | 中 |
| 6 | 修改 Mock 动态回复 | `common/mock.js` (修改) | 中 |
| 7 | 后端接收 systemPrompt | `server/app/services/ai_service.py` (修改) | 小 |
| 8 | 后端 temperature 调优 | `server/app/services/ai_service.py` (修改) | 小 |

**验收**: 同一问题连续 3 次回复不同 / AI 能引用历史数据 / 20 角色语气区分 / H5 构建通过

---

### 第二批: 全局 AI 悬浮气泡 + aiCore 模块

| 步骤 | 任务 | 文件 | 改动量 |
|------|------|------|--------|
| 1 | 创建 aiCore Vuex 模块 | `store/modules/aiCore.js` (新建) | 中 |
| 2 | 注册 aiCore 模块 | `store/index.js` (修改) | 小 |
| 3 | 创建悬浮气泡组件 | `components/ai-floating-bubble.vue` (新建) | 大 |
| 4 | 创建页面 mixin | `common/page-mixin.js` (新建) | 小 |
| 5 | 所有页面添加 mixin+组件 | 13 个页面 vue 文件 (修改) | 中 |
| 6 | 创建闲置行走计时器 | `common/walk-idle-timer.js` (新建) | 中 |
| 7 | App.vue 启动计时器 | `App.vue` (修改) | 小 |

**验收**: 所有页面有悬浮气泡 / 轻量聊天可用 / 场景问候切换 / 闲置 AI 移动+闲聊 / H5 构建通过

---

### 第三批: 习惯打卡 + 地图深度联动

| 步骤 | 任务 | 文件 | 改动量 |
|------|------|------|--------|
| 1 | 打卡前 AI 前置打气 | `pages/habit/habit.vue` (修改) | 中 |
| 2 | 拖延检测+开导 | `pages/habit/habit.vue` (修改) | 中 |
| 3 | 增强 checkinTrigger | `store/index.js` (修改) | 中 |
| 4 | 增强打卡弹窗 | `components/habit-checkin-popup.vue` (修改) | 中 |
| 5 | 打卡失败安慰组件 | `components/checkin-fail-comfort.vue` (新建) | 中 |
| 6 | 日记互通 | `components/checkin-diary-generator.vue` (修改) | 小 |
| 7 | 地图进度同步 AI 记忆 | `store/index.js` (修改) | 小 |
| 8 | 地图剧情文件 | `common/map-storylines.js` (新建) | 大 |
| 9 | 地图剧情弹窗 | `components/map-storyline-popup.vue` (新建) | 中 |
| 10 | 聊天页成长足迹入口 | `pages/chat/chat.vue` (修改) | 小 |

**验收**: 打卡前 AI 打气 / 打卡后专属互动 / 失败安慰 / 关卡解锁剧情 / 聊天页成长足迹 / H5 构建通过

---

### 第四批: 情绪/正念/成长档案/盲盒联动

| 步骤 | 任务 | 文件 | 改动量 |
|------|------|------|--------|
| 1 | 情绪记录同步 AI | `pages/emotion/emotion.vue` (修改) | 中 |
| 2 | 负面情绪 AI 疏导 | `pages/emotion/emotion.vue` (修改) | 中 |
| 3 | 正念 AI 陪伴 | `pages/meditation/meditation.vue` (修改) | 中 |
| 4 | 正念小结同步聊天 | `pages/meditation/meditation.vue` (修改) | 小 |
| 5 | 成长档案 AI 解读 | `pages/growth-archive/growth-archive.vue` (修改) | 中 |
| 6 | 聊天页调取档案 | `pages/chat/chat.vue` (修改) | 小 |
| 7 | 100 条励志盲盒 | `common/daily-quotes.js` (新建) | 大 |
| 8 | 角色盲盒解读 | `common/daily-quotes.js` (含) | 中 |
| 9 | 聊天页盲盒推送 | `pages/chat/chat.vue` (修改) | 小 |

**验收**: 情绪记录同步 AI / 负面情绪疏导 / 正念陪伴 / 档案 AI 解读 / 每日盲盒推送 / H5 构建通过

---

## 附录: 新增文件清单

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `frontend/src/common/character-personas.js` | 新建 | 20 角色完整人设包 |
| `frontend/src/common/ai-context-builder.js` | 新建 | 50轮上下文+行为数据构建器 |
| `frontend/src/common/emotion-detector.js` | 新建 | 多维度情绪识别插件 |
| `frontend/src/common/map-storylines.js` | 新建 | 20角色x6关卡剧情台词 |
| `frontend/src/common/daily-quotes.js` | 新建 | 100条励志盲盒+角色解读 |
| `frontend/src/common/walk-idle-timer.js` | 新建 | 闲置行走计时器 |
| `frontend/src/common/page-mixin.js` | 新建 | 页面mixin（悬浮气泡+场景检测）|
| `frontend/src/store/modules/aiCore.js` | 新建 | AI核心Vuex模块 |
| `frontend/src/components/ai-floating-bubble.vue` | 新建 | 全局悬浮AI伙伴入口 |
| `frontend/src/components/checkin-fail-comfort.vue` | 新建 | 打卡失败安慰弹窗 |
| `frontend/src/components/map-storyline-popup.vue` | 新建 | 地图剧情弹窗 |

## 附录: 修改文件清单

| 文件路径 | 修改内容 |
|---------|---------|
| `frontend/src/common/ai-prompts.js` | 引入人设包，增强 getSystemPrompt |
| `frontend/src/common/mock.js` | 移除固定模板，改用动态生成 |
| `frontend/src/store/index.js` | 注册aiCore模块，增强checkinTrigger，新增mutations |
| `frontend/src/pages/chat/chat.vue` | 集成情绪检测+50轮上下文+成长足迹+盲盒推送 |
| `frontend/src/pages/habit/habit.vue` | 打卡前AI打气+拖延检测 |
| `frontend/src/pages/emotion/emotion.vue` | 情绪记录同步AI+负面情绪疏导 |
| `frontend/src/pages/meditation/meditation.vue` | 正念AI陪伴+小结同步 |
| `frontend/src/pages/growth-archive/growth-archive.vue` | AI解读档案 |
| `frontend/src/components/habit-checkin-popup.vue` | 增强弹窗展示 |
| `frontend/src/components/checkin-diary-generator.vue` | 日记同步聊天 |
| `frontend/src/App.vue` | 启动闲置计时器 |
| `server/app/services/ai_service.py` | 接收systemPrompt+temperature调优 |
| 13个页面vue文件 | 添加pageMixin和悬浮气泡组件 |

---

## 附录: 新增后端端点清单（可选，Mock 模式不需要）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ai-core/context` | GET | 获取完整用户画像 |
| `/api/v1/ai-core/emotion-detect` | POST | 文字情绪检测 |
| `/api/v1/habit-ai/pre-checkin` | POST | 打卡前AI打气 |
| `/api/v1/habit-ai/checkin-fail` | POST | 打卡失败AI安慰 |
| `/api/v1/walk-ai/storyline` | GET | 获取地图剧情台词 |
| `/api/v1/walk-ai/idle-walk` | POST | 闲置行走同步 |
| `/api/v1/emotion-ai/guide` | POST | 情绪疏导对话 |
| `/api/v1/mindfulness-ai/companion` | POST | 正念AI陪伴引导 |
| `/api/v1/archive-ai/interpret` | POST | AI解读成长档案 |
| `/api/v1/daily-quote` | GET | 获取每日盲盒文案 |

---

> **执行完毕标准**: 所有 4 批任务完成后，运行 H5 构建 (`npm run build:h5`)，确保无编译错误。逐页面验证 AI 悬浮气泡显示、轻量聊天可用、场景问候切换正常。在 Mock 模式下测试所有联动流程，确认数据同步无延迟、AI 回复匹配角色人设、无回归问题。