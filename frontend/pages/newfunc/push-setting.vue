<template>
  <view class="xt-page xt-s57">
    <view class="body">
      <view class="chat-head" style="padding:2px 2px 12px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">推送设置</view>
          <view class="chat-st">我们尽量少打扰你</view>
        </view>
        <view class="icon-btn"></view>
      </view>

      <view class="mem-hero" style="padding:13px">
        <view style="display:flex;align-items:baseline;justify-content:space-between">
          <text style="font-size:9px;font-weight:900">每天最多推送</text>
          <text style="font-size:11px;font-weight:900;color:var(--v7-green)">{{ dailyLimit }} 条</text>
        </view>
        <view class="meter" style="margin-top:8px">
          <view class="meter-i" :style="{ width: dailyPercent + '%' }"></view>
        </view>
        <view style="display:flex;justify-content:space-between;margin-top:5px;font-size:6.5px;color:#BFC7BF">
          <text>1 条</text><text>5 条</text>
        </view>
      </view>

      <view class="set-row" style="margin-top:8px">
        <view class="si tint-sand"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">消息频率</view>
          <view class="m">少一点，还是多听她说</view>
        </view>
        <view class="chips" style="margin:0">
          <text
            class="chip"
            :class="{ on: form.ai_frequency === 'low' }"
            @click="save({ ai_frequency: 'low' })"
          >少</text>
          <text
            class="chip"
            :class="{ on: form.ai_frequency === 'medium' }"
            @click="save({ ai_frequency: 'medium' })"
          >适中</text>
          <text
            class="chip"
            :class="{ on: form.ai_frequency === 'high' }"
            @click="save({ ai_frequency: 'high' })"
          >多</text>
        </view>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">静默时段</text><text class="s">这期间完全不打扰</text></view>
      <view class="set-row" @click="save({ quiet_enabled: !form.quiet_enabled })">
        <view class="si tint-blue"><xt-icon name="i-moon" /></view>
        <view class="tx">
          <view class="t">{{ form.quiet_start }} — {{ form.quiet_end }}</view>
          <view class="m">她会在你醒来后再出现</view>
        </view>
        <view class="switch2" :class="{ on: form.quiet_enabled }"></view>
      </view>
      <view v-if="form.quiet_enabled" class="chips" style="margin:0 0 8px">
        <picker mode="time" :value="form.quiet_start" @change="e => save({ quiet_start: e.detail.value })">
          <text class="chip">开始 {{ form.quiet_start }}</text>
        </picker>
        <picker mode="time" :value="form.quiet_end" @change="e => save({ quiet_end: e.detail.value })">
          <text class="chip">结束 {{ form.quiet_end }}</text>
        </picker>
      </view>

      <view class="cal-sec" style="margin-top:13px"><text class="t">哪些可以叫醒你</text><text class="s">按重要程度</text></view>
      <view
        class="set-row"
        :style="!form.push_enabled ? 'opacity:.45' : ''"
        @click="form.push_enabled && save({ ai_push_enabled: !form.ai_push_enabled })"
      >
        <view class="si tint-green"><xt-icon name="i-heart" /></view>
        <view class="tx">
          <view class="t">她主动发来的消息</view>
          <view class="m">每天最多 {{ dailyLimit }} 条</view>
        </view>
        <view class="switch2" :class="{ on: form.ai_push_enabled }"></view>
      </view>
      <view
        class="set-row"
        :style="!form.push_enabled ? 'opacity:.45' : ''"
        @click="form.push_enabled && save({ checkin_push_enabled: !form.checkin_push_enabled })"
      >
        <view class="si tint-peach"><xt-icon name="i-calendar" /></view>
        <view class="tx">
          <view class="t">打卡与专注提醒</view>
          <view class="m">按你设定的时间</view>
        </view>
        <view class="switch2" :class="{ on: form.checkin_push_enabled }"></view>
      </view>
      <view v-if="form.checkin_push_enabled" class="chips" style="margin:0 0 8px 50px">
        <picker mode="time" :value="form.checkin_push_time" @change="e => save({ checkin_push_time: e.detail.value })">
          <text class="chip">提醒时间 {{ form.checkin_push_time }}</text>
        </picker>
      </view>
      <view
        class="set-row"
        :style="!form.push_enabled ? 'opacity:.45' : ''"
        @click="form.push_enabled && save({ todo_push_enabled: !form.todo_push_enabled })"
      >
        <view class="si tint-sand"><xt-icon name="i-clock" /></view>
        <view class="tx">
          <view class="t">待办到期提醒</view>
          <view class="m">日程开始前按提前量推送</view>
        </view>
        <view class="switch2" :class="{ on: form.todo_push_enabled }"></view>
      </view>
      <view
        class="set-row"
        :style="!form.push_enabled ? 'opacity:.45' : ''"
        @click="form.push_enabled && save({ group_push_enabled: !form.group_push_enabled })"
      >
        <view class="si tint-green"><xt-icon name="i-chat" /></view>
        <view class="tx">
          <view class="t">群聊消息提醒</view>
          <view class="m">伙伴群里有人说话时提醒你</view>
        </view>
        <view class="switch2" :class="{ on: form.group_push_enabled }"></view>
      </view>
      <view
        class="set-row"
        :style="!form.push_enabled ? 'opacity:.45' : ''"
        @click="form.push_enabled && saveAuth(!form.diary_read_auth)"
      >
        <view class="si tint-purple"><xt-icon name="i-moments" /></view>
        <view class="tx">
          <view class="t">情绪日历授权</view>
          <view class="m">允许她读取你的情绪日历，让陪伴更懂你</view>
        </view>
        <view class="switch2" :class="{ on: form.diary_read_auth }"></view>
      </view>
      <view class="set-row" @click="save({ push_enabled: !form.push_enabled })">
        <view class="si" style="background:#F5F2EF;color:#C08A56"><xt-icon name="i-bell" /></view>
        <view class="tx">
          <view class="t">系统推送</view>
          <view class="m">关闭后将不再收到任何通知</view>
        </view>
        <view class="switch2" :class="{ on: form.push_enabled }"></view>
      </view>

      <view class="set-row" @click="sendTest">
        <view class="si tint-green"><xt-icon name="i-send" /></view>
        <view class="tx">
          <view class="t">发送一条测试推送</view>
          <view class="m">试试看，它会以伙伴的语气出现</view>
        </view>
        <text class="v">{{ testing ? '发送中…' : '发送' }}</text>
      </view>

      <view class="quote" style="color:#BFC7BF;margin-top:14px;font-size:8px">少一条推送，多一点想念。</view>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】推送设置页：开关 / 免打扰时段 / AI 消息频率 / 情绪日历授权
 */
import api from '@/api/newfunc'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      form: {
        push_enabled: true,
        checkin_push_enabled: true,
        checkin_push_time: '21:30',
        todo_push_enabled: true,
        ai_push_enabled: true,
        ai_frequency: 'medium',
        quiet_enabled: false,
        quiet_start: '23:00',
        quiet_end: '08:00',
        diary_read_auth: false,
        // 【模块4·群推送】群聊消息提醒开关，默认开启
        group_push_enabled: true
      },
      testing: false
    }
  },
  computed: {
    // 设计稿「每天最多推送」：按消息频率换算
    dailyLimit() {
      return { low: 1, medium: 3, high: 5 }[this.form.ai_frequency] || 3
    },
    dailyPercent() {
      return Math.round((this.dailyLimit / 5) * 100)
    }
  },
  onShow() {
    this.load()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/profile/profile' }) })
    },
    async load() {
      try {
        const res = await api.getPushSetting()
        if (res.data) this.form = { ...this.form, ...res.data }
      } catch (e) { /* request 层已提示 */ }
    },
    async save(patch) {
      this.form = { ...this.form, ...patch }
      try {
        const res = await api.savePushSetting(patch)
        if (res.data) this.form = { ...this.form, ...res.data }
      } catch (e) { /* request 层已提示 */ }
    },
    async saveAuth(v) {
      this.form.diary_read_auth = v
      try {
        await api.diaryAuthorize(v)
        uni.showToast({ title: v ? '已授权' : '已关闭授权', icon: 'success' })
      } catch (e) { /* request 层已提示 */ }
    },
    async sendTest() {
      this.testing = true
      try {
        await api.pushTest()
        uni.showToast({ title: '测试推送已发送', icon: 'success' })
      } catch (e) { /* request 层已提示 */ }
      this.testing = false
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间 */
.xt-page.xt-s57 .body {
  padding-bottom: 24px;
}

/* 设计稿 .meter 依赖 i 元素，改用同名 class 补等价规则 */
.xt-page.xt-s57 .meter .meter-i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9CBFAA, var(--v7-green));
}
</style>
