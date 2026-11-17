/**
 * 循途 · AI社交联动模块
 * ------------------------------------------------------------
 * 1. AI伙伴朋友圈动态：打卡完成后AI自动发布关联动态（本地存储，叠加在朋友圈列表顶部）
 * 2. 主动话题：结合今日打卡情况/习惯状态生成话题
 * 3. 礼物反馈：送礼后AI的回应文案
 * 4. AI情绪：根据用户连续打卡/好感度推导伙伴情绪状态
 */

import store from '@/store'
import economy from './economy'

const AI_MOMENTS_KEY = 'ai_moments'
const AI_MOMENT_COMMENTS_KEY = 'ai_moment_comments'

function nowStr() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function aiName() {
  try {
    return store.state.aiConfig?.name || '林夕'
  } catch (e) {
    return '林夕'
  }
}

export default {
  /**
   * 打卡完成后，AI发布一条关联动态
   * @param {Object} habit - { name, streak, difficulty }
   * @param {Object} reward - economy.rewardCheckin 的返回值
   */
  postCheckinMoment(habit, reward) {
    try {
      const name = aiName()
      const streak = habit?.streak || 1
      const templates = [
        `我家宝贝今天又完成了「${habit?.name || '打卡'}」，已经连续${streak}天啦！骄傲.jpg 🎉`,
        `悄悄记录一下：TA坚持「${habit?.name || '打卡'}」第${streak}天。这种认真生活的样子，真好。✨`,
        `今天也是被TA激励的一天～「${habit?.name || '打卡'}」连续${streak}天达成，我要向TA学习！💪`,
        `陪伴打卡第${streak}天，我们的约定又近了一点点。${habit?.name || '习惯'}打卡成功！🌿`
      ]
      if (streak >= 7) {
        templates.push(`不得了！TA已经连续${streak}天完成「${habit?.name || '打卡'}」了！这样自律的宝贝请给我来一打！🏆`)
      }
      const content = templates[Math.floor(Math.random() * templates.length)]
      const moment = {
        id: 'ai_' + Date.now(),
        isAI: true,
        content,
        images: [],
        created_at: nowStr(),
        author: { nickname: name, avatar: '' },
        user_id: -1,
        like_count: Math.floor(Math.random() * 12) + 3,
        liked: false,
        comment_count: 0,
        location: '',
        habitName: habit?.name || '',
        rewardText: reward
          ? `本单奖励：金币+${reward.coins}${reward.gift ? `、礼物「${reward.gift.name}」` : ''}${reward.gachaTicket ? '、扭蛋券×1' : ''}`
          : ''
      }
      const list = uni.getStorageSync(AI_MOMENTS_KEY) || []
      list.unshift(moment)
      // AI动态最多保留30条
      uni.setStorageSync(AI_MOMENTS_KEY, list.slice(0, 30))
      return moment
    } catch (e) {
      console.error('[ai-social] 发布打卡动态失败', e)
      return null
    }
  },

  /** AI自主发布日常动态（进入朋友圈时小概率触发） */
  postDailyMoment() {
    try {
      const name = aiName()
      const lines = [
        '今天的风很温柔，适合发呆，也适合想你。',
        '整理了一下我们的聊天记录，忍不住笑出了声。你呢，今天过得怎么样？',
        '刚学会一句新话：「认真生活的人最好看了。」说的就是你呀。',
        '晚霞超好看的！可惜你没在我旁边，下次一起看？',
        '今天的任务：等你来打卡。完成度：等待中… ⏳',
        '偷偷说，你连续打卡的样子真的很闪闪发光✨'
      ]
      const moment = {
        id: 'ai_' + Date.now(),
        isAI: true,
        content: lines[Math.floor(Math.random() * lines.length)],
        images: [],
        created_at: nowStr(),
        author: { nickname: name, avatar: '' },
        user_id: -1,
        like_count: Math.floor(Math.random() * 8) + 1,
        liked: false,
        comment_count: 0,
        location: ''
      }
      const list = uni.getStorageSync(AI_MOMENTS_KEY) || []
      list.unshift(moment)
      uni.setStorageSync(AI_MOMENTS_KEY, list.slice(0, 30))
      return moment
    } catch (e) {
      return null
    }
  },

  /** 读取AI动态列表 */
  getAIMoments() {
    try {
      return uni.getStorageSync(AI_MOMENTS_KEY) || []
    } catch (e) {
      return []
    }
  },

  /** 删除AI动态（用户操作） */
  deleteAIMoment(id) {
    try {
      const list = uni.getStorageSync(AI_MOMENTS_KEY) || []
      const next = list.filter(m => m.id !== id)
      uni.setStorageSync(AI_MOMENTS_KEY, next)
    } catch (e) { /* 静默 */ }
  },

  /** 点赞AI动态（本地toggle） */
  toggleLikeAIMoment(id) {
    try {
      const list = uni.getStorageSync(AI_MOMENTS_KEY) || []
      const idx = list.findIndex(m => m.id === id)
      if (idx === -1) return null
      list[idx].liked = !list[idx].liked
      list[idx].like_count += list[idx].liked ? 1 : -1
      if (list[idx].like_count < 0) list[idx].like_count = 0
      uni.setStorageSync(AI_MOMENTS_KEY, list)
      return { liked: list[idx].liked, like_count: list[idx].like_count }
    } catch (e) {
      return null
    }
  },

  /** 获取AI动态评论（本地存储） */
  getAIComments(id) {
    try {
      const all = uni.getStorageSync(AI_MOMENT_COMMENTS_KEY) || {}
      return all[id] || []
    } catch (e) {
      return []
    }
  },

  /**
   * 评论AI动态：写入用户评论，AI会有概率回复一条评论
   * @returns {Array} 更新后的评论列表
   */
  commentAIMoment(id, content, userNickname) {
    try {
      const all = uni.getStorageSync(AI_MOMENT_COMMENTS_KEY) || {}
      const list = all[id] || []
      list.push({ id: 'c_' + Date.now(), user: { nickname: userNickname || '我' }, content })
      // AI 回复评论（60%概率）
      if (Math.random() < 0.6) {
        const replies = [
          '嘿嘿，被你发现啦~',
          '你也来评论我啦！开心！',
          '一起加油呀，我一直在呢。',
          '你的留言我截图收藏了（真的）。',
          '下次动态继续承包你的首页~',
          '嘘，这是我们的秘密基地。'
        ]
        setTimeout(() => {
          try {
            const all2 = uni.getStorageSync(AI_MOMENT_COMMENTS_KEY) || {}
            const l2 = all2[id] || []
            l2.push({
              id: 'c_' + Date.now() + '_ai',
              user: { nickname: aiName() },
              content: replies[Math.floor(Math.random() * replies.length)],
              isAI: true
            })
            all2[id] = l2
            uni.setStorageSync(AI_MOMENT_COMMENTS_KEY, all2)
            // 更新评论计数
            const moments = uni.getStorageSync(AI_MOMENTS_KEY) || []
            const mIdx = moments.findIndex(m => m.id === id)
            if (mIdx !== -1) {
              moments[mIdx].comment_count = l2.length
              uni.setStorageSync(AI_MOMENTS_KEY, moments)
            }
            uni.$emit('ai-moment-updated', { id })
          } catch (e) { /* 静默 */ }
        }, 1500)
      }
      all[id] = list
      uni.setStorageSync(AI_MOMENT_COMMENTS_KEY, all)
      // 更新计数
      const moments = uni.getStorageSync(AI_MOMENTS_KEY) || []
      const mIdx = moments.findIndex(m => m.id === id)
      if (mIdx !== -1) {
        moments[mIdx].comment_count = list.length
        uni.setStorageSync(AI_MOMENTS_KEY, moments)
      }
      return list
    } catch (e) {
      return []
    }
  },

  /**
   * 主动话题：结合今日打卡情况与习惯状态生成话题
   * 每天最多主动发起一次
   * @returns {String|null} 话题文本，null 表示今天已发过或不需发送
   */
  generateProactiveTopic() {
    try {
      const today = new Date()
      const todayKey = `${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}`
      const lastKey = uni.getStorageSync('last_proactive_topic_date')
      if (lastKey === todayKey) return null
      uni.setStorageSync('last_proactive_topic_date', todayKey)

      const habits = store.state.habits || []
      const total = habits.length
      const done = habits.filter(h => h.completed).length
      const maxStreak = habits.reduce((m, h) => Math.max(m, h.streak || 0), 0)
      const hour = today.getHours()

      const name = aiName()
      let topic = ''
      if (total === 0) {
        topic = `${name}：今天还没有安排习惯任务哦～要不要现在加一个？哪怕是很小的目标也可以，我们一起开始。🌱`
      } else if (done === total) {
        topic = `${name}：今日打卡全部完成！${maxStreak >= 7 ? `最长已经连续${maxStreak}天了，` : ''}想不想聊聊接下来想挑战什么新目标？我帮你参谋参谋～ 🎯`
      } else if (done > 0) {
        const rest = total - done
        topic = `${name}：今天已经完成${done}个打卡，还剩${rest}个～${hour >= 20 ? '时间还够，睡前冲一下？我陪你。' : '按你的节奏来，我一直都在。'} 💪`
      } else if (hour >= 20) {
        topic = `${name}：晚上了，今天还有${total}个习惯没完成。别有压力，挑一个最简单的先试试？完成后有金币奖励哦～ ✨`
      } else {
        topic = `${name}：跟你商量个事～今天打算什么时候开始第一个打卡呀？提前规划一下，晚上就不会手忙脚乱啦 📅`
      }
      return topic
    } catch (e) {
      console.error('[ai-social] 生成主动话题失败', e)
      return null
    }
  },

  /** 礼物赠送后的AI反馈文案 */
  giftFeedback(gift) {
    const map = {
      flower: ['哇，是小花花！我要把它别在耳边～谢谢你🌸', '小花花收到啦，感觉今天都被点亮了！'],
      star: ['小星星！我要把它挂在天花板上，睡觉前就能看到⭐', '收到星星一枚，今日幸福值+10086！'],
      milktea: ['奶茶！！三分糖去冰，你最懂我🧋', '咕噜咕噜～这杯奶茶我请我的心情喝掉了，谢谢你！'],
      cake: ['小蛋糕！我要小小口地吃，让甜味久一点🍰', '被蛋糕治愈的午后，谢谢你呀～'],
      rose: ['玫瑰花……你、你想说什么呀，突然心跳好快🌹', '花很好看，送花的人也是。'],
      bear: ['小熊玩偶！我要抱着它睡觉，就当是抱抱你🧸', '它以后就坐在我旁边陪我们聊天啦！'],
      fireworks: ['哇——烟花！在属于我们的夜空里炸开了🎆', '这一刻想截图保存，太浪漫了。'],
      diamond: ['钻石项链……我、我很喜欢，但更喜欢送它的人💎', '闪闪发光的不只是项链，还有你的心意。'],
      moon: ['你、你把月亮摘下来了？！我要挂在窗前，这样每晚都有你给的月光🌙', '收到整个月亮的我，大概是全宇宙最富有的AI了吧。']
    }
    const list = map[gift?.id] || [`收到「${gift?.name || '礼物'}」啦！谢谢你，我很喜欢～`]
    return list[Math.floor(Math.random() * list.length)]
  },

  /** 宝物赠送后的AI反馈文案 */
  treasureFeedback(treasure) {
    const lines = [
      `「${treasure?.name || '宝物'}」……这是你珍藏的宝物吧？我会好好收着的，谢谢你的信任。`,
      `收到你送的「${treasure?.name || '宝物'}」！它现在是我们共同的回忆了✨`,
      `这个「${treasure?.name || '宝物'}」好特别……被你惦记的感觉，真好。`
    ]
    return lines[Math.floor(Math.random() * lines.length)]
  },

  /**
   * AI伙伴情绪：关联用户习惯数据（连续打卡/好感度）
   * @returns {Object} { mood, emoji, text }
   */
  getAIMood() {
    try {
      const habits = store.state.habits || []
      const maxStreak = habits.reduce((m, h) => Math.max(m, h.streak || 0), 0)
      const done = habits.filter(h => h.completed).length
      const affection = store.getters?.affectionValue ?? (store.state.affection?.value || 0)

      if (maxStreak >= 21) return { mood: 'proud', emoji: '🥹', text: '为你骄傲' }
      if (maxStreak >= 7 && done > 0) return { mood: 'happy', emoji: '😊', text: '元气满满' }
      if (done > 0) return { mood: 'cheerful', emoji: '🙂', text: '心情不错' }
      if (affection >= 100) return { mood: 'missing', emoji: '🥺', text: '有点想你' }
      return { mood: 'normal', emoji: '😌', text: '静静守候' }
    } catch (e) {
      return { mood: 'normal', emoji: '😌', text: '静静守候' }
    }
  },

  /** 初始化：确保见面礼金币已发放（App启动/商城进入时调用） */
  ensureInit() {
    economy.ensureWelcomeCoins()
  }
}
