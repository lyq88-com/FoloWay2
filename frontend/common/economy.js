/**
 * 循途 · 虚拟货币经济系统
 * ------------------------------------------------------------
 * 统一管理：金币余额、礼物目录、商城商品、收支账单、
 * 打卡奖励产出（金币/礼物/扭蛋券）、宝物赠送联动。
 *
 * 数据保存在本地存储（key: xuntu_economy），通过 uni.$emit('economy-updated')
 * 广播变更，页面订阅后自行刷新（避免侵入 vuex 主状态）。
 */

// ↓↓↓ 新增 ↓↓↓ 云端同步所需（与 request.js 保持同源的地址与登录态）
import store from '@/store'
import { API_BASE } from './env'
// ↑↑↑ 新增 ↑↑↑

const ECONOMY_KEY = 'xuntu_economy'
const MAX_BILLS = 300

/** 礼物目录（可赠送AI伙伴；价格即直接赠送时消耗的金币） */
export const GIFT_CATALOG = [
  { id: 'flower', name: '小花花', icon: '🌸', price: 10, affection: 3, rarity: '普通', desc: '路边摘的小花，心意满满' },
  { id: 'star', name: '小星星', icon: '⭐', price: 20, affection: 5, rarity: '普通', desc: '摘一颗星星送给你' },
  { id: 'milktea', name: '奶茶', icon: '🧋', price: 30, affection: 8, rarity: '普通', desc: '三分糖，去冰，谢谢' },
  { id: 'cake', name: '小蛋糕', icon: '🍰', price: 50, affection: 12, rarity: '稀有', desc: '甜甜的奶油蛋糕' },
  { id: 'rose', name: '玫瑰花', icon: '🌹', price: 66, affection: 15, rarity: '稀有', desc: '热烈而浪漫' },
  { id: 'bear', name: '小熊玩偶', icon: '🧸', price: 88, affection: 20, rarity: '稀有', desc: '软软的抱抱熊' },
  { id: 'fireworks', name: '烟花', icon: '🎆', price: 128, affection: 28, rarity: '史诗', desc: '为你绽放整夜烟花' },
  { id: 'diamond', name: '钻石项链', icon: '💎', price: 199, affection: 40, rarity: '史诗', desc: '像你一样闪亮' },
  { id: 'moon', name: '月亮', icon: '🌙', price: 520, affection: 88, rarity: '传说', desc: '把月亮摘下来送给你' }
]

/** 商城商品（礼物之外还含装扮道具、扭蛋券） */
export const MALL_GOODS = [
  ...GIFT_CATALOG.map(g => ({ ...g, kind: 'gift' })),
  { id: 'gacha_ticket', name: '扭蛋券', icon: '🎟️', price: 60, kind: 'ticket', rarity: '普通', desc: '用于扭蛋抽奖获取新AI伙伴' },
  { id: 'deco_bubble', name: '限定气泡·星河', icon: '🎨', price: 120, kind: 'deco', rarity: '稀有', desc: '聊天限定气泡样式「星河」' },
  { id: 'deco_bubble_sakura', name: '限定气泡·樱花', icon: '🌸', price: 120, kind: 'deco', rarity: '稀有', desc: '聊天限定气泡样式「樱花」' },
  { id: 'deco_bg_aurora', name: '限定聊天背景·极光', icon: '🌌', price: 150, kind: 'deco', rarity: '史诗', desc: '聊天页限定背景「极光之夜」' },
  { id: 'deco_voice', name: '限定音色·精灵', icon: '🧚', price: 180, kind: 'deco', rarity: '史诗', desc: '解锁AI伙伴限定音色参数' }
]

/** 聊天气泡样式（含默认可用的与需解锁的） */
export const BUBBLE_STYLES = [
  { id: 'default', name: '默认', needUnlock: false },
  { id: 'mint', name: '薄荷', needUnlock: false },
  { id: 'sakura', name: '樱花', needUnlock: 'deco_bubble_sakura' },
  { id: 'galaxy', name: '星河', needUnlock: 'deco_bubble' }
]

/** 宝物收集解锁表：收集特定类型宝物达到数量 → 解锁限定内容 */
export const TREASURE_UNLOCKS = [
  { id: 'unlock_style_dream', needType: 'theme', needCount: 3, name: '限定对话·梦境絮语', desc: '收集3个主题类宝物解锁' },
  { id: 'unlock_style_star', needType: 'quote', needCount: 5, name: '限定对话·星光语录', desc: '收集5个语录类宝物解锁' },
  { id: 'unlock_deco_crown', needType: 'avatar', needCount: 3, name: '限定装扮·小皇冠', desc: '收集3个装饰类宝物解锁AI伙伴限定装扮' }
]

function defaultState() {
  return {
    coins: 0,
    bills: [],          // 收支明细 [{ type:'income'|'expense', amount, source, desc, time }]
    giftInventory: {},  // 礼物背包 { giftId: count }
    gachaTickets: 0,    // 扭蛋券
    unlockedDecos: [],  // 已解锁装扮/气泡/背景 id
    totalCheckinRewarded: 0, // 累计打卡奖励次数（用于掉落节奏控制）
    giftedCount: 0      // 累计送礼次数
  }
}

function loadState() {
  try {
    const saved = uni.getStorageSync(ECONOMY_KEY)
    if (saved) {
      const parsed = typeof saved === 'string' ? JSON.parse(saved) : saved
      return Object.assign(defaultState(), parsed)
    }
  } catch (e) {
    console.error('[economy] 读取状态失败', e)
  }
  return defaultState()
}

// ↓↓↓ 新增 ↓↓↓
/**
 * 只写本地，不触发云端上传
 * （拉云端数据落地时必须用它，否则会形成 拉取→回推 的无意义往返）
 */
function writeLocal(state) {
  try {
    uni.setStorageSync(ECONOMY_KEY, state)
  } catch (e) {
    console.error('[economy] 保存状态失败', e)
  }
}

// 上传防抖：打卡/送礼可能在短时间内连续触发多次写操作
const PUSH_DELAY = 1500
let _pushTimer = null
let _lastPushedSig = ''

function _token() {
  return (store && store.state && store.state.token) || ''
}

function _toBody(state) {
  return {
    coins: state.coins,
    bills: state.bills,
    giftInventory: state.giftInventory,
    gachaTickets: state.gachaTickets,
    unlockedDecos: state.unlockedDecos,
    totalCheckinRewarded: state.totalCheckinRewarded,
    giftedCount: state.giftedCount
  }
}

function pushToCloud(state) {
  const token = _token()
  if (!token) return   // 未登录：纯本地模式，行为与改动前完全一致

  const body = _toBody(state)
  const sig = JSON.stringify(body)
  if (sig === _lastPushedSig) return   // 内容没变就别重复打接口
  _lastPushedSig = sig

  uni.request({
    url: API_BASE + '/economy/state',
    method: 'PUT',
    data: body,
    timeout: 10000,
    header: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    success: (res) => {
      const data = res.data
      if (!(res.statusCode === 200 && data && data.code === 200)) {
        console.warn('[economy] 云端同步失败', res.statusCode, data && data.message)
      }
    },
    fail: (err) => {
      // 网络异常不阻塞本地流程：本地已写入，下次变更会再试
      console.warn('[economy] 云端同步异常', err && err.errMsg)
    }
  })
}

function scheduleCloudPush() {
  if (_pushTimer) clearTimeout(_pushTimer)
  _pushTimer = setTimeout(() => {
    _pushTimer = null
    pushToCloud(loadState())
  }, PUSH_DELAY)
}

/**
 * 合并两条账单流水（按 time+desc+amount 去重），最多保留 MAX_BILLS 条
 */
function mergeBills(localBills, cloudBills) {
  const seen = new Set()
  const merged = []
  const push = (b) => {
    if (!b) return
    const key = `${b.time || ''}|${b.desc || ''}|${b.amount || 0}`
    if (seen.has(key)) return
    seen.add(key)
    merged.push(b)
  }
  ;(localBills || []).forEach(push)
  ;(cloudBills || []).forEach(push)
  merged.sort((a, b) => String(a.time || '').localeCompare(String(b.time || '')))
  return merged.slice(-MAX_BILLS)
}
// ↑↑↑ 新增结束 ↑↑↑

function saveState(state) {
  if (state.bills.length > MAX_BILLS) {
    state.bills = state.bills.slice(-MAX_BILLS)
  }
  writeLocal(state)
  // ↓↓↓ 新增 ↓↓↓ 本地写完顺手同步云端（未登录/断网时自动跳过）
  scheduleCloudPush()
  // ↑↑↑ 新增结束 ↑↑↑
}

function notify() {
  try { uni.$emit('economy-updated') } catch (e) { /* 静默 */ }
}

function nowStr() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function addBill(state, type, amount, source, desc) {
  state.bills.push({ type, amount, source, desc, time: nowStr() })
}

export default {
  /** 读取完整状态（返回副本） */
  getState() {
    const s = loadState()
    return JSON.parse(JSON.stringify(s))
  },

  getCoins() {
    return loadState().coins
  },

  getBills() {
    return loadState().bills
  },

  getGiftInventory() {
    return loadState().giftInventory
  },

  getGachaTickets() {
    return loadState().gachaTickets
  },

  getUnlockedDecos() {
    return loadState().unlockedDecos
  },

  /**
   * 金币收入（打卡奖励 / 任务奖励 / 补偿等）
   * @returns {Boolean} 是否成功
   */
  addCoins(amount, source, desc) {
    amount = Math.max(0, Math.floor(Number(amount) || 0))
    if (amount <= 0) return false
    const s = loadState()
    s.coins += amount
    addBill(s, 'income', amount, source, desc || source)
    saveState(s)
    notify()
    return true
  },

  /**
   * 金币支出（送礼 / 商城购买 / 扭蛋）
   * @returns {Boolean} 余额不足时返回 false
   */
  spendCoins(amount, source, desc) {
    amount = Math.max(0, Math.floor(Number(amount) || 0))
    const s = loadState()
    if (s.coins < amount) return false
    s.coins -= amount
    addBill(s, 'expense', amount, source, desc || source)
    saveState(s)
    notify()
    return true
  },

  /**
   * 打卡成功 → 产出奖励（金币 + 概率掉落礼物 / 扭蛋券）
   * 难度越高金币越多，连续打卡有加成
   * @param {Object} habit - { id, name, difficulty, streak }
   * @returns {Object} { coins, gift, gachaTicket, streakBonus }
   */
  rewardCheckin(habit) {
    const s = loadState()
    const difficultyMap = { easy: 10, medium: 20, hard: 30 }
    let coins = difficultyMap[habit?.difficulty] || 10
    let streakBonus = 0
    const streak = habit?.streak || 0
    if (streak >= 21) streakBonus = 10
    else if (streak >= 14) streakBonus = 6
    else if (streak >= 7) streakBonus = 3
    coins += streakBonus

    s.coins += coins
    addBill(s, 'income', coins, 'checkin', `完成打卡「${habit?.name || '习惯'}」${streakBonus ? `（含连续${streak}天加成+${streakBonus}）` : ''}`)
    s.totalCheckinRewarded += 1

    // 礼物掉落：约 25% 概率（每3次打卡保底一次）
    let gift = null
    const nth = s.totalCheckinRewarded % 3 === 0
    if (Math.random() < 0.25 || nth) {
      const pool = GIFT_CATALOG.filter(g => g.price <= 88)
      gift = pool[Math.floor(Math.random() * pool.length)] || null
      if (gift) {
        s.giftInventory[gift.id] = (s.giftInventory[gift.id] || 0) + 1
        addBill(s, 'income', 0, 'gift_drop', `打卡掉落礼物「${gift.name}」×1`)
      }
    }

    // 扭蛋券：每累计5次打卡掉一张
    let gachaTicket = false
    if (s.totalCheckinRewarded % 5 === 0) {
      s.gachaTickets += 1
      gachaTicket = true
      addBill(s, 'income', 0, 'gacha_ticket', '打卡累计奖励：扭蛋券 ×1')
    }

    saveState(s)
    notify()
    return { coins, gift, gachaTicket, streakBonus }
  },

  /** 商城购买（礼物入背包 / 扭蛋券 / 装扮解锁） */
  buyGoods(goodsId) {
    const goods = MALL_GOODS.find(g => g.id === goodsId)
    if (!goods) return { ok: false, msg: '商品不存在' }
    const s = loadState()
    if (s.coins < goods.price) return { ok: false, msg: '金币不足，去打卡赚金币吧~' }
    s.coins -= goods.price
    addBill(s, 'expense', goods.price, 'mall', `商城购买「${goods.name}」`)
    if (goods.kind === 'gift') {
      s.giftInventory[goods.id] = (s.giftInventory[goods.id] || 0) + 1
    } else if (goods.kind === 'ticket') {
      s.gachaTickets += 1
    } else if (goods.kind === 'deco') {
      s.unlockedDecos.push(goods.id)
    }
    saveState(s)
    notify()
    return { ok: true, msg: `购买成功：${goods.name}` }
  },

  /**
   * 赠送礼物给AI伙伴
   * 优先消耗背包中的礼物；背包没有则直接扣金币（转账式赠送）
   * @returns {Object} { ok, msg, fromInventory, gift }
   */
  sendGift(giftId) {
    const gift = GIFT_CATALOG.find(g => g.id === giftId)
    if (!gift) return { ok: false, msg: '礼物不存在' }
    const s = loadState()
    let fromInventory = false
    if ((s.giftInventory[giftId] || 0) > 0) {
      s.giftInventory[giftId] -= 1
      if (s.giftInventory[giftId] <= 0) delete s.giftInventory[giftId]
      fromInventory = true
      addBill(s, 'expense', 0, 'gift', `赠送「${gift.name}」（消耗背包礼物×1）`)
    } else {
      if (s.coins < gift.price) {
        return { ok: false, msg: `背包没有该礼物，金币也不足（需${gift.price}金币）` }
      }
      s.coins -= gift.price
      addBill(s, 'expense', gift.price, 'gift', `赠送「${gift.name}」`)
    }
    s.giftedCount += 1
    saveState(s)
    notify()
    return { ok: true, msg: `已赠送「${gift.name}」`, fromInventory, gift }
  },

  /** 消耗一张扭蛋券（扭蛋页调用），无券时返回 false */
  useGachaTicket() {
    const s = loadState()
    if (s.gachaTickets <= 0) return false
    s.gachaTickets -= 1
    addBill(s, 'expense', 0, 'gacha', '扭蛋抽奖（消耗扭蛋券×1）')
    saveState(s)
    notify()
    return true
  },

  /** 扭蛋扣费（无券时按金币 60/次） */
  payGacha() {
    const s = loadState()
    if (s.gachaTickets > 0) {
      return this.useGachaTicket()
    }
    if (s.coins < 60) return false
    return this.spendCoins(60, 'gacha', '扭蛋抽奖')
  },

  /**
   * 宝物系统联动：读取仓库中可作为礼物的宝物
   * （box_warehouse 中未使用的宝物均可赠送）
   */
  getGiftableTreasures() {
    try {
      const warehouse = uni.getStorageSync('box_warehouse') || []
      return warehouse.filter(t => !t.isUsed).map((t, i) => ({
        key: `${t.type}_${t.value}_${t.date || i}`,
        name: t.name,
        emoji: t.emoji,
        type: t.type,
        value: t.value,
        date: t.date
      }))
    } catch (e) {
      return []
    }
  },

  /**
   * 宝物系统联动：把宝物送给AI伙伴
   * @returns {Object} { ok, msg, affection }
   */
  sendTreasure(treasure) {
    try {
      const warehouse = uni.getStorageSync('box_warehouse') || []
      const idx = warehouse.findIndex(w =>
        w.type === treasure.type && w.value === treasure.value && !w.isUsed
      )
      if (idx === -1) return { ok: false, msg: '宝物不存在或已使用' }
      warehouse[idx].isUsed = true
      warehouse[idx].usedAs = 'gift'
      uni.setStorageSync('box_warehouse', warehouse)
      const s = loadState()
      addBill(s, 'expense', 0, 'treasure_gift', `将宝物「${treasure.name}」赠予AI伙伴`)
      saveState(s)
      notify()
      return { ok: true, msg: `已将「${treasure.name}」送给TA`, affection: 10 }
    } catch (e) {
      return { ok: false, msg: '赠送失败' }
    }
  },

  /**
   * 宝物收集解锁检查：收集特定类型宝物达数量 → 解锁限定装扮/对话
   * @returns {Array} 本次新解锁的条目
   */
  checkTreasureUnlocks() {
    try {
      const warehouse = uni.getStorageSync('box_warehouse') || []
      const s = loadState()
      const newUnlocks = []
      TREASURE_UNLOCKS.forEach(rule => {
        if (s.unlockedDecos.includes(rule.id)) return
        const count = warehouse.filter(t => t.type === rule.needType).length
        if (count >= rule.needCount) {
          s.unlockedDecos.push(rule.id)
          newUnlocks.push(rule)
        }
      })
      if (newUnlocks.length > 0) {
        saveState(s)
        notify()
      }
      return newUnlocks
    } catch (e) {
      return []
    }
  },

  /** 新用户初始金币（首次进入商城/聊天时发放一次） */
  ensureWelcomeCoins() {
    const flag = 'economy_welcome_granted'
    try {
      if (uni.getStorageSync(flag)) return
      // ↓↓↓ 新增 ↓↓↓ 换设备/清缓存后本地标记会丢，但云端金币已随登录拉回来了；
      // 此时若再发一次见面礼就成了无限刷金币，这里直接跳过。
      if (loadState().coins > 0) {
        uni.setStorageSync(flag, '1')
        return
      }
      // ↑↑↑ 新增结束 ↑↑↑
      uni.setStorageSync(flag, '1')
      this.addCoins(100, 'welcome', '新用户见面礼')
    } catch (e) { /* 静默 */ }
  },

  /** 金币收支汇总 */
  getSummary() {
    const s = loadState()
    let income = 0
    let expense = 0
    s.bills.forEach(b => {
      if (b.type === 'income') income += b.amount
      else expense += b.amount
    })
    return { income, expense, balance: s.coins, count: s.bills.length }
  },

  // ↓↓↓ 新增 ↓↓↓
  /**
   * 登录后从云端拉回经济状态（换设备 / 清缓存后靠它恢复资产）
   * 合并策略：云端是权威账本，标量（金币/券/计数/礼物背包/已解锁装扮）以云端为准；
   *          账单流水取本地与云端的并集（按 time+desc+amount 去重），两边都不丢。
   * @returns {Promise<Boolean>} 是否成功拿到并应用了云端数据
   */
  pullFromCloud() {
    return new Promise((resolve) => {
      const token = _token()
      if (!token) {
        resolve(false)
        return
      }
      uni.request({
        url: API_BASE + '/economy/state',
        method: 'GET',
        timeout: 10000,
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          const data = res.data
          if (!(res.statusCode === 200 && data && data.code === 200
                && data.data && data.data.initialized)) {
            resolve(false)
            return
          }
          try {
            const cloud = data.data.state
            const local = loadState()
            const merged = Object.assign({}, local, cloud)
            merged.bills = mergeBills(local.bills, cloud.bills)
            // 用 writeLocal 而非 saveState：刚拉回来的数据不必再推一次回云端
            writeLocal(merged)
            _lastPushedSig = JSON.stringify(_toBody(merged))
            notify()
            resolve(true)
          } catch (e) {
            console.error('[economy] 应用云端经济数据失败', e)
            resolve(false)
          }
        },
        fail: () => resolve(false)
      })
    })
  }
  // ↑↑↑ 新增结束 ↑↑↑
}
