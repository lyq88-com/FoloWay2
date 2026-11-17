/**
 * 主题管理模块 v2
 * 功能：浅色/深色/自动3主题切换 + 亮度 0-100% + storage 持久化 + 空值边界保护
 */

export const themes = {
  light: {
    name: '浅色主题',
    'bg-color': '#F8F9FA',
    'bg-card': '#FFFFFF',
    'bg-secondary': '#F0F2F5',
    'bg-mask': 'rgba(0, 0, 0, 0.5)',
    'text-primary': '#333333',
    'text-secondary': '#8f8f94',
    'text-light': '#999999',
    'border-color': '#E8E8E8',
    'nav-bg': '#FFFFFF',
    'nav-text': '#333333',
    'tab-bar-bg': '#FFFFFF',
    'primary-color': '#6B8E7B',
    'primary-light': '#A8C9B8',
    'success-color': '#6B8E7B',
    'warning-color': '#FFD93D',
    'danger-color': '#FF6B6B',
    'shadow-sm': '0 2rpx 8rpx rgba(0, 0, 0, 0.04)',
    'shadow-md': '0 4rpx 16rpx rgba(0, 0, 0, 0.08)',
    'shadow-lg': '0 12rpx 48rpx rgba(0, 0, 0, 0.12)',
    'radius-sm': '12rpx',
    'radius-md': '20rpx',
    'radius-lg': '32rpx',
    'anim-fast': '200ms',
    'anim-normal': '300ms',
    'anim-slow': '500ms',
    'ease-smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
    'ease-spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)'
  },
  dark: {
    name: '深色主题',
    'bg-color': '#1A1A2E',
    'bg-card': '#16213E',
    'bg-secondary': '#0F1626',
    'bg-mask': 'rgba(0, 0, 0, 0.7)',
    'text-primary': '#FFFFFF',
    'text-secondary': '#A0A0B0',
    'text-light': '#6B6B80',
    'border-color': '#2A2A4A',
    'nav-bg': '#16213E',
    'nav-text': '#FFFFFF',
    'tab-bar-bg': '#16213E',
    'primary-color': '#7BC49F',
    'primary-light': '#5A9E7E',
    'success-color': '#7BC49F',
    'warning-color': '#FFD93D',
    'danger-color': '#FF6B6B',
    'shadow-sm': '0 2rpx 8rpx rgba(0, 0, 0, 0.3)',
    'shadow-md': '0 4rpx 16rpx rgba(0, 0, 0, 0.4)',
    'shadow-lg': '0 12rpx 48rpx rgba(0, 0, 0, 0.5)',
    'radius-sm': '12rpx',
    'radius-md': '20rpx',
    'radius-lg': '32rpx',
    'anim-fast': '200ms',
    'anim-normal': '300ms',
    'anim-slow': '500ms',
    'ease-smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
    'ease-spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)'
  }
}

const APP_THEME_KEY = 'app_theme'            // 'light' | 'dark'
const AUTO_MODE_KEY = 'auto_theme_mode'     // 'auto' | 'manual'
const AUTO_LAST_CHECK = 'auto_theme_last_check'
const BRIGHTNESS_KEY = 'screen_brightness_v2' // 0 - 100

function safeGetStorage(key, fallback) {
  try {
    const v = uni.getStorageSync(key)
    return (v === '' || v === undefined || v === null) ? fallback : v
  } catch (e) {
    console.warn('[theme] safeGetStorage fail', key, e)
    return fallback
  }
}

function safeSetStorage(key, value) {
  try {
    uni.setStorageSync(key, value)
  } catch (e) {
    console.warn('[theme] safeSetStorage fail', key, e)
  }
}

/**
 * 根据当前时间判断自动模式下的主题
 */
function getTimeBasedTheme() {
  try {
    const hour = new Date().getHours()
    const sunriseHour = 6
    const sunsetHour = 19
    return hour >= sunriseHour && hour < sunsetHour ? 'light' : 'dark'
  } catch (e) {
    return 'light'
  }
}

/**
 * 检查自动模式：是否需要切换主题
 * 返回需要切换的主题名，或 null 表示无需切换
 */
export function checkAutoTheme() {
  try {
    if (!isAutoMode()) return null
    const now = Date.now()
    const lastCheck = Number(safeGetStorage(AUTO_LAST_CHECK, 0)) || 0
    const hourMs = 60 * 60 * 1000
    if (now - lastCheck < hourMs) return null

    const newTheme = getTimeBasedTheme()
    const current = getCurrentTheme()
    if (newTheme !== current) {
      safeSetStorage(AUTO_LAST_CHECK, now)
      return newTheme
    }
    return null
  } catch (e) {
    console.warn('[theme] checkAutoTheme fail', e)
    return null
  }
}

/**
 * 应用主题 + 亮度 + 数据驱动深/浅背景 + 导航栏颜色
 */
export function applyTheme(themeName, brightnessPct) {
  try {
    // 兼容空值/未知主题，回退浅色
    const safeThemeName = (themes && themes[themeName]) ? themeName : 'light'
    const theme = themes[safeThemeName] || themes.light
    if (!theme) return

    // 亮度（0-100）→ 10%~100% 的视觉缩放
    let bPct = brightnessPct
    if (bPct === undefined || bPct === null) bPct = getBrightness()
    bPct = Number(bPct)
    if (isNaN(bPct)) bPct = 80
    if (bPct < 0) bPct = 0
    if (bPct > 100) bPct = 100
    // 亮度系数：100% → 1.0；最低 10% → 0.35 避免完全黑屏
    const brightnessMul = 0.35 + (bPct / 100) * 0.65

    // 应用到 DOM（H5）
    if (typeof document !== 'undefined') {
      const root = document.documentElement
      const page = document.querySelector ? document.querySelector('page') : null

      // 写入所有 CSS 变量 + 叠加亮度
      const applyVars = (el) => {
        if (!el) return
        try {
          el.setAttribute('data-theme', safeThemeName)
          Object.keys(theme).forEach(key => {
            const raw = theme[key]
            let finalVal = raw
            // 对背景类变量叠加亮度（混合黑/白）
            if (typeof raw === 'string' && (raw.startsWith('#') || raw.startsWith('rgb'))) {
              if (key.startsWith('bg-') || key.includes('-bg')) {
                finalVal = mixWithBrightness(raw, brightnessMul, safeThemeName === 'dark')
              }
            }
            el.style.setProperty(`--${key}`, finalVal)
          })
          el.style.setProperty('--screen-brightness', String(bPct / 100))
        } catch (e) {
          console.warn('[theme] applyVars fail', e)
        }
      }

      applyVars(root)
      applyVars(page)

      // body/page 亮度遮罩（不影响布局）
      try {
        if (root) {
          root.style.filter = `brightness(${brightnessMul.toFixed(3)})`
        }
      } catch (e) {
        console.warn('[theme] brightness overlay fail', e)
      }
    }

    // 设置导航栏（uni 原生）
    try {
      uni.setNavigationBarColor({
        frontColor: safeThemeName === 'dark' ? '#ffffff' : '#000000',
        backgroundColor: theme['nav-bg'] || '#FFFFFF'
      })
    } catch (e) {
      console.warn('[theme] setNavigationBarColor fail', e)
    }

    // 设备亮度（仅 App 端生效；H5 端 fallback 到 CSS filter）
    try {
      if (uni.setScreenBrightness) {
        uni.setScreenBrightness({ value: bPct / 100 })
      }
    } catch (e) {
      // H5 端不支持，忽略
    }

    // 持久化（仅当明确传入主题名时覆盖；亮度始终更新）
    if (themeName) safeSetStorage(APP_THEME_KEY, safeThemeName)
    if (brightnessPct !== undefined && brightnessPct !== null) safeSetStorage(BRIGHTNESS_KEY, String(bPct))

    // 触发全局 theme 变更事件（跨组件通知）
    try {
      uni.$emit('theme-changed', { theme: safeThemeName, brightness: bPct })
    } catch (e) {}

    return safeThemeName
  } catch (e) {
    console.error('[theme] applyTheme fail', e)
    return 'light'
  }
}

/**
 * 将 #RGB/#RRGGBB/rgb(a) 与亮度系数叠加（近似：按比例混合黑/白）
 */
function mixWithBrightness(color, mul, isDark) {
  try {
    if (typeof color !== 'string') return color
    let rgb = parseColor(color)
    if (!rgb) return color

    // 暗色模式：亮度减小 -> 叠加黑色（向 0,0,0 走）；亮色模式：反之
    if (isDark) {
      rgb.r = Math.round(rgb.r * mul)
      rgb.g = Math.round(rgb.g * mul)
      rgb.b = Math.round(rgb.b * mul)
    } else {
      // 亮色模式：亮度低 = 变暗
      rgb.r = Math.min(255, Math.round(rgb.r * mul))
      rgb.g = Math.min(255, Math.round(rgb.g * mul))
      rgb.b = Math.min(255, Math.round(rgb.b * mul))
    }
    return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`
  } catch (e) {
    return color
  }
}

function parseColor(c) {
  if (!c) return null
  c = c.trim()
  if (c.startsWith('#')) {
    if (c.length === 4) {
      const r = c[1], g = c[2], b = c[3]
      return { r: parseInt(r + r, 16), g: parseInt(g + g, 16), b: parseInt(b + b, 16) }
    }
    if (c.length === 7) {
      return {
        r: parseInt(c.substr(1, 2), 16),
        g: parseInt(c.substr(3, 2), 16),
        b: parseInt(c.substr(5, 2), 16)
      }
    }
    return null
  }
  if (c.startsWith('rgb')) {
    const m = c.match(/rgba?\(([^)]+)\)/)
    if (!m) return null
    const parts = m[1].split(',').map(s => parseInt(s.trim(), 10))
    return { r: parts[0] || 0, g: parts[1] || 0, b: parts[2] || 0 }
  }
  return null
}

/* ============== 读写工具函数 ============== */

export function getCurrentTheme() {
  try {
    const saved = safeGetStorage(APP_THEME_KEY, '')
    if (saved === 'dark' || saved === 'light') return saved
    // 空值默认浅色（边界保护）
    return 'light'
  } catch (e) {
    return 'light'
  }
}

export function getTheme() {
  const n = getCurrentTheme()
  return themes[n] || themes.light
}

export function getThemeValue(key, defaultValue) {
  try {
    const theme = getTheme()
    if (!theme) return defaultValue
    return theme[key] !== undefined ? theme[key] : defaultValue
  } catch (e) {
    return defaultValue
  }
}

export function isAutoMode() {
  try {
    return safeGetStorage(AUTO_MODE_KEY, 'manual') === 'auto'
  } catch (e) {
    return false
  }
}

export function setAutoMode(enabled) {
  try {
    safeSetStorage(AUTO_MODE_KEY, enabled ? 'auto' : 'manual')
    if (enabled) {
      const now = getTimeBasedTheme()
      applyTheme(now)
    }
  } catch (e) {
    console.warn('[theme] setAutoMode fail', e)
  }
}

export function getBrightness() {
  try {
    const v = Number(safeGetStorage(BRIGHTNESS_KEY, '80'))
    if (isNaN(v)) return 80
    if (v < 0) return 0
    if (v > 100) return 100
    return v
  } catch (e) {
    return 80
  }
}

export function setBrightness(pct) {
  try {
    let v = Number(pct)
    if (isNaN(v)) v = 80
    if (v < 0) v = 0
    if (v > 100) v = 100
    applyTheme(getCurrentTheme(), v)
    return v
  } catch (e) {
    return 80
  }
}

/**
 * 启动时一次性初始化（App.vue onLaunch 调用）
 * 自动：按时间；手动：按 storage 里主题；全部走 applyTheme 带亮度写入 CSS 变量
 */
export function initTheme() {
  try {
    let themeName
    if (isAutoMode()) {
      themeName = getTimeBasedTheme()
    } else {
      themeName = getCurrentTheme()
    }
    const b = getBrightness()
    applyTheme(themeName, b)
  } catch (e) {
    console.error('[theme] initTheme fail', e)
    // 兜底
    applyTheme('light', 80)
  }
}

// 兼容旧模块（保留名称，避免其他 import 破坏）
export const lightEffects = { day: { name: '白天', gradient: '' } }
export function getTimeBasedLightEffect() { return 'day' }
export function getLightOpacity() { return 0 }
export function setLightOpacity() { return 0 }
export function getLightEffectConfig() { return {} }
