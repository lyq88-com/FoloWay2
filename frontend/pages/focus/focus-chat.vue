<template>
  <view class="xt-page xt-s54">
    <view class="body" style="display: flex; flex-direction: column">
      <!-- 会话头 -->
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-av"><text class="av-emoji">🌿</text></view>
        <view class="chat-meta">
          <view class="chat-name">监督陪伴人</view>
          <view class="chat-st"><i></i>在线 · 只在需要时提醒你</view>
        </view>
        <view class="icon-btn" @click="goRecords"><xt-icon name="i-clock" /></view>
      </view>

      <!-- 相处方式 -->
      <view class="mem-hero" style="padding: 10px 12px; margin: 10px 0 11px">
        <view class="t">我们的相处方式</view>
        <view class="m">我是你的监督陪伴人。可以让我记日程、建待办、设提醒 —— 试试对我说「提醒我九点四十五收拾房间」</view>
      </view>

      <!-- 消息区 -->
      <scroll-view class="chat-scroll" scroll-y :scroll-top="scrollTop" scroll-with-animation>
        <view class="date-sep"><text>轻消息 · 不会震动</text></view>

        <view v-for="(m, i) in messages" :key="i" class="msg" :class="{ me: m.mine }">
          <view v-if="!m.mine" class="msg-av"><text class="av-emoji">🌿</text></view>
          <view class="msg-body">
            <view class="bubble" :class="m.mine ? 'me' : 'ai'">
              <text>{{ m.content }}</text>
            </view>
            <!-- 安排确认条 -->
            <view v-if="m.arrangement" class="arrange">
              <view class="arrange-h">
                <xt-icon name="i-check" />
                <text class="arrange-t">已为你安排</text>
              </view>
              <text class="arrange-task">「{{ m.arrangement.task.title }}」</text>
              <text v-if="m.arrangement.remind_at" class="arrange-remind">提醒：{{ m.arrangement.remind_at }}</text>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- 快捷指令 -->
      <view class="chips">
        <view v-for="(q, i) in quicks" :key="i" class="chip" @click="send(q)">
          <text>{{ q }}</text>
        </view>
      </view>

      <!-- 输入区 -->
      <view class="inputbar">
        <view class="in-field">
          <input v-model="draft" class="chat-input" :maxlength="200" placeholder="说说你的安排或状态…" @confirm="send()" />
        </view>
        <view class="in-send" :class="{ busy: sending }" @click="send()">
          <xt-icon name="i-send" />
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 监督陪伴聊天（模块 E · 陪伴对话）
 * -------------------------------
 * - 监督陪伴人设分支：POST /focus/companion-chat（后端叠加监督人设 prompt）
 * - 指令解析：用户说「提醒我九点四十五收拾房间」→ AI 解析 → 自动建待办 + 提醒
 * - 完全独立接口与页面，不触碰现有 AI 伙伴聊天模块
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      messages: [],
      draft: '',
      sending: false,
      scrollTop: 0,
      history: [],
      quicks: ['提醒我九点四十五收拾房间', '今晚八点提醒我背单词', '明天下午三点写作业', '帮我建一个每日复盘的任务']
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    this.messages.push({
      mine: false,
      content: '你好呀，我是你的监督陪伴人。任何「提醒我…」「明天…点做…」的安排，直接告诉我就好。'
    })
  },
  methods: {
    async send(text) {
      const content = (text || this.draft || '').trim()
      if (!content || this.sending) return
      this.draft = ''
      this.messages.push({ mine: true, content })
      this.sending = true
      try {
        const res = await focusApi.companionChat(content, this.history.slice(-10))
        if (res && res.code === 200) {
          const data = res.data || {}
          this.messages.push({
            mine: false,
            content: data.reply || '收到！',
            arrangement: data.arrangement || null
          })
          this.history.push({ role: 'user', content })
          this.history.push({ role: 'assistant', content: data.reply || '' })
        }
      } catch (e) { /* request 层已提示 */ } finally {
        this.sending = false
        this.$nextTick(() => { this.scrollTop = this.messages.length * 999 })
      }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goRecords() {
      uni.navigateTo({ url: '/pages/focus/focus-records' })
    }
  }
}
</script>

<style lang="scss" scoped>
.xt-page.xt-s54 .body {
  padding-bottom: 0;
}
.xt-page.xt-s54 .chat-head {
  padding-top: 8px;
  flex-shrink: 0;
}

/* 头像（页面无人设头像，用伙伴标记兜底） */
.xt-page.xt-s54 .chat-av {
  border-radius: 50%;
  background: #EDF3F0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s54 .msg-av {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #EDF3F0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.xt-page.xt-s54 .av-emoji {
  font-size: 15px;
}

/* 消息滚动区 */
.xt-page.xt-s54 .chat-scroll {
  flex: 1;
  min-height: 0;
  padding: 2px 2px 0;
}
.xt-page.xt-s54 .msg-body {
  max-width: 244px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.xt-page.xt-s54 .msg.me .msg-body {
  align-items: flex-end;
}

/* 安排确认条 */
.xt-page.xt-s54 .arrange {
  margin-top: 6px;
  width: 100%;
  box-sizing: border-box;
  padding: 9px 11px;
  border-radius: 12px;
  background: rgba(248, 244, 236, 0.9);
  box-shadow: inset 0 0 0 1px rgba(192, 138, 86, 0.2);
}
.xt-page.xt-s54 .arrange-h {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #B57F4C;
}
.xt-page.xt-s54 .arrange-h .ic {
  width: 11px;
  height: 11px;
}
.xt-page.xt-s54 .arrange-t {
  font-size: 8px;
  font-weight: 900;
  color: #B57F4C;
}
.xt-page.xt-s54 .arrange-task {
  display: block;
  margin-top: 4px;
  font-size: 10px;
  color: #22302A;
}
.xt-page.xt-s54 .arrange-remind {
  display: block;
  margin-top: 3px;
  font-size: 7.5px;
  color: #AEB6AE;
}

/* 快捷指令：四条较长，允许换行 */
.xt-page.xt-s54 .chips {
  flex-wrap: wrap;
  flex-shrink: 0;
  margin: 8px 0 6px;
}
.xt-page.xt-s54 .chip text {
  font-size: 8px;
}

/* 输入区 */
.xt-page.xt-s54 .inputbar {
  flex-shrink: 0;
  padding: 6px 2px calc(6px + env(safe-area-inset-bottom));
}
.xt-page.xt-s54 .chat-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 9px;
  color: #22302A;
  background: transparent;
}
.xt-page.xt-s54 .in-send.busy {
  opacity: 0.6;
}
</style>
