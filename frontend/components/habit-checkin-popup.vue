<template>
  <view v-if="visible" class="checkin-popup-mask" @click="onMaskClick">
    <view class="checkin-popup" @click.stop>
      <!-- 头部 -->
      <view class="popup-header">
        <view class="header-icon">{{ achievementData ? '🎉' : '✅' }}</view>
        <text class="header-title">{{ achievementData ? '成就解锁！' : '打卡成功' }}</text>
        <view class="header-close" @click="close">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <!-- AI对话气泡 -->
      <view class="ai-dialogue-section">
        <view class="ai-avatar">{{ characterAvatar }}</view>
        <view class="dialogue-bubble">
          <text class="dialogue-text">{{ popupData.dialogue }}</text>
        </view>
      </view>

      <!-- 统计信息 -->
      <view class="stats-row">
        <view class="stat-item">
          <text class="stat-value">{{ popupData.continuous_day || 0 }}</text>
          <text class="stat-label">连续天数</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-item">
          <text class="stat-value">{{ popupData.emotion_tag || '平和' }}</text>
          <text class="stat-label">情绪状态</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-item">
          <text class="stat-value">{{ styleLabel }}</text>
          <text class="stat-label">对话风格</text>
        </view>
      </view>

      <!-- 成就庆祝(如有) -->
      <view v-if="achievementData" class="achievement-banner">
        <view class="banner-glow"></view>
        <view class="banner-content">
          <text class="banner-title">🏅 {{ achievementData.title }}</text>
          <text class="banner-milestone">{{ achievementData.milestone }}天连续打卡</text>
          <text class="banner-story">{{ achievementData.ai_dialogue }}</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-row">
        <view class="action-btn secondary" @click="onViewDiary">
          <text class="btn-text">查看日记</text>
        </view>
        <view class="action-btn primary" @click="onContinueChat">
          <text class="btn-text">继续聊天</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { useStore } from 'vuex'
import { computed } from 'vue'
import { getCharacterProfile, getStyleLabel } from '@/common/ai-prompts'

export default {
  name: 'HabitCheckinPopup',
  setup() {
    const store = useStore()

    const popupData = computed(() => store.getters.checkinPopupData || {})
    const achievementData = computed(() => store.getters.achievementCelebrationData)
    const visible = computed(() => !!popupData.value.dialogue)

    const characterId = computed(() => store.state.habitAI?.currentCharacterId || 'linxi')
    const characterAvatar = computed(() => {
      const profile = getCharacterProfile(characterId.value)
      return profile?.name?.charAt(0) || '林'
    })
    const styleLabel = computed(() => getStyleLabel(popupData.value.style || 'gentle'))

    const close = () => {
      store.commit('clearCheckinPopup')
      if (achievementData.value) {
        store.commit('clearAchievementCelebration')
      }
    }

    const onMaskClick = () => {
      close()
    }

    const onViewDiary = () => {
      const result = store.getters.lastCheckinResult
      if (result?.diary) {
        uni.setClipboardData({
          data: result.diary,
          success: () => {
            uni.showToast({ title: '日记已复制', icon: 'success' })
          }
        })
      }
      close()
    }

    const onContinueChat = () => {
      close()
      uni.switchTab({ url: '/pages/chat/chat' })
    }

    return {
      visible,
      popupData,
      achievementData,
      characterAvatar,
      styleLabel,
      close,
      onMaskClick,
      onViewDiary,
      onContinueChat,
    }
  }
}
</script>

<style scoped>
.checkin-popup-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.checkin-popup {
  width: 86%;
  max-width: 340px;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes slideUp {
  from { transform: translateY(40px) scale(0.9); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.popup-header {
  display: flex;
  align-items: center;
  padding: 20px 16px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.header-icon { font-size: 28px; margin-right: 10px; }
.header-title { color: #fff; font-size: 18px; font-weight: bold; flex: 1; }
.header-close { padding: 4px 8px; }
.close-icon { color: rgba(255,255,255,0.8); font-size: 16px; }

.ai-dialogue-section {
  display: flex;
  padding: 16px;
  align-items: flex-start;
}
.ai-avatar {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: bold; color: #555;
  flex-shrink: 0; margin-right: 10px;
}
.dialogue-bubble {
  background: #f5f5f5;
  border-radius: 12px 12px 12px 4px;
  padding: 12px 14px;
  flex: 1;
}
.dialogue-text { font-size: 14px; color: #333; line-height: 1.6; }

.stats-row {
  display: flex;
  padding: 12px 16px;
  justify-content: space-around;
  align-items: center;
}
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 18px; font-weight: bold; color: #667eea; }
.stat-label { font-size: 11px; color: #999; margin-top: 2px; }
.stat-divider { width: 1px; height: 24px; background: #eee; }

.achievement-banner {
  margin: 0 16px 12px;
  border-radius: 14px;
  overflow: hidden;
  position: relative;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
}
.banner-glow {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.4), transparent 70%);
  animation: glow 2s ease-in-out infinite alternate;
}
@keyframes glow { from { opacity: 0.5; } to { opacity: 1; } }
.banner-content { position: relative; padding: 16px; }
.banner-title { display: block; font-size: 16px; font-weight: bold; color: #fff; }
.banner-milestone { display: block; font-size: 12px; color: rgba(255,255,255,0.9); margin-top: 4px; }
.banner-story { display: block; font-size: 13px; color: #fff; line-height: 1.6; margin-top: 8px; }

.action-row {
  display: flex;
  padding: 0 16px 16px;
  gap: 10px;
}
.action-btn {
  flex: 1;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.action-btn.secondary { background: #f0f0f0; }
.action-btn.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.btn-text { font-size: 14px; }
.secondary .btn-text { color: #666; }
.primary .btn-text { color: #fff; }
</style>
