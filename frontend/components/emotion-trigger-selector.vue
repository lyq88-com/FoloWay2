<template>
  <view class="trigger-selector">
    <view class="selector-header">
      <text class="header-label">触发因素</text>
      <text class="header-count">已选 {{ selectedTags.length }} 个</text>
    </view>

    <!-- 预设标签 -->
    <view class="tag-grid">
      <view
        v-for="tag in displayTags"
        :key="tag"
        class="tag-chip"
        :class="{ selected: isSelected(tag) }"
        @click="toggleTag(tag)"
      >
        <text class="chip-icon">{{ getTagIcon(tag) }}</text>
        <text class="chip-text">{{ tag }}</text>
      </view>
    </view>

    <!-- 自定义输入 -->
    <view class="custom-input-wrap">
      <input
        v-model="customInput"
        class="custom-input"
        placeholder="或自定义标签..."
        maxlength="10"
        confirm-type="done"
        @confirm="addCustomTag"
      />
      <view class="add-btn" @click="addCustomTag">
        <text class="add-btn-text">添加</text>
      </view>
    </view>

    <!-- 已选标签展示 -->
    <view class="selected-wrap" v-if="selectedTags.length > 0">
      <text class="selected-title">本次选择：</text>
      <view class="selected-tags">
        <view
          v-for="tag in selectedTags"
          :key="tag"
          class="selected-chip"
          @click="toggleTag(tag)"
        >
          <text class="selected-chip-text">{{ tag }}</text>
          <text class="selected-chip-x">×</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'EmotionTriggerSelector',
  props: {
    // 已选标签数组
    value: { type: Array, default: () => [] },
    // 用户历史使用过的标签（从 Vuex 加载）
    historyTags: { type: Array, default: () => [] }
  },
  data() {
    return {
      customInput: '',
      presetTags: [
        { name: '工作', icon: '💼' },
        { name: '学习', icon: '📚' },
        { name: '家庭', icon: '🏠' },
        { name: '感情', icon: '❤️' },
        { name: '健康', icon: '🏃' },
        { name: '财务', icon: '💰' },
        { name: '社交', icon: '👥' },
        { name: '其他', icon: '✨' }
      ]
    }
  },
  computed: {
    selectedTags() {
      return this.value || []
    },
    // 显示标签 = 预设 + 历史中不在预设的（最多5个额外）
    displayTags() {
      const presetNames = this.presetTags.map(t => t.name)
      const extraFromHistory = (this.historyTags || [])
        .filter(t => !presetNames.includes(t))
        .slice(0, 5)
      return [
        ...this.presetTags.map(t => t.name),
        ...extraFromHistory
      ]
    }
  },
  methods: {
    isSelected(tag) {
      return this.selectedTags.includes(tag)
    },
    getTagIcon(tag) {
      const found = this.presetTags.find(t => t.name === tag)
      return found ? found.icon : '🏷️'
    },
    toggleTag(tag) {
      const current = [...this.selectedTags]
      const idx = current.indexOf(tag)
      if (idx >= 0) {
        current.splice(idx, 1)
      } else {
        if (current.length >= 5) {
          uni.showToast({ title: '最多选择5个标签', icon: 'none' })
          return
        }
        current.push(tag)
      }
      this.$emit('input', current)
      this.$emit('change', current)
    },
    addCustomTag() {
      const tag = this.customInput.trim()
      if (!tag) return
      if (tag.length > 10) {
        uni.showToast({ title: '标签最多10个字', icon: 'none' })
        return
      }
      if (this.selectedTags.includes(tag)) {
        uni.showToast({ title: '标签已选择', icon: 'none' })
        return
      }
      if (this.selectedTags.length >= 5) {
        uni.showToast({ title: '最多选择5个标签', icon: 'none' })
        return
      }
      const current = [...this.selectedTags, tag]
      this.$emit('input', current)
      this.$emit('change', current)
      this.$emit('custom-add', tag)  // 通知父组件记录到 Vuex
      this.customInput = ''
    }
  }
}
</script>

<style lang="scss" scoped>
.trigger-selector {
  padding: 8rpx 0;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}
.header-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.header-count {
  font-size: 22rpx;
  color: #999;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 20rpx;
}
.tag-chip {
  display: flex;
  align-items: center;
  padding: 12rpx 24rpx;
  background: #f5f5f5;
  border-radius: 32rpx;
  border: 2rpx solid transparent;
  transition: all 0.25s ease;
}
.tag-chip.selected {
  background: rgba(107, 142, 123, 0.12);
  border-color: #6B8E7B;
}
.chip-icon {
  font-size: 26rpx;
  margin-right: 8rpx;
}
.chip-text {
  font-size: 26rpx;
  color: #555;
}
.tag-chip.selected .chip-text {
  color: #6B8E7B;
  font-weight: 600;
}

.custom-input-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.custom-input {
  flex: 1;
  height: 64rpx;
  background: #f5f5f5;
  border-radius: 32rpx;
  padding: 0 24rpx;
  font-size: 26rpx;
  color: #333;
  box-sizing: border-box;
}
.add-btn {
  padding: 12rpx 28rpx;
  background: rgba(107, 142, 123, 0.1);
  border-radius: 32rpx;
  border: 2rpx solid rgba(107, 142, 123, 0.3);
}
.add-btn-text {
  font-size: 26rpx;
  color: #6B8E7B;
  font-weight: 600;
}

.selected-wrap {
  background: rgba(107, 142, 123, 0.04);
  border-radius: 16rpx;
  padding: 16rpx 20rpx;
}
.selected-title {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 12rpx;
}
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}
.selected-chip {
  display: flex;
  align-items: center;
  padding: 8rpx 20rpx;
  background: #6B8E7B;
  border-radius: 24rpx;
}
.selected-chip-text {
  font-size: 24rpx;
  color: #fff;
  margin-right: 8rpx;
}
.selected-chip-x {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 700;
}
</style>
