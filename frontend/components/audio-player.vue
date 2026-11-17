<template>
  <view class="audio-player" :class="{ playing: isPlaying }">
    <!-- 播放控制 -->
    <view class="player-main">
      <view class="play-btn" @click="togglePlay" :style="{ background: themeColor }">
        <text class="play-icon">{{ isPlaying ? '⏸' : '▶' }}</text>
      </view>
      <view class="player-info">
        <text class="audio-title">{{ title || '未选择音频' }}</text>
        <text class="audio-meta">{{ categoryLabel }} · {{ durationMinutes }}分钟</text>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="progress-section">
      <view class="progress-bar" @click="seekTo">
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: progressPercent + '%', background: themeColor }"></view>
        </view>
        <view class="progress-thumb" :style="{ left: progressPercent + '%', background: themeColor }"></view>
      </view>
      <view class="time-display">
        <text class="time-current">{{ formatTime(currentTime) }}</text>
        <text class="time-total">{{ formatTime(totalTime) }}</text>
      </view>
    </view>

    <!-- 倍速控制 -->
    <view class="speed-control">
      <view
        v-for="spd in speedOptions"
        :key="spd"
        class="speed-item"
        :class="{ active: currentSpeed === spd }"
        @click="setSpeed(spd)"
      >
        <text>{{ spd }}x</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'AudioPlayer',
  props: {
    title: { type: String, default: '' },
    category: { type: String, default: 'mindfulness' },
    durationMinutes: { type: Number, default: 10 },
    audioUrl: { type: String, default: '' },
    themeColor: { type: String, default: '#6B8E7B' },
    autoPlay: { type: Boolean, default: false }
  },
  data() {
    return {
      isPlaying: false,
      currentTime: 0,
      totalTime: 0,
      currentSpeed: 1,
      speedOptions: [0.75, 1, 1.25, 1.5],
      playTimer: null,
      audioCtx: null
    }
  },
  computed: {
    progressPercent() {
      if (this.totalTime === 0) return 0
      return Math.min(100, (this.currentTime / this.totalTime) * 100)
    },
    categoryLabel() {
      const labels = {
        breathing: '呼吸放松',
        body_scan: '身体扫描',
        mindfulness: '正念冥想',
        anxiety_relief: '焦虑缓解',
        sleep_aid: '助眠安神'
      }
      return labels[this.category] || '正念练习'
    }
  },
  watch: {
    durationMinutes: {
      handler(val) {
        this.totalTime = val * 60
      },
      immediate: true
    },
    autoPlay(val) {
      if (val) this.play()
    }
  },
  mounted() {
    this.totalTime = this.durationMinutes * 60
  },
  beforeDestroy() {
    this.stopPlay()
  },
  beforeUnmount() {
    this.stopPlay()
  },
  methods: {
    togglePlay() {
      if (this.isPlaying) {
        this.pause()
      } else {
        this.play()
      }
    },
    play() {
      if (this.currentTime >= this.totalTime) {
        this.currentTime = 0
      }
      this.isPlaying = true

      // 如果有真实音频URL，使用uni audio context
      if (this.audioUrl) {
        this._playRealAudio()
      } else {
        // Mock模式：使用计时器模拟播放
        this._startMockPlay()
      }

      this.$emit('play', { currentTime: this.currentTime, totalTime: this.totalTime })
    },
    _startMockPlay() {
      if (this.playTimer) clearInterval(this.playTimer)
      this.playTimer = setInterval(() => {
        this.currentTime += this.currentSpeed
        if (this.currentTime >= this.totalTime) {
          this.currentTime = this.totalTime
          this._onPlayEnd()
        }
        this.$emit('timeupdate', { currentTime: this.currentTime, totalTime: this.totalTime })
      }, 1000)
    },
    _playRealAudio() {
      if (!this.audioCtx) {
        this.audioCtx = uni.createInnerAudioContext()
        this.audioCtx.src = this.audioUrl
        this.audioCtx.onTimeUpdate(() => {
          this.currentTime = Math.floor(this.audioCtx.currentTime)
          this.totalTime = Math.floor(this.audioCtx.duration || this.durationMinutes * 60)
          this.$emit('timeupdate', { currentTime: this.currentTime, totalTime: this.totalTime })
        })
        this.audioCtx.onEnded(() => {
          this._onPlayEnd()
        })
        this.audioCtx.onError((err) => {
          console.error('音频播放错误', err)
          // 降级为Mock播放
          this._startMockPlay()
        })
      }
      this.audioCtx.playbackRate = this.currentSpeed
      this.audioCtx.play()
    },
    pause() {
      this.isPlaying = false
      if (this.playTimer) {
        clearInterval(this.playTimer)
        this.playTimer = null
      }
      if (this.audioCtx) {
        this.audioCtx.pause()
      }
      this.$emit('pause', { currentTime: this.currentTime })
    },
    stopPlay() {
      this.isPlaying = false
      if (this.playTimer) {
        clearInterval(this.playTimer)
        this.playTimer = null
      }
      if (this.audioCtx) {
        this.audioCtx.stop()
        this.audioCtx.destroy()
        this.audioCtx = null
      }
      this.currentTime = 0
    },
    _onPlayEnd() {
      this.isPlaying = false
      if (this.playTimer) {
        clearInterval(this.playTimer)
        this.playTimer = null
      }
      this.$emit('ended', { completed: true, duration: this.durationMinutes })
    },
    seekTo(e) {
      // 简单的点击进度条跳转
      const totalSeconds = this.totalTime
      // 在实际场景中，需要获取触摸位置计算百分比
      // 这里简化处理，暂不实现精确跳转
    },
    setSpeed(spd) {
      this.currentSpeed = spd
      if (this.audioCtx) {
        this.audioCtx.playbackRate = spd
      }
      this.$emit('speedchange', spd)
    },
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    }
  }
}
</script>

<style lang="scss" scoped>
.audio-player {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.player-main {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.play-btn {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  flex-shrink: 0;
  box-shadow: 0 6rpx 20rpx rgba(107, 142, 123, 0.3);
  transition: transform 0.2s ease;
}

.play-btn:active {
  transform: scale(0.92);
}

.play-icon {
  font-size: 40rpx;
  color: #fff;
  margin-left: 4rpx;
}

.player-info {
  flex: 1;
  overflow: hidden;
}

.audio-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 6rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-meta {
  font-size: 24rpx;
  color: #999;
}

.progress-section {
  margin-bottom: 20rpx;
}

.progress-bar {
  position: relative;
  height: 48rpx;
  display: flex;
  align-items: center;
}

.progress-track {
  width: 100%;
  height: 6rpx;
  background: #E8E8E8;
  border-radius: 3rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3rpx;
  transition: width 0.3s linear;
}

.progress-thumb {
  position: absolute;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  transform: translateX(-50%);
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  transition: left 0.3s linear;
}

.time-display {
  display: flex;
  justify-content: space-between;
  margin-top: 8rpx;
}

.time-current,
.time-total {
  font-size: 22rpx;
  color: #999;
  font-family: monospace;
}

.speed-control {
  display: flex;
  gap: 16rpx;
  justify-content: flex-end;
}

.speed-item {
  padding: 6rpx 20rpx;
  border-radius: 20rpx;
  background: #F5F5F5;
}

.speed-item.active {
  background: rgba(107, 142, 123, 0.15);
}

.speed-item text {
  font-size: 22rpx;
  color: #666;
}

.speed-item.active text {
  color: #6B8E7B;
  font-weight: 600;
}
</style>
