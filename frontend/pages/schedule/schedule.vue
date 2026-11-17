<template>
  <view class="xt-page xt-s4">
    <view class="body">
      <view class="gcal-head">
        <span class="gcal-back" @click="goBack"><xt-icon name="i-left" /></span>
        <view class="gcal-ht">
          <h2>成长日历</h2>
          <p>{{ currentYear }} 年 {{ currentMonth }} 月 · 第 {{ weekOfMonth }} 周</p>
        </view>
        <span class="gcal-set" @click="toggleAuth"><xt-icon name="i-settings" /></span>
      </view>

      <view class="gcal-hero">
        <view class="gcal-ring" :style="{ '--p': weekPercent + '%' }">
          <view class="gcal-rin">
            <b>{{ $store.state.streakDays || 0 }}</b>
            <span>连续天数</span>
          </view>
        </view>
        <view class="gcal-hx">
          <view class="gcal-hk">本周进度</view>
          <view class="gcal-hv">{{ weekDone }} <em>/ 7 天</em></view>
          <view class="gcal-hbar"><i :style="{ width: weekPercent + '%' }"></i></view>
          <view class="gcal-hf">完成率 <b>{{ weekPercent }}%</b> · 本月 {{ Object.keys(monthMarks).length }} 天</view>
        </view>
      </view>

      <view class="gcal-week">
        <view
          v-for="(d, i) in weekCells"
          :key="'wd' + i"
          class="gcal-d"
          :class="{ ok: d.done, miss: d.miss, on: d.on }"
          @click="selectDate(d)"
        >
          <span>{{ d.label }}</span><b>{{ d.day }}</b><i></i>
        </view>
      </view>

      <view class="gcal-sec">
        <b>{{ selectedDate === todayStr ? '今天，一起做' : selectedDate }}</b>
        <span @click="openCreate">{{ doneCount }} / {{ schedules.length }} 已完成</span>
      </view>

      <view v-for="(s, i) in schedules" :key="s.id" class="gcal-r" @longpress="deleteSchedule(s)">
        <span class="gcal-tm">{{ (s.start_time || '').slice(0, 5) }}</span>
        <span class="gcal-ln" :class="s.is_done ? 'g' : (i % 3 === 1 ? 'b' : 'p')"></span>
        <span class="gcal-tx">
          <b>{{ s.title }}</b>
          <em>{{ s.is_done ? '已完成 · 她记下了' : (s.description || '待开始 · 到点她会来找你') }}</em>
        </span>
        <span class="gcal-ck" :class="s.is_done ? 'done' : 'now'" @click.stop="!s.is_done && completeSchedule(s)">
          <xt-icon :name="s.is_done ? 'i-check' : 'i-clock'" />
        </span>
      </view>

      <view v-if="!schedules.length" class="gcal-r" @click="openCreate">
        <span class="gcal-tm">--:--</span>
        <span class="gcal-ln"></span>
        <span class="gcal-tx">
          <b>这一天还没有安排</b>
          <em>点这里新建 · 或让 AI 排一排</em>
        </span>
        <span class="gcal-ck todo"><xt-icon name="i-plus" /></span>
      </view>

      <view class="gcal-sg">
        <span class="si"><xt-icon name="i-moon" /></span>
        <span class="tx">
          <b>她根据你的睡眠建议</b>
          <em>今晚 22:40 · 睡前放下手机，10 分钟</em>
        </span>
        <span class="add" @click="aiGenerate">加入</span>
      </view>

      <view class="gcal-month">
        <view class="gcal-mh">
          <b>{{ currentMonth }} 月打卡</b>
          <span><i></i>已完成 · 共 {{ Object.keys(monthMarks).length }} 天</span>
        </view>
        <view class="gcal-mg">
          <i v-for="(c, i) in monthCells" :key="'mc' + i" :class="c.cls" @click="selectDate(c)"></i>
        </view>
      </view>

      <view class="gcal-sum">
        <view class="gcal-sh">
          <b><xt-icon name="i-spark" />本周小结</b>
          <span>{{ Object.keys(diaryMarks).length }} 天有记录</span>
        </view>
        <p class="gcal-sp">{{ summaryText }}</p>
        <p class="gcal-sgn">—— {{ $store.state.aiConfig.name || '林夕' }} · {{ selectedDate }}</p>
      </view>
    </view>

    <!-- 新建日程（设计稿外的功能弹层，默认隐藏） -->
    <view class="schedx-mask" v-if="showCreate" @click="showCreate = false">
      <view class="schedx-sheet" @click.stop>
        <view class="schedx-head">
          <text class="schedx-title">新建日程 · {{ selectedDate }}</text>
          <text class="schedx-close" @click="showCreate = false">关闭</text>
        </view>
        <input class="schedx-input" v-model="form.title" placeholder="日程标题（如：一起读 10 页）" />
        <textarea class="schedx-area" v-model="form.description" placeholder="备注（可选）" maxlength="200" />
        <view class="schedx-row">
          <text class="schedx-lab">开始</text>
          <picker mode="time" :value="form.start_time" @change="form.start_time = $event.detail.value">
            <view class="schedx-pick">{{ form.start_time }}</view>
          </picker>
          <text class="schedx-lab">结束</text>
          <picker mode="time" :value="form.end_time" @change="form.end_time = $event.detail.value">
            <view class="schedx-pick">{{ form.end_time }}</view>
          </picker>
        </view>
        <view class="schedx-row">
          <text class="schedx-lab">提醒</text>
          <picker
            mode="selector"
            :range="remindOptions"
            :value="remindValues.indexOf(form.remind_minutes)"
            @change="form.remind_minutes = remindValues[$event.detail.value]"
          >
            <view class="schedx-pick">提前 {{ form.remind_minutes }} 分钟</view>
          </picker>
        </view>
        <view class="schedx-btn" @click="submitCreate">保存日程</view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 【四大新增模块·模块2】日程提醒页
 * 与打卡系统联动:
 *  - 创建日程时可绑定习惯, 完成日程自动触发打卡
 *  - AI生成: 后端读取用户习惯 + 打卡情况生成建议日程
 *  - 提醒扫描: onShow 时调用, AI伙伴到点主动提醒
 */
import scheduleApi from '@/api/schedule'
// 【newfunc 增量】情绪日记日历联动接口（独立模块，只读复用情绪/打卡/待办数据）
import newfuncApi from '@/api/newfunc'

export default {
  data() {
    const sys = uni.getSystemInfoSync()
    const now = new Date()
    const pad = n => String(n).padStart(2, '0')
    return {
      statusBarHeight: sys.statusBarHeight || 20,
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1, // 1-12
      selectedDate: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      todayStr: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      weekNames: ['日', '一', '二', '三', '四', '五', '六'],
      // 该月每天是否有日程(日历圆点)
      monthMarks: {},
      schedules: [],
      showCreate: false,
      form: {
        title: '',
        description: '',
        start_time: '08:00',
        end_time: '09:00',
        remind_minutes: 5
      },
      remindOptions: ['5分钟', '10分钟', '15分钟', '30分钟', '60分钟'],
      remindValues: [5, 10, 15, 30, 60],
      // ===== 【newfunc 增量】情绪日记日历数据 =====
      diaryMarks: {},
      diaryAuth: false,
      dayEmotions: [],
      showSummaryEdit: false,
      summaryDraft: '',
      moodTagOptions: [
        { key: 'happy', label: '开心', emoji: '😄' },
        { key: 'calm', label: '平静', emoji: '😌' },
        { key: 'excited', label: '兴奋', emoji: '🤩' },
        { key: 'tired', label: '疲惫', emoji: '😪' },
        { key: 'sad', label: '低落', emoji: '😢' },
        { key: 'angry', label: '烦躁', emoji: '😠' }
      ],
      moodForm: { mood_tags: [], mood_score: 5, diary_text: '', summary: '', summary_source: '' }
    }
  },
  computed: {
    // 生成日历格子(6行7列, 含前后月空白)
    calendarCells() {
      const y = this.currentYear
      const m = this.currentMonth
      const first = new Date(y, m - 1, 1)
      const firstWeekday = first.getDay()
      const daysInMonth = new Date(y, m, 0).getDate()
      const pad = n => String(n).padStart(2, '0')
      const cells = []
      // 前置空白
      for (let i = 0; i < firstWeekday; i++) cells.push({ day: 0 })
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${y}-${pad(m)}-${pad(d)}`
        cells.push({
          day: d,
          dateStr,
          isToday: dateStr === this.todayStr,
          hasSchedule: !!this.monthMarks[dateStr]
        })
      }
      // 补齐到 42 格
      while (cells.length % 7 !== 0) cells.push({ day: 0 })
      return cells
    },
    // 本周 7 天（周一为起点），用于顶部周条
    weekCells() {
      const labels = ['一', '二', '三', '四', '五', '六', '日']
      const now = new Date()
      const offset = (now.getDay() + 6) % 7
      const pad = n => String(n).padStart(2, '0')
      const cells = []
      for (let i = 0; i < 7; i++) {
        const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - offset + i)
        const dateStr = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
        const done = !!(this.monthMarks[dateStr] || this.diaryMarks[dateStr])
        cells.push({
          label: labels[i],
          day: d.getDate(),
          dateStr,
          done,
          on: dateStr === this.selectedDate,
          miss: !done && dateStr < this.todayStr
        })
      }
      return cells
    },
    weekDone() {
      return this.weekCells.filter(c => c.done).length
    },
    weekPercent() {
      return Math.round((this.weekDone / 7) * 100)
    },
    weekOfMonth() {
      const parts = this.selectedDate.split('-')
      const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
      const offset = (d.getDay() + 6) % 7
      return Math.ceil((offset + d.getDate()) / 7)
    },
    // 月打卡热力格（按本月日程/日记标记着色）
    monthCells() {
      const y = this.currentYear
      const m = this.currentMonth
      const days = new Date(y, m, 0).getDate()
      const pad = n => String(n).padStart(2, '0')
      const cells = []
      for (let d = 1; d <= days; d++) {
        const dateStr = `${y}-${pad(m)}-${pad(d)}`
        let cls = 'l1'
        if (dateStr === this.todayStr) cls = 'td'
        else if (this.monthMarks[dateStr]) cls = 'l3'
        else if (this.diaryMarks[dateStr]) cls = 'l2'
        else if (dateStr < this.todayStr) cls = 'ms'
        cells.push({ day: d, dateStr, cls })
      }
      while (cells.length % 7 !== 0) cells.push({ day: 0, dateStr: '', cls: '' })
      return cells
    },
    doneCount() {
      return this.schedules.filter(s => s.is_done).length
    },
    summaryText() {
      return this.moodForm.summary || '这周的小事都记在这里了。不是你变自律了，是我们把它变简单了。'
    }
  },
  onLoad() {
  },
  // 【newfunc 增量】初始加载情绪区块（不改动 onLoad/onShow 原逻辑）
  mounted() {
    this.loadDiaryMarks()
    this.loadDiaryDay()
  },
  watch: {
    selectedDate() { this.loadDiaryDay() },
    currentMonth() { this.loadDiaryMarks() }
  },
  onShow() {
    this.loadMonthMarks()
    this.loadSchedules()
    this.scanReminders()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },

    // ===== 整月日程标记(日历圆点) =====
    async loadMonthMarks() {
      try {
        const res = await scheduleApi.getList({
          month: `${this.currentYear}-${String(this.currentMonth).padStart(2, '0')}`
        })
        const list = (res && res.data) || []
        const marks = {}
        list.forEach(s => { marks[s.schedule_date] = true })
        this.monthMarks = marks
      } catch (e) {
        // 静默
      }
    },

    // ===== 当日日程列表 =====
    async loadSchedules() {
      try {
        const res = await scheduleApi.getList({ day: this.selectedDate })
        this.schedules = (res && res.data) || []
      } catch (e) {
        this.schedules = []
        uni.showToast({ title: '日程加载失败', icon: 'none' })
      }
    },

    // ===== AI提醒扫描 =====
    async scanReminders() {
      try {
        const res = await scheduleApi.remindScan()
        const list = (res && res.data) || []
        if (list.length > 0) {
          // 展示第一条AI提醒(多条依次toast)
          const first = list[0]
          uni.showModal({
            title: '⏰ AI伙伴提醒',
            content: first.ai_message || `「${first.schedule.title}」时间快到了`,
            showCancel: false,
            confirmText: '知道啦'
          })
        }
      } catch (e) {
        // 静默
      }
    },

    // ===== 日历交互 =====
    changeMonth(delta) {
      let m = this.currentMonth + delta
      let y = this.currentYear
      if (m < 1) { m = 12; y-- }
      if (m > 12) { m = 1; y++ }
      this.currentYear = y
      this.currentMonth = m
      this.loadMonthMarks()
    },
    selectDate(cell) {
      if (!cell.day) return
      this.selectedDate = cell.dateStr
      this.loadSchedules()
    },

    // ==================================================
    // 【newfunc 增量】情绪 · 日记 · 当日总结（绑定 selectedDate）
    // ==================================================
    async loadDiaryMarks() {
      try {
        const month = `${this.currentYear}-${String(this.currentMonth).padStart(2, '0')}`
        const res = await newfuncApi.diaryMonth(month)
        this.diaryMarks = (res && res.data && res.data.marks) || {}
      } catch (e) {
        this.diaryMarks = {}
      }
    },
    async loadDiaryDay() {
      try {
        const res = await newfuncApi.diaryDay(this.selectedDate)
        const data = (res && res.data) || {}
        this.dayEmotions = data.emotions || []
        const d = data.diary || {}
        this.moodForm = {
          mood_tags: d.mood_tags || [],
          mood_score: d.mood_score != null ? d.mood_score : 5,
          diary_text: d.diary_text || '',
          summary: d.summary || '',
          summary_source: d.summary_source || ''
        }
        this.showSummaryEdit = false
      } catch (e) {
        this.dayEmotions = []
      }
      try {
        const s = await newfuncApi.getPushSetting()
        this.diaryAuth = !!(s && s.data && s.data.diary_read_auth)
      } catch (e) { /* 静默 */ }
    },
    toggleMoodTag(key) {
      const i = this.moodForm.mood_tags.indexOf(key)
      if (i > -1) this.moodForm.mood_tags.splice(i, 1)
      else if (this.moodForm.mood_tags.length < 6) this.moodForm.mood_tags.push(key)
    },
    async saveMood() {
      try {
        await newfuncApi.diarySave({
          date: this.selectedDate,
          mood_tags: this.moodForm.mood_tags,
          mood_score: this.moodForm.mood_score,
          diary_text: this.moodForm.diary_text
        })
        uni.showToast({ title: '已保存到 ' + this.selectedDate, icon: 'success' })
        this.loadDiaryMarks()
      } catch (e) { /* request 层已提示 */ }
    },
    async genAiSummary() {
      uni.showLoading({ title: 'AI 正在回顾这一天…' })
      try {
        await newfuncApi.diaryAiSummary(this.selectedDate)
        uni.hideLoading()
        uni.showToast({ title: '总结已生成', icon: 'success' })
        this.loadDiaryDay()
      } catch (e) {
        uni.hideLoading()
      }
    },
    openSummaryEdit() {
      this.summaryDraft = this.moodForm.summary
      this.showSummaryEdit = true
    },
    async saveSummaryManual() {
      try {
        await newfuncApi.diarySaveSummary(this.selectedDate, this.summaryDraft)
        this.showSummaryEdit = false
        uni.showToast({ title: '总结已保存', icon: 'success' })
        this.loadDiaryDay()
      } catch (e) { /* request 层已提示 */ }
    },
    async toggleAuth() {
      try {
        await newfuncApi.diaryAuthorize(!this.diaryAuth)
        this.diaryAuth = !this.diaryAuth
        uni.showToast({ title: this.diaryAuth ? '已授权 AI 读取情绪日历' : '已关闭授权', icon: 'none' })
      } catch (e) { /* request 层已提示 */ }
    },

    // ===== AI 生成建议日程 =====
    async aiGenerate() {
      uni.showLoading({ title: 'AI伙伴思考中...' })
      try {
        const res = await scheduleApi.aiGenerate(this.selectedDate)
        uni.hideLoading()
        const data = res.data || {}
        if (data.list && data.list.length > 0) {
          uni.showToast({ title: data.tip || '已生成建议日程', icon: 'success' })
        } else {
          uni.showToast({ title: '今天都安排好啦', icon: 'none' })
        }
        this.loadMonthMarks()
        this.loadSchedules()
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: (e && e.message) || '生成失败', icon: 'none' })
      }
    },

    // ===== 新建日程 =====
    openCreate() {
      this.form = {
        title: '',
        description: '',
        start_time: '08:00',
        end_time: '09:00',
        remind_minutes: 5
      }
      this.showCreate = true
    },
    async submitCreate() {
      if (!this.form.title.trim()) {
        uni.showToast({ title: '请填写日程标题', icon: 'none' })
        return
      }
      try {
        await scheduleApi.create({
          title: this.form.title.trim(),
          description: this.form.description,
          schedule_date: this.selectedDate,
          start_time: this.form.start_time,
          end_time: this.form.end_time,
          remind_minutes: this.form.remind_minutes
        })
        this.showCreate = false
        uni.showToast({ title: '已创建', icon: 'success' })
        this.loadMonthMarks()
        this.loadSchedules()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '创建失败', icon: 'none' })
      }
    },

    // ===== 完成日程 =====
    async completeSchedule(s) {
      try {
        const res = await scheduleApi.complete(s.id)
        const data = (res && res.data) || {}
        if (data.auto_checkin) {
          uni.showToast({ title: '完成! 已自动打卡 ✓', icon: 'none' })
          // 【修复】自动打卡后同步行走地图计数，否则「累计打卡/到站」永远显示 0
          this.$store.commit('addWalkStep', {
            steps: 1, type: 'habit', description: s.title || '日程完成'
          })
        } else {
          uni.showToast({ title: '已完成 ✓', icon: 'success' })
        }
        this.loadSchedules()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '操作失败', icon: 'none' })
      }
    },

    // ===== 删除日程 =====
    async deleteSchedule(s) {
      uni.showModal({
        title: '删除日程',
        content: `确定删除「${s.title}」吗?`,
        success: async (r) => {
          if (r.confirm) {
            try {
              await scheduleApi.remove(s.id)
              uni.showToast({ title: '已删除', icon: 'none' })
              this.loadMonthMarks()
              this.loadSchedules()
            } catch (e) {
              uni.showToast({ title: '删除失败', icon: 'none' })
            }
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 进度环：用 conic-gradient 等价实现设计稿的 SVG 圆环 */
.xt-page.xt-s4 .gcal-ring::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(#e9c79c 0 var(--p, 78%), rgba(255, 253, 250, 0.16) var(--p, 78%) 100%);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px));
}

/* 新建日程弹层 */
.xt-page.xt-s4 .schedx-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 99;
  background: rgba(34, 48, 42, 0.42);
  display: flex;
  align-items: flex-end;
}
.xt-page.xt-s4 .schedx-sheet {
  width: 100%;
  padding: 16px 18px 22px;
  border-radius: 22px 22px 0 0;
  background: #fffcf6;
}
.xt-page.xt-s4 .schedx-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.xt-page.xt-s4 .schedx-title {
  font-size: 12px;
  font-weight: 900;
  color: #22302a;
}
.xt-page.xt-s4 .schedx-close {
  font-size: 9px;
  color: #a6b0a9;
}
.xt-page.xt-s4 .schedx-input {
  width: 100%;
  height: 38px;
  margin-top: 12px;
  padding: 0 12px;
  border-radius: 12px;
  background: #f5f3ec;
  font-size: 10px;
}
.xt-page.xt-s4 .schedx-area {
  width: 100%;
  height: 62px;
  margin-top: 8px;
  padding: 9px 12px;
  border-radius: 12px;
  background: #f5f3ec;
  font-size: 10px;
}
.xt-page.xt-s4 .schedx-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}
.xt-page.xt-s4 .schedx-lab {
  font-size: 8px;
  color: #8e9a91;
}
.xt-page.xt-s4 .schedx-pick {
  padding: 7px 11px;
  border-radius: 10px;
  background: #f5f3ec;
  font-size: 9px;
  color: #22302a;
}
.xt-page.xt-s4 .schedx-btn {
  margin-top: 16px;
  height: 42px;
  border-radius: 14px;
  text-align: center;
  line-height: 42px;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.6px;
  color: #fffcf6;
  background: linear-gradient(135deg, #44705a, #2e5643);
}
</style>
