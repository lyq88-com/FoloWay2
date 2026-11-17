<template>
  <view class="xt-page xt-s32">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">时光胶囊</view>
          <view class="page-sub">写给未来，也写给她</view>
        </view>
        <view class="icon-btn" @click="openCreate"><xt-icon name="i-plus" /></view>
      </view>

      <view
        v-for="cap in capsules"
        :key="cap.id"
        class="letter"
        :style="capsuleStyle(cap)"
        @click="openCapsule(cap)"
      >
        <view style="font-size:7px;letter-spacing:1.6px;color:rgba(255,255,255,.55)">{{ capsuleStatusText(cap) }}</view>
        <view style="margin-top:8px;font-size:14px;font-weight:900">{{ cap.title || '未命名胶囊' }}</view>
        <view class="ln" style="margin-top:6px;color:rgba(255,255,255,.72)">
          {{ (cap.isOpened || cap.isOpenable) ? '“' + cap.content + '”' : '“封存中，到期后再来看”' }}
        </view>
        <view style="margin-top:10px;display:flex;align-items:center;justify-content:space-between;font-size:7.5px;color:rgba(255,255,255,.5)">
          <text>封存于 {{ prettyDate(cap.createdAt) }}</text>
          <text>{{ cap.openAt ? prettyDate(cap.openAt) + ' 开启' : '不设期限' }}</text>
        </view>
      </view>

      <view v-if="capsules.length === 0" class="letter" style="background:linear-gradient(145deg,#3D5449,#23332C);color:#fff;box-shadow:0 18px 34px -24px rgba(36,64,47,.8)">
        <view style="font-size:7px;letter-spacing:1.6px;color:rgba(255,255,255,.55)">SEALED · 暂无胶囊</view>
        <view style="margin-top:8px;font-size:14px;font-weight:900">写给未来的第一句话</view>
        <view class="ln" style="margin-top:6px;color:rgba(255,255,255,.72)">“把此刻的心情封起来，交给未来的自己。”</view>
      </view>

      <view class="cal-sec" style="margin-top:13px">
        <text class="t">我的胶囊</text>
        <text class="s">{{ allNotes.length }} 个</text>
      </view>

      <view class="chips" style="margin:0 0 10px">
        <text
          v-for="tab in timeTabs"
          :key="tab.key"
          class="chip"
          :class="{ on: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</text>
      </view>

      <view v-if="filteredNotes.length > 0">
        <view
          v-for="(note, index) in filteredNotes"
          :key="note.id || index"
          class="mem-item"
          @click="exportNote(note)"
        >
          <view class="mi" :class="index % 2 ? 'tint-green' : 'tint-sand'">
            <xt-icon :name="index % 2 ? 'i-check' : 'i-clock'" />
          </view>
          <view class="tx">
            <view class="t">{{ getHabitName(note.habitId) }}</view>
            <view class="m">“{{ note.content }}”</view>
            <view class="d">{{ formatDate(note.date) }} {{ formatTime(note.date) }}</view>
          </view>
          <text class="v" style="font-size:8px;color:var(--v7-green)" @click.stop="shareNote(note)">分享</text>
        </view>
      </view>
      <view v-else class="mem-item">
        <view class="mi tint-sand"><xt-icon name="i-clock" /></view>
        <view class="tx">
          <view class="t">暂无{{ getTabLabel() }}的时光记录</view>
          <view class="m">完成习惯打卡时记录心情，留下珍贵回忆</view>
        </view>
      </view>

      <view class="auth-btn" style="margin-top:12px;background:#FFFDFA;color:var(--v7-green);box-shadow:0 0 0 1px rgba(30,42,36,.10)" @click="openCreate">封一颗新胶囊</view>
    </view>

    <view v-if="showCreate" class="popup-mask" @click="closeCreate">
      <view class="export-modal" @click.stop>
        <view class="export-handle"></view>
        <view class="export-header">
          <text class="export-title">封一颗新胶囊</text>
          <view class="export-close" @click="closeCreate">
            <text>✕</text>
          </view>
        </view>
        <view class="capsule-form">
          <input
            v-model="formTitle"
            class="capsule-input"
            maxlength="40"
            placeholder="标题（可选）"
          />
          <textarea
            v-model="formContent"
            class="capsule-textarea"
            maxlength="2000"
            placeholder="写给未来，也写给她..."
          />
          <picker mode="date" :value="formDate" :start="todayStr" @change="onDateChange">
            <view class="capsule-date">
              <text>开启日期：{{ formDate || '不设期限（随时可开）' }}</text>
              <text class="capsule-date-pick">选择</text>
            </view>
          </picker>
        </view>
        <view class="export-actions">
          <view class="export-btn" @click="submitCapsule">
            <text>封存</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="showExportModal" class="popup-mask" @click="closeExportModal">
      <view class="export-modal" @click.stop>
        <view class="export-handle"></view>
        <view class="export-header">
          <text class="export-title">导出时光卡片</text>
          <view class="export-close" @click="closeExportModal">
            <text>✕</text>
          </view>
        </view>
        <view class="export-preview">
          <canvas
            canvas-id="noteCanvas"
            class="note-canvas"
            :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
          ></canvas>
        </view>
        <view class="export-actions">
          <view class="export-btn" @click="saveToAlbum">
            <text>保存到相册</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      activeTab: 'all',
      timeTabs: [
        { key: 'all', label: '全部' },
        { key: 'today', label: '今天' },
        { key: 'week', label: '本周' },
        { key: 'month', label: '本月' },
        { key: 'year', label: '本年' }
      ],
      allNotes: [],
      habits: [],
      capsules: [],
      showCreate: false,
      submitting: false,
      formTitle: '',
      formContent: '',
      formDate: '',
      showExportModal: false,
      currentNote: null,
      canvasWidth: 300,
      canvasHeight: 400
    }
  },
  computed: {
    todayStr() {
      const d = new Date()
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    },
    filteredNotes() {
      if (this.activeTab === 'all') return this.allNotes

      const now = new Date()
      let filtered = []

      switch (this.activeTab) {
        case 'today':
          filtered = this.allNotes.filter(n => {
            const date = new Date(n.date)
            return date.toDateString() === now.toDateString()
          })
          break
        case 'week':
          const weekStart = new Date(now)
          weekStart.setDate(now.getDate() - now.getDay())
          filtered = this.allNotes.filter(n => n.date >= weekStart.getTime())
          break
        case 'month':
          const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
          filtered = this.allNotes.filter(n => n.date >= monthStart.getTime())
          break
        case 'year':
          const yearStart = new Date(now.getFullYear(), 0, 1)
          filtered = this.allNotes.filter(n => n.date >= yearStart.getTime())
          break
      }
      return filtered.sort((a, b) => b.date - a.date)
    }
  },
  onShow() {
    this.loadData()
    this.loadCapsules()
  },
  methods: {
    // ↓↓↓ 时光胶囊（云端） ↓↓↓
    loadCapsules() {
      const token = (this.$store && this.$store.state && this.$store.state.token) || ''
      if (!token) {
        this.capsules = []
        return
      }
      playSync.fetchCapsules().then(res => {
        const body = res.body || {}
        if (res.ok && body.code === 200) {
          this.capsules = (body.data && body.data.list) || []
        }
      })
    },
    openCreate() {
      const token = (this.$store && this.$store.state && this.$store.state.token) || ''
      if (!token) {
        uni.showToast({ title: '登录后才能封存胶囊', icon: 'none' })
        return
      }
      this.formTitle = ''
      this.formContent = ''
      this.formDate = ''
      this.showCreate = true
    },
    closeCreate() {
      this.showCreate = false
    },
    onDateChange(e) {
      this.formDate = (e.detail && e.detail.value) || ''
    },
    async submitCapsule() {
      if (this.submitting) return
      const content = (this.formContent || '').trim()
      if (!content) {
        uni.showToast({ title: '写点什么再封存吧', icon: 'none' })
        return
      }
      this.submitting = true
      uni.showLoading({ title: '封存中...', mask: true })
      const res = await playSync.createCapsule({
        title: (this.formTitle || '').trim(),
        content,
        openAt: this.formDate || null
      })
      uni.hideLoading()
      this.submitting = false
      const body = res.body || {}
      if (res.ok && body.code === 200) {
        this.capsules.unshift(body.data)
        this.showCreate = false
        uni.showToast({ title: '已封存', icon: 'success' })
      } else {
        uni.showToast({ title: body.message || '封存失败，请稍后重试', icon: 'none' })
      }
    },
    capsuleStatusText(cap) {
      if (cap.isOpened) return 'OPENED · 已开启'
      if (!cap.openAt) return 'SEALED · 随时可开'
      const days = this.remainDays(cap)
      return days > 0 ? `SEALED · 还有 ${days} 天` : 'SEALED · 已到期，点击开启'
    },
    capsuleStyle(cap) {
      if (cap.isOpened) {
        return 'background:linear-gradient(145deg,#6B8E7B,#3D5449);color:#fff;box-shadow:0 18px 34px -24px rgba(36,64,47,.8)'
      }
      return 'background:linear-gradient(145deg,#3D5449,#23332C);color:#fff;box-shadow:0 18px 34px -24px rgba(36,64,47,.8)'
    },
    remainDays(cap) {
      if (!cap.openAt) return 0
      const target = new Date(String(cap.openAt).replace(/-/g, '/')).getTime()
      return Math.max(0, Math.ceil((target - Date.now()) / 86400000))
    },
    prettyDate(str) {
      if (!str) return ''
      return String(str).slice(0, 10).replace(/-/g, '.')
    },
    openCapsule(cap) {
      if (!cap || cap.isOpened) return
      if (!cap.isOpenable) {
        uni.showToast({ title: `还有 ${this.remainDays(cap)} 天才能开启`, icon: 'none' })
        return
      }
      uni.showModal({
        title: '开启胶囊',
        content: '确定现在打开这颗胶囊吗？',
        confirmText: '打开',
        success: async (r) => {
          if (!r.confirm) return
          const res = await playSync.openCapsule(cap.id)
          const body = res.body || {}
          if (res.ok && body.code === 200) {
            const idx = this.capsules.findIndex(c => c.id === cap.id)
            if (idx !== -1) this.capsules.splice(idx, 1, body.data)
            uni.showToast({ title: '已开启', icon: 'success' })
          } else {
            uni.showToast({ title: body.message || '开启失败', icon: 'none' })
          }
        }
      })
    },
    // ↑↑↑ 时光胶囊 ↑↑↑
    loadData() {
      try {
        const notes = uni.getStorageSync('habit_notes') || {}
        const habits = uni.getStorageSync('habits') || []
        this.habits = habits

        this.allNotes = []
        Object.keys(notes).forEach(habitId => {
          notes[habitId].forEach(note => {
            this.allNotes.push({ ...note, habitId })
          })
        })
        this.allNotes.sort((a, b) => b.date - a.date)
      } catch (e) {
        console.error('加载时光胶囊数据失败', e)
        this.allNotes = []
      }
    },
    getHabitName(habitId) {
      const habit = this.habits.find(h => h.id == habitId)
      return habit ? habit.name : '未知习惯'
    },
    formatDate(timestamp) {
      const date = new Date(timestamp)
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
    },
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    },
    getTabLabel() {
      const tab = this.timeTabs.find(t => t.key === this.activeTab)
      return tab ? tab.label : ''
    },
    goBack() {
      uni.navigateBack()
    },
    /**
     * ↓↓↓ 改造（2026-10-27）：原来只有一句「分享功能开发中」 ↓↓↓
     * 分享走两条路：
     *   1) 浏览器原生分享（navigator.share，手机 Chrome/Safari 支持）→ 直接调起系统分享面板
     *   2) 不支持时降级为「复制文案到剪贴板」，提示用户自行粘贴
     * 小程序/App 端没有 navigator.share，会直接走剪贴板，不会报错。
     */
    async shareNote(note) {
      if (!note) return
      const text = this.buildShareText(note)

      try {
        if (typeof navigator !== 'undefined' && navigator.share) {
          await navigator.share({ title: '循途 · 时光胶囊', text })
          return
        }
      } catch (e) {
        // 用户主动取消分享（AbortError）不该再提示，直接结束
        if (e && (e.name === 'AbortError' || e.name === 'NotAllowedError')) return
        // 其它失败 → 继续走剪贴板兜底
      }

      uni.setClipboardData({
        data: text,
        success: () => {
          uni.showToast({ title: '内容已复制，去粘贴分享吧', icon: 'none', duration: 2000 })
        },
        fail: () => {
          uni.showToast({ title: '分享失败，请稍后再试', icon: 'none' })
        }
      })
    },
    /** 拼分享文案 */
    buildShareText(note) {
      const d = note.date ? new Date(note.date) : new Date()
      const dateStr = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${this.formatTime(note.date)}`
      const habit = this.getHabitName(note.habitId)
      const lines = [
        '【循途 · 时光胶囊】',
        dateStr + (habit && habit !== '未知习惯' ? ` · ${habit}` : ''),
        '',
        note.content || '',
        '',
        '—— 来自循途，陪你记录每一次坚持'
      ]
      return lines.filter(l => l !== null && l !== undefined).join('\n')
    },
    async exportNote(note) {
      this.currentNote = note
      this.showExportModal = true

      await this.$nextTick()
      this.drawNoteCanvas(note)
    },
    drawNoteCanvas(note) {
      const ctx = uni.createCanvasContext('noteCanvas')

      const w = this.canvasWidth
      const h = this.canvasHeight

      ctx.setFillStyle('#FFFFFF')
      ctx.fillRect(0, 0, w, h)

      ctx.setStrokeStyle('#E8E8E8')
      ctx.setLineWidth(2)
      ctx.strokeRect(0, 0, w, h)

      const gradient = ctx.createLinearGradient(0, 0, w, 0)
      gradient.addColorStop(0, '#6B8E7B')
      gradient.addColorStop(1, '#8FBC8F')
      ctx.setFillStyle(gradient)
      ctx.fillRect(0, 0, w, 80)

      ctx.setFillStyle('#FFFFFF')
      ctx.setFontSize(20)
      ctx.setTextAlign('center')
      ctx.fillText('时光胶囊', w / 2, 35)

      ctx.setFillStyle('#FFFFFF')
      ctx.setFontSize(14)
      ctx.fillText(this.formatDate(note.date), w / 2, 60)

      ctx.setFillStyle('#333333')
      ctx.setFontSize(14)
      ctx.setTextAlign('left')
      ctx.fillText(`习惯：${this.getHabitName(note.habitId)}`, 20, 110)

      ctx.setFillStyle('#666666')
      ctx.setFontSize(12)
      ctx.fillText(`时间：${this.formatTime(note.date)}`, 20, 135)

      ctx.setFillStyle('#333333')
      ctx.setFontSize(16)
      ctx.setTextAlign('left')

      const content = note.content
      const lineHeight = 28
      const maxWidth = w - 40
      const words = content.split('')
      let line = ''
      let y = 170

      for (let i = 0; i < words.length; i++) {
        const testLine = line + words[i]
        const metrics = ctx.measureText(testLine)
        const testWidth = metrics.width

        if (testWidth > maxWidth && i > 0) {
          ctx.fillText(line, 20, y)
          line = words[i]
          y += lineHeight
        } else {
          line = testLine
        }
      }
      ctx.fillText(line, 20, y)

      ctx.setFillStyle('#E8E8E8')
      ctx.fillRect(20, h - 50, w - 40, 1)

      ctx.setFillStyle('#999999')
      ctx.setFontSize(12)
      ctx.setTextAlign('center')
      ctx.fillText('循途 · 记录每一天', w / 2, h - 25)

      ctx.draw()
    },
    saveToAlbum() {
      uni.canvasToTempFilePath({
        canvasId: 'noteCanvas',
        success: (res) => {
          uni.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success: () => {
              uni.showToast({ title: '保存成功', icon: 'success' })
              this.closeExportModal()
            },
            fail: () => {
              uni.showToast({ title: '保存失败，请授权相册', icon: 'none' })
            }
          })
        },
        fail: () => {
          uni.showToast({ title: '生成图片失败', icon: 'none' })
        }
      })
    },
    closeExportModal() {
      this.showExportModal = false
      this.currentNote = null
    }
  }
}
</script>

<style lang="scss" scoped>
/* 导出弹层：设计稿未覆盖，沿用原有交互样式 */
.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  padding: 0 40rpx;
  box-sizing: border-box;
  background: rgba(31, 42, 37, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}

.export-modal {
  width: 100%;
  max-width: 680rpx;
  overflow: hidden;
  background: var(--v7-card);
  border-radius: 32rpx;
}

.export-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 18rpx auto 0;
  border-radius: 999rpx;
  background: rgba(46, 86, 67, 0.14);
}

.export-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx 20rpx;
}

.export-title {
  font-size: 31rpx;
  font-weight: 700;
  color: var(--v7-green);
}

.export-close {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(46, 86, 67, 0.06);
}

.export-close text {
  font-size: 26rpx;
  color: rgba(60, 82, 72, 0.5);
}

/* 封存胶囊表单 */
.capsule-form {
  padding: 4rpx 32rpx 0;
}

.capsule-input {
  width: 100%;
  height: 84rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  background: rgba(46, 86, 67, 0.06);
  font-size: 28rpx;
  color: var(--v7-green);
}

.capsule-textarea {
  width: 100%;
  height: 220rpx;
  margin-top: 16rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  background: rgba(46, 86, 67, 0.06);
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--v7-green);
}

.capsule-date {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
  padding: 24rpx;
  border-radius: 20rpx;
  background: rgba(46, 86, 67, 0.04);
  font-size: 26rpx;
  color: rgba(60, 82, 72, 0.75);
}

.capsule-date-pick {
  color: var(--v7-green);
  font-weight: 600;
}

.export-preview {
  padding: 8rpx 32rpx 24rpx;
  display: flex;
  justify-content: center;
}

.note-canvas {
  border-radius: 16rpx;
  box-shadow: 0 10rpx 26rpx rgba(46, 86, 67, 0.12);
}

.export-actions {
  padding: 8rpx 32rpx 34rpx;
}

.export-btn {
  padding: 26rpx;
  border-radius: 999rpx;
  text-align: center;
  background: var(--v7-green);
  box-shadow: 0 10rpx 22rpx rgba(46, 86, 67, 0.22);
}

.export-btn text {
  font-size: 28rpx;
  font-weight: 600;
  color: #F8F3E7;
}
</style>
