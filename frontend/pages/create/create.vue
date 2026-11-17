<template>
  <view class="xt-page xt-s24 v7-create">
    <view class="cr-body">
      <!-- 顶栏 -->
      <view class="cr-head">
        <view class="cr-back" @click="close"><xt-icon name="i-left" :size="15" /></view>
        <view class="cr-title">
          <text class="t">记录今天</text>
          <text class="s">写给自己，也可以让她看见</text>
        </view>
        <view class="cr-clock" @click="goSchedule"><xt-icon name="i-clock" :size="16" /></view>
      </view>

      <!-- 记录类型 -->
      <view class="chips cr-chips">
        <view
          v-for="t in types"
          :key="t"
          class="chip"
          :class="{ on: type === t }"
          @click="type = t"
        >{{ t }}</view>
      </view>

      <!-- 输入卡 -->
      <view class="mood-card cr-card">
        <text class="q">今天想留下点什么？</text>
        <text class="hint">不用完整，写一句也行。</text>
        <view class="cr-input-wrap">
          <textarea
            v-model="content"
            class="cr-input"
            :maxlength="300"
            :placeholder="placeholder"
            placeholder-class="cr-ph"
            auto-height
          />
          <text class="cr-count">{{ content.length }}/300</text>
        </view>
        <view class="cr-tools">
          <view v-for="(img, i) in images" :key="'img-' + i" class="cr-thumb">
            <image :src="img" mode="aspectFill" />
            <view class="cr-del" @click.stop="removeImage(i)">×</view>
          </view>
          <view v-if="images.length < 3" class="cr-add" @click="chooseImage">
            <xt-icon name="i-plus" :size="15" />
          </view>
          <view class="cr-ai-pick" @click="applyAiLine">
            <xt-icon name="i-spark" :size="12" />
            <text>记一句</text>
          </view>
        </view>
      </view>

      <!-- 她发来的 -->
      <view class="cr-sect">
        <text class="h">她发来的</text>
        <text class="s">一张今天的光</text>
      </view>
      <view class="cr-polaroid" @click="previewHero">
        <image v-if="heroPhoto" class="cr-pola-img" :src="heroPhoto" mode="aspectFill" />
        <view v-else class="cr-pola-fb">{{ characterName.slice(0, 1) }}</view>
        <view class="cr-pola-cap">
          <text class="n">{{ characterName }}</text>
          <text class="d">今天 · 刚刚</text>
        </view>
      </view>

      <!-- 风景横滑 -->
      <view class="cr-sect">
        <text class="h">选一张风景寄给她</text>
        <view class="cr-sect-r">
          <text class="s">{{ selectedScenery ? selectedScenery.city : '横滑挑选' }}</text>
          <text class="all" @click="goSceneryGallery">全部 ›</text>
        </view>
      </view>
      <scroll-view class="cr-scenery" scroll-x :show-scrollbar="false">
        <view class="cr-scenery-inner">
          <view
            v-for="s in sceneries"
            :key="s.city"
            class="cr-scene"
            :class="{ on: selectedScenery && selectedScenery.city === s.city }"
            @click="pickScenery(s)"
          >
            <image :src="s.img" mode="aspectFill" />
            <text>{{ s.city }}</text>
          </view>
        </view>
      </scroll-view>

      <!-- AI 接一句 -->
      <view class="ai-rec cr-ai">
        <view class="sp"><xt-icon name="i-spark" :size="13" /></view>
        <view class="tx">
          <text class="k">{{ characterName }}想接一句</text>
          <text class="p">{{ aiLine }}</text>
        </view>
        <view class="arrow" @click="applyAiLine"><xt-icon name="i-arrow" :size="13" /></view>
      </view>

      <!-- 可见范围 -->
      <view class="cr-sect">
        <text class="h">谁可以看</text>
        <text class="s">随时可改</text>
      </view>
      <view class="cr-vis">
        <view
          v-for="v in visibilities"
          :key="v"
          class="cr-vchip"
          :class="{ on: visibility === v }"
          @click="visibility = v"
        >{{ v }}</view>
      </view>

      <!-- 心情 -->
      <view class="cr-sect">
        <text class="h">此刻的心情</text>
        <text class="s">选一个就够</text>
      </view>
      <view class="cr-moods">
        <view
          v-for="m in moods"
          :key="m.key"
          class="cr-mood"
          :class="{ on: mood === m.key }"
          @click="mood = m.key"
        >
          <view class="dot" :style="{ background: m.color }"></view>
          <text>{{ m.label }}</text>
        </view>
      </view>

      <!-- 今天做到的小事 -->
      <view class="cr-sect">
        <text class="h">今天做到的小事</text>
        <text class="s">{{ doneCount }}/{{ tasks.length }}</text>
      </view>
      <view class="cr-tasks">
        <view v-for="t in tasks" :key="t.key" class="cr-task" @click="toggleTask(t)">
          <view class="ck" :class="{ on: t.done }">
            <xt-icon v-if="t.done" name="i-check" :size="10" />
          </view>
          <text :class="{ done: t.done }">{{ t.label }}</text>
        </view>
      </view>

      <!-- 今天的一句 -->
      <view class="cr-note">
        <text class="k">今天的一句</text>
        <text class="p">{{ note }}</text>
      </view>
    </view>

    <!-- 保存回执 -->
    <view v-if="saved" class="cr-saved">
      <xt-icon name="i-check" :size="18" />
      <text>已记下</text>
      <text class="s">在「我的 · 我的记录」可以回看</text>
    </view>

    <!-- 固定底部发布 -->
    <view class="cr-submit">
      <view class="auth-btn" @click="submit">记下来，她会记得</view>
    </view>

    <v7-tabbar active="create" />
  </view>
</template>

<script>
/**
 * 「+」记录页（设计稿 s24）
 * 先选记什么，再写一句；图片、风景、心情、小事都可以顺手留下
 */
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import V7Tabbar from '@/components/v7-tabbar/v7-tabbar.vue'
import { getActivePartner, getPartnerPhoto } from '@/common/ai-partner'

const SCENERIES = [
  { city: '京都', img: '/static/images/postcard/kyoto.webp' },
  { city: '上海', img: '/static/images/postcard/shanghai.webp' },
  { city: '大理', img: '/static/images/postcard/dali.webp' },
  { city: '杭州', img: '/static/images/postcard/hangzhou.webp' },
  { city: '重庆', img: '/static/images/postcard/chongqing.webp' },
  { city: '成都', img: '/static/images/postcard/chengdu.webp' },
  { city: '西安', img: '/static/images/postcard/xian.webp' },
  { city: '苏州', img: '/static/images/postcard/suzhou.webp' }
]

export default {
  components: { XtIcon, V7Tabbar },
  data() {
    return {
      types: ['打卡', '小想法', '心情', '日程'],
      type: '打卡',
      content: '',
      images: [],
      sceneries: SCENERIES,
      selectedScenery: null,
      visibilities: ['仅自己可见', '伙伴可见', '发到朋友圈'],
      visibility: '伙伴可见',
      moods: [
        { key: 'calm', label: '平静', color: '#7E9B8C' },
        { key: 'happy', label: '开心', color: '#C9A35B' },
        { key: 'tired', label: '有点累', color: '#8A8F9B' },
        { key: 'miss', label: '想念', color: '#B98C8C' },
        { key: 'low', label: '低落', color: '#6E7E8A' }
      ],
      mood: 'calm',
      tasks: [
        { key: 'cup', label: '把杯子洗掉', done: false },
        { key: 'read', label: '读两页书', done: false },
        { key: 'walk', label: '出门走 10 分钟', done: false }
      ],
      note: '慢一点也没关系，方向对了就好。',
      submitting: false,
      saved: false
    }
  },
  computed: {
    characterName() {
      return getActivePartner().name || '她'
    },
    heroPhoto() {
      return getPartnerPhoto(getActivePartner()) || ''
    },
    doneCount() {
      return this.tasks.filter(t => t.done).length
    },
    placeholder() {
      const map = {
        打卡: '今天做到了什么……',
        小想法: '刚刚想到……',
        心情: '此刻的心情是……',
        日程: '接下来要做……'
      }
      return map[this.type] || '今天……'
    },
    aiLine() {
      return '今天风大，回来的路上记得把围巾往上拉一点。'
    }
  },
  onShow() {
    try {
      uni.hideTabBar({ animation: false, fail: () => {} })
    } catch (e) {}
  },
  methods: {
    close() {
      uni.switchTab({ url: '/pages/index/index' })
    },
    goSchedule() {
      uni.navigateTo({ url: '/pages/schedule/schedule' })
    },
    goSceneryGallery() {
      uni.navigateTo({ url: '/pages/postcard-gallery/postcard-gallery' })
    },
    chooseImage() {
      uni.chooseImage({
        count: 3 - this.images.length,
        success: res => {
          this.images = this.images.concat(res.tempFilePaths).slice(0, 3)
        }
      })
    },
    removeImage(i) {
      this.images.splice(i, 1)
    },
    pickScenery(s) {
      this.selectedScenery = this.selectedScenery && this.selectedScenery.city === s.city ? null : s
    },
    applyAiLine() {
      const line = this.aiLine
      if (this.content.includes(line)) return
      this.content = this.content ? this.content + '\n' + line : line
    },
    toggleTask(t) {
      t.done = !t.done
    },
    previewHero() {
      if (this.heroPhoto) uni.previewImage({ urls: [this.heroPhoto] })
    },
    submit() {
      if (this.submitting) return
      if (!this.content.trim() && !this.images.length && !this.selectedScenery) {
        uni.showToast({ title: '先写一句或选张图吧', icon: 'none', duration: 1500 })
        return
      }
      this.submitting = true
      try {
        const record = {
          id: Date.now(),
          type: this.type,
          content: this.content.trim(),
          images: this.images.slice(),
          scenery: this.selectedScenery ? this.selectedScenery.city : '',
          visibility: this.visibility,
          mood: this.mood,
          tasks: this.tasks.filter(t => t.done).map(t => t.key),
          created_at: new Date().toISOString()
        }
        const list = uni.getStorageSync('create_records') || []
        list.unshift(record)
        uni.setStorageSync('create_records', list.slice(0, 100))
      } catch (e) {
        console.error('保存记录失败', e)
      }
      uni.showToast({ title: '已记下', icon: 'none', duration: 1500 })
      this.saved = true
      setTimeout(() => {
        this.reset()
        this.close()
      }, 1500)
    },
    reset() {
      this.content = ''
      this.images = []
      this.selectedScenery = null
      this.mood = 'calm'
      this.type = '打卡'
      this.tasks.forEach(t => { t.done = false })
      this.submitting = false
      this.saved = false
    }
  }
}
</script>

<style lang="scss" scoped>
/* ===== V7 纸感手帐 · 记录今天 ===== */
.v7-create {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background:
    radial-gradient(420px 300px at 88% -4%, rgba(196, 205, 189, 0.24), transparent 62%),
    radial-gradient(380px 320px at 4% 102%, rgba(228, 211, 187, 0.22), transparent 60%),
    #f8f4ec;
  color: #18231d;
}

.cr-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding: calc(env(safe-area-inset-top) + 12px) 17px calc(150px + env(safe-area-inset-bottom));
}

/* 顶栏 */
.cr-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cr-back,
.cr-clock {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 10px 20px -18px rgba(24, 35, 29, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #24493a;
  flex-shrink: 0;
}
.cr-clock {
  border-radius: 50%;
  color: #a2aaa3;
  box-shadow: none;
  background: transparent;
  border-color: transparent;
}
.cr-title {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cr-title .t {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
}
.cr-title .s {
  margin-top: 2px;
  font-size: 8.5px;
  color: #a2aaa3;
  letter-spacing: 0.3px;
}

/* 类型 chips */
.cr-chips {
  margin: 14px 0 10px;
}

/* 输入卡 */
.cr-card {
  border-radius: 19px;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 18px 34px -30px rgba(24, 35, 29, 0.55);
  padding: 14px;
}
.cr-input-wrap {
  position: relative;
  margin-top: 9px;
  padding: 11px 12px 20px;
  border-radius: 13px;
  background: #fffcf6;
}
.cr-input {
  width: 100%;
  min-height: 76px;
  font-size: 11px;
  line-height: 1.75;
  color: #3f4d45;
}
.cr-ph {
  color: #b3bab4;
}
.cr-count {
  position: absolute;
  right: 12px;
  bottom: 6px;
  font-size: 7.5px;
  color: #b3bab4;
}
.cr-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 9px;
}
.cr-thumb,
.cr-add {
  position: relative;
  width: 42px;
  height: 42px;
  border-radius: 11px;
  overflow: hidden;
  flex-shrink: 0;
}
.cr-thumb image {
  width: 100%;
  height: 100%;
}
.cr-del {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: rgba(24, 35, 29, 0.62);
  color: #fff;
  font-size: 11px;
  line-height: 14px;
  text-align: center;
}
.cr-add {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8b968f;
  background: #f4f0e6;
  border: 1px dashed rgba(30, 42, 36, 0.18);
}
.cr-ai-pick {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 8.5px;
  color: #44705a;
  padding: 5px 9px;
  border-radius: 999px;
  background: #edf3ef;
}

/* 分节 */
.cr-sect {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 16px 2px 8px;
}
.cr-sect .h {
  font-size: 12px;
  font-weight: 800;
  color: #18231d;
}
.cr-sect .s {
  font-size: 8px;
  color: #a2aaa3;
}
.cr-sect-r {
  display: flex;
  align-items: baseline;
  gap: 7px;
}
.cr-sect-r .all {
  font-size: 8px;
  font-weight: 700;
  color: #44705a;
}

/* 拍立得 */
.cr-polaroid {
  width: 148px;
  padding: 7px 7px 9px;
  border-radius: 6px;
  background: #fffdf9;
  border: 1px solid rgba(30, 42, 36, 0.08);
  box-shadow: 0 16px 28px -24px rgba(24, 35, 29, 0.6);
  transform: rotate(-1.6deg);
}
.cr-pola-img,
.cr-pola-fb {
  width: 100%;
  height: auto;
  aspect-ratio: 3 / 4;
  border-radius: 2px;
  display: block;
}
.cr-pola-img :deep(div),
.cr-pola-img :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.cr-pola-img :deep(img) {
  object-fit: cover;
}
.cr-pola-fb {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  color: #fff;
  background: linear-gradient(135deg, #7d9b8b, #35594a);
}
.cr-pola-cap {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 7px 2px 0;
}
.cr-pola-cap .n {
  font-size: 9px;
  font-weight: 700;
  color: #3f4d45;
}
.cr-pola-cap .d {
  font-size: 7px;
  color: #a9b1aa;
}

/* 风景横滑 */
.cr-scenery {
  width: 100%;
  white-space: nowrap;
}
.cr-scenery-inner {
  display: inline-flex;
  gap: 8px;
  padding: 2px 1px 4px;
}
.cr-scene {
  position: relative;
  width: 128px;
  height: auto;
  aspect-ratio: 16 / 9;
  border-radius: 13px;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid transparent;
  transition: border-color 0.2s ease;
}
.cr-scene image,
.cr-scene uni-image,
.cr-scene :deep(uni-image > div),
.cr-scene :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.cr-scene :deep(uni-image img) {
  object-fit: cover;
}
.cr-scene::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 56%;
  background: linear-gradient(to top, rgba(12, 20, 16, 0.52), transparent);
}
.cr-scene text {
  position: absolute;
  z-index: 1;
  left: 0;
  right: 0;
  bottom: 7px;
  text-align: center;
  font-size: 9px;
  color: #fff;
  letter-spacing: 0.5px;
}
.cr-scene.on {
  border-color: #24493a;
}

/* AI 接一句 */
.cr-ai {
  margin-top: 14px;
  padding: 11px 12px;
  border-radius: 16px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  box-shadow: 0 16px 30px -28px rgba(24, 35, 29, 0.55);
}
.cr-ai .k {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.6px;
  color: #44705a;
}
.cr-ai .p {
  display: block;
  margin-top: 3px;
  font-size: 10px;
  line-height: 1.6;
  color: #4b5a51;
}

/* 可见范围 */
.cr-vis {
  display: flex;
  gap: 7px;
}
.cr-vchip {
  flex: 1;
  text-align: center;
  padding: 9px 4px;
  border-radius: 12px;
  font-size: 9px;
  color: #7c877f;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
}
.cr-vchip.on {
  color: #fff;
  font-weight: 700;
  background: #24493a;
  border-color: #24493a;
}

/* 心情 */
.cr-moods {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.cr-mood {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 11px;
  border-radius: 999px;
  font-size: 9px;
  color: #7c877f;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
}
.cr-mood .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.cr-mood.on {
  color: #24493a;
  font-weight: 700;
  border-color: #24493a;
  background: #edf3ef;
}

/* 小事 */
.cr-tasks {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.cr-task {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 12px;
  border-radius: 13px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
}
.cr-task .ck {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  border: 1px solid rgba(30, 42, 36, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.cr-task .ck.on {
  background: #44705a;
  border-color: #44705a;
}
.cr-task text {
  font-size: 10px;
  color: #3f4d45;
}
.cr-task text.done {
  color: #a2aaa3;
  text-decoration: line-through;
}

/* 今天的一句 */
.cr-note {
  margin-top: 16px;
  padding: 13px 14px;
  border-radius: 16px;
  background: #f6efdf;
  border: 1px dashed rgba(178, 121, 63, 0.28);
}
.cr-note .k {
  display: block;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 1.2px;
  color: #b2793f;
}
.cr-note .p {
  display: block;
  margin-top: 5px;
  font-size: 11px;
  line-height: 1.8;
  color: #5b4a35;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
}

/* 保存回执 */
.cr-saved {
  position: fixed;
  left: 50%;
  top: 46%;
  z-index: 60;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 26px;
  border-radius: 18px;
  background: rgba(36, 73, 58, 0.94);
  color: #fff;
  font-size: 11px;
  letter-spacing: 1px;
  box-shadow: 0 22px 40px -20px rgba(24, 35, 29, 0.7);
  animation: crSaved 0.24s ease both;
}
.cr-saved .s {
  font-size: 8px;
  letter-spacing: 0.3px;
  opacity: 0.72;
}
@keyframes crSaved {
  from { opacity: 0; transform: translate(-50%, -46%) scale(0.94); }
  to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

/* 固定底部 */
.cr-submit {
  position: fixed;
  left: 17px;
  right: 17px;
  bottom: calc(74px + env(safe-area-inset-bottom));
  z-index: 20;
  padding: 10px 0;
  background: linear-gradient(to top, #f8f4ec 62%, rgba(248, 244, 236, 0));
}
.cr-submit .auth-btn {
  margin-top: 0;
  font-size: 12px;
  padding: 14px 0;
  letter-spacing: 0.6px;
  background: linear-gradient(135deg, #44705a, #24493a);
  box-shadow: 0 18px 30px -18px rgba(36, 73, 58, 0.85);
}
</style>
