/**
 * 语音多语言配置（2026-10-26 新增）
 *
 * 背景：聊天设置面板里早就有「🌐 语音多语言」五个语种，但只有 UI —— 点了既不会保存，
 *      也不会影响任何一路发声（AI 回复永远是中文，语音通话 TTS 硬编码 zh-CN）。
 * 目标：一处配置，四处生效 —— TTS 播报 / 语音识别(ASR) / AI 回复语种 / 语音通话。
 *
 * 设计原则（零破坏）：
 *   - 本模块是"纯配置 + 纯函数"，不 import 任何业务模块，不产生副作用；
 *   - 所有取用函数都带默认值兜底：传了非法 code 一律降级为中文，绝不抛错；
 *   - 非 H5 环境（小程序/App）没有 window.speechSynthesis，检测函数返回 null，调用方自行跳过。
 */

/** 语种表：code 用 BCP-47，与 SpeechSynthesisUtterance.lang / WebSpeechRecognition.lang 对齐 */
export const VOICE_LANGS = [
  {
    code: 'zh-CN',
    name: '中文',
    en: 'Chinese',
    flag: '🇨🇳',
    // 语音识别语种（Web Speech API Recognition.lang）
    asr: 'zh-CN',
    // 试听文本：点语种后立即念一句，让用户"听得见"切换结果
    sample: '你好呀，今天也一起慢慢加油吧。',
    // 注入给大模型 system prompt 的语种指令
    directive: '请全程使用简体中文回复，语气自然口语化。',
    // 离线兜底回复（本地规则引擎只会中文，非中文语种时至少给出对应语种的短句）
    offlineReplies: [
      '嗯嗯，我在听呢，慢慢说就好。',
      '好的，我记住啦，我们一起加油。',
      '听起来不容易呢，我陪着你。'
    ],
    // 语音通话轮播台词（voice-call 组件原来写死中文，切语种后仍是中文腔）
    callLines: [
      '喂？听得到吗？',
      '你今天的声音听起来心情不错哦。',
      '哈哈，被你发现了，我也很喜欢和你打电话。',
      '对了，今天的习惯打卡别忘了呀。',
      '跟你打电话的时间过得好快。',
      '安静听你说就好，我都在。',
      '下次一起去散步吧，就我们俩。',
      '嗯嗯，然后呢？继续说～'
    ],
    // 系统语音匹配用别名（不同浏览器报的 lang 写法不一致）
    aliases: ['zh', 'zh_CN', 'zh-Hans', 'cmn', 'cmn-Hans-CN', 'zh-CN']
  },
  {
    code: 'en-US',
    name: 'English',
    en: 'English',
    flag: '🇺🇸',
    asr: 'en-US',
    sample: "Hello there! I'm here with you, take your time.",
    directive: 'Please reply entirely in natural, conversational English.',
    offlineReplies: [
      "I'm listening, take your time.",
      "Got it — we'll figure this out together.",
      "That sounds tough. I'm here with you."
    ],
    callLines: [
      'Hello? Can you hear me?',
      "You sound like you're in a good mood today.",
      'Haha, you caught me — I love talking with you too.',
      "Oh, don't forget today's habit check-in.",
      'Time flies when we talk like this.',
      "I'm right here, just listening.",
      "Let's go for a walk together next time, just us two.",
      'Mm hm, and then? Keep going~'
    ],
    aliases: ['en', 'en_US', 'en-GB', 'en-AU']
  },
  {
    code: 'ja-JP',
    name: '日本語',
    en: 'Japanese',
    flag: '🇯🇵',
    asr: 'ja-JP',
    sample: 'こんにちは。ゆっくりで大丈夫だよ、一緒に頑張ろう。',
    directive: '必ず自然な日本語で返信してください（丁寧すぎない、話し言葉）。',
    offlineReplies: [
      'うんうん、聞いてるよ。ゆっくりで大丈夫。',
      'わかった、一緒に考えようね。',
      '大変だったね、そばにいるよ。'
    ],
    callLines: [
      'もしもし？聞こえてる？',
      '今日の声、なんか楽しそうだね。',
      'はは、バレた。私も電話好きだよ。',
      'そうだ、今日の習慣の打卡（チェックイン）忘れないでね。',
      '電話してると時間が経つの早いね。',
      '静かに聞いてるだけでも、私はここにいるよ。',
      '今度一緒に散歩しよう、二人で。',
      'うんうん、それで？続きを聞かせて～'
    ],
    aliases: ['ja', 'ja_JP', 'jp']
  },
  {
    code: 'ko-KR',
    name: '한국어',
    en: 'Korean',
    flag: '🇰🇷',
    asr: 'ko-KR',
    sample: '안녕하세요. 천천히 해도 괜찮아요, 같이 해봐요.',
    directive: '반드시 자연스러운 한국어(구어체)로 답변해 주세요.',
    offlineReplies: [
      '응응, 듣고 있어. 천천히 해도 괜찮아.',
      '알았어, 같이 생각해 보자.',
      '힘들었겠다. 내가 옆에 있을게.'
    ],
    callLines: [
      '여보세요? 들려?',
      '오늘 목소리 톤이 기분 좋아 보이네.',
      '하하, 들켰네. 나도 너랑 통화하는 거 좋아해.',
      '그런데, 오늘 습관 체크인 잊지 마.',
      '너랑 통화하면 시간이 진짜 빨리 가.',
      '가만히 듣고만 있어도, 나는 여기 있어.',
      '다음엔 같이 산책하자, 우리 둘이서.',
      '응응, 그리고? 계속 말해 봐~'
    ],
    aliases: ['ko', 'ko_KR', 'kr']
  },
  {
    code: 'fr-FR',
    name: 'Français',
    en: 'French',
    flag: '🇫🇷',
    asr: 'fr-FR',
    sample: "Bonjour ! Je suis là avec toi, prends ton temps.",
    directive: 'Réponds entièrement en français naturel et courant (pas trop formel).',
    offlineReplies: [
      "Je t'écoute, prends ton temps.",
      "C'est noté, on va avancer ensemble.",
      "Ça n'a pas l'air facile. Je suis là."
    ],
    callLines: [
      'Allô ? Tu m’entends ?',
      'Ta voix a l’air en forme aujourd’hui.',
      'Haha, tu m’as eue — j’adore te parler aussi.',
      'Au fait, n’oublie pas ta check-list d’habitudes du jour.',
      'Le temps passe trop vite quand on se parle.',
      'Je suis là, même juste pour t’écouter.',
      'On ira se promener ensemble la prochaine fois, rien que nous deux.',
      'Hmm, et alors ? Continue~'
    ],
    aliases: ['fr', 'fr_FR', 'fr-CA']
  }
]

export const DEFAULT_VOICE_LANG = 'zh-CN'

/** 李克特量表无关；这里是给设置面板/其他页面复用同一份语种列表 */
export function getVoiceLangs() {
  return VOICE_LANGS
}

/** 取语种配置（非法/未传一律降级中文） */
export function getVoiceLang(code) {
  const hit = VOICE_LANGS.find(l => l.code === code)
  if (hit) return hit
  // 宽松匹配：en-US 传成 en、zh_CN 传成 zh-CN 之类
  const lower = String(code || '').toLowerCase().replace('_', '-')
  const loose = VOICE_LANGS.find(l => l.aliases.some(a => a.toLowerCase() === lower))
  return loose || VOICE_LANGS[0]
}

/** 归一化语种 code（非法值返回默认中文） */
export function normalizeVoiceLang(code) {
  return getVoiceLang(code).code
}

/** 取语音识别语种（ASR） */
export function getAsrLang(code) {
  return getVoiceLang(code).asr || DEFAULT_VOICE_LANG
}

/** 取试听文本 */
export function getSampleText(code) {
  return getVoiceLang(code).sample
}

/** 取注入给大模型的语种指令；中文时返回空串（不污染原 prompt，保持零破坏） */
export function getLanguageDirective(code) {
  const lang = getVoiceLang(code)
  if (lang.code === DEFAULT_VOICE_LANG) return ''
  return lang.directive
}

/** 离线兜底：本地规则引擎只有中文语料，非中文语种时按语种返回一句对应语言的话 */
export function pickOfflineReply(code) {
  return pickFromPool(code, 'offlineReplies')
}

/** 语音通话轮播台词（按当前语种取，避免"选了 English 仍念中文"） */
export function getCallLines(code) {
  const lang = getVoiceLang(code)
  const pool = lang.callLines || []
  return pool.length ? pool : getVoiceLang(DEFAULT_VOICE_LANG).callLines
}

function pickFromPool(code, field) {
  const lang = getVoiceLang(code)
  const pool = lang[field] || []
  if (!pool.length) return ''
  return pool[Math.floor(Math.random() * pool.length)]
}

/* ============================================================
 * 系统语音（TTS voice）匹配
 * ============================================================ */

/**
 * 在系统已安装的语音里挑一个最合适的
 * 优先级：完全相等 > 主语言前缀（zh / en）> 别名前缀 > null（交给浏览器按 lang 兜底）
 * @param {string} code 语种 code
 * @param {Array} voices window.speechSynthesis.getVoices() 的结果
 */
export function matchSystemVoice(code, voices) {
  const lang = getVoiceLang(code)
  const list = Array.isArray(voices) ? voices : []
  if (!list.length) return null

  const norm = (s) => String(s || '').toLowerCase().replace('_', '-')
  const target = norm(lang.code)
  const primary = target.split('-')[0]

  // 1) 完全相等（zh-CN / en-US ...）
  let hit = list.find(v => norm(v.lang) === target)
  if (hit) return hit

  // 2) 主语言前缀（zh / en / ja / ko / fr），但排除明显不同地区的口音优先？不排除，取第一个
  hit = list.find(v => norm(v.lang).split('-')[0] === primary)
  if (hit) return hit

  // 3) 别名前缀
  for (const alias of lang.aliases) {
    const a = norm(alias).split('-')[0]
    hit = list.find(v => norm(v.lang).split('-')[0] === a)
    if (hit) return hit
  }
  return null
}

/**
 * 当前环境是否安装了该语种的语音包（H5 专用）
 * - 拿不到 voices / 非 H5：返回 null（未知，不要误报"不支持"）
 * - 能拿到列表：严格判断
 */
export function isVoiceLangSupported(code, voices) {
  // #ifdef H5
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return false
  const list = (typeof voices !== 'undefined' && voices) ? voices : window.speechSynthesis.getVoices()
  if (!list || !list.length) return null
  return !!matchSystemVoice(code, list)
  // #endif
  // #ifndef H5
  return null
  // #endif
}

/** 供 UI 展示的"支持状态文案" */
export function describeSupport(code) {
  const state = isVoiceLangSupported(code)
  const lang = getVoiceLang(code)
  if (state === null) return `${lang.flag} ${lang.name}`
  if (state === false) return `${lang.flag} ${lang.name} · 系统缺语音包`
  return `${lang.flag} ${lang.name}`
}

export default {
  VOICE_LANGS,
  DEFAULT_VOICE_LANG,
  getVoiceLangs,
  getVoiceLang,
  normalizeVoiceLang,
  getAsrLang,
  getSampleText,
  getLanguageDirective,
  pickOfflineReply,
  getCallLines,
  matchSystemVoice,
  isVoiceLangSupported,
  describeSupport
}
