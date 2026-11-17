/**
 * 循途 · AI音乐模块（Web Audio 实现的轻量音乐引擎）
 * ------------------------------------------------------------
 * 1. 哄睡安眠曲：柔和的五声音阶摇篮曲循环，可定时渐弱停止
 * 2. AI角色唱歌：旋律 + 歌词TTS同步，模拟AI伙伴演唱
 * 3. 通用音符序列播放器
 *
 * 说明：使用浏览器 Web Audio API 直接合成，无需音频资源文件；
 * 非 H5 环境下降级为静默（返回 false），不影响页面其他功能。
 */

let audioCtx = null
let activeNodes = []
let stopTimer = null

function getCtx() {
  // #ifdef H5
  if (typeof window === 'undefined') return null
  const AC = window.AudioContext || window.webkitAudioContext
  if (!AC) return null
  if (!audioCtx) audioCtx = new AC()
  if (audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {})
  }
  return audioCtx
  // #endif
  // #ifndef H5
  return null
  // #endif
}

/**
 * 播放单个音符
 * @param {Number} freq - 频率 Hz
 * @param {Number} startAt - 开始时间（AudioContext时间）
 * @param {Number} duration - 时长秒
 * @param {String} type - 波形 sine/triangle
 * @param {Number} volume - 音量 0-1
 */
function playNote(freq, startAt, duration, type = 'sine', volume = 0.18) {
  const ctx = getCtx()
  if (!ctx) return
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = type
  osc.frequency.value = freq
  gain.gain.setValueAtTime(0, startAt)
  gain.gain.linearRampToValueAtTime(volume, startAt + 0.05)
  gain.gain.exponentialRampToValueAtTime(0.001, startAt + duration)
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(startAt)
  osc.stop(startAt + duration + 0.05)
  activeNodes.push(osc)
}

/** 音名转频率（C4=60） */
export function noteToFreq(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

/**
 * 播放音符序列
 * @param {Array} notes - [{ midi, beat, type?, volume? }]，beat为拍数
 * @param {Number} bpm - 每分钟拍数
 * @param {Object} opts - { loop }
 */
export function playSequence(notes, bpm = 72, opts = {}) {
  stopMusic()
  const ctx = getCtx()
  if (!ctx) return false
  const beatSec = 60 / bpm
  let t = ctx.currentTime + 0.1
  notes.forEach(n => {
    const dur = n.beat * beatSec
    playNote(noteToFreq(n.midi), t, dur * 0.95, n.type || 'sine', n.volume || 0.18)
    t += dur
  })
  if (opts.loop) {
    const totalMs = (t - ctx.currentTime) * 1000
    stopTimer = setTimeout(() => playSequence(notes, bpm, opts), totalMs)
  }
  return true
}

/** 停止所有音乐 */
export function stopMusic() {
  if (stopTimer) {
    clearTimeout(stopTimer)
    stopTimer = null
  }
  activeNodes.forEach(osc => {
    try { osc.stop() } catch (e) { /* 已停止 */ }
  })
  activeNodes = []
}

/** 是否正在播放 */
export function isPlaying() {
  return stopTimer !== null || activeNodes.length > 0
}

/** 安眠曲：五声音阶摇篮曲（循环） */
const LULLABY_NOTES = [
  { midi: 72, beat: 1 }, { midi: 74, beat: 1 }, { midi: 76, beat: 2 },
  { midi: 74, beat: 1 }, { midi: 72, beat: 1 }, { midi: 69, beat: 2 },
  { midi: 72, beat: 1 }, { midi: 76, beat: 1 }, { midi: 79, beat: 2 },
  { midi: 76, beat: 1 }, { midi: 74, beat: 1 }, { midi: 72, beat: 4 },
  { midi: 69, beat: 1 }, { midi: 72, beat: 1 }, { midi: 74, beat: 2 },
  { midi: 72, beat: 1 }, { midi: 69, beat: 1 }, { midi: 67, beat: 4 },
  { midi: 72, beat: 1 }, { midi: 74, beat: 1 }, { midi: 76, beat: 2 },
  { midi: 79, beat: 1 }, { midi: 76, beat: 1 }, { midi: 74, beat: 4 }
]

export function playLullaby() {
  return playSequence(LULLABY_NOTES, 56, { loop: true })
}

/**
 * AI唱歌：播放一段欢快旋律
 * @param {Function} onLyric - 每句歌词回调（与旋律大致同步）
 */
export async function playSong(onLyric) {
  stopMusic()
  const ctx = getCtx()
  if (!ctx) return false
  const SONG_NOTES = [
    { midi: 69, beat: 0.5 }, { midi: 71, beat: 0.5 }, { midi: 73, beat: 1 },
    { midi: 76, beat: 1 }, { midi: 73, beat: 1 }, { midi: 71, beat: 0.5 },
    { midi: 69, beat: 0.5 }, { midi: 66, beat: 2 },
    { midi: 68, beat: 0.5 }, { midi: 69, beat: 0.5 }, { midi: 71, beat: 1 },
    { midi: 73, beat: 1 }, { midi: 71, beat: 1 }, { midi: 69, beat: 0.5 },
    { midi: 68, beat: 0.5 }, { midi: 64, beat: 2 }
  ]
  const lyrics = [
    '🎵 一起去嘛 去看樱花落下～',
    '🎵 把烦恼都 藏进晚霞～',
    '🎵 你笑起来 像春天的芽～',
    '🎵 有你在的每天 都在发光呀～'
  ]
  const bpm = 96
  const beatSec = 60 / bpm
  // 歌词节奏：第2、6、10、14个音符处
  const lyricAtBeats = [1.5, 5.5, 9.5, 13.5]

  playSequence(SONG_NOTES, bpm, { loop: false })

  if (typeof onLyric === 'function') {
    lyricAtBeats.forEach((beats, i) => {
      setTimeout(() => {
        try { onLyric(lyrics[i] || '') } catch (e) { /* 静默 */ }
      }, beats * beatSec * 1000)
    })
  }
  // 总时长后停止标记
  const totalBeats = SONG_NOTES.reduce((s, n) => s + n.beat, 0)
  setTimeout(() => { stopMusic() }, totalBeats * beatSec * 1000 + 500)
  return true
}

export default {
  playLullaby,
  playSong,
  playSequence,
  stopMusic,
  isPlaying
}
