<template>
  <view class="xt-page xt-s53">
    <view class="body">
      <!-- 页头 -->
      <view class="page-title-row">
        <view class="ttl">
          <view class="icon-btn" @click="goBack"><xt-icon name="i-left" /></view>
          <view>
            <view class="page-title">专注动态</view>
            <view class="page-sub">{{ list.length }} 条记录 · 只有你和互关好友能看见</view>
          </view>
        </view>
        <view class="icon-btn" :class="{ on: showPublish }" @click="togglePublish">
          <xt-icon name="i-edit" />
        </view>
      </view>

      <!-- 此刻 -->
      <view class="pills">
        <view class="pill">
          <view class="v">{{ list.length }}<span> 条</span></view>
          <view class="k">此刻的记录</view>
        </view>
        <view class="pill">
          <view class="v">{{ mutualCount }}<span> 人</span></view>
          <view class="k">互关好友</view>
        </view>
      </view>

      <!-- 发布面板 -->
      <view v-if="showPublish" class="mem-hero" style="margin-bottom: 10px; padding: 11px">
        <textarea
          v-model="content" class="pub-input" :maxlength="500"
          placeholder="记录一下今天的学习/专注碎碎念…"
        />
        <image v-if="imagePreview" :src="imagePreview" class="pub-image" mode="widthFix" @click="previewImage" />
        <view class="pub-row">
          <view class="pub-vis" @click="cycleVis">
            <text class="pub-vis-text">{{ visibleType === 'self' ? '🔒 仅自己可见' : '👥 互关好友可见' }}</text>
          </view>
          <!-- #ifndef H5 -->
          <view class="pub-img-btn" @click="chooseImage">
            <text class="pub-img-text">📷 配图</text>
          </view>
          <!-- #endif -->
          <view class="pub-send" :class="{ busy: publishing }" @click="publish">
            <text class="pub-send-text">{{ publishing ? '发布中…' : '发布' }}</text>
          </view>
        </view>
      </view>

      <!-- 分区标题 -->
      <view class="cal-sec">
        <text class="t">此刻</text>
        <text class="s">安静模式 · 不显示排名</text>
      </view>

      <!-- 动态流 -->
      <view v-for="d in list" :key="d.id" class="post">
        <view class="post-head">
          <image v-if="d.avatar" class="post-av" :src="avatarOf(d)" mode="aspectFill" />
          <view v-else class="post-av post-av-t">
            <text>{{ (d.nickname || '用').slice(0, 1) }}</text>
          </view>
          <view class="post-who">
            <view class="post-name">
              <text>{{ d.nickname }}</text>
              <text v-if="d.uid === myUid" class="post-me">（我）</text>
            </view>
            <view class="post-time">{{ d.create_time }}</view>
          </view>
          <text class="post-role">{{ d.visible_type === 'self' ? '仅自己' : '互关' }}</text>
          <text v-if="d.uid === myUid" class="post-del" @click.stop="removeDyn(d)">删</text>
        </view>

        <view class="post-text">{{ d.content }}</view>
        <image v-if="d.image" class="post-img" :src="imageOf(d)" mode="widthFix" @click="previewDyn(d)" />

        <!-- 角色留言 -->
        <view v-if="d.comments && d.comments.length" class="post-comments">
          <view v-for="c in d.comments" :key="c.id" class="pc-item">
            <text class="pc-name" :class="{ ai: c.is_ai }">{{ c.nickname }}：</text>
            <text class="pc-text">{{ c.content }}</text>
          </view>
        </view>

        <view class="post-foot">
          <view class="foot-i" :class="{ liked: d.liked }" @click.stop="react(d)">
            <xt-icon name="i-heart" />
            <text>{{ d.like_count }}</text>
          </view>
          <view class="foot-i">
            <xt-icon name="i-chat" />
            <text>{{ (d.comments || []).length }}</text>
          </view>
          <text style="margin-left: auto; color: #BFC7BF">安静地陪着</text>
        </view>
      </view>

      <!-- 空态 -->
      <view v-if="!loading && !list.length" class="mem-hero" style="text-align: center; padding: 24px 14px">
        <view class="t">还没有动态</view>
        <view class="m">发布一条专注碎碎念，AI 伙伴会来给你鼓励</view>
      </view>

      <!-- 一起坐 -->
      <view class="auth-btn" style="margin-top: 2px" @click="togglePublish">
        <text>{{ showPublish ? '先不写了' : '我也坐一会儿' }}</text>
      </view>

      <view style="height: 18px"></view>
    </view>
  </view>
</template>

<script>
/**
 * 专注动态（轻动态，严禁公开广场）
 * -------------------------------
 * - 发布：visible_type = self(仅自己) / follow(互关好友)，走内容审核
 * - 动态流：只返回 自己 + 互关好友(follow) 的内容，没有任何公开列表
 * - 点赞幂等；发布后 AI 角色自动鼓励留言
 * - 与「小想法模块」完全独立，两套内容互不干扰
 */
import focusApi from '@/api/focus'
import http from '@/common/request'

export default {
  data() {
    return {
      statusBarHeight: 20,
      list: [],
      loading: false,
      refreshing: false,
      showPublish: false,
      content: '',
      imageRel: '',
      imagePreview: '',
      visibleType: 'self',
      publishing: false,
      mutualCount: 0,
      myUid: 0
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    // 当前用户 ID（复用现有登录态）
    try {
      const u = uni.getStorageSync('user_info') || {}
      this.myUid = u.id || 0
    } catch (e) { /* noop */ }
  },
  onShow() { this.load() },
  methods: {
    async load() {
      this.loading = true
      try {
        const [res, fs] = await Promise.all([focusApi.getDynamics(), focusApi.getFollows()])
        if (res && res.code === 200) this.list = res.data.list || []
        if (fs && fs.code === 200) this.mutualCount = (fs.data.list || []).length
      } catch (e) { /* noop */ } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onRefresh() {
      this.refreshing = true
      this.load()
    },
    togglePublish() { this.showPublish = !this.showPublish },
    cycleVis() {
      this.visibleType = this.visibleType === 'self' ? 'follow' : 'self'
    },

    /* ---------- 图片 ---------- */
    chooseImage() {
      uni.chooseImage({
        count: 1,
        success: async (r) => {
          const fp = r.tempFilePaths && r.tempFilePaths[0]
          if (!fp) return
          uni.showLoading({ title: '上传中…' })
          try {
            const res = await focusApi.uploadImage(fp)
            uni.hideLoading()
            if (res && res.code === 200) {
              this.imageRel = (res.data && res.data.path) || ''
              this.imagePreview = (res.data && res.data.url) || fp
            }
          } catch (e) { uni.hideLoading(); uni.showToast({ title: '上传失败', icon: 'none' }) }
        }
      })
    },
    previewImage() {
      if (this.imagePreview) uni.previewImage({ urls: [this.imagePreview] })
    },
    previewDyn(d) {
      const url = this.imageOf(d)
      if (url) uni.previewImage({ urls: [url] })
    },
    avatarOf(d) { return d.avatar ? http.toAvatarUrl(d.avatar) : '' },
    imageOf(d) { return d.image ? http.toStaticUrl(d.image) : '' },

    /* ---------- 发布 ---------- */
    async publish() {
      if (!(this.content || '').trim() && !this.imageRel) {
        uni.showToast({ title: '写点什么再发布吧', icon: 'none' }); return
      }
      if (this.publishing) return
      this.publishing = true
      try {
        const res = await focusApi.publishDynamic(this.content, this.imageRel, this.visibleType)
        if (res && res.code === 200) {
          this.content = ''
          this.imageRel = ''
          this.imagePreview = ''
          uni.showToast({ title: '已发布，AI 伙伴来看你啦', icon: 'none' })
          this.load()
        }
      } catch (e) { /* noop */ } finally { this.publishing = false }
    },

    /* ---------- 点赞（幂等） ---------- */
    async react(d) {
      try {
        const res = await focusApi.reactDynamic(d.id)
        if (res && res.code === 200) {
          d.liked = !!(res.data && res.data.liked)
          d.like_count += d.liked ? 1 : -1
        }
      } catch (e) { /* noop */ }
    },

    removeDyn(d) {
      uni.showModal({
        title: '删除动态', content: '删除后留言与点赞一并清除，确定吗？',
        success: async (m) => {
          if (!m.confirm) return
          await focusApi.deleteDynamic(d.id).catch(() => {})
          this.load()
        }
      })
    },

    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 动态较多时在内容区滚动 */
.xt-page.xt-s53 .body {
  overflow-y: auto;
  padding-bottom: 18px;
}
.xt-page.xt-s53 .page-title-row {
  padding-top: 10px;
}
.xt-page.xt-s53 .ttl {
  display: flex;
  align-items: center;
  gap: 9px;
}
.xt-page.xt-s53 .icon-btn.on {
  background: var(--v7-green);
  color: #F8F3E7;
  box-shadow: none;
}

/* 头像 / 配图尺寸同步到 uni-image 包装层 */
.xt-page.xt-s53 .post-av,
.xt-page.xt-s53 .post-av uni-image {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.xt-page.xt-s53 .post-av :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.xt-page.xt-s53 .post-av-t {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(140deg, #ACC2B8, var(--v7-green));
  color: #FFFDFA;
  font-size: 11px;
  font-weight: 900;
}
.xt-page.xt-s53 .post-img,
.xt-page.xt-s53 .post-img uni-image {
  width: 100%;
  height: auto;
  border-radius: 12px;
  overflow: hidden;
  display: block;
}
.xt-page.xt-s53 .post-img :deep(div) {
  background-size: contain;
  background-position: center;
}
.xt-page.xt-s53 .post-img :deep(img) {
  width: 100%;
  height: auto;
  object-fit: contain;
}

/* 头像旁的标记与删除 */
.xt-page.xt-s53 .post-me {
  font-size: 7px;
  color: #AEB6AE;
}
.xt-page.xt-s53 .post-del {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(192, 138, 86, 0.12);
  font-size: 7px;
  color: #B57F4C;
}

/* 留言 */
.xt-page.xt-s53 .post-comments {
  margin-top: 8px;
  padding: 8px 9px;
  border-radius: 11px;
  background: rgba(248, 244, 236, 0.9);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s53 .pc-item {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 3px;
}
.xt-page.xt-s53 .pc-item:last-child {
  margin-bottom: 0;
}
.xt-page.xt-s53 .pc-name {
  font-size: 8px;
  font-weight: 800;
  color: #6E9B81;
}
.xt-page.xt-s53 .pc-name.ai {
  color: #B57F4C;
}
.xt-page.xt-s53 .pc-text {
  flex: 1;
  font-size: 8px;
  line-height: 1.55;
  color: #3C5248;
}

/* 点赞 / 留言入口 */
.xt-page.xt-s53 .foot-i {
  display: flex;
  align-items: center;
  gap: 4px;
}
.xt-page.xt-s53 .foot-i.liked {
  color: #B57F4C;
}

/* 发布面板 */
.xt-page.xt-s53 .pub-input {
  width: 100%;
  height: 74px;
  font-size: 9px;
  line-height: 1.7;
  color: #22302A;
}
.xt-page.xt-s53 .pub-image {
  margin-top: 7px;
  width: 100%;
  height: auto;
  border-radius: 10px;
  display: block;
}
.xt-page.xt-s53 .pub-image :deep(div) {
  background-size: contain;
  background-position: center;
}
.xt-page.xt-s53 .pub-image :deep(img) {
  width: 100%;
  height: auto;
  object-fit: contain;
}
.xt-page.xt-s53 .pub-row {
  display: flex;
  align-items: center;
  margin-top: 8px;
}
.xt-page.xt-s53 .pub-vis {
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s53 .pub-vis-text {
  font-size: 7.5px;
  color: #6A776E;
}
.xt-page.xt-s53 .pub-img-btn {
  margin-left: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s53 .pub-img-text {
  font-size: 7.5px;
  color: #B57F4C;
}
.xt-page.xt-s53 .pub-send {
  margin-left: auto;
  padding: 6px 16px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4E7A64, #24493A);
}
.xt-page.xt-s53 .pub-send.busy {
  opacity: 0.6;
}
.xt-page.xt-s53 .pub-send-text {
  font-size: 8.5px;
  font-weight: 900;
  color: #FFFDFA;
}
</style>
