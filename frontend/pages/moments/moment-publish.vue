<template>
  <view class="xt-page xt-s46">
    <view class="body">
      <!-- 页头 -->
      <view class="chat-head" style="padding:2px 2px 12px">
        <view class="back" @click="goBack">
          <xt-icon name="i-left" />
        </view>
        <view class="chat-meta">
          <view class="chat-name">发一条动态</view>
          <view class="chat-st">记录今天，也让她看见</view>
        </view>
        <text class="icon-btn" style="font-size:8px;font-weight:800;color:var(--v7-green)" @click="onPublish">发布</text>
      </view>

      <!-- 文字 + 图片 -->
      <view class="mood-card" style="padding:13px">
        <textarea
          v-model="content"
          class="mood-input"
          placeholder="这一刻的想法..."
          maxlength="500"
          :auto-height="true"
          style="width:100%;min-height:88px;background:#fff;padding:0;font-size:10.5px;line-height:1.8"
        />
        <view style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px">
          <view
            v-for="(img, idx) in images"
            :key="idx"
            class="pub-cell"
            style="height:76px;border-radius:10px;overflow:hidden;position:relative;background:#F3EFE5"
          >
            <image class="pub-img" :src="img" mode="aspectFill" />
            <view class="pub-del" @click="removeImage(idx)">
              <text>×</text>
            </view>
          </view>
          <view
            v-if="images.length < 9"
            class="pub-add"
            style="height:76px;border-radius:10px;background:#FFFDFA;border:1px dashed #D3DBD7;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;color:#AEB6AE;font-size:6.5px"
            @click="chooseImage"
          >
            <xt-icon name="i-plus" />
            <text>添加</text>
          </view>
        </view>
      </view>

      <!-- 位置 -->
      <view class="set-row" style="margin-top:10px">
        <view class="si tint-green">
          <xt-icon name="i-world" />
        </view>
        <view class="tx">
          <input
            class="t loc-input"
            v-model="location"
            :focus="locFocus"
            placeholder="雾港 · 海堤"
            placeholder-style="color:#BFC7BF"
          />
          <text class="m">和她的当前位置关联</text>
        </view>
        <text class="v" @click="editLocation">更改</text>
      </view>

      <!-- 可见范围 -->
      <view class="seg" style="margin-top:2px">
        <text class="seg-i" :class="{ on: visibility === 'all' }" @click="setVisibility('all')">所有人</text>
        <text class="seg-i" :class="{ on: visibility === 'partner' }" @click="setVisibility('partner')">仅伙伴</text>
        <text class="seg-i" :class="{ on: visibility === 'self' }" @click="setVisibility('self')">仅自己</text>
      </view>

      <!-- 她会怎么回应 -->
      <view class="ai-rec" style="margin-top:11px">
        <view class="sp">
          <xt-icon name="i-spark" />
        </view>
        <view class="tx">
          <text class="k">{{ aiName }}大概会这样说</text>
          <text class="p">"那我也把窗关小一点。你搬花的时候，记得慢一点。"</text>
        </view>
      </view>

      <!-- 小标签 -->
      <view class="chips" style="margin-top:9px">
        <text class="chip" @click="mentionPartner">@ 她</text>
        <text class="chip" :class="{ on: syncIdea }" @click="toggleSyncIdea">同步到小想法</text>
        <text class="chip" :class="{ on: allowAiComment }" @click="toggleAllowAiComment">允许她评论</text>
      </view>

      <!-- 发布按钮 -->
      <view
        class="auth-btn"
        :class="{ disabled: !canPublish || uploading }"
        style="margin-top:12px"
        @click="onPublish"
      >{{ publishingText }}</view>
    </view>
  </view>
</template>

<script>
import momentApi from '@/api/moment'
import ideaApi from '@/api/idea'
// ↓↓↓ 安全合规批次：发布内容本地前置校验（后端同源兜底） ↓↓↓
import { checkContent, checkDanger } from '@/common/content-check'
// ↑↑↑ 新增结束 ↑↑↑
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      content: '',
      images: [],
      location: '',
      locFocus: false,
      visibility: 'all',      // 后端暂无可见范围字段，仅「所有人」生效
      syncIdea: false,
      allowAiComment: true,
      uploading: false
    }
  },
  computed: {
    canPublish() {
      return this.content.trim().length > 0 || this.images.length > 0
    },
    publishingText() {
      if (this.uploading) return '发布中...'
      return '发布'
    },
    // ↓↓↓ 新增 ↓↓↓ 设计稿中的角色名称
    aiName() {
      const cfg = this.$store && this.$store.state && this.$store.state.aiConfig
      return (cfg && cfg.name) || '林夕'
    }
  },
  methods: {
    goBack() {
      uni.navigateBack({
        fail: () => uni.redirectTo({ url: '/pages/moments/moments' })
      })
    },
    editLocation() {
      // 无地图选点能力：聚焦输入框让用户直接改，至少点得动
      this.locFocus = false
      this.$nextTick(() => { this.locFocus = true })
      uni.showToast({ title: '可直接输入位置', icon: 'none', duration: 900 })
    },
    setVisibility(v) {
      if (v !== 'all') {
        uni.showToast({ title: '该可见范围暂未开放，当前所有人可见', icon: 'none' })
        return
      }
      this.visibility = v
    },
    mentionPartner() {
      const tag = '@' + this.aiName + ' '
      if (this.content.includes(tag)) {
        uni.showToast({ title: '已经 @ 过她了', icon: 'none' })
        return
      }
      this.content = (this.content ? this.content + ' ' : '') + tag
    },
    toggleSyncIdea() {
      this.syncIdea = !this.syncIdea
      uni.showToast({ title: this.syncIdea ? '发布后同步到小想法' : '已取消同步', icon: 'none', duration: 900 })
    },
    toggleAllowAiComment() {
      this.allowAiComment = !this.allowAiComment
      uni.showToast({ title: this.allowAiComment ? '她可以看到并回应' : '她不会回应这条', icon: 'none', duration: 900 })
    },
    chooseImage() {
      const remain = 9 - this.images.length
      if (remain <= 0) {
        uni.showToast({ title: '最多上传9张图片', icon: 'none' })
        return
      }
      uni.chooseImage({
        count: remain,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.images = this.images.concat(res.tempFilePaths)
        }
      })
    },
    removeImage(idx) {
      this.images.splice(idx, 1)
    },
    async onPublish() {
      if (!this.canPublish || this.uploading) return
      this.uploading = true

      // ↓↓↓ 安全合规批次：文本内容本地安全校验，命中直接拦截 ↓↓↓
      const _text = this.content.trim()
      if (_text) {
        const _danger = checkDanger(_text)
        if (_danger.isDanger) {
          this.uploading = false
          uni.showModal({
            title: '我们有点担心你',
            content: _danger.message,
            showCancel: false,
            confirmText: '我知道了'
          })
          return
        }
        const _sec = checkContent(_text)
        if (!_sec.ok) {
          this.uploading = false
          uni.showToast({ title: _sec.reason, icon: 'none', duration: 2500 })
          return
        }
      }
      // ↑↑↑ 新增结束 ↑↑↑

      // === 两步发布流程 ===
      // Step1: 逐张上传图片获取 URL (uni.uploadFile 不支持多文件 multipart)
      let imageUrls = []
      if (this.images.length > 0) {
        uni.showLoading({ title: '上传图片中...', mask: true })
        try {
          for (const filePath of this.images) {
            const res = await momentApi.uploadImage(filePath)
            if (res && res.data && res.data.url) {
              imageUrls.push(res.data.url)
            }
          }
          uni.hideLoading()
        } catch (e) {
          uni.hideLoading()
          uni.showToast({ title: e.message || '图片上传失败', icon: 'none' })
          this.uploading = false
          return
        }
      }

      // Step2: 用 URL 数组创建动态
      try {
        await momentApi.publish({
          content: this.content.trim(),
          images: imageUrls,
          location: this.location.trim()
        })
        // 勾选「同步到小想法」时，复用已有的 /idea/publish 接口再发一份（失败不阻断）
        if (this.syncIdea) {
          ideaApi.publish({
            content: this.content.trim(),
            image: imageUrls[0] || '',
            is_anonymous: false
          }).catch(() => {})
        }
        uni.showToast({ title: '发布成功', icon: 'success' })
        setTimeout(() => {
          uni.navigateBack({ fail: () => uni.redirectTo({ url: '/pages/moments/moments' }) })
        }, 800)
      } catch (e) {
        uni.showToast({ title: e.message || '发布失败', icon: 'none' })
      } finally {
        this.uploading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间 */
.xt-page.xt-s46 .body {
  padding-bottom: 24px;
}

/* 位置输入：uni-input 尺寸对齐设计稿 .t */
.xt-page.xt-s46 .loc-input {
  width: 100%;
  height: 14px;
  font-size: 9px;
  font-weight: 800;
  color: #22302A;
}

/* 设计稿 .seg 依赖 span 元素选择器，改用同名 class 补等价规则 */
.xt-page.xt-s46 .seg .seg-i {
  flex: 1;
  padding: 7px 0;
  border-radius: 9px;
  text-align: center;
  font-size: 8px;
  color: #8E9A91;
  background: var(--v7-card);
}

/* 设计稿 img 尺寸同步到 uni-image 包装层 */
.xt-page.xt-s46 .pub-cell uni-image {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
  display: block;
}
.xt-page.xt-s46 .pub-cell :deep(uni-image > div),
.xt-page.xt-s46 .pub-cell :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s46 .pub-cell :deep(uni-image img) {
  object-fit: cover;
}

/* 图片删除按钮 */
.xt-page.xt-s46 .pub-del {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(34, 48, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}
.xt-page.xt-s46 .pub-del text {
  color: #fff;
  font-size: 11px;
  line-height: 1;
}

.xt-page.xt-s46 .auth-btn.disabled {
  opacity: 0.45;
}
</style>
