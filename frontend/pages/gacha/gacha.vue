<template>
  <view class="xt-page xt-s8">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">互动扭蛋</view>
          <view class="page-sub">今天和她发生一点意外</view>
        </view>
        <view class="icon-btn" @click="showRecords = true"><xt-icon name="i-clock" /></view>
      </view>

      <view class="gacha-stage">
        <view class="capsule" :class="{ 'is-drawing': drawing }" @click="draw">
          <view class="shine"></view>
          <image v-if="capsulePhoto" :src="capsulePhoto" mode="aspectFill" />
          <text v-else class="capsule-emoji">{{ capsuleEmoji }}</text>
        </view>
        <text class="gacha-tag">{{ gachaTag }}</text>
        <view class="gacha-btn" @click="draw">
          <text>{{ drawing ? '扭蛋滚动中…' : '扭一次' }}</text>
          <xt-icon name="i-spark" />
        </view>
      </view>

      <view class="prob">
        <view class="pr"><text class="tag ssr">SSR</text><text class="pt">双人专属剧情 · 可保存</text><text class="b">2%</text></view>
        <view class="pr"><text class="tag sr">SR</text><text class="pt">角色私藏语音 · 30 秒</text><text class="b">28%</text></view>
        <view class="pr"><text class="tag r">R</text><text class="pt">日常互动 · 小礼物</text><text class="b">70%</text></view>
      </view>

      <view class="cal-sec" style="margin-top: 11px">
        <text class="t">最近扭到</text>
        <text class="s">图鉴 {{ templates.length }} / 60</text>
      </view>
      <view class="postcards">
        <view v-for="(c, i) in recentCards" :key="i" class="pcard">
          <view class="ph" :style="{ background: cardBgs[i] }"><xt-icon :name="c.icon" /></view>
          <view class="pn">{{ c.name }}</view>
        </view>
      </view>
    </view>

    <!-- ===== 抽取结果弹窗 ===== -->
    <view class="modal-mask" v-if="drawResult" @click="closeDraw">
      <view class="result-card" @click.stop>
        <view class="result-glow"><text class="result-egg">🥚</text></view>
        <text class="result-label">抽中了</text>
        <text class="result-title">{{ drawResult.template.title }}</text>
        <text class="result-desc">{{ drawResult.template.description }}</text>
        <view class="result-btns">
          <text class="r-btn ghost" @click="closeDraw">稍后再玩</text>
          <text class="r-btn primary" @click="startStory">开始剧本 →</text>
        </view>
      </view>
    </view>

    <!-- ===== 角色抽取结果 ===== -->
    <view class="modal-mask" v-if="drawChar" @click="closeChar">
      <view class="char-result" @click.stop>
        <view class="cr-top">
          <text class="cr-rarity" :class="'r-' + drawChar.rarity">{{ drawChar.rarityLabel }}</text>
          <text class="cr-avatar">{{ drawChar.avatar }}</text>
          <text class="cr-name">{{ drawChar.name }}</text>
          <text class="cr-tag">{{ drawChar.personality }}</text>
        </view>

        <scroll-view scroll-y class="cr-body">
          <view class="cr-greeting">「{{ drawChar.greeting || drawChar.catchphrase }}」</view>

          <view class="cr-block" v-if="drawChar.backstory">
            <text class="cr-label">TA 的故事</text>
            <text class="cr-text">{{ drawChar.backstory }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.speechStyle">
            <text class="cr-label">怎么说话</text>
            <text class="cr-text">{{ drawChar.speechStyle }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.quirks">
            <text class="cr-label">小癖好</text>
            <text class="cr-text">{{ drawChar.quirks }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.expressionHabits">
            <text class="cr-label">表达习惯</text>
            <text class="cr-text">{{ drawChar.expressionHabits }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.taboos">
            <text class="cr-label">雷区</text>
            <text class="cr-text">{{ drawChar.taboos }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.angryStyle">
            <text class="cr-label">生气时</text>
            <text class="cr-text">{{ drawChar.angryStyle }}</text>
          </view>
          <view class="cr-block" v-if="drawChar.happyStyle">
            <text class="cr-label">开心时</text>
            <text class="cr-text">{{ drawChar.happyStyle }}</text>
          </view>

          <view class="cr-foot-note">
            TA 已经有了一间只属于自己的记忆小屋，之后你们聊过的一切都不会和别的角色混在一起。
          </view>
        </scroll-view>

        <view class="cr-btns">
          <text class="cr-btn ghost" @click="closeChar">先认识一下</text>
          <text class="cr-btn primary" @click="chatWithChar">去找 TA 聊聊 →</text>
        </view>
      </view>
    </view>

    <!-- ===== 剧本问答弹窗 ===== -->
    <view class="modal-mask story-mask" v-if="story.active">
      <view class="story-card">
        <view class="story-head">
          <text class="story-title">{{ story.title }}</text>
          <text class="story-close" @click="closeStory">✕</text>
        </view>
        <scroll-view scroll-y class="story-body" :scroll-top="storyScrollTop">
          <view class="story-msg" v-for="(m, i) in story.messages" :key="i">
            <text class="msg-role">{{ m.role === 'ai' ? '🤖 AI伙伴' : '🙋 我' }}</text>
            <text class="msg-content" :class="{ mine: m.role !== 'ai' }">{{ m.content }}</text>
          </view>
          <view class="story-q" v-if="story.currentQ">
            <text class="msg-role">🤖 AI伙伴</text>
            <text class="q-text">{{ story.currentQ.question }}</text>
            <view class="q-options">
              <text
                class="q-opt"
                v-for="(opt, i) in story.currentQ.options"
                :key="i"
                @click="answer(opt)">{{ opt }}</text>
            </view>
            <text class="q-hint" v-if="story.currentQ.hint">💡 {{ story.currentQ.hint }}</text>
          </view>
          <view class="story-end" v-if="story.finished">
            <text class="end-text">🎭 剧本已完满落幕</text>
            <text class="end-sub">对话已保存到聊天历史，随时可以回味</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- ===== 自创剧本弹窗 ===== -->
    <view class="modal-mask" v-if="showCreate" @click="showCreate = false">
      <scroll-view scroll-y class="create-scroll" @click.stop>
        <view class="create-card" @click.stop>
          <text class="modal-title">创建你的扭蛋剧本</text>
          <input class="m-input" v-model="cf.title" placeholder="剧本标题" placeholder-class="m-ph" />
          <input class="m-input" v-model="cf.description" placeholder="剧本简介" placeholder-class="m-ph" />
          <view class="cat-row left">
            <text
              class="cat-chip"
              :class="{ active: cf.category === 'companion' }"
              @click="cf.category = 'companion'">🎯 陪伴打卡</text>
            <text
              class="cat-chip"
              :class="{ active: cf.category === 'emotion' }"
              @click="cf.category = 'emotion'">🌊 情绪倾诉</text>
            <text
              class="cat-chip"
              :class="{ active: cf.category === 'chat' }"
              @click="cf.category = 'chat'">💬 趣味闲聊</text>
          </view>
          <textarea
            class="m-textarea"
            v-model="cf.opening_text"
            placeholder="AI开场白(扭蛋打开后AI说的第一句话)"
            placeholder-class="m-ph" />
          <view
            class="q-edit"
            v-for="(q, qi) in cf.questions"
            :key="qi">
            <view class="q-edit-head">
              <text class="q-edit-label">问题 {{ qi + 1 }}</text>
              <text class="q-del" @click="cf.questions.splice(qi, 1)">✕</text>
            </view>
            <input class="m-input" v-model="q.question" placeholder="问题内容" placeholder-class="m-ph" />
            <input class="m-input" v-model="q.hint" placeholder="AI回应提示(可选)" placeholder-class="m-ph" />
          </view>
          <text class="add-q" @click="cf.questions.push({ question: '', options: [], hint: '' })">＋ 添加问题</text>
          <view class="m-btns">
            <text class="m-btn cancel" @click="showCreate = false">取消</text>
            <text class="m-btn confirm" @click="submitCreate">发布</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- ===== 抽取记录弹窗 ===== -->
    <view class="modal-mask" v-if="showRecords" @click="showRecords = false">
      <view class="records-card" @click.stop>
        <view class="story-head">
          <text class="modal-title">我的扭蛋币 · {{ wallet.coin_balance }}</text>
          <text class="story-close" @click="showRecords = false">✕</text>
        </view>
        <view class="rec-tools">
          <text class="rec-chip" :class="{ on: drawCategory === '' }" @click="drawCategory = ''">全部</text>
          <text class="rec-chip" :class="{ on: drawCategory === 'companion' }" @click="drawCategory = 'companion'">陪伴打卡</text>
          <text class="rec-chip" :class="{ on: drawCategory === 'emotion' }" @click="drawCategory = 'emotion'">情绪倾诉</text>
          <text class="rec-chip" :class="{ on: drawCategory === 'chat' }" @click="drawCategory = 'chat'">趣味闲聊</text>
        </view>
        <scroll-view scroll-y class="records-body">
          <view class="rec-item" v-for="r in records" :key="r.record_id">
            <view class="rec-main">
              <text class="rec-title">{{ r.title }}</text>
              <text class="rec-meta">{{ r.created_at }} · {{ catLabel(r.category) }}</text>
            </view>
            <text class="rec-status" :class="{ done: r.status === 'finished' }">
              {{ r.status === 'finished' ? '已完场' : '进行中' }}
            </text>
          </view>
          <view class="empty-state" v-if="records.length === 0">
            <text class="empty-sub">还没有抽取记录</text>
          </view>
        </scroll-view>
        <view class="rec-actions">
          <text class="rec-btn" @click="drawCharacter">{{ drawingChar ? '正在呼唤…' : '抽一位伙伴' }}</text>
          <text class="rec-btn primary" @click="showRecords = false; openCreate()">＋ 自创剧本</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 【四大新增模块·模块3】互动扭蛋机页
 * 与打卡系统联动: 扭蛋币通过每日打卡赚取(每打卡一个习惯+10), 不需要充值
 * 抽取后 AI 直接开启剧本对话, 对话记录写入聊天历史(可在聊天页回看)
 */
import gachaApi from '@/api/gacha'
// ↓↓↓ 安全合规批次：剧本内容本地前置校验（后端同源兜底） ↓↓↓
import { checkContent } from '@/common/content-check'
// ↑↑↑ 新增结束 ↑↑↑
// ↓↓↓ 陪伴感增强 v3：角色扭蛋（完整人设 + 独立记忆空间） ↓↓↓
import personaApi from '@/api/persona'
// ↑↑↑ 新增结束 ↑↑↑
import { getActivePartner, getPartnerPhoto, saveActivePartner } from '@/common/ai-partner'

export default {
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      wallet: { coin_balance: 0, total_earned: 0, total_cost: 0 },
      activeTab: 'recommend',
      drawCategory: '',
      tabs: [
        { key: 'recommend', label: '推荐' },
        { key: 'hot', label: '最热' },
        { key: 'favorite', label: '收藏' },
        { key: 'mine', label: '我创建' }
      ],
      templates: [],
      loading: false,
      drawing: false,
      drawResult: null,
      // ↓↓↓ 陪伴感增强 v3 ↓↓↓
      drawingChar: false,
      drawChar: null,
      charPool: [],
      // ↑↑↑ 新增结束 ↑↑↑
      story: {
        active: false,
        title: '',
        recordId: 0,
        sessionId: 0,
        questions: [],
        qIndex: 0,
        currentQ: null,
        messages: [],
        finished: false
      },
      storyScrollTop: 0,
      showCreate: false,
      cf: { title: '', description: '', category: 'chat', opening_text: '', questions: [{ question: '', options: [], hint: '' }] },
      showRecords: false,
      records: []
    }
  },
  computed: {
    capsulePhoto() {
      return getPartnerPhoto(getActivePartner()) || ''
    },
    capsuleEmoji() {
      const p = getActivePartner()
      return (p && p.avatar) || '✨'
    },
    gachaTag() {
      return `今日免费 1 次 · 扭蛋币 ${this.wallet.coin_balance}`
    },
    cardBgs() {
      return [
        'linear-gradient(145deg,#8FB79E,#24493A)',
        'linear-gradient(145deg,#C08A56,#A87A5E)',
        'linear-gradient(145deg,#93A9B8,#4A5C68)'
      ]
    },
    recentCards() {
      const icons = ['i-moon', 'i-heart', 'i-book']
      const list = (this.templates || []).slice(0, 3)
      if (!list.length) {
        return [
          { name: '月下散步', icon: icons[0] },
          { name: '递一杯热茶', icon: icons[1] },
          { name: '共读一页', icon: icons[2] }
        ]
      }
      return list.map((t, i) => ({ name: t.title, icon: icons[i % icons.length] }))
    }
  },
  onShow() {
    this.loadWallet()
    this.loadTemplates()
    // ↓↓↓ 陪伴感增强 v3 ↓↓↓
    this.loadCharPool()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },

    catLabel(c) {
      const map = { companion: '🎯 陪伴打卡', emotion: '🌊 情绪倾诉', chat: '💬 趣味闲聊' }
      return map[c] || c
    },

    // ===== 钱包 =====
    async loadWallet() {
      try {
        const res = await gachaApi.getWallet()
        if (res && res.data) this.wallet = res.data
      } catch (e) { /* 静默 */ }
    },

    // ===== 剧本列表 =====
    async loadTemplates() {
      this.loading = true
      try {
        const res = await gachaApi.getList(this.activeTab, this.drawCategory === '' ? '' : this.drawCategory)
        this.templates = (res && res.data) || []
      } catch (e) {
        this.templates = []
      }
      this.loading = false
    },
    switchTab(key) {
      this.activeTab = key
      this.loadTemplates()
    },

    // ===== 收藏 =====
    async toggleFav(t) {
      try {
        const res = await gachaApi.toggleFavorite(t.id)
        const data = (res && res.data) || {}
        t.favored = data.favored
        t.favorite_count = data.favorite_count
      } catch (e) {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    },

    // ===== 扭蛋抽取 =====
    async draw() {
      if (this.drawing) return
      this.drawing = true
      try {
        const res = await gachaApi.draw(this.drawCategory)
        // 播放滚动动画后弹出结果
        setTimeout(() => {
          this.drawing = false
          this.drawResult = res.data
          this.loadWallet()
          this.loadTemplates()
        }, 900)
      } catch (e) {
        this.drawing = false
        uni.showToast({ title: (e && e.message) || '抽取失败', icon: 'none' })
      }
    },
    closeDraw() {
      this.drawResult = null
    },

    // ↓↓↓ 陪伴感增强 v3：角色扭蛋 ↓↓↓
    async loadCharPool() {
      try {
        const res = await personaApi.getGachaPool()
        this.charPool = (res && res.data) || []
      } catch (e) {
        this.charPool = []
      }
    },
    async drawCharacter() {
      if (this.drawingChar) return
      this.drawingChar = true
      try {
        const res = await personaApi.drawGachaCharacter()
        this.drawChar = (res && res.data) || null
        this.loadCharPool()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '抽取失败', icon: 'none' })
      } finally {
        this.drawingChar = false
      }
    },
    closeChar() {
      this.drawChar = null
    },
    chatWithChar() {
      const c = this.drawChar
      if (!c) return
      // 把角色写进全局配置，聊天页就会用 TA 的身份与记忆空间对话
      try {
        saveActivePartner(c.roleKey, c.name, { profile: { ...c, id: c.roleKey } })
      } catch (e) {
        console.log('切换角色失败', e)
      }
      this.drawChar = null
      uni.switchTab({
        url: '/pages/chat/chat',
        fail: () => {
          uni.showToast({ title: '已抽到，去「我的」里切换角色吧', icon: 'none' })
        }
      })
    },
    // ↑↑↑ 新增结束 ↑↑↑

    // ===== 开启剧本问答 =====
    startStory() {
      const r = this.drawResult
      this.story = {
        active: true,
        title: r.template.title,
        recordId: r.record_id,
        sessionId: r.session_id,
        questions: r.questions || [],
        qIndex: 0,
        currentQ: (r.questions && r.questions[0]) || null,
        messages: [{ role: 'ai', content: r.template.opening_text || '剧本开始啦~' }],
        finished: false
      }
      this.drawResult = null
    },
    async answer(opt) {
      if (!this.story.currentQ || this.story.finished) return
      const q = this.story.currentQ
      const qi = this.story.qIndex
      this.story.messages.push({ role: 'me', content: opt })
      this.story.currentQ = null
      try {
        const res = await gachaApi.answer(this.story.recordId, qi, opt)
        const data = (res && res.data) || {}
        this.story.messages.push({ role: 'ai', content: data.reply || '' })
        if (data.finished) {
          this.story.finished = true
        } else {
          this.story.qIndex = data.next_question_index
          this.story.currentQ = this.story.questions[data.next_question_index] || null
        }
        this.scrollStory()
      } catch (e) {
        this.story.messages.push({ role: 'ai', content: '抱歉, 回应出了点小问题...' })
      }
    },
    scrollStory() {
      this.$nextTick(() => {
        this.storyScrollTop = this.storyScrollTop + 99999
      })
    },
    closeStory() {
      this.story.active = false
      this.loadTemplates()
    },

    // ===== 自创剧本 =====
    openCreate() {
      this.cf = {
        title: '', description: '', category: 'chat',
        opening_text: '', questions: [{ question: '', options: [], hint: '' }]
      }
      this.showCreate = true
    },
    async submitCreate() {
      if (!this.cf.title.trim()) {
        uni.showToast({ title: '请填写剧本标题', icon: 'none' })
        return
      }
      // ↓↓↓ 安全合规批次：标题/描述/开场白/题目本地安全校验，命中直接拦截 ↓↓↓
      const secTexts = [this.cf.title, this.cf.description, this.cf.opening_text]
      for (const q of this.cf.questions) {
        secTexts.push(q.question)
        secTexts.push(...(q.options || []))
        secTexts.push(q.hint)
      }
      for (const t of secTexts) {
        const sec = checkContent((t || '').trim())
        if (!sec.ok) {
          uni.showToast({ title: sec.reason, icon: 'none', duration: 2500 })
          return
        }
      }
      // ↑↑↑ 新增结束 ↑↑↑
      const questions = this.cf.questions
        .filter(q => q.question.trim())
        .map(q => ({ question: q.question.trim(), options: q.options || [], hint: q.hint || '' }))
      try {
        await gachaApi.create({
          title: this.cf.title.trim(),
          description: this.cf.description,
          category: this.cf.category,
          opening_text: this.cf.opening_text,
          questions
        })
        this.showCreate = false
        uni.showToast({ title: '剧本已发布', icon: 'success' })
        this.activeTab = 'mine'
        this.loadTemplates()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '发布失败', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
.xt-page.xt-s8 .capsule uni-image {
  width: 72px;
  height: 96px;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 0 0 3px var(--v7-card);
}
.xt-page.xt-s8 .capsule :deep(uni-image > div),
.xt-page.xt-s8 .capsule :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 18px;
}
.xt-page.xt-s8 .capsule :deep(uni-image img) {
  object-fit: cover;
  box-shadow: none;
}
.xt-page.xt-s8 .capsule-emoji { font-size: 40px; line-height: 1; }
.xt-page.xt-s8 .gacha-stage .capsule:active { transform: scale(0.97); }
.xt-page.xt-s8 .prob .pr .pt { color: #6A776E; }
.xt-page.xt-s8 .prob .pr .b { margin-left: auto; font-size: 8.5px; font-weight: 700; color: #22302A; }

/* ===== 弹窗通用 ===== */
.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(34, 48, 42, 0.45);
}
.modal-title { font-size: 14px; font-weight: 800; color: #22302A; }

/* 抽取结果 */
.result-card {
  width: 288px;
  padding: 24px 18px 18px;
  border-radius: 20px;
  background: var(--v7-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.result-glow {
  width: 86px; height: 86px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(156, 191, 170, 0.5), rgba(255, 252, 246, 0));
  display: flex; align-items: center; justify-content: center;
}
.result-egg { font-size: 42px; }
.result-label { margin-top: 10px; font-size: 8px; letter-spacing: 3px; color: #B4BDB9; }
.result-title { margin-top: 5px; font-size: 17px; font-weight: 800; color: #22302A; }
.result-desc { margin-top: 6px; font-size: 9.5px; line-height: 1.65; color: #8E9A91; text-align: center; }
.result-btns { display: flex; gap: 8px; margin-top: 16px; width: 100%; }
.r-btn { flex: 1; text-align: center; padding: 10px 0; border-radius: 999px; font-size: 10.5px; font-weight: 700; }
.r-btn.ghost { background: rgba(255, 253, 250, 0.8); color: #6A776E; }
.r-btn.primary { background: linear-gradient(140deg, #4E7A64, #24493A); color: #FFFDFA; }

/* 角色抽取结果 */
.char-result {
  width: 320px;
  max-height: 86vh;
  border-radius: 20px;
  background: var(--v7-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.cr-top {
  padding: 20px 16px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(180deg, #F4F7F4, rgba(255, 252, 246, 0));
}
.cr-rarity { font-size: 8px; padding: 3px 9px; border-radius: 999px; background: #F8F3ED; color: #B8874E; }
.cr-avatar { font-size: 44px; margin-top: 6px; }
.cr-name { font-size: 18px; font-weight: 800; color: #22302A; margin-top: 4px; }
.cr-tag { font-size: 10px; color: #8E9A91; margin-top: 3px; }
.cr-body { padding: 0 16px; max-height: 40vh; height: 40vh; }
.cr-greeting { font-size: 11px; color: var(--v7-green); line-height: 1.7; padding: 10px 0; border-bottom: 1px solid var(--v7-line); }
.cr-block { padding: 8px 0; }
.cr-label { font-size: 9px; font-weight: 800; color: var(--v7-green); }
.cr-text { display: block; margin-top: 3px; font-size: 10.5px; line-height: 1.7; color: #4A564E; }
.cr-foot-note { font-size: 8.5px; line-height: 1.7; color: #B4BDB9; padding: 9px 0 14px; }
.cr-btns { display: flex; gap: 8px; padding: 10px 16px 14px; }
.cr-btn { flex: 1; padding: 10px 0; text-align: center; border-radius: 999px; font-size: 10.5px; font-weight: 700; }
.cr-btn.ghost { background: rgba(255, 253, 250, 0.8); color: #6A776E; }
.cr-btn.primary { background: linear-gradient(140deg, #4E7A64, #24493A); color: #FFFDFA; }

/* 剧本问答 */
.story-card {
  width: 320px;
  height: 78vh;
  border-radius: 20px;
  background: var(--v7-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.story-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--v7-line);
}
.story-title { font-size: 13px; font-weight: 800; color: #22302A; }
.story-close { font-size: 13px; color: #A2AAA3; padding: 0 5px; }
.story-body { flex: 1; height: 0; padding: 12px 16px; box-sizing: border-box; }
.story-msg { display: flex; flex-direction: column; margin-bottom: 10px; }
.msg-role { font-size: 8px; color: #A2AAA3; margin-bottom: 4px; }
.msg-content {
  align-self: flex-start;
  font-size: 10.5px;
  line-height: 1.6;
  color: #333E37;
  background: var(--v7-card);
  border-radius: 3px 14px 14px 14px;
  padding: 8px 10px;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.msg-content.mine {
  align-self: flex-end;
  color: #FFFDFA;
  background: linear-gradient(140deg, #4E7A64, #24493A);
  border-radius: 14px 3px 14px 14px;
  box-shadow: none;
}
.story-q { margin-top: 6px; }
.q-text { display: block; font-size: 11px; line-height: 1.6; color: #22302A; font-weight: 700; margin-bottom: 8px; }
.q-options { display: flex; flex-direction: column; gap: 6px; }
.q-opt {
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--v7-card);
  font-size: 10px;
  color: var(--v7-green);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.q-opt:active { background: #F2F6F3; }
.q-hint { display: block; margin-top: 6px; font-size: 8.5px; color: #B4BDB9; }
.story-end { padding: 16px 0; display: flex; flex-direction: column; align-items: center; }
.end-text { font-size: 11px; font-weight: 800; color: var(--v7-green); }
.end-sub { margin-top: 4px; font-size: 8.5px; color: #AEB6AE; }

/* 自创剧本 */
.create-scroll { width: 320px; max-height: 76vh; background: var(--v7-card); border-radius: 18px; }
.create-card { padding: 18px 16px; }
.m-input {
  width: 100%;
  height: 36px;
  margin-top: 9px;
  padding: 0 12px;
  box-sizing: border-box;
  border-radius: 10px;
  background: #F7F3EA;
  font-size: 10px;
  color: #22302A;
}
.m-textarea {
  width: 100%;
  height: 64px;
  margin-top: 9px;
  padding: 8px 12px;
  box-sizing: border-box;
  border-radius: 10px;
  background: #F7F3EA;
  font-size: 10px;
  line-height: 1.6;
  color: #22302A;
}
.m-ph { color: #BFC7BF; }
.cat-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }
.cat-chip { font-size: 9px; padding: 5px 10px; border-radius: 999px; background: #F7F3EA; color: #6A776E; }
.cat-chip.active { background: var(--v7-green); color: #FFFDFA; font-weight: 700; }
.q-edit { margin-top: 10px; padding: 10px; border-radius: 12px; background: #FBF7F0; }
.q-edit-head { display: flex; align-items: center; justify-content: space-between; }
.q-edit-label { font-size: 9px; font-weight: 800; color: #3C5248; }
.q-del { font-size: 11px; color: #B4BDB9; padding: 0 4px; }
.add-q { display: block; margin-top: 10px; font-size: 10px; font-weight: 700; color: var(--v7-green); }
.m-btns { display: flex; gap: 8px; margin-top: 14px; }
.m-btn { flex: 1; text-align: center; padding: 10px 0; border-radius: 999px; font-size: 10.5px; font-weight: 700; }
.m-btn.cancel { background: rgba(255, 253, 250, 0.8); color: #6A776E; }
.m-btn.confirm { background: linear-gradient(140deg, #4E7A64, #24493A); color: #FFFDFA; }

/* 抽取记录 */
.records-card {
  width: 320px;
  max-height: 76vh;
  border-radius: 18px;
  background: var(--v7-card);
  padding: 14px 16px 16px;
  box-sizing: border-box;
}
.rec-tools { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.rec-chip { font-size: 8.5px; padding: 4px 9px; border-radius: 999px; background: rgba(255, 253, 250, 0.8); color: #6A776E; }
.rec-chip.on { background: var(--v7-green); color: #FFFDFA; font-weight: 700; }
.records-body { height: 230px; margin-top: 8px; }
.rec-item {
  display: flex;
  align-items: center;
  padding: 9px 10px;
  margin-bottom: 7px;
  border-radius: 11px;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.rec-main { flex: 1; min-width: 0; }
.rec-title { display: block; font-size: 10.5px; font-weight: 700; color: #22302A; }
.rec-meta { display: block; margin-top: 2px; font-size: 8px; color: #AEB6AE; }
.rec-status { font-size: 8px; color: #B8874E; }
.rec-status.done { color: #AEB6AE; }
.rec-actions { display: flex; gap: 8px; margin-top: 10px; }
.rec-btn {
  flex: 1;
  text-align: center;
  padding: 9px 0;
  border-radius: 999px;
  background: rgba(255, 253, 250, 0.8);
  color: #6A776E;
  font-size: 10px;
  font-weight: 700;
}
.rec-btn.primary { background: linear-gradient(140deg, #4E7A64, #24493A); color: #FFFDFA; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 24px 0; }
.empty-sub { font-size: 9px; color: #B4BDB9; }
</style>
