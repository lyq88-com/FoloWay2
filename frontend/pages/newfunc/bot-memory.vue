<template>
  <view class="xt-page xt-s61">
    <view class="body">
      <!-- 页头 -->
      <view class="chat-head" style="padding: 2px 2px 12px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">{{ name }}的记忆</view>
          <view class="chat-st">{{ total }} 件事 · 只在这段关系里</view>
        </view>
        <view class="icon-btn" @click="confirmReset"><xt-icon name="i-settings" /></view>
      </view>

      <!-- 说明 -->
      <view class="mem-hero">
        <view class="t">她把你放在心上的方式</view>
        <view class="m">记忆只用于让对话更连贯，不会用于推荐或分享。你可以随时删掉任何一条。</view>
      </view>

      <!-- 未选择伙伴：兜底提示，避免空页面 -->
      <view v-if="invalidBot" class="mem-no-bot">
        <view class="mi tint-sand"><xt-icon name="i-brain" /></view>
        <view class="tx">
          <view class="t">请先选择一位伙伴</view>
          <view class="m">记忆是和某个伙伴一对一的，先去伙伴列表选一位吧。</view>
        </view>
        <view class="auth-btn mem-no-bot-btn" @click="goManage">去选择伙伴</view>
      </view>

      <!-- 类型筛选 -->
      <view v-if="!invalidBot" class="chips" style="margin: 10px 0 0">
        <view class="chip" :class="{ on: filter === '' }" @click="setFilter('')">全部</view>
        <view class="chip" :class="{ on: filter === 'fact' }" @click="setFilter('fact')">事实</view>
        <view class="chip" :class="{ on: filter === 'preference' }" @click="setFilter('preference')">偏好</view>
        <view class="chip" :class="{ on: filter === 'emotion' }" @click="setFilter('emotion')">情绪</view>
        <view class="chip" :class="{ on: filter === 'dialogue' }" @click="setFilter('dialogue')">对话</view>
      </view>

      <block v-if="!invalidBot">
      <!-- TA 记住的 -->
      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">她记住的</text>
        <text class="s">来自你们的对话</text>
      </view>

      <view class="mem-item" v-for="m in memories" :key="m.id">
        <view class="mi" :class="memTints[m.mem_type] || 'tint-green'">
          <xt-icon :name="memIcons[m.mem_type] || 'i-brain'" />
        </view>
        <view class="tx">
          <view class="t">{{ m.content }}</view>
          <view class="m">{{ typeLabel(m.mem_type) }} · 重要度 {{ m.importance }}</view>
          <view class="d">{{ m.created_at }}</view>
        </view>
        <text class="v" @click="confirmDelete(m)">删除</text>
      </view>

      <view class="mem-item" v-if="memories.length === 0">
        <view class="mi tint-sand"><xt-icon name="i-brain" /></view>
        <view class="tx">
          <view class="t">TA 还没有记住什么</view>
          <view class="m">聊天中提到的喜好、目标、情绪会自动沉淀为记忆</view>
        </view>
      </view>

      <!-- 你希望她记住的 -->
      <view class="cal-sec" style="margin-top: 13px">
        <text class="t">你希望她记住的</text>
        <text class="s">由你写下</text>
      </view>

      <!-- 【修复】原来开关只是静态样式，现在接 /user/prefs 的真实偏好（allow_proactive_msg） -->
      <view class="set-row" style="margin-top: 10px" @click="toggleRecall">
        <view class="si tint-green"><xt-icon name="i-brain" /></view>
        <view class="tx">
          <view class="t">允许她主动提起过去</view>
          <view class="m">偶尔说“上次你说…”，会更像真的记得</view>
        </view>
        <view class="switch2" :class="{ on: recallOn }"></view>
      </view>

      <!-- 手动写入记忆 -->
      <view v-if="!showForm" class="auth-btn" style="margin-top: 11px" @click="showForm = true">再告诉她一件事</view>
      <view v-else class="mem-write">
        <textarea
          class="mem-write-input"
          v-model="newContent"
          placeholder="写下你希望她记住的事，比如：我对芒果过敏 / 我最近在准备考试"
          maxlength="500"
          auto-height
        />
        <view class="chips mem-write-types">
          <view
            v-for="t in writeTypes"
            :key="t.value"
            class="chip"
            :class="{ on: newType === t.value }"
            @click="newType = t.value"
          >{{ t.label }}</view>
        </view>
        <view class="mem-write-actions">
          <view class="mem-write-cancel" @click="cancelWrite">取消</view>
          <view
            class="auth-btn mem-write-submit"
            :class="{ disabled: !canSubmit || submitting }"
            @click="submitMemory"
          >{{ submitting ? '保存中…' : '保存这条记忆' }}</view>
        </view>
      </view>
      </block>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】伙伴记忆管理：查看 / 删除单条 / 重置（只影响该 bot_id）
 */
import api from '@/api/newfunc'
import settingsExtra from '@/api/settings-extra'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const TYPE_LABELS = {
  fact: '事实', preference: '偏好', emotion: '情绪', dialogue: '对话'
}

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      botId: 0,
      name: '伙伴',
      memories: [],
      total: 0,
      filter: '',
      page: 1,
      // 【修复】主动提起过去的开关：真实读写用户偏好 allow_proactive_msg
      recallOn: true,
      savingRecall: false,
      // 手动写入记忆表单
      showForm: false,
      newContent: '',
      newType: 'fact',
      submitting: false,
      // botId 无效（未选择伙伴）时的兜底
      invalidBot: false
    }
  },
  computed: {
    memTints() {
      return { fact: 'tint-blue', preference: 'tint-peach', emotion: 'tint-green', dialogue: 'tint-sand' }
    },
    memIcons() {
      return { fact: 'i-book', preference: 'i-heart', emotion: 'i-moon', dialogue: 'i-chat' }
    },
    writeTypes() {
      return [
        { value: 'fact', label: '事实' },
        { value: 'preference', label: '偏好' },
        { value: 'emotion', label: '情绪' },
        { value: 'dialogue', label: '对话' }
      ]
    },
    canSubmit() {
      return (this.newContent || '').trim().length > 0 && !this.submitting
    }
  },
  onLoad(opt) {
    this.botId = Number(opt.id || 0)
    // uni-app H5 路由解析 query 时已解码一次；这里再兜底解码，失败则原样使用
    const rawName = opt.name || '伙伴'
    try {
      this.name = decodeURIComponent(rawName)
    } catch (e) {
      this.name = rawName
    }
    this.invalidBot = !this.botId
  },
  onShow() {
    this.page = 1
    this.load()
    this.loadPrefs()
  },
  methods: {
    /** 读取偏好：allow_proactive_msg = 是否允许 AI 主动提起过去 */
    async loadPrefs() {
      // 先用本地缓存（与设置页共用同一个 key），游客也能用
      this.recallOn = uni.getStorageSync('pref_allow_proactive_msg') !== 'false'
      try {
        const res = await settingsExtra.getPrefs()
        const d = (res && res.data) || {}
        if (typeof d.allow_proactive_msg === 'number') {
          this.recallOn = d.allow_proactive_msg === 1
          uni.setStorageSync('pref_allow_proactive_msg', this.recallOn ? 'true' : 'false')
        }
      } catch (e) {
        // 未登录/游客：保留本地缓存值，不影响记忆列表
      }
    },
    /** 切换开关：本地立即生效 + 写回 /user/prefs */
    async toggleRecall() {
      if (this.savingRecall) return
      const next = !this.recallOn
      this.recallOn = next
      uni.setStorageSync('pref_allow_proactive_msg', next ? 'true' : 'false')
      uni.showToast({
        title: next ? '已开启，她会偶尔提起过去' : '已关闭，她不会再主动提起',
        icon: 'none'
      })
      this.savingRecall = true
      try {
        await settingsExtra.savePrefs({ allow_proactive_msg: next ? 1 : 0 })
      } catch (e) {
        console.warn('[bot-memory] 保存主动提起开关失败（已存本地）:', e)
      } finally {
        this.savingRecall = false
      }
    },
    goBack() {
      uni.navigateBack()
    },
    goManage() {
      uni.redirectTo({ url: '/pages/newfunc/bot-manage' })
    },
    typeLabel(t) {
      return TYPE_LABELS[t] || '记忆'
    },
    setFilter(f) {
      this.filter = f
      this.page = 1
      this.load()
    },
    async load() {
      if (this.invalidBot) {
        this.memories = []
        this.total = 0
        return
      }
      try {
        const res = await api.botMemories(this.botId, {
          mem_type: this.filter, page: this.page, size: 30
        })
        const data = res.data || {}
        this.total = data.total || 0
        this.memories = data.list || []
      } catch (e) {
        this.memories = []
      }
    },
    confirmDelete(m) {
      uni.showModal({
        title: '删除这条记忆',
        content: m.content.slice(0, 40),
        confirmColor: '#E57373',
        success: async (r) => {
          if (!r.confirm) return
          try {
            await api.botMemoryDelete(this.botId, m.id)
            this.memories = this.memories.filter(x => x.id !== m.id)
            this.total = Math.max(0, this.total - 1)
            uni.showToast({ title: '已删除', icon: 'success' })
          } catch (e) { /* request 层已提示 */ }
        }
      })
    },
    confirmReset() {
      uni.showModal({
        title: '重置记忆',
        content: `将清空「${this.name}」的全部 ${this.total} 条记忆，且无法恢复。其他伙伴不受影响。`,
        confirmColor: '#E57373',
        success: async (r) => {
          if (!r.confirm) return
          try {
            await api.botMemoryReset(this.botId)
            uni.showToast({ title: '记忆已重置', icon: 'success' })
            this.load()
          } catch (e) { /* request 层已提示 */ }
        }
      })
    },
    cancelWrite() {
      this.showForm = false
      this.newContent = ''
      this.newType = 'fact'
    },
    async submitMemory() {
      if (!this.canSubmit || this.invalidBot) return
      const content = this.newContent.trim()
      this.submitting = true
      try {
        const res = await api.botMemoryCreate(this.botId, {
          content,
          mem_type: this.newType,
          importance: 5
        })
        const created = res.data && res.data.created
        uni.showToast({
          title: created ? '她记住了' : '这条她已经记得啦',
          icon: 'none'
        })
        this.cancelWrite()
        this.filter = ''
        this.load()
      } catch (e) {
        /* request 层已提示 */
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.xt-page.xt-s61 .body { padding-bottom: calc(24px + env(safe-area-inset-bottom)); }
.xt-page.xt-s61 .mem-item { align-items: flex-start; }
.xt-page.xt-s61 .mem-item .t { font-size: 9px; line-height: 1.5; }
.xt-page.xt-s61 .mem-item .v {
  flex-shrink: 0; padding-top: 1px;
  font-size: 7px; color: #BFC7BF;
}

/* 手动写入记忆表单 */
.mem-write {
  margin-top: 11px;
  padding: 12px;
  border-radius: 14px;
  background: #FFFDFA;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, .10);
}
.mem-write-input {
  width: 100%;
  min-height: 66px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #F4F6F4;
  font-size: 12px;
  line-height: 1.5;
  box-sizing: border-box;
}
.mem-write-types { margin: 9px 0 0; gap: 6px; }
.mem-write-types .chip { font-size: 11px; padding: 5px 12px; }
.mem-write-actions {
  display: flex; align-items: center; gap: 10px; margin-top: 11px;
}
.mem-write-cancel {
  flex: 0 0 auto; font-size: 12px; color: #7C877E; padding: 0 6px;
}
.mem-write-submit { flex: 1; margin-top: 0; }
.mem-write-submit.disabled { opacity: .5; }

/* 未选择伙伴兜底 */
.mem-no-bot {
  margin-top: 12px;
  display: flex; align-items: center; gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: #FFFDFA;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, .10);
}
.mem-no-bot .tx { flex: 1; min-width: 0; }
.mem-no-bot .tx .t { font-size: 12px; font-weight: 900; color: #22302A; }
.mem-no-bot .tx .m { margin-top: 3px; font-size: 10.5px; line-height: 1.5; color: #7C877E; }
.mem-no-bot-btn { flex: 0 0 auto; margin: 0; padding: 6px 12px; font-size: 11px; }
</style>
