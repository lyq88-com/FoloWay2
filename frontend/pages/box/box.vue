<template>
  <view class="xt-page xt-s15">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">每日盲盒</view>
          <view class="page-sub">她每天往里面放一点小东西</view>
        </view>
        <view class="icon-btn" @click="goToWarehouse"><xt-icon name="i-clock" /></view>
      </view>

      <!-- 礼盒舞台 -->
      <view class="box-stage" :class="{ opened: isOpened }" @click="onStageTap">
        <view class="gift">
          <span class="knot"></span>
          <span class="lid"></span>
          <span class="base"></span>
          <span class="rib"></span>
        </view>
        <span class="box-tag">{{ boxTagText }}</span>
        <span class="box-open" @click.stop="onBoxTap">{{ boxBtnText }}</span>
      </view>

      <!-- 三枚数据药丸 -->
      <view class="pills" style="margin-top:11px">
        <view class="pill">
          <view class="v">{{ remainingCount }}<span> 次</span></view>
          <view class="k">今日机会</view>
        </view>
        <view class="pill">
          <view class="v">{{ recentRewards.length }}<span> 件</span></view>
          <view class="k">最近获得</view>
        </view>
        <view class="pill">
          <view class="v">{{ isOpened ? '已开' : '待开' }}</view>
          <view class="k">今日状态</view>
        </view>
      </view>

      <!-- 最近获得 -->
      <view class="cal-sec" style="margin-top:11px">
        <span class="t">最近获得</span>
        <span class="s">已收进仓库 · {{ recentRewards.length }} 件</span>
      </view>
      <view class="postcards">
        <view v-for="(item, i) in previewCards" :key="i" class="pcard">
          <view
            class="ph"
            :style="{ background: ['linear-gradient(145deg,#C08A56,#A87A5E)','linear-gradient(145deg,#8FB79E,#24493A)','linear-gradient(145deg,#93A9B8,#4A5C68)'][i % 3] }"
          >
            <text v-if="item.emoji">{{ item.emoji }}</text>
            <xt-icon v-else :name="item.icon" />
          </view>
          <view class="pn">{{ item.name }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { applyTheme } from '@/common/theme'
import { getDailyQuote } from '@/common/ai-dialogue-engine'
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const REWARD_POOL = [
  { type: 'theme', name: '清新绿色主题', description: '焕然一新的视觉体验', emoji: '🎨', value: 'light' },
  { type: 'theme', name: '深邃暗夜主题', description: '护眼舒适的深色模式', emoji: '🌙', value: 'dark' },
  { type: 'theme', name: '暖阳橙色主题', description: '温暖活力的配色方案', emoji: '☀️', value: 'light' },
  { type: 'bg', name: '星空背景', description: '浪漫星空下的习惯养成', emoji: '🌌', value: 'starry' },
  { type: 'bg', name: '森林背景', description: '清新自然的森林气息', emoji: '🌲', value: 'forest' },
  { type: 'bg', name: '海洋背景', description: '宁静深邃的海洋氛围', emoji: '🌊', value: 'ocean' },
  { type: 'bg', name: '樱花背景', description: '浪漫唯美的樱花飘落', emoji: '🌸', value: 'sakura' },
  { type: 'avatar', name: '星星装饰', description: '闪耀的星星头像装饰', emoji: '⭐', value: 'star' },
  { type: 'avatar', name: '花朵装饰', description: '美丽的花朵头像装饰', emoji: '🌺', value: 'flower' },
  { type: 'avatar', name: '皇冠装饰', description: '尊贵的皇冠头像装饰', emoji: '👑', value: 'crown' },
  { type: 'avatar', name: '眼镜装饰', description: '时尚的眼镜头像装饰', emoji: '🕶️', value: 'glasses' },
  { type: 'quote', name: '励志语录', description: '给你满满的正能量', emoji: '💪', value: '每天进步一点点，积累成就大未来。' },
  { type: 'quote', name: '温馨语录', description: '温暖心灵的话语', emoji: '💕', value: '生活不是等待风暴过去，而是学会在雨中跳舞。' },
  { type: 'quote', name: '哲理语录', description: '深刻的人生感悟', emoji: '📖', value: '成功的秘诀在于始终如一地坚持目标。' },
  { type: 'quote', name: '幽默语录', description: '轻松愉快的心情', emoji: '😄', value: '早起的鸟儿有虫吃，早起的虫儿被鸟吃，所以做个快乐的懒人吧！' }
]

const SEASON_REWARDS = {
  spring: [
    { type: 'theme', name: '春日樱花主题', description: '粉嫩浪漫的春日配色', emoji: '🌸', value: 'spring', seasonal: true },
    { type: 'bg', name: '春雨背景', description: '细雨绵绵的春日景象', emoji: '🌧️', value: 'spring_rain', seasonal: true },
    { type: 'skin', name: '樱花限定皮肤', description: '春季限定界面皮肤', emoji: '🌸', value: 'spring_skin', seasonal: true },
    { type: 'avatar', name: '蝴蝶装饰', description: '春日蝴蝶头像装饰', emoji: '🦋', value: 'butterfly', seasonal: true }
  ],
  summer: [
    { type: 'theme', name: '夏日海滩主题', description: '清凉蓝色的夏日配色', emoji: '🌊', value: 'summer', seasonal: true },
    { type: 'bg', name: '夏日阳光背景', description: '阳光沙滩的夏日氛围', emoji: '☀️', value: 'summer_sun', seasonal: true },
    { type: 'skin', name: '海滩限定皮肤', description: '夏季限定界面皮肤', emoji: '🏖️', value: 'summer_skin', seasonal: true },
    { type: 'avatar', name: '椰子装饰', description: '夏日椰子头像装饰', emoji: '🥥', value: 'coconut', seasonal: true }
  ],
  autumn: [
    { type: 'theme', name: '秋日枫叶主题', description: '温暖橙红的秋日配色', emoji: '🍁', value: 'autumn', seasonal: true },
    { type: 'bg', name: '秋日落叶背景', description: '落叶纷飞的秋日景象', emoji: '🍂', value: 'autumn_leaves', seasonal: true },
    { type: 'skin', name: '枫叶限定皮肤', description: '秋季限定界面皮肤', emoji: '🍁', value: 'autumn_skin', seasonal: true },
    { type: 'avatar', name: '南瓜装饰', description: '秋日南瓜头像装饰', emoji: '🎃', value: 'pumpkin', seasonal: true }
  ],
  winter: [
    { type: 'theme', name: '冬日雪花主题', description: '纯洁白色的冬日配色', emoji: '❄️', value: 'winter', seasonal: true },
    { type: 'bg', name: '冬日雪景背景', description: '银装素裹的冬日氛围', emoji: '🌨️', value: 'winter_snow', seasonal: true },
    { type: 'skin', name: '雪花限定皮肤', description: '冬季限定界面皮肤', emoji: '❄️', value: 'winter_skin', seasonal: true },
    { type: 'avatar', name: '雪人装饰', description: '冬日雪人头像装饰', emoji: '☃️', value: 'snowman', seasonal: true }
  ]
}

function getCurrentSeason() {
  const month = new Date().getMonth() + 1
  if (month >= 3 && month <= 5) return 'spring'
  if (month >= 6 && month <= 8) return 'summer'
  if (month >= 9 && month <= 11) return 'autumn'
  return 'winter'
}

const BOX_KEY = 'box_daily_count'
const LAST_OPEN_KEY = 'box_last_open_date'
const REWARD_HISTORY_KEY = 'box_reward_history'
const WAREHOUSE_KEY = 'box_warehouse'

export default {
  components: { XtIcon },
  data() {
    return {
      isOpened: false,
      isOpening: false,
      reward: null,
      remainingCount: 1,
      recentRewards: [],
      boxBackgroundConfig: '',
      appTheme: 'light',
      autoThemeMode: false,
      pageBackground: ''
    }
  },
  computed: {
    boxStatusText() {
      if (this.isOpening) return '开启中...'
      if (this.isOpened) return '今日已开'
      if (this.remainingCount === 0) return '明日再来'
      return '点击开启'
    },
    boxTagText() {
      if (this.isOpening) return '她正在放东西…'
      if (this.reward) return `${this.reward.emoji} ${this.reward.name}`
      if (this.isOpened) return '今天已拆开 · 明天再来'
      return '今天只有一份，拆开就没有了'
    },
    boxBtnText() {
      if (this.isOpening) return '开启中…'
      if (this.reward) return this.reward.type === 'quote' ? '收进仓库' : '立即使用'
      if (this.isOpened) return '今日已开'
      return '拆开今天'
    },
    previewCards() {
      const list = (this.recentRewards || []).slice(0, 3)
      if (list.length) return list.map(item => ({ emoji: item.emoji, name: item.name }))
      return [
        { icon: 'i-heart', name: '她的小纸条' },
        { icon: 'i-spark', name: '限定互动' },
        { icon: 'i-moon', name: '装扮碎片' }
      ]
    },
    dailyQuote() {
      return getDailyQuote()
    },
    todayDate() {
      const d = new Date()
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },
    isDarkTheme() {
      if (this.autoThemeMode) {
        const hour = new Date().getHours()
        return hour >= 18 || hour < 6
      }
      return this.appTheme === 'dark'
    },
    pageStyle() {
      const bg = this.pageBackground || this.getDefaultBackground()
      const styleObj = {
        '--box-page-bg': bg,
        background: bg
      }
      return styleObj
    }
  },
  onShow() {
    this.loadData()
    // 先本地渲染，再异步拉云端（换设备后盲盒/仓库不丢）
    playSync.pullKey('box').then(ok => {
      if (ok) this.loadData()
    })
  },
  methods: {
    getDefaultBackground() {
      if (this.isDarkTheme) {
        return 'linear-gradient(180deg, #1A1A2E 0%, #16213E 50%, #0F1626 100%)'
      }
      return 'linear-gradient(180deg, #FFF8E7 0%, #F8F9FA 40%, #E8F4EC 100%)'
    },
    resolveBackground(config) {
      if (!config) return ''
      if (typeof config === 'string') {
        if (config.startsWith('http') || config.startsWith('linear-gradient') || config.startsWith('radial-gradient') || config.startsWith('#') || config.startsWith('rgb')) {
          return config
        }
        if (config.includes('url(')) {
          return config
        }
      }
      if (typeof config === 'object') {
        if (config.imageUrl) {
          return `url(${config.imageUrl})`
        }
        if (config.gradient) {
          return config.gradient
        }
        if (config.color) {
          return config.color
        }
      }
      return ''
    },
    loadData() {
      const today = new Date().toDateString()

      try {
        this.boxBackgroundConfig = uni.getStorageSync('box_background_config') || ''
      } catch (e) {
        console.error('读取 box_background_config 失败', e)
        this.boxBackgroundConfig = ''
      }

      try {
        this.appTheme = uni.getStorageSync('app_theme') || 'light'
      } catch (e) {
        console.error('读取 app_theme 失败', e)
        this.appTheme = 'light'
      }

      try {
        this.autoThemeMode = uni.getStorageSync('auto_theme_mode') || false
      } catch (e) {
        console.error('读取 auto_theme_mode 失败', e)
        this.autoThemeMode = false
      }

      let lastOpen = ''
      try {
        lastOpen = uni.getStorageSync(LAST_OPEN_KEY) || ''
      } catch (e) {
        console.error('读取 box_last_open_date 失败', e)
        lastOpen = ''
      }

      let count = 0
      try {
        count = uni.getStorageSync(BOX_KEY) || 0
      } catch (e) {
        console.error('读取 box_daily_count 失败', e)
        count = 0
      }

      if (lastOpen !== today) {
        this.remainingCount = 1
        this.isOpened = false
        try {
          uni.setStorageSync(BOX_KEY, 0)
          uni.setStorageSync(LAST_OPEN_KEY, today)
        } catch (e) {
          console.error('重置盲盒计数失败', e)
        }
      } else {
        this.remainingCount = count >= 1 ? 0 : 1
        this.isOpened = count >= 1
      }

      try {
        const history = uni.getStorageSync(REWARD_HISTORY_KEY) || []
        this.recentRewards = history.slice(0, 5)
      } catch (e) {
        console.error('读取奖励历史失败', e)
        this.recentRewards = []
      }

      const resolvedBg = this.resolveBackground(this.boxBackgroundConfig)
      this.pageBackground = resolvedBg || ''
    },
    onStageTap() {
      if (this.reward) {
        this.closeReward()
        return
      }
      this.openBox()
    },
    onBoxTap() {
      if (this.reward) {
        if (this.reward.type === 'quote') {
          this.closeReward()
        } else {
          this.useReward()
        }
        return
      }
      this.openBox()
    },
    openBox() {
      if (this.isOpened || this.isOpening || this.remainingCount === 0) return

      this.isOpening = true

      setTimeout(() => {
        this.isOpening = false
        this.isOpened = true
        this.remainingCount = 0

        this.reward = this.getRandomReward()

        this.saveReward(this.reward)
        this.updateHistory(this.reward)

        try {
          uni.setStorageSync(BOX_KEY, 1)
        } catch (e) {
          console.error('保存开箱计数失败', e)
        }
        // 开箱结果（计数 / 仓库 / 历史）同步云端
        playSync.schedulePush('box')
      }, 2000)
    },
    getRandomReward() {
      try {
        const season = getCurrentSeason()
        const seasonPool = SEASON_REWARDS[season] || []
        const combinedPool = [...REWARD_POOL, ...seasonPool]
        if (!combinedPool || combinedPool.length === 0) {
          return { emoji: '🎁', name: '惊喜礼物', description: '祝你好运连连', type: 'quote', value: '加油！', id: Date.now() }
        }
        const index = Math.floor(Math.random() * combinedPool.length)
        const reward = combinedPool[index]
        if (!reward) {
          return { emoji: '🎁', name: '惊喜礼物', description: '祝你好运连连', type: 'quote', value: '加油！', id: Date.now() }
        }
        return { ...reward, id: Date.now() }
      } catch (e) {
        console.error('获取随机奖励失败', e)
        return { emoji: '🎁', name: '惊喜礼物', description: '祝你好运连连', type: 'quote', value: '加油！', id: Date.now() }
      }
    },
    saveReward(reward) {
      try {
        const warehouse = uni.getStorageSync(WAREHOUSE_KEY) || []
        const exists = warehouse.find(w => w.type === reward.type && w.value === reward.value)
        if (!exists) {
          warehouse.push({ ...reward, date: Date.now() })
          uni.setStorageSync(WAREHOUSE_KEY, warehouse)
        }
      } catch (e) {
        console.error('保存奖励失败', e)
      }
    },
    updateHistory(reward) {
      try {
        const history = uni.getStorageSync(REWARD_HISTORY_KEY) || []
        history.unshift({ ...reward, date: Date.now() })
        if (history.length > 20) history.pop()
        uni.setStorageSync(REWARD_HISTORY_KEY, history)
        this.recentRewards = history.slice(0, 5)
      } catch (e) {
        console.error('更新历史失败', e)
      }
    },
    useReward() {
      if (!this.reward) return

      try {
        if (this.reward.type === 'theme') {
          applyTheme(this.reward.value)
          uni.showToast({ title: '主题已切换', icon: 'success' })
        } else if (this.reward.type === 'bg') {
          this.applyBackground(this.reward.value)
          uni.showToast({ title: '背景已设置', icon: 'success' })
        } else if (this.reward.type === 'avatar') {
          uni.setStorageSync('avatar_decoration', this.reward.value)
          uni.showToast({ title: '头像装饰已保存', icon: 'success' })
        } else if (this.reward.type === 'skin') {
          uni.setStorageSync('current_skin', this.reward.value)
          uni.showToast({ title: '皮肤已更换', icon: 'success' })
        }

        // 好感度联动（对标循途礼物系统）：使用宝物赠予AI伙伴，提升好感度
        this.$store.commit('addAffection', 5)
        setTimeout(() => {
          uni.showToast({ title: '好感度 +5', icon: 'none', duration: 1500 })
        }, 600)

        this.closeReward()
      } catch (e) {
        console.error('使用奖励失败', e)
        uni.showToast({ title: '使用失败', icon: 'none' })
      }
    },
    applyBackground(type) {
      const bgMap = {
        starry: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        forest: 'linear-gradient(135deg, #2d5016 0%, #3d723d 50%, #56ab2f 100%)',
        ocean: 'linear-gradient(135deg, #006994 0%, #0083b0 50%, #00b4db 100%)',
        sakura: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%)',
        spring_rain: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #a5d6a7 100%)',
        summer_sun: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
        autumn_leaves: 'linear-gradient(135deg, #d7ccc8 0%, #bcaaa4 50%, #a1887f 100%)',
        winter_snow: 'linear-gradient(135deg, #eceff1 0%, #cfd8dc 50%, #b0bec5 100%)'
      }
      const bg = bgMap[type] || '#F8F9FA'

      try {
        uni.setStorageSync('custom_bg', bg)
      } catch (e) {
        console.error('保存 custom_bg 失败', e)
      }

      try {
        uni.setStorageSync('box_background_config', bg)
      } catch (e) {
        console.error('保存 box_background_config 失败', e)
      }

      try {
        this.pageBackground = bg
        if (this.$store && typeof this.$store.commit === 'function') {
          this.$store.commit('setCustomBackground', bg)
        }
      } catch (e) {
        console.error('更新 store 背景失败', e)
      }

      try {
        if (typeof document !== 'undefined' && document.documentElement) {
          const root = document.documentElement
          const page = document.querySelector('page')
          if (root) root.style.background = bg
          if (page) page.style.background = bg
        }
      } catch (e) {
        console.error('DOM 注入背景失败', e)
      }
    },
    closeReward() {
      this.reward = null
    },
    goBack() {
      uni.navigateBack()
    },
    goToWarehouse() {
      uni.navigateTo({ url: '/pages/box-warehouse/box-warehouse' })
    },
    formatDate(timestamp) {
      const date = new Date(timestamp)
      return `${date.getMonth() + 1}/${date.getDate()}`
    }
  }
}
</script>

<style lang="scss" scoped>
.xt-page.xt-s15 .body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 16px;
}
</style>