<template>
  <view class="xt-page xt-s41">
    <view class="body chat-body">
      <!-- 顶部：返回 / 头像 / 昵称 -->
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <image v-if="other.avatar" class="head-av" :src="other.avatar" mode="aspectFill" />
        <view v-else class="head-av ph"><text class="head-av-t">{{ initial }}</text></view>
        <view class="chat-meta">
          <view class="chat-name">{{ other.nickname || '同频的人' }}</view>
          <view class="chat-st">因为同一句话认识 · 在线</view>
        </view>
        <view class="icon-btn" @click="openSettings"><xt-icon name="i-settings" /></view>
      </view>

      <!-- 共鸣上下文 -->
      <view class="mem-hero" style="padding:10px 12px;margin-bottom:11px">
        <view class="t" style="font-size:7px;color:#8E9A91;letter-spacing:.4px">你们共鸣的那句话</view>
        <view class="m" style="margin-top:3px;font-size:9px;color:#505B56;font-weight:800">“{{ resonanceText || '因为同一句话认识，你们更懂彼此' }}”</view>
      </view>

      <!-- 对话流 -->
      <scroll-view
        class="chat-scroll"
        scroll-y
        :scroll-into-view="scrollInto"
        scroll-with-animation
      >
        <view class="date-sep"><text>今天</text></view>

        <view v-for="(m, i) in list" :key="m.id || i" :id="`msg-${i}`">
          <view class="msg" :class="{ me: m.mine }">
            <image v-if="!m.mine && other.avatar" class="mav" :src="other.avatar" mode="aspectFill" />
            <view v-else-if="!m.mine" class="mav ph"><text class="mav-t">{{ initial }}</text></view>
            <view class="bubble" :class="m.mine ? 'me' : 'ai'">
              <text>{{ m.content }}</text>
              <text class="btime">{{ shortTime(m.create_time) }}</text>
            </view>
          </view>
        </view>

        <view v-if="!loading && !list.length" class="date-sep" style="margin-top:18px">
          <text>你们因共鸣相遇，打个招呼吧~</text>
        </view>
      </scroll-view>

      <!-- 快捷短句 -->
      <view class="chips" style="margin-bottom:8px">
        <text class="chip on" @click="draft = '一起专注 10 分钟？'">一起专注 10 分钟</text>
        <text class="chip" @click="draft = '今天互相打个卡吧'">互相打卡</text>
      </view>

      <!-- 输入栏 -->
      <view class="inputbar">
        <input
          v-model="draft"
          class="in-field"
          placeholder="说点什么…"
          placeholder-style="color:#BFC7BF"
          confirm-type="send"
          :adjust-position="true"
          style="color:#22302A"
          @confirm="onSend"
        />
        <view class="in-send" @click="onSend"><xt-icon name="i-send" :size="14" /></view>
      </view>
    </view>

    <!-- 会话设置 -->
    <view v-if="settingsVisible" class="sheet-mask" @click="closeSettings">
      <view class="sheet" @click.stop>
        <view class="sheet-title">会话设置</view>
        <view class="sheet-row">
          <view class="sheet-tx">
            <view class="sheet-t">消息免打扰</view>
            <view class="sheet-d">开启后不再自动刷新对方的新消息</view>
          </view>
          <switch :checked="muted" color="#2E6B4F" @change="onMuteChange" />
        </view>
        <view class="sheet-row" @click="blockOther">
          <view class="sheet-tx">
            <view class="sheet-t">拉黑对方</view>
            <view class="sheet-d">会话将从列表隐藏，双方无法继续发消息</view>
          </view>
          <text class="sheet-arrow">›</text>
        </view>
        <view class="sheet-cancel" @click="closeSettings">取消</view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 小想法 · 真人私聊（双向点亮后开放）
 * 数据来源：GET  /idea/conversation/{id} → { other:{nickname,avatar}, list[] }
 * 发送：    POST /idea/conversation/{id} { content } → 新消息
 * 进入时清对方未读（后端自动处理）；发送后滚到底部。
 */
import ideaApi from '@/api/idea'
import http from '@/common/request'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      conversationId: 0,
      other: { nickname: '', avatar: '' },
      list: [],
      draft: '',
      loading: false,
      scrollInto: '',
      pollTimer: null,
      settingsVisible: false,
      muted: false,
      resonanceText: '',
      blocking: false
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    initial() {
      const n = this.other.nickname || ''
      return n ? n.slice(0, 1) : '友'
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    this.conversationId = parseInt(options.id || options.conversationId || 0, 10)
    if (this.conversationId) {
      this.muted = uni.getStorageSync(`idea_mute_${this.conversationId}`) === '1'
    }
  },
  onShow() {
    if (this.conversationId) this.loadMessages()
    this.startPoll()
  },
  onHide() { this.stopPoll() },
  onUnload() { this.stopPoll() },
  methods: {
    startPoll() {
      this.stopPoll()
      // 免打扰时不做 5s 轮询，进入页面仍会主动拉一次
      if (this.muted) return
      this.pollTimer = setInterval(() => {
        if (this.conversationId && !this.loading) this.loadMessages(true)
      }, 5000)
    },
    stopPoll() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
    openSettings() {
      this.settingsVisible = true
    },
    closeSettings() {
      this.settingsVisible = false
    },
    onMuteChange(e) {
      this.muted = !!(e.detail && e.detail.value)
      try {
        uni.setStorageSync(`idea_mute_${this.conversationId}`, this.muted ? '1' : '0')
      } catch (err) { /* 静默 */ }
      this.startPoll()
      uni.showToast({ title: this.muted ? '已开启免打扰' : '已关闭免打扰', icon: 'none' })
    },
    blockOther() {
      if (this.blocking || !this.other.id) return
      uni.showModal({
        title: '拉黑对方',
        content: '拉黑后会话会从列表隐藏，双方无法继续发消息。确定拉黑吗？',
        confirmText: '拉黑',
        confirmColor: '#C4564A',
        success: async (r) => {
          if (!r.confirm) return
          this.blocking = true
          try {
            const res = await ideaApi.blockUser(this.other.id)
            if (res && res.code === 200) {
              this.settingsVisible = false
              uni.showToast({ title: '已拉黑', icon: 'success' })
              setTimeout(() => this.goBack(), 600)
            }
          } catch (e) { /* request 层已提示 */ } finally {
            this.blocking = false
          }
        }
      })
    },
    async loadMessages(silent = false) {
      if (!silent) this.loading = true
      try {
        const res = await ideaApi.getConversation(this.conversationId)
        const data = (res && res.data) || {}
        this.other = {
          nickname: (data.other && data.other.nickname) || '同频的人',
          avatar: (data.other && data.other.avatar) ? http.toAvatarUrl(data.other.avatar) : '',
          id: (data.other && data.other.id) || 0
        }
        this.resonanceText = data.resonance_text || ''
        const prevLen = this.list.length
        this.list = data.list || []
        if (this.list.length !== prevLen || !silent) {
          this.$nextTick(() => this.scrollToBottom())
        }
      } catch (e) {
        /* request 层已提示 */
      } finally {
        this.loading = false
      }
    },
    async onSend() {
      const content = this.draft.trim()
      if (!content) return
      try {
        const res = await ideaApi.sendMessage(this.conversationId, content)
        if (res && res.code === 200) {
          this.draft = ''
          this.list.push(res.data)
          this.$nextTick(() => this.scrollToBottom())
        }
      } catch (e) { /* request 层已提示 */ }
    },
    scrollToBottom() {
      const idx = Math.max(this.list.length - 1, 0)
      this.scrollInto = ''
      this.$nextTick(() => { this.scrollInto = `msg-${idx}` })
    },
    shortTime(t) {
      if (!t) return ''
      // 今天只显示 时:分，更早显示 月/日 时:分
      const d = t.slice(5, 16)
      const today = new Date()
      const mm = String(today.getMonth() + 1).padStart(2, '0')
      const dd = String(today.getDate()).padStart(2, '0')
      return t.slice(0, 5) === `${mm}-${dd}` ? t.slice(11, 16) : d
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.redirectTo({ url: '/pages/idea/idea-resonance' }) })
    }
  }
}
</script>

<style scoped>
/* 页面撑满，滚动交给对话流，输入栏固定在底部 */
.xt-page.xt-s41 .chat-body {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
}
.xt-page.xt-s41 .chat-scroll {
  flex: 1;
  height: 0;
  min-height: 0;
}
.xt-page.xt-s41 .chat-head,
.xt-page.xt-s41 .mem-hero,
.xt-page.xt-s41 .chips,
.xt-page.xt-s41 .inputbar {
  flex-shrink: 0;
}

/* 设计稿 img 在 H5 渲染为 uni-image，补齐尺寸/圆角 */
.xt-page.xt-s41 .head-av {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #F0F4F2;
}
.xt-page.xt-s41 uni-image.head-av {
  display: block;
}
.xt-page.xt-s41 uni-image.head-av :deep(img),
.xt-page.xt-s41 uni-image.mav :deep(img) {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}
.xt-page.xt-s41 .head-av-t {
  font-size: 9px;
  font-weight: 800;
  color: var(--v7-green);
}
.xt-page.xt-s41 .mav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #F0F4F2;
}
.xt-page.xt-s41 uni-image.mav {
  display: block;
}
.xt-page.xt-s41 .mav-t {
  font-size: 8px;
  font-weight: 800;
  color: var(--v7-green);
}
.xt-page.xt-s41 .btime {
  display: block;
  margin-top: 5px;
  font-size: 7.5px;
  color: #BFC7BF;
}
.xt-page.xt-s41 .bubble.me .btime {
  color: rgba(255, 253, 250, .7);
}

/* 会话设置底部弹层 */
.sheet-mask {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: flex;
  align-items: flex-end;
  background: rgba(18, 26, 22, .42);
}
.sheet {
  width: 100%;
  padding: 16px 18px calc(14px + env(safe-area-inset-bottom));
  background: #FFFDFA;
  border-radius: 20px 20px 0 0;
}
.sheet-title {
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 900;
  color: #22302A;
  text-align: center;
}
.sheet-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 2px;
  border-bottom: 1px solid rgba(30, 42, 36, .06);
}
.sheet-tx {
  flex: 1;
  padding-right: 12px;
}
.sheet-t {
  font-size: 10px;
  font-weight: 800;
  color: #22302A;
}
.sheet-d {
  margin-top: 3px;
  font-size: 8px;
  color: #8E9A91;
}
.sheet-arrow {
  font-size: 16px;
  color: #BFC7BF;
}
.sheet-cancel {
  margin-top: 12px;
  padding: 12px 0;
  border-radius: 12px;
  background: rgba(46, 86, 67, .06);
  font-size: 10px;
  font-weight: 800;
  color: #4A5A51;
  text-align: center;
}
</style>
