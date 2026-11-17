<template>
  <view class="xt-page xt-s50">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">专注计划</view>
          <view class="page-sub">先定一个愿意投入的节奏，不用排满</view>
        </view>
        <view class="hbtns">
          <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
          <view class="icon-btn" @click="editPlan"><xt-icon name="i-edit" /></view>
        </view>
      </view>

      <view class="mem-hero" style="padding: 13px">
        <view style="display: flex; align-items: baseline; justify-content: space-between">
          <text style="font-size: 9px; font-weight: 900">每天愿意投入</text>
          <text style="font-size: 15px; font-weight: 900; color: #24493A">{{ form.daily_minutes }}<text style="font-size: 7.5px; color: #A2AAA3; font-weight: 400"> 分钟</text></text>
        </view>
        <view class="meter" style="margin-top: 7px">
          <view class="fill" :style="{ width: (form.daily_minutes / 120 * 100) + '%' }"></view>
        </view>
        <view style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 6.5px; color: #BFC7BF">
          <text>30 分钟</text>
          <text>{{ form.exam_date || '考试日期待定' }}</text>
          <text>120 分钟</text>
        </view>
      </view>

      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">每天的安排</text>
        <text class="s">点一下就好</text>
      </view>
      <view
        v-for="o in [{ m: 30, n: '轻一点的一周', d: '适合最近有点累、但不想断掉的你' }, { m: 45, n: '稳步推进', d: '有明确的截止日期时选这个' }, { m: 60, n: '保持节奏', d: '状态不错，想把进度往前推' }, { m: 120, n: '冲刺一下', d: '只剩几天，需要集中补一补' }]"
        :key="o.m"
        class="plan"
        :class="{ on: form.daily_minutes === o.m }"
        @click="form.daily_minutes = o.m"
      >
        <text class="tag2" v-if="o.m === 45">推荐</text>
        <view class="n">{{ o.n }}</view>
        <view class="p">{{ o.m }} 分钟 × 每天</view>
        <view class="d">{{ o.d }}</view>
      </view>

      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">你的考试</text>
        <text class="s">AI 帮你拆</text>
      </view>
      <view class="fcard">
        <view class="frow">
          <text class="fl">考试类型</text>
          <input v-model="form.exam_type" class="fi" placeholder="如：考研 / 教资 / 期末" />
        </view>
        <view class="frow">
          <text class="fl">考试日期</text>
          <picker mode="date" :value="form.exam_date" @change="onDate">
            <view class="fi pick">
              <text :class="{ ph: !form.exam_date }">{{ form.exam_date || '选择考试日期' }}</text>
            </view>
          </picker>
        </view>
        <view class="frow">
          <text class="fl">当前薄弱点</text>
          <input v-model="form.weakness" class="fi" placeholder="如：数学大题 / 听力" />
        </view>
        <view class="frow">
          <text class="fl">每日提醒时间（可选）</text>
          <picker mode="time" :value="form.remind_time" @change="onTime">
            <view class="fi pick">
              <text :class="{ ph: !form.remind_time }">{{ form.remind_time || '选择提醒时间' }}</text>
            </view>
          </picker>
        </view>
      </view>

      <view class="auth-btn" :class="{ busy: generating }" @click="generate">
        <text>{{ generating ? 'AI 正在规划…' : (generated ? '重新生成' : '生成备考计划') }}</text>
      </view>
      <view class="gen-tip">生成后自动拆解为每日待办{{ form.remind_time ? '，并批量设置定时提醒' : '' }}</view>

      <view v-if="phases.length" class="cal-sec" style="margin-top: 13px">
        <text class="t">分阶段安排</text>
        <text class="s">{{ phases.length }} 个阶段</text>
      </view>
      <view v-for="(p, pi) in phases" :key="pi" class="plan">
        <view class="n">{{ p.name }}</view>
        <view class="d">{{ p.days.length }} 项每日任务</view>
        <view v-for="(d, di) in p.days" :key="di" class="drow">
          <view class="ddot ok"></view>
          <text class="dt">{{ d.title }}</text>
          <text class="dm">{{ d.tag }} · {{ d.minutes }}′</text>
        </view>
      </view>

      <view v-if="generated" class="mem-hero" style="margin-top: 12px">
        <view class="t">已生成 {{ taskCount }} 条每日待办{{ remindTip }}</view>
        <view class="m">每天只放做得完的量，剩下的时间留给生活</view>
        <view class="fbtn main" style="margin-top: 10px" @click="goBoard"><text>查看今日看板</text></view>
      </view>

      <view style="height: 24px"></view>
    </view>
  </view>
</template>

<script>
/**
 * AI 备考计划生成 & 详情
 * -------------------------------
 * 表单（考试类型/日期/薄弱点/每日时长）→ POST /focus/plan/generate
 * AI 输出分阶段计划 → 自动落成 focus_task（批量），可批量设置提醒
 * 「重新生成」随时可点（后端限流 5 次/10 分钟）
 */
import focusApi from '@/api/focus'

export default {
  data() {
    return {
      statusBarHeight: 20,
      form: { exam_type: '', exam_date: '', weakness: '', daily_minutes: 45, remind_time: '' },
      generating: false,
      generated: false,
      phases: [],
      taskCount: 0
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    remindTip() { return this.form.remind_time ? '，提醒时间每日 ' + this.form.remind_time : '' }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    // 恢复上次填写的计划参数，省得每次重新输入
    try {
      const saved = uni.getStorageSync('focus_plan_form')
      if (saved && typeof saved === 'object') this.form = Object.assign(this.form, saved)
    } catch (e) { /* 静默 */ }
  },
  methods: {
    onDate(e) { this.form.exam_date = e.detail.value; this.persistForm() },
    onTime(e) { this.form.remind_time = e.detail.value; this.persistForm() },
    editPlan() {
      const options = [
        { m: 30, n: '轻一点的一周' },
        { m: 45, n: '稳步推进' },
        { m: 60, n: '保持节奏' },
        { m: 120, n: '冲刺一下' }
      ]
      uni.showActionSheet({
        itemList: options.map(o => `${o.n} · ${o.m} 分钟`),
        success: (res) => {
          const picked = options[res.tapIndex]
          if (!picked) return
          this.form.daily_minutes = picked.m
          this.persistForm()
          uni.showToast({ title: '已更新每日投入，重新生成后生效', icon: 'none', duration: 2000 })
        }
      })
    },
    persistForm() {
      try { uni.setStorageSync('focus_plan_form', this.form) } catch (e) { /* 静默 */ }
    },
    async generate() {
      if (!this.form.exam_type) { uni.showToast({ title: '先填一下考试类型', icon: 'none' }); return }
      if (this.generating) return
      this.generating = true
      this.persistForm()
      try {
        const res = await focusApi.generatePlan({
          exam_type: this.form.exam_type,
          exam_date: this.form.exam_date,
          weakness: this.form.weakness,
          daily_minutes: this.form.daily_minutes,
          remind_time: this.form.remind_time
        })
        if (res && res.code === 200) {
          const data = res.data
          this.phases = data.phases || []
          this.taskCount = data.task_count || 0
          this.generated = true
          uni.showToast({
            title: data.source === 'ai' ? '计划已生成' : '已生成通用计划（AI 通道繁忙）',
            icon: 'none', duration: 2200
          })
        }
      } catch (e) { /* request 层已提示 */ } finally {
        this.generating = false
      }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goBoard() { uni.navigateTo({ url: '/pages/focus/focus-board' }) }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿页头右侧只有编辑图标，这里并排放返回键以保留返回能力 */
.xt-page.xt-s50 .hbtns {
  display: flex;
  gap: 7px;
  flex-shrink: 0;
}

/* 设计稿 .meter 依赖 i 元素，改用等价 class */
.xt-page.xt-s50 .meter .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #A9C6B4, #24493A);
}

/* 表单卡：沿用设计稿白卡 + 细分隔线 */
.xt-page.xt-s50 .fcard {
  padding: 2px 12px;
  background: var(--v7-card);
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s50 .frow {
  padding: 9px 0;
}
.xt-page.xt-s50 .frow + .frow {
  border-top: 1px solid var(--v7-line);
}
.xt-page.xt-s50 .fl {
  display: block;
  font-size: 7px;
  font-weight: 900;
  letter-spacing: 0.4px;
  color: #8E9A91;
}
.xt-page.xt-s50 .fi {
  display: flex;
  align-items: center;
  width: 100%;
  height: 30px;
  margin-top: 5px;
  padding: 0 10px;
  box-sizing: border-box;
  border-radius: 10px;
  background: rgba(248, 244, 236, 0.92);
  font-size: 9px;
  color: #22302A;
}
.xt-page.xt-s50 .fi .ph {
  color: #C2CBC4;
}
.xt-page.xt-s50 uni-picker {
  display: block;
  width: 100%;
}

.xt-page.xt-s50 .auth-btn.busy {
  opacity: 0.6;
}
.xt-page.xt-s50 .gen-tip {
  margin-top: 7px;
  text-align: center;
  font-size: 7.5px;
  line-height: 1.6;
  color: #AEB6AE;
}

/* 阶段内的每日任务行 */
.xt-page.xt-s50 .drow {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 7px;
  padding-top: 7px;
  border-top: 1px solid var(--v7-line);
}
.xt-page.xt-s50 .ddot {
  margin-top: 4px;
  flex-shrink: 0;
}
.xt-page.xt-s50 .dt {
  flex: 1;
  font-size: 7.5px;
  line-height: 1.5;
  color: #4B5A51;
}
.xt-page.xt-s50 .dm {
  flex-shrink: 0;
  margin-left: 6px;
  font-size: 6.5px;
  color: #AEB6AE;
}
</style>
