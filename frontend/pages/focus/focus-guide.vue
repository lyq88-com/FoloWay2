<template>
  <view class="xt-page xt-s48">
    <view class="body">
      <view class="chat-head" style="padding: 2px 2px 6px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">一起专注</view>
          <view class="chat-st">第 {{ current.step_index }} / {{ steps.length }} 步 · {{ mode === 'simple' ? '简单模式' : '心流模式' }}</view>
        </view>
        <text class="tick">{{ timerText }}</text>
      </view>

      <view class="focus-wrap" style="padding-top: 6px">
        <view class="ring">
          <view class="in">
            <view class="t">{{ current.est_minutes }}</view>
            <view class="k">分钟</view>
          </view>
        </view>
        <view class="focus-task">
          <view class="n">{{ current.content }}</view>
          <view class="m">做完就可以休息，不用做下一件</view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 14px">
        <text class="t">她要怎么陪你</text>
        <text class="s">可随时改</text>
      </view>
      <view class="seg">
        <view class="sg" :class="{ on: mode === 'simple' }" @click="switchMode('simple')">简单模式</view>
        <view class="sg" :class="{ on: mode !== 'simple' }" @click="switchMode('flow')">心流模式</view>
      </view>

      <view class="mem-item" style="align-items: flex-start">
        <view class="mi tint-green"><xt-icon name="i-focus" /></view>
        <view class="tx">
          <view class="t">{{ current.est_minutes }} 分钟后，我们会一起停下来</view>
          <view class="m">她会说一句“辛苦了”，然后提醒你喝水。中途退出不会责怪你。</view>
        </view>
      </view>
      <view class="mem-item" style="align-items: flex-start">
        <view class="mi tint-peach"><xt-icon name="i-heart" /></view>
        <view class="tx">
          <view class="t">{{ cheer }}</view>
          <view class="m">专注期间她不会打断你，只会在你想说话时回应。</view>
        </view>
      </view>

      <view v-if="finishedList.length" class="cal-sec" style="margin-top: 13px">
        <text class="t">已完成 {{ finishedList.length }} 步</text>
        <text class="s">回顾</text>
      </view>
      <view v-for="(s, i) in finishedList" :key="i" class="mem-item">
        <view class="mi tint-teal"><xt-icon name="i-check" /></view>
        <view class="tx">
          <view class="t done">{{ s.content }}</view>
          <view class="m">第 {{ i + 1 }} 步 · 已完成</view>
        </view>
      </view>

      <view v-if="taskDone" class="mem-hero" style="margin-top: 12px">
        <view class="t">全部步骤完成！</view>
        <view class="m">今天对自己兑现了承诺</view>
        <view class="fbtn main" style="margin-top: 10px" @click="goTimer"><text>再来一轮番茄专注</text></view>
      </view>

      <view class="focus-btns" style="margin-top: auto; padding-bottom: 4px">
        <view class="fbtn ghost" @click="goTimer"><text>换个时长</text></view>
        <view class="fbtn main" :class="{ busy }" @click="onDone">
          <text>{{ busy ? '推进中…' : '我做到了' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 分步引导页（核心特色：解决启动困难）
 * -------------------------------
 * - 界面一次只展示当前这一步；点「我做到了」→ POST /focus/step/finish
 * - 全程计时；推进时回写 /focus/record（引导记录可回放/导出）
 * - AI/角色台词随步骤推进更新
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      recordId: 0,
      roleId: 'companion',
      mode: 'simple',
      steps: [],
      current: { step_index: 1, content: '', est_minutes: 5, id: 0 },
      currentIndex: 1,
      finishedList: [],
      taskDone: false,
      cheer: '',
      busy: false,
      seconds: 0,
      timer: null
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    timerText() {
      const m = Math.floor(this.seconds / 60)
      const s = this.seconds % 60
      return `${m}:${s < 10 ? '0' + s : s}`
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    this.recordId = parseInt(options.record_id || 0, 10)
    this.roleId = options.role_id || 'companion'
    this.mode = options.mode || 'simple'
    this.loadRecord()
    this.timer = setInterval(() => { this.seconds++ }, 1000)
  },
  onUnload() {
    clearInterval(this.timer)
    this.saveProgress()
  },
  onHide() {
    this.saveProgress()
  },
  methods: {
    async loadRecord() {
      try {
        const res = await focusApi.getRecordDetail(this.recordId)
        const data = (res && res.data) || {}
        const steps = data.steps || []
        // 预生成步骤 id 占位（步骤完成按内容序号推进，finish 接口按 step_id）
        // 引导模式的步骤不在 focus_step 表（引导记录独立保存），此处用本地索引推进
        this.steps = steps.map((s, i) => Object.assign({}, s, { step_index: i + 1 }))
        const idx = Math.min(this.currentIndex, this.steps.length)
        this.current = this.steps[idx - 1] || { step_index: idx, content: '', est_minutes: 5 }
        this.cheer = data.cheer || '我们开始吧，只做眼前这一步。'
      } catch (e) { /* request 层已提示 */ }
    },
    async onDone() {
      if (this.busy) return
      this.busy = true
      try {
        this.finishedList.push(this.current)
        this.currentIndex++
        const next = this.steps[this.currentIndex - 1]
        // 回写引导记录（计时 + 进度）
        focusApi.saveRecord(this.recordId, this.currentIndex, this.seconds).catch(() => {})
        if (next) {
          this.current = next
          this.cheer = '很好，再来下一步。'
        } else {
          this.taskDone = true
          this.cheer = '全部完成！今天对自己兑现了承诺。'
        }
      } finally {
        this.busy = false
      }
    },
    async saveProgress() {
      if (!this.recordId) return
      try { await focusApi.saveRecord(this.recordId, this.currentIndex, this.seconds) } catch (e) { /* noop */ }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    switchMode(m) {
      if (this.mode === m) return
      this.mode = m
      uni.showToast({ title: m === 'simple' ? '已切换为简单模式' : '已切换为心流模式', icon: 'none', duration: 900 })
    },
    goTimer() {
      uni.navigateTo({ url: `/pages/focus/focus-timer?role_id=${this.roleId}&mode=${this.mode}&minutes=25` })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿为整屏纵向排布，底部 CTA 固定贴底 */
.xt-page.xt-s48 .body {
  display: flex;
  flex-direction: column;
  padding-bottom: 20px;
}

/* 会话头右侧的计时（原导航条时长） */
.xt-page.xt-s48 .tick {
  flex-shrink: 0;
  font-size: 8px;
  font-weight: 800;
  color: var(--v7-green);
}

/* 设计稿 158px 环 + 126px 内圈 */
.xt-page.xt-s48 .ring {
  width: 158px;
  height: 158px;
  background: conic-gradient(#B5C7BF 0deg 300deg, #EDF1F0 300deg 360deg);
}
.xt-page.xt-s48 .ring::before {
  inset: 16px;
}
.xt-page.xt-s48 .ring .t {
  font-size: 30px;
  font-weight: 900;
  letter-spacing: -1px;
}
.xt-page.xt-s48 .ring .k {
  font-size: 7px;
  letter-spacing: 1.4px;
}
.xt-page.xt-s48 .focus-task .n {
  font-size: 13px;
}
.xt-page.xt-s48 .focus-task .m {
  margin-top: 3px;
  font-size: 8.5px;
  color: #8E9A91;
}

/* 设计稿 .seg 依赖 span 元素选择器，改用等价 class */
.xt-page.xt-s48 .seg .sg {
  flex: 1;
  padding: 7px 0;
  border-radius: 9px;
  text-align: center;
  font-size: 8px;
  color: var(--v7-gray);
  background: rgba(255, 253, 250, 0.75);
}
.xt-page.xt-s48 .seg .sg.on {
  color: #F8F3E7;
  font-weight: 900;
  background: var(--v7-green);
  box-shadow: none;
}

.xt-page.xt-s48 .mem-item .t.done {
  font-weight: 400;
  color: #AEB6AE;
  text-decoration: line-through;
}

.xt-page.xt-s48 .fbtn.busy {
  opacity: 0.6;
}
</style>
