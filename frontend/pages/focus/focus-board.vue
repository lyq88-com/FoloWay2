<template>
  <view class="xt-page xt-s49">
    <scroll-view
      class="body"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
    >
      <view class="page-title-row">
        <view>
          <view class="page-title">专注看板</view>
          <view class="page-sub">今天 {{ board.progress.total }} 件，已经做完 {{ board.progress.finished }} 件</view>
        </view>
        <view class="hbtns">
          <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
          <view class="icon-btn" @click="goPlan"><xt-icon name="i-plus" /></view>
        </view>
      </view>

      <view class="mem-hero" style="display: flex; align-items: center; gap: 11px; padding: 11px 13px">
        <view
          class="fring"
          :style="{ background: 'conic-gradient(#24493A 0deg ' + (board.progress.percent * 3.6) + 'deg, #ECF0EE ' + (board.progress.percent * 3.6) + 'deg 360deg)' }"
        >
          <view class="fring-in">{{ board.progress.percent }}</view>
        </view>
        <view style="flex: 1">
          <view style="font-size: 9.5px; font-weight: 900">今日进度 · {{ board.date }}</view>
          <view style="font-size: 7.5px; color: #8E9A91; margin-top: 2px">还剩 {{ board.progress.total - board.progress.finished }} 件 · 她在旁边</view>
        </view>
        <text class="chip on" style="font-size: 7.5px">{{ board.progress.percent }}%</text>
      </view>

      <view class="board" style="margin-top: 12px" v-if="board.list.length">
        <!-- 待开始 -->
        <view class="bcol2">
          <view class="ct">待开始</view>
          <view v-for="t in board.list" :key="'todo' + t.id" class="bwrap">
            <view v-if="t.status !== 2 && !t.finished_steps" class="card2 bcard" @click="toggleExpand(t)">
              <view class="brow">
                <view class="bcheck" @click.stop="toggleTask(t)"></view>
                <text class="bt">{{ t.title }}</text>
              </view>
              <view class="bm">{{ t.tag }} · {{ t.est_minutes }}′<text v-if="t.remind_time"> · {{ t.remind_time }}</text></view>
              <view v-if="t._expanded && t.steps && t.steps.length" class="bsteps">
                <view v-for="(s, i) in t.steps" :key="s.id" class="bstep" @click.stop="finishStep(t, s)">
                  <view class="bcheck sm" :class="{ on: s.is_finished }">
                    <text class="bk">{{ s.is_finished ? '✓' : i + 1 }}</text>
                  </view>
                  <text class="bst" :class="{ on: s.is_finished }">{{ s.content }}</text>
                </view>
              </view>
              <view v-if="t._expanded" class="bdel" @click.stop="removeTask(t)"><text>删除</text></view>
            </view>
          </view>
          <view class="card2 add" @click="goPlan"><text>+ 加一件</text></view>
        </view>

        <!-- 进行中 -->
        <view class="bcol2">
          <view class="ct">进行中</view>
          <view v-for="t in board.list" :key="'doing' + t.id" class="bwrap">
            <view v-if="t.status !== 2 && t.finished_steps" class="card2 bcard doing" @click="toggleExpand(t)">
              <view class="brow">
                <view class="bcheck" @click.stop="toggleTask(t)"></view>
                <text class="bt">{{ t.title }}</text>
              </view>
              <view class="bm">{{ t.tag }} · {{ t.est_minutes }}′<text v-if="t.remind_time"> · {{ t.remind_time }}</text></view>
              <view v-if="t._expanded && t.steps && t.steps.length" class="bsteps">
                <view v-for="(s, i) in t.steps" :key="s.id" class="bstep" @click.stop="finishStep(t, s)">
                  <view class="bcheck sm" :class="{ on: s.is_finished }">
                    <text class="bk">{{ s.is_finished ? '✓' : i + 1 }}</text>
                  </view>
                  <text class="bst" :class="{ on: s.is_finished }">{{ s.content }}</text>
                </view>
              </view>
              <view v-if="t._expanded" class="bdel" @click.stop="removeTask(t)"><text>删除</text></view>
            </view>
          </view>
          <view class="card2 hint"><text>一次只做一件</text></view>
        </view>

        <!-- 已完成 -->
        <view class="bcol2">
          <view class="ct">已完成</view>
          <view v-for="t in board.list" :key="'done' + t.id" class="bwrap">
            <view v-if="t.status === 2" class="card2 bcard wdone" @click="toggleExpand(t)">
              <view class="brow">
                <view class="bcheck on" @click.stop="toggleTask(t)"><text class="bk">✓</text></view>
                <text class="bt">{{ t.title }}</text>
              </view>
              <view class="bm">{{ t.tag }} · {{ t.est_minutes }}′</view>
              <view v-if="t._expanded && t.steps && t.steps.length" class="bsteps">
                <view v-for="(s, i) in t.steps" :key="s.id" class="bstep" @click.stop="finishStep(t, s)">
                  <view class="bcheck sm" :class="{ on: s.is_finished }">
                    <text class="bk">{{ s.is_finished ? '✓' : i + 1 }}</text>
                  </view>
                  <text class="bst" :class="{ on: s.is_finished }">{{ s.content }}</text>
                </view>
              </view>
              <view v-if="t._expanded" class="bdel" @click.stop="removeTask(t)"><text>删除</text></view>
            </view>
          </view>
          <view class="card2 hint"><text>每件都算数</text></view>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 14px">
        <text class="t">今天的节奏</text>
        <text class="s">{{ board.progress.finished }} 件完成 · {{ board.progress.percent }}%</text>
      </view>
      <view class="prob">
        <view class="prow">
          <text class="pk">今日总进度</text>
          <text class="pv">{{ board.progress.finished }}/{{ board.progress.total }}</text>
        </view>
        <view class="meter" style="margin-top: 6px"><view class="fill" :style="{ width: board.progress.percent + '%' }"></view></view>
        <view v-for="t in board.list" :key="'row' + t.id" class="prow">
          <text class="pk">{{ t.est_minutes }} 分钟 · {{ t.title }}</text>
          <text class="pv">{{ t.status === 2 ? '已完成' : (t.remind_time || '待开始') }}</text>
        </view>
      </view>

      <view class="focus-tip" style="margin-top: 11px">
        <view class="sp"><xt-icon name="i-spark" /></view>
        <text class="p">先做最小的那一步：把「完成任务」换成「打开文件」。</text>
      </view>

      <view v-if="!loading && !board.list.length" class="mem-hero" style="margin-top: 12px; padding: 22px 14px; text-align: center">
        <view style="font-size: 30px">🌤️</view>
        <view class="t" style="margin-top: 8px">今天还没有安排</view>
        <view class="m">先坐下，剩下的我们一起拆</view>
        <view class="fbtn main" style="margin-top: 12px" @click="goHome"><text>去拆解一个任务</text></view>
      </view>

      <view style="height: 24px"></view>
    </scroll-view>
  </view>
</template>

<script>
/**
 * 今日待办看板
 * -------------------------------
 * - 今日总进度条；上午/下午分组；子步骤展开勾选完成
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      board: { date: '', list: [], progress: { finished: 0, total: 0, percent: 0 } },
      loading: false,
      refreshing: false
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    /** 按 remind_time（有则上午<12:00 否则下午）与来源时段分组 */
    groups() {
      const am = [], pm = []
      for (const t of this.board.list) {
        const rt = (t.remind_time || '').slice(0, 5)
        const hour = rt ? parseInt(rt.split(':')[0], 10) : NaN
        if (!isNaN(hour) && hour < 12) am.push(t)
        else pm.push(t)
      }
      return [{ key: 'am', label: '上午', list: am }, { key: 'pm', label: '下午', list: pm }]
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() { this.load() },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await focusApi.getTasks()
        if (res && res.code === 200) {
          const data = res.data
          data.list = (data.list || []).map(t => Object.assign({ _expanded: false }, t))
          this.board = data
        }
      } catch (e) { /* request 层已提示 */ } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onRefresh() {
      this.refreshing = true
      this.load()
    },
    toggleExpand(t) { t._expanded = !t._expanded },

    /** 勾选任务整体完成/取消 */
    async toggleTask(t) {
      const next = t.status === 2 ? 0 : 2
      try {
        await focusApi.setTaskStatus(t.id, next)
        t.status = next
        this.load()
      } catch (e) { /* noop */ }
    },

    /** 勾选子步骤 → finishStep 推进 + AI 鼓励 */
    async finishStep(t, s) {
      if (s.is_finished) return
      try {
        const res = await focusApi.finishStep(s.id)
        if (res && res.code === 200) {
          s.is_finished = true
          const cheer = (res.data && res.data.cheer) || ''
          if (cheer) uni.showToast({ title: cheer, icon: 'none', duration: 2200 })
          this.load()
        }
      } catch (e) { /* noop */ }
    },

    async removeTask(t) {
      uni.showModal({
        title: '删除任务',
        content: '删除后子步骤、提醒、专注记录一并清除，确定吗？',
        success: async (r) => {
          if (!r.confirm) return
          await focusApi.deleteTask(t.id).catch(() => {})
          this.load()
        }
      })
    },

    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goHome() { uni.navigateTo({ url: '/pages/focus/focus-home' }) },
    goPlan() { uni.navigateTo({ url: '/pages/focus/focus-plan' }) }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿页头右侧只有 + 号，这里并排放返回键以保留返回能力 */
.xt-page.xt-s49 .hbtns {
  display: flex;
  gap: 7px;
  flex-shrink: 0;
}

/* 迷你进度环 44px + 内圈 34px */
.xt-page.xt-s49 .fring {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.xt-page.xt-s49 .fring-in {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(248, 244, 236, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 900;
  color: var(--v7-green);
}

/* 看板卡片：设计稿只有标题，这里补勾选/子步骤/删除的可交互细节 */
.xt-page.xt-s49 .bwrap {
  display: block;
}
.xt-page.xt-s49 .card2.bcard {
  padding: 6px 7px;
}
.xt-page.xt-s49 .card2.doing {
  box-shadow: 0 0 0 1.5px #8FB79E;
}
.xt-page.xt-s49 .card2.wdone {
  background: rgba(248, 244, 236, 0.9);
}
.xt-page.xt-s49 .card2.wdone .bt {
  color: #8E9A91;
  text-decoration: line-through;
}
.xt-page.xt-s49 .card2.add {
  border: 1px dashed #D3DBD7;
  color: #AEB6AE;
  text-align: center;
}
.xt-page.xt-s49 .card2.hint {
  color: #BFC7BF;
  font-size: 6.5px;
  text-align: center;
}
.xt-page.xt-s49 .brow {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}
.xt-page.xt-s49 .bcheck {
  width: 11px;
  height: 11px;
  margin-top: 1px;
  border-radius: 4px;
  border: 1px solid #B5C7BF;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.xt-page.xt-s49 .bcheck.on {
  background: var(--v7-green);
  border-color: var(--v7-green);
}
.xt-page.xt-s49 .bcheck.sm {
  width: 10px;
  height: 10px;
  margin-top: 0;
  border-radius: 3px;
}
.xt-page.xt-s49 .bt {
  flex: 1;
  font-size: 7.4px;
  line-height: 1.4;
  color: #22302A;
}
.xt-page.xt-s49 .bm {
  margin-top: 2px;
  font-size: 6px;
  color: #AEB6AE;
}
.xt-page.xt-s49 .bsteps {
  margin-top: 5px;
  padding-top: 4px;
  border-top: 1px solid var(--v7-line);
}
.xt-page.xt-s49 .bstep {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 0;
}
.xt-page.xt-s49 .bk {
  font-size: 5.5px;
  line-height: 1;
  color: #4B5A51;
}
.xt-page.xt-s49 .bcheck.on .bk {
  color: #FFFDFA;
}
.xt-page.xt-s49 .bst {
  flex: 1;
  font-size: 6.5px;
  color: #4B5A51;
}
.xt-page.xt-s49 .bst.on {
  color: #AEB6AE;
  text-decoration: line-through;
}
.xt-page.xt-s49 .bdel {
  margin-top: 5px;
  text-align: right;
  font-size: 6px;
  color: #B8874E;
}

/* 设计稿 .prow 未在共享样式中定义，这里补等价规则 */
.xt-page.xt-s49 .prob .prow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 8px;
  color: #6A776E;
}
.xt-page.xt-s49 .prob .pk {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.xt-page.xt-s49 .prob .pv {
  flex-shrink: 0;
  margin-left: 6px;
  font-size: 7.5px;
  font-weight: 900;
  color: var(--v7-green);
}

/* 设计稿 .meter 依赖 i 元素，改用等价 class */
.xt-page.xt-s49 .meter .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #A9C6B4, #24493A);
}

.xt-page.xt-s49 .focus-tip .sp {
  width: 26px;
  height: 26px;
  border-radius: 9px;
  background: rgba(248, 244, 236, 0.95);
  color: var(--v7-green);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
