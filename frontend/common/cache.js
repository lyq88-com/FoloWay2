/**
 * 简易缓存层 - API 响应缓存到 localStorage
 * 减少 unnecessary network requests, 优先使用缓存
 */

const CACHE_PREFIX = 'ahp_cache_'
const DEFAULT_TTL = 300000 // 5分钟

/**
 * 生成缓存 key
 * @param {string} key - 原始 key
 * @returns {string} 带前缀的 key
 */
function buildKey(key) {
  return CACHE_PREFIX + key
}

/**
 * 获取缓存
 * @param {string} key - 缓存 key
 * @returns {*} 缓存数据, 未命中返回 null
 */
export function getCache(key) {
  try {
    const raw = uni.getStorageSync(buildKey(key))
    if (!raw) return null

    const cached = JSON.parse(raw)
    if (cached.expire && Date.now() > cached.expire) {
      // 已过期, 清除
      uni.removeStorageSync(buildKey(key))
      return null
    }
    return cached.data
  } catch (e) {
    return null
  }
}

/**
 * 设置缓存
 * @param {string} key - 缓存 key
 * @param {*} data - 缓存数据
 * @param {number} ttl - 过期时间(毫秒), 默认 5 分钟
 */
export function setCache(key, data, ttl = DEFAULT_TTL) {
  try {
    const payload = {
      data,
      expire: ttl > 0 ? Date.now() + ttl : 0,
      createdAt: Date.now()
    }
    uni.setStorageSync(buildKey(key), JSON.stringify(payload))
  } catch (e) {
    // 存储满或序列化失败, 静默忽略
  }
}

/**
 * 清除缓存
 * @param {string} pattern - 匹配模式(前缀), 不传则清除全部
 */
export function clearCache(pattern) {
  try {
    const keys = uni.getStorageInfoSync().keys || []
    const prefix = pattern ? buildKey(pattern) : CACHE_PREFIX

    keys.forEach(k => {
      if (k.startsWith(prefix)) {
        uni.removeStorageSync(k)
      }
    })
  } catch (e) {
    // 静默忽略
  }
}

/**
 * 带缓存的 GET 请求
 * 优先读缓存, 缓存未命中则请求并写入缓存
 * @param {function} fetchFn - 实际请求函数, 返回 Promise
 * @param {string} cacheKey - 缓存 key
 * @param {object} options - { ttl: number, force: boolean }
 * @returns {Promise<*>}
 */
export async function cachedGet(fetchFn, cacheKey, options = {}) {
  const { ttl = DEFAULT_TTL, force = false } = options

  // 非强制刷新时, 先读缓存
  if (!force) {
    const cached = getCache(cacheKey)
    if (cached !== null) {
      return cached
    }
  }

  // 请求并缓存
  const data = await fetchFn()
  setCache(cacheKey, data, ttl)
  return data
}

/**
 * 使指定缓存失效
 * @param {string} key - 缓存 key (不含前缀)
 */
export function invalidateCache(key) {
  try {
    uni.removeStorageSync(buildKey(key))
  } catch (e) {
    // 静默忽略
  }
}

/**
 * 获取缓存信息
 * @returns {object} { keys: string[], size: number, limit: number }
 */
export function getCacheInfo() {
  try {
    const info = uni.getStorageInfoSync()
    const cacheKeys = (info.keys || []).filter(k => k.startsWith(CACHE_PREFIX))
    return {
      keys: cacheKeys,
      count: cacheKeys.length,
      size: info.currentSize || 0,
      limit: info.limitSize || 0
    }
  } catch (e) {
    return { keys: [], count: 0, size: 0, limit: 0 }
  }
}

export default {
  getCache,
  setCache,
  clearCache,
  cachedGet,
  invalidateCache,
  getCacheInfo,
  DEFAULT_TTL,
  CACHE_PREFIX
}
