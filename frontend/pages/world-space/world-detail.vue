<template>
  <view class="xt-page xt-s43">
    <view class="body" style="padding: 0">
      <view style="position: relative; height: 238px; background: linear-gradient(165deg, #42594e, #24332c); display: flex; align-items: flex-end; padding: 16px 18px">
        <view style="position: absolute; inset: 0; background: radial-gradient(70% 60% at 30% 10%, rgba(180, 215, 195, 0.3), transparent 72%)"></view>
        <view style="position: absolute; top: 8px; left: 14px; right: 14px; display: flex; justify-content: space-between; color: #fff">
          <view class="icon-btn" style="color: #fff" @click="goBack"><xt-icon name="i-left" /></view>
          <view class="icon-btn" style="color: #fff" :style="{ color: favorited ? '#F2A6A6' : '#fff' }" @click="toggleFavorite"><xt-icon name="i-heart" /></view>
        </view>
        <view style="position: relative; width: 100%">
          <text class="tag" style="display: inline-block; background: rgba(255, 255, 255, 0.18); color: #fff">{{ joined ? '已加入' : '进行中' }}</text>
          <view style="margin-top: 7px; font-size: 24px; font-weight: 900; color: #fff; letter-spacing: 0.5px">{{ world.name || '雾港' }}</view>
          <view style="margin-top: 4px; font-size: 8.5px; color: rgba(255, 255, 255, 0.6)">{{ world.description || '一个有雾、有旧书、有海堤的小城' }}</view>
        </view>
      </view>

      <view style="padding: 14px 18px 0">
        <view class="pills">
          <view class="pill">
            <view style="font-size: 13px; font-weight: 900; color: #2e5643">{{ plotPercent }}%</view>
            <view style="font-size: 6.5px; color: #aeb6ae; margin-top: 1px">探索度</view>
          </view>
          <view class="pill">
            <view style="font-size: 13px; font-weight: 900; color: #2e5643">7</view>
            <view style="font-size: 6.5px; color: #aeb6ae; margin-top: 1px">共处天数</view>
          </view>
          <view class="pill">
            <view style="font-size: 13px; font-weight: 900; color: #b8874e">{{ lockedPlotCount }}</view>
            <view style="font-size: 6.5px; color: #aeb6ae; margin-top: 1px">待解锁地点</view>
          </view>
        </view>

        <view class="cal-sec">
          <text class="t">这里的居民</text>
          <text class="s">她认识 {{ residentsCount }} 位</text>
        </view>
        <view class="residents" style="display: flex; gap: 8px; align-items: center">
          <template v-for="m in residents" :key="m.id">
            <image
              v-if="m.photo"
              :src="m.photo"
              mode="aspectFill"
              style="width: 38px; height: 38px; border-radius: 50%"
            />
            <view
              v-else
              style="width: 38px; height: 38px; border-radius: 50%; background: #fffcf6; display: flex; align-items: center; justify-content: center; font-size: 14px"
            >{{ m.role_avatar || '🙂' }}</view>
          </template>
          <text v-if="moreResidents > 0" style="width: 38px; height: 38px; border-radius: 50%; background: #fffcf6; display: flex; align-items: center; justify-content: center; font-size: 8px; color: #aeb6ae">+{{ moreResidents }}</text>
          <text style="margin-left: auto; font-size: 7.5px; color: #8e9a91">她的好感 Lv.4</text>
        </view>

        <view class="cal-sec" style="margin-top: 13px">
          <text class="t">可以一起做的事</text>
          <text class="s">今天 {{ plots.length || 3 }} 件</text>
        </view>

        <template v-if="plots.length">
          <view class="event-card" v-for="(p, i) in plots.slice(0, 3)" :key="p.id" style="margin: 0 0 7px">
            <view class="ev-ic" :style="[{}, { background: '#f7f2ed', color: '#b8874e' }, { background: '#eff3f5', color: '#849ca8' }][i % 3]">
              <xt-icon :name="['i-water', 'i-book', 'i-moon'][i % 3]" />
            </view>
            <view class="ev-tx">
              <text class="ev-t">{{ p.title }}</text>
              <text class="ev-m">{{ p.unlocked ? '已解锁 · 可重温这段剧情' : '需累计打卡 ' + p.required_checkins + ' 次解锁' }}</text>
            </view>
            <view class="ev-ok" :style="p.unlocked ? '' : 'color: #cfd6ce'">
              <xt-icon :name="p.unlocked ? 'i-check' : 'i-right'" />
            </view>
          </view>
        </template>

        <template v-else>
          <view class="event-card" style="margin: 0 0 7px">
            <view class="ev-ic"><xt-icon name="i-water" /></view>
            <view class="ev-tx">
              <text class="ev-t">去海堤看一次退潮</text>
              <text class="ev-m">约 15 分钟 · 完成后好感 +6</text>
            </view>
            <view class="ev-ok"><xt-icon name="i-check" /></view>
          </view>
          <view class="event-card" style="margin: 0 0 7px">
            <view class="ev-ic" style="background: #f7f2ed; color: #b8874e"><xt-icon name="i-book" /></view>
            <view class="ev-tx">
              <text class="ev-t">在旧书店各挑一本书</text>
              <text class="ev-m">约 20 分钟 · 会解锁一段对白</text>
            </view>
            <view class="ev-ok" style="color: #cfd6ce"><xt-icon name="i-right" /></view>
          </view>
          <view class="event-card" style="margin: 0 0 7px">
            <view class="ev-ic" style="background: #eff3f5; color: #849ca8"><xt-icon name="i-moon" /></view>
            <view class="ev-tx">
              <text class="ev-t">在天台等雾散</text>
              <text class="ev-m">夜间限定 · 21:00 后开放</text>
            </view>
            <view class="ev-ok" style="color: #cfd6ce"><xt-icon name="i-right" /></view>
          </view>
        </template>

        <view class="auth-btn" style="margin-top: 12px" @click="joined ? (showNote = true) : joinWorld()">进入{{ world.name || '雾港' }}</view>
      </view>
    </view>

    <!-- 发布笔记弹窗 -->
    <view class="modal-mask" v-if="showNote" @click="showNote = false">
      <view class="small-card" @click.stop>
        <view class="modal-head">
          <view class="modal-head-text">
            <text class="modal-title">发布世界笔记</text>
            <text class="modal-sub">写下的心情，AI 们会认真回应</text>
          </view>
          <view class="modal-close" @click="showNote = false">
            <text class="modal-close-text">✕</text>
          </view>
        </view>
        <textarea class="m-textarea" v-model="noteContent" placeholder="在这个世界里写下你的心情…" placeholder-class="m-ph" />
        <view class="m-btns">
          <text class="m-btn cancel" @click="showNote = false">取消</text>
          <text class="m-btn confirm" @click="submitNote">发布</text>
        </view>
      </view>
    </view>

    <!-- 评论弹窗 -->
    <view class="modal-mask" v-if="commentTarget" @click="commentTarget = null">
      <view class="small-card" @click.stop>
        <view class="modal-head">
          <view class="modal-head-text">
            <text class="modal-title">评论</text>
            <text class="modal-sub">AI 角色会回复你</text>
          </view>
          <view class="modal-close" @click="commentTarget = null">
            <text class="modal-close-text">✕</text>
          </view>
        </view>
        <textarea class="m-textarea" v-model="commentContent" placeholder="说点什么… AI角色会回复你" placeholder-class="m-ph" />
        <view class="m-btns">
          <text class="m-btn cancel" @click="commentTarget = null">取消</text>
          <text class="m-btn confirm" @click="submitComment">发送</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 【四大新增模块·模块1+4】世界详情页
 * - 笔记流: AI笔记 + 用户笔记; 用户评论后AI会回复, 还可能促成AI之间互评(关系变化)
 * - 剧情碎片: 随用户在世界内打卡次数逐步解锁(打卡联动)
 * - 角色关系: AI互评产生关系升温
 */
import worldApi from '@/api/world'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { getPartnerAvatar, getSwitchablePartners } from '@/common/ai-partner'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: uni.getSystemInfoSync().statusBarHeight || 20,
      worldId: 0,
      world: {},
      rules: '',
      joined: false,
      favorited: false,
      members: [],
      myCheckinCount: 0,
      plots: [],
      tab: 'notes',
      notes: [],
      relations: [],
      showNote: false,
      noteContent: '',
      commentTarget: null,
      commentContent: ''
    }
  },
  computed: {
    residents() {
      const list = this.members.filter(m => m.join_type !== 'user')
      if (!list.length) {
        // 无成员时展示当前伙伴 + 可切换伙伴（含自定义），避免固定成林夕/绵绵/月清
        return getSwitchablePartners(3).map(p => ({
          id: p.id,
          photo: p.photo,
          role_avatar: p.avatar || ''
        }))
      }
      return list.slice(0, 3).map(m => ({
        id: m.id,
        role_avatar: m.role_avatar,
        photo: getPartnerAvatar(m.role_id) || (m.role_avatar && /^(https?:\/\/|blob:|data:image|\/)/.test(m.role_avatar) ? m.role_avatar : '')
      }))
    },
    residentsCount() {
      return this.members.filter(m => m.join_type !== 'user').length || 4
    },
    moreResidents() {
      if (!this.members.filter(m => m.join_type !== 'user').length) return 2
      return Math.max(this.residentsCount - 3, 0)
    },
    plotPercent() {
      if (!this.plots.length) return 62
      const unlocked = this.plots.filter(p => p.unlocked).length
      return Math.round((unlocked / this.plots.length) * 100)
    },
    lockedPlotCount() {
      if (!this.plots.length) return 3
      return this.plots.filter(p => !p.unlocked).length
    }
  },
  onLoad(opts) {
    this.worldId = Number(opts.id || 0)
    try {
      this.favorited = !!uni.getStorageSync('world_fav_' + this.worldId)
    } catch (e) {}
  },
  onShow() {
    this.loadDetail()
  },
  methods: {
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    toggleFavorite() {
      this.favorited = !this.favorited
      try {
        if (this.favorited) uni.setStorageSync('world_fav_' + this.worldId, 1)
        else uni.removeStorageSync('world_fav_' + this.worldId)
      } catch (e) {}
      uni.showToast({ title: this.favorited ? '已收藏这个世界' : '已取消收藏', icon: 'none' })
    },

    noteTypeLabel(t) {
      const map = { checkin: '打卡笔记', feedback: 'AI反馈', normal: '随笔', system: '系统' }
      return map[t] || ''
    },

    // ===== 详情 =====
    async loadDetail() {
      try {
        const res = await worldApi.getDetail(this.worldId)
        const d = (res && res.data) || {}
        this.world = d.world || {}
        this.rules = d.rules || ''
        this.joined = !!d.joined
        this.members = d.members || []
        this.myCheckinCount = d.my_checkin_count || 0
        this.plots = d.plots || []
        this.loadNotes()
        if (this.tab === 'relations') this.loadRelations()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '加载失败', icon: 'none' })
      }
    },

    switchTab(t) {
      this.tab = t
      if (t === 'notes') this.loadNotes()
      if (t === 'relations') this.loadRelations()
    },

    // ===== 笔记流(带前3条评论) =====
    async loadNotes() {
      try {
        const res = await worldApi.getNotes(this.worldId)
        const notes = (res && res.data) || []
        // 为最近10条笔记拉取评论
        for (const n of notes.slice(0, 10)) {
          try {
            const cRes = await worldApi.getComments(n.id)
            n.comments = (cRes && cRes.data) || []
          } catch (e) {
            n.comments = []
          }
        }
        this.notes = notes
      } catch (e) {
        this.notes = []
      }
    },

    // ===== 加入世界 =====
    async joinWorld() {
      try {
        await worldApi.join(this.worldId)
        uni.showToast({ title: '已加入, AI们欢迎你~', icon: 'none' })
        this.loadDetail()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '加入失败', icon: 'none' })
      }
    },

    // ===== 离开世界 =====
    leaveWorld() {
      uni.showModal({
        title: '退出世界',
        content: '确定要退出这个世界吗?',
        success: async (r) => {
          if (!r.confirm) return
          try {
            await worldApi.leave(this.worldId)
            uni.navigateBack()
          } catch (e) {
            uni.showToast({ title: '操作失败', icon: 'none' })
          }
        }
      })
    },

    // ===== 发布笔记(AI会跟评欢迎) =====
    async submitNote() {
      if (!this.noteContent.trim()) {
        uni.showToast({ title: '写点内容吧', icon: 'none' })
        return
      }
      try {
        await worldApi.publishNote(this.worldId, this.noteContent.trim())
        this.showNote = false
        this.noteContent = ''
        uni.showToast({ title: '已发布', icon: 'success' })
        this.loadDetail()
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '发布失败', icon: 'none' })
      }
    },

    // ===== 评论(AI回复 + 可能AI互评) =====
    openComment(n) {
      this.commentTarget = n
      this.commentContent = ''
    },
    async submitComment() {
      if (!this.commentContent.trim() || !this.commentTarget) return
      try {
        const res = await worldApi.comment(this.commentTarget.id, this.commentContent.trim())
        const newOnes = (res && res.data && res.data.comments) || []
        // 直接把新评论(含AI回复/互评)追加到该笔记评论里, 即时可见
        const target = this.notes.find(x => x.id === this.commentTarget.id)
        if (target) {
          target.comments = [...(target.comments || []), ...newOnes]
          target.comment_count = (res.data.comment_count !== undefined)
            ? res.data.comment_count : target.comment_count
        }
        this.commentTarget = null
        uni.showToast({ title: 'AI们回应了你', icon: 'none' })
      } catch (e) {
        uni.showToast({ title: (e && e.message) || '评论失败', icon: 'none' })
      }
    },

    // ===== 角色关系 =====
    async loadRelations() {
      try {
        const res = await worldApi.getRelations(this.worldId)
        this.relations = (res && res.data) || []
      } catch (e) {
        this.relations = []
      }
    }
  }
}
</script>

<style scoped>
/* 设计稿 img 在 H5 渲染为 uni-image，补齐尺寸与圆角 */
.xt-page.xt-s43 .residents uni-image {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  display: block;
}

/* ===== 弹窗（保留原有交互样式） ===== */
.modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(18, 28, 23, 0.55);
  z-index: 99;
  display: flex; align-items: center; justify-content: center;
}
.small-card {
  width: 640rpx;
  background: var(--v7-card);
  border-radius: 36rpx;
  padding: 36rpx 32rpx 32rpx;
  box-shadow: 0 30rpx 60rpx -30rpx rgba(12, 22, 17, 0.6);
}
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20rpx;
}
.modal-head-text { flex: 1; display: flex; flex-direction: column; }
.modal-title { font-size: 32rpx; font-weight: 800; color: #22302A; letter-spacing: 1rpx; }
.modal-sub { margin-top: 8rpx; font-size: 19rpx; color: #AEB6AE; }
.modal-close {
  width: 52rpx; height: 52rpx;
  border-radius: 50%;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  display: flex; align-items: center; justify-content: center;
  margin-left: 12rpx;
}
.modal-close-text { font-size: 20rpx; color: #8E9A91; }
.m-textarea {
  width: 100%; height: 180rpx;
  background: var(--v7-card);
  border-radius: 20rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
  padding: 20rpx 24rpx;
  color: #22302A;
  font-size: 25rpx;
  box-sizing: border-box;
}
.m-ph { color: #BFC7BF; }
.m-btns { display: flex; margin-top: 24rpx; }
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
