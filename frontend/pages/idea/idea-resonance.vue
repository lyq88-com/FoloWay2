<template>
  <view class="xt-page xt-s39">
    <view class="body">
      <!-- 顶部：返回 / 标题 / 我的想法 -->
      <view class="chat-head" style="padding:2px 2px 10px">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">一个想法</view>
          <view class="chat-st">它找到了同类</view>
        </view>
        <view class="icon-btn" @click="goMyIdeas"><xt-icon name="i-spark" /></view>
      </view>

      <!-- 想法主体 -->
      <view class="mood-card" style="padding:16px;background:linear-gradient(150deg,#FFFDFA,#F8F4EC)">
        <view class="hero-quote">“{{ heroIdea.content || '还没有匹配到同频的想法' }}”</view>
        <view class="hero-meta">
          <text class="tag" style="background:#EEF4F1;color:#3C6B55">{{ heroTag }}</text>
          <text>{{ heroTime }} · {{ list.length }} 次共鸣</text>
        </view>
        <image
          v-if="heroImage"
          class="hero-img"
          :src="heroImage"
          mode="widthFix"
          @click="previewHero"
        />
      </view>

      <!-- 有多少人和你想到了一起 -->
      <view class="mem-hero" style="margin-top:11px;display:flex;align-items:center;gap:10px">
        <view v-if="stackAvatars.length" style="display:flex">
          <image
            v-for="(a, i) in stackAvatars"
            :key="i"
            :src="a"
            mode="aspectFill"
            style="width:26px;height:26px;border-radius:50%;object-fit:cover;border:2px solid #fff"
            :style="i ? 'margin-left:-8px' : ''"
          />
        </view>
        <view v-else style="display:flex">
          <view v-for="(n, i) in stackFallback" :key="i" class="av-fallback" :style="i ? 'margin-left:-8px' : ''">
            <text class="av-fallback-t">{{ n }}</text>
          </view>
        </view>
        <view>
          <view class="t" style="font-size:9.5px">{{ list.length }} 个人和你想到了一起</view>
          <view class="m">{{ list.length ? '他们也想找个一起开始的人' : '再等一会儿，同类正在路上' }}</view>
        </view>
      </view>

      <!-- 回应列表 -->
      <view class="cal-sec" style="margin-top:13px">
        <text class="t">他们的回应</text>
        <text class="s">只有温柔能发出</text>
      </view>

      <view
        v-for="(c, i) in list"
        :key="c.resonance_id"
        class="mem-item"
        style="align-items:flex-start"
        @click="onItemTap(c)"
        @longpress="onItemReact(c)"
      >
        <view class="mi" :class="tintOf(i)" style="border-radius:50%">
          <xt-icon :name="iconOf(i)" />
        </view>
        <view class="tx">
          <view class="t">{{ nameOf(c) }}</view>
          <view class="m">“{{ c.idea.content }}”</view>
          <view class="d">{{ relTime(c.idea.create_time) }} · {{ statusText(c) }}</view>
        </view>
      </view>

      <!-- 空态 -->
      <view v-if="!loading && !list.length" class="mem-hero" style="margin-top:7px">
        <view class="t" style="font-size:11px">暂时还没有找到同频的想法</view>
        <view class="m">稍后再来，或再发一条小想法，让同类找到你。</view>
      </view>

      <!-- 底部输入条：写一句温柔的话（进入发布页） -->
      <view class="inputbar" style="margin-top:10px;padding-bottom:14px" @click="goPublish">
        <view class="in-field">说一句温柔的话…</view>
        <view class="in-send"><xt-icon name="i-send" :size="14" /></view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 小想法 · 共鸣（设计稿 s39 1:1 还原）
 * 数据来源：
 *   GET /idea/my-resonance  → list[] = { resonance_id, idea{content,image,is_anonymous,create_time},
 *                                        author{id,nickname,avatar}, lit, other_lit_me, matched,
 *                                        conversation_id, reacts{good,agree,highfive,pat} }
 *   GET /idea/my-ideas      → 取最新一条作为顶部「一个想法」主体（取不到则回落到共鸣里的第一条）
 *
 * 交互：
 *   - 点击回应条目：已共鸣 → 进私聊；未点亮 → 点亮；已点亮 → 提示
 *   - 长按回应条目：弹「温柔回应」动作面板（好棒/同意/击掌/摸摸头）
 *   - 底部输入条：进入发布页
 */
import ideaApi from '@/api/idea'
import http from '@/common/request'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      list: [],
      myIdeas: [],
      loading: false,
      reactTypes: ['good', 'agree', 'highfive', 'pat'],
      reactLabels: ['好棒', '同意', '击掌', '摸摸头']
    }
  },
  computed: {
    heroIdea() {
      if (this.myIdeas.length) return this.myIdeas[0]
      if (this.list.length) return this.list[0].idea
      return {}
    },
    heroTag() {
      return this.heroIdea.is_anonymous ? '匿名' : '我'
    },
    heroTime() {
      return this.relTime(this.heroIdea.create_time)
    },
    heroImage() {
      return this.heroIdea.image ? http.toStaticUrl(this.heroIdea.image) : ''
    },
    stackAvatars() {
      return this.list
        .map(c => (c.author && c.author.avatar ? http.toAvatarUrl(c.author.avatar) : ''))
        .filter(Boolean)
        .slice(0, 3)
    },
    stackFallback() {
      const n = Math.min(this.list.length, 3)
      const arr = []
      for (let i = 0; i < n; i++) arr.push(this.nameOf(this.list[i]).slice(0, 1))
      return arr
    }
  },
  onLoad() {
    this.loadAll()
  },
  onShow() {
    if (this.list.length) this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      try {
        const [res, mine] = await Promise.all([
          ideaApi.getMyResonance(),
          ideaApi.getMyIdeas()
        ])
        const data = (res && res.data) || {}
        this.list = (data.list || []).sort(
          (a, b) => this.timeValue(b.idea.create_time) - this.timeValue(a.idea.create_time)
        )
        this.myIdeas = ((mine && mine.data) || {}).list || []
      } catch (e) {
        /* request 层已 toast，这里保持页面可用 */
      } finally {
        this.loading = false
      }
    },

    /* ---------- 展示辅助 ---------- */
    timeValue(str) {
      if (!str) return 0
      return new Date(String(str).replace(/-/g, '/')).getTime() || 0
    },
    relTime(str) {
      const t = this.timeValue(str)
      if (!t) return ''
      const diff = Date.now() - t
      if (diff < 60 * 1000) return '刚刚'
      if (diff < 60 * 60 * 1000) return Math.floor(diff / 60000) + ' 分钟前'
      if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / 3600000) + ' 小时前'
      if (diff < 7 * 24 * 60 * 60 * 1000) return Math.floor(diff / 86400000) + ' 天前'
      return String(str).slice(0, 10)
    },
    nameOf(c) {
      const n = (c.author && c.author.nickname) || '匿名的想法'
      if (c.author && c.author.id === 0) return '匿名 · 和你相似'
      return n
    },
    iconOf(i) {
      return ['i-heart', 'i-water', 'i-spark'][i % 3]
    },
    tintOf(i) {
      return ['tint-peach', 'tint-blue', 'tint-green'][i % 3]
    },
    statusText(c) {
      if (c.matched) return '已共鸣 · 点这里去聊'
      if (c.lit) return '已被你点亮'
      if (c.other_lit_me) return 'TA 也点亮了你'
      return '还没点亮'
    },
    previewHero() {
      if (this.heroImage) uni.previewImage({ urls: [this.heroImage] })
    },

    /* ---------- 点击：点亮 / 进私聊 ---------- */
    onItemTap(c) {
      if (c.matched) return this.goChat(c)
      if (c.lit) {
        uni.showToast({ title: '已经点亮过啦', icon: 'none' })
        return
      }
      this.onLight(c)
    },
    async onLight(c) {
      try {
        const res = await ideaApi.light(c.resonance_id)
        const data = (res && res.data) || {}
        c.lit = true
        if (data.matched) {
          c.matched = true
          c.conversation_id = data.conversation_id || c.conversation_id
          uni.showToast({ title: '你们找到了共鸣，可以聊聊了', icon: 'none' })
        } else {
          uni.showToast({ title: '已点亮，等对方看到你的心意', icon: 'none' })
        }
      } catch (e) { /* request 层已提示 */ }
    },

    /* ---------- 长按：温柔回应 ---------- */
    onItemReact(c) {
      uni.showActionSheet({
        itemList: this.reactLabels,
        success: (r) => this.onReact(c, this.reactTypes[r.tapIndex])
      })
    },
    async onReact(c, type) {
      if (!type) return
      if (c.reacts && c.reacts[type]) {
        uni.showToast({ title: '已经回应过啦', icon: 'none' })
        return
      }
      try {
        const res = await ideaApi.react(c.idea.id, type)
        if (res && res.code === 200) {
          if (!c.reacts) c.reacts = {}
          c.reacts[type] = true
          const idx = this.reactTypes.indexOf(type)
          uni.showToast({ title: `已回应「${this.reactLabels[idx]}」`, icon: 'none' })
        }
      } catch (e) { /* request 层已提示 */ }
    },

    /* ---------- 导航 ---------- */
    goChat(c) {
      const id = c && c.conversation_id
      if (!id) {
        uni.showToast({ title: '会话创建中，请稍后在私聊列表查看', icon: 'none' })
        return
      }
      uni.navigateTo({ url: `/pages/idea/idea-chat?id=${id}` })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goPublish() {
      uni.navigateTo({ url: '/pages/idea/idea-publish' })
    },
    goMyIdeas() {
      uni.navigateTo({ url: '/pages/idea/idea-my' })
    }
  }
}
</script>

<style scoped>
/* 页面级微调：不改变设计稿比例 */
.hero-quote {
  display: block;
  font-size: 12px;
  line-height: 1.8;
  font-weight: 800;
  color: #22302A;
}
.hero-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 7px;
  color: #8E9A91;
}
.hero-img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 12px;
  margin-top: 9px;
  overflow: hidden;
}
.hero-img :deep(div) {
  background-size: contain;
  background-position: center;
}
.hero-img :deep(img) {
  width: 100%;
  height: auto;
  object-fit: contain;
}
.av-fallback {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #EDF3F0;
  border: 2px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.av-fallback-t {
  font-size: 9px;
  font-weight: 800;
  color: var(--v7-green);
}
</style>
