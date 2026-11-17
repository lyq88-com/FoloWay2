<template>
  <view class="xt-page xt-s59">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">伙伴工坊</view>
          <view class="page-sub">{{ bots.length }} 位专属伙伴 · {{ roleTotal }} 位官方角色</view>
        </view>
        <view v-if="tab === 'mine'" class="icon-btn" @click="openForm()"><xt-icon name="i-plus" /></view>
      </view>

      <!-- 两套伙伴体系合并为一个入口：我的伙伴（自定义 Bot）/ 官方角色（20 位现成角色） -->
      <view class="seg" style="margin:2px 0 12px">
        <view class="sg" :class="{ on: tab === 'mine' }" @click="tab = 'mine'">我的伙伴</view>
        <view class="sg" :class="{ on: tab === 'roles' }" @click="tab = 'roles'">官方角色</view>
      </view>

      <!-- 我的伙伴 -->
      <view v-for="b in bots" v-if="tab === 'mine'" :key="b.id" class="mem-item" @click="openChat(b)">
        <view class="bot-av">
          <image
            v-if="b.avatar && (b.avatar.indexOf('http') === 0 || b.avatar.charAt(0) === '/')"
            :src="b.avatar"
            mode="aspectFill"
            style="width: 100%; height: 100%; border-radius: 50%; display: block;"
          />
          <text v-else class="bot-emoji">{{ b.avatar }}</text>
        </view>
        <view class="tx">
          <view class="t">{{ b.name }}<text v-if="b.personality"> · {{ b.personality }}</text></view>
          <view class="m">记得 {{ b.memory_count || 0 }} 件事 · {{ b.speak_style || '只属于你们的对话' }}</view>
          <view class="d">{{ b.self_intro || b.taboo || '慢慢来，我在。' }}</view>
          <view class="chips bot-ops">
            <view class="chip" @click.stop="openMemory(b)">记忆</view>
            <view class="chip" @click.stop="openForm(b)">编辑</view>
            <view class="chip" @click.stop="tryProactive(b)">想你</view>
            <view class="chip" @click.stop="confirmDelete(b)">删除</view>
          </view>
        </view>
        <text class="v">{{ b.allow_push ? '主动' : '安静' }}</text>
      </view>

      <!-- 空状态 -->
      <view v-if="tab === 'mine' && bots.length === 0" class="mem-item">
        <view class="mi tint-green"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">还没有自己的 AI 伙伴</view>
          <view class="m">创建一个专属伙伴：自定义性格、说话风格，TA 只记得只属于你们的记忆</view>
        </view>
      </view>

      <!-- 创建入口 -->
      <view v-if="tab === 'mine'">
        <view class="cal-sec" style="margin-top: 13px">
          <text class="t">创建一个新的她</text>
          <text class="s">随时可以删除</text>
        </view>

        <view class="custom-role" @click="goGallery">
          <view class="ci"><xt-icon name="i-compass" /></view>
          <view class="tx">
            <view class="t">发现更多 AI 伙伴</view>
            <view class="m">循途画廊 · 20 位现成伙伴，找到那个懂你的 TA</view>
          </view>
          <view class="ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="custom-role" @click="openForm()">
          <view class="ci"><xt-icon name="i-spark" /></view>
          <view class="tx">
            <view class="t">从性格开始</view>
            <view class="m">温柔 / 理性 / 元气 / 毒舌但心软</view>
          </view>
          <view class="ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="custom-role" @click="openForm()">
          <view class="ci tint-peach"><xt-icon name="i-call" /></view>
          <view class="tx">
            <view class="t">从声音开始</view>
            <view class="m">选一个你想每天听见的声音</view>
          </view>
          <view class="ar"><xt-icon name="i-right" /></view>
        </view>
        <view class="custom-role" @click="openForm()">
          <view class="ci tint-blue"><xt-icon name="i-edit" /></view>
          <view class="tx">
            <view class="t">从一句话开始</view>
            <view class="m">写一句 TA 最该对你说的话</view>
          </view>
          <view class="ar"><xt-icon name="i-right" /></view>
        </view>

        <view class="quote">伙伴之间不共享记忆，但可以一起出现。</view>
      </view>

      <!-- 官方角色：原先独立的「伙伴工坊」角色页，合并到这里作为一个分页 -->
      <view v-if="tab === 'roles'">
        <view class="role-grid">
          <view
            v-for="r in roles"
            :key="r.id"
            class="role"
            :class="{ on: r.id === currentRoleId }"
            @click="selectRole(r)"
          >
            <image v-if="r.photo" :src="r.photo" mode="aspectFill" />
            <view v-else class="role-ph"><text>{{ r.avatar }}</text></view>
            <text>{{ r.name }}</text>
          </view>
        </view>

        <view class="ai-rec" style="margin-top: 12px">
          <view class="sp"><xt-icon name="i-brain" /></view>
          <view class="tx">
            <view class="k">记忆彼此隔离</view>
            <view class="p">每位伙伴只记得和你单独发生的事，不会串线。</view>
          </view>
        </view>

        <view class="custom-role" style="margin-top: 12px" @click="goWorkshop">
          <view class="ci"><xt-icon name="i-plus" /></view>
          <view class="tx">
            <view class="t">创建自定义角色</view>
            <view class="m">设定性格、说话方式与专属记忆</view>
          </view>
          <view class="ar"><xt-icon name="i-right" /></view>
        </view>
      </view>
    </view>

    <!-- 创建/编辑弹窗 -->
    <view class="modal-mask" v-if="showForm" @click="showForm = false">
      <scroll-view scroll-y class="form-card" @click.stop>
        <view class="form-grip"></view>
        <text class="form-title">{{ form.id ? '编辑伙伴' : '创建 AI 伙伴' }}</text>
        <text class="form-sub">给 TA 一个名字、一个性格，和只属于你们的记忆。</text>
        <input class="f-input" v-model="form.name" maxlength="12" placeholder="伙伴名称" placeholder-class="f-ph" />
        <view class="avatar-row">
          <text
            class="avatar-item"
            v-for="e in AVATARS"
            :key="e"
            :class="{ active: form.avatar === e }"
            @click="form.avatar = e"
          >{{ e }}</text>
        </view>
        <input class="f-input" v-model="form.personality" maxlength="60" placeholder="性格（如：温柔坚定，偶尔毒舌）" placeholder-class="f-ph" />
        <input class="f-input" v-model="form.speak_style" maxlength="60" placeholder="说话风格（如：口语化，爱用比喻）" placeholder-class="f-ph" />
        <textarea class="f-area" v-model="form.self_intro" maxlength="200" placeholder="自述：TA 的身份/背景设定（如：陪你备考的学姐）" placeholder-class="f-ph" />
        <input class="f-input" v-model="form.taboo" maxlength="60" placeholder="禁忌：TA 绝不做/不说的事" placeholder-class="f-ph" />
        <view class="switch-row">
          <text class="switch-label">允许 TA 主动发来陪伴消息</text>
          <switch :checked="form.allow_push" color="#24493A" @change="e => form.allow_push = e.detail.value" />
        </view>
        <view class="form-btns">
          <text class="f-btn cancel" @click="showForm = false">取消</text>
          <text class="f-btn confirm" @click="submitForm">{{ form.id ? '保存' : '创建' }}</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
/**
 * 【newfunc 增量】AI 伙伴工坊：创建/编辑自定义人设伙伴，进入聊天/记忆管理
 */
import api from '@/api/newfunc'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { CHARACTERS } from '@/common/ai-characters'
import { getActivePartnerId, getPartnerAvatar, saveActivePartner } from '@/common/ai-partner'

const AVATARS = ['🌿', '🐱', '🦊', '🐰', '🌙', '☕', '🎧', '📚', '🌊', '🔥', '🧸', '⭐']

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      tab: 'mine',            // mine=我的伙伴（自定义 Bot） / roles=官方角色
      bots: [],
      showForm: false,
      AVATARS,
      form: {
        id: 0, name: '', avatar: '🌿', personality: '',
        speak_style: '', self_intro: '', taboo: '', allow_push: true
      }
    }
  },
  onShow() {
    this.load()
  },
  computed: {
    roles() {
      const presets = CHARACTERS.map(c => ({
        id: c.id,
        name: c.name,
        avatar: c.avatar,
        photo: getPartnerAvatar(c)
      }))
      const customs = (this.$store.state.customCharacters || [])
        .filter(c => c && c.id)
        .map(c => ({
          id: c.id,
          name: c.name,
          avatar: c.avatar || '🌟',
          photo: getPartnerAvatar(c)
        }))
      return [...presets, ...customs]
    },
    roleTotal() {
      return this.roles.length
    },
    currentRoleId() {
      return getActivePartnerId()
    }
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    /** 发现AI入口（原发现页「发现AI」，2026-11-09 并入工坊）：去循途画廊选伙伴 */
    goGallery() {
      uni.navigateTo({ url: '/pages/character-gallery/character-gallery' })
    },
    /** 官方角色：切换当前 AI 伙伴（与角色工坊共用同一份 aiConfig） */
    selectRole(r) {
      saveActivePartner(r.id, r.name)
      uni.showToast({ title: `已切换到 ${r.name}`, icon: 'none' })
    },
    /** 进入角色工坊做完整设定（原「伙伴工坊」页，现作为角色设定/自定义创建页） */
    goWorkshop() {
      uni.navigateTo({ url: '/pages/character-workshop/character-workshop' })
    },
    async load() {
      try {
        const res = await api.botList()
        this.bots = (res.data && res.data.list) || []
      } catch (e) {
        this.bots = []
      }
    },
    openForm(b) {
      this.form = b
        ? { id: b.id, name: b.name, avatar: b.avatar, personality: b.personality,
            speak_style: b.speak_style, self_intro: b.self_intro, taboo: b.taboo,
            allow_push: !!b.allow_push }
        : { id: 0, name: '', avatar: '🌿', personality: '', speak_style: '',
            self_intro: '', taboo: '', allow_push: true }
      this.showForm = true
    },
    async submitForm() {
      if (!this.form.name.trim()) {
        uni.showToast({ title: '先给伙伴起个名字吧', icon: 'none' })
        return
      }
      try {
        if (this.form.id) {
          await api.botUpdate(this.form.id, this.form)
          uni.showToast({ title: '已保存', icon: 'success' })
        } else {
          await api.botCreate(this.form)
          uni.showToast({ title: '伙伴已创建', icon: 'success' })
        }
        this.showForm = false
        this.load()
      } catch (e) { /* request 层已提示 */ }
    },
    openChat(b) {
      uni.navigateTo({ url: `/pages/newfunc/bot-chat?id=${b.id}&name=${encodeURIComponent(b.name)}&avatar=${encodeURIComponent(b.avatar)}` })
    },
    openMemory(b) {
      uni.navigateTo({ url: `/pages/newfunc/bot-memory?id=${b.id}&name=${encodeURIComponent(b.name)}` })
    },
    async tryProactive(b) {
      try {
        const res = await api.botProactive(b.id)
        uni.showModal({
          title: `${b.name} 说：`,
          content: (res.data && res.data.message) || '……',
          showCancel: false,
          confirmText: '去聊聊',
          success: () => this.openChat(b)
        })
      } catch (e) { /* request 层已提示 */ }
    },
    confirmDelete(b) {
      uni.showModal({
        title: '删除伙伴',
        content: `删除「${b.name}」会同时清空 TA 的全部记忆（不影响其他伙伴），确定吗？`,
        confirmColor: '#E57373',
        success: async (r) => {
          if (!r.confirm) return
          try {
            await api.botDelete(b.id)
            uni.showToast({ title: '已删除', icon: 'success' })
            this.load()
          } catch (e) { /* request 层已提示 */ }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
/* === 伙伴卡片：设计稿 42px 圆头像 === */
.xt-page.xt-s59 .body { padding-bottom: calc(24px + env(safe-area-inset-bottom)); }
.xt-page.xt-s59 .mem-item { padding: 12px; align-items: flex-start; }
.xt-page.xt-s59 .bot-av {
  width: 42px; height: 42px; border-radius: 50%; flex-shrink: 0; overflow: hidden;
  background: #F3EFE5; display: flex; align-items: center; justify-content: center;
}
.xt-page.xt-s59 .bot-av uni-image { width: 100%; height: 100%; display: block; }
.xt-page.xt-s59 .bot-emoji { font-size: 20px; line-height: 1; }
.xt-page.xt-s59 .mem-item .t { font-size: 10px; }
.xt-page.xt-s59 .mem-item .v { font-size: 7px; color: var(--v7-green); align-self: flex-start; padding-top: 1px; flex-shrink: 0; }

/* 卡片内操作胶囊 */
.xt-page.xt-s59 .bot-ops { margin: 6px 0 0; flex-wrap: wrap; }
.xt-page.xt-s59 .bot-ops .chip { font-size: 7px; padding: 3px 8px; }

/* === 创建入口箭头 === */
.xt-page.xt-s59 .custom-role .ar { color: #C6CEC7; display: flex; align-items: center; }
.xt-page.xt-s59 .custom-role .ar .ic { width: 12px; height: 12px; }

.xt-page.xt-s59 .quote {
  margin-top: 14px; text-align: center;
  font-size: 8px; color: #BFC7BF; letter-spacing: .4px;
}

/* === 创建/编辑弹窗 === */
.modal-mask {
  position: absolute; inset: 0; z-index: 80;
  background: rgba(34, 48, 42, 0.42);
  display: flex; align-items: flex-end;
}
.form-card {
  width: 100%; max-height: 82%;
  background: var(--v7-card);
  border-radius: 20px 20px 0 0;
  padding: 10px 18px 28px; box-sizing: border-box;
}
.form-grip {
  width: 36px; height: 4px; border-radius: 999px;
  background: var(--v7-line);
  margin: 0 auto 13px;
}
.form-title { display: block; font-size: 15px; font-weight: 900; color: #22302A; }
.form-sub {
  display: block; margin-top: 4px; margin-bottom: 13px;
  font-size: 9px; color: #AEB6AE; line-height: 1.6;
}
.f-input {
  height: 38px; background: var(--v7-card); border-radius: 12px; padding: 0 12px;
  font-size: 11px; margin-bottom: 8px; color: #22302A;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.f-area {
  background: var(--v7-card); border-radius: 12px; padding: 10px 12px;
  font-size: 11px; margin-bottom: 8px; width: 100%; height: 72px; color: #22302A;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.f-ph { color: #B4BDB9; }
.avatar-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.avatar-item {
  width: 34px; height: 34px; border-radius: 10px; font-size: 16px;
  background: var(--v7-card); color: #22302A;
  display: flex; align-items: center; justify-content: center;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.avatar-item.active {
  background: #F3EFE5;
  box-shadow: inset 0 0 0 2px var(--v7-green);
}
.switch-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; margin: 2px 0 11px;
  border-top: 1px solid var(--v7-line);
}
.switch-label { font-size: 10px; color: var(--v7-green); }
.form-btns { display: flex; gap: 10px; }
.f-btn {
  flex: 1; text-align: center; padding: 12px 0;
  border-radius: 999px; font-size: 12px;
}
.f-btn.cancel {
  background: var(--v7-card); color: #6A776E;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.f-btn.confirm {
  background: linear-gradient(140deg, #4E7A64, #24493A);
  color: #FFFDFA; font-weight: 800;
  box-shadow: 0 8px 16px -10px rgba(36, 73, 58, 0.8);
}

/* 官方角色网格：uni-image 默认 320×240，必须显式收缩成圆形头像 */
.xt-page.xt-s59 .role uni-image {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--v7-card);
  box-shadow: 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s59 .role.on uni-image { box-shadow: 0 0 0 2px var(--v7-green); }
.xt-page.xt-s59 .role > text { font-size: 6.5px; color: #A2AAA3; }
.xt-page.xt-s59 .role.on > text { color: #3C6B55; font-weight: 800; }
.xt-page.xt-s59 .role:active { transform: scale(0.96); }

/* 官方角色网格里没有照片时的 emoji 头像 */
.role-ph {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #F1EFE7;
  border: 2px solid var(--v7-card);
  box-shadow: 0 0 0 1px var(--v7-line);
}

/* 顶部分页：我的伙伴 / 官方角色 */
.seg .sg {
  flex: 1;
  padding: 7px 0;
  border-radius: 9px;
  text-align: center;
  font-size: 9px;
  color: #8E9A91;
  background: var(--v7-card);
}
.seg .sg.on {
  color: #26332C;
  font-weight: 900;
  background: var(--v7-card);
  box-shadow: 0 0 0 1px var(--v7-line);
}
</style>
