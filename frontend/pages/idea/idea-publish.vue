<template>
  <view class="xt-page xt-s38">
    <view class="body">
      <!-- 顶部：返回 / 标题 / 存草稿 -->
      <view class="chat-head" style="padding:2px 2px 12px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">写下一个小想法</view>
          <view class="chat-st">不需要标题，也不需要结论</view>
        </view>
        <text class="icon-btn" style="font-size:8px;font-weight:800;color:var(--v7-green)" @click="saveDraft">存草稿</text>
      </view>

      <!-- 书写卡 -->
      <view class="mood-card" style="padding:15px">
        <textarea
          v-model="content"
          class="mood-input"
          placeholder="此刻，你想说的话"
          maxlength="300"
          :auto-height="true"
          :show-confirm-bar="false"
          style="width:100%;min-height:150px;background:#fff;padding:0;font-size:11px;line-height:1.85;color:#22302A"
        />
        <view style="text-align:right;margin-top:6px;font-size:7px;color:#CFD6CE">{{ content.length }} / 300</view>
      </view>

      <view class="cal-sec" style="margin-top:12px">
        <text class="t">此刻的心情</text>
        <text class="s">可多选</text>
      </view>
      <view class="chips">
        <text
          v-for="m in moodOptions"
          :key="m"
          class="chip"
          :class="{ on: moods.includes(m) }"
          @click="toggleMood(m)"
        >{{ m }}</text>
        <text class="chip" @click="chooseImage">＋ 配图</text>
      </view>

      <!-- 配图预览 -->
      <view v-if="imagePath" class="pick-cell">
        <image class="pick-img" :src="imagePath" mode="aspectFill" />
        <view class="pick-del" @click="removeImage"><text>×</text></view>
      </view>

      <view class="cal-sec" style="margin-top:12px">
        <text class="t">谁会看到</text>
        <text class="s">默认只给同类的人</text>
      </view>
      <view class="seg">
        <text class="seg-i" :class="{ on: visibility === 'same' }" @click="setVisibility('same')">同频的人</text>
        <text class="seg-i" :class="{ on: visibility === 'all' }" @click="setVisibility('all')">所有人</text>
        <text class="seg-i" :class="{ on: visibility === 'self' }" @click="setVisibility('self')">仅自己</text>
      </view>

      <!-- 匿名 -->
      <view class="set-row" style="margin-top:12px">
        <view class="si tint-green"><xt-icon name="i-user" /></view>
        <view class="tx">
          <view class="t">匿名发布</view>
          <view class="m">不显示头像和昵称，只显示“一个和你相似的人”</view>
        </view>
        <view class="switch2" :class="{ on: isAnonymous }" @click="isAnonymous = !isAnonymous"></view>
      </view>

      <!-- 她会怎么说 -->
      <view class="ai-rec">
        <view class="sp"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <text class="k">林夕读完了</text>
          <text class="p">“要不要我陪你把‘一起开始’变成一个今天就能做的小事？”</text>
        </view>
      </view>

      <view
        class="auth-btn"
        :class="{ disabled: !canPublish || submitting }"
        style="margin-top:12px"
        @click="onPublish"
      >{{ submitting ? '发布中…' : '发出去' }}</view>
    </view>
  </view>
</template>

<script>
/**
 * 小想法 · 发布页
 * 发布成功后立即跳转「我的共鸣列表页」（用 redirectTo，避免返回到本页）。
 */
import ideaApi from '@/api/idea'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      statusBarHeight: 20,
      content: '',
      imagePath: '',      // 本地临时路径（预览用）
      imageUrl: '',       // 上传后的云端 URL
      isAnonymous: false,
      visibility: 'same',   // 后端目前只支持同频匹配，其余范围尚未开放
      moodOptions: ['有点累', '想被理解', '平静', '期待'],
      moods: [],
      submitting: false
    }
  },
  computed: {
    navBodyTop() { return this.statusBarHeight + 44 },
    canPublish() { return this.content.trim().length > 0 }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.statusBarHeight = sys.statusBarHeight || 20
    // 恢复本地草稿
    try {
      const draft = uni.getStorageSync('idea_publish_draft')
      if (draft && draft.content) {
        this.content = draft.content
        this.moods = draft.moods || []
      }
    } catch (e) {}
  },
  methods: {
    toggleMood(m) {
      const i = this.moods.indexOf(m)
      if (i > -1) this.moods.splice(i, 1)
      else this.moods.push(m)
    },
    setVisibility(v) {
      if (v !== 'same') {
        uni.showToast({ title: '该可见范围暂未开放，当前按同频匹配发布', icon: 'none' })
        return
      }
      this.visibility = v
    },
    saveDraft() {
      if (!this.content.trim()) {
        uni.showToast({ title: '还没写内容', icon: 'none' })
        return
      }
      try {
        uni.setStorageSync('idea_publish_draft', {
          content: this.content,
          moods: this.moods,
          time: Date.now()
        })
        uni.showToast({ title: '草稿已保存', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: '草稿保存失败', icon: 'none' })
      }
    },
    chooseImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.imagePath = res.tempFilePaths[0]
          this.imageUrl = ''   // 重新选择，需重新上传
        }
      })
    },
    removeImage() {
      this.imagePath = ''
      this.imageUrl = ''
    },
    async onPublish() {
      if (!this.canPublish || this.submitting) return
      this.submitting = true

      // 单图先上传（若已选但未上传）
      if (this.imagePath && !this.imageUrl) {
        uni.showLoading({ title: '上传配图中…', mask: true })
        try {
          const up = await ideaApi.uploadImage(this.imagePath)
          this.imageUrl = (up && up.data && up.data.url) || ''
        } catch (e) {
          uni.hideLoading()
          uni.showToast({ title: e.message || '配图上传失败', icon: 'none' })
          this.submitting = false
          return
        }
        uni.hideLoading()
      }

      try {
        const res = await ideaApi.publish({
          content: this.content.trim(),
          image: this.imageUrl,
          is_anonymous: this.isAnonymous
        })
        uni.setStorageSync('idea_welcomed', '1')
        try { uni.removeStorageSync('idea_publish_draft') } catch (e) {}
        const count = (res && res.data && res.data.resonance_count) || 0
        uni.showToast({
          title: count > 0 ? `遇见 ${count} 个共鸣` : '已发布，正在寻找同频的人',
          icon: 'none',
          duration: 1500
        })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/idea/idea-resonance' })
        }, 900)
      } catch (e) {
        uni.showToast({ title: e.message || '发布失败', icon: 'none' })
      } finally {
        this.submitting = false
      }
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.redirectTo({ url: '/pages/idea/idea-resonance' }) })
    }
  }
}
</script>

<style scoped>
/* 设计稿 img 在 H5 渲染为 uni-image，补齐尺寸/圆角 */
.xt-page.xt-s38 .pick-img,
.xt-page.xt-s38 uni-image.pick-img {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
}
.xt-page.xt-s38 .pick-img :deep(div),
.xt-page.xt-s38 .pick-img :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s38 .pick-img :deep(img) {
  object-fit: cover;
}
.xt-page.xt-s38 .pick-cell {
  position: relative;
  width: 64px;
  height: 64px;
  margin-top: 2px;
  border-radius: 10px;
  overflow: hidden;
  background: #F3EFE5;
}
.xt-page.xt-s38 .pick-del {
  position: absolute;
  right: 0;
  top: 0;
  width: 18px;
  height: 18px;
  border-radius: 0 0 0 8px;
  background: rgba(34, 48, 42, .6);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
}

/* 设计稿 .seg span 的元素选择器 → 等价 class */
.xt-page.xt-s38 .seg .seg-i {
  flex: 1;
  padding: 7px 0;
  border-radius: 9px;
  text-align: center;
  font-size: 8px;
  color: #8E9A91;
  background: var(--v7-card);
}
.xt-page.xt-s38 .seg .seg-i.on {
  color: #26332C;
  font-weight: 900;
  background: #fff;
  box-shadow: 0 0 0 1px var(--v7-line);
}

/* 设计稿 .set-row .switch2 默认不可点，这里开放匿名开关 */
.xt-page.xt-s38 .set-row .switch2 {
  pointer-events: auto;
}

.xt-page.xt-s38 .auth-btn.disabled {
  opacity: .45;
  box-shadow: none;
}
</style>
