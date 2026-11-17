<template>
  <view class="xt-page xt-s66">
    <view class="body" style="display:flex;flex-direction:column">
      <!-- 顶部：返回 / 状态 / 设置 -->
      <view class="fcs-head">
        <view class="fcs-back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="fcs-mode"><i></i>{{ modeLabel }} · {{ stateText }}</view>
        <view class="fcs-set"><xt-icon name="i-settings" /></view>
      </view>

      <!-- 本次任务 -->
      <view class="fcs-task">
        <b>{{ tag }}</b>
        <span>不强求做完，坐满这 {{ totalMinutes }} 分钟就好</span>
      </view>

      <!-- 计时环 -->
      <view class="fcs-ringwrap">
        <view class="fcs-ticks"></view>
        <view class="fcs-ring" :style="ringStyle">
          <view class="fcs-in">
            <span class="fcs-time">{{ timeText }}</span>
            <span class="fcs-k">剩余 · 共 {{ totalMinutes }} 分钟</span>
          </view>
          <view class="fcs-hand" :style="{ transform: `rotate(${progressDeg}deg)` }"><i></i></view>
        </view>
      </view>

      <!-- 她在旁边 -->
      <view class="fcs-presence">
        <view class="fcs-av">
          <image v-if="rolePhoto" :src="rolePhoto" mode="aspectFill" />
          <view v-else class="fcs-av-fb"><text>{{ roleAvatar }}</text></view>
        </view>
        <view class="fcs-pt">
          <b>{{ running ? '她在旁边' : (finished ? '她陪你收尾' : '她准备好了') }}</b>
          <span>{{ currentCheer }}</span>
        </view>
        <view class="fcs-wave"><i></i><i></i><i></i><i></i><i></i></view>
      </view>

      <!-- 防分心守护 + 时长 -->
      <view class="fcs-sound">
        <view class="fcs-srow">
          <view class="fcs-sic"><xt-icon name="i-bell" /></view>
          <view class="fcs-st">
            <b>防分心守护</b>
            <span>{{ guardText }}</span>
          </view>
          <view class="fcs-eq"><i></i><i></i><i></i><i></i></view>
        </view>
        <view class="fcs-chips" v-if="!running && !finished">
          <span
            v-for="m in [15, 25, 45, 60]"
            :key="m"
            :class="{ on: totalMinutes === m }"
            @click="totalMinutes = m"
          >{{ m }} 分钟</span>
        </view>
      </view>

      <!-- 本次数据 -->
      <view class="fcs-stats">
        <view class="st"><b>{{ elapsedText }}</b><span>本次已专注</span></view>
        <view class="st"><b>{{ session.count }}</b><span>离开次数</span></view>
        <view class="st"><b>{{ totalMinutes }}′</b><span>计划时长</span></view>
      </view>

      <view class="fcs-quote">「不用做得很完美，<b>先坐下来，就已经开始了。」</b></view>

      <!-- 操作 -->
      <view class="fcs-actions">
        <view v-if="!running && !finished" class="fbtn fcs-main" @click="startTimer">
          <xt-icon name="i-clock" />开始专注
        </view>
        <view v-else-if="running" class="fbtn fcs-main" @click="finishTimer(false)">
          <xt-icon name="i-clock" />结束专注
        </view>
        <view v-else class="fbtn fcs-main" @click="resetTimer">
          <xt-icon name="i-clock" />再来一轮
        </view>
        <view v-if="running" class="fbtn fcs-ghost" @click="finishTimer(true)">放弃</view>
        <view v-else class="fbtn fcs-ghost" @click="goBack">返回</view>
      </view>

      <view class="fcs-note">{{ finished ? (summary || '本次专注已完成') : lockTip }}</view>
    </view>

    <!-- App 锁拦截弹窗（原生 App；切出后返回时弹出） -->
    <view v-if="showLockMask" class="mask" @click="backToFocus">
      <view class="lock-card" @click.stop>
        <view class="lock-halo"><text class="lock-emoji">🍅</text></view>
        <text class="lock-title">专注还在进行中</text>
        <text class="lock-sub">你刚才离开了 {{ session.count }} 次，回来继续，就差一点点啦</text>
        <view class="lock-btn" @click="backToFocus">
          <text class="lock-btn-text">返回专注</text>
        </view>
        <text class="lock-later" @click="finishTimer(true)">放弃本次专注</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 专注番茄计时页 + App 锁（防分心）
 * -------------------------------
 * - 计时由前端驱动；start → POST /focus/session/start 登记
 * - 离开检测：onHide / App 切出 → POST /focus/session/interrupt 记录
 * - App 锁拦截弹窗：切出后回到 App 时弹出（#ifdef APP-PLUS 走 plus 事件，其余端用 onHide）
 * - 结束 → POST /focus/session/finish 自动生成专注记录
 *
 * 平台能力差异（需求第四节）：
 * - App：plus 'pause'/'resume' 事件拦截 + 弹窗；黑名单应用级拦截需原生插件，见交付说明
 * - 小程序 / H5：仅页面 onHide 离开检测，能力降级
 */
import focusApi from '@/api/focus'
import { getActivePartnerId, getPartnerAvatar, findPartner } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      tag: '学习',
      roleId: getActivePartnerId(),
      mode: 'simple',
      totalMinutes: 25,
      running: false,
      finished: false,
      remain: 0,
      session: { id: 0, count: 0 },
      cheerLines: [],
      cheerIdx: 0,
      cheerTimer: null,
      timer: null,
      summary: '',
      showLockMask: false,
      _pausedAt: 0
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    timeText() {
      const m = Math.floor(this.remain / 60)
      const s = this.remain % 60
      return `${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`
    },
    currentCheer() {
      return this.cheerLines.length ? this.cheerLines[this.cheerIdx % this.cheerLines.length] : '专注眼前这一件事。'
    },
    lockTip() {
      // #ifdef APP-PLUS
      return 'App 端：专注期间切出会触发拦截提醒'
      // #endif
      // #ifndef APP-PLUS
      return '小程序 / H5：切离页面会被记录打断（能力降级）'
      // #endif
    },
    modeLabel() {
      return this.mode === 'flow' ? '心流引导' : '简单引导'
    },
    stateText() {
      return this.running ? '专注中' : (this.finished ? '已完成' : '准备开始')
    },
    guardText() {
      return this.session.count > 0
        ? `本次已记录离开 ${this.session.count} 次`
        : '专注期间切出会被记录'
    },
    elapsedText() {
      const used = Math.max(this.totalMinutes * 60 - this.remain, 0)
      const m = Math.floor(used / 60)
      const s = used % 60
      return `${m}:${s < 10 ? '0' + s : s}`
    },
    progressDeg() {
      if (!this.running && !this.finished) return 0
      const total = this.totalMinutes * 60 || 1
      return 360 - Math.round((this.remain / total) * 360)
    },
    ringStyle() {
      const deg = this.progressDeg
      return `background: conic-gradient(from -90deg, #24493A 0deg ${deg}deg, #F1F2EA ${deg}deg 360deg)`
    },
    rolePhoto() {
      return getPartnerAvatar(findPartner(this.roleId) || this.roleId) || ''
    },
    roleAvatar() {
      const p = findPartner(this.roleId)
      return (p && p.avatar) || '🌿'
    }
  },
  onLoad(options) {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    this.roleId = options.role_id || 'companion'
    this.mode = options.mode || 'simple'
    this.tag = options.tag || '学习'
    if (options.minutes) this.totalMinutes = parseInt(options.minutes, 10) || 25
    this.remain = this.totalMinutes * 60
    this.registerAppLock()
  },
  onUnload() {
    this.clearTimers()
    this.unregisterAppLock()
    if (this.running) this.finishTimer(true) // 页面被关掉时按中断落库
  },
  onShow() {
    // 从其它页面/切后台回来：App 弹拦截窗
    if (this.running && this._pausedAt) {
      this.session.count++
      if (this.session.id) focusApi.sessionInterrupt(this.session.id, 1).catch(() => {})
      // #ifdef APP-PLUS
      this.showLockMask = true
      // #endif
      this._pausedAt = 0
    }
  },
  onHide() {
    if (this.running) {
      this._pausedAt = Date.now()
      this.session.count++
      if (this.session.id) focusApi.sessionInterrupt(this.session.id, 1).catch(() => {})
    }
  },
  methods: {
    /* ---------- App 锁（仅原生 App） ---------- */
    registerAppLock() {
      // #ifdef APP-PLUS
      try {
        const that = this
        plus.event.addEventListener('pause', () => {
          if (that.running) {
            that._pausedAt = Date.now()
            that.session.count++
            if (that.session.id) focusApi.sessionInterrupt(that.session.id, 1).catch(() => {})
          }
        }, false)
        plus.event.addEventListener('resume', () => {
          if (that.running && that._pausedAt) {
            that.showLockMask = true
            that._pausedAt = 0
          }
        }, false)
      } catch (e) { /* 降级到 onShow/onHide */ }
      // #endif
    },
    unregisterAppLock() {
      // #ifdef APP-PLUS
      try {
        plus.event.removeEventListener('pause')
        plus.event.removeEventListener('resume')
      } catch (e) { /* noop */ }
      // #endif
    },
    backToFocus() {
      this.showLockMask = false
    },

    /* ---------- 计时 ---------- */
    async startTimer() {
      try {
        const res = await focusApi.startSession({
          task_id: 0, role_id: this.roleId, mode: this.mode, tag: this.tag
        })
        const data = (res && res.data) || {}
        this.session = { id: data.session_id || 0, count: 0 }
        this.cheerLines = data.cheer_lines && data.cheer_lines.length
          ? data.cheer_lines : ['专注眼前这一件事。']
      } catch (e) {
        // 会话登记失败也允许本地计时，结束时会话 id 为 0 不落库
        this.cheerLines = ['专注眼前这一件事。']
      }
      this.running = true
      this.remain = this.totalMinutes * 60
      this.cheerTimer = setInterval(() => { this.cheerIdx++ }, 12000)
      this.timer = setInterval(() => {
        this.remain--
        if (this.remain <= 0) {
          this.remain = 0
          this.finishTimer(false)
        }
      }, 1000)
    },
    finishTimer(interrupted) {
      this.running = false
      this.showLockMask = false
      this.finished = true
      this.clearTimers()
      const duration = this.totalMinutes * 60 - this.remain
      if (this.session.id) {
        focusApi.finishSession(this.session.id, duration, interrupted || this.session.count > 0)
          .then((res) => {
            this.summary = (res && res.data && res.data.summary) || `本次专注 ${Math.round(duration / 60)} 分钟`
          }).catch(() => {
            this.summary = `本次专注 ${Math.round(duration / 60)} 分钟`
          })
      } else {
        this.summary = `本次专注 ${Math.round(duration / 60)} 分钟`
      }
    },
    resetTimer() {
      this.finished = false
      this.session = { id: 0, count: 0 }
      this.remain = this.totalMinutes * 60
      this.summary = ''
    },
    clearTimers() {
      clearInterval(this.timer)
      clearInterval(this.cheerTimer)
      this.timer = null
      this.cheerTimer = null
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 页面滚动（设计稿为静态长屏） */
.xt-page.xt-s66 .body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* uni-image 同步设计稿 img 尺寸 */
.xt-page.xt-s66 .fcs-av uni-image {
  width: 100%; height: 100%; border-radius: 50%; display: block; overflow: hidden;
}
.xt-page.xt-s66 .fcs-av uni-image :deep(img) {
  width: 100%; height: 100%; object-fit: cover;
}

/* 无立绘伙伴回退 */
.xt-page.xt-s66 .fcs-av-fb {
  width: 100%; height: 100%; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: #F1EDE3; font-size: 16px; line-height: 1;
}

/* 数据三格：设计稿用 div 选择器，这里换成 class */
.xt-page.xt-s66 .fcs-stats .st { flex: 1; text-align: center; }
.xt-page.xt-s66 .fcs-stats .st + .st { border-left: 1px solid var(--v7-line); }

/* 守护文案可能较长，避免挤压右侧律动条 */
.xt-page.xt-s66 .fcs-srow .fcs-st { flex: 1; min-width: 0; }

/* ---------- App 锁弹窗 ---------- */
.mask {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 100;
  background: rgba(34, 48, 42, 0.46);
  display: flex; align-items: center; justify-content: center;
}
.lock-card {
  width: 280px; padding: 22px 18px 16px;
  border-radius: 18px; background: var(--v7-card);
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 15px 30px -15px rgba(34, 48, 42, 0.5);
}
.lock-halo {
  width: 90px; height: 90px; border-radius: 50%;
  background: radial-gradient(circle at 50% 40%, rgba(156, 191, 170, 0.30), rgba(156, 191, 170, 0.06) 70%);
  display: flex; align-items: center; justify-content: center;
}
.lock-emoji { font-size: 42px; }
.lock-title { margin-top: 9px; font-size: 16px; font-weight: 800; color: #22302A; }
.lock-sub { margin-top: 6px; font-size: 11px; line-height: 1.7; color: #8A968D; text-align: center; }
.lock-btn {
  margin-top: 16px; width: 100%; height: 46px; border-radius: 999px;
  background: linear-gradient(140deg, #4E7A64, #24493A);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 7px 13px -9px rgba(36, 73, 58, 0.9);
  &:active { transform: scale(0.98); }
}
.lock-btn-text { font-size: 14px; font-weight: 800; color: #FFFDFA; letter-spacing: 1px; }
.lock-later { margin-top: 11px; font-size: 11px; color: #AEB6AE; }
</style>
