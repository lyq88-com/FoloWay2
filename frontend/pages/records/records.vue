<template>
  <view class="xt-page rc-page">
    <view class="body rc-body">
      <!-- 顶栏 -->
      <view class="rc-nav">
        <view class="rc-nav-ic" @click="goBack"><xt-icon name="i-left" :size="15" /></view>
        <view class="rc-nav-tx">
          <text class="t">我的记录</text>
          <text class="s">写下的每一句，都在这里</text>
        </view>
        <view class="rc-nav-ic" @click="goCreate"><xt-icon name="i-plus" :size="15" /></view>
      </view>

      <!-- 分类筛选 -->
      <view class="rc-chips">
        <view
          v-for="t in types"
          :key="t"
          class="rc-chip"
          :class="{ on: filter === t }"
          @click="filter = t"
        >{{ t }}</view>
      </view>

      <!-- 空状态 -->
      <view v-if="!groups.length" class="rc-empty">
        <view class="rc-empty-ic"><xt-icon name="i-edit" :size="20" /></view>
        <text class="rc-empty-t">{{ records.length ? '这个分类下还没有记录' : '还没有写下什么' }}</text>
        <text class="rc-empty-s">今天想留下点什么？写一句也行。</text>
        <view class="auth-btn rc-empty-btn" @click="goCreate">去记录今天</view>
      </view>

      <!-- 按日期分组 -->
      <view v-for="group in groups" :key="group.key" class="rc-group">
        <view class="rc-date">
          <text>{{ group.label }}</text>
          <text class="n">{{ group.items.length }} 条</text>
        </view>
        <view v-for="r in group.items" :key="r.id" class="rc-card">
          <view class="rc-card-top">
            <text class="rc-type">{{ r.type || '打卡' }}</text>
            <text class="rc-time">{{ timeOf(r) }}</text>
            <text class="rc-vis">{{ r.visibility || '伙伴可见' }}</text>
          </view>

          <text v-if="r.content" class="rc-content">{{ r.content }}</text>

          <view v-if="r.images && r.images.length" class="rc-imgs">
            <image
              v-for="(img, i) in r.images"
              :key="'img-' + i"
              :src="img"
              mode="aspectFill"
              @click="preview(r.images, i)"
            />
          </view>

          <view v-if="sceneryOf(r)" class="rc-scenery" @click="goGallery">
            <image :src="sceneryOf(r).img" mode="aspectFill" />
            <view class="rc-scenery-tx">
              <text class="c">寄自 {{ r.scenery }}</text>
              <text class="e">{{ sceneryOf(r).en }}</text>
            </view>
            <xt-icon name="i-right" :size="12" />
          </view>

          <view v-if="moodOf(r) || (r.tasks && r.tasks.length)" class="rc-foot">
            <view v-if="moodOf(r)" class="rc-mood">
              <view class="dot" :style="{ background: moodOf(r).color }"></view>
              <text>{{ moodOf(r).label }}</text>
            </view>
            <text v-if="r.tasks && r.tasks.length" class="rc-tasks">完成 {{ r.tasks.length }} 件小事</text>
          </view>
        </view>
      </view>

      <view v-if="groups.length" class="rc-end">
        <view class="line"></view>
        <text>一共 {{ records.length }} 条 · 存在本机，换设备不会同步</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 我的记录 —— 展示「+ 记录今天」页写下的内容
 * 数据来源：create_records（本地存储，最多 100 条，create.vue 写入）
 */
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { findCity } from '@/common/postcard-cities'

const MOODS = {
  calm: { label: '平静', color: '#7E9B8C' },
  happy: { label: '开心', color: '#C9A35B' },
  tired: { label: '有点累', color: '#8A8F9B' },
  miss: { label: '想念', color: '#B98C8C' },
  low: { label: '低落', color: '#6E7E8A' }
}

function dayKey(d) {
  const dt = d instanceof Date ? d : new Date(d)
  if (isNaN(dt.getTime())) return 'unknown'
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  return `${dt.getFullYear()}-${mm}-${dd}`
}

function dayLabel(key) {
  const now = new Date()
  if (key === dayKey(now)) return '今天'
  const yesterday = new Date(now.getTime() - 86400000)
  if (key === dayKey(yesterday)) return '昨天'
  return key.replace(/-/g, '.')
}

export default {
  components: { XtIcon },
  data() {
    return {
      types: ['全部', '打卡', '小想法', '心情', '日程'],
      filter: '全部',
      records: []
    }
  },
  computed: {
    filtered() {
      const list = this.filter === '全部'
        ? this.records
        : this.records.filter(r => (r.type || '打卡') === this.filter)
      return list
    },
    groups() {
      const map = new Map()
      this.filtered.forEach(r => {
        const key = dayKey(r.created_at)
        if (!map.has(key)) map.set(key, [])
        map.get(key).push(r)
      })
      return Array.from(map.entries()).map(([key, items]) => ({
        key,
        label: dayLabel(key),
        items
      }))
    }
  },
  onShow() {
    this.loadRecords()
  },
  methods: {
    loadRecords() {
      let list = []
      try {
        list = uni.getStorageSync('create_records') || []
      } catch (e) {
        list = []
      }
      if (!Array.isArray(list)) list = []
      this.records = list
        .slice()
        .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    },
    timeOf(r) {
      const d = new Date(r.created_at)
      if (isNaN(d.getTime())) return ''
      return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    },
    moodOf(r) {
      return MOODS[r.mood] || null
    },
    sceneryOf(r) {
      return findCity(r.scenery)
    },
    preview(urls, i) {
      if (!urls || !urls.length) return
      uni.previewImage({ urls, current: urls[i] || urls[0] })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/profile/profile' }) })
    },
    goCreate() {
      uni.switchTab({ url: '/pages/create/create' })
    },
    goGallery() {
      uni.navigateTo({ url: '/pages/postcard-gallery/postcard-gallery' })
    }
  }
}
</script>

<style lang="scss" scoped>
.rc-page {
  background:
    radial-gradient(420px 300px at 88% -4%, rgba(196, 205, 189, 0.24), transparent 62%),
    radial-gradient(380px 320px at 4% 102%, rgba(228, 211, 187, 0.22), transparent 60%),
    #f8f4ec;
  color: #18231d;
}
.rc-body {
  display: flex;
  flex-direction: column;
  padding-bottom: calc(36px + env(safe-area-inset-bottom));
}

/* 顶栏 */
.rc-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: calc(env(safe-area-inset-top) + 12px) 0 2px;
}
.rc-nav-ic {
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
.rc-nav-tx {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.rc-nav-tx .t {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
}
.rc-nav-tx .s {
  margin-top: 2px;
  font-size: 8.5px;
  color: #a2aaa3;
  letter-spacing: 0.3px;
}

/* 分类 */
.rc-chips {
  display: flex;
  gap: 7px;
  margin: 14px 0 4px;
  flex-wrap: wrap;
}
.rc-chip {
  padding: 7px 13px;
  border-radius: 999px;
  font-size: 9.5px;
  color: #7c877f;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
}
.rc-chip.on {
  color: #fff;
  font-weight: 700;
  background: #24493a;
  border-color: #24493a;
}

/* 空状态 */
.rc-empty {
  flex: 1;
  margin: 16px 0;
  padding: 34px 20px 30px;
  border-radius: 20px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.rc-empty-ic {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #44705a;
  background: #edf3ef;
}
.rc-empty-t {
  margin-top: 12px;
  font-size: 12.5px;
  font-weight: 800;
  color: #18231d;
}
.rc-empty-s {
  margin-top: 5px;
  font-size: 9.5px;
  color: #a2aaa3;
}
.rc-empty-btn {
  width: 180px;
  margin-top: 16px;
  padding: 12px 0;
  font-size: 11px;
  background: linear-gradient(135deg, #44705a, #24493a);
}

/* 日期分组 */
.rc-group {
  margin-top: 18px;
}
.rc-date {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 0 2px 8px;
}
.rc-date text {
  font-size: 11px;
  font-weight: 800;
  color: #3f4d45;
  letter-spacing: 0.4px;
}
.rc-date .n {
  font-size: 8px;
  font-weight: 400;
  color: #a2aaa3;
}

/* 记录卡片 */
.rc-card {
  margin-bottom: 9px;
  padding: 13px 14px;
  border-radius: 17px;
  background: #fffdfa;
  border: 1px solid rgba(30, 42, 36, 0.09);
  box-shadow: 0 16px 30px -30px rgba(24, 35, 29, 0.55);
}
.rc-card-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rc-type {
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 8px;
  font-weight: 700;
  color: #44705a;
  background: #edf3ef;
}
.rc-time {
  font-size: 8px;
  color: #a2aaa3;
}
.rc-vis {
  margin-left: auto;
  font-size: 7.5px;
  color: #b3bab4;
}
.rc-content {
  display: block;
  margin-top: 9px;
  font-size: 10.5px;
  line-height: 1.8;
  color: #3f4d45;
  white-space: pre-wrap;
  word-break: break-word;
}
.rc-imgs {
  display: flex;
  gap: 6px;
  margin-top: 9px;
}
.rc-imgs image {
  width: 72px;
  height: 72px;
  border-radius: 10px;
  background: #f3efe5;
}
.rc-imgs :deep(uni-image > div),
.rc-imgs :deep(uni-image img),
.rc-scenery :deep(uni-image > div),
.rc-scenery :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.rc-imgs :deep(uni-image img),
.rc-scenery :deep(uni-image img) {
  object-fit: cover;
}
.rc-scenery {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 10px;
  padding: 7px 9px 7px 7px;
  border-radius: 13px;
  background: #f7f4ec;
  color: #8b968f;
}
.rc-scenery image {
  width: 64px;
  height: 36px;
  border-radius: 8px;
  flex-shrink: 0;
}
.rc-scenery-tx {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.rc-scenery-tx .c {
  font-size: 9.5px;
  font-weight: 700;
  color: #3f4d45;
}
.rc-scenery-tx .e {
  margin-top: 2px;
  font-size: 7px;
  letter-spacing: 1px;
  color: #a9b1aa;
}
.rc-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.rc-mood {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 8.5px;
  color: #7c877f;
}
.rc-mood .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.rc-tasks {
  font-size: 8px;
  color: #a2aaa3;
}

.rc-end {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 22px 0 8px;
  color: #b3bab4;
  font-size: 8px;
}
.rc-end .line {
  width: 40px;
  height: 1px;
  background: rgba(30, 42, 36, 0.12);
}
</style>
