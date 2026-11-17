<template>
  <view class="xt-page xt-s34">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">碎片图鉴</view>
          <view class="page-sub">已收集 {{ collectedCount }} / {{ totalTypes }} · 她的故事碎片</view>
        </view>
        <view class="icon-btn" @click="toggleSearch"><xt-icon name="i-search" /></view>
      </view>

      <!-- 搜索 -->
      <view v-if="showSearch" style="margin-bottom:10px">
        <input
          v-model="keyword"
          :focus="showSearch"
          placeholder="搜索碎片名称"
          placeholder-style="color:#BFC7BF"
          style="height:36px;padding:0 12px;border-radius:12px;background:#FFFDFA;border:1px solid rgba(30,42,36,.10);font-size:9px;color:#22302A"
        />
      </view>

      <view class="chips" style="margin:0 0 10px">
        <text
          v-for="c in filters"
          :key="c.key"
          class="chip"
          :class="{ on: filter === c.key }"
          @click="filter = c.key"
        >{{ c.label }}</text>
      </view>

      <view class="vault-grid">
        <view
          v-for="item in displayFragments"
          :key="item.id"
          class="vitem"
          :class="{ lock: !item.got }"
          @click="showFragmentDetail(item)"
        >
          <view class="box2" :class="item.got ? item.tint : ''">
            <xt-icon :name="item.ic" />
          </view>
          <view class="n">{{ item.name }}</view>
          <view class="c">{{ getRarityText(item.rarity) }} · {{ item.got ? '已收集' : '未收集' }}</view>
        </view>
      </view>

      <view class="mem-item" style="margin-top:11px">
        <view class="mi tint-purple"><xt-icon name="i-spark" /></view>
        <view class="tx">
          <view class="t">已收集 {{ fragments }} 枚碎片 · 5 枚换 1 次盲盒</view>
          <view class="m">完成「雨天共伞」剧情，可解锁稀有碎片。</view>
        </view>
        <text class="v" style="font-size:8px;color:var(--v7-green)" @click="exchangeBox">兑换</text>
      </view>
    </view>
  </view>
</template>

<script>
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

// 设计稿图标 / 底色与碎片类型的对应关系
const FRAGMENT_META = {
  focus: ['i-focus', 'tint-green'],
  time: ['i-clock', 'tint-sand'],
  star: ['i-spark', 'tint-purple'],
  book: ['i-book', 'tint-blue'],
  pen: ['i-edit', 'tint-peach'],
  coffee: ['i-heart', 'tint-sand'],
  moon: ['i-moon', 'tint-blue'],
  sun: ['i-spark', 'tint-peach'],
  heart: ['i-heart', 'tint-peach'],
  flower: ['i-heart', 'tint-teal'],
  key: ['i-check', 'tint-green'],
  rainbow: ['i-water', 'tint-teal']
}

export default {
  components: { XtIcon },
  data() {
    return {
      fragments: 0,
      collected: [],
      history: [],
      filter: 'all',
      showSearch: false,
      keyword: '',
      filters: [
        { key: 'all', label: '全部' },
        { key: 'common', label: '普通' },
        { key: 'rare', label: '稀有' },
        { key: 'legendary', label: '传说' }
      ],
      fragmentTypes: [
        { id: 'focus', icon: '🔮', name: '专注水晶', description: '凝聚专注力的神奇水晶，散发着柔和的光芒', rarity: 'common', source: '完成专注时长' },
        { id: 'time', icon: '⏰', name: '时光沙漏', description: '记录每一刻奋斗的时光之沙', rarity: 'common', source: '连续专注5天' },
        { id: 'star', icon: '⭐', name: '星光碎片', description: '来自星空的神秘碎片，蕴含无限可能', rarity: 'rare', source: '连续专注7天' },
        { id: 'book', icon: '📚', name: '智慧书页', description: '古老书籍中掉落的珍贵书页', rarity: 'common', source: '完成学习类习惯' },
        { id: 'pen', icon: '✏️', name: '灵感之笔', description: '书写梦想的魔法之笔', rarity: 'rare', source: '连续完成写作习惯' },
        { id: 'coffee', icon: '☕', name: '能量咖啡', description: '永不疲倦的能量源泉', rarity: 'common', source: '清晨专注' },
        { id: 'moon', icon: '🌙', name: '月光宝石', description: '在月光下闪耀的神秘宝石', rarity: 'legendary', source: '夜间专注超过2小时' },
        { id: 'sun', icon: '☀️', name: '太阳徽章', description: '象征光明与希望的金色徽章', rarity: 'legendary', source: '连续打卡30天' },
        { id: 'heart', icon: '❤️', name: '恒心之石', description: '代表坚持与毅力的永恒之心', rarity: 'rare', source: '完成100次打卡' },
        { id: 'flower', icon: '🌸', name: '成长之花', description: '在努力中绽放的美丽花朵', rarity: 'common', source: '养成新习惯' },
        { id: 'key', icon: '🔑', name: '成就之钥', description: '开启成功之门的神秘钥匙', rarity: 'legendary', source: '完成所有成就' },
        { id: 'rainbow', icon: '🌈', name: '彩虹碎片', description: '雨后彩虹凝聚而成的梦幻碎片', rarity: 'rare', source: '完成一周全部打卡' }
      ]
    }
  },
  computed: {
    totalTypes() {
      return this.fragmentTypes.length
    },
    collectedCount() {
      return this.collected.length
    },
    displayFragments() {
      const k = this.keyword.trim()
      let list = this.filter === 'all'
        ? this.fragmentTypes
        : this.fragmentTypes.filter(f => f.rarity === this.filter)
      if (k) list = list.filter(f => (f.name || '').includes(k))
      return list.map(f => {
        const meta = FRAGMENT_META[f.id] || ['i-spark', 'tint-green']
        return { ...f, ic: meta[0], tint: meta[1], got: this.isCollected(f.id) }
      })
    }
  },
  onShow() {
    this.loadData()
    // 先本地渲染，再异步拉云端（碎片 / 收集记录换设备不丢）
    playSync.pullKey('fragment').then(ok => {
      if (ok) this.loadData()
    })
  },
  methods: {
    toggleSearch() {
      this.showSearch = !this.showSearch
      if (!this.showSearch) this.keyword = ''
    },
    loadData() {
      try {
        this.fragments = uni.getStorageSync('focus_fragments') || 0
        this.collected = uni.getStorageSync('collected_fragments') || []
        this.history = uni.getStorageSync('fragment_history') || []
      } catch (e) {
        console.error('加载碎片数据失败', e)
        this.fragments = 0
        this.collected = []
        this.history = []
      }
    },
    isCollected(id) {
      return this.collected.includes(id)
    },
    isNew(id) {
      if (!this.isCollected(id)) return false
      const record = this.history.find(h => h.type === id)
      if (!record) return false
      const now = Date.now()
      return now - record.date < 24 * 60 * 60 * 1000
    },
    getFragmentIcon(type) {
      const item = this.fragmentTypes.find(t => t.id === type)
      return item ? item.icon : '❓'
    },
    getFragmentName(type) {
      const item = this.fragmentTypes.find(t => t.id === type)
      return item ? item.name : '未知碎片'
    },
    getRarityText(rarity) {
      const texts = {
        common: '普通',
        rare: '稀有',
        legendary: '传说'
      }
      return texts[rarity] || '普通'
    },
    showFragmentDetail(item) {
      if (!item) return
      uni.showModal({
        title: `${item.icon} ${item.name}`,
        content: `${item.description}\n稀有度：${this.getRarityText(item.rarity)}\n获取方式：${item.source}`,
        showCancel: false,
        confirmText: '知道了'
      })
    },
    exchangeBox() {
      if (this.fragments < 5) {
        uni.showToast({ title: '碎片不足，需要5个碎片', icon: 'none' })
        return
      }

      uni.showModal({
        title: '兑换盲盒',
        content: '确定消耗5个碎片兑换1次盲盒机会吗？',
        success: (res) => {
          if (res.confirm) {
            this.fragments -= 5
            uni.setStorageSync('focus_fragments', this.fragments)

            const boxCount = uni.getStorageSync('box_daily_count') || 0
            uni.setStorageSync('box_daily_count', boxCount)

            const extraBoxCount = uni.getStorageSync('extra_box_count') || 0
            uni.setStorageSync('extra_box_count', extraBoxCount + 1)

            playSync.schedulePush('fragment')

            uni.showToast({ title: '兑换成功！', icon: 'success' })
            uni.navigateTo({ url: '/pages/box/box' })
          }
        }
      })
    },
    formatDate(timestamp) {
      const date = new Date(timestamp)
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
    },
    goBack() {
      uni.navigateBack()
    }
  }
}
</script>
