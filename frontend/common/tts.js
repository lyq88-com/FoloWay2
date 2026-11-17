/**
 * H5 语音播报（TTS）
 *
 * 用浏览器原生 Web Speech API 实现，不引入任何依赖、不需要后端。
 * settings 页本来就有一个「语音播报」开关（ttsEnabled），但之前只是存了个布尔值，
 * 没有任何地方真正发声——本模块补上这一段。
 *
 * 平台差异：
 *   - H5：可用（Chrome / Edge / Safari 都支持 speechSynthesis）
 *   - App / 小程序：window.speechSynthesis 不存在 → isSupported() 返回 false，
 *     所有调用静默返回 false，行为与接入前完全一致
 *
 * 用法：
 *   import tts from '@/common/tts'
 *   tts.setEnabled(true)
 *   tts.speak('你好呀')      // 受开关控制，关着就不播
 *   tts.stop()
 */

const STORAGE_KEY = 'settings_tts_enabled'
const MAX_LEN = 300          // 太长念起来难受，截断

let enabled = true
let initialized = false

function isSupported() {
  try {
    return typeof window !== 'undefined' && !!window.speechSynthesis &&
      typeof window.SpeechSynthesisUtterance === 'function'
  } catch (e) {
    return false
  }
}

function loadEnabled() {
  try {
    const v = uni.getStorageSync(STORAGE_KEY)
    // 没存过就默认开启，与 settings.vue 里 ttsEnabled 的初始值 true 保持一致
    enabled = (v === undefined || v === null || v === '') ? true : (v === true || v === 'true' || v === 1 || v === '1')
  } catch (e) {
    enabled = true
  }
  initialized = true
  return enabled
}

function getEnabled() {
  if (!initialized) loadEnabled()
  return enabled
}

function setEnabled(v) {
  enabled = !!v
  try {
    uni.setStorageSync(STORAGE_KEY, enabled ? 'true' : 'false')
  } catch (e) { /* 静默 */ }
  if (!enabled) stop()
  return enabled
}

/** 播报一段文本；返回是否真的播了 */
function speak(text, opts) {
  if (!getEnabled()) return false
  if (!isSupported()) return false

  const raw = String(text == null ? '' : text).trim()
  if (!raw) return false

  try {
    stop()                                  // 新句子打断上一句，避免排队念个不停
    const u = new window.SpeechSynthesisUtterance(raw.slice(0, MAX_LEN))
    u.lang = (opts && opts.lang) || 'zh-CN'
    u.rate = (opts && opts.rate) || 1
    u.pitch = (opts && opts.pitch) || 1
    u.volume = (opts && opts.volume) || 1
    // iOS/Chrome 的一个老问题：不挂引用，某些情况下会被 GC 掉导致播到一半停
    lastUtterance = u
    u.onend = () => { lastUtterance = null }
    u.onerror = () => { lastUtterance = null }
    window.speechSynthesis.speak(u)
    return true
  } catch (e) {
    return false
  }
}

let lastUtterance = null

function stop() {
  if (!isSupported()) return false
  try {
    window.speechSynthesis.cancel()
    lastUtterance = null
    return true
  } catch (e) {
    return false
  }
}

export default {
  isSupported,
  getEnabled,
  setEnabled,
  speak,
  stop
}
