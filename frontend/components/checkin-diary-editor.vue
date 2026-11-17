<template>
  <view v-if="visible" class="diary-overlay" @click="handleClose">
    <view class="diary-panel ahp-slide-up" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <view class="header-info">
          <text class="panel-title">📝 打卡日记</text>
          <text class="panel-subtitle">{{ habitName }}</text>
        </view>
        <view class="header-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <scroll-view scroll-y class="diary-body">
        <!-- 心情选择 -->
        <view class="section">
          <text class="section-label">此刻心情</text>
          <view class="mood-grid">
            <view
              v-for="mood in moodOptions"
              :key="mood.value"
              class="mood-item"
              :class="{ active: selectedMood === mood.value }"
              @click="selectedMood = mood.value"
            >
              <text class="mood-emoji">{{ mood.icon }}</text>
              <text class="mood-label">{{ mood.label }}</text>
            </view>
          </view>
        </view>

        <!-- 日记输入 -->
        <view class="section">
          <text class="section-label">记录这一刻</text>
          <view class="textarea-wrap">
            <textarea
              v-model="diaryContent"
              class="diary-textarea"
              placeholder="写下你此刻的感受、今天的收获、或者任何想记录的话..."
              maxlength="200"
              :auto-height="true"
            />
            <text class="char-count">{{ diaryContent.length }}/200</text>
          </view>
        </view>

        <!-- AI鼓励回复 -->
        <view v-if="aiReply" class="ai-reply-section ahp-fade-in-up">
          <view class="ai-reply-header">
            <view class="ai-avatar-mini">
              <text class="ai-emoji">{{ aiEmoji }}</text>
            </view>
            <text class="ai-reply-title">AI伙伴的回应</text>
          </view>
          <view class="ai-reply-content">
            <text class="ai-reply-text">{{ aiReply }}</text>
          </view>
        </view>

        <!-- 历史日记 -->
        <view v-if="historyDiaries.length > 0" class="history-section">
          <text class="section-label">历史日记</text>
          <view
            v-for="(diary, index) in historyDiaries"
            :key="diary.id || index"
            class="history-item"
          >
            <view class="history-header">
              <text class="history-mood">{{ getMoodIcon(diary.mood) }}</text>
              <text class="history-time">{{ formatTime(diary.created_at) }}</text>
            </view>
            <text class="history-content">{{ diary.content }}</text>
            <view v-if="diary.ai_encouragement" class="history-ai-reply">
              <text class="history-ai-text">{{ diary.ai_encouragement }}</text>
            </view>
          </view>
        </view>

        <view class="bottom-space"></view>
      </scroll-view>

      <!-- 底部保存按钮 -->
      <view class="diary-footer">
        <view
          class="save-btn"
          :class="{ disabled: !diaryContent.trim() }"
          @click="handleSave"
        >
          <text class="save-text">{{ aiReply ? '完成' : '保存日记' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import habitApi from '@/api/habit'
import { getCharacterById } from '@/common/ai-characters'

export default {
  name: 'checkin-diary-editor',
  props: {
    visible: { type: Boolean, default: false },
    habitId: { type: Number, default: 0 },
    habitName: { type: String, default: '' },
    checkinId: { type: Number, default: 0 }
  },
  data() {
    return {
      diaryContent: '',
      selectedMood: 'calm',
      aiReply: '',
      historyDiaries: [],
      moodOptions: [
        { value: 'happy', icon: '😊', label: '开心' },
        { value: 'excited', icon: '🤩', label: '兴奋' },
        { value: 'calm', icon: '😌', label: '平静' },
        { value: 'tired', icon: '😴', label: '疲惫' },
        { value: 'sad', icon: '😔', label: '低落' },
        { value: 'angry', icon: '😤', label: '烦躁' }
      ]
    }
  },
  computed: {
    aiEmoji() {
      const charId = this.$store?.state?.aiConfig?.avatarType || 'linxi'
      const char = getCharacterById(charId)
      return char?.emoji || '🌸'
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.resetForm()
        this.loadHistory()
      }
    }
  },
  methods: {
    resetForm() {
      this.diaryContent = ''
      this.selectedMood = 'calm'
      this.aiReply = ''
    },
    async loadHistory() {
      try {
        const res = await habitApi.getDiaries(this.habitId)
        const data = res?.data || res
        if (Array.isArray(data)) {
          this.historyDiaries = data.slice(0, 10)
        }
      } catch (e) {
        console.error('加载历史日记失败', e)
        this.historyDiaries = []
      }
    },
    async handleSave() {
      if (!this.diaryContent.trim()) return

      if (this.aiReply) {
        // 已有AI回复，直接关闭
        this.handleClose()
        return
      }

      uni.showLoading({ title: '保存中...' })
      try {
        const res = await habitApi.submitDiary({
          habit_id: this.habitId,
          checkin_id: this.checkinId,
          content: this.diaryContent.trim(),
          mood: this.selectedMood
        })

        const diary = res?.data || res
        if (diary?.ai_encouragement) {
          this.aiReply = diary.ai_encouragement
          // 添加到store
          this.$store.commit('addCheckinDiary', {
            id: diary.id || Date.now(),
            habit_id: this.habitId,
            content: this.diaryContent.trim(),
            mood: this.selectedMood,
            ai_encouragement: diary.ai_encouragement,
            created_at: diary.created_at || new Date().toISOString()
          })
          // 添加到历史列表头部
          this.historyDiaries.unshift({
            id: diary.id || Date.now(),
            content: this.diaryContent.trim(),
            mood: this.selectedMood,
            ai_encouragement: diary.ai_encouragement,
            created_at: diary.created_at || new Date().toISOString()
          })
        }

        uni.hideLoading()
        uni.showToast({ title: '保存成功', icon: 'success' })
      } catch (e) {
        uni.hideLoading()
        console.error('保存日记失败', e)
        uni.showToast({ title: '保存失败', icon: 'none' })
      }
    },
    handleClose() {
      this.$emit('close')
    },
    getMoodIcon(mood) {
      const found = this.moodOptions.find(m => m.value === mood)
      return found?.icon || '😌'
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      const d = new Date(timeStr)
      const now = new Date()
      const diff = now - d
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
      if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
      return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    }
  }
}
</script>

<style lang="scss" scoped>
.diary-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: flex;
  align-items: flex-end;
}

.diary-panel {
  width: 100%;
  max-height: 85vh;
  background: var(--bg-card, #fff);
  border-radius: 32rpx 32rpx 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid var(--border-color, #F0F0F0);
}

.header-info {
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--text-primary, #333);
}

.panel-subtitle {
  font-size: 24rpx;
  color: var(--primary-color, #6B8E7B);
  margin-top: 6rpx;
}

.header-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  font-size: 36rpx;
  color: var(--text-light, #999);
}

.diary-body {
  flex: 1;
  padding: 24rpx 32rpx;
}

.section {
  margin-bottom: 32rpx;
}

.section-label {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary, #333);
  display: block;
  margin-bottom: 16rpx;
}

.mood-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.mood-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 24rpx;
  border-radius: 16rpx;
  background: var(--bg-secondary, #F5F6F7);
  transition: all 0.2s;
}

.mood-item.active {
  background: var(--primary-color, #6B8E7B);
  transform: scale(1.05);
}

.mood-emoji {
  font-size: 36rpx;
  margin-bottom: 6rpx;
}

.mood-label {
  font-size: 22rpx;
  color: var(--text-secondary, #666);
}

.mood-item.active .mood-label {
  color: #fff;
}

.textarea-wrap {
  position: relative;
}

.diary-textarea {
  width: 100%;
  min-height: 200rpx;
  background: var(--bg-secondary, #F5F6F7);
  border-radius: 20rpx;
  padding: 24rpx;
  font-size: 28rpx;
  color: var(--text-primary, #333);
  box-sizing: border-box;
  line-height: 1.6;
}

.char-count {
  position: absolute;
  bottom: 16rpx;
  right: 24rpx;
  font-size: 22rpx;
  color: var(--text-light, #999);
}

.ai-reply-section {
  background: linear-gradient(135deg, rgba(107, 142, 123, 0.06), rgba(168, 201, 184, 0.04));
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 32rpx;
  border: 1rpx solid rgba(107, 142, 123, 0.12);
}

.ai-reply-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.ai-avatar-mini {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #6B8E7B, #A8C9B8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-emoji {
  font-size: 28rpx;
}

.ai-reply-title {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary-color, #6B8E7B);
}

.ai-reply-content {
  padding-left: 60rpx;
}

.ai-reply-text {
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--text-primary, #333);
}

.history-section {
  margin-bottom: 32rpx;
}

.history-item {
  background: var(--bg-secondary, #F8F9FA);
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.history-mood {
  font-size: 28rpx;
}

.history-time {
  font-size: 22rpx;
  color: var(--text-light, #999);
}

.history-content {
  font-size: 28rpx;
  line-height: 1.5;
  color: var(--text-primary, #333);
  display: block;
  margin-bottom: 12rpx;
}

.history-ai-reply {
  background: rgba(107, 142, 123, 0.06);
  border-radius: 12rpx;
  padding: 16rpx;
  border-left: 4rpx solid var(--primary-color, #6B8E7B);
}

.history-ai-text {
  font-size: 26rpx;
  color: var(--text-secondary, #666);
  line-height: 1.5;
}

.bottom-space {
  height: 120rpx;
}

.diary-footer {
  position: sticky;
  bottom: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid var(--border-color, #F0F0F0);
  z-index: 10;
}

.save-btn {
  width: 100%;
  height: 84rpx;
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
  border-radius: 42rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(107, 142, 123, 0.3);
  transition: transform 0.2s;
}

.save-btn:active {
  transform: scale(0.98);
}

.save-btn.disabled {
  background: var(--bg-secondary, #D0D0D0);
  box-shadow: none;
}

.save-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}
</style>
