<template>
  <view class="xt-page xt-s6">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view>
          <view class="page-title">朋友圈</view>
          <view class="page-sub">她和你的日常，都在这里</view>
        </view>
        <view class="icon-btn" @click="goPublish">
          <xt-icon name="i-edit" />
        </view>
      </view>

      <!-- 分类 -->
      <view class="mom-tabs">
        <text
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ on: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</text>
      </view>

      <!-- 动态列表 -->
      <view class="moments-list" v-if="shownMoments.length > 0">
        <view class="post" v-for="item in shownMoments" :key="item.id">
          <view class="post-head">
            <image
              v-if="postPhoto(item)"
              :src="postPhoto(item)"
              class="post-av"
              mode="aspectFill"
            />
            <view v-else class="post-av post-av-t">
              <text>{{ postInitial(item) }}</text>
            </view>
            <view class="post-who">
              <view class="post-name">
                <text>{{ (item.author && item.author.nickname) || (item.isAI ? aiName : '匿名用户') }}</text>
                <text v-if="item.isAI" class="post-role">AI 伙伴</text>
              </view>
              <view class="post-time">{{ postMeta(item) }}</view>
            </view>
            <text
              v-if="item.user_id === currentUserId"
              class="post-more"
              @click.stop="onDelete(item)"
            >⋯</text>
          </view>

          <view class="post-text" v-if="item.content">{{ item.content }}</view>

          <image
            v-for="(img, idx) in (item.images || [])"
            :key="idx"
            :src="img"
            class="post-img"
            mode="widthFix"
            @click="previewImages(item, idx)"
          />

          <!-- 【修复】原来只是链接外观，现在可进入伙伴页继续 -->
          <view class="post-link" v-if="item.habitName" @click.stop="goCompanion">
            <xt-icon name="i-book" />
            <text>{{ item.habitName }} · 一起继续</text>
          </view>

          <view class="post-foot">
            <view class="foot-i" :class="{ liked: item.liked }" @click.stop="onLike(item)">
              <xt-icon name="i-heart" />
              <text>{{ item.like_count > 0 ? item.like_count : '赞' }}</text>
            </view>
            <view class="foot-i" @click.stop="openComments(item)">
              <xt-icon name="i-chat" />
              <text>{{ item.comment_count > 0 ? item.comment_count + ' 条回应' : '评论' }}</text>
            </view>
            <view class="foot-i" style="margin-left:auto">
              <xt-icon name="i-spark" />
              <text>收藏</text>
            </view>
          </view>

          <!-- 评论（保留原有评论交互） -->
          <view class="post-comments" v-if="commentMomentId === item.id">
            <view class="pc-item" v-for="c in comments" :key="c.id">
              <text class="pc-user">{{ c.user && c.user.nickname }}</text>
              <text class="pc-text">：{{ c.content }}</text>
            </view>
            <view class="pc-row">
              <input
                v-model="commentText"
                class="pc-input"
                placeholder="说点什么..."
                confirm-type="send"
                @confirm="submitComment(item)"
              />
              <view class="pc-send" @click="submitComment(item)">
                <text>发送</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view class="empty-wrap" v-else-if="!loading">
        <text class="empty-title">还没有动态</text>
        <text class="empty-desc">成为第一个分享的人吧</text>
      </view>

      <!-- 加载中 -->
      <view class="loading-wrap" v-if="loading">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 加载完毕提示 -->
      <view class="end-tip" v-if="!loading && noMore && moments.length > 0">
        <text>· 没有更多了 ·</text>
      </view>
    </view>
  </view>
</template>

<script>
import momentApi from '@/api/moment'
import userApi from '@/api/user'
import aiSocial from '@/common/ai-social'
// ↓↓↓ 新增 ↓↓↓ 统一拼头像地址
import { toAvatarUrl } from '@/common/request'
// ↓↓↓ 新增 ↓↓↓ 设计稿角色头像
import { getActivePartner, getActivePartnerId, getPartnerAvatar } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      moments: [],
      page: 1,
      pageSize: 20,
      loading: false,
      noMore: false,
      currentUserId: 0,
      userNickname: '',
      userAvatar: '',
      hasLoaded: false,
      activeTab: 'all',
      tabs: [
        { key: 'all', label: '全部' },
        { key: 'ai', label: '伙伴' },
        { key: 'me', label: '我' }
      ],
      // ↓↓↓ 新增 ↓↓↓ 评论展开状态（沿用原有评论接口）
      commentMomentId: null,
      comments: [],
      commentText: ''
    }
  },
  computed: {
    shownMoments() {
      if (this.activeTab === 'ai') return this.moments.filter(m => m.isAI)
      if (this.activeTab === 'me') return this.moments.filter(m => m.user_id === this.currentUserId)
      return this.moments
    },
    userInitial() {
      if (this.userNickname) return this.userNickname.charAt(0).toUpperCase()
      return '我'
    },
    // ↓↓↓ 新增 ↓↓↓ 把取到的头像（可能是相对路径）转成可直接用的地址
    avatarUrl() {
      return toAvatarUrl(this.userAvatar)
    },
    // ↓↓↓ 新增 ↓↓↓ 当前角色头像 / 名称
    aiRoleId() {
      return getActivePartnerId()
    },
    aiPhoto() {
      return getPartnerAvatar(this.aiRoleId)
    },
    aiName() {
      return getActivePartner().name || 'AI伙伴'
    }
  },
  onLoad() {
    this.loadUserInfo()
    this.loadMoments(true).finally(() => {
      this.hasLoaded = true
    })
  },
  onPullDownRefresh() {
    this.loadMoments(true).finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  onReachBottom() {
    if (!this.noMore && !this.loading) {
      this.loadMoments(false)
    }
  },
  onShow() {
    // 从发布页返回时刷新(首次 onLoad 已加载过则跳过)
    if (this.hasLoaded) {
      this.loadMoments(true)
    }
  },
  methods: {
    /** 【新增】习惯链接：进入伙伴页继续陪她做 */
    goCompanion() {
      uni.navigateTo({ url: '/pages/companion/companion' })
    },
    async loadUserInfo() {
      try {
        const res = await userApi.getUserInfo()
        if (res && res.data) {
          this.currentUserId = res.data.id || 0
          this.userNickname = res.data.nickname || res.data.username || ''
          this.userAvatar = res.data.avatar || ''
        }
      } catch (e) {
        // 静默
      }
    },
    async loadMoments(reset = false) {
      if (this.loading) return
      this.loading = true
      if (reset) {
        this.page = 1
        this.noMore = false
      }
      try {
        const res = await momentApi.getList(this.page, this.pageSize)
        const list = (res.data && res.data.list) || []
        if (reset) {
          // AI伙伴动态叠加在列表顶部（本地生成，含打卡关联动态）
          const aiMoments = aiSocial.getAIMoments()
          this.moments = [...aiMoments, ...list]
        } else {
          this.moments = this.moments.concat(list)
        }
        if (list.length < this.pageSize) {
          this.noMore = true
        } else {
          this.page++
        }
      } catch (e) {
        // 后端不可达时仅展示AI动态，避免白屏
        if (reset) {
          this.moments = aiSocial.getAIMoments()
          this.noMore = true
          if (this.moments.length === 0) {
            uni.showToast({ title: e.message || '加载失败', icon: 'none' })
          }
        }
      } finally {
        this.loading = false
      }
    },
    goPublish() {
      uni.navigateTo({ url: '/pages/moments/moment-publish' })
    },
    async onLike(moment) {
      // AI伙伴动态：本地点赞
      if (moment.isAI) {
        const res = aiSocial.toggleLikeAIMoment(moment.id)
        if (res) {
          const idx = this.moments.findIndex(m => m.id === moment.id)
          if (idx > -1) {
            this.$set(this.moments, idx, {
              ...this.moments[idx],
              liked: res.liked,
              like_count: res.like_count
            })
          }
        }
        return
      }
      try {
        const res = await momentApi.toggleLike(moment.id)
        const idx = this.moments.findIndex(m => m.id === moment.id)
        if (idx > -1) {
          this.$set(this.moments, idx, {
            ...this.moments[idx],
            liked: res.data.liked,
            like_count: res.data.like_count
          })
        }
      } catch (e) {
        uni.showToast({ title: e.message || '操作失败', icon: 'none' })
      }
    },
    onComment(moment) {
      // 评论在页内展开式呈现,此处仅刷新评论计数
      const idx = this.moments.findIndex(m => m.id === moment.id)
      if (idx > -1) {
        this.$set(this.moments, idx, {
          ...this.moments[idx],
          comment_count: (this.moments[idx].comment_count || 0) + 1
        })
      }
    },
    async onDelete(moment) {
      // AI伙伴动态：本地删除
      if (moment.isAI) {
        uni.showModal({
          title: '提示',
          content: '确定删除这条AI动态吗?',
          success: (r) => {
            if (r.confirm) {
              aiSocial.deleteAIMoment(moment.id)
              this.moments = this.moments.filter(m => m.id !== moment.id)
              uni.showToast({ title: '已删除', icon: 'success' })
            }
          }
        })
        return
      }
      uni.showModal({
        title: '提示',
        content: '确定删除这条动态吗?',
        success: async (r) => {
          if (r.confirm) {
            try {
              await momentApi.delete(moment.id)
              uni.showToast({ title: '已删除', icon: 'success' })
              this.moments = this.moments.filter(m => m.id !== moment.id)
            } catch (e) {
              uni.showToast({ title: e.message || '删除失败', icon: 'none' })
            }
          }
        }
      })
    },
    // ↓↓↓ 新增 ↓↓↓ 展示用字段映射
    postPhoto(moment) {
      if (moment.isAI) return this.aiPhoto
      return toAvatarUrl(moment.author && moment.author.avatar)
    },
    postInitial(moment) {
      const name = (moment.author && moment.author.nickname) || (moment.isAI ? this.aiName : '')
      if (name) return name.charAt(0).toUpperCase()
      return moment.isAI ? '她' : '我'
    },
    postMeta(moment) {
      const raw = moment && moment.created_at ? String(moment.created_at).replace(/-/g, '/') : ''
      const time = raw ? raw.slice(5, 16) : '今天'
      return moment && moment.location ? `${time} · ${moment.location}` : time
    },
    previewImages(moment, idx) {
      const urls = (moment && moment.images) || []
      if (!urls.length) return
      uni.previewImage({ urls, current: urls[idx] })
    },
    // ↓↓↓ 新增 ↓↓↓ 评论展开（沿用原有评论接口）
    async openComments(moment) {
      if (this.commentMomentId === moment.id) {
        this.commentMomentId = null
        return
      }
      this.commentMomentId = moment.id
      this.commentText = ''
      this.comments = []
      if (moment.isAI) {
        this.comments = aiSocial.getAIComments(moment.id)
        return
      }
      try {
        const res = await momentApi.getComments(moment.id)
        this.comments = (res.data) || []
      } catch (e) {
        // 静默
      }
    },
    async submitComment(moment) {
      const text = this.commentText.trim()
      if (!text) {
        uni.showToast({ title: '请输入评论', icon: 'none' })
        return
      }
      if (moment.isAI) {
        let nickname = '我'
        try {
          nickname = this.$store.state.userInfo.nickname || '我'
        } catch (e) { /* 静默 */ }
        this.comments = aiSocial.commentAIMoment(moment.id, text, nickname)
        this.commentText = ''
        this.onComment(moment)
        uni.showToast({ title: '评论成功', icon: 'success' })
        return
      }
      try {
        const res = await momentApi.comment(moment.id, text)
        this.comments.push(res.data)
        this.commentText = ''
        this.onComment(moment)
        uni.showToast({ title: '评论成功', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.message || '评论失败', icon: 'none' })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部为原生 tabBar 留出空间 */
.xt-page.xt-s6 .body {
  padding-bottom: calc(66px + env(safe-area-inset-bottom));
}

/* 设计稿 img 尺寸/圆角同步到 uni-image 包装层 */
.xt-page.xt-s6 .post-av,
.xt-page.xt-s6 .post-av uni-image {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.xt-page.xt-s6 .post-img,
.xt-page.xt-s6 .post-img uni-image {
  width: 100%;
  height: auto;
  border-radius: 12px;
  overflow: hidden;
  display: block;
}
.xt-page.xt-s6 .post-av :deep(img) {
  object-fit: cover;
}
.xt-page.xt-s6 .post-img :deep(div) {
  background-size: contain;
  background-position: center;
}
.xt-page.xt-s6 .post-img :deep(img) {
  width: 100%;
  height: auto;
  object-fit: contain;
}

/* 无头像时的首字母兜底 */
.post-av-t {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(140deg, #ACC2B8, var(--v7-green));
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}
.post-more {
  padding-left: 6px;
  font-size: 12px;
  line-height: 1;
  color: #CFD6CE;
}

/* 设计稿用 i 元素选择器，改用同名 class 补一条同效果规则 */
.post-foot .foot-i {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 空状态 / 加载 / 评论展开 */
.empty-wrap,
.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 0 20px;
}
.empty-title {
  font-size: 12px;
  font-weight: 800;
  color: #6A776E;
}
.empty-desc {
  margin-top: 5px;
  font-size: 9.5px;
  color: #AEB6AE;
}
.loading-text {
  font-size: 9.5px;
  color: #AEB6AE;
}
.end-tip {
  padding: 12px 0 6px;
  text-align: center;
  font-size: 8px;
  color: #B4BDB9;
}
.post-comments {
  margin-top: 8px;
  padding: 8px 9px;
  border-radius: 11px;
  background: var(--v7-card);
}
.pc-item {
  padding: 2px 0;
  font-size: 8.5px;
  line-height: 1.6;
}
.pc-user {
  color: var(--v7-green);
  font-weight: 800;
}
.pc-text {
  color: #4B5A51;
}
.pc-row {
  display: flex;
  align-items: center;
  margin-top: 6px;
}
.pc-input {
  flex: 1;
  height: 26px;
  padding: 0 10px;
  border-radius: 99px;
  background: #fff;
  font-size: 8.5px;
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.pc-send {
  margin-left: 6px;
  padding: 5px 11px;
  border-radius: 99px;
  background: linear-gradient(140deg, #6E9B81, var(--v7-green));
}
.pc-send text {
  color: #fff;
  font-size: 8px;
  font-weight: 800;
}
</style>
