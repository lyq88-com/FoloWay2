<template>
  <view class="xt-page xt-s9">
    <view class="body">
      <!-- 选人阶段 -->
      <view v-if="phase === 'select'" class="gc-select">
        <view class="page-title-row">
          <view>
            <view class="page-title">发起群聊</view>
            <view class="page-sub">选择 2~4 位 AI 伙伴，一起加入群聊房间</view>
          </view>
          <view class="head-count">
            <text class="count-num">{{ selected.length }}</text>
            <text class="count-max">/4</text>
          </view>
        </view>

        <view class="cal-sec">
          <text class="t">选择伙伴</text>
          <text class="s">{{ selected.length < 2 ? '还差 ' + (2 - selected.length) + ' 位伙伴' : '已选 ' + selected.length + ' 位' }}</text>
        </view>

        <scroll-view scroll-y class="char-list">
          <view
            v-for="c in characters"
            :key="c.id"
            class="char-card"
            :class="{ selected: isSelected(c.id) }"
            @click="toggleSelect(c)">
            <view class="char-avatar" :style="getPhoto(c.id) ? null : { background: 'linear-gradient(135deg, ' + (c.colors ? c.colors.primary : '#9CBFAA') + ', ' + (c.colors ? c.colors.accent : '#24493A') + ')' }">
              <image v-if="getPhoto(c.id)" class="char-avatar-img" :src="getPhoto(c.id)" mode="aspectFill" />
              <text v-else class="char-emoji">{{ c.avatar }}</text>
            </view>
            <view class="char-info">
              <text class="char-name">{{ c.name }}</text>
              <text class="char-desc">{{ c.personality }}</text>
            </view>
            <view class="char-check" :class="{ on: isSelected(c.id) }">
              <text>{{ isSelected(c.id) ? '✓' : '+' }}</text>
            </view>
          </view>
          <view class="list-bottom-space"></view>
        </scroll-view>

        <view class="gc-select-footer">
          <view class="create-btn" :class="{ disabled: selected.length < 2 }" @click="createRoom">
            <text>{{ selected.length < 2 ? '还差 ' + (2 - selected.length) + ' 位伙伴' : '创建群聊（' + selected.length + '人）' }}</text>
            <text class="create-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 群聊房间 -->
      <view v-else class="gc-room">
        <view class="chat-head">
          <view class="back" @click="exitRoom"><xt-icon name="i-left" /></view>
          <view class="multi-avs">
            <template v-for="m in headerMembers" :key="m.id">
              <image v-if="m.photo" :src="m.photo" mode="aspectFill" />
              <view v-else class="multi-av-fallback"><text>{{ m.avatar }}</text></view>
            </template>
          </view>
          <view class="chat-meta">
            <view class="chat-name">{{ groupName || roomName }}</view>
            <view class="chat-st"><text class="st-dot"></text>{{ members.length }} 位伙伴都在{{ aiPaused ? ' · AI 已暂停' : '' }}</view>
          </view>
          <view class="icon-btn" @click="exitRoom"><xt-icon name="i-settings" /></view>
        </view>

        <scroll-view scroll-y class="messages" :scroll-top="scrollTop">

          <template v-for="(msg, idx) in messages" :key="idx">
            <template v-if="msg.role !== 'user'">
              <view class="bname">{{ memberName(msg.role) }}</view>
              <view class="msg">
                <image v-if="memberPhotoMap[msg.role]" class="mav" :src="memberPhotoMap[msg.role]" mode="aspectFill" />
                <view v-else class="mav mav-fallback"><text>{{ memberAvatar(msg.role) }}</text></view>
                <view class="bubble ai">{{ msg.content }}</view>
              </view>
            </template>
            <view v-else class="msg me">
              <view class="bubble me">{{ msg.content }}</view>
            </view>
          </template>

          <view v-if="aiTyping" class="msg">
            <image v-if="memberPhotoMap[typingMemberId]" class="mav" :src="memberPhotoMap[typingMemberId]" mode="aspectFill" />
            <view v-else class="mav mav-fallback"><text>{{ memberAvatar(typingMemberId) }}</text></view>
            <view class="bubble ai typing-bubble">
              <view class="typing-dots">
                <view class="typing-dot"></view>
                <view class="typing-dot"></view>
                <view class="typing-dot"></view>
              </view>
            </view>
          </view>
        </scroll-view>

        <!-- 【模块4】强负面情绪兜底入口：只做跳转，不改目标页面 -->
        <view v-if="showComfort" style="display:flex;align-items:center;gap:8px;padding:8px 16px 0;flex-wrap:wrap;">
          <text style="font-size:12px;color:#7A8C84;">心里这么沉，要不要先</text>
          <text style="font-size:12px;color:#2E6B57;background:#EAF4EE;padding:4px 10px;border-radius:12px;" @click="goMind">呼吸一下</text>
          <text style="font-size:12px;color:#2E6B57;background:#EAF4EE;padding:4px 10px;border-radius:12px;" @click="goEmotion">记一笔心情</text>
        </view>

        <view class="quick">
          <text class="chip" @click="inputText = '今天有点累'; sendMessage()">今天有点累</text>
          <text class="chip" @click="inputText = '陪我聊会儿'; sendMessage()">陪我聊会儿</text>
          <text class="chip" :class="{ on: aiPaused }" @click="toggleAI">{{ aiPaused ? '继续聊天' : '大家先停一下' }}</text>
        </view>
        <view class="inputbar">
          <view class="in-plus"><xt-icon name="i-plus" /></view>
          <input
            class="in-field"
            v-model="inputText"
            placeholder="和三位伙伴说点什么…"
            placeholder-style="color: #BFC7BF"
            confirm-type="send"
            @confirm="sendMessage" />
          <view class="in-send" @click="sendMessage"><xt-icon name="i-send" /></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 多角色群聊房间
 * - 选择多位AI伙伴共同进入群聊
 * - 用户发言后，各角色按人设轮流回复；角色之间也会互相搭话
 */
import { CHARACTERS } from '@/common/ai-characters'
import chatApi from '@/api/chat'
import groupApi from '@/api/group'
import { getPartnerAvatar } from '@/common/ai-partner'
// 【复用原有语音播报】沿用设置页的「语音播报」开关与后端 TTS 接口，不新建语音系统
import aiSpeak from '@/common/ai-speak'
import tts from '@/common/tts'
// 【修复】走统一 http 层：H5 相对路径经代理、App 用局域网地址，token 从 store 注入
import personaApi from '@/api/persona'

export default {
  data() {
    return {
      statusBarHeight: 20,
      phase: 'select', // select | room
      characters: CHARACTERS,
      backendCharacters: [], // 从后端拉的 AI 伙伴列表（官方+自定义+扭蛋）
      selected: [],
      members: [],
      messages: [],
      inputText: '',
      scrollTop: 0,
      aiTyping: false,
      typingMemberId: '',
      sending: false,
      // ↓↓↓ 模块4 新增：后端群聊真实 ID ↓↓↓
      groupId: 0,
      groupName: '',
      // ↑↑↑ 模块4 新增结束 ↑↑↑
      // 【修复】喊停状态：与后端 group_chats.ai_muted 同步
      aiPaused: false,
      // 【模块4】识别到强负面情绪时显示正念/情绪日记入口
      showComfort: false,
      // 【复用原有语音开关】跟随设置页「语音播报」，不新建开关
      ttsEnabled: false,
    }
  },
  computed: {
    memberNames() {
      const names = this.members.map(m => m.name)
      const me = (this.$store.state.userInfo && this.$store.state.userInfo.nickname) || '我'
      return [...names, me].join('、')
    },
    roomName() {
      return this.members.length > 0 ? `和${this.members[0].name}等${this.members.length + 1}人的群聊` : '群聊房间'
    },
    headerMembers() {
      return this.members.slice(0, 3).map(m => ({
        id: m.id,
        avatar: m.avatar,
        photo: this.memberPhotoMap[m.id] || ''
      }))
    },
    memberPhotoMap() {
      const map = {}
      this.members.forEach(m => {
        map[m.id] = this.resolveMemberPhoto(m)
      })
      return map
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    // 【复用原有语音开关】
    try { this.ttsEnabled = tts.getEnabled() } catch (e) { this.ttsEnabled = false }

    // ↓↓↓ 模块4 新增：启动时从后端拉 AI 伙伴列表 + 恢复已存在的群聊 ↓↓↓
    this._loadBackendCharacters()
    if (options && options.group_id) {
      this._enterExistingGroup(parseInt(options.group_id))
    }
    // ↑↑↑ 模块4 新增结束 ↑↑↑
  },
  onUnload() {
    // 【性能】离开页面立刻停掉播报，避免后台占用
    try { aiSpeak.stop() } catch (e) {}
  },
  methods: {
    // ↓↓↓ 模块4 新增：只拉「官方 + 自己」的 AI 伙伴，避免看到其他用户自建角色 ↓↓↓
    async _loadBackendCharacters() {
      try {
        // scope=mine：官方角色 + 当前用户自建/扭蛋角色；不能用 all，all 会带上别人的角色
        const r = await personaApi.getRoles('mine')
        const data = (r && r.data) || []
        // 过滤冒烟角色
        const list = data.filter(c => !(c.name && c.name.startsWith('冒烟')))
        this.backendCharacters = list
        // 选人列表优先用后端数据，没有再 fallback 到 CHARACTERS
        if (list.length > 0) this.characters = list
      } catch (e) {
        // 后端不可用则 fallback 到 CHARACTERS
        console.warn('拉后端角色列表失败，用本地 fallback', e)
      }
    },
    async _enterExistingGroup(gid) {
      try {
        const r = await groupApi.detail(gid)
        const g = r.data
        if (!g) return
        this.groupId = gid
        this.groupName = g.group_name
        this.aiPaused = !!g.ai_muted
        this.members = g.members.map(m => ({
          id: m.role_type || ('me_' + (m.user_id || '')),
          role_type: m.role_type || '',
          member_type: m.member_type,
          name: m.ai_name || (CHARACTERS.find(c => c.id === m.role_type)?.name) || m.role_type || '伙伴',
          avatar: m.ai_avatar || (CHARACTERS.find(c => c.id === m.role_type)?.avatar) || (m.member_type === 0 ? '🙂' : '🌿'),
          personality: m.personality || '',
          colors: { primary: '#9CBFAA', accent: '#24493A' },
        }))
        this.phase = 'room'
        // 拉历史消息
        const msgs = await groupApi.messages(gid, 1, 50)
        const list = (msgs.data && msgs.data.list) || []
        this.messages = list.map(m => ({
          role: m.sender_type === 0 ? 'user' : m.sender_role_type,
          content: m.content,
          id: m.id,
        }))
      } catch (e) {
        uni.showToast({ title: '群聊不存在或已解散', icon: 'none' })
      }
    },
    // ↑↑↑ 模块4 新增结束 ↑↑↑

    isSelected(id) {
      return this.selected.some(c => c.id === id)
    },
    /** 伙伴立绘：与首页/头像行共用同一套解析，兼容自定义伙伴上传的头像 */
    getPhoto(id) {
      const c = (this.characters || []).find(x => x && (x.id === id || x.role_key === id))
      return getPartnerAvatar(id) || this.imageOf(c) || ''
    },
    /** 从角色/群成员数据里取可能是图片的 avatar 字段 */
    imageOf(obj) {
      const v = obj && obj.avatar
      return (typeof v === 'string' && /^(https?:\/\/|blob:|data:image|\/)/.test(v)) ? v : ''
    },
    /** 群成员头像（自定义/后端角色可能只有 avatar 图片地址） */
    resolveMemberPhoto(m) {
      if (!m) return ''
      return getPartnerAvatar(m.role_type || m.id) || this.imageOf(m) || ''
    },
    toggleSelect(c) {
      const idx = this.selected.findIndex(s => s.id === c.id)
      if (idx > -1) {
        this.selected.splice(idx, 1)
      } else {
        if (this.selected.length >= 4) {
          uni.showToast({ title: '最多选择4位伙伴', icon: 'none' })
          return
        }
        this.selected.push(c)
      }
    },
    // ↓↓↓ 模块4 修改：createRoom 走后端 group API ↓↓↓
    async createRoom() {
      if (this.selected.length < 2) return
      try {
        // 【修复】后端角色字段是 roleKey（驼峰），取错会传数字 id 导致建群 422
        const role_types = this.selected.map(c => String(c.roleKey || c.role_key || c.id))
        const r = await groupApi.create('我的群聊', role_types)
        const g = r.data
        this.groupId = g.id
        this.groupName = g.group_name
        this.members = g.members.map(m => ({
          id: m.role_type || ('me_' + (m.user_id || '')),
          role_type: m.role_type || '',
          member_type: m.member_type,
          name: m.ai_name || (CHARACTERS.find(c => c.id === m.role_type)?.name) || m.role_type || '伙伴',
          avatar: m.ai_avatar || (CHARACTERS.find(c => c.id === m.role_type)?.avatar) || (m.member_type === 0 ? '🙂' : '🌿'),
          personality: m.personality || '',
          colors: { primary: '#9CBFAA', accent: '#24493A' },
        }))
        this.phase = 'room'
        uni.showToast({ title: '群聊已创建', icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '创建失败', icon: 'none' })
      }
    },
    memberBg(id) {
      const m = this.members.find(x => x.id === id)
      return m ? `linear-gradient(135deg, ${m.colors.primary}, ${m.colors.accent})` : '#E8F4EC'
    },
    memberAvatar(id) {
      const m = this.members.find(x => x.id === id)
      if (m) return m.avatar
      const c = CHARACTERS.find(x => x.id === id)
      return c ? c.avatar : '🌿'
    },
    memberName(id) {
      const m = this.members.find(x => x.id === id)
      if (m) return m.name
      const c = CHARACTERS.find(x => x.id === id)
      return c ? c.name : ''
    },
    /** 拼群聊上下文，注入 system prompt 让 AI 知道群成员和最近对话 */
    buildGroupContext() {
      const me = (this.$store.state.userInfo && this.$store.state.userInfo.nickname) || '用户'
      const lines = ['群成员：']
      this.members.forEach(m => lines.push(`- ${m.name}（${m.personality || ''}）`))
      lines.push(`- ${me}（真人用户）`)

      // 取最近 4 条群聊消息作为上下文（够了，多了反而塞爆 prompt）
      lines.push('\n最近对话：')
      const recent = this.messages.slice(-4)
      for (const msg of recent) {
        let who = ''
        if (msg.role === 'user') {
          who = me
        } else {
          const m = this.members.find(x => x.id === msg.role)
          who = m ? m.name : msg.role
        }
        lines.push(`[${who}] ${msg.content}`)
      }
      return lines.join('\n')
    },
    /** CHARACTERS.style 到 DIALOGUE_STYLES 的映射 */
    styleToDialogue(style) {
      const map = {
        relaxed: 'gentle', chinese: 'gentle', artsy: 'gentle', mythical: 'gentle',
        y2k: 'energetic', cyber: 'rational', cool: 'rational', energetic: 'energetic',
      }
      return map[style] || 'gentle'
    },
    /** 角色发言（真实后端 SSE 流式生成） */
    async memberSpeak(memberIdx, userContent, isGreeting = false) {
      const member = this.members[memberIdx]
      if (!member) return
      this.typingMemberId = member.id
      this.aiTyping = true
      this.scrollToBottom()

      // 极简前置等待（50ms 足够让打字动画闪一下，不阻塞 SSE 首字输出）
      await new Promise(r => setTimeout(r, 50))

      // 创建消息气泡，初始为空，等待 SSE 流式填充
      const msg = { role: member.id, content: '' }
      this.messages.push(msg)
      const msgIdx = this.messages.length - 1
      this.aiTyping = false // 结束打字动画，开始流式显示
      this.scrollToBottom()

      try {
        const groupCtx = this.buildGroupContext()
        // greeting 场景没有用户输入，传一个简短指令让 AI 自然开场
        const content = isGreeting ? '打个招呼，自我介绍一下吧' : (userContent || '')
        const fullReply = await chatApi.streamSend(
          content,
          (chunk) => {
            this.messages[msgIdx].content += chunk
            this.scrollToBottom()
          },
          {
            role_key: member.id,
            role_type: member.style || 'companion',
            dialogue_style: this.styleToDialogue(member.style),
            scene_type: 'group_chat',
            group_context: groupCtx,
          }
        )
        // streamPost 最终返回完整内容，兜底替换（避免流式拼接丢字）
        if (fullReply && fullReply !== this.messages[msgIdx].content) {
          this.messages[msgIdx].content = fullReply
        }
      } catch (e) {
        // 网络失败降级：用角色 catchphrase 兜底
        this.messages[msgIdx].content = member.catchphrase || '嗯嗯，我在听～'
      }
      this.scrollToBottom()
    },
    // ↓↓↓ 模块4 新增：SSE 版打字动画 helper（逐字符填充 AI 回复，30ms/字） ↓↓↓
    async _typeAiReply(roleType, fullContent) {
      // 找到这个 roleType 对应的 member.id（用于 typing 动画和气泡显示）
      // 注意：members 里的 id 可能是 role_type（AI）或 'me_' 前缀（人类）
      const memberId = roleType  // SSE yield 的 role_type 就是 AI 的 role_type，直接用作 member.id
      this.typingMemberId = memberId
      this.aiTyping = true
      this.scrollToBottom()

      // typing 动画闪 300ms（让用户感知"AI 正在打字"）
      await new Promise(r => setTimeout(r, 300))

      // 创建气泡，初始为空
      const msg = { role: memberId, content: '' }
      this.messages.push(msg)
      const msgIdx = this.messages.length - 1
      this.aiTyping = false  // 结束 typing 动画，开始填充内容
      this.scrollToBottom()

      // 逐字符填充（30ms/字），制造"AI 在打字"的体验
      const chars = String(fullContent || '').split('')
      for (let i = 0; i < chars.length; i++) {
        this.messages[msgIdx].content += chars[i]
        if (i % 5 === 0) this.scrollToBottom()  // 每 5 字滚一次，避免每字都滚太频繁
        await new Promise(r => setTimeout(r, 30))
      }
      this.scrollToBottom()
    },
    // ↑↑↑ 新增结束 ↑↑↑

    async sendMessage() {
      const content = this.inputText.trim()
      if (!content || this.sending) return
      if (!this.groupId) { uni.showToast({ title: '群聊未创建', icon: 'none' }); return }
      this.sending = true
      this.inputText = ''
      this.messages.push({ role: 'user', content })
      this.scrollToBottom()

      // ↓↓↓ 模块4 修改：调后端 SSE /send-sse，每个 AI 回复到达即流式展示 ↓↓↓
      // 后端自动调度 1-2 位 AI + 错开 0.8-1.5s；前端逐个显示打字动画
      const repliesBuffer = []  // 收集所有 AI 完整回复，SSE 结束后统一播报（避免边打字边播报冲突）
      try {
        await groupApi.sendSse(this.groupId, content, {
          onArrival: () => {
            // 用户消息已入群（可忽略，用户消息已经 push 了）
          },
          onAiReply: async (roleType, replyContent) => {
            // 每个 AI 回复到达：打字动画 + 逐字填充
            await this._typeAiReply(roleType, replyContent)
            repliesBuffer.push({ roleType, content: replyContent })
          },
          onDone: () => {
            // 全部 AI 回复结束
            this.sending = false
            this.aiTyping = false
            // 【复用原有语音播报】按顺序念出 AI 回复，开关沿用设置页
            if (this.ttsEnabled && repliesBuffer.length) {
              // 延迟一小段等打字动画彻底收尾再播报
              setTimeout(async () => {
                for (const rep of repliesBuffer) {
                  try { await aiSpeak.speak(rep.content) } catch (e) {}
                }
              }, 500)
            }
          },
          onError: (err) => {
            console.warn('[群聊 SSE] 错误', err)
            uni.showToast({ title: '发送失败，请重试', icon: 'none' })
            this.sending = false
            this.aiTyping = false
          }
        })
      } catch (e) {
        uni.showToast({ title: '发送失败，请重试', icon: 'none' })
        this.sending = false
        this.aiTyping = false
      }
      // ↑↑↑ SSE 版结束 ↑↑↑
    },
    /** 【模块4】跳转已有正念页面（仅跳转，不改对方） */
    goMind() {
      uni.navigateTo({ url: '/pages/meditation/meditation' })
    },
    /** 【模块4】跳转已有情绪日记页面（仅跳转，不改对方） */
    goEmotion() {
      uni.navigateTo({ url: '/pages/emotion/emotion' })
    },
    /** 【修复】喊停 / 继续聊天：复用后端 /stop 与 /resume，前端不再自行假暂停 */
    async toggleAI() {
      if (!this.groupId || this.sending) return
      try {
        if (this.aiPaused) {
          await groupApi.resume(this.groupId)
          this.aiPaused = false
          uni.showToast({ title: '伙伴们回来了', icon: 'none' })
        } else {
          const r = await groupApi.stop(this.groupId)
          this.aiPaused = true
          this.messages.push({ role: 'user', content: '【喊停】大家先停下来' })
          this.scrollToBottom()
          uni.showToast({ title: '已暂停 AI 发言', icon: 'none' })
        }
      } catch (e) {
        uni.showToast({ title: '操作失败，请重试', icon: 'none' })
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        this.scrollTop = 99999
      })
    },
    exitRoom() {
      // ↓↓↓ 模块4 修改：退出群聊后如果后端解散了，返回选人页 ↓↓↓
      uni.showModal({
        title: '退出群聊',
        content: '退出后本次群聊记录将清空，确定退出吗？',
        confirmText: '退出',
        success: (r) => {
          if (r.confirm) {
            this.phase = 'select'
            this.members = []
            this.messages = []
            this.groupId = 0
            this.groupName = ''
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.xt-page.xt-s9 {
  background: #F8F4EC;
  background-image: radial-gradient(420px 300px at 90% -6%, rgba(156,191,170,.18), transparent 62%),
    radial-gradient(360px 300px at 0% 104%, rgba(192,138,86,.12), transparent 60%);
}
.xt-page.xt-s9 .body {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 16px;
  box-sizing: border-box;
}

/* 群聊房间容器：此前未设 flex，导致 .messages 的 flex:1 失效、高度塌陷为 0，
   表现为“看不到任何消息 / 以为消息发不出去”。这里补成纵向撑满 */
.xt-page.xt-s9 .gc-room {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ===== 群聊：头像 / 消息 ===== */
.xt-page.xt-s9 .multi-avs uni-image {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--v7-card);
  margin-left: -9px;
}
.xt-page.xt-s9 .multi-avs > :first-child { margin-left: 0; }
.xt-page.xt-s9 .multi-av-fallback {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #EDF3F0;
  border: 2px solid var(--v7-card);
  margin-left: -9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
.xt-page.xt-s9 .st-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #81B19B;
  display: inline-block;
}

.xt-page.xt-s9 .messages {
  flex: 1;
  height: 0;
  min-height: 0;
  box-sizing: border-box;
}
.xt-page.xt-s9 .bname {
  padding-left: 31px;
  margin-bottom: 2px;
  font-size: 6.5px;
  font-weight: 700;
  color: #A2AAA3;
}
.xt-page.xt-s9 .msg uni-image.mav {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.xt-page.xt-s9 .msg uni-image.mav :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.xt-page.xt-s9 .mav-fallback {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #EDF3F0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
}
.xt-page.xt-s9 .typing-bubble { display: flex; align-items: center; }
.typing-dots { display: flex; align-items: center; }
.typing-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #9CBFAA;
  margin: 0 2px;
  animation: tBlink 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes tBlink {
  0%, 100% { opacity: 0.25; }
  50% { opacity: 1; }
}
.xt-page.xt-s9 .vote .vo .vo-k { width: 26px; flex-shrink: 0; }
.xt-page.xt-s9 .vote .vo .bar .bar-in {
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9CBFAA, var(--v7-green));
}
.xt-page.xt-s9 .in-field :deep(.uni-input-input) {
  font-size: 9px;
  color: #22302A;
}

/* ===== 选人阶段（V7 纸感） ===== */
.xt-page.xt-s9 .gc-select {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.xt-page.xt-s9 .page-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 6px 0 14px;
}
.xt-page.xt-s9 .page-title {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -.4px;
  color: #22302A;
  line-height: 1.1;
}
.xt-page.xt-s9 .page-sub {
  margin-top: 5px;
  font-size: 11px;
  color: #8E9A91;
  line-height: 1.5;
}
.xt-page.xt-s9 .head-count {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #FFFDFA;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px -10px rgba(34,48,42,.5), inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s9 .count-num { font-size: 14px; font-weight: 800; color: #24493A; line-height: 1; }
.xt-page.xt-s9 .count-max { font-size: 9px; color: #AEB6AE; line-height: 1; }

.xt-page.xt-s9 .cal-sec {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 2px 0 10px;
}
.xt-page.xt-s9 .cal-sec .t { font-size: 12px; font-weight: 900; color: #22302A; }
.xt-page.xt-s9 .cal-sec .s { font-size: 10px; color: #AEB6AE; }

.xt-page.xt-s9 .char-list {
  flex: 1;
  height: 0;
  min-height: 0;
  padding: 0 2px;
  box-sizing: border-box;
}
.xt-page.xt-s9 .list-bottom-space { height: 12px; }
.xt-page.xt-s9 .char-card {
  display: flex;
  align-items: center;
  padding: 12px 13px;
  margin-bottom: 9px;
  background: #FFFDFA;
  border-radius: 16px;
  box-shadow: 0 12px 26px -22px rgba(34,48,42,.6), inset 0 0 0 1px var(--v7-line);
  transition: all 0.15s ease;
}
.xt-page.xt-s9 .char-card.selected {
  background: #F4F8F4;
  box-shadow: inset 0 0 0 1.5px rgba(68,112,90,.6), 0 8px 20px -16px rgba(68,112,90,.4);
}
.xt-page.xt-s9 .char-avatar {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.xt-page.xt-s9 .char-avatar uni-image,
.xt-page.xt-s9 .char-avatar-img {
  width: 44px;
  height: 44px;
  display: block;
  border-radius: 13px;
}
.xt-page.xt-s9 .char-avatar :deep(uni-image img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.xt-page.xt-s9 .char-emoji { font-size: 22px; }
.xt-page.xt-s9 .char-info { flex: 1; min-width: 0; margin-left: 11px; }
.xt-page.xt-s9 .char-name { display: block; font-size: 14px; font-weight: 800; color: #22302A; }
.xt-page.xt-s9 .char-desc {
  display: block;
  margin-top: 3px;
  font-size: 11px;
  color: #8E9A91;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.xt-page.xt-s9 .char-check {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  margin-left: 10px;
  border-radius: 50%;
  background: #F4EFE3;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.xt-page.xt-s9 .char-check text { font-size: 13px; color: #B4A998; line-height: 1; font-weight: 700; }
.xt-page.xt-s9 .char-check.on { background: #24493A; }
.xt-page.xt-s9 .char-check.on text { color: #FFFDFA; }

.xt-page.xt-s9 .gc-select-footer { padding: 10px 2px 14px; }
.xt-page.xt-s9 .create-btn {
  height: 46px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--v7-green), #274B3A);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14px 26px -14px rgba(46,86,67,.7);
}
.xt-page.xt-s9 .create-btn.disabled { background: #E9E4D9; box-shadow: none; }
.xt-page.xt-s9 .create-btn text { font-size: 14px; font-weight: 800; color: #FFFDFA; letter-spacing: .5px; }
.xt-page.xt-s9 .create-btn.disabled text { color: #A8B0A8; }
.xt-page.xt-s9 .create-arrow { margin-left: 5px; font-size: 16px; line-height: 1; color: rgba(255,253,250,.85); }
.xt-page.xt-s9 .create-btn.disabled .create-arrow { color: #C2CBC4; }
</style>
