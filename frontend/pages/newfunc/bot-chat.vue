<template>
  <view class="xt-page xt-s60">
    <view class="body">
      <!-- 对话页头 -->
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-av">
          <image
            v-if="avatar && (avatar.indexOf('http') === 0 || avatar.charAt(0) === '/')"
            :src="avatar"
            mode="aspectFill"
            style="width: 100%; height: 100%; border-radius: 50%; display: block;"
          />
          <text v-else class="chat-av-emoji">{{ avatar }}</text>
        </view>
        <view class="chat-meta">
          <view class="chat-name">{{ name }}</view>
          <view class="chat-st">
            {{ memories.length ? '记得你 ' + memories.length + ' 件事' : '只属于你们的对话' }}
          </view>
        </view>
        <view class="icon-btn" @click="openMemory"><xt-icon name="i-brain" /></view>
      </view>

      <!-- 她记得 -->
      <view class="mem-hero s60-mem">
        <view class="s60-mem-top">
          <text class="s60-mem-t">她记得</text>
          <text class="s60-mem-more" @click="openMemory">管理 ›</text>
        </view>
        <view class="chips" style="margin: 7px 0 0">
          <view class="chip" v-for="m in memoryChips" :key="m.id">{{ m.content }}</view>
          <view class="chip" v-if="memoryChips.length === 0">还在慢慢记住你</view>
        </view>
      </view>

      <!-- 消息列表 -->
      <scroll-view scroll-y class="msg-scroll" :scroll-top="scrollTop" :scroll-with-animation="true">
        <view class="messages">
          <view class="date-sep"><text>今天</text></view>

          <view
            class="msg"
            v-for="(m, i) in messages"
            :key="i"
            :class="{ me: m.role === 'user' }"
          >
            <image
              v-if="m.role !== 'user' && avatar && (avatar.indexOf('http') === 0 || avatar.charAt(0) === '/')"
              class="mav"
              :src="avatar"
              mode="aspectFill"
              style="width: 24px; height: 24px; border-radius: 50%; display: block; flex-shrink: 0;"
            />
            <view v-else-if="m.role !== 'user'" class="mav mav-emoji"><text>{{ avatar }}</text></view>
            <view class="bubble" :class="m.role === 'user' ? 'me' : 'ai'">
              <text>{{ m.content }}</text>
              <!-- 【newfunc 增量-语音包】AI 回复朗读（用伙伴绑定的语种/方言音色） -->
              <view class="speak-btn" v-if="m.role === 'assistant'" @click.stop="speak(m.content, i)">
                <text>{{ speakingIndex === i ? '⏸ 朗读中' : '🔊 朗读' }}</text>
              </view>
            </view>
          </view>

          <view class="msg" v-if="sending">
            <view class="mav mav-emoji"><text>{{ avatar }}</text></view>
            <view class="bubble ai"><text>{{ name }} 正在输入…</text></view>
          </view>
        </view>
      </scroll-view>

      <!-- 快捷话术 -->
      <view class="chips s60-quick">
        <view class="chip" @click="draft = '抱抱'">抱抱</view>
        <view class="chip" @click="draft = '陪我待会儿'">陪我待会儿</view>
        <view class="chip" @click="draft = '别说话，就好'">别说话，就好</view>
      </view>

      <!-- 输入区 -->
      <view class="inputbar">
        <input
          class="in-field"
          v-model="draft"
          confirm-type="send"
          placeholder="想说点什么…"
          placeholder-class="ph"
          @confirm="send"
        />
        <view class="in-send" :class="{ sending }" @click="send"><xt-icon name="i-send" /></view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】与自建 AI 伙伴的独立聊天页
 * - 人设贴合 + 隔离记忆（只召回/沉淀该伙伴自己的记忆）
 * - 独立页面，不修改既有 ai-chat 页任何逻辑
 */
import api from '@/api/newfunc'
import { API_BASE } from '@/common/env'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      botId: 0,
      name: '伙伴',
      avatar: '🌿',
      messages: [],
      memories: [],
      draft: '',
      sending: false,
      scrollTop: 0,
      audioCtx: null,
      speakingIndex: -1
    }
  },
  computed: {
    memoryChips() {
      return this.memories.slice(0, 3).map(m => ({
        id: m.id,
        content: (m.content || '').slice(0, 10)
      }))
    }
  },
  onLoad(opt) {
    this.botId = Number(opt.id || 0)
    this.name = decodeURIComponent(opt.name || '伙伴')
    this.avatar = decodeURIComponent(opt.avatar || '🌿')
    uni.setNavigationBarTitle ? null : null
    this.greet()
    this.loadMemories()
  },
  onUnload() {
    if (this.audioCtx) { this.audioCtx.destroy(); this.audioCtx = null }
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    openMemory() {
      uni.navigateTo({ url: `/pages/newfunc/bot-memory?id=${this.botId}&name=${encodeURIComponent(this.name)}` })
    },
    /** 顶部「她记得」展示：只读取该伙伴的前几条记忆，不参与对话逻辑 */
    async loadMemories() {
      if (!this.botId) return
      try {
        const res = await api.botMemories(this.botId, { size: 3 })
        const list = (res.data && res.data.list) || []
        this.memories = list.filter(m => m && m.content)
      } catch (e) {
        this.memories = []
      }
    },
    greet() {
      this.messages.push({
        role: 'assistant',
        content: `我是${this.name}，这个聊天里只有我们两个，我记下的也只会是我们俩的事。`
      })
    },
    scrollBottom() {
      this.$nextTick(() => {
        this.scrollTop = this.messages.length * 999 + 999
      })
    },
    async send() {
      const text = this.draft.trim()
      if (!text || this.sending) return
      this.messages.push({ role: 'user', content: text })
      this.draft = ''
      this.sending = true
      this.scrollBottom()
      try {
        const history = this.messages
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .slice(-10, -1)
          .map(m => ({ role: m.role, content: m.content }))
        const res = await api.botChat(this.botId, text, history)
        this.messages.push({
          role: 'assistant',
          content: (res.data && res.data.reply) || '……'
        })
      } catch (e) {
        this.messages.push({ role: 'assistant', content: '（网络开小差了，再试一次？）' })
      }
      this.sending = false
      this.scrollBottom()
    },
    // ===== 【newfunc 增量-语音包】AI 回复朗读（后端 TTS + 伙伴专属语音 + 兜底回退） =====
    async speak(text, idx) {
      // 再次点击 = 停止播放
      if (this.speakingIndex === idx) {
        if (this.audioCtx) this.audioCtx.stop()
        this.speakingIndex = -1
        return
      }
      try {
        // bot_id 传入后：优先伙伴绑定语音 > 用户默认 > 全局默认（后端兜底）
        const res = await api.ttsSynthesize(text, '', this.botId)
        if (res.data && res.data.audio_url) {
          const base = (API_BASE || '').replace(/\/api\/v1$/, '')
          if (this.audioCtx) this.audioCtx.destroy()
          this.audioCtx = uni.createInnerAudioContext()
          this.audioCtx.src = base + res.data.audio_url
          this.audioCtx.onEnded(() => { this.speakingIndex = -1 })
          this.audioCtx.onError(() => { this.speakingIndex = -1 })
          this.speakingIndex = idx
          this.audioCtx.play()
          if (res.data.fallback) {
            uni.showToast({ title: res.data.fallback_reason || '已回退默认语音', icon: 'none' })
          }
        }
      } catch (e) {
        uni.showToast({ title: '语音生成失败，已回退默认语音', icon: 'none' })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* === 页面骨架：页头 / 记忆 / 消息滚动 / 输入 === */
.xt-page.xt-s60 .body {
  display: flex; flex-direction: column;
  overflow: hidden;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
}
.xt-page.xt-s60 .chat-head { flex-shrink: 0; }

.xt-page.xt-s60 .chat-av { width: 32px; height: 32px; overflow: visible; }
.xt-page.xt-s60 .chat-av uni-image { width: 100%; height: 100%; border-radius: 50%; display: block; }
.xt-page.xt-s60 .chat-av-emoji {
  width: 100%; height: 100%; border-radius: 50%;
  background: #F3EFE5; font-size: 17px;
  display: flex; align-items: center; justify-content: center;
}

/* === 她记得 === */
.xt-page.xt-s60 .s60-mem { flex-shrink: 0; padding: 10px 12px; margin-bottom: 11px; }
.xt-page.xt-s60 .s60-mem-top { display: flex; align-items: center; justify-content: space-between; }
.xt-page.xt-s60 .s60-mem-t { font-size: 8px; font-weight: 900; color: #3C6B55; }
.xt-page.xt-s60 .s60-mem-more { font-size: 7px; color: #8E9A91; }
.xt-page.xt-s60 .s60-mem .chips { flex-wrap: wrap; }
.xt-page.xt-s60 .s60-mem .chip {
  font-size: 8px; padding: 4px 9px;
  max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* === 消息滚动区 === */
.xt-page.xt-s60 .msg-scroll { flex: 1; min-height: 0; height: 0; }
.xt-page.xt-s60 .messages {
  display: flex; flex-direction: column; justify-content: flex-start;
  padding: 4px 2px 0;
}
.xt-page.xt-s60 .msg uni-image { width: 24px; height: 24px; border-radius: 50%; display: block; flex-shrink: 0; }
.xt-page.xt-s60 .mav-emoji {
  width: 24px; height: 24px; border-radius: 50%;
  background: #F3EFE5; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.xt-page.xt-s60 .bubble { display: flex; flex-direction: column; align-items: flex-start; }
.xt-page.xt-s60 .bubble.me { align-items: flex-end; }
.xt-page.xt-s60 .speak-btn {
  margin-top: 6px; font-size: 7px; color: var(--v7-green);
  background: #F3EFE5; padding: 2px 8px; border-radius: 999px;
}

/* === 快捷话术 === */
.xt-page.xt-s60 .s60-quick { flex-shrink: 0; margin: 6px 0 8px; }
.xt-page.xt-s60 .s60-quick .chip { font-size: 8px; padding: 5px 9px; }

/* === 输入区 === */
.xt-page.xt-s60 .inputbar { flex-shrink: 0; }
.xt-page.xt-s60 .in-field {
  height: 34px; box-sizing: border-box;
  background: #fff; border-radius: 999px;
  padding: 0 13px; font-size: 9px; color: #22302A;
  box-shadow: 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s60 .in-field .uni-input-wrapper,
.xt-page.xt-s60 .in-field .uni-input-input { height: 100%; font-size: 9px; }
.xt-page.xt-s60 .ph { color: #BFC7BF; }
.xt-page.xt-s60 .in-send.sending { opacity: 0.6; }
</style>
