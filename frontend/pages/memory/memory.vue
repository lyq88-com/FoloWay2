<template>
  <view class="xt-page xt-s19">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">记忆管理</view>
          <view class="page-sub">{{ currentRoleName }}记得你 {{ stats.total || 0 }} 件事</view>
        </view>
        <view class="icon-btn" @click="openAdd"><xt-icon name="i-edit" /></view>
      </view>

      <view class="mem-hero">
        <view class="t">她理解到的你</view>
        <view class="m">不太喜欢被催，但需要有人提醒；比起鼓励，更希望被具体地关心。</view>
      </view>

      <!-- 记忆跟角色走：换一个角色，就换一套记忆 -->
      <scroll-view class="role-scroll" scroll-x>
        <view class="chips" style="display: inline-flex; margin: 11px 0 0">
          <view
            v-for="r in roles"
            :key="r.roleKey"
            class="chip"
            :class="{ on: r.roleKey === roleKey }"
            @click="switchRole(r.roleKey)"
          >{{ r.name }}</view>
        </view>
      </scroll-view>

      <view class="chips" style="margin: 8px 0 2px">
        <view
          v-for="t in tabs"
          :key="t.key"
          class="chip"
          :class="{ on: layer === t.key }"
          @click="switchLayer(t.key)"
        >{{ t.label }}</view>
      </view>

      <view
        v-for="m in list"
        :key="m.id"
        class="mem-item"
        @longpress="confirmDelete(m)"
      >
        <view
          class="mi"
          :class="m.layer === 'profile' ? 'tint-green' : (m.layer === 'event' ? 'tint-sand' : 'tint-peach')"
        >
          <xt-icon :name="m.layer === 'profile' ? 'i-user' : (m.layer === 'event' ? 'i-clock' : 'i-heart')" />
        </view>
        <view class="tx">
          <view class="t">{{ m.title || m.layerLabel }}</view>
          <view class="m">{{ m.content }}</view>
          <view class="d">
            {{ m.createdAt }} · {{ m.layerLabel }} · 重要度 {{ m.salience }}<text v-if="m.shared"> · 共享</text>
          </view>
        </view>
      </view>

      <view v-if="!loading && list.length === 0" class="quiz-hint" style="margin-top: 14px; text-align: center">
        还没有记忆，和她多聊几句，她会慢慢记住你
      </view>
      <view v-if="loading" class="quiz-hint" style="margin-top: 14px; text-align: center">加载中…</view>
      <view
        v-if="!loading && list.length > 0 && list.length < (stats.total || 0)"
        class="quiz-hint"
        style="margin-top: 10px; text-align: center"
        @click="loadMore"
      >加载更多（还有 {{ (stats.total || 0) - list.length }} 条）</view>

      <view class="focus-btns" style="margin-top: 12px">
        <view class="fbtn ghost" @click="openAdd">＋ 补一条记忆</view>
        <view class="fbtn ghost" @click="confirmClear">一键清空</view>
      </view>

      <view class="quiz-hint" style="margin: 12px 0 18px; text-align: center">记忆仅你可见，可随时删除或让她忘记</view>
    </view>

    <!-- 添加记忆 -->
    <view v-if="showAdd" class="mem-modal-mask" @click="closeAdd">
      <view class="mem-modal" @click.stop>
        <view class="mem-modal-t">补一条记忆</view>
        <view class="chips" style="margin: 10px 0 0; flex-wrap: wrap">
          <view
            v-for="t in addTabs"
            :key="t.key"
            class="chip"
            :class="{ on: form.layer === t.key }"
            @click="form.layer = t.key"
          >{{ t.label }}</view>
        </view>
        <input
          class="mem-input"
          v-model="form.title"
          placeholder="短标签（如：称呼 / 忌口）"
          maxlength="20"
        />
        <textarea
          class="mood-input"
          v-model="form.content"
          placeholder="想让 TA 记住什么？"
          :maxlength="200"
        />
        <view class="focus-btns" style="margin-top: 12px">
          <view class="fbtn ghost" @click="closeAdd">取消</view>
          <view class="fbtn main" @click="submitAdd">记住</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import memoryApi from '@/api/memory'
import personaApi from '@/api/persona'
import { CHARACTERS } from '@/common/ai-characters'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const LAYERS = [
  { key: 'profile', label: '长期信息' },
  { key: 'event', label: '共同经历' },
  { key: 'preference', label: '偏好习惯' }
]

export default {
  components: { XtIcon },
  data() {
    return {
      roleKey: '',
      roles: [],
      layer: '',
      list: [],
      stats: { total: 0, by_layer: { profile: 0, event: 0, preference: 0 } },
      page: 1,
      pageSize: 50,
      loading: false,
      showAdd: false,
      form: { layer: 'profile', title: '', content: '' }
    }
  },
  computed: {
    tabs() {
      const b = this.stats.by_layer || {}
      return [{ key: '', label: '全部', count: this.stats.total || 0 }].concat(
        LAYERS.map(l => ({ key: l.key, label: l.label, count: b[l.key] || 0 }))
      )
    },
    addTabs() {
      return LAYERS
    },
    currentRoleName() {
      const r = this.roles.find(x => x.roleKey === this.roleKey)
      return r ? r.name : '这个角色'
    }
  },
  onLoad(options) {
    if (options && options.roleKey) this.roleKey = options.roleKey
    this.loadRoles()
  },
  onShow() {
    // 从别的页面回来时刷新，保证删除/新增立即可见
    if (this.roles.length) this.reload()
  },
  methods: {
    async loadRoles() {
      try {
        // 官方角色：来自 ai-characters.js 的 20 个（稳定、前端本地，避免后端 seed 不全）
        const officialRoles = (CHARACTERS || []).map(c => ({
          roleKey: c.id,
          name: c.name,
          avatar: c.avatar || '🌿',
          origin: 'official'
        }))
        // 用户自定义角色：来自后端 persona API（custom + gacha）
        let customRoles = []
        try {
          const customRes = await personaApi.getRoles('custom', false)
          const gachaRes = await personaApi.getRoles('gacha', false)
          const parseList = (res) => {
            const d = res && res.data ? res.data : (Array.isArray(res) ? res : [])
            return (d || []).map(r => ({
              roleKey: r.roleKey || r.role_type || String(r.id),
              name: r.name,
              avatar: r.avatar || '🌿',
              origin: r.origin || 'custom'
            }))
          }
          customRoles = parseList(customRes).concat(parseList(gachaRes))
        } catch (e) { /* 后端未接入 custom 时静默 */ }
        this.roles = officialRoles.concat(customRoles)
        if (!this.roleKey && this.roles.length) this.roleKey = this.roles[0].roleKey
      } catch (e) {
        this.roles = []
      }
      this.reload()
    },
    switchRole(key) {
      if (key === this.roleKey) return
      this.roleKey = key
      this.reload()
    },
    switchLayer(key) {
      if (key === this.layer) return
      this.layer = key
      this.reload()
    },
    async reload() {
      this.page = 1
      this.list = []
      await this.fetch()
    },
    async loadMore() {
      if (this.loading) return
      if (this.list.length >= (this.stats.total || 0)) return
      this.page += 1
      await this.fetch(true)
    },
    async fetch(append = false) {
      this.loading = true
      try {
        const res = await memoryApi.getList({
          role_key: this.roleKey,
          layer: this.layer,
          page: this.page,
          page_size: this.pageSize
        })
        const d = (res && res.data) || {}
        const rows = d.list || []
        this.list = append ? this.list.concat(rows) : rows
        if (d.stats) this.stats = d.stats
      } catch (e) {
        if (!append) this.list = []
      } finally {
        this.loading = false
      }
    },
    confirmDelete(m) {
      const self = this
      uni.showModal({
        title: '删除这条记忆',
        content: m.content,
        confirmText: '删除',
        confirmColor: '#E06C75',
        success(r) {
          if (r.confirm) self.doDelete(m)
        }
      })
    },
    async doDelete(m) {
      try {
        await memoryApi.remove(m.id)
        this.list = this.list.filter(x => x.id !== m.id)
        this.stats.total = Math.max(0, (this.stats.total || 0) - 1)
        const b = this.stats.by_layer || {}
        if (b[m.layer] != null) b[m.layer] = Math.max(0, b[m.layer] - 1)
        uni.showToast({ title: '已删除这一条', icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '删除失败', icon: 'none' })
      }
    },
    confirmClear() {
      const self = this
      uni.showActionSheet({
        itemList: [`清空「${this.currentRoleName}」的记忆`, '清空所有角色的记忆'],
        success(res) {
          const all = res.tapIndex === 1
          uni.showModal({
            title: all ? '清空全部记忆' : '清空这个角色的记忆',
            content: '清空后 TA 会忘记你们聊过的一切，此操作不可恢复。',
            confirmText: '清空',
            confirmColor: '#E06C75',
            success(r) {
              if (r.confirm) self.doClear(all)
            }
          })
        }
      })
    },
    async doClear(all) {
      try {
        const res = await memoryApi.clear(this.roleKey, all)
        const n = (res && res.data && res.data.deleted) || 0
        this.list = []
        this.stats = { total: 0, by_layer: { profile: 0, event: 0, preference: 0 } }
        uni.showToast({ title: `已清空 ${n} 条`, icon: 'none' })
      } catch (e) {
        uni.showToast({ title: '清空失败', icon: 'none' })
      }
    },
    openAdd() {
      this.form = { layer: this.layer || 'profile', title: '', content: '' }
      this.showAdd = true
    },
    closeAdd() {
      this.showAdd = false
    },
    async submitAdd() {
      const content = (this.form.content || '').trim()
      if (!content) {
        uni.showToast({ title: '写点什么再存吧', icon: 'none' })
        return
      }
      try {
        await memoryApi.add({
          content,
          layer: this.form.layer,
          title: (this.form.title || '').trim(),
          salience: 7,
          role_key: this.roleKey
        })
        this.showAdd = false
        uni.showToast({ title: '记住了', icon: 'success' })
        this.reload()
      } catch (e) {
        uni.showToast({ title: '保存失败', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
/* 弹层：补一条记忆（设计稿未覆盖，沿用页面设计 token） */
.mem-modal-mask {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 99;
  background: rgba(31, 42, 37, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.mem-modal {
  width: 300px;
  padding: 16px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 18px 40px -20px rgba(31, 42, 37, 0.4);
}
.mem-modal-t { font-size: 13px; font-weight: 900; color: var(--v7-green); }
.mem-input {
  height: 34px;
  margin-top: 10px;
  padding: 0 12px;
  border-radius: 12px;
  background: var(--v7-card);
  font-size: 10px;
  color: #22302A;
}
.mood-input { width: 100%; margin-top: 8px; height: 74px; }
</style>
