<template>
  <view class="xt-page xt-s42">
    <view class="body" style="padding: 0">
      <view class="world-hero" style="height: 288px; border-radius: 0 0 28px 28px">
        <view style="position: absolute; inset: 0; background: radial-gradient(80% 60% at 70% 20%, rgba(160, 205, 180, 0.35), transparent 70%)"></view>
        <view style="position: relative; display: flex; align-items: center; justify-content: space-between">
          <view class="icon-btn" style="color: #FFFDFA" @click="goBack"><xt-icon name="i-left" /></view>
          <text class="wk">雾 港 · 第 3 章</text>
          <view class="icon-btn" style="color: #FFFDFA" @click="showCreate = true"><xt-icon name="i-search" /></view>
        </view>
        <view style="position: relative; margin-top: 44px">
          <view style="font-size: 8px; letter-spacing: 1.4px; color: rgba(255, 255, 255, 0.5)">正在和她一起</view>
          <view style="margin-top: 7px; font-size: 26px; font-weight: 900; letter-spacing: 1px">雾港的第七个清晨</view>
          <view style="position: relative; margin-top: 8px; width: 74%; font-size: 9px; line-height: 1.8; color: rgba(255, 255, 255, 0.66)">你们在这里住了七天。她说喜欢有雾的港口，因为看不清远方的时候，刚好可以看看身边的人。</view>
        </view>
        <view class="wprog">
          <view style="display: flex; justify-content: space-between; font-size: 7px; color: rgba(255, 255, 255, 0.5); margin-bottom: 6px">
            <text>探索度 62%</text>
            <text>还差 3 个地点</text>
          </view>
          <view style="height: 4px; border-radius: 99px; background: rgba(255, 255, 255, 0.16); overflow: hidden">
            <view style="width: 62%; height: 100%; background: rgba(255, 255, 255, 0.82); border-radius: 99px"></view>
          </view>
          <view class="steps">
            <text>灯塔</text>
            <text>旧书店</text>
            <text>海堤</text>
            <text>码头</text>
            <text>雾中车站</text>
          </view>
        </view>
      </view>

      <view style="padding: 14px 18px 0">
        <view class="sec">
          <text class="sec-t">一起 <text class="i">去过的</text> 地方</text>
          <text class="sec-s" @click="switchTab(tab === 'public' ? 'mine' : 'public')">{{ worlds.length || 4 }} 个世界</text>
        </view>

        <template v-if="worlds.length">
          <view class="world-row" v-for="(w, i) in worlds" :key="w.id" @click="goDetail(w)">
            <view class="wcover" :class="['tint-green', 'tint-sand', 'tint-peach', 'tint-blue'][i % 4]">
              <xt-icon :name="['i-world', 'i-moon', 'i-heart', 'i-water'][i % 4]" />
            </view>
            <view class="tx">
              <text class="n">{{ w.name }}</text>
              <text class="m">{{ w.description || (w.is_public ? '公开世界 · 可以一起加入' : '私人世界 · 只有你们知道') }}</text>
            </view>
            <view class="ar"><xt-icon name="i-right" /></view>
          </view>
        </template>

        <template v-else>
          <view class="world-row">
            <view class="wcover tint-green"><xt-icon name="i-world" /></view>
            <view class="tx">
              <text class="n">雾港</text>
              <text class="m">进行中 · 62%</text>
            </view>
            <view class="ar"><xt-icon name="i-right" /></view>
            <view class="rib" style="opacity: 0.16"></view>
          </view>
          <view class="world-row">
            <view class="wcover tint-sand"><xt-icon name="i-moon" /></view>
            <view class="tx">
              <text class="n">月背旅店</text>
              <text class="m">未解锁 · 需要连续 7 天打卡</text>
            </view>
            <view class="ar"><xt-icon name="i-right" /></view>
          </view>
          <view class="world-row">
            <view class="wcover tint-peach"><xt-icon name="i-heart" /></view>
            <view class="tx">
              <text class="n">橘子汽水镇</text>
              <text class="m">已通关 · 可重游</text>
            </view>
            <view class="ar"><xt-icon name="i-right" /></view>
          </view>
          <view class="world-row">
            <view class="wcover tint-blue"><xt-icon name="i-water" /></view>
            <view class="tx">
              <text class="n">深蓝信号站</text>
              <text class="m">未解锁 · VIP 专属</text>
            </view>
            <view class="ar"><xt-icon name="i-right" /></view>
          </view>
        </template>

        <view class="auth-btn" style="margin-top: 11px" @click="worlds.length ? goDetail(worlds[0]) : (showCreate = true)">回到雾港</view>
      </view>
    </view>

    <!-- ===== 创建世界弹窗 ===== -->
    <view class="modal-mask" v-if="showCreate" @click="showCreate = false">
      <scroll-view scroll-y class="create-scroll" @click.stop>
        <view class="create-card" @click.stop>
          <view class="modal-head">
            <view class="modal-head-text">
              <text class="modal-title">创建虚拟世界</text>
              <text class="modal-sub">给它一个名字，和一条只属于你们的规则</text>
            </view>
            <view class="modal-close" @click="showCreate = false">
              <text class="modal-close-text">✕</text>
            </view>
          </view>

          <text class="field-label">世界名字</text>
          <input class="m-input" v-model="cf.name" placeholder="世界名字" placeholder-class="m-ph" />

          <text class="field-label">世界描述</text>
          <textarea class="m-textarea" v-model="cf.description" placeholder="世界描述" placeholder-class="m-ph" />

          <text class="field-label">世界观规则</text>
          <textarea class="m-textarea short" v-model="cf.rules" placeholder="世界观规则(例如: 在这个世界里, 每份坚持都会被看见)" placeholder-class="m-ph" />

          <!-- 公开/私人 -->
          <text class="field-label">可见范围</text>
          <view class="vis-row">
            <text class="vis-item" :class="{ active: cf.is_public === 1 }" @click="cf.is_public = 1">🌍 公开(别人可加入)</text>
            <text class="vis-item" :class="{ active: cf.is_public === 0 }" @click="cf.is_public = 0">🔒 私人(仅自己可见)</text>
          </view>

          <!-- AI角色多选 -->
          <text class="sec-label">邀请AI角色入驻(可多选)</text>
          <view class="role-wrap">
            <text
              class="role-chip"
              v-for="r in aiRoles"
              :key="r.id"
              :class="{ active: cf.role_ids.includes(r.id) }"
              @click="toggleRole(r.id)">{{ r.avatar || r.avatar_emoji || '🤖' }} {{ r.name }}</text>
          </view>

          <!-- 自设角色 -->
          <text class="sec-label">自设角色(每行一个, 可空)</text>
          <textarea class="m-textarea short" v-model="cf.customRolesText" placeholder="例如: 小狼&#10;月见" placeholder-class="m-ph" />

          <!-- 打卡目标 -->
          <text class="sec-label">每完成 {{ cf.checkin_target }} 次打卡解锁一段剧情</text>
          <view class="slider-wrap">
            <slider :value="cf.checkin_target" :min="1" :max="10" show-value activeColor="#24493A" backgroundColor="#E8E2D4" @change="e => cf.checkin_target = e.detail.value" />
          </view>

          <view class="m-btns">
            <text class="m-btn cancel" @click="showCreate = false">取消</text>
            <text class="m-btn confirm" @click="submitCreate">创造世界</text>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
/**
 * 【四大新增模块·模块1】虚拟世界列表页
 * - 公开世界: 其他用户可加入; 私人世界仅本人可见
 * - 创建世界时可邀请多个AI角色 + 添加自设角色
 * - 打卡联动: 在世界内打卡会触发AI角色互动反馈并解锁剧情碎片
 */
import worldApi from '@/api/world'
// ↓↓↓ 安全合规批次：创建内容本地前置校验（后端同源兜底） ↓↓↓
import { checkContent } from '@/common/content-check'
// ↑↑↑ 新增结束 ↑↑↑
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      tab: 'public',
      worlds: [],
      loading: false,
      aiRoles: [],
      showCreate: false,
      cf: {
        name: '', description: '', rules: '',
        is_public: 1, role_ids: [], customRolesText: '',
        checkin_target: 3
      }
    }
  },
  onShow() {
    this.loadWorlds()
    this.loadAiRoles()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },

    // ===== AI角色列表(创建时选择) =====
    async loadAiRoles() {
      try {
        const res = await worldApi.getAiRoles()
        this.aiRoles = (res && res.data) || []
      } catch (e) {
        this.aiRoles = []
      }
    },

    // ===== 世界列表 =====
    async loadWorlds() {
      this.loading = true
      try {
        const res = await worldApi.getList(this.tab)
        this.worlds = (res && res.data) || []
      } catch (e) {
        this.worlds = []
      }
      this.loading = false
    },
    switchTab(t) {
      this.tab = t
      this.loadWorlds()
    },

    toggleRole(id) {
      const idx = this.cf.role_ids.indexOf(id)
      if (idx > -1) this.cf.role_ids.splice(idx, 1)
      else this.cf.role_ids.push(id)
    },

    // ===== 创建世界 =====
    async submitCreate() {
      if (!this.cf.name.trim()) {
        uni.showToast({ title: '请给世界起个名字', icon: 'none' })
        return
      }
      // ↓↓↓ 安全合规批次：名称/简介/规则本地安全校验，命中直接拦截 ↓↓↓
      for (const [label, text] of [['名称', this.cf.name], ['简介', this.cf.description], ['规则', this.cf.rules]]) {
        const sec = checkContent(text || '')
        if (!sec.ok) {
          uni.showToast({ title: `${label}${sec.reason}`, icon: 'none', duration: 2500 })
          return
        }
      }
      // ↑↑↑ 新增结束 ↑↑↑
      const customRoles = this.cf.customRolesText
        .split('\n').map(s => s.trim()).filter(Boolean)
      try {
        const res = await worldApi.create({
          name: this.cf.name.trim(),
          description: this.cf.description,
          rules: this.cf.rules,
          is_public: this.cf.is_public,
          role_ids: this.cf.role_ids,
          custom_roles: customRoles,
          checkin_target: this.cf.checkin_target
        })
        this.showCreate = false
        uni.showToast({ title: '世界已诞生 🌏', icon: 'none' })
        // 直接进入新世界
        const w = (res && res.data) || {}
        if (w.id) {
          setTimeout(() => {
            uni.navigateTo({ url: `/pages/world-space/world-detail?id=${w.id}` })
          }, 600)
        }
        this.loadWorlds()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '创建失败', icon: 'none' })
      }
    },

    goDetail(w) {
      uni.navigateTo({ url: `/pages/world-space/world-detail?id=${w.id}` })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿 i / span 元素选择器的等价规则 */
.xt-page.xt-s42 .sec-t .i {
  font-style: normal;
  color: #44705a;
}
.xt-page.xt-s42 .world-hero .wprog .steps uni-text {
  display: inline;
}

/* ===== 视觉精修：英雄区操作按钮（白底白图标 -> 玻璃底白图标） ===== */
.xt-page.xt-s42 .world-hero .icon-btn {
  width: 34px; height: 34px;
  color: #FFFDFA;
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}
.xt-page.xt-s42 .world-hero .icon-btn .ic { width: 16px; height: 16px; }

/* ===== 视觉精修：地点进度点（原来缺少布局，连成一行） ===== */
.xt-page.xt-s42 .world-hero .wprog .steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 9px;
  font-size: 7.5px;
  line-height: 1;
  letter-spacing: 0.2px;
  color: rgba(255, 255, 255, 0.48);
}
.xt-page.xt-s42 .world-hero .wprog .steps uni-text {
  flex-shrink: 0;
  white-space: nowrap;
}

/* ===== 视觉精修：世界列表（标题/描述分行 + 卡片化） ===== */
.xt-page.xt-s42 .world-row {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: 8px;
  padding: 9px 12px 9px 10px;
  border-radius: 16px;
  background: var(--v7-card);
  box-shadow: var(--v7-shadow), inset 0 0 0 1px var(--v7-line);
  transition: transform var(--dur, .18s), box-shadow var(--dur, .18s);
}
.xt-page.xt-s42 .world-row:active {
  transform: scale(.99);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s42 .world-row .tx {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.xt-page.xt-s42 .world-row .tx .n {
  display: block;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .2px;
  color: var(--v7-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.xt-page.xt-s42 .world-row .tx .m {
  display: block;
  margin-top: 3px;
  font-size: 8.5px;
  color: var(--v7-gray-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.xt-page.xt-s42 .world-row .ar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  color: #CFD6CE;
}
.xt-page.xt-s42 .world-row .ar .ic { width: 13px; height: 13px; }

/* 封面底色浅，图标不能被 .wcover 的白字覆盖 */
.xt-page.xt-s42 .world-row .wcover.tint-green { color: #2E5643; }
.xt-page.xt-s42 .world-row .wcover.tint-sand { color: #A18466; }
.xt-page.xt-s42 .world-row .wcover.tint-peach { color: #B57F4C; }
.xt-page.xt-s42 .world-row .wcover.tint-blue { color: #74919F; }

/* ===== 创建弹窗（保留原有交互样式） ===== */
.modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(18, 28, 23, 0.55);
  z-index: 99;
  display: flex; align-items: center; justify-content: center;
}
.create-scroll { max-height: 86vh; width: 100%; display: flex; }
.create-card {
  width: 660rpx;
  margin: auto;
  background: var(--v7-card);
  border-radius: 36rpx;
  padding: 36rpx 32rpx 32rpx;
  box-shadow: 0 30rpx 60rpx -30rpx rgba(12, 22, 17, 0.6);
}
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10rpx;
}
.modal-head-text { display: flex; flex-direction: column; }
.modal-title { font-size: 34rpx; font-weight: 800; color: #22302A; letter-spacing: 1rpx; }
.modal-sub { margin-top: 8rpx; font-size: 19rpx; color: #AEB6AE; }
.modal-close {
  width: 52rpx; height: 52rpx;
  border-radius: 50%;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  display: flex; align-items: center; justify-content: center;
}
.modal-close-text { font-size: 20rpx; color: #8E9A91; }

.field-label {
  display: block;
  margin: 24rpx 0 0;
  font-size: 19rpx;
  letter-spacing: 1rpx;
  color: #8E9A91;
}
.m-input {
  background: var(--v7-card);
  border-radius: 18rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  padding: 20rpx 24rpx;
  color: #22302A;
  font-size: 25rpx;
  margin-top: 10rpx;
}
.m-textarea {
  width: 100%; height: 124rpx;
  background: var(--v7-card);
  border-radius: 18rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  padding: 20rpx 24rpx;
  color: #22302A;
  font-size: 25rpx;
  margin-top: 10rpx;
  box-sizing: border-box;
}
.m-textarea.short { height: 96rpx; }
.m-ph { color: #BFC7BF; }
.vis-row { display: flex; margin-top: 10rpx; }
.vis-item {
  flex: 1;
  text-align: center;
  font-size: 20rpx;
  color: #8E9A91;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  border-radius: 18rpx;
  padding: 18rpx 0;

  &:first-child { margin-right: 12rpx; }
}
.vis-item.active {
  color: #F8F3E7;
  background: var(--v7-green);
  box-shadow: none;
  font-weight: 600;
}
.sec-label {
  display: block;
  margin: 26rpx 0 12rpx;
  font-size: 19rpx;
  letter-spacing: 1rpx;
  color: #8E9A91;
}
.role-wrap { display: flex; flex-wrap: wrap; margin: 0 -6rpx; }
.role-chip {
  font-size: 21rpx;
  color: #6A776E;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  border-radius: 999rpx;
  padding: 10rpx 22rpx;
  margin: 0 6rpx 10rpx;
}
.role-chip.active {
  color: #F8F3E7;
  background: var(--v7-green);
  box-shadow: none;
}
.slider-wrap { padding: 6rpx 4rpx 0; }
.m-btns { display: flex; margin-top: 30rpx; }
.m-btn {
  flex: 1;
  text-align: center;
  padding: 22rpx 0;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 700;
}
.m-btn.cancel {
  background: var(--v7-card);
  color: #6A776E;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  margin-right: 14rpx;
}
.m-btn.confirm {
  background: linear-gradient(140deg, #4E7A64, #24493A);
  color: #F8F3E7;
}
</style>
