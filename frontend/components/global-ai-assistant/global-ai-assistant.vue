<template>
  <view v-if="visible" class="global-ai-assistant" :style="rootStyle" @click="onTap">
    <!-- ↓↓↓ 新增（2026-10-28 打卡陪伴）：场景化提示气泡，tipText 为空时不渲染 ↓↓↓ -->
    <view v-if="tipText" class="assistant-tip">
      <text class="assistant-tip-text">{{ tipText }}</text>
    </view>
    <!-- ↑↑↑ 新增结束 ↑↑↑ -->
    <!-- 浮动按钮 -->
    <view class="assistant-float-btn" :class="{ active: panelOpen }">
      <CharacterHead :characterId="characterId" size="xs" :disableBlink="false" />
      <view v-if="showNotification" class="notification-dot"></view>
      <view class="float-ring"></view>
    </view>

    <!-- 快捷面板 -->
    <view v-if="panelOpen" class="assistant-panel" @click.stop>
      <view class="panel-header">
        <view class="panel-avatar" :style="avatarBgStyle">
          <CharacterHead :characterId="characterId" size="small" />
        </view>
        <view class="panel-info">
          <text class="panel-name">{{ aiName }}</text>
          <text class="panel-status">{{ statusText }}</text>
        </view>
        <view class="panel-close" @click="togglePanel">
          <text class="close-icon">×</text>
        </view>
      </view>

      <view class="panel-quick-actions">
        <view class="quick-action" @click="quickChat('今天感觉怎么样？')">
          <view class="action-icon-wrap">
            <text class="action-icon">💬</text>
          </view>
          <text class="action-label">聊聊心情</text>
        </view>
        <view class="quick-action" @click="quickChat('我需要一些鼓励')">
          <view class="action-icon-wrap">
            <text class="action-icon">💪</text>
          </view>
          <text class="action-label">获取鼓励</text>
        </view>
        <view class="quick-action" @click="quickChat('帮我分析一下拖延原因')">
          <view class="action-icon-wrap">
            <text class="action-icon">🧠</text>
          </view>
          <text class="action-label">分析拖延</text>
        </view>
        <view class="quick-action" @click="quickChat('今天完成了打卡，给自己一个奖励')">
          <view class="action-icon-wrap">
            <text class="action-icon">🎉</text>
          </view>
          <text class="action-label">庆祝打卡</text>
        </view>
      </view>

      <view class="panel-memory-hint" v-if="userContext">
        <view class="hint-item">
          <text class="hint-icon">📊</text>
          <text class="hint-text">今日完成 {{ userContext.todayCompletion || 0 }}/{{ userContext.totalHabits || 0 }} 项</text>
        </view>
        <view class="hint-item">
          <text class="hint-icon">🔥</text>
          <text class="hint-text">连续打卡 {{ userContext.streakDays || 0 }} 天</text>
        </view>
      </view>

      <view class="panel-main-btn" @click="goToChat">
        <text class="main-btn-icon">💗</text>
        <text class="main-btn-text">进入聊天</text>
      </view>
    </view>
  </view>
</template>

<script>
import CharacterHead from '@/components/character-sprite/character-head.vue'
import { getCharacterById } from '@/common/ai-characters'

export default {
  name: 'GlobalAIAssistant',
  components: { CharacterHead },
  props: {
    visible: { type: Boolean, default: true },
    // ↓↓↓ 新增（2026-10-28 打卡陪伴）：四个 prop 全都有默认值，不传 = 改造前的原行为 ↓↓↓
    // 场景提示文案：非空时在悬浮球上方显示气泡，用于「打卡陪伴」这类需要说话的场景
    tipText: { type: String, default: '' },
    // true：点击悬浮球直接进入聊天（不再展开快捷面板）；false：保持原来的展开面板
    directChat: { type: Boolean, default: false },
    // directChat 为 true 时，跳转前写入 pending_proactive_message 的上下文
    // 结构沿用聊天页已在消费的格式：{ content, time, chat_context:{ habit_id, habit_name, event, emotion } }
    chatPayload: { type: Object, default: null },
    // 层级（打卡弹窗场景需高于弹窗的 100）
    zIndex: { type: [Number, String], default: 999 },
    // 距底部距离（打卡弹窗场景需下移，避免压住弹窗内容）；为空则用组件默认的 200rpx
    bottomOffset: { type: String, default: '' }
    // ↑↑↑ 新增结束 ↑↑↑
  },
  data() {
    return {
      panelOpen: false,
      statusTimer: null
    }
  },
  computed: {
    // ↓↓↓ 新增（2026-10-28 打卡陪伴）：只覆盖层级与底部偏移，其余样式沿用全局 ↓↓↓
    rootStyle() {
      const s = { zIndex: String(this.zIndex) }
      if (this.bottomOffset) s.bottom = this.bottomOffset
      return s
    },
    // ↑↑↑ 新增结束 ↑↑↑
    characterId() {
      return this.$store?.state?.aiConfig?.avatarType || 'linxi'
    },
    aiName() {
      const c = getCharacterById(this.characterId)
      return c ? c.name : 'AI伙伴'
    },
    userContext() {
      const state = this.$store?.state
      if (!state) return {}
      const habits = state.habits || []
      const todayStr = new Date().toISOString().split('T')[0]
      const todayCompleted = habits.filter(h => {
        if (!h.completedDate) return false
        return h.completedDate === todayStr || h.completedDate?.startsWith?.(todayStr)
      }).length
      return {
        todayCompletion: todayCompleted,
        totalHabits: habits.length,
        streakDays: state.streakDays || 0
      }
    },
    showNotification() {
      return false // 可扩展：当有未读消息时显示
    },
    statusText() {
      const h = new Date().getHours()
      if (h < 12) return '早上好呀~'
      if (h < 18) return '下午好~'
      return '晚上好~'
    },
    avatarBgStyle() {
      const c = getCharacterById(this.characterId)
      if (c && c.colors) {
        return {
          background: `linear-gradient(135deg, ${c.colors.primary}, ${c.colors.accent})`
        }
      }
      return {}
    }
  },
  methods: {
    /**
     * ↓↓↓ 新增（2026-10-28 打卡陪伴）↓↓↓
     * 点击悬浮球的统一入口。directChat=false 时走原来的「展开快捷面板」，
     * 所以不传新 prop 的调用方行为完全不变。
     */
    onTap() {
      if (!this.directChat) {
        this.togglePanel()
        return
      }
      // 先把上下文落地，再跳聊天页：聊天页 onShow 会自己取走并清除
      try {
        if (this.chatPayload) {
          uni.setStorageSync('pending_proactive_message', this.chatPayload)
        }
      } catch (e) {
        console.error('写入打卡上下文失败:', e)
      }
      this.$emit('tap', this.chatPayload || {})
      try {
        uni.switchTab({ url: '/pages/chat/chat' })
      } catch (e) {
        console.error('跳转聊天失败:', e)
      }
    },
    // ↑↑↑ 新增结束 ↑↑↑
    togglePanel() {
      this.panelOpen = !this.panelOpen
    },
    async quickChat(message) {
      this.panelOpen = false
      // 跳转到聊天页面并发送预设消息
      try {
        // 存储预设消息到 localStorage，供聊天页面读取
        uni.setStorageSync('pending_chat_message', message)
        uni.switchTab({ url: '/pages/chat/chat' })
      } catch (e) {
        console.error('跳转聊天失败:', e)
        uni.switchTab({ url: '/pages/chat/chat' })
      }
    },
    goToChat() {
      this.panelOpen = false
      uni.switchTab({ url: '/pages/chat/chat' })
    }
  }
}
</script>

<style lang="scss" scoped>
.global-ai-assistant {
  position: fixed;
  right: 24rpx;
  bottom: 200rpx;
  z-index: 999;
}

/* ↓↓↓ 新增（2026-10-28 打卡陪伴）：场景提示气泡 ↓↓↓
   配色沿用本项目伙伴系（#2D4A3E 文字 / #6B8E7B 阴影 / 白卡），不引入新配色 */
.assistant-tip {
  position: absolute;
  right: 0;
  bottom: 116rpx;
  width: 400rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 18rpx 22rpx;
  box-shadow: 0 8rpx 28rpx rgba(107, 142, 123, 0.25);
}

.assistant-tip-text {
  display: block;
  font-size: 24rpx;
  line-height: 1.55;
  color: #2D4A3E;
}
/* ↑↑↑ 新增结束 ↑↑↑ */

/* 浮动按钮 */
.assistant-float-btn {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8rpx 32rpx rgba(107, 142, 123, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.assistant-float-btn:active {
  transform: scale(0.92);
}

.assistant-float-btn.active {
  transform: scale(1.1) rotate(10deg);
}

.float-ring {
  position: absolute;
  top: -8rpx;
  left: -8rpx;
  right: -8rpx;
  bottom: -8rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(107, 142, 123, 0.3);
  animation: ringPulse 2s ease-out infinite;
}

@keyframes ringPulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.4); opacity: 0; }
}

.notification-dot {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 16rpx;
  height: 16rpx;
  background: #FF5252;
  border-radius: 50%;
  border: 3rpx solid #fff;
}

/* 快捷面板 */
.assistant-panel {
  position: absolute;
  right: 0;
  bottom: 120rpx;
  width: 520rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.15);
  padding: 32rpx;
  animation: panelSlideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes panelSlideUp {
  from { transform: translateY(20rpx); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.panel-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.panel-info {
  flex: 1;
}

.panel-name {
  font-size: 30rpx;
  font-weight: 700;
  color: #2D4A3E;
  display: block;
}

.panel-status {
  font-size: 22rpx;
  color: #6B8E7B;
  margin-top: 4rpx;
  display: block;
}

.panel-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  font-size: 40rpx;
  color: #999;
}

.panel-quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 20rpx;
  background: #F8FBF9;
  border-radius: 20rpx;
  transition: all 0.2s ease;
}

.quick-action:active {
  transform: scale(0.95);
  background: #EDF5F0;
}

.action-icon-wrap {
  width: 48rpx;
  height: 48rpx;
  background: #fff;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.action-icon {
  font-size: 26rpx;
}

.action-label {
  font-size: 22rpx;
  color: #333;
  font-weight: 500;
}

.panel-memory-hint {
  background: #FFF8E1;
  border-radius: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 20rpx;
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 6rpx;
}

.hint-item:last-child {
  margin-bottom: 0;
}

.hint-icon {
  font-size: 20rpx;
}

.hint-text {
  font-size: 20rpx;
  color: #666;
}

.panel-main-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  border-radius: 24rpx;
  transition: transform 0.2s ease;
}

.panel-main-btn:active {
  transform: scale(0.98);
}

.main-btn-icon {
  font-size: 28rpx;
}

.main-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}
</style>
