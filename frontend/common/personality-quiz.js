/**
 * 性格测评 v2（2026-10-26 重写题库与计分）
 *
 * 为什么要重写 v1：
 *   v1 只有 8 道题、每题四个选项，而选项本身就是人格标签（"焦虑型/完美型/拖延型/佛系型"），
 *   作答=直接挑标签，既没有区分度也没有效度可言，结果基本靠"点哪句顺眼"。
 *
 * v2 的改动（保留所有对外导出名，老调用方不用改）：
 *   1. 量表：统一李克特 5 点（完全不符合 → 非常符合），选项不再暴露人格标签
 *   2. 维度：5 个特质维度（大五简化：外向性/尽责性/情绪稳定性/开放性/宜人性）
 *            + 4 类陪伴偏好（温柔/理性/元气/创意），共 9 个分量表、28 题
 *   3. 反向计分：每个维度都混入反向表述题，抑制"一路点同意"的作答定势
 *   4. 题序：按维度轮转交错，避免同维度连排带来的顺序效应
 *   5. 计分：维度内取均分 → 折算 0-100 标准分 → 三档等级（偏低/中等/偏高）
 *   6. 作答质量：直线作答、正反向矛盾、奇偶分半差、作答过快 —— 都会被检测并在结果页提示
 *   7. 向下兼容：仍然输出 personality / emotionalResilience / procrastination / companionStyle
 *      四个老字段，角色推荐 getRecommendedCharacter 一行都不用改
 *
 * ⚠️ 定位说明：本量表为产品内"AI 伙伴匹配"用的自编简版量表，
 *    不是临床诊断工具，结果仅作个性化推荐参考。
 */

// ============ 作答量表（李克特 5 点）============
export const LIKERT_OPTIONS = [
  { value: 1, text: '完全不符合' },
  { value: 2, text: '不太符合' },
  { value: 3, text: '一般 / 说不清' },
  { value: 4, text: '比较符合' },
  { value: 5, text: '非常符合' }
]

export const QUIZ_VERSION = 'v2'

// ============ 维度定义 ============
export const DIMENSIONS = [
  {
    key: 'extraversion',
    name: '外向性',
    desc: '从人际互动中获取能量的倾向',
    lowText: '偏内向：独处时更自在，社交之后需要充电',
    midText: '中间型：能社交也享受独处，看场合切换',
    highText: '偏外向：喜欢与人连接，互动中更有活力'
  },
  {
    key: 'conscientiousness',
    name: '尽责自律',
    desc: '计划性、坚持度与自我约束',
    lowText: '偏低：容易被当下的感受带走，计划常搁置',
    midText: '中等：大体能推进，状态差时会掉链子',
    highText: '偏高：条理清晰，能按计划推进并自我约束'
  },
  {
    key: 'emotionalStability',
    name: '情绪稳定性',
    desc: '面对波动时情绪的平稳程度与恢复力',
    lowText: '偏低：情绪起伏明显，需要更多安抚与缓冲',
    midText: '中等：多数时候能自稳，遇到大事会晃动',
    highText: '偏高：情绪平稳，受挫之后恢复较快'
  },
  {
    key: 'openness',
    name: '开放性',
    desc: '对新经验、新想法与想象的接纳度',
    lowText: '偏低：更偏好熟悉稳妥的方式',
    midText: '中等：愿意尝试，但不主动追逐新鲜',
    highText: '偏高：好奇爱探索，容易被新点子点燃'
  },
  {
    key: 'agreeableness',
    name: '宜人共情',
    desc: '体谅他人、顾及关系的倾向',
    lowText: '偏低：更直率，优先把对错讲清楚',
    midText: '中等：能体谅，也有自己的边界',
    highText: '偏高：善解人意，倾向先照顾感受与关系'
  }
]

// 陪伴偏好：测的是"我喜欢被怎样陪伴"，不是人格特质，所以单独成组
export const COMPANION_STYLES = [
  { key: 'warm', name: '温柔陪伴', icon: '🌿', desc: '先接住情绪，再谈办法' },
  { key: 'smart', name: '理性分析', icon: '📘', desc: '给有依据的建议和清晰的利弊' },
  { key: 'energetic', name: '元气激励', icon: '🔥', desc: '打气、催促、一起冲' },
  { key: 'creative', name: '创意灵感', icon: '✨', desc: '出人意料的角度和玩法' }
]

// ============ 题库（按维度分组；reverse=true 为反向计分题）============
const BANK = {
  extraversion: [
    { id: 'E1', text: '在不熟的人群里，我通常也会主动开口聊天。', reverse: false },
    { id: 'E2', text: '连续几天的社交之后，我会明显想一个人待着。', reverse: true },
    { id: 'E3', text: '聚会时，我往往是活跃气氛的那一个。', reverse: false },
    { id: 'E4', text: '遇到不认识的人，我多半会等对方先开口。', reverse: true }
  ],
  conscientiousness: [
    { id: 'C1', text: '我会在截止日期前就把事情做完，不喜欢拖到最后一刻。', reverse: false },
    { id: 'C2', text: '我习惯把要做的事列成清单，再按轻重缓急推进。', reverse: false },
    { id: 'C3', text: '只要没人催，我很容易把事情一直往后放。', reverse: true },
    { id: 'C4', text: '计划被打乱时，我会尽快重新安排，而不是干脆放弃。', reverse: false },
    { id: 'C5', text: '我的桌面或文件常常很乱，也不太想整理。', reverse: true }
  ],
  emotionalStability: [
    { id: 'S1', text: '一点小事就可能让我心情明显变差。', reverse: true },
    { id: 'S2', text: '遇到突发状况，我通常能先稳住情绪再处理。', reverse: false },
    { id: 'S3', text: '别人的一句评价，会让我反复琢磨很久。', reverse: true },
    { id: 'S4', text: '心情低落时，我多半能自己慢慢调整回来。', reverse: false }
  ],
  openness: [
    { id: 'O1', text: '我愿意尝试没接触过的新鲜事物，哪怕可能做不好。', reverse: false },
    { id: 'O2', text: '我常对「为什么」这类问题感兴趣，喜欢琢磨背后的原理。', reverse: false },
    { id: 'O3', text: '我更喜欢按熟悉的方式做事，不太想换花样。', reverse: true },
    { id: 'O4', text: '音乐、画面或故事常常能打动我。', reverse: false }
  ],
  agreeableness: [
    { id: 'A1', text: '朋友情绪不好时，我会先照顾他的感受，再讲道理。', reverse: false },
    { id: 'A2', text: '与人有分歧时，我更愿意先找共同点。', reverse: false },
    { id: 'A3', text: '如果有人拖累进度，我会直接表达不满。', reverse: true }
  ],
  companion_warm: [
    { id: 'K1', text: '我更希望伙伴先接住我的情绪，而不是马上给建议。', reverse: false },
    { id: 'K2', text: '难过的时候，被温柔地陪着比被分析问题更管用。', reverse: false }
  ],
  companion_smart: [
    { id: 'K3', text: '我更希望伙伴给出有依据、有条理的分析。', reverse: false },
    { id: 'K4', text: '选择困难时，我期待有人帮我把利弊列清楚。', reverse: false }
  ],
  companion_energetic: [
    { id: 'K5', text: '我更需要有人打气、催着我动起来。', reverse: false },
    { id: 'K6', text: '有人陪我一起「冲一把」时，我更容易坚持下去。', reverse: false }
  ],
  companion_creative: [
    { id: 'K7', text: '我更喜欢伙伴带来意想不到的点子和玩法。', reverse: false },
    { id: 'K8', text: '相比标准答案，我更喜欢有趣的角度和比喻。', reverse: false }
  ]
}

const DIM_ORDER = [
  'extraversion', 'conscientiousness', 'emotionalStability', 'openness', 'agreeableness',
  'companion_warm', 'companion_smart', 'companion_energetic', 'companion_creative'
]

/**
 * 按维度轮转交错出题：同维度的题不连排，降低顺序效应与"顺着手感一路点"的风险
 */
function interleaveQuestions(bank, order) {
  const pools = order.map(key => ({ key, items: (bank[key] || []).slice() }))
  const out = []
  let guard = 0
  while (pools.some(p => p.items.length) && guard < 100) {
    for (const p of pools) {
      if (p.items.length) {
        const item = p.items.shift()
        out.push({
          ...item,
          dimension: p.key,
          // 兼容老页面：题目仍带 options，但统一指向同一份量表
          options: LIKERT_OPTIONS,
          index: out.length + 1
        })
      }
    }
    guard++
  }
  return out
}

export const QUESTIONS = interleaveQuestions(BANK, DIM_ORDER)

// ============ 计分 ============

/** 取作答原始分：兼容 {value} 对象与纯数字两种写法 */
function getRawValue(answer) {
  if (answer == null) return 0
  if (typeof answer === 'number') return answer >= 1 && answer <= 5 ? answer : 0
  if (typeof answer === 'object' && typeof answer.value === 'number') {
    return answer.value >= 1 && answer.value <= 5 ? answer.value : 0
  }
  return 0
}

function mean(arr) {
  if (!arr || !arr.length) return 0
  return arr.reduce((s, v) => s + v, 0) / arr.length
}

function stdDev(arr) {
  if (!arr || arr.length < 2) return 0
  const m = mean(arr)
  return Math.sqrt(arr.reduce((s, v) => s + Math.pow(v - m, 2), 0) / arr.length)
}

/** 5 点均分 → 0-100 标准分（1 分=0，5 分=100） */
function toScore(m) {
  return Math.round(((m - 1) / 4) * 100)
}

/** 均分 → 三档等级 */
function levelOf(m) {
  if (m < 2.6) return 'low'
  if (m < 3.5) return 'medium'
  return 'high'
}

/** 反向计分：1↔5，2↔4，3 不变 */
function scoreItem(raw, reverse) {
  return reverse ? 6 - raw : raw
}

/**
 * 计算测评结果
 * @param {Array} answers - 每题作答（LIKERT_OPTIONS 中的选项对象，或 1-5 的数字）
 * @param {Object} meta - { durationMs, startedAt } 可选，用于作答质量判断
 * @returns {Object} 含兼容四字段 + dimensions + companion + validity
 */
export function calculateResult(answers, meta = {}) {
  const list = Array.isArray(answers) ? answers : []
  const scored = []

  QUESTIONS.forEach((q, i) => {
    const raw = getRawValue(list[i])
    if (!raw) return
    scored.push({
      id: q.id,
      dimension: q.dimension,
      reverse: !!q.reverse,
      raw,
      scored: scoreItem(raw, q.reverse)
    })
  })

  // ---- 5 个特质维度 ----
  const dimensions = {}
  DIMENSIONS.forEach(d => {
    const items = scored.filter(s => s.dimension === d.key)
    const vals = items.map(s => s.scored)
    const m = mean(vals)
    const positives = items.filter(s => !s.reverse).map(s => s.scored)
    const negatives = items.filter(s => s.reverse).map(s => s.scored)
    // 奇偶分半：单次施测下唯一能做的粗略一致性检查
    const odd = vals.filter((_, idx) => idx % 2 === 0)
    const even = vals.filter((_, idx) => idx % 2 === 1)
    const splitDiff = (odd.length && even.length) ? Math.abs(mean(odd) - mean(even)) : 0
    const reverseGap = (positives.length && negatives.length)
      ? Math.abs(mean(positives) - mean(negatives)) : 0

    dimensions[d.key] = {
      key: d.key,
      name: d.name,
      desc: d.desc,
      n: vals.length,
      mean: Math.round(m * 100) / 100,
      sd: Math.round(stdDev(vals) * 100) / 100,
      score: toScore(m),
      level: levelOf(m),
      // 0 分维度（一题没答）不给等级，避免"全 0 判成 low"这种假结果
      answered: vals.length > 0,
      splitDiff: Math.round(splitDiff * 100) / 100,
      reverseGap: Math.round(reverseGap * 100) / 100
    }
  })

  // ---- 4 类陪伴偏好 ----
  const companion = {}
  COMPANION_STYLES.forEach(c => {
    const vals = scored.filter(s => s.dimension === 'companion_' + c.key).map(s => s.scored)
    const m = mean(vals)
    companion[c.key] = {
      key: c.key,
      name: c.name,
      icon: c.icon,
      desc: c.desc,
      n: vals.length,
      mean: Math.round(m * 100) / 100,
      score: toScore(m),
      answered: vals.length > 0
    }
  })

  // ---- 作答质量（效度线索）----
  const raws = scored.map(s => s.raw)
  const straightLining = raws.length >= 10 && raws.every(v => v === raws[0])
  const inconsistent = DIMENSIONS.filter(d => dimensions[d.key].reverseGap >= 2).map(d => d.key)
  const splitWarn = DIMENSIONS.filter(d => dimensions[d.key].splitDiff >= 1.5).map(d => d.key)
  const avgMs = raws.length && meta.durationMs ? meta.durationMs / Math.max(raws.length, 1) : 0
  const tooFast = avgMs > 0 && avgMs < 1200

  const notes = []
  if (straightLining) notes.push('所有题目都选了同一档，结果可能无法反映真实差异，建议重测。')
  if (inconsistent.length) notes.push('部分维度的正反向题目回答相互矛盾，相关维度结果仅供参考。')
  if (splitWarn.length) notes.push('个别维度内部一致性偏低，该维度结论建议谨慎看待。')
  if (tooFast) notes.push('作答速度偏快，可能没有充分阅读题目。')
  if (scored.length < QUESTIONS.length) notes.push('有题目未作答，相关维度分数基于已答题目计算。')

  const validity = {
    answered: scored.length,
    total: QUESTIONS.length,
    complete: scored.length === QUESTIONS.length,
    straightLining,
    inconsistentDims: inconsistent,
    splitWarnDims: splitWarn,
    avgMsPerItem: Math.round(avgMs),
    tooFast,
    valid: !straightLining && scored.length >= QUESTIONS.length * 0.8,
    notes
  }

  // ---- 向下兼容的四字段（角色推荐 & 旧页面直接读）----
  const esLevel = dimensions.emotionalStability.level
  const cLevel = dimensions.conscientiousness.level

  let personality = 'buddha'
  if (esLevel === 'low') personality = 'anxious'
  else if (cLevel === 'high') personality = 'perfect'
  else if (cLevel === 'low') personality = 'procrastinator'

  const procrastination = cLevel === 'high' ? 'low' : (cLevel === 'medium' ? 'medium' : 'high')

  // 陪伴风格：取偏好分最高的一项；全平手时用宜人性兜底（宜人高→温柔）
  let companionStyle = 'warm'
  let best = -1
  COMPANION_STYLES.forEach(c => {
    const s = companion[c.key].score
    if (s > best) { best = s; companionStyle = c.key }
  })
  if (best <= 0) companionStyle = dimensions.agreeableness.level === 'high' ? 'warm' : 'smart'

  // 兼容旧结构的 rawScores（老代码/云端历史记录仍按四维读）
  const rawScores = {
    extraversion: dimensions.extraversion.mean,
    conscientiousness: dimensions.conscientiousness.mean,
    emotionalStability: dimensions.emotionalStability.mean,
    openness: dimensions.openness.mean,
    agreeableness: dimensions.agreeableness.mean,
    companion: {
      warm: companion.warm.mean,
      smart: companion.smart.mean,
      energetic: companion.energetic.mean,
      creative: companion.creative.mean
    }
  }

  return {
    // 兼容字段
    personality,
    emotionalResilience: esLevel,
    procrastination,
    companionStyle,
    // 新增结构
    dimensions,
    companion,
    validity,
    rawScores,
    answers: scored.map(s => ({ id: s.id, dimension: s.dimension, raw: s.raw })),
    version: QUIZ_VERSION,
    finishedAt: new Date().toISOString()
  }
}

/** 维度等级 → 展示文案 */
export function getDimensionText(result, key) {
  const dim = result && result.dimensions && result.dimensions[key]
  if (!dim) return ''
  const def = DIMENSIONS.find(d => d.key === key)
  if (!def) return ''
  if (dim.level === 'low') return def.lowText
  if (dim.level === 'high') return def.highText
  return def.midText
}

/** 结果页用的维度列表（分数条） */
export function getDimensionList(result) {
  return DIMENSIONS.map(d => {
    const dim = (result && result.dimensions && result.dimensions[d.key]) || {}
    return {
      key: d.key,
      name: d.name,
      desc: d.desc,
      score: typeof dim.score === 'number' ? dim.score : 0,
      level: dim.level || 'medium',
      levelText: dim.level === 'low' ? '偏低' : (dim.level === 'high' ? '偏高' : '中等'),
      text: getDimensionText(result, d.key)
    }
  })
}

/** 结果页用的陪伴偏好列表（按得分排序） */
export function getCompanionList(result) {
  const src = (result && result.companion) || {}
  return COMPANION_STYLES
    .map(c => ({
      key: c.key,
      name: c.name,
      icon: c.icon,
      desc: c.desc,
      score: (src[c.key] && src[c.key].score) || 0,
      top: false
    }))
    .sort((a, b) => b.score - a.score)
    .map((item, idx) => ({ ...item, top: idx === 0 }))
}

export function getResultDescription(result) {
  const descriptions = {
    personality: {
      anxious: '你的情绪感知很细腻，容易被外界影响起伏，需要被稳稳接住、慢慢来的陪伴。',
      perfect: '你自律且有条理，喜欢把事情想清楚再动手，适合被有质量的分析和挑战推着走。',
      procrastinator: '你对"被安排"比较敏感，靠状态和兴致驱动，需要有人把起步门槛降到最低。',
      buddha: '你心态平稳、不易内耗，节奏自洽，适合温和陪伴式的长期相处。'
    },
    emotionalResilience: {
      low: '情绪起伏较明显，遇到波折时需要更多缓冲、安抚与陪伴。',
      medium: '大多数时候能自己消化情绪，遇到大事时会需要有人搭把手。',
      high: '情绪比较稳，受挫后能较快恢复，独立消化能力强。'
    },
    procrastination: {
      low: '行动力强，计划一旦定下就能推进，很少拖到最后一刻。',
      medium: '整体能完成，但状态不好的时候会明显拖延。',
      high: '启动困难比较明显，需要外部提醒、拆解任务来降低起步阻力。'
    },
    companionStyle: {
      warm: '你更在意"被理解"：先有人接住情绪，再谈解决办法。',
      smart: '你更在意"被讲清楚"：希望得到有依据、有结构的分析与建议。',
      energetic: '你更在意"被推一把"：需要打气、催促和一起行动的劲头。',
      creative: '你更在意"被点亮"：喜欢出其不意的角度、比喻和玩法。'
    }
  }

  const r = result || {}
  return {
    personality: descriptions.personality[r.personality] || '',
    emotionalResilience: descriptions.emotionalResilience[r.emotionalResilience] || '',
    procrastination: descriptions.procrastination[r.procrastination] || '',
    companionStyle: descriptions.companionStyle[r.companionStyle] || ''
  }
}

// ============ 云端同步（2026-10-26 新增）============
// 背景：原方案 100% 跑在 localStorage —— 换设备/清缓存就没了，
//       且 personality_result 是全局单份，多人共用一台设备会串。
// 方案：本地仍即时写入（保证不破坏任何现有同步调用），额外异步同步到云端；
//       云端接口见 @/api/personality，数据表 user_personality_results。
// 容错：任何一步失败都静默降级为"纯本地"，绝不阻塞页面。

let _cloudEnabled = true

/** 云端同步总开关（排查问题时可临时关闭） */
export function setQuizCloudEnabled(flag) {
  _cloudEnabled = !!flag
}

/** 惰性取 store：避免与 common/request 形成模块级循环依赖 */
async function _getStore() {
  try {
    const mod = await import('@/store')
    return (mod && mod.default) || null
  } catch (e) {
    return null
  }
}

/** 惰性取 api 模块 */
async function _getApi() {
  try {
    const mod = await import('@/api/personality')
    return (mod && mod.default) || null
  } catch (e) {
    return null
  }
}

/** 已登录（有 token）才走云端；游客/未登录只用本地 */
async function _canUseCloud() {
  if (!_cloudEnabled) return false
  try {
    const store = await _getStore()
    const token = store && store.state && store.state.token
    return !!token
  } catch (e) {
    return false
  }
}

/**
 * 同一份结果的并发/重复提交去重（saveQuizResult 内部推一次、
 * saveQuizResultAsync 又 await 一次，不去重会写两行一模一样的记录）
 */
let _pushCache = { key: '', promise: null }

function _pushKey(result, source) {
  try {
    return JSON.stringify([
      result.personality, result.emotionalResilience,
      result.procrastination, result.companionStyle, source || 'app'
    ])
  } catch (e) {
    return ''
  }
}

/** 把结果推到云端（内部用，失败静默） */
async function _pushQuizResultToCloud(result, source) {
  if (!result) return false
  if (!(await _canUseCloud())) return false

  const key = _pushKey(result, source)
  if (key && _pushCache.key === key && _pushCache.promise) {
    return await _pushCache.promise
  }

  const p = (async () => {
    try {
      const api = await _getApi()
      if (!api) return false
      await api.saveResult({
        personality: result.personality,
        emotionalResilience: result.emotionalResilience,
        procrastination: result.procrastination,
        companionStyle: result.companionStyle,
        rawScores: result.rawScores || null,
        answers: result.answers || null,
        // v2 起带题库版本，云端可据此区分新老量表的结果
        quizVersion: result.version || QUIZ_VERSION,
        source: source || 'app'
      })
      return true
    } catch (e) {
      console.warn('[personality] 云端保存失败（已降级为本地）:', e && e.message)
      return false
    }
  })()

  _pushCache = { key: key, promise: p }
  return await p
}

/**
 * 保存测评结果（本地即时写 + 云端异步同步）
 * 保持同步签名，现有调用方一行都不用改。
 * 需要"确认已落云端"时用下面的 saveQuizResultAsync。
 */
export function saveQuizResult(result, username) {
  try {
    uni.setStorageSync('personality_result', JSON.stringify(result))
    // 测评完成标记按用户名区分，新账号登录时仍会触发测评
    const user = username || 'default'
    uni.setStorageSync('quiz_completed_' + user, 'true')
    uni.setStorageSync('quiz_last_user', user)
    // 兼容旧版全局标记
    uni.setStorageSync('quiz_completed', 'true')
    uni.setStorageSync('quiz_date', new Date().toISOString())
  } catch (e) {
    console.error('保存测评结果失败', e)
  }
  // ↓↓↓ 新增：异步同步到云端（失败不影响本地） ↓↓↓
  _pushQuizResultToCloud(result, 'app')
  // ↑↑↑ 新增结束 ↑↑↑
}

/**
 * 保存测评结果（await 版）：本地写 + 等云端返回
 * 性格测评页确认结果时用这个，保证跳转前已落库。
 */
export async function saveQuizResultAsync(result, username) {
  saveQuizResult(result, username)
  return await _pushQuizResultToCloud(result, 'app')
}

/**
 * 读取本地测评结果（同步，保持原行为不变）
 * ⚠️ 这是"本地缓存"，不是云端真相。换设备后这里会是 null，
 *    需要云端结果请 await fetchQuizResultFromCloud()。
 */
export function getSavedQuizResult() {
  try {
    const saved = uni.getStorageSync('personality_result')
    return saved ? JSON.parse(saved) : null
  } catch (e) {
    console.error('读取测评结果失败', e)
    return null
  }
}

/**
 * 从云端拉取测评结果并落到本地（换设备/清缓存后的恢复入口）
 * - 云端有结果   -> 覆盖本地（含按账号的完成标记），返回云端结果
 * - 云端无、本地有 -> 老数据补传上云，返回本地结果
 * - 都没有 / 未登录 / 接口挂 -> 返回本地结果或 null，绝不抛错
 */
export async function fetchQuizResultFromCloud() {
  const local = getSavedQuizResult()
  try {
    if (!(await _canUseCloud())) return local
    const api = await _getApi()
    if (!api) return local

    // 当前登录账号（用于判断本地那份结果到底属于谁）
    let username = ''
    try {
      const store = await _getStore()
      username = (store && store.state && store.state.username) || ''
    } catch (e) { /* 静默 */ }
    let lastUser = ''
    try { lastUser = uni.getStorageSync('quiz_last_user') || '' } catch (e) { /* 静默 */ }
    if (!username) username = lastUser

    const data = await api.getResult()
    if (data && data.completed && data.result) {
      const r = data.result
      const cloud = {
        personality: r.personality,
        emotionalResilience: r.emotionalResilience,
        procrastination: r.procrastination,
        companionStyle: r.companionStyle,
        rawScores: r.rawScores || undefined
      }
      // 云端结果写回本地，让现存所有读本地的代码自动生效
      _writeLocalResult(cloud, username)
      return cloud
    }

    // 云端还没有：本地老数据只有"确实属于当前账号"时才补传，避免串号
    const localBelongsToUser = !!local && (!lastUser || lastUser === username)
    if (localBelongsToUser) {
      _pushQuizResultToCloud(local, 'migrate')
      return local
    }
    // 本地那份是别人的（多人共用设备）→ 清掉，别让下一个人读到
    _clearLocalResultOnly()
    return null
  } catch (e) {
    console.warn('[personality] 云端拉取失败（已降级为本地）:', e && e.message)
    return local
  }
}

/** 内部：只清"结果本体"，保留各账号的完成标记（避免串号时读到别人的结果） */
function _clearLocalResultOnly() {
  try {
    uni.removeStorageSync('personality_result')
    uni.removeStorageSync('quiz_date')
    uni.removeStorageSync('quiz_last_user')
    uni.removeStorageSync('quiz_completed')
  } catch (e) {
    console.error('清理本地测评结果失败', e)
  }
}

/** 内部：只写本地缓存（供云端结果回灌） */
function _writeLocalResult(result, username) {
  try {
    uni.setStorageSync('personality_result', JSON.stringify(result))
    const user = username || uni.getStorageSync('quiz_last_user') || 'default'
    uni.setStorageSync('quiz_completed_' + user, 'true')
    uni.setStorageSync('quiz_last_user', user)
    uni.setStorageSync('quiz_completed', 'true')
    uni.setStorageSync('quiz_date', new Date().toISOString())
  } catch (e) {
    console.error('回写本地测评结果失败', e)
  }
}

/** 指定用户是否已完成测评 */
export function isQuizCompletedBy(username) {
  try {
    if (!username) return false
    return uni.getStorageSync('quiz_completed_' + username) === 'true'
  } catch (e) {
    return false
  }
}

export function isQuizCompleted() {
  try {
    // 仅当全局标记属于最近一次测评的用户时才认为完成（按账号区分）
    const lastUser = uni.getStorageSync('quiz_last_user')
    if (lastUser) return uni.getStorageSync('quiz_completed_' + lastUser) === 'true'
    return uni.getStorageSync('quiz_completed') === 'true'
  } catch (e) {
    return false
  }
}

export function resetQuiz() {
  try {
    uni.removeStorageSync('personality_result')
    uni.removeStorageSync('quiz_completed')
    uni.removeStorageSync('quiz_date')
    uni.removeStorageSync('quiz_last_user')
    // 清掉所有按用户名区分的完成标记
    const info = uni.getStorageInfoSync()
    ;(info.keys || []).forEach(k => {
      if (k.indexOf('quiz_completed_') === 0) uni.removeStorageSync(k)
    })
  } catch (e) {
    console.error('重置测评失败', e)
  }
  // ↓↓↓ 新增：同步重置云端（失败不影响本地） ↓↓↓
  _resetQuizOnCloud()
  // ↑↑↑ 新增结束 ↑↑↑
}

/** 云端重置（内部用，失败静默） */
async function _resetQuizOnCloud() {
  if (!(await _canUseCloud())) return false
  try {
    const api = await _getApi()
    if (!api) return false
    await api.reset()
    _pushCache = { key: '', promise: null }   // 重置后允许再次保存相同结果
    return true
  } catch (e) {
    console.warn('[personality] 云端重置失败（已降级为本地）:', e && e.message)
    return false
  }
}
