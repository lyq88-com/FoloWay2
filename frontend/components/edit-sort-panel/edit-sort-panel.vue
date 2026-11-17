<template>
  <view v-if="visible" class="popup-mask" @click="closePanel">
    <view class="panel-content" @click.stop>
      <!-- 头部 -->
      <view class="panel-header">
        <text class="panel-title">编辑排序</text>
        <view class="header-actions">
          <view v-if="!editMode" class="header-btn" @click="enterEditMode">
            <text class="btn-text">编辑</text>
          </view>
          <view v-else class="header-btn save" @click="saveSort">
            <text class="btn-text">保存</text>
          </view>
          <text class="panel-close" @click="closePanel">✕</text>
        </view>
      </view>

      <scroll-view scroll-y class="panel-body">
        <!-- 批量操作栏 -->
        <view class="batch-bar">
          <view class="batch-left">
            <view class="select-all-btn" @click="toggleSelectAll">
              <view class="checkbox" :class="{ checked: allSelected }">
                <text v-if="allSelected" class="check-icon">✓</text>
              </view>
              <text class="select-text">全选</text>
            </view>
            <text class="selected-count" v-if="selectedIds.length > 0">已选 {{ selectedIds.length }} 项</text>
          </view>
          <view class="batch-actions" v-if="selectedIds.length > 0">
            <view class="batch-btn start" @click="batchStart">
              <text>开启</text>
            </view>
            <view class="batch-btn pause" @click="batchPause">
              <text>暂停</text>
            </view>
            <view class="batch-btn delete" @click="batchDelete">
              <text>删除</text>
            </view>
          </view>
        </view>

        <!-- 习惯排序列表 -->
        <view class="sort-list">
          <view
            v-for="(habit, index) in sortedHabits"
            :key="habit.id"
            class="sort-item"
            :class="{ editing: editMode, selected: selectedIds.includes(habit.id), paused: habit.paused }"
            @click="toggleSelect(habit.id)"
          >
            <!-- 拖拽手柄 -->
            <view v-if="editMode" class="drag-handle" @click.stop>
              <text class="drag-icon">⠿</text>
            </view>
            <!-- 选择框 -->
            <view class="checkbox-wrap" @click.stop="toggleSelect(habit.id)">
              <view class="checkbox" :class="{ checked: selectedIds.includes(habit.id) }">
                <text v-if="selectedIds.includes(habit.id)" class="check-icon">✓</text>
              </view>
            </view>
            <!-- 习惯信息 -->
            <view class="habit-info" @click.stop="editHabit(habit)">
              <view class="habit-icon-wrap" :style="{ background: (habit.color || '#6B8E7B') + '20' }">
                <text class="habit-icon">{{ habit.icon || '⭐' }}</text>
              </view>
              <view class="habit-detail">
                <view class="habit-name-row">
                  <text class="habit-name">{{ habit.name }}</text>
                  <view v-if="habit.paused" class="paused-tag"><text>已暂停</text></view>
                  <view v-if="habit.completed" class="completed-tag"><text>✓</text></view>
                </view>
                <view class="habit-meta">
                  <text class="meta-item">{{ habit.target || '完成1次' }}</text>
                  <text class="meta-divider">|</text>
                  <text class="meta-item">{{ difficultyMap[habit.difficulty] || '简单' }}</text>
                  <text class="meta-divider">|</text>
                  <text class="meta-item">连续{{ habit.streak || 0 }}天</text>
                  <text v-if="habit.reminder_time" class="meta-divider">|</text>
                  <text v-if="habit.reminder_time" class="meta-item">{{ habit.reminder_time }}</text>
                </view>
              </view>
            </view>
            <!-- 排序按钮 -->
            <view v-if="editMode" class="sort-btns">
              <view class="sort-btn up" :class="{ disabled: index === 0 }" @click.stop="moveUp(index)">
                <text>↑</text>
              </view>
              <view class="sort-btn down" :class="{ disabled: index === sortedHabits.length - 1 }" @click.stop="moveDown(index)">
                <text>↓</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 编辑弹窗 -->
        <view v-if="editingHabit" class="edit-modal-mask" @click="closeEditHabit">
          <view class="edit-modal" @click.stop>
            <view class="edit-header">
              <text class="edit-title">编辑习惯</text>
              <text class="edit-close" @click="closeEditHabit">✕</text>
            </view>
            <scroll-view scroll-y class="edit-body">
              <view class="form-group">
                <text class="form-label">任务名称</text>
                <input v-model="editForm.name" class="form-input" placeholder="习惯名称" maxlength="20" />
              </view>
              <view class="form-group">
                <text class="form-label">打卡频次</text>
                <view class="freq-options">
                  <view class="freq-option" :class="{ active: editForm.frequency === 'daily' }" @click="editForm.frequency = 'daily'">
                    <text>每日</text>
                  </view>
                  <view class="freq-option" :class="{ active: editForm.frequency === 'weekly' }" @click="editForm.frequency = 'weekly'">
                    <text>每周</text>
                  </view>
                  <view class="freq-option" :class="{ active: editForm.frequency === 'custom' }" @click="editForm.frequency = 'custom'">
                    <text>自定义</text>
                  </view>
                </view>
              </view>
              <view v-if="editForm.frequency === 'custom'" class="form-group">
                <text class="form-label">自定义天数（每周）</text>
                <view class="weekday-picker">
                  <view
                    v-for="(day, idx) in weekdays"
                    :key="idx"
                    class="weekday-item"
                    :class="{ active: editForm.customDays.includes(idx) }"
                    @click="toggleWeekday(idx)"
                  >
                    <text>{{ day }}</text>
                  </view>
                </view>
              </view>
              <view class="form-group">
                <text class="form-label">每日执行时间</text>
                <picker mode="time" :value="editForm.executionTime" @change="onTimeChange">
                  <view class="picker-value">
                    <text>{{ editForm.executionTime || '选择时间' }}</text>
                    <text class="picker-arrow">›</text>
                  </view>
                </picker>
              </view>
              <view class="form-group">
                <text class="form-label">任务难度</text>
                <view class="diff-options">
                  <view class="diff-option" :class="{ active: editForm.difficulty === 'easy' }" @click="editForm.difficulty = 'easy'">
                    <text>简单</text>
                  </view>
                  <view class="diff-option" :class="{ active: editForm.difficulty === 'medium' }" @click="editForm.difficulty = 'medium'">
                    <text>中等</text>
                  </view>
                  <view class="diff-option" :class="{ active: editForm.difficulty === 'hard' }" @click="editForm.difficulty = 'hard'">
                    <text>困难</text>
                  </view>
                </view>
              </view>
              <view class="form-bottom-space"></view>
            </scroll-view>
            <view class="edit-footer">
              <view class="edit-btn cancel" @click="closeEditHabit">
                <text>取消</text>
              </view>
              <view class="edit-btn save" @click="saveHabitEdit">
                <text>保存</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 提示信息 -->
        <view class="tip-card">
          <text class="tip-icon">💡</text>
          <view class="tip-content">
            <text class="tip-title">操作提示</text>
            <text class="tip-desc">点击「编辑」可拖拽排序；点击习惯卡片可编辑详情；勾选后可批量操作。修改后AI会自动更新督促计划。</text>
          </view>
        </view>
        <view class="form-bottom-space"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'edit-sort-panel',
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      habits: [],
      editMode: false,
      selectedIds: [],
      editingHabit: null,
      editForm: {
        name: '',
        frequency: 'daily',
        customDays: [],
        executionTime: '',
        difficulty: 'easy'
      },
      weekdays: ['一', '二', '三', '四', '五', '六', '日'],
      difficultyMap: { easy: '简单', medium: '中等', hard: '困难' }
    }
  },
  computed: {
    sortedHabits() {
      return [...this.habits].sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
    },
    allSelected() {
      return this.habits.length > 0 && this.selectedIds.length === this.habits.length
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadData()
      }
    }
  },
  methods: {
    loadData() {
      this.habits = [...(this.$store.state.habits || [])].map((h, idx) => ({
        ...h,
        sortOrder: h.sortOrder !== undefined ? h.sortOrder : idx,
        paused: h.paused || false,
        frequency: h.frequency || 'daily',
        customDays: h.customDays || [],
        executionTime: h.executionTime || h.reminder_time || ''
      }))
      this.selectedIds = []
      this.editMode = false
    },
    enterEditMode() {
      this.editMode = true
    },
    saveSort() {
      this.editMode = false
      // 保存排序到Vuex和本地
      const sorted = this.sortedHabits.map((h, idx) => ({ ...h, sortOrder: idx }))
      this.habits = sorted
      this.$store.commit('setHabits', sorted)
      uni.setStorageSync('habits', sorted)
      // AI更新督促计划
      this.triggerAIPlanUpdate()
      uni.showToast({ title: '排序已保存', icon: 'success' })
    },
    toggleSelect(id) {
      const idx = this.selectedIds.indexOf(id)
      if (idx > -1) {
        this.selectedIds.splice(idx, 1)
      } else {
        this.selectedIds.push(id)
      }
    },
    toggleSelectAll() {
      if (this.allSelected) {
        this.selectedIds = []
      } else {
        this.selectedIds = this.habits.map(h => h.id)
      }
    },
    moveUp(index) {
      if (index === 0) return
      const list = this.sortedHabits
      const temp = list[index].sortOrder
      list[index].sortOrder = list[index - 1].sortOrder
      list[index - 1].sortOrder = temp
      this.habits = [...list]
    },
    moveDown(index) {
      if (index === this.sortedHabits.length - 1) return
      const list = this.sortedHabits
      const temp = list[index].sortOrder
      list[index].sortOrder = list[index + 1].sortOrder
      list[index + 1].sortOrder = temp
      this.habits = [...list]
    },
    batchStart() {
      this.selectedIds.forEach(id => {
        const habit = this.habits.find(h => h.id === id)
        if (habit) habit.paused = false
      })
      this.$store.commit('setHabits', this.habits)
      uni.setStorageSync('habits', this.habits)
      uni.showToast({ title: `已开启${this.selectedIds.length}个任务`, icon: 'success' })
      this.selectedIds = []
      this.triggerAIPlanUpdate()
    },
    batchPause() {
      this.selectedIds.forEach(id => {
        const habit = this.habits.find(h => h.id === id)
        if (habit) habit.paused = true
      })
      this.$store.commit('setHabits', this.habits)
      uni.setStorageSync('habits', this.habits)
      uni.showToast({ title: `已暂停${this.selectedIds.length}个任务`, icon: 'none' })
      this.selectedIds = []
      this.triggerAIPlanUpdate()
    },
    batchDelete() {
      uni.showModal({
        title: '批量删除',
        content: `确定要删除选中的${this.selectedIds.length}个习惯吗？`,
        confirmText: '删除',
        confirmColor: '#FF6B6B',
        success: (r) => {
          if (r.confirm) {
            this.habits = this.habits.filter(h => !this.selectedIds.includes(h.id))
            this.$store.commit('setHabits', this.habits)
            uni.setStorageSync('habits', this.habits)
            uni.showToast({ title: '已删除', icon: 'none' })
            this.selectedIds = []
            this.triggerAIPlanUpdate()
          }
        }
      })
    },
    editHabit(habit) {
      this.editingHabit = habit
      this.editForm = {
        name: habit.name || '',
        frequency: habit.frequency || 'daily',
        customDays: [...(habit.customDays || [])],
        executionTime: habit.executionTime || habit.reminder_time || '',
        difficulty: habit.difficulty || 'easy'
      }
    },
    closeEditHabit() {
      this.editingHabit = null
    },
    toggleWeekday(idx) {
      const i = this.editForm.customDays.indexOf(idx)
      if (i > -1) {
        this.editForm.customDays.splice(i, 1)
      } else {
        this.editForm.customDays.push(idx)
      }
    },
    onTimeChange(e) {
      this.editForm.executionTime = e.detail.value
    },
    saveHabitEdit() {
      if (!this.editForm.name.trim()) {
        uni.showToast({ title: '请填写名称', icon: 'none' })
        return
      }
      const idx = this.habits.findIndex(h => h.id === this.editingHabit.id)
      if (idx > -1) {
        this.habits[idx] = {
          ...this.habits[idx],
          name: this.editForm.name.trim(),
          frequency: this.editForm.frequency,
          customDays: this.editForm.customDays,
          executionTime: this.editForm.executionTime,
          reminder_time: this.editForm.executionTime,
          difficulty: this.editForm.difficulty
        }
        this.$store.commit('setHabits', this.habits)
        uni.setStorageSync('habits', this.habits)
        this.triggerAIPlanUpdate()
        uni.showToast({ title: '已保存', icon: 'success' })
      }
      this.closeEditHabit()
    },
    triggerAIPlanUpdate() {
      // AI更新督促计划 - 发送消息到聊天
      const activeHabits = this.habits.filter(h => !h.paused)
      const pausedCount = this.habits.length - activeHabits.length
      const charId = this.$store.state.aiConfig?.avatarType || 'linxi'
      const aiName = this.$store.state.aiConfig?.name || '林夕'
      const messages = [
        `${aiName}已更新督促计划~ 今天有${activeHabits.length}个任务等着你，一起加油！`,
        `计划已同步！${activeHabits.length}个习惯已就绪${pausedCount > 0 ? `，${pausedCount}个已暂停` : ''}~`,
        `督促计划已更新~ 我会按照新的顺序和时间提醒你哦！`,
        `好的，计划已同步~ 按时完成，我们在环球地图上一起前进！`
      ]
      const msg = messages[Math.floor(Math.random() * messages.length)]
      this.$store.commit('addChatMessage', {
        type: 'ai',
        content: msg,
        time: Date.now()
      })
    },
    closePanel() {
      if (this.editMode) {
        this.saveSort()
      }
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.popup-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
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
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.panel-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.header-btn {
  padding: 8rpx 24rpx;
  background: #6B8E7B;
  border-radius: 24rpx;
}
.header-btn.save {
  background: #4CAF50;
}
.header-btn:active {
  transform: scale(0.95);
}
.btn-text {
  font-size: 26rpx;
  color: #fff;
}
.panel-close {
  font-size: 36rpx;
  color: #999;
  padding: 8rpx;
}
.panel-body {
  flex: 1;
  padding: 24rpx 32rpx;
  max-height: 78vh;
}

/* 批量操作栏 */
.batch-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  margin-bottom: 16rpx;
}
.batch-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.select-all-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.checkbox {
  width: 40rpx;
  height: 40rpx;
  border-radius: 8rpx;
  border: 3rpx solid #D0D0D0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.checkbox.checked {
  background: #6B8E7B;
  border-color: #6B8E7B;
}
.check-icon {
  font-size: 24rpx;
  color: #fff;
}
.select-text {
  font-size: 26rpx;
  color: #666;
}
.selected-count {
  font-size: 24rpx;
  color: #6B8E7B;
}
.batch-actions {
  display: flex;
  gap: 12rpx;
}
.batch-btn {
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}
.batch-btn.start {
  background: #E8F5E9;
}
.batch-btn.start text {
  color: #4CAF50;
}
.batch-btn.pause {
  background: #FFF3E0;
}
.batch-btn.pause text {
  color: #FF9800;
}
.batch-btn.delete {
  background: #FFEBEE;
}
.batch-btn.delete text {
  color: #F44336;
}
.batch-btn:active {
  transform: scale(0.95);
}

/* 排序列表 */
.sort-list {
  margin-bottom: 24rpx;
}
.sort-item {
  display: flex;
  align-items: center;
  padding: 20rpx 16rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
  transition: all 0.2s;
}
.sort-item.editing {
  background: #F0F7F3;
}
.sort-item.selected {
  background: #E8F5E9;
  border: 2rpx solid #6B8E7B;
}
.sort-item.paused {
  opacity: 0.5;
}
.drag-handle {
  width: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
}
.drag-icon {
  font-size: 32rpx;
  color: #999;
}
.checkbox-wrap {
  margin-right: 12rpx;
}
.habit-info {
  flex: 1;
  display: flex;
  align-items: center;
}
.habit-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
}
.habit-icon {
  font-size: 32rpx;
}
.habit-detail {
  flex: 1;
  min-width: 0;
}
.habit-name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.habit-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}
.paused-tag {
  padding: 2rpx 10rpx;
  background: #FFF3E0;
  border-radius: 8rpx;
}
.paused-tag text {
  font-size: 18rpx;
  color: #FF9800;
}
.completed-tag {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  background: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
}
.completed-tag text {
  font-size: 18rpx;
  color: #fff;
}
.habit-meta {
  display: flex;
  align-items: center;
  margin-top: 4rpx;
  flex-wrap: wrap;
}
.meta-item {
  font-size: 22rpx;
  color: #999;
}
.meta-divider {
  font-size: 20rpx;
  color: #E0E0E0;
  margin: 0 8rpx;
}
.sort-btns {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-left: 12rpx;
}
.sort-btn {
  width: 48rpx;
  height: 48rpx;
  border-radius: 12rpx;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sort-btn text {
  font-size: 28rpx;
  color: #6B8E7B;
}
.sort-btn.disabled {
  opacity: 0.3;
}
.sort-btn:active:not(.disabled) {
  background: #E8F5E9;
}

/* 编辑弹窗 */
.edit-modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.edit-modal {
  width: 90%;
  max-width: 640rpx;
  max-height: 80vh;
  background: #fff;
  border-radius: 32rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.edit-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
}
.edit-close {
  font-size: 36rpx;
  color: #999;
  padding: 8rpx;
}
.edit-body {
  flex: 1;
  padding: 24rpx 32rpx;
  max-height: 50vh;
}
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
.freq-options, .diff-options {
  display: flex;
  gap: 12rpx;
}
.freq-option, .diff-option {
  flex: 1;
  height: 72rpx;
  background: #F5F6F7;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  color: #666;
}
.freq-option.active, .diff-option.active {
  background: #6B8E7B;
  color: #fff;
}
.weekday-picker {
  display: flex;
  gap: 12rpx;
}
.weekday-item {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #F5F6F7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  color: #666;
}
.weekday-item.active {
  background: #6B8E7B;
  color: #fff;
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
.form-bottom-space {
  height: 60rpx;
}
.edit-footer {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #F0F0F0;
}
.edit-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.edit-btn.cancel {
  background: #F5F6F7;
}
.edit-btn.cancel text {
  font-size: 30rpx;
  color: #666;
}
.edit-btn.save {
  background: linear-gradient(135deg, #6B8E7B, #8FBC8F);
}
.edit-btn.save text {
  font-size: 30rpx;
  color: #fff;
  font-weight: 600;
}

/* 提示卡片 */
.tip-card {
  display: flex;
  gap: 12rpx;
  background: #FFF8E1;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 24rpx;
}
.tip-icon {
  font-size: 32rpx;
  flex-shrink: 0;
}
.tip-content {
  flex: 1;
}
.tip-title {
  font-size: 26rpx;
  color: #8B6914;
  font-weight: 600;
  display: block;
  margin-bottom: 4rpx;
}
.tip-desc {
  font-size: 22rpx;
  color: #B8941A;
  line-height: 1.5;
}

.form-bottom-space {
  height: 120rpx;
}
</style>
