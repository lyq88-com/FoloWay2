<template>
  <view class="xt-page xt-s65">
    <view class="body">
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="s65-av"><text class="s65-av-t">🌿</text></view>
        <view class="chat-meta">
          <view class="chat-name">{{ partnerName }} · 助手模式</view>
          <view class="chat-st"><i :class="{ off: serverOnline === false }"></i>{{ onlineText }}</view>
        </view>
        <view class="icon-btn" @click="clearHistory"><xt-icon name="i-archive" /></view>
      </view>

      <view class="chips s65-chips">
        <text
          v-for="(q, qi) in quickQuestions"
          :key="q"
          class="chip"
          :class="{ on: qi === 0 }"
          @click="sendQuick(q)"
        >{{ q }}</text>
      </view>

      <scroll-view class="msg-list" scroll-y :scroll-top="scrollTop" scroll-anchoring>
        <view class="ai-rec s65-welcome">
          <view class="sp"><xt-icon name="i-spark" /></view>
          <view class="tx">
            <view class="k">你好呀，我是{{ partnerName }}</view>
            <view class="p">今天过得怎么样？打卡进展、心情烦恼，都可以跟我聊聊～</view>
          </view>
        </view>

        <view class="date-sep" v-if="messages.length">
          <text>今天 · 助手模式</text>
        </view>

        <view
          v-for="(msg, idx) in messages"
          :key="msg.id"
          class="msg"
          :class="msg.role === 'user' ? 'me' : 'ai'"
        >
          <view v-if="msg.role === 'ai'" class="mav s65-mav"><text class="s65-mav-t">🌿</text></view>
          <view class="bubble" :class="msg.role === 'user' ? 'me' : 'ai'">
            <text class="s65-t">{{ msg.content }}</text>
          </view>
        </view>

        <!-- AI 正在输入（loading状态） -->
        <view v-if="sending" class="msg ai">
          <view class="mav s65-mav"><text class="s65-mav-t">🌿</text></view>
          <view class="bubble ai typing-bubble">
            <view class="typing-dot"></view>
            <view class="typing-dot typing-dot--2"></view>
            <view class="typing-dot typing-dot--3"></view>
          </view>
        </view>

        <!-- 发送失败标记（网络错误重发） -->
        <view v-if="lastFailed" class="retry-bar" @click="retryLast">
          <text class="retry-text">⚠️ {{ lastFailed }}，点击重试</text>
        </view>

        <view class="list-bottom-space"></view>
      </scroll-view>

      <!-- 底部输入区 -->
      <view class="inputbar s65-inputbar" :style="{ paddingBottom: keyboardHeight > 0 ? keyboardHeight + 'px' : 'safe-area' }">
        <view class="in-field">
          <input
            class="s65-in"
            v-model="inputText"
            placeholder="告诉我你想做什么…"
            placeholder-class="s65-ph"
            confirm-type="send"
            :disabled="sending"
            maxlength="500"
            @confirm="sendMessage"
            @focus="onInputFocus"
            @blur="onInputBlur"
          />
        </view>
        <view class="in-send" :class="{ off: !canSend }" @click="sendMessage">
          <xt-icon name="i-send" />
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 循途APP - AI陪伴聊天页（助手模式）
 * 对接 FastAPI：POST /api/v1/chat/quick
 * 入参 {"messages":[{role,content}...]} → 返回 {"reply": "...", "degraded": bool}
 *
 * ★★★ 真机调试必读 ★★★
 * 接口地址统一由 common/env.js 提供：H5 走 vite proxy，真机走局域网绝对地址。
 * 换 WiFi 后跑 tools/sync-lan-host.js 更新即可，本页不再写死 IP。
 *
 * ★★★ 安全红线 ★★★
 * 大模型 API Key 只存在后端 .env（AI_API_KEY），前端与打包产物里绝不能出现。
 */
import { CHARACTERS } from '@/common/ai-characters'
import { API_BASE } from '@/common/env'

// 【2026-11-15 统一 AI 链路】本页原先直连 Flask ai_server.py（5001），
// 与主聊天页的 FastAPI /chat 属于两条独立 AI 链路，人格/降级策略各不相同。
// 现在统一打到 FastAPI POST /api/v1/chat/quick（非流式），Flask AI 服务不再需要启动。
const apiUrl = API_BASE + '/chat/quick'
const healthUrl = API_BASE + '/chat/ai-status'

const STORAGE_KEY = 'ai_chat_history_xuntu'
const MAX_HISTORY = 100 // 本地最多保留条数

let msgId = 1

/**
 * 获取当前选中AI伙伴的性格描述文本（作为 partner_prompt 传给后端）
 * 优先级：store.aiConfig → 角色库 CHARACTERS 匹配 → 默认林夕
 * 返回格式：名字 + 人物简介 + 性格关键词 + 说话风格，供后端拼接动态人设
 */
function buildPartnerPrompt(cfg) {
  try {
    const list = (CHARACTERS || []).filter(c => c && c.personality)
    // 按名字或 avatarType 匹配当前选中伙伴
    let role = null
    if (cfg) {
      role = list.find(c => c.name === cfg.name) ||
             list.find(c => c.id === cfg.avatarType) ||
             null
    }
    role = role || list.find(c => c.id === 'linxi') || list[0] || null
    if (!role) return '温柔、善解人意、细腻、包容'
    const parts = [
      '你叫' + (role.name || '林夕') + '。',
      (role.description || '') + '。',
      '性格：' + (role.personality || '') + '。',
      role.voiceStyle ? '说话风格：' + role.voiceStyle + '。' : '',
      role.catchphrase ? '口头禅：' + role.catchphrase : ''
    ]
    return parts.filter(Boolean).join('')
  } catch (e) {
    // 兜底：角色库不可用时给默认性格
    return '温柔、善解人意、细腻、包容'
  }
}

export default {
  data() {
    return {
      statusBarHeight: 20,
      keyboardHeight: 0,
      inputText: '',
      sending: false,        // loading状态：发送中
      serverOnline: null,    // null=未知 true=在线 false=离线
      degraded: false,       // true=当前回复来自大模型以外的离线兜底
      messages: [],          // [{id, role: 'user'|'ai', content, time}]
      partnerName: '',       // 当前AI伙伴名字（欢迎语展示）
      scrollTop: 0,
      lastFailed: '',        // 最近一次失败原因（展示重试条）
      lastUserMessage: '',   // 用于失败重发
      quickQuestions: [
        '今天打卡成功了！',
        '最近有点 emo',
        '陪我聊聊天',
        '坚持不下去怎么办'
      ]
    }
  },
  computed: {
    navBodyTop() {
      return this.statusBarHeight + 44
    },
    canSend() {
      return !this.sending && this.inputText.trim().length > 0
    },
    onlineText() {
      if (this.degraded) return '离线陪伴'
      if (this.serverOnline === true) return '在线'
      if (this.serverOnline === false) return '离线'
      return '检测中…'
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    // 显示当前选中伙伴的名字（与 partner_prompt 人设一致）
    this.partnerName = (() => {
      try {
        const cfg = this.$store.state.aiConfig || {}
        const role = (CHARACTERS || []).find(c => c.name === cfg.name) ||
                    (CHARACTERS || []).find(c => c.id === cfg.avatarType)
        return (role && role.name) || cfg.name || '林夕'
      } catch (e) {
        return '林夕'
      }
    })()
    this.loadHistory()
    this.checkHealth()
    // 监听键盘高度（真机弹起输入法时把输入框顶上来）
    // ↓↓↓ 修复 ↓↓↓ H5 端没有 uni.onKeyboardHeightChange，直接调用会在 onLoad 里抛错 → 整个页面白屏
    if (typeof uni.onKeyboardHeightChange === 'function') {
      uni.onKeyboardHeightChange(res => {
        this.keyboardHeight = res.height || 0
        if (res.height > 0) this.scrollToBottom()
      })
    }
  },
  onUnload() {
    // ↓↓↓ 修复 ↓↓↓ 同理，H5 没有这个 API
    if (typeof uni.offKeyboardHeightChange === 'function') {
      try { uni.offKeyboardHeightChange() } catch (e) { /* 静默 */ }
    }
  },
  methods: {
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) uni.navigateBack()
      // ↓↓↓ 修复 ↓↓↓ index 不是 tabBar 页，switchTab 过去会失败；用 redirectTo
      else uni.redirectTo({ url: '/pages/index/index' })
    },
    /** 从本地缓存恢复聊天记录 */
    loadHistory() {
      try {
        const list = uni.getStorageSync(STORAGE_KEY)
        if (Array.isArray(list) && list.length) this.messages = list
      } catch (e) { /* 静默 */ }
    },
    saveHistory() {
      try {
        uni.setStorageSync(STORAGE_KEY, this.messages.slice(-MAX_HISTORY))
      } catch (e) { /* 静默 */ }
    },
    clearHistory() {
      uni.showModal({
        title: '清空聊天',
        content: '确定要清空所有聊天记录吗？',
        confirmColor: '#6B8E7B',
        success: res => {
          if (res.confirm) {
            this.messages = []
            this.lastFailed = ''
            this.saveHistory()
            uni.showToast({ title: '已清空', icon: 'success' })
          }
        }
      })
    },
    /** 健康检查：探测 AI 链路是否可用（FastAPI /chat/ai-status） */
    checkHealth() {
      uni.request({
        url: healthUrl,
        method: 'GET',
        timeout: 5000,
        success: res => {
          const body = res.data || {}
          const d = body.data || {}
          this.serverOnline = body.code === 200 && !!d.configured
          this.degraded = !!d.degraded
          if (body.code === 200 && !d.configured) {
            setTimeout(() => {
              uni.showToast({ title: 'AI 未配置，当前为离线陪伴模式', icon: 'none', duration: 2500 })
            }, 600)
          }
        },
        fail: () => {
          this.serverOnline = false
        }
      })
    },
    onInputFocus() { this.scrollToBottom() },
    onInputBlur() { this.keyboardHeight = 0 },
    sendQuick(q) {
      if (this.sending) return
      this.inputText = q
      this.sendMessage()
    },
    pushMessage(role, content) {
      this.messages.push({ id: msgId++, role, content, time: Date.now() })
      this.saveHistory()
      this.scrollToBottom()
    },
    scrollToBottom() {
      // 等 DOM 更新后再滚动
      this.$nextTick(() => {
        setTimeout(() => {
          this.scrollTop = this.scrollTop === 99999 ? 99998 : 99999
        }, 50)
      })
    },
    /** 发送消息（核心） */
    sendMessage() {
      const text = (this.inputText || '').trim()
      if (!text) return
      if (this.sending) {
        uni.showToast({ title: 'AI正在回复中，稍等一下～', icon: 'none' })
        return
      }

      this.inputText = ''
      this.lastFailed = ''
      this.lastUserMessage = text
      this.pushMessage('user', text)
      this.requestAI(text)
    },
    /** 失败重试：重发上一条用户消息 */
    retryLast() {
      if (!this.lastUserMessage || this.sending) return
      this.lastFailed = ''
      this.requestAI(this.lastUserMessage)
    },
    /** 请求后端 /chat/quick，带完整异常处理 */
    requestAI(text) {
      this.sending = true // 显示"正在输入"loading气泡，发送按钮置灰
      // 当前选中AI伙伴的性格描述，作为 system prompt 交给后端
      const partnerPrompt = buildPartnerPrompt(this.$store && this.$store.state.aiConfig)
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      uni.request({
        url: apiUrl,
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        data: {
          messages: [
            { role: 'system', content: partnerPrompt },
            { role: 'user', content: text }
          ]
        },
        timeout: 60000, // 大模型生成较慢，超时给足
        success: res => {
          // HTTP 层异常
          if (res.statusCode !== 200) {
            this.failWith('服务异常(' + res.statusCode + ')')
            return
          }
          const body = res.data || {}
          if (body.code !== 200) {
            this.failWith(body.message || '返回数据异常')
            return
          }
          const d = body.data || {}
          if (typeof d.reply === 'string' && d.reply.trim()) {
            this.pushMessage('ai', d.reply.trim())
            this.serverOnline = true
            this.degraded = !!d.degraded
          } else {
            this.failWith('返回数据异常')
          }
        },
        fail: err => {
          // 网络/超时层异常（真机连不上电脑多为：IP写错、不在同一WiFi、后端没启动、防火墙拦截）
          const msg = (err && err.errMsg) || ''
          if (msg.includes('timeout')) {
            this.failWith('请求超时')
          } else {
            this.serverOnline = false
            this.failWith('连接不上后端')
          }
        },
        complete: () => {
          this.sending = false
        }
      })
    },
    /** 统一失败处理：记录原因 + 提示 */
    failWith(reason) {
      this.lastFailed = reason
      let tip = reason
      if (reason === '连接不上后端') {
        tip = '连接不上后端，请检查：\n1. FastAPI 8000 是否已启动\n2. 手机电脑是否同一WiFi\n3. common/env.js 里的地址是否正确'
      }
      uni.showToast({ title: tip, icon: 'none', duration: 2500 })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 第 65 屏 · AI 对话（助手模式，保留完整聊天链路） */
.xt-page.xt-s65 .body {
  padding: env(safe-area-inset-top) 18px 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.xt-page.xt-s65 .s65-av {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #E8F0EA;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}

.xt-page.xt-s65 .s65-av-t {
  font-size: 16px;
  line-height: 1;
}

.xt-page.xt-s65 .chat-st i.off {
  background: #D9A08A;
}

.xt-page.xt-s65 .s65-chips {
  margin: 8px 0;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.xt-page.xt-s65 .s65-chips .chip {
  flex-shrink: 0;
  white-space: nowrap;
}

.xt-page.xt-s65 .msg-list {
  flex: 1;
  min-height: 0;
}

.xt-page.xt-s65 .s65-welcome {
  margin: 4px 0 0;
}

.xt-page.xt-s65 .s65-mav {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #E8F0EA;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}

.xt-page.xt-s65 .s65-mav-t {
  font-size: 12px;
  line-height: 1;
}

.xt-page.xt-s65 .s65-t {
  white-space: pre-wrap;
  word-break: break-all;
}

.xt-page.xt-s65 .typing-bubble {
  display: flex;
  align-items: center;
  padding: 12px 14px;
}

.xt-page.xt-s65 .typing-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #9CBFAA;
  margin: 0 3px;
  animation: s65Blink 1.2s infinite;
}

.xt-page.xt-s65 .typing-dot--2 {
  animation-delay: 0.2s;
}

.xt-page.xt-s65 .typing-dot--3 {
  animation-delay: 0.4s;
}

.xt-page.xt-s65 .retry-bar {
  margin: 0 auto;
  padding: 7px 14px;
  border-radius: 999px;
  text-align: center;
  background: #FBF3E6;
  box-shadow: inset 0 0 0 1px rgba(192, 138, 86, 0.28);
}

.xt-page.xt-s65 .retry-text {
  font-size: 8px;
  color: #8A5D33;
}

.xt-page.xt-s65 .list-bottom-space {
  height: 16px;
}

.xt-page.xt-s65 .s65-inputbar {
  flex-shrink: 0;
  padding: 8px 0 calc(env(safe-area-inset-bottom) + 8px);
  background: rgba(255, 252, 246, 0.96);
}

.xt-page.xt-s65 .s65-in {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 9px;
  color: #22302A;
  background: transparent;
}

.xt-page.xt-s65 .s65-ph {
  color: #BFC7BF;
}

.xt-page.xt-s65 .in-send.off {
  opacity: 0.45;
}

@keyframes s65Blink {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}
</style>
