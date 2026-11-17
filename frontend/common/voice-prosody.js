/**
 * 语气起伏（Prosody）—— 让语音不再是平铺直叙的播音腔
 *
 * 背景：tts.js 里 rate/pitch 是常量，整段话一个语调念到底，听起来像机器。
 * 本模块做的是「分词 → 逐句给不同的语速/音高/停顿 → 按顺序播放」，
 * 让语气有起伏、有停顿、有情绪变化。
 *
 * 设计要点：
 * 1. 断句自然：按 。！？；，、…… 和换行切句，超长句再按逗号二次切分
 * 2. 句间停顿：句末标点决定停顿时长（感叹最短促、省略号最长）
 * 3. 情绪变化：happy 上扬轻快 / sad 下沉缓慢 / angry 短促 / quiet 气声慢
 * 4. 角色音色：voiceTone 决定基础音高（soft/warm/bright/cool/husky）
 * 5. 句内微扰：同一段里相邻句子的 rate/pitch 小幅抖动，避免"一马平川"
 *
 * 用法：
 *   import { speakExpressive } from '@/common/voice-prosody'
 *   speakExpressive('真的吗！我太开心了～', { emotion: 'happy', tone: 'bright' })
 *
 * 注意：本模块只做增强，不改动 tts.js 任何一行；tts.speak 仍然可用。
 */

import tts from '@/common/tts'

/** 情绪 -> 语速/音高/停顿的整体倾向 */
const EMOTION_PROFILE = {
  happy: { rate: 1.12, pitch: 1.15, pauseScale: 0.8, jitter: 0.06 },
  excited: { rate: 1.18, pitch: 1.2, pauseScale: 0.7, jitter: 0.08 },
  sad: { rate: 0.86, pitch: 0.84, pauseScale: 1.5, jitter: 0.04 },
  angry: { rate: 1.06, pitch: 0.92, pauseScale: 1.1, jitter: 0.07 },
  tired: { rate: 0.9, pitch: 0.88, pauseScale: 1.4, jitter: 0.03 },
  quiet: { rate: 0.88, pitch: 0.9, pauseScale: 1.6, jitter: 0.03 },
  gentle: { rate: 0.96, pitch: 0.98, pauseScale: 1.2, jitter: 0.04 },
  neutral: { rate: 1.0, pitch: 1.0, pauseScale: 1.0, jitter: 0.05 }
}

/** 角色音色 -> 基础参数（与后端 persona_service.VOICE_TONE_PARAMS 对齐） */
const TONE_PROFILE = {
  soft: { rate: 0.88, pitch: 0.95, volume: 0.9 },
  bright: { rate: 1.08, pitch: 1.18, volume: 1.0 },
  warm: { rate: 0.96, pitch: 0.92, volume: 0.95 },
  cool: { rate: 0.98, pitch: 0.85, volume: 0.9 },
  husky: { rate: 0.9, pitch: 0.72, volume: 0.95 }
}

/** 句末标点 -> 停顿毫秒（句间呼吸感的关键） */
const PAUSE_BY_END = {
  '。': 420, '！': 300, '!': 300, '？': 460, '?': 460,
  '；': 340, ';': 340, '，': 220, ',': 220, '、': 160,
  '…': 620, '~': 380, '～': 380, '\n': 360
}
const DEFAULT_PAUSE = 380

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v))
}

/** 把一段话切成"能一口气念完"的小段，并记住每段结尾是什么标点 */
export function splitSentences(text) {
  const raw = String(text == null ? '' : text).trim()
  if (!raw) return []

  const parts = []
  let buf = ''
  for (let i = 0; i < raw.length; i++) {
    const ch = raw[i]
    buf += ch
    const isBreak = '。！？；!?;\n'.indexOf(ch) >= 0
    const isComma = '，、,'.indexOf(ch) >= 0
    // 句末标点必须断；逗号在攒够 18 字后才断（避免把短句切碎）
    if (isBreak || (isComma && buf.length >= 18) || buf.length >= 42) {
      parts.push(buf)
      buf = ''
    }
  }
  if (buf.trim()) parts.push(buf)

  // 二次切分：仍过长的按逗号切
  const out = []
  parts.forEach(p => {
    if (p.length <= 42) { out.push(p); return }
    let b = ''
    for (let i = 0; i < p.length; i++) {
      b += p[i]
      if ('，、,'.indexOf(p[i]) >= 0 && b.length >= 14) { out.push(b); b = '' }
    }
    if (b.trim()) out.push(b)
  })
  return out.filter(x => x.trim())
}

function pauseFor(segment, pauseScale) {
  const last = segment.slice(-1)
  let base = PAUSE_BY_END[last]
  if (base === undefined) base = DEFAULT_PAUSE
  // 以省略号结尾给足留白
  if (/…+$/.test(segment)) base = 620
  return Math.round(base * pauseScale)
}

/**
 * 生成朗读计划（不发声，便于调试/字幕高亮）
 * @returns {Array<{text:string, rate:number, pitch:number, volume:number, pause:number}>}
 */
export function planProsody(text, opts = {}) {
  const emotion = EMOTION_PROFILE[opts.emotion] ? opts.emotion : 'neutral'
  const em = EMOTION_PROFILE[emotion]
  const tone = TONE_PROFILE[opts.tone] || (opts.toneParams) || TONE_PROFILE.warm

  // 用户在设置里调的全局语速/音高，作为整体倍率叠加（默认 1 = 不动）
  const globalRate = opts.rate || 1
  const globalPitch = opts.pitch || 1

  const segs = splitSentences(text)
  return segs.map((s, idx) => {
    // 句内微扰：奇偶句交替 + 位置衰减，让整段有起伏而不是一条直线
    const wave = (idx % 2 === 0 ? 1 : -1) * em.jitter
    const tail = idx === segs.length - 1 ? -0.04 : 0   // 最后一句略收，像说完一句话
    const exclaim = /[！!]/.test(s) ? 0.08 : 0
    const question = /[？?]/.test(s) ? 0.12 : 0         // 疑问尾音上扬

    return {
      text: s.trim(),
      rate: clamp((tone.rate * em.rate + wave + tail + exclaim) * globalRate, 0.5, 2),
      pitch: clamp((tone.pitch * em.pitch + wave * 0.6 + question) * globalPitch, 0, 2),
      volume: clamp(tone.volume == null ? 1 : tone.volume, 0, 1),
      pause: pauseFor(s, em.pauseScale)
    }
  })
}

/**
 * 带语气起伏地朗读
 * @param {string} text 要念的内容
 * @param {Object} opts
 *   - emotion: happy/sad/angry/tired/quiet/gentle/neutral
 *   - tone:    soft/bright/warm/cool/husky（角色音色）
 *   - lang:    语种，默认 zh-CN
 *   - onSegment(index, segment): 每念完一段回调（可用于通话字幕逐句高亮）
 *   - onDone(): 全部念完
 * @returns {boolean} 是否真的开始播了
 */
/**
 * 从文本里猜一个情绪（用于语音语气；猜不出来就 neutral）
 * 只是给 TTS 选语调用的轻量判断，不参与任何业务逻辑。
 */
export function detectEmotion(text) {
  const s = String(text == null ? '' : text)
  if (!s) return 'neutral'
  if (/(哈哈|嘿嘿|太好了|好开心|开心|喜欢|棒|耶|！{1,})/.test(s) && !/(难过|心疼|抱歉)/.test(s)) return 'happy'
  if (/(难过|心疼|抱歉|对不起|唉|委屈|想哭|孤独|失落)/.test(s)) return 'sad'
  if (/(生气|过分|凭什么|受不了|讨厌|气死)/.test(s)) return 'angry'
  if (/(好累|累了|疲惫|困|想睡|没力气)/.test(s)) return 'tired'
  if (/(陪着你|慢慢来|没关系|别急|我在|安心|晚安)/.test(s)) return 'quiet'
  if (/(温柔|轻轻|抱抱|放心)/.test(s)) return 'gentle'
  return 'neutral'
}

export function speakExpressive(text, opts = {}) {
  if (!tts.getEnabled()) return false
  if (typeof window === 'undefined' || !window.speechSynthesis ||
      typeof window.SpeechSynthesisUtterance !== 'function') return false

  const plan = planProsody(text, opts)
  if (!plan.length) return false

  try { window.speechSynthesis.cancel() } catch (e) { /* 静默 */ }

  let i = 0
  let stopped = false

  const playNext = () => {
    if (stopped || i >= plan.length) {
      if (!stopped && typeof opts.onDone === 'function') opts.onDone()
      return
    }
    const seg = plan[i]
    const idx = i

    const u = new window.SpeechSynthesisUtterance(seg.text)
    u.lang = opts.lang || 'zh-CN'
    u.rate = seg.rate
    u.pitch = seg.pitch
    u.volume = seg.volume

    let moved = false
    const advance = () => {
      if (moved) return
      moved = true
      if (typeof opts.onSegment === 'function') {
        try { opts.onSegment(idx, seg) } catch (e) { /* 静默 */ }
      }
      i += 1
      // 句间停顿：这就是"自然断句"的听感来源
      setTimeout(playNext, seg.pause)
    }

    u.onend = advance
    u.onerror = advance
    // 兜底：某些内核不触发 onend，按字数估算一个上限继续往下走
    setTimeout(advance, Math.max(1500, seg.text.length * 320 / seg.rate) + 2500)

    try { window.speechSynthesis.speak(u) } catch (e) { advance() }
  }

  playNext()

  // 记住停止句柄，stopExpressive() 可中断
  _stopFlag = () => { stopped = true }
  return true
}

let _stopFlag = null

export function stopExpressive() {
  if (_stopFlag) _stopFlag()
  _stopFlag = null
  try { window.speechSynthesis && window.speechSynthesis.cancel() } catch (e) { /* 静默 */ }
}

/** 给 UI 用：某情绪下这段大概要念多久（毫秒），用于通话字幕节奏 */
export function estimateDuration(text, opts = {}) {
  const plan = planProsody(text, opts)
  return plan.reduce((sum, s) => sum + s.text.length * 300 / s.rate + s.pause, 0)
}

export default {
  splitSentences,
  planProsody,
  detectEmotion,
  speakExpressive,
  stopExpressive,
  estimateDuration,
  EMOTION_PROFILE,
  TONE_PROFILE
}
