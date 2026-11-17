<template>
  <view class="sp-mask" v-if="visible" @click="$emit('close')">
    <view class="sp-panel" @click.stop>
      <view class="sp-header">
        <text class="sp-title">😁 表情包</text>
        <view class="sp-upload" @click="uploadSticker">
          <text>＋ 上传</text>
        </view>
        <text class="sp-close" @click="$emit('close')">✕</text>
      </view>
      <scroll-view scroll-y class="sp-body">
        <!-- 自定义表情包 -->
        <view v-if="customStickers.length > 0" class="sp-group">
          <text class="sp-group-title">我的表情包（长按删除）</text>
          <view class="emoji-grid">
            <view
              v-for="(s, idx) in customStickers"
              :key="'c' + idx"
              class="sticker-cell"
              @click="$emit('send-sticker', { type: 'image', imageUrl: s })"
              @longpress="removeSticker(idx)"
            >
              <image class="sticker-img" :src="s" mode="aspectFill" />
            </view>
          </view>
        </view>
        <!-- 内置表情 -->
        <view class="sp-group">
          <text class="sp-group-title">经典表情</text>
          <view class="emoji-grid">
            <view
              v-for="e in emojis"
              :key="e"
              class="emoji-cell"
              @click="$emit('send-sticker', { type: 'emoji', content: e })"
            >
              <text class="emoji-text">{{ e }}</text>
            </view>
          </view>
        </view>
        <view class="sp-bottom-space"></view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
/**
 * 表情包面板：内置经典表情 + 用户上传自定义表情包
 * 上传的表情以 dataURL 形式保存在本地，可长期使用
 */
const STICKER_KEY = 'custom_stickers'

export default {
  props: {
    visible: { type: Boolean, default: false }
  },
  data() {
    return {
      customStickers: [],
      emojis: [
        '😂', '🥰', '😭', '😡', '🤔', '😎', '🥳', '😴',
        '🙈', '👍', '👎', '🙏', '💪', '🤝', '✌️', '🤞',
        '💕', '💔', '🌸', '🌈', '⭐', '🔥', '🎉', '🎁',
        '🐱', '🐶', '🐰', '🐼', '🦊', '🍩', '🍰', '🧋'
      ]
    }
  },
  watch: {
    visible(v) {
      if (v) this.loadStickers()
    }
  },
  methods: {
    loadStickers() {
      try {
        this.customStickers = uni.getStorageSync(STICKER_KEY) || []
      } catch (e) {
        this.customStickers = []
      }
    },
    saveStickers() {
      try {
        uni.setStorageSync(STICKER_KEY, this.customStickers)
      } catch (e) { /* 静默 */ }
    },
    uploadSticker() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (!path) return
          // H5 下转为 dataURL 持久保存
          // #ifdef H5
          if (typeof window !== 'undefined' && window.FileReader && /^blob:|^file:/.test(path)) {
            const xhr = new XMLHttpRequest()
            xhr.open('GET', path)
            xhr.responseType = 'blob'
            xhr.onload = () => {
              const reader = new FileReader()
              reader.onload = () => {
                this.customStickers.push(reader.result)
                this.saveStickers()
                uni.showToast({ title: '表情已添加', icon: 'success' })
              }
              reader.readAsDataURL(xhr.response)
            }
            xhr.onerror = () => {
              this.customStickers.push(path)
              this.saveStickers()
            }
            xhr.send()
            return
          }
          // #endif
          this.customStickers.push(path)
          this.saveStickers()
          uni.showToast({ title: '表情已添加', icon: 'success' })
        }
      })
    },
    removeSticker(idx) {
      uni.showModal({
        title: '删除表情',
        content: '确定删除这个自定义表情吗？',
        success: (r) => {
          if (r.confirm) {
            this.customStickers.splice(idx, 1)
            this.saveStickers()
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.sp-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  display: flex;
  align-items: flex-end;
}
.sp-panel {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  max-height: 56vh;
  display: flex;
  flex-direction: column;
}
.sp-header {
  display: flex;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.sp-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #333;
  flex: 1;
}
.sp-upload {
  padding: 10rpx 26rpx;
  background: #E8F4EC;
  border-radius: 999rpx;
  margin-right: 20rpx;
}
.sp-upload text { font-size: 24rpx; color: #6B8E7B; }
.sp-close {
  font-size: 34rpx;
  color: #999;
}
.sp-body {
  flex: 1;
  padding: 20rpx 32rpx 0;
  box-sizing: border-box;
}
.sp-group { margin-bottom: 24rpx; }
.sp-group-title {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 16rpx;
}
.emoji-grid {
  display: flex;
  flex-wrap: wrap;
}
.emoji-cell {
  width: 20%;
  height: 110rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.emoji-cell:active { background: #F0F7F3; border-radius: 16rpx; }
.emoji-text { font-size: 52rpx; }
.sticker-cell {
  width: 25%;
  height: 150rpx;
  padding: 10rpx;
  box-sizing: border-box;
}
.sticker-cell:active { opacity: 0.7; }
.sticker-img {
  width: 100%;
  height: 100%;
  border-radius: 16rpx;
}
.sp-bottom-space { height: calc(env(safe-area-inset-bottom) + 20rpx); }
</style>
