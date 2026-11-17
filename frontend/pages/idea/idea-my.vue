<template>
  <view class="xt-page xt-s40">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">我的小想法</view>
          <view class="page-sub">{{ list.length }} 句被认真读过</view>
        </view>
        <view class="icon-btn" @click="goPublish"><xt-icon name="i-plus" /></view>
      </view>

      <!-- 数据 -->
      <view class="stat-row">
        <view class="stat">
          <view class="v" style="font-size:16px;color:var(--v7-green)">{{ list.length }}</view>
          <view class="k" style="margin-top:2px">发布</view>
        </view>
        <view class="stat">
          <view class="v" style="font-size:16px;color:#B8874E">{{ lightTotal }}</view>
          <view class="k" style="margin-top:2px">被共鸣</view>
        </view>
        <view class="stat">
          <view class="v" style="font-size:16px;color:#C08A56">{{ reactTotal }}</view>
          <view class="k" style="margin-top:2px">收到回应</view>
        </view>
      </view>

      <view class="mom-tabs" style="margin-top:14px">
        <text class="on" style="color:#22302A">全部</text>
        <text>被共鸣</text>
        <text>草稿</text>
        <text>已归档</text>
      </view>

      <!-- 想法列表 -->
      <view
        v-for="(it, i) in list"
        :key="it.id"
        class="mem-item"
        @longpress="onDelete(it)"
      >
        <image
          v-if="it.image"
          class="mi-img"
          :src="it.image"
          mode="aspectFill"
          @click="preview(it)"
        />
        <view v-else class="mi" :class="tintOf(i)"><xt-icon :name="iconOf(i)" /></view>
        <view class="tx">
          <view class="t">“{{ it.content }}”</view>
          <view class="m">
            {{ it.create_time }} · {{ it.light_count || 0 }} 次共鸣<text v-if="it.react_count"> · {{ it.react_count }} 条回应</text><text v-if="it.is_anonymous"> · 匿名</text>
          </view>
        </view>
        <text class="v" style="font-size:7px;color:var(--v7-green);flex-shrink:0">已发布</text>
      </view>

      <!-- 空态 -->
      <view v-if="!loading && !list.length" class="mem-hero" style="margin-top:12px">
        <view class="t">还没有发布过小想法</view>
        <view class="m">不必完整，半句话也值得被听见。</view>
      </view>

      <view style="color:#BFC7BF;margin-top:14px;font-size:8px">有些想法不用解决，被看见就够了。</view>
    </view>
  </view>
</template>

<script>
/**
 * 小想法 · 我的想法列表
 * 数据来源：GET /idea/my-ideas
 *   → data.list[] = { id, content, image, is_anonymous, create_time,
 *                     light_count, react_count, matched_count }
 * 点亮 / 回应数仅本人可见，对外永不展示（隐私红线）。
 * 删除：DELETE /idea/my-ideas/{id}，后端级联清理共鸣与点亮记录。
 */
import ideaApi from '@/api/idea'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      list: [],
      loading: false,
      refreshing: false
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    lightTotal() {
      return this.list.reduce((sum, it) => sum + (it.light_count || 0), 0)
    },
    reactTotal() {
      return this.list.reduce((sum, it) => sum + (it.react_count || 0), 0)
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
  },
  onShow() {
    this.loadList()
  },
  methods: {
    async loadList() {
      this.loading = true
      try {
        const res = await ideaApi.getMyIdeas()
        this.list = ((res && res.data) || {}).list || []
      } catch (e) {
        /* request 层已 toast */
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    onRefresh() {
      this.refreshing = true
      this.loadList()
    },
    preview(it) {
      if (it.image) uni.previewImage({ urls: [it.image] })
    },
    onDelete(it) {
      uni.showModal({
        title: '删除这条想法？',
        content: '删除后相关的共鸣和点亮记录也会一起清除',
        confirmText: '删除',
        confirmColor: '#D98C6A',
        success: async (r) => {
          if (!r.confirm) return
          try {
            await ideaApi.deleteIdea(it.id)
            this.list = this.list.filter(x => x.id !== it.id)
            uni.showToast({ title: '已删除', icon: 'none' })
          } catch (e) { /* request 层已提示 */ }
        }
      })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.redirectTo({ url: '/pages/idea/idea-resonance' }) })
    },
    goPublish() {
      uni.navigateTo({ url: '/pages/idea/idea-publish' })
    },
    iconOf(i) {
      return ['i-spark', 'i-heart', 'i-moon'][i % 3]
    },
    tintOf(i) {
      return ['tint-green', 'tint-peach', 'tint-blue', 'tint-sand'][i % 4]
    }
  }
}
</script>

<style scoped>
/* 设计稿 img 在 H5 渲染为 uni-image，补齐尺寸/圆角 */
.xt-page.xt-s40 .mi-img,
.xt-page.xt-s40 uni-image.mi-img {
  display: block;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex-shrink: 0;
  overflow: hidden;
}
.xt-page.xt-s40 .mi-img :deep(div),
.xt-page.xt-s40 .mi-img :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s40 .mi-img :deep(img) {
  object-fit: cover;
}
</style>
