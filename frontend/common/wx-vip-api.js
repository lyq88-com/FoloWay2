/**
 * 循途 · 微信扫码登录 + VIP会员 前端接口层（新增模块，隔离）
 *
 * 【零副作用约定】
 *   1. 本文件是新增文件，不 import 任何原有页面/组件
 *   2. 未改动 common/request.js、store、任何已有 api 模块
 *   3. 所有 demo 数据写在文件内，不依赖后端
 *
 * 【如何使用】
 *   演示/开发阶段 USE_MOCK = true（默认），界面全部可点、可跑通完整闭环；
 *   后端接口（SpringBoot 版见 xuntu-wx-vip/ 交付包）就绪后，把 USE_MOCK 改成 false 即可，
 *   前端页面无需任何改动。
 */

// =====================================================================
// 配置区
// =====================================================================
export const WX_VIP_CONFIG = {
  /** true = 演示数据（无需后端）；false = 走真实接口 */
  useMock: true,

  /** 真实接口基地址（SpringBoot 侧前缀）；H5 走 vite proxy，App 端需填局域网 IP */
  // #ifdef H5
  baseUrl: '/api',
  // #endif
  // #ifndef H5
  baseUrl: 'http://172.20.10.3:8080/api',
  // #endif
}

/** 演示模式下的本地持久化 key（VIP 状态、模拟订单） */
const DEMO_KEY = 'xuntu_vip_demo_v1'

// =====================================================================
// 演示数据 & 演示状态存取
// =====================================================================
const MOCK_PACKAGES = [
  {
    id: 1,
    name: 'VIP月卡',
    subTitle: '先体验一个月',
    price: 19.9,
    originalPrice: 29.9,
    days: 30,
    benefits: ['专属身份标识', 'AI伙伴无限对话', '限定星球场景', '成长报告导出'],
    tag: '',
    recommended: false,
  },
  {
    id: 2,
    name: 'VIP季卡',
    subTitle: '最受欢迎，性价比之选',
    price: 52.9,
    originalPrice: 89.7,
    days: 90,
    benefits: ['专属身份标识', 'AI伙伴无限对话', '限定星球场景', '成长报告导出', '专属主题皮肤', '优先新功能体验'],
    tag: '推荐',
    recommended: true,
  },
  {
    id: 3,
    name: 'VIP年卡',
    subTitle: '一年长效陪伴，超值推荐',
    price: 178.0,
    originalPrice: 358.8,
    days: 365,
    benefits: ['专属身份标识', 'AI伙伴无限对话', '限定星球场景', '成长报告导出', '专属主题皮肤', '优先新功能体验', '一对一成长顾问'],
    tag: '超值',
    recommended: false,
  },
]

function readDemo() {
  try {
    const raw = uni.getStorageSync(DEMO_KEY)
    if (raw) return JSON.parse(raw)
  } catch (e) {
    /* ignore */
  }
  return { orders: {}, vipExpireAt: null, wxBound: false }
}

function writeDemo(data) {
  try {
    uni.setStorageSync(DEMO_KEY, JSON.stringify(data))
  } catch (e) {
    /* ignore */
  }
}

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

// 演示模式：扫码状态机
// scene -> 'WAITING' | 'SCANNED'
const mockScenes = {}

const fail = (msg, code = 500) => Promise.reject({ code, msg, message: msg })

// =====================================================================
// 环境判断
// =====================================================================
/** 是否在微信内置浏览器中（JSAPI 支付的前置条件） */
export function isWechatBrowser() {
  // #ifdef H5
  const ua = (navigator.userAgent || '').toLowerCase()
  return ua.indexOf('micromessenger') !== -1
  // #endif
  // #ifndef H5
  return false
  // #endif
}

// =====================================================================
// 一、微信登录
// =====================================================================

/** 1. 获取登录二维码 */
export async function getWxQrcode() {
  if (WX_VIP_CONFIG.useMock) {
    await delay(300)
    const scene = 'demo' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
    mockScenes[scene] = 'WAITING'
    return {
      scene,
      // 真实场景是微信开放平台授权地址；演示模式下给一个占位地址用于渲染二维码图形
      authorizeUrl: 'https://open.weixin.qq.com/connect/qrconnect?appid=DEMO_MODE&scope=snsapi_login&state=' + scene,
      expireSeconds: 300,
      demo: true,
    }
  }
  return request({ url: '/wx/qrcode', method: 'GET' })
}

/** 2. 轮询扫码结果 */
export async function pollWxLogin(scene) {
  if (WX_VIP_CONFIG.useMock) {
    await delay(120)
    const state = mockScenes[scene]
    if (!state) return { status: 'EXPIRED', msg: '二维码已过期，请刷新' }
    if (state === 'WAITING') return { status: 'PENDING', msg: '等待扫码' }
    // 已被"模拟扫码"
    delete mockScenes[scene]
    const demo = readDemo()
    const firstTime = !demo.wxBound
    demo.wxBound = true
    writeDemo(demo)
    return {
      status: 'SUCCESS',
      msg: '登录成功',
      token: 'demo_token_' + Date.now(),
      newUser: firstTime,
      user: {
        id: 10001,
        username: 'wx_demo_8891',
        nickname: '微信用户',
        avatar: '',
        isVip: !!demo.vipExpireAt,
        vipExpireAt: demo.vipExpireAt,
      },
      demo: true,
    }
  }
  return request({ url: '/wx/poll', method: 'GET', data: { scene } })
}

/**
 * 3. 演示专用：模拟用户扫码成功
 *    真实环境不会调用这个方法（由后端 /wx/callback 驱动状态变化）
 */
export async function simulateScan(scene) {
  if (!scene) return
  mockScenes[scene] = 'SCANNED'
}

/** 4. 新用户决策 CREATE / BIND */
export async function decideWxUser({ scene, action }) {
  if (WX_VIP_CONFIG.useMock) {
    await delay(300)
    delete mockScenes[scene]
    return {
      status: 'SUCCESS',
      token: 'demo_token_' + Date.now(),
      newUser: action === 'CREATE',
      user: { id: 10001, username: 'wx_demo_8891', nickname: '微信用户', avatar: '', isVip: false },
      demo: true,
    }
  }
  return request({ url: '/wx/decide', method: 'POST', data: { scene, action } })
}

/** 5. 获取支付授权地址（补齐公众号 openid） */
export async function getMpAuthUrl() {
  if (WX_VIP_CONFIG.useMock) {
    await delay(200)
    return { scene: 'demoMp', authUrl: 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=DEMO', demo: true }
  }
  return request({ url: '/wx/mp-auth-url', method: 'GET' })
}

// =====================================================================
// 二、VIP 会员
// =====================================================================

/** 6. 套餐列表 */
export async function getVipPackages() {
  if (WX_VIP_CONFIG.useMock) {
    await delay(300)
    return MOCK_PACKAGES
  }
  return request({ url: '/vip/packages', method: 'GET' })
}

/** 7. 创建支付订单 */
export async function createVipOrder(packageId) {
  if (WX_VIP_CONFIG.useMock) {
    await delay(500)
    const pkg = MOCK_PACKAGES.find((p) => p.id === packageId)
    if (!pkg) return fail('套餐不存在')
    const orderNo = 'V' + new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14) + Math.random().toString(36).slice(2, 8).toUpperCase()
    const demo = readDemo()
    demo.orders[orderNo] = {
      orderNo,
      packageId: pkg.id,
      packageName: pkg.name,
      payAmount: Math.round(pkg.price * 100),
      days: pkg.days,
      paid: false,
      createTime: Date.now(),
    }
    writeDemo(demo)
    return { orderNo, payAmount: demo.orders[orderNo].payAmount, demo: true }
  }
  return request({ url: '/vip/create-order', method: 'POST', data: { packageId } })
}

/**
 * 8. 演示专用：模拟支付结果（成功 / 取消）
 *    真实环境由微信公众号支付 -> 后端 notify 回调驱动状态
 */
export async function simulatePayResult(orderNo, success) {
  await delay(600)
  const demo = readDemo()
  const order = demo.orders[orderNo]
  if (!order) return fail('订单不存在')
  if (!success) return { paid: false, orderNo }

  const now = new Date()
  const base = demo.vipExpireAt && new Date(demo.vipExpireAt) > now ? new Date(demo.vipExpireAt) : now
  const expire = new Date(base.getTime() + order.days * 86400000)
  demo.vipExpireAt = expire.toISOString()
  // 幂等演示：已支付订单再次标记也不会重复叠加
  if (!order.paid) {
    order.paid = true
    order.expireAt = demo.vipExpireAt
  }
  writeDemo(demo)
  return { paid: true, orderNo, expireAt: order.expireAt }
}

/** 9. 查询订单支付结果 */
export async function queryOrderResult(orderNo) {
  if (WX_VIP_CONFIG.useMock) {
    await delay(200)
    const demo = readDemo()
    const order = demo.orders[orderNo]
    if (!order) return fail('订单不存在')
    return { orderNo, paid: !!order.paid, expireAt: order.expireAt || null }
  }
  return request({ url: '/vip/order-result', method: 'GET', data: { orderNo } })
}

/** 10. 当前用户 VIP 状态 */
export async function getVipStatus() {
  if (WX_VIP_CONFIG.useMock) {
    await delay(200)
    const demo = readDemo()
    const expire = demo.vipExpireAt ? new Date(demo.vipExpireAt) : null
    const isVip = !!expire && expire > new Date()
    return {
      isVip,
      expireAt: expire ? formatDate(expire) : null,
      remainDays: isVip ? Math.ceil((expire - new Date()) / 86400000) : 0,
    }
  }
  return request({ url: '/vip/status', method: 'GET' })
}

/** 11. 读取演示订单快照（成功页展示套餐名用；真实模式下返回 null） */
export function readDemoOrder(orderNo) {
  if (!WX_VIP_CONFIG.useMock || !orderNo) return null
  const demo = readDemo()
  return demo.orders[orderNo] || null
}

// =====================================================================
// 内部：真实请求（USE_MOCK = false 时才会走到这里）
// =====================================================================
function request({ url, method = 'GET', data = {} }) {
  const token = uni.getStorageSync('token')
  return new Promise((resolve, reject) => {
    uni.request({
      url: WX_VIP_CONFIG.baseUrl + url,
      method,
      data,
      timeout: 20000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
      success: (res) => {
        const body = res.data || {}
        // 后端统一格式 {code, msg, data}
        if (res.statusCode >= 200 && res.statusCode < 300 && (body.code === 200 || body.code === undefined)) {
          resolve(body.data !== undefined ? body.data : body)
          return
        }
        reject({ code: body.code || res.statusCode, msg: body.msg || body.message || '请求失败' })
      },
      fail: (err) => reject({ code: -1, msg: err.errMsg || '网络异常' }),
    })
  })
}

function formatDate(d) {
  const p = (n) => (n < 10 ? '0' + n : n)
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

export default {
  WX_VIP_CONFIG,
  isWechatBrowser,
  getWxQrcode,
  pollWxLogin,
  simulateScan,
  decideWxUser,
  getMpAuthUrl,
  getVipPackages,
  createVipOrder,
  simulatePayResult,
  queryOrderResult,
  getVipStatus,
  readDemoOrder,
}
