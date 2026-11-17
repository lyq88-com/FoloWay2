<template>
  <view class="xt-page xt-s12">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view class="fh-title">
          <view class="fh-back" @click="goBack"><xt-icon name="i-left" /></view>
          <view>
            <view class="page-title">一起专注</view>
            <view class="page-sub">她坐在旁边，不打扰你</view>
          </view>
        </view>
        <view class="icon-btn" @click="goTimer"><xt-icon name="i-clock" /></view>
      </view>

      <!-- 引导节奏 -->
      <view class="chips" style="margin:0 0 4px">
        <view class="chip" :class="{ on: mode === 'simple' }" @click="mode = 'simple'">简单引导</view>
        <view class="chip" :class="{ on: mode === 'flow' }" @click="mode = 'flow'">心流引导</view>
        <view class="chip" :class="{ on: plan_style === 'appoint' }" @click="plan_style = 'appoint'">约定开始</view>
        <view class="chip" :class="{ on: plan_style === 'fixed' }" @click="plan_style = 'fixed'">固定时长</view>
      </view>

      <!-- 今日进度环 -->
      <view class="focus-wrap">
        <view class="ring" :style="ringStyle" @click="goBoard">
          <view class="in">
            <view class="t">{{ board.progress.percent }}<text class="unit">%</text></view>
            <view class="k">今日进度 · 点进看板</view>
          </view>
        </view>

        <view class="focus-task">
          <view class="n">{{ currentTask ? currentTask.title : '今天还没有安排' }}</view>
          <view class="m" v-if="currentTask && currentTask.total_steps">拆成 {{ currentTask.total_steps }} 步 · 已完成 {{ currentTask.finished_steps }} 步</view>
          <view class="m" v-else>写下想做的事，她陪你拆成小步</view>
        </view>

        <view class="focus-tip" @click="goChat">
          <image v-if="rolePhoto" :src="rolePhoto" mode="aspectFill" />
          <view v-else class="fh-tip-av"><text>{{ currentRole.avatar || '🌿' }}</text></view>
          <text class="p">{{ roleTip }}</text>
        </view>

        <view class="focus-btns">
          <view class="fbtn ghost" @click="goBoard">看看今天</view>
          <view class="fbtn main" @click="goTimer">开始专注</view>
        </view>
      </view>

      <!-- 今日三格 -->
      <view class="pills" style="margin-top:12px">
        <view class="pill">
          <view class="v">{{ board.progress.finished }}</view>
          <view class="k">已完成</view>
        </view>
        <view class="pill">
          <view class="v">{{ board.progress.total - board.progress.finished }}</view>
          <view class="k">待完成</view>
        </view>
        <view class="pill">
          <view class="v">{{ board.progress.percent }}<span>%</span></view>
          <view class="k">完成率</view>
        </view>
      </view>

      <!-- 陪伴角色 -->
      <view class="sec">
        <text class="sec-t">陪伴角色</text>
        <text class="sec-s">点选切换</text>
      </view>
      <scroll-view class="fh-roles" scroll-x>
        <view class="rail">
          <view
            v-for="r in roleRail"
            :key="r.id"
            class="rail-role"
            :class="{ on: roleId === r.id }"
            @click="roleId = r.id"
          >
            <view class="rail-av">
              <image v-if="r.photo" :src="r.photo" mode="aspectFill" />
              <text v-else class="rail-emoji">{{ r.avatar }}</text>
            </view>
            <text class="rail-name">{{ r.name }}</text>
          </view>
        </view>
      </scroll-view>

      <!-- 任务输入 -->
      <view class="sec">
        <text class="sec-t">现在想做什么？</text>
        <text class="sec-s">一句话就够</text>
      </view>
      <view class="mem-hero">
        <textarea
          v-model="prompt"
          class="mood-input"
          :maxlength="120"
          placeholder="例如：复习数学第三章 / 收拾房间"
        />
        <!-- #ifndef H5 -->
        <text v-if="recording" class="fh-rec">正在聆听…再次点击结束并识别</text>
        <!-- #endif -->
        <view class="fh-row">
          <!-- #ifndef H5 -->
          <view class="task-plus" @click="toggleRecord"><xt-icon :name="recording ? 'i-check' : 'i-plus'" /></view>
          <!-- #endif -->
          <view class="fbtn main" @click="startGuide">{{ starting ? '正在拆解…' : '开始分步引导' }}</view>
        </view>
      </view>

      <!-- 空态推荐 -->
      <view class="sec" v-if="recommends.length">
        <text class="sec-t">不知道做什么？</text>
        <text class="sec-s">{{ recommends.length }} 个灵感</text>
      </view>
      <view
        v-for="(r, i) in recommends"
        :key="i"
        class="task"
        @click="prompt = r.title"
      >
        <view class="task-ic ti-book"><xt-icon name="i-spark" /></view>
        <view class="task-main">
          <view class="task-n">{{ r.title }}</view>
          <view class="task-m">{{ r.minutes }} 分钟 · 点一下填进输入框</view>
        </view>
        <view class="task-go">用这个</view>
      </view>

      <!-- 专注工具箱 -->
      <view class="sec">
        <text class="sec-t">专注工具箱</text>
        <text class="sec-s">全部入口</text>
      </view>
      <view class="mod-grid">
        <view class="mod" @click="goBoard">
          <view class="mod-top"><view class="mod-ic tint-green"><xt-icon name="i-calendar" /></view></view>
          <view><view class="mod-n">待办看板</view><view class="mod-m">今天要做的事</view></view>
        </view>
        <view class="mod" @click="goPlan">
          <view class="mod-top"><view class="mod-ic tint-peach"><xt-icon name="i-focus" /></view></view>
          <view><view class="mod-n">备考计划</view><view class="mod-m">AI 帮你排期</view></view>
        </view>
        <view class="mod" @click="goTimer">
          <view class="mod-top"><view class="mod-ic tint-blue"><xt-icon name="i-clock" /></view></view>
          <view><view class="mod-n">番茄专注</view><view class="mod-m">25 分钟一轮</view></view>
        </view>
        <view class="mod" @click="goChat">
          <view class="mod-top"><view class="mod-ic tint-teal"><xt-icon name="i-chat" /></view></view>
          <view><view class="mod-n">监督陪伴</view><view class="mod-m">说说话再开始</view></view>
        </view>
        <view class="mod" @click="goRecords">
          <view class="mod-top"><view class="mod-ic tint-sand"><xt-icon name="i-book" /></view></view>
          <view><view class="mod-n">引导记录</view><view class="mod-m">回看每次拆解</view></view>
        </view>
        <view class="mod" @click="goStats">
          <view class="mod-top"><view class="mod-ic tint-purple"><xt-icon name="i-tool" /></view></view>
          <view><view class="mod-n">专注统计</view><view class="mod-m">看看这周的变化</view></view>
        </view>
        <view class="mod" @click="goDynamic">
          <view class="mod-top"><view class="mod-ic tint-green"><xt-icon name="i-spark" /></view></view>
          <view><view class="mod-n">专注动态</view><view class="mod-m">记下一点点进步</view></view>
        </view>
      </view>

      <!-- 设置 -->
      <view class="sec">
        <text class="sec-t">设置</text>
        <text class="sec-s" @click="goSetting">随时可改</text>
      </view>
      <view class="fh-switch">
        <text class="t">专注提醒</text>
        <switch :checked="setting.allow_remind" @change="onToggleRemind" color="#24493A" />
      </view>
      <view class="fh-switch">
        <text class="t">专注动态发布</text>
        <switch :checked="setting.allow_dynamic" @change="onToggleDynamic" color="#24493A" />
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 专注引导首页
 * -------------------------------
 * 角色选择（沿用现有角色体系）/ 模式选择 / 任务输入（语音）
 * 「开始分步引导」→ POST /focus/task/split → 跳分步引导页
 *
 * 平台说明：
 * - 语音输入：App / 小程序使用 uni.getRecorderManager；H5 自动隐藏（能力降级）
 * - 应用锁等原生能力只在专注计时页（focus-timer）内启用
 */
import focusApi from '@/api/focus'
import focusNotify from '@/common/focus-notify'
import { CHARACTERS, STYLE_LABELS } from '@/common/ai-characters'
import { getActivePartnerId, getPartnerAvatar, findPartner } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      roles: [],
      roleId: getActivePartnerId(),
      mode: 'simple',
      plan_style: 'appoint',
      prompt: '',
      recording: false,
      recorder: null,
      starting: false,
      board: { progress: { finished: 0, total: 0, percent: 0 } },
      setting: { allow_dynamic: true, allow_remind: true },
      recommends: []
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    currentTask() {
      const list = (this.board && this.board.list) || []
      return list.find(t => t.status !== 2) || list[0] || null
    },
    currentRole() {
      return findPartner(this.roleId) || findPartner(getActivePartnerId()) || CHARACTERS[0] || {}
    },
    rolePhoto() {
      return getPartnerAvatar(this.currentRole) || ''
    },
    roleTip() {
      return this.currentRole.catchphrase || '她坐在旁边，不打扰你'
    },
    roleRail() {
      return this.roles.map((r) => {
        const c = findPartner(r.id) || {}
        return { id: r.id, name: r.name, avatar: c.avatar || '🌿', photo: getPartnerAvatar(c) || '' }
      })
    },
    ringStyle() {
      const deg = Math.round((this.board.progress.percent || 0) * 3.6)
      return `background: conic-gradient(#24493A 0deg ${deg}deg, #F1F2EA ${deg}deg 360deg)`
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() {
    this.loadAll()
    // 拉取待触发提醒并调度本地通知（复用系统通知能力，不改既有通知代码）
    focusNotify.scheduleAll()
  },
  onUnload() {
    // 离开页面时确保录音停止
    if (this.recording) this.stopRecord(true)
  },
  methods: {
    async loadAll() {
      try {
        // 角色源统一用 CHARACTERS 20 个（绕过后端 focus/persona.py 硬编码的 7 个旧角色）
        const customs = (this.$store.state.customCharacters || [])
          .filter(c => c && c.id)
          .map(c => ({ id: c.id, name: c.name, style: c.style || '自定义' }))
        this.roles = [
          ...CHARACTERS.map(c => ({
            id: c.id,
            name: c.name,
            style: STYLE_LABELS[c.style] || c.style,
          })),
          ...customs
        ]
        // 默认对齐当前生效伙伴（含自定义），不再回落成第一个角色
        this.roleId = getActivePartnerId()
        if (this.roles.length && !this.roles.find(r => r.id === this.roleId)) {
          this.roleId = this.roles[0].id
        }
        const [board, setting, rec] = await Promise.all([
          focusApi.getTasks(), focusApi.getSetting(), focusApi.getRecommend()
        ])
        if (board && board.code === 200) this.board = board.data
        if (setting && setting.code === 200) this.setting = setting.data
        if (rec && rec.code === 200) this.recommends = rec.data.list || []
      } catch (e) { /* request 层已提示 */ }
    },

    /* ---------- 分步引导启动 ---------- */
    async startGuide() {
      const p = (this.prompt || '').trim()
      if (!p) { uni.showToast({ title: '先说说你想做什么吧', icon: 'none' }); return }
      if (this.starting) return
      this.starting = true
      try {
        const res = await focusApi.splitTask(p, this.mode)
        const data = (res && res.data) || {}
        if (data.record_id) {
          uni.navigateTo({
            url: `/pages/focus/focus-guide?record_id=${data.record_id}&role_id=${this.roleId}&mode=${this.mode}`
          })
        }
      } catch (e) { /* request 层已提示 */ } finally {
        this.starting = false
      }
    },

    /* ---------- 语音输入（App / 小程序） ---------- */
    toggleRecord() {
      if (this.recording) { this.stopRecord(false); return }
      const rm = uni.getRecorderManager()
      this.recorder = rm
      rm.onStop((res) => {
        this.recording = false
        if (!res || !res.tempFilePath) return
        uni.showLoading({ title: '识别中…' })
        focusApi.uploadAudio(res.tempFilePath).then((r) => {
          uni.hideLoading()
          if (r && r.code === 200 && r.data && r.data.text) {
            this.prompt = this.prompt ? this.prompt + ' ' + r.data.text : r.data.text
          } else {
            // 后端未配置/识别失败时返回明确原因，不再统一说「没听清」
            uni.showToast({ title: (r && r.message) || '没听清，再试一次？', icon: 'none', duration: 2600 })
          }
        }).catch((e) => { uni.hideLoading(); uni.showToast({ title: (e && e.message) || '识别失败', icon: 'none' }) })
      })
      rm.onError(() => { this.recording = false; uni.showToast({ title: '录音出错', icon: 'none' }) })
      rm.start({ format: 'mp3', duration: 30000 })
      this.recording = true
    },
    stopRecord(silent) {
      try { this.recorder && this.recorder.stop() } catch (e) { /* noop */ }
      this.recording = false
      if (silent) { /* 页面卸载时静默停止 */ }
    },

    /* ---------- 开关 ---------- */
    async onToggleRemind(e) {
      const v = !!e.detail.value
      this.setting.allow_remind = v
      try { await focusApi.setSetting({ allow_remind: v }) } catch (err) { /* noop */ }
    },
    async onToggleDynamic(e) {
      const v = !!e.detail.value
      this.setting.allow_dynamic = v
      try { await focusApi.setSetting({ allow_dynamic: v }) } catch (err) { /* noop */ }
    },

    /* ---------- 导航 ---------- */
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goBoard() { uni.navigateTo({ url: '/pages/focus/focus-board' }) },
    goPlan() { uni.navigateTo({ url: '/pages/focus/focus-plan' }) },
    goTimer() { uni.navigateTo({ url: `/pages/focus/focus-timer?role_id=${this.roleId}&mode=${this.mode}&minutes=${this.plan_style === 'flow' ? 45 : 25}` }) },
    goChat() { uni.navigateTo({ url: '/pages/focus/focus-chat' }) },
    goRecords() { uni.navigateTo({ url: '/pages/focus/focus-records' }) },
    goStats() { uni.navigateTo({ url: '/pages/focus/focus-stats' }) },
    goDynamic() { uni.navigateTo({ url: '/pages/focus/focus-dynamic' }) },
    goSetting() { uni.showToast({ title: '下方「设置」区可直接开关', icon: 'none' }) }
  }
}
</script>

<style lang="scss" scoped>
/* 页面滚动 + 底部留白（设计稿为静态长屏） */
.xt-page.xt-s12 .body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 24px;
}

/* 页头：返回 + 标题 */
.xt-page.xt-s12 .fh-title { display: flex; align-items: center; gap: 8px; }
.xt-page.xt-s12 .fh-back {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: var(--v7-gray); background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s12 .fh-back .ic { width: 15px; height: 15px; }

/* 进度环单位 */
.xt-page.xt-s12 .ring .unit {
  font-size: 15px; font-weight: 700; color: var(--v7-gray-2); letter-spacing: 0;
}

/* 她的话：无真人头像时的兜底 */
.xt-page.xt-s12 .fh-tip-av {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(156, 191, 170, 0.18); font-size: 15px;
}

/* uni-image 同步设计稿 img 的尺寸（H5 渲染为 uni-image） */
.xt-page.xt-s12 .focus-tip uni-image {
  width: 30px; height: 30px; border-radius: 50%; display: block; overflow: hidden;
}
.xt-page.xt-s12 .rail-av uni-image {
  width: 100%; height: 100%; border-radius: 50%; display: block; overflow: hidden;
}
.xt-page.xt-s12 .focus-tip uni-image :deep(img),
.xt-page.xt-s12 .rail-av uni-image :deep(img) {
  width: 100%; height: 100%; object-fit: cover;
}
.xt-page.xt-s12 .rail-av {
  display: flex; align-items: center; justify-content: center;
}
.xt-page.xt-s12 .rail-emoji { font-size: 20px; line-height: 1; }

/* 角色轨道横向滚动 */
.xt-page.xt-s12 .fh-roles { white-space: nowrap; }
.xt-page.xt-s12 .fh-roles .rail { width: max-content; padding-bottom: 2px; }
.xt-page.xt-s12 .fh-roles .rail-role { flex: 0 0 46px; }

/* 任务输入 */
.xt-page.xt-s12 .mood-input { width: 100%; height: 62px; font-size: 9px; line-height: 1.65; }
.xt-page.xt-s12 .fh-row { display: flex; align-items: center; gap: 8px; margin-top: 9px; }
.xt-page.xt-s12 .fh-rec { display: block; margin-top: 6px; font-size: 8px; color: #B8874E; }

/* 设置行 */
.xt-page.xt-s12 .fh-switch {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 13px; margin-bottom: 7px; border-radius: 15px; background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s12 .fh-switch .t { font-size: 9.5px; font-weight: 800; color: var(--v7-ink); }
.xt-page.xt-s12 .fh-switch uni-switch { transform: scale(0.68); transform-origin: right center; }
</style>
