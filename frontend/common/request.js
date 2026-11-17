import store from '@/store'
import { getCache, setCache, clearCache, invalidateCache } from './cache'

// ============ 接口 / 静态资源基础地址 ============
// ↓↓↓ 修复 ↓↓↓ 原来 H5 与 App 两套地址直接写在本文件，且非 H5 分支硬编码
// http://172.20.10.3:8000 —— 换 WiFi 后真机全部连不上，还要记得同时改两处。
// 现在统一从 common/env.js 取（那里是全项目 IP 的唯一出处）：
//   - H5:   相对路径，走 vite devServer proxy 转发到 127.0.0.1:8000（不经局域网，IP 再变也不影响）
//   - App:  局域网绝对地址，换网络时跑 tools/sync-lan-host.js（或 .bat）一键更新
import { API_BASE, STATIC_BASE } from './env'

const BASE_URL = API_BASE

/**
 * 把接口返回的相对 path（avatar/xxx.jpg）或绝对 URL 转成可直接给 <image src> 用的地址
 * 传入已是 http(s) 开头的原样返回，避免二次拼接
 */
function toStaticUrl(pathOrUrl) {
  if (!pathOrUrl) return ''
  const s = String(pathOrUrl)
  if (s.startsWith('blob:') || s.startsWith('data:')) return s  // 本地临时图片，照原样用
  // 后端返回的是带硬编码局域网 IP 的绝对地址（http://172.20.10.3:8000/uploads/avatar/x.png），
  // 只保留 /uploads/ 之后的部分，再用当前环境前缀拼 —— 换 WiFi 后图片才不会全挂
  const idx = s.indexOf('/uploads/')
  if (idx >= 0) return STATIC_BASE + '/' + s.slice(idx + '/uploads/'.length)
  if (/^https?:\/\//.test(s)) return s
  return STATIC_BASE + '/' + s.replace(/^\/+/, '')
}

/**
 * 用户头像专用解析器【新增】
 * 接口返回的可能是相对路径（avatar/xxx.png）、带硬编码 IP 的绝对 URL，也可能压根没有头像。
 * 另外 choosImage 拿到的本地临时地址（blob: / wxfile://）刷新即失效，这里直接按「无头像」处理，
 * 好让页面回退到首字母占位，而不是显示一张裂图。
 * 拿不到有效头像时返回空串，调用方用 v-if 判断是否渲染 <image>。
 */
function toAvatarUrl(raw) {
  if (!raw) return ''
  const s = String(raw)
  if (/^(blob:|data:image|wxfile:)/.test(s)) return ''
  return toStaticUrl(s)
}

const MAX_RETRY = 2
const RETRY_DELAY = 1000
const DEFAULT_TIMEOUT = 20000

let isNetworkAvailable = true

// 网络恢复回调队列
const networkRecoveryCallbacks = []

function checkNetwork() {
  uni.getNetworkType({
    success: (res) => {
      isNetworkAvailable = res.networkType !== 'none'
    },
    fail: () => {
      isNetworkAvailable = false
    }
  })
}

checkNetwork()

uni.onNetworkStatusChange((res) => {
  const wasOffline = !isNetworkAvailable
  isNetworkAvailable = res.isConnected

  if (!res.isConnected) {
    uni.showToast({ title: '网络已断开', icon: 'none', duration: 3000 })
  } else if (wasOffline && res.isConnected) {
    // 网络恢复: 通知所有注册的回调
    uni.showToast({ title: '网络已恢复', icon: 'success', duration: 2000 })
    networkRecoveryCallbacks.forEach(cb => {
      try { cb() } catch (e) { /* 静默 */ }
    })
  }
})

/**
 * 注册网络恢复回调
 * @param {function} callback - 网络恢复时执行的函数
 * @returns {function} 取消注册函数
 */
function onNetworkRecovery(callback) {
  networkRecoveryCallbacks.push(callback)
  return () => {
    const idx = networkRecoveryCallbacks.indexOf(callback)
    if (idx > -1) networkRecoveryCallbacks.splice(idx, 1)
  }
}

function parseValidationError(data) {
  if (!data) return '数据验证失败'
  if (data.detail && Array.isArray(data.detail)) {
    const msgs = data.detail.map(d => d.msg).filter(Boolean)
    if (msgs.length > 0) {
      return msgs.join('；')
    }
  }
  if (data.error) {
    if (data.error.message) return data.error.message
    if (data.error.details) return data.error.details.join('；')
  }
  return data.detail || data.message || '数据验证失败'
}

function handleHttpError(statusCode, data) {
  // 兼容两种后端错误格式：
  //   FastAPI:  { detail: '...' | [{msg}], error: { message } }
  //   Flask:    { code, message, data }   ← 之前漏读 data.message，导致登录/注册失败时显示 "登录已过期/资源已存在/请求失败(400)"
  const extractMsg = (data, fallback) =>
    data?.error?.message || data?.detail || data?.message || fallback

  if (statusCode === 401) {
    // 登录/注册接口也会返回 401（用户名或密码错误），此时不应清 token、不应跳转
    const pages = getCurrentPages()
    const route = pages.length ? '/' + pages[pages.length - 1].route : ''
    const onAuthPage = route === '/pages/login/login' || route === '/pages/login/register'
    const msg = extractMsg(data, '登录已过期，请重新登录')
    if (!onAuthPage) {
      store.commit('clearToken')
      uni.showToast({ title: msg, icon: 'none' })
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/login/login' })
      }, 1500)
    }
    return new Error(msg)
  }
  if (statusCode === 403) {
    const msg = extractMsg(data, '权限不足')
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  if (statusCode === 404) {
    const msg = extractMsg(data, '资源不存在')
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  if (statusCode === 409) {
    const msg = extractMsg(data, '资源已存在')
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  if (statusCode === 422) {
    const msg = parseValidationError(data)
    uni.showToast({ title: msg, icon: 'none', duration: 3000 })
    return new Error(msg)
  }
  if (statusCode === 500) {
    const msg = extractMsg(data, '服务器内部错误，请稍后重试')
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  if (statusCode >= 500) {
    const msg = '服务器暂时繁忙，请稍后重试'
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  if (statusCode >= 400) {
    const msg = extractMsg(data, `请求失败(${statusCode})`)
    uni.showToast({ title: msg, icon: 'none' })
    return new Error(msg)
  }
  return null
}

function requestWithRetry(options = {}, retryCount = 0) {
  const { url, method = 'GET', data = {}, needToken = true, header = {}, timeout = DEFAULT_TIMEOUT, silent = false } = options

  if (!isNetworkAvailable && !silent) {
    uni.showToast({ title: '当前无网络连接', icon: 'none', duration: 3000 })
    return Promise.reject(new Error('当前无网络连接'))
  }

  if (needToken) {
    const token = store.state.token
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }
  }

  return new Promise((resolve, reject) => {
    // 兼容绝对 URL（跨后端调用，如 Flask 鉴权走 http://localhost:5000）
    const fullUrl = /^https?:\/\//.test(url) ? url : BASE_URL + url
    uni.request({
      url: fullUrl,
      method,
      data,
      timeout,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      success: (res) => {
        const error = handleHttpError(res.statusCode, res.data)
        if (error) {
          reject(error)
          return
        }
        resolve(res.data)
      },
      fail: (err) => {
        console.error('请求失败:', err, '重试次数:', retryCount)
        
        if (retryCount < MAX_RETRY) {
          const isRetryable = err.errMsg && (
            err.errMsg.includes('timeout') ||
            err.errMsg.includes('超时') ||
            err.errMsg.includes('fail') ||
            err.errMsg.includes('连接') ||
            err.errMsg.includes('network')
          )
          
          if (isRetryable) {
            setTimeout(() => {
              requestWithRetry(options, retryCount + 1).then(resolve).catch(reject)
            }, RETRY_DELAY * Math.pow(2, retryCount))
            return
          }
        }

        let msg = '网络异常，请稍后重试'
        if (err.errMsg) {
          if (err.errMsg.includes('timeout') || err.errMsg.includes('超时')) {
            msg = '请求超时，请检查网络或稍后重试'
          } else if (err.errMsg.includes('fail') || err.errMsg.includes('连接') || err.errMsg.includes('network')) {
            msg = '网络连接异常，请检查网络设置'
          } else if (err.errMsg.includes('abort')) {
            msg = '请求已取消'
          } else if (err.errMsg.includes('SSL') || err.errMsg.includes('ssl')) {
            msg = 'SSL连接失败，请检查网络设置'
          }
        }
        
        if (!silent) {
          if (retryCount >= MAX_RETRY) {
            uni.showToast({ title: msg, icon: 'none', duration: 3000 })
          }
        }
        reject(new Error(msg))
      }
    })
  })
}

function request(options = {}) {
  // 【真机调试适配】兜底 try-catch: 捕获请求层异常并记录,
  // 避免接口报错以未捕获异常形式阻塞页面渲染; 业务错误仍抛给页面级 try-catch 处理
  try {
    return requestWithRetry(options, 0).catch((err) => {
      console.warn('[request] 接口异常(已兜底,不阻塞渲染):', options.url, err && err.message)
      throw err
    })
  } catch (e) {
    console.error('[request] 请求构造异常(已兜底):', options.url, e)
    return Promise.reject(e)
  }
}

function get(url, data = {}, needToken = true) {
  return request({ url, method: 'GET', data, needToken })
}

function post(url, data = {}, needToken = true) {
  return request({ url, method: 'POST', data, needToken })
}

function put(url, data = {}, needToken = true) {
  return request({ url, method: 'PUT', data, needToken })
}

function del(url, data = {}, needToken = true) {
  return request({ url, method: 'DELETE', data, needToken })
}

function uploadFile(filePath, url = '/upload', name = 'file') {
  const token = store.state.token
  
  if (!isNetworkAvailable) {
    uni.showToast({ title: '当前无网络连接', icon: 'none', duration: 3000 })
    return Promise.reject(new Error('当前无网络连接'))
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath,
      name,
      header: token ? { 'Authorization': `Bearer ${token}` } : {},
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (data.code && data.code >= 400) {
            const msg = data.message || '上传失败'
            uni.showToast({ title: msg, icon: 'none' })
            reject(new Error(msg))
          } else {
            resolve(data)
          }
        } catch (e) {
          resolve(res.data)
        }
      },
      fail: (err) => {
        let msg = '上传失败，请检查网络'
        if (err.errMsg) {
          if (err.errMsg.includes('timeout')) {
            msg = '上传超时，请重试'
          } else if (err.errMsg.includes('fail')) {
            msg = '上传失败，请检查网络'
          }
        }
        uni.showToast({ title: msg, icon: 'none', duration: 3000 })
        reject(new Error(msg))
      }
    })
  })
}

// ============ SSE 流式请求 ============

/**
 * SSE 流式 POST 请求
 * H5: 使用 fetch + ReadableStream 逐字读取
 * 非H5: 降级为普通 POST，一次性返回完整内容
 * @param {string} url - 请求路径(不含BASE_URL)
 * @param {object} data - 请求体
 * @param {function} onChunk - 每收到一个chunk回调 (content: string) => void
 * @param {function} onDone - 流结束回调 (fullContent: string) => void
 * @param {function} onError - 错误回调 (err: Error) => void
 * @returns {Promise<string>} 完整内容
 */
async function streamPost(url, data = {}, onChunk, onDone, onError, onMeta) {
  const token = store.state.token
  const fullUrl = BASE_URL + url

  // #ifdef H5
  try {
    const response = await fetch(fullUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`SSE请求失败(${response.status}): ${errorText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let fullContent = ''
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 解析 SSE data: 行
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留不完整的行

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data:')) continue

        const jsonStr = trimmed.slice(5).trim()
        if (!jsonStr) continue

        try {
          const parsed = JSON.parse(jsonStr)
          if (parsed.done) {
            // 流结束信号
          } else if (parsed.content) {
            fullContent += parsed.content
            if (onChunk) onChunk(parsed.content)
          } else if (parsed.session_id) {
            // v3.1：后端首个事件回传会话 id，前端拿到后下次请求带上，
            // 服务端才能攒下历史（否则每条消息都开新会话，AI 记不住上一句）
            if (onMeta) onMeta({ sessionId: parsed.session_id })
          } else if (parsed.habit_context) {
            // 2026-10-28：习惯会话模式状态（{habit_id, habit_name, active, exited}）
            if (onMeta) onMeta({ habitContext: parsed.habit_context })
          } else if (parsed.error) {
            throw new Error(parsed.error)
          }
        } catch (parseErr) {
          // 非JSON行，忽略
        }
      }
    }

    if (onDone) onDone(fullContent)
    return fullContent
  } catch (err) {
    if (onError) onError(err)
    throw err
  }
  // #endif

  // #ifndef H5
  // 非H5平台: 降级为普通请求
  try {
    const res = await post(url, data)
    const content = res.data?.reply || res.data?.content || res.message || ''
    if (onChunk && content) {
      // 模拟逐字输出
      const chars = content.split('')
      for (let i = 0; i < chars.length; i++) {
        onChunk(chars[i])
        await new Promise(r => setTimeout(r, 30))
      }
    }
    if (onDone) onDone(content)
    return content
  } catch (err) {
    if (onError) onError(err)
    throw err
  }
  // #endif
}

// ============ 工具函数 ============

/**
 * 防抖函数
 * @param {function} fn - 要防抖的函数
 * @param {number} delay - 延迟毫秒
 * @returns {function} 防抖后的函数
 */
function debounce(fn, delay = 500) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

// ============ 带缓存的请求 ============

/**
 * 带缓存的 GET 请求
 * 优先读缓存, 缓存未命中或 force=true 时请求并写入缓存
 * @param {string} url - 请求路径
 * @param {object} data - 查询参数
 * @param {object} options - { ttl: number(ms), force: boolean, needToken: boolean }
 * @returns {Promise<*>}
 */
async function cachedGet(url, data = {}, options = {}) {
  const { ttl = 300000, force = false, needToken = true } = options
  const cacheKey = url + JSON.stringify(data || {})

  if (!force) {
    const cached = getCache(cacheKey)
    if (cached !== null) return cached
  }

  const result = await get(url, data, needToken)
  setCache(cacheKey, result, ttl)
  return result
}

export default {
  request,
  get,
  post,
  put,
  del,
  uploadFile,
  // ↓↓↓ 新增 ↓↓↓ 静态资源地址拼接（头像/朋友圈图片等）
  STATIC_BASE,
  toStaticUrl,
  toAvatarUrl,
  // ↑↑↑ 新增 ↑↑↑
  streamPost,
  debounce,
  cachedGet,
  onNetworkRecovery,
  invalidateCache,
  clearCache
}

// ↓↓↓ 新增 ↓↓↓
// 本文件历史上只有 default 导出对象，导致 `import { toAvatarUrl } from '@/common/request'`
// 会报 "does not provide an export named"。这里补一份具名导出，两种引用方式都能用。
export {
  request,
  get,
  post,
  put,
  del,
  uploadFile,
  STATIC_BASE,
  toStaticUrl,
  toAvatarUrl,
  streamPost,
  debounce,
  cachedGet,
  onNetworkRecovery,
  invalidateCache,
  clearCache
}
// ↑↑↑ 新增结束 ↑↑↑