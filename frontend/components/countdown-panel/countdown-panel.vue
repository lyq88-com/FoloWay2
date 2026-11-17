<template>
  <view v-if="visible" class="popup-mask" @click="closePanel">
    <view class="panel-content" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <text class="panel-title">未来倒计时</text>
        <text class="panel-close" @click="closePanel">✕</text>
      </view>

      <scroll-view scroll-y class="panel-body">
        <!-- 倒计时显示区 -->
        <view v-if="activeCountdown" class="countdown-display">
          <view class="countdown-mode-tag" :class="{ positive: isPositiveMode }">
            <text>{{ isPositiveMode ? '正计时' : '倒计时' }}</text>
          </view>
          <view class="countdown-target-name">
            <text class="target-icon">{{ activeCountdown.icon || '🎯' }}</text>
            <text class="target-name">{{ activeCountdown.name }}</text>
          </view>
          <view class="countdown-numbers">
            <view class="time-block">
              <text class="time-num">{{ displayDays }}</text>
              <text class="time-unit">天</text>
            </view>
            <view class="time-colon"><text>:</text></view>
            <view class="time-block">
              <text class="time-num">{{ displayHours }}</text>
              <text class="time-unit">时</text>
            </view>
            <view class="time-colon"><text>:</text></view>
            <view class="time-block">
              <text class="time-num">{{ displayMinutes }}</text>
              <text class="time-unit">分</text>
            </view>
            <view class="time-colon"><text>:</text></view>
            <view class="time-block">
              <text class="time-num">{{ displaySeconds }}</text>
              <text class="time-unit">秒</text>
            </view>
          </view>
          <view class="countdown-progress-bar">
            <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
          </view>
          <view class="countdown-deadline">
            <text>{{ isPositiveMode ? '已过时间' : '截止时间' }}: {{ formatDate(isPositiveMode ? activeCountdown.startDate : activeCountdown.deadline) }}</text>
          </view>
          <!-- AI 督促消息 -->
          <view v-if="aiMessage" class="ai-message-card">
            <view class="ai-avatar">{{ aiAvatar }}</view>
            <view class="ai-message-content">
              <text class="ai-message-text">{{ aiMessage }}</text>
              <text class="ai-message-time">{{ aiMessageTime }}</text>
            </view>
          </view>
          <!-- 操作按钮 -->
          <view class="countdown-actions">
            <view class="action-btn switch" @click="toggleMode">
              <text>{{ isPositiveMode ? '切换倒计时' : '切换正计时' }}</text>
            </view>
            <view class="action-btn delete" @click="deleteCountdown">
              <text>删除</text>
            </view>
          </view>
        </view>

        <!-- 无活跃倒计时时的提示 -->
        <view v-else class="empty-state">
          <text class="empty-icon">🎯</text>
          <text class="empty-text">还没有设置倒计时</text>
          <text class="empty-desc">创建一个目标倒计时，AI伙伴会陪你一起坚持</text>
        </view>

        <!-- 历史倒计时列表 -->
        <view v-if="countdownList.length > 0" class="history-section">
          <view class="section-header">
            <text class="section-title">历史目标</text>
          </view>
          <view
            v-for="item in countdownList"
            :key="item.id"
            class="history-item"
            :class="{ active: activeCountdown && activeCountdown.id === item.id }"
            @click="selectCountdown(item)"
          >
            <view class="history-item-info">
              <text class="history-icon">{{ item.icon || '🎯' }}</text>
              <view class="history-text">
                <text class="history-name">{{ item.name }}</text>
                <text class="history-deadline">截止: {{ formatDate(item.deadline) }}</text>
              </view>
            </view>
            <view class="history-status" :class="item.status">
              <text>{{ getStatusText(item.status) }}</text>
            </view>
          </view>
        </view>

        <!-- 创建/编辑表单 -->
        <view class="create-section">
          <view class="section-header">
            <text class="section-title">{{ editingId ? '编辑倒计时' : '创建新倒计时' }}</text>
          </view>
          <view class="form-group">
            <text class="form-label">目标名称</text>
            <input v-model="formData.name" class="form-input" placeholder="例如：考研倒计时、减肥30天..." maxlength="20" />
          </view>
          <view class="form-group">
            <text class="form-label">目标图标</text>
            <view class="icon-picker">
              <view
                v-for="icon in presetIcons"
                :key="icon"
                class="icon-option"
                :class="{ active: formData.icon === icon }"
                @click="formData.icon = icon"
              >
                <text>{{ icon }}</text>
              </view>
            </view>
          </view>
          <view class="form-group">
            <text class="form-label">截止日期</text>
            <picker mode="date" :value="formData.deadline" @change="onDeadlineChange">
              <view class="picker-value">
                <text>{{ formData.deadline || '选择截止日期' }}</text>
                <text class="picker-arrow">›</text>
              </view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">每日提醒时间</text>
            <picker mode="time" :value="formData.reminderTime" @change="onReminderChange">
              <view class="picker-value">
                <text>{{ formData.reminderTime || '选择提醒时间' }}</text>
                <text class="picker-arrow">›</text>
              </view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">任务时长（小时）</text>
            <view class="duration-options">
              <view
                v-for="opt in durationOptions"
                :key="opt.value"
                class="duration-option"
                :class="{ active: formData.duration === opt.value }"
                @click="formData.duration = opt.value"
              >
                <text>{{ opt.label }}</text>
              </view>
            </view>
          </view>
          <view class="form-group">
            <view class="switch-row">
              <text class="form-label">系统通知提醒</text>
              <switch :checked="formData.notifyEnabled" @change="onNotifyChange" color="#6B8E7B" />
            </view>
          </view>
          <view class="form-group">
            <view class="switch-row">
              <text class="form-label">同步至成长档案</text>
              <switch :checked="formData.syncToArchive" @change="onSyncChange" color="#6B8E7B" />
            </view>
          </view>
          <view class="form-bottom-space"></view>
        </view>
      </scroll-view>

      <!-- 底部操作按钮 -->
      <view class="panel-footer">
        <view class="save-btn" :class="{ disabled: !canSave }" @click="saveCountdown">
          <text class="save-btn-text">{{ editingId ? '更新' : '创建倒计时' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getInactivityDialogue, getRandomLocationDialogue } from '@/common/walk-map-config.js'

const STORAGE_KEY = 'ahp_countdowns'
const ARCHIVE_KEY = 'ahp_countdown_archive'

export default {
  name: 'countdown-panel',
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      countdownList: [],
      activeCountdownId: null,
      editingId: null,
      formData: {
        name: '',
        icon: '🎯',
        deadline: '',
        reminderTime: '08:00',
        duration: 2,
        notifyEnabled: true,
        syncToArchive: true
      },
      presetIcons: ['🎯', '📚', '💪', '🏃', '⏰', '🏆', '✏️', '🎨', '🎸', '💻'],
      durationOptions: [
        { value: 1, label: '1小时' },
        { value: 2, label: '2小时' },
        { value: 4, label: '4小时' },
        { value: 8, label: '8小时' }
      ],
      currentTime: Date.now(),
      timerInterval: null,
      aiMessage: '',
      aiMessageTime: '',
      aiAvatar: '🌸',
      lastReminderKey: ''
    }
  },
  computed: {
    activeCountdown() {
      if (!this.activeCountdownId) return null
      return this.countdownList.find(c => c.id === this.activeCountdownId) || null
    },
    isPositiveMode() {
      return this.activeCountdown && this.activeCountdown.mode === 'positive'
    },
    remainingTime() {
      if (!this.activeCountdown) return { days: 0, hours: 0, minutes: 0, seconds: 0 }
      const now = this.currentTime
      if (this.isPositiveMode) {
        const start = new Date(this.activeCountdown.startDate + 'T00:00:00').getTime()
        const diff = now - start
        return this.parseTime(diff)
      } else {
        const deadline = new Date(this.activeCountdown.deadline + 'T23:59:59').getTime()
        const diff = deadline - now
        return this.parseTime(Math.max(0, diff))
      }
    },
    displayDays() {
      return String(this.remainingTime.days).padStart(2, '0')
    },
    displayHours() {
      return String(this.remainingTime.hours).padStart(2, '0')
    },
    displayMinutes() {
      return String(this.remainingTime.minutes).padStart(2, '0')
    },
    displaySeconds() {
      return String(this.remainingTime.seconds).padStart(2, '0')
    },
    progressPercent() {
      if (!this.activeCountdown) return 0
      if (this.isPositiveMode) {
        const start = new Date(this.activeCountdown.startDate + 'T00:00:00').getTime()
        const totalDuration = this.activeCountdown.duration * 3600 * 1000
        const elapsed = this.currentTime - start
        return Math.min(100, Math.round(elapsed / totalDuration * 100))
      } else {
        const created = new Date(this.activeCountdown.createdAt).getTime()
        const deadline = new Date(this.activeCountdown.deadline + 'T23:59:59').getTime()
        const total = deadline - created
        const remaining = deadline - this.currentTime
        if (total <= 0) return 100
        return Math.max(0, Math.min(100, Math.round((1 - remaining / total) * 100)))
      }
    },
    canSave() {
      return this.formData.name.trim().length > 0 && this.formData.deadline
    },
    aiCharacterId() {
      return this.$store.state.aiConfig?.avatarType || 'linxi'
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadData()
        this.startTimer()
      } else {
        this.stopTimer()
      }
    }
  },
  beforeDestroy() {
    this.stopTimer()
  },
  methods: {
    loadData() {
      try {
        const stored = uni.getStorageSync(STORAGE_KEY) || []
        this.countdownList = stored
        // 自动选择第一个进行中的倒计时
        const active = stored.find(c => c.status === 'active')
        if (active && !this.activeCountdownId) {
          this.activeCountdownId = active.id
        }
      } catch (e) {
        this.countdownList = []
      }
    },
    saveData() {
      try {
        uni.setStorageSync(STORAGE_KEY, this.countdownList)
      } catch (e) {
        console.error('保存倒计时数据失败', e)
      }
    },
    startTimer() {
      this.stopTimer()
      this.currentTime = Date.now()
      this.timerInterval = setInterval(() => {
        this.currentTime = Date.now()
        this.checkCountdownStatus()
        this.checkAIReminder()
      }, 1000)
    },
    stopTimer() {
      if (this.timerInterval) {
        clearInterval(this.timerInterval)
        this.timerInterval = null
      }
    },
    parseTime(ms) {
      if (ms <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0 }
      const totalSeconds = Math.floor(ms / 1000)
      const days = Math.floor(totalSeconds / 86400)
      const hours = Math.floor((totalSeconds % 86400) / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      return { days, hours, minutes, seconds }
    },
    formatDate(dateStr) {
      if (!dateStr) return '--'
      const d = new Date(dateStr)
      const m = d.getMonth() + 1
      const day = d.getDate()
      return `${d.getFullYear()}/${m}/${day}`
    },
    getStatusText(status) {
      const map = { active: '进行中', completed: '已完成', expired: '已超时' }
      return map[status] || '未知'
    },
    onDeadlineChange(e) {
      this.formData.deadline = e.detail.value
    },
    onReminderChange(e) {
      this.formData.reminderTime = e.detail.value
    },
    onNotifyChange(e) {
      this.formData.notifyEnabled = e.detail.value
    },
    onSyncChange(e) {
      this.formData.syncToArchive = e.detail.value
    },
    saveCountdown() {
      if (!this.canSave) return
      const now = new Date()
      const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
      if (this.editingId) {
        const idx = this.countdownList.findIndex(c => c.id === this.editingId)
        if (idx > -1) {
          this.countdownList[idx] = {
            ...this.countdownList[idx],
            ...this.formData,
            name: this.formData.name.trim()
          }
        }
        this.editingId = null
      } else {
        const newCountdown = {
          id: Date.now(),
          name: this.formData.name.trim(),
          icon: this.formData.icon,
          deadline: this.formData.deadline,
          reminderTime: this.formData.reminderTime,
          duration: this.formData.duration,
          notifyEnabled: this.formData.notifyEnabled,
          syncToArchive: this.formData.syncToArchive,
          mode: 'countdown',
          status: 'active',
          createdAt: now.getTime(),
          startDate: dateStr,
          aiMessages: []
        }
        this.countdownList.unshift(newCountdown)
        this.activeCountdownId = newCountdown.id
        this.setupSystemNotification(newCountdown)
      }
      this.saveData()
      this.syncToArchive()
      this.resetForm()
      uni.showToast({ title: this.editingId ? '已更新' : '已创建', icon: 'success' })
    },
    resetForm() {
      this.formData = {
        name: '',
        icon: '🎯',
        deadline: '',
        reminderTime: '08:00',
        duration: 2,
        notifyEnabled: true,
        syncToArchive: true
      }
    },
    selectCountdown(item) {
      this.activeCountdownId = item.id
      this.formData = {
        name: item.name,
        icon: item.icon,
        deadline: item.deadline,
        reminderTime: item.reminderTime,
        duration: item.duration,
        notifyEnabled: item.notifyEnabled,
        syncToArchive: item.syncToArchive
      }
      this.editingId = item.id
    },
    toggleMode() {
      if (!this.activeCountdown) return
      const idx = this.countdownList.findIndex(c => c.id === this.activeCountdown.id)
      if (idx > -1) {
        this.countdownList[idx].mode = this.isPositiveMode ? 'countdown' : 'positive'
        this.saveData()
        uni.showToast({ title: this.isPositiveMode ? '已切换倒计时' : '已切换正计时', icon: 'none' })
      }
    },
    deleteCountdown() {
      if (!this.activeCountdown) return
      uni.showModal({
        title: '确认删除',
        content: `确定要删除「${this.activeCountdown.name}」吗？`,
        success: (r) => {
          if (r.confirm) {
            this.countdownList = this.countdownList.filter(c => c.id !== this.activeCountdown.id)
            this.activeCountdownId = null
            this.saveData()
            uni.showToast({ title: '已删除', icon: 'none' })
          }
        }
      })
    },
    checkCountdownStatus() {
      if (!this.activeCountdown) return
      const now = Date.now()
      const deadline = new Date(this.activeCountdown.deadline + 'T23:59:59').getTime()
      if (!this.isPositiveMode && now > deadline && this.activeCountdown.status === 'active') {
        const idx = this.countdownList.findIndex(c => c.id === this.activeCountdown.id)
        if (idx > -1) {
          this.countdownList[idx].status = 'expired'
          this.saveData()
          // AI 情绪疏导
          this.triggerAIEmotionSupport()
        }
      }
      // 正计时模式完成判定
      if (this.isPositiveMode) {
        const start = new Date(this.activeCountdown.startDate + 'T00:00:00').getTime()
        const totalDuration = this.activeCountdown.duration * 3600 * 1000
        if (now - start >= totalDuration && this.activeCountdown.status === 'active') {
          const idx = this.countdownList.findIndex(c => c.id === this.activeCountdown.id)
          if (idx > -1) {
            this.countdownList[idx].status = 'completed'
            this.saveData()
            // 同步行走里程
            this.$store.commit('addWalkStep', {
              steps: 1,
              type: 'habit',
              description: '完成倒计时目标: ' + this.activeCountdown.name
            })
            uni.showToast({ title: '🎉 目标达成！', icon: 'success' })
          }
        }
      }
    },
    checkAIReminder() {
      if (!this.activeCountdown || this.isPositiveMode) return
      const deadline = new Date(this.activeCountdown.deadline + 'T23:59:59').getTime()
      const now = this.currentTime
      const remaining = deadline - now
      const oneDay = 86400000
      const threeDays = oneDay * 3
      const oneWeek = oneDay * 7
      // 临近截止：3天内、1天内、超时
      let reminderKey = ''
      if (remaining < 0) {
        reminderKey = 'expired_' + this.activeCountdown.id
      } else if (remaining < oneDay) {
        reminderKey = '1day_' + this.activeCountdown.id
      } else if (remaining < threeDays) {
        reminderKey = '3days_' + this.activeCountdown.id
      } else if (remaining < oneWeek) {
        reminderKey = '7days_' + this.activeCountdown.id
      }
      if (reminderKey && reminderKey !== this.lastReminderKey) {
        this.lastReminderKey = reminderKey
        this.triggerAIReminder(remaining)
      }
    },
    triggerAIReminder(remaining) {
      const charId = this.aiCharacterId
      const stageId = this.$store.getters.currentStage?.id || 0
      let msg = ''
      if (remaining < 0) {
        msg = getInactivityDialogue(charId)
      } else if (remaining < 86400000) {
        msg = getRandomLocationDialogue(charId, stageId)
      } else if (remaining < 86400000 * 3) {
        const reminders = [
          '时间不多了，但我们还有机会！再坚持一下~',
          '倒计时在加速，你的努力也要跟上节奏哦',
          '最后的冲刺阶段，我在你身边陪你走完'
        ]
        msg = reminders[Math.floor(Math.random() * reminders.length)]
      } else {
        const reminders = [
          '一周倒计时开始啦，稳步推进，不用着急~',
          '时间在走，你也在前进，继续加油',
          '倒计时提醒你：每一步都在靠近目标'
        ]
        msg = reminders[Math.floor(Math.random() * reminders.length)]
      }
      this.aiMessage = msg
      const now = new Date()
      this.aiMessageTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      this.aiAvatar = this.getAIAvatar(charId)
      // 存储AI消息
      if (this.activeCountdown) {
        const idx = this.countdownList.findIndex(c => c.id === this.activeCountdown.id)
        if (idx > -1) {
          if (!this.countdownList[idx].aiMessages) this.countdownList[idx].aiMessages = []
          this.countdownList[idx].aiMessages.push({ msg, time: this.aiMessageTime })
          this.saveData()
        }
      }
    },
    triggerAIEmotionSupport() {
      const charId = this.aiCharacterId
      const supportMessages = [
        '任务超时了也没关系，你已经很努力了！休息一下，我们重新出发~',
        '超时不代表失败，它只说明我们需要调整策略。别自责，我陪着你',
        '时间到了但你的坚持没有被浪费。每一次努力都算数，深呼吸，再来',
        '没完成也没事呀，重要的是你开始了。我们一起复盘，下次会更好'
      ]
      this.aiMessage = supportMessages[Math.floor(Math.random() * supportMessages.length)]
      const now = new Date()
      this.aiMessageTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      this.aiAvatar = this.getAIAvatar(charId)
      this.$store.commit('addChatMessage', {
        type: 'ai',
        content: this.aiMessage,
        time: Date.now()
      })
    },
    getAIAvatar(charId) {
      const avatars = {
        linxi: '🌸', mianmian: '🍑', yuki: '⚡', kira: '🗡️', yueqing: '🌙',
        fengye: '🍁', nova: '🤖', zero: '📊', xingchen: '✨', muhan: '📜',
        qinghe: '🌿', chenfeng: '💨', sunny: '☀️', lele: '😄', linglong: '🔔',
        baihu: '🐯', qinglan: '🕊️', xuanwu: '🐢', huoyun: '🔥', linling: '💝'
      }
      return avatars[charId] || '🌸'
    },
    setupSystemNotification(countdown) {
      // #ifdef H5
      if (countdown.notifyEnabled && 'Notification' in window) {
        if (Notification.permission === 'granted') {
          this.scheduleNotification(countdown)
        } else if (Notification.permission !== 'denied') {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              this.scheduleNotification(countdown)
            }
          })
        }
      }
      // #endif
    },
    scheduleNotification(countdown) {
      // #ifdef H5
      if (!countdown.reminderTime) return
      const [hours, minutes] = countdown.reminderTime.split(':').map(Number)
      const now = new Date()
      const notifyTime = new Date()
      notifyTime.setHours(hours, minutes, 0, 0)
      if (notifyTime <= now) {
        notifyTime.setDate(notifyTime.getDate() + 1)
      }
      const delay = notifyTime.getTime() - now.getTime()
      setTimeout(() => {
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('循途 - 倒计时提醒', {
            body: `${countdown.icon} ${countdown.name} - 剩余时间不多了，加油！`,
            icon: '/static/logo.png'
          })
        }
      }, delay)
      // #endif
    },
    syncToArchive() {
      if (!this.formData.syncToArchive) return
      try {
        const archive = uni.getStorageSync(ARCHIVE_KEY) || []
        const now = new Date()
        const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
        archive.push({
          date: dateStr,
          type: 'countdown',
          name: this.formData.name,
          deadline: this.formData.deadline,
          timestamp: now.getTime()
        })
        if (archive.length > 500) archive.splice(0, archive.length - 500)
        uni.setStorageSync(ARCHIVE_KEY, archive)
      } catch (e) {
        console.error('同步档案失败', e)
      }
    },
    closePanel() {
      this.stopTimer()
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.panel-content {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.panel-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
}
.panel-close {
  font-size: 36rpx;
  color: #999;
  padding: 8rpx;
}
.panel-body {
  flex: 1;
  padding: 24rpx 32rpx;
  max-height: 70vh;
}

/* 倒计时显示 */
.countdown-display {
  background: linear-gradient(135deg, #6B8E7B 0%, #8FBC8F 100%);
  border-radius: 24rpx;
  padding: 40rpx 32rpx;
  margin-bottom: 24rpx;
  text-align: center;
}
.countdown-mode-tag {
  display: inline-block;
  padding: 6rpx 20rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20rpx;
  margin-bottom: 20rpx;
}
.countdown-mode-tag text {
  font-size: 22rpx;
  color: #fff;
}
.countdown-mode-tag.positive {
  background: rgba(255, 217, 61, 0.3);
}
.countdown-target-name {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}
.target-icon {
  font-size: 36rpx;
  margin-right: 12rpx;
}
.target-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}
.countdown-numbers {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}
.time-block {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.time-num {
  font-size: 64rpx;
  font-weight: 700;
  color: #fff;
  font-family: 'Helvetica Neue', monospace;
}
.time-unit {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4rpx;
}
.time-colon {
  font-size: 48rpx;
  color: rgba(255, 255, 255, 0.5);
  padding: 0 8rpx;
  margin-bottom: 20rpx;
}
.countdown-progress-bar {
  width: 100%;
  height: 8rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
}
.progress-fill {
  height: 100%;
  background: #FFD93D;
  border-radius: 4rpx;
  transition: width 0.5s ease;
}
.countdown-deadline {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}
.ai-message-card {
  display: flex;
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16rpx;
  padding: 20rpx;
  margin-top: 20rpx;
}
.ai-avatar {
  font-size: 36rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.ai-message-content {
  flex: 1;
  text-align: left;
}
.ai-message-text {
  font-size: 26rpx;
  color: #fff;
  display: block;
  line-height: 1.5;
}
.ai-message-time {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8rpx;
  display: block;
}
.countdown-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
}
.action-btn {
  flex: 1;
  height: 72rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.action-btn.switch {
  background: rgba(255, 255, 255, 0.2);
}
.action-btn.switch text {
  font-size: 26rpx;
  color: #fff;
}
.action-btn.delete {
  background: rgba(255, 107, 107, 0.2);
}
.action-btn.delete text {
  font-size: 26rpx;
  color: #FF6B6B;
}
.action-btn:active {
  transform: scale(0.95);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60rpx 0;
}
.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 16rpx;
}
.empty-text {
  font-size: 30rpx;
  color: #333;
  font-weight: 600;
  display: block;
  margin-bottom: 8rpx;
}
.empty-desc {
  font-size: 24rpx;
  color: #999;
}

/* 历史列表 */
.history-section {
  margin-bottom: 24rpx;
}
.section-header {
  margin-bottom: 16rpx;
}
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
}
.history-item.active {
  background: #E8F5E9;
  border: 2rpx solid #6B8E7B;
}
.history-item-info {
  display: flex;
  align-items: center;
  flex: 1;
}
.history-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}
.history-text {
  flex: 1;
}
.history-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
}
.history-deadline {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
  display: block;
}
.history-status {
  padding: 6rpx 16rpx;
  border-radius: 12rpx;
}
.history-status.active {
  background: #E8F5E9;
}
.history-status.active text {
  color: #4CAF50;
  font-size: 22rpx;
}
.history-status.completed {
  background: #E3F2FD;
}
.history-status.completed text {
  color: #2196F3;
  font-size: 22rpx;
}
.history-status.expired {
  background: #FFEBEE;
}
.history-status.expired text {
  color: #F44336;
  font-size: 22rpx;
}

/* 表单 */
.form-group {
  margin-bottom: 24rpx;
}
.form-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 12rpx;
}
.form-input {
  width: 100%;
  height: 80rpx;
  background: #F5F6F7;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333;
  box-sizing: border-box;
}
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.icon-option {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  background: #F5F6F7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  transition: all 0.2s;
}
.icon-option.active {
  background: #6B8E7B;
  transform: scale(1.1);
}
.picker-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 80rpx;
  background: #F5F6F7;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333;
}
.picker-arrow {
  font-size: 32rpx;
  color: #999;
}
.duration-options {
  display: flex;
  gap: 12rpx;
}
.duration-option {
  flex: 1;
  height: 72rpx;
  border-radius: 16rpx;
  background: #F5F6F7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  color: #666;
  transition: all 0.2s;
}
.duration-option.active {
  background: #6B8E7B;
  color: #fff;
}
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.switch-row .form-label {
  margin-bottom: 0;
}
.form-bottom-space {
  height: 120rpx;
}

/* 底部按钮 */
.panel-footer {
  background: rgba(255, 255, 255, 0.98);
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #F0F0F0;
}
.save-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #6B8E7B 0%, #5A7A6A 100%);
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(107, 142, 123, 0.35);
}
.save-btn:active {
  transform: scale(0.98);
}
.save-btn.disabled {
  background: #D0D0D0;
  box-shadow: none;
}
.save-btn-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}
</style>
