<template>
  <view class="xt-page xt-postcard">
    <view class="body pc-scroll">
      <!-- 顶部导航（视觉稿：返回 / 标题 / 分享保存） -->
      <view class="pc-nav">
        <view class="pc-nav-ic" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="pc-nav-title">往期明信片</view>
        <view class="pc-nav-ic" @click="saveToAlbum"><xt-icon name="i-share" /></view>
      </view>

      <!-- 标题区 -->
      <view class="pc-intro">
        <view class="pc-intro-title">往期明信片</view>
        <view class="pc-intro-sub">
          {{ year }} · 已收集 <text class="hl">{{ collectedCount }}</text> 张 · 来自
          <text class="hl">{{ cityCount }}</text> 座城市
        </view>
        <view class="pc-more" @click="goGallery">浏览全部风景 ›</view>
      </view>

      <view class="pc-cards">
        <!-- 本周 -->
        <view class="pc-card">
          <view class="pc-photo-wrap">
            <view class="pc-badge"><view class="pc-dot"></view><text>本周 · 第 {{ weekNo }} 周</text></view>
            <image class="pc-photo" :src="currentCard.img" mode="aspectFill" />
            <view class="pc-city">
              <text>{{ currentCard.city }}</text>
              <text class="pc-city-en">{{ currentCard.en }}</text>
            </view>
          </view>
          <view class="pc-content">
            <view class="pc-quote">“{{ currentCard.quote }}”</view>
            <view class="pc-meta">
              <text>{{ weekRange }}</text>
              <view class="pc-sep"></view>
              <text>与她相伴 {{ weekStats.streak }} 天</text>
              <view class="pc-sep"></view>
              <text>{{ weekStats.checkins }} 次打卡</text>
            </view>
            <view class="pc-actions">
              <view class="pc-act" @click="saveToAlbum">
                <xt-icon name="i-heart" :size="14" />
                <text>收藏</text>
              </view>
              <view class="pc-act" @click="saveToAlbum">
                <xt-icon name="i-archive" :size="14" />
                <text>生成海报</text>
              </view>
              <view class="pc-act pc-act-right" @click="goGrowthTrack">查看这一周 →</view>
            </view>
          </view>
        </view>

        <!-- 往期 -->
        <view v-for="card in historyCards" :key="card.key" class="pc-card pc-mini">
          <view class="pc-photo-wrap">
            <view class="pc-badge"><view class="pc-dot"></view><text>{{ card.badge }}</text></view>
            <image class="pc-photo" :src="card.img" mode="aspectFill" lazy-load />
            <view class="pc-city">
              <text>{{ card.city }}</text>
              <text class="pc-city-en">{{ card.en }}</text>
            </view>
          </view>
          <view class="pc-content">
            <view class="pc-quote">“{{ card.quote }}”</view>
            <view class="pc-meta">
              <text>{{ card.range }}</text>
              <view class="pc-sep"></view>
              <text>与她相伴 {{ card.days }} 天</text>
              <view class="pc-sep"></view>
              <text>{{ card.checkins }} 次打卡</text>
            </view>
          </view>
        </view>
      </view>

      <view class="pc-end">
        <view class="line"></view>
        <text>每一张，都是那一周你们一起走过的路</text>
      </view>

      <canvas
        canvas-id="postcardCanvas"
        class="xt-export-canvas"
        :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
      ></canvas>
    </view>

    <!-- 胶片颗粒：叠在最上层，提升整体质感 -->
    <view class="pc-grain"></view>
  </view>
</template>

<script>
import playSync from '@/common/play-sync'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

// 往期明信片城市库（低饱和电影感胶片版，WebP 素材位于 static/images/postcard/）
const CITY_CARDS = [
  { city: '上海', en: 'SHANGHAI', img: '/static/images/postcard/shanghai.webp', quote: '慢一点也没关系，方向对了就好。', days: 7, checkins: 12 },
  { city: '大理', en: 'DALI', img: '/static/images/postcard/dali.webp', quote: '风把云吹散的时候，忽然就不那么着急了。', days: 7, checkins: 9 },
  { city: '杭州', en: 'HANGZHOU', img: '/static/images/postcard/hangzhou.webp', quote: '早起的那天，湖面比想象中安静。', days: 7, checkins: 15 },
  { city: '重庆', en: 'CHONGQING', img: '/static/images/postcard/chongqing.webp', quote: '灯一层层亮起来的时候，忽然觉得日子也在往前走。', days: 7, checkins: 11 },
  { city: '成都', en: 'CHENGDU', img: '/static/images/postcard/chengdu.webp', quote: '下雨天最适合什么都不做，就坐着听雨。', days: 7, checkins: 6 },
  { city: '西安', en: "XI'AN", img: '/static/images/postcard/xian.webp', quote: '城墙上的风很大，把烦心事都吹散了。', days: 7, checkins: 14 },
  { city: '苏州', en: 'SUZHOU', img: '/static/images/postcard/suzhou.webp', quote: '园林里的水很静，像把时间也一起放慢了。', days: 7, checkins: 10 },
  { city: '青岛', en: 'QINGDAO', img: '/static/images/postcard/qingdao.webp', quote: '海雾散开的那一下，早起这件事突然就值了。', days: 7, checkins: 13 },
  { city: '厦门', en: 'XIAMEN', img: '/static/images/postcard/xiamen.webp', quote: '三角梅开得太认真，我都不好意思偷懒。', days: 7, checkins: 9 },
  { city: '哈尔滨', en: 'HARBIN', img: '/static/images/postcard/harbin.webp', quote: '零下的城市，每一扇窗户里都是暖的。', days: 7, checkins: 16 },
  { city: '长沙', en: 'CHANGSHA', img: '/static/images/postcard/changsha.webp', quote: '江边的风一吹，夜宵都变得理直气壮。', days: 7, checkins: 12 },
  { city: '泉州', en: 'QUANZHOU', img: '/static/images/postcard/quanzhou.webp', quote: '红砖被雨打得发亮，花串一路垂到肩头。', days: 7, checkins: 10 },
  { city: '洛阳', en: 'LUOYANG', img: '/static/images/postcard/luoyang.webp', quote: '灯一层层挂上去，夜色就软了下来。', days: 7, checkins: 8 },
  { city: '景德镇', en: 'JINGDEZHEN', img: '/static/images/postcard/jingdezhen.webp', quote: '看匠人拉坯的时候，忽然明白慢是什么。', days: 7, checkins: 11 },
  { city: '阿勒泰', en: 'ALTAY', img: '/static/images/postcard/altay.webp', quote: '草原上的风很干净，像被雪山洗过一遍。', days: 7, checkins: 7 },
  { city: '敦煌', en: 'DUNHUANG', img: '/static/images/postcard/dunhuang.webp', quote: '沙丘的影子拉得很长，一天就这样过去了。', days: 7, checkins: 9 },
  { city: '桂林', en: 'GUILIN', img: '/static/images/postcard/guilin.webp', quote: '山从雾里长出来，竹筏划开一整个清晨。', days: 7, checkins: 14 },
  { city: '南京', en: 'NANJING', img: '/static/images/postcard/nanjing.webp', quote: '梧桐叶落满石阶，秋天走得比谁都快。', days: 7, checkins: 12 },
  { city: '汕头', en: 'SHANTOU', img: '/static/images/postcard/shantou.webp', quote: '骑楼的灯亮起来，像把旧时光重新点了一次。', days: 7, checkins: 10 },
  { city: '拉萨', en: 'LHASA', img: '/static/images/postcard/lhasa.webp', quote: '转经的人走得慢，时间在高原上也是慢的。', days: 7, checkins: 12 },
  { city: '喀什', en: 'KASHGAR', img: '/static/images/postcard/kashi.webp', quote: '巷口的铜器敲了一下午，声音比阳光还亮。', days: 7, checkins: 9 },
  { city: '张家界', en: 'ZHANGJIAJIE', img: '/static/images/postcard/zhangjiajie.webp', quote: '云在脚下走，山像是从天上借来的。', days: 7, checkins: 17 },
  { city: '伊犁', en: 'ILI', img: '/static/images/postcard/yili.webp', quote: '草原一眼望不到边，风把云影推得很远。', days: 7, checkins: 15 },
  { city: '婺源', en: 'WUYUAN', img: '/static/images/postcard/wuyuan.webp', quote: '油菜花开满整座山坡，连空气都是甜的。', days: 7, checkins: 10 },
  { city: '平遥', en: 'PINGYAO', img: '/static/images/postcard/pingyao.webp', quote: '红灯笼挂在灰墙下，古城比想象中安静。', days: 7, checkins: 8 },
  { city: '霞浦', en: 'XIAPU', img: '/static/images/postcard/xiapu.webp', quote: '退潮后的滩涂，被落日一条条照亮。', days: 7, checkins: 13 },
  { city: '扬州', en: 'YANGZHOU', img: '/static/images/postcard/yangzhou.webp', quote: '柳枝垂到水面上，春天被剪成一条条。', days: 7, checkins: 7 }
]

const CURRENT_CARD = {
  city: '京都',
  en: 'KYOTO',
  img: '/static/images/postcard/kyoto.webp'
}

export default {
  components: { XtIcon },
  data() {
    return {
      canvasWidth: 340,
      canvasHeight: 480,
      weekStats: {
        checkins: 0,
        minutes: 0,
        streak: 0,
        notes: 0
      },
      currentQuote: {
        text: '每一个不曾起舞的日子，都是对生命的辜负',
        author: '尼采'
      },
      quotes: [
        { text: '每一个不曾起舞的日子，都是对生命的辜负', author: '尼采' },
        { text: '成功不是将来才有的，而是从决定去做的那一刻起，持续累积而成', author: '俞敏洪' },
        { text: '所谓无底深渊，下去，也是前程万里', author: '木心' },
        { text: '星光不问赶路人，时光不负有心人', author: '大冰' },
        { text: '生活不是等待风暴过去，而是学会在雨中翩翩起舞', author: '维维安·格林' },
        { text: '只有那些敢于相信自己内心深处的力量，敢于去梦想的人，才能改变世界', author: '乔布斯' },
        { text: '成功的路上并不拥挤，因为坚持的人不多', author: '佚名' },
        { text: '你的时间有限，不要浪费在重复别人的生活上', author: '乔布斯' },
        { text: '人生最大的挑战是发现自己是谁，而第二大的挑战是对所发现的感到满意', author: '罗杰·塞尔夫' },
        { text: '不要等待机会，而要创造机会', author: '林肯' }
      ],
      historyPostcards: []
    }
  },
  computed: {
    weekNo() {
      const d = new Date()
      const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
      const dayNum = date.getUTCDay() || 7
      date.setUTCDate(date.getUTCDate() + 4 - dayNum)
      const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
      return Math.ceil(((date - yearStart) / 86400000 + 1) / 7)
    },
    postcardDate() {
      const d = new Date()
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${d.getFullYear()}.${mm}.${dd}`
    },
    year() {
      return new Date().getFullYear()
    },
    weekRange() {
      return this.weekRangeOf(0)
    },
    currentCard() {
      return { ...CURRENT_CARD, quote: this.currentQuote.text }
    },
    historyCards() {
      return CITY_CARDS.map((card, i) => ({
        ...card,
        key: card.city,
        badge: `第 ${this.weekNo - (i + 1)} 周`,
        range: this.weekRangeOf(i + 1)
      }))
    },
    collectedCount() {
      return this.historyCards.length + 1
    },
    cityCount() {
      return new Set([this.currentCard.city, ...this.historyCards.map(c => c.city)]).size
    }
  },
  onShow() {
    this.loadData()
    this.generatePostcard()
    playSync.pullKey('postcard').then(ok => {
      if (ok) {
        this.historyPostcards = uni.getStorageSync('postcard_history') || []
      }
    })
  },
  methods: {
    loadData() {
      try {
        const today = new Date()
        const weekStart = new Date(today)
        weekStart.setDate(today.getDate() - today.getDay())

        const checkins = uni.getStorageSync('habit_checkins') || {}
        const notes = uni.getStorageSync('habit_notes') || {}

        let weekCheckins = 0
        let weekMinutes = 0
        let weekNotes = 0

        Object.values(checkins).forEach(dates => {
          dates.forEach(date => {
            if (date >= weekStart.toISOString().split('T')[0]) {
              weekCheckins++
            }
          })
        })

        Object.values(notes).forEach(noteList => {
          noteList.forEach(note => {
            if (note.date >= weekStart.getTime()) {
              weekNotes++
            }
          })
        })

        const streakDays = this.calculateStreak(checkins)

        this.weekStats = {
          checkins: weekCheckins,
          minutes: weekMinutes,
          streak: streakDays,
          notes: weekNotes
        }

        this.currentQuote = this.quotes[Math.floor(Math.random() * this.quotes.length)]

        this.historyPostcards = uni.getStorageSync('postcard_history') || []
      } catch (e) {
        console.error('加载明信片数据失败', e)
      }
    },
    calculateStreak(checkins) {
      let streak = 0
      const today = new Date()

      for (let i = 0; i < 365; i++) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateStr = date.toISOString().split('T')[0]

        let hasCheckin = false
        Object.values(checkins).forEach(dates => {
          if (dates.includes(dateStr)) {
            hasCheckin = true
          }
        })

        if (hasCheckin) {
          streak++
        } else if (i > 0) {
          break
        }
      }
      return streak
    },
    generatePostcard() {
      const ctx = uni.createCanvasContext('postcardCanvas')
      const w = this.canvasWidth
      const h = this.canvasHeight

      const gradient = ctx.createLinearGradient(0, 0, w, h)
      gradient.addColorStop(0, '#6B8E7B')
      gradient.addColorStop(0.5, '#8FBC8F')
      gradient.addColorStop(1, '#A7D7A0')
      ctx.setFillStyle(gradient)
      ctx.fillRect(0, 0, w, h)

      ctx.setFillStyle('rgba(255,255,255,0.1)')
      ctx.beginPath()
      ctx.arc(w * 0.8, h * 0.2, 60, 0, Math.PI * 2)
      ctx.fill()

      ctx.beginPath()
      ctx.arc(w * 0.2, h * 0.8, 40, 0, Math.PI * 2)
      ctx.fill()

      ctx.setFillStyle('#FFFFFF')
      ctx.setFontSize(28)
      ctx.setTextAlign('center')
      ctx.fillText('循途', w / 2, 40)

      ctx.setFontSize(20)
      ctx.setFillStyle('rgba(255,255,255,0.8)')
      const weekStr = this.getWeekString()
      ctx.fillText(weekStr, w / 2, 70)

      ctx.setFillStyle('#FFFFFF')
      ctx.fillRect(20, 100, w - 40, 280)

      ctx.setStrokeStyle('#E8E8E8')
      ctx.setLineWidth(1)
      ctx.strokeRect(20, 100, w - 40, 280)

      ctx.setFillStyle('#333333')
      ctx.setFontSize(24)
      ctx.setTextAlign('left')
      ctx.fillText('📊 本周学习报告', 35, 140)

      ctx.setFillStyle('#666666')
      ctx.setFontSize(22)

      const stats = [
        { icon: '✅', label: '打卡次数', value: this.weekStats.checkins },
        { icon: '⏱️', label: '专注时长', value: this.formatMinutes(this.weekStats.minutes) },
        { icon: '🔥', label: '连续打卡', value: `${this.weekStats.streak}天` },
        { icon: '📝', label: '心情记录', value: `${this.weekStats.notes}条` }
      ]

      let y = 180
      stats.forEach(stat => {
        ctx.fillText(`${stat.icon} ${stat.label}: ${stat.value}`, 35, y)
        y += 40
      })

      ctx.setFillStyle('#E8E8E8')
      ctx.fillRect(35, y + 10, w - 70, 1)

      ctx.setFillStyle('#333333')
      ctx.setFontSize(18)
      ctx.setTextAlign('center')

      const quoteLines = this.wrapText(this.currentQuote.text, ctx, w - 70)
      y += 40
      quoteLines.forEach(line => {
        ctx.fillText(line, w / 2, y)
        y += 30
      })

      ctx.setFillStyle('#999999')
      ctx.setFontSize(16)
      ctx.fillText(`—— ${this.currentQuote.author}`, w / 2, y + 20)

      ctx.setFillStyle('#FFFFFF')
      ctx.setFontSize(14)
      ctx.setTextAlign('center')
      ctx.fillText('Keep Going, Keep Growing', w / 2, h - 25)

      ctx.draw()
    },
    wrapText(text, ctx, maxWidth) {
      const words = text.split('')
      const lines = []
      let line = ''

      for (let i = 0; i < words.length; i++) {
        const testLine = line + words[i]
        const metrics = ctx.measureText(testLine)
        if (metrics.width > maxWidth && i > 0) {
          lines.push(line)
          line = words[i]
        } else {
          line = testLine
        }
      }
      lines.push(line)
      return lines
    },
    getWeekString() {
      const today = new Date()
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay())

      const formatDate = (date) => {
        return `${date.getMonth() + 1}月${date.getDate()}日`
      }

      return `${formatDate(weekStart)} - ${formatDate(today)}`
    },
    formatMinutes(minutes) {
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60)
        const mins = minutes % 60
        return mins > 0 ? `${hours}h${mins}m` : `${hours}h`
      }
      return `${minutes}m`
    },
    saveToAlbum() {
      uni.canvasToTempFilePath({
        canvasId: 'postcardCanvas',
        success: (res) => {
          // #ifdef H5
          // H5 没有相册权限，直接触发浏览器下载
          this.downloadInH5(res.tempFilePath)
          return
          // #endif
          uni.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success: () => {
              this.saveToHistory(res.tempFilePath)
              uni.showToast({ title: '保存成功', icon: 'success' })
            },
            fail: () => {
              uni.showToast({ title: '保存失败，请授权相册', icon: 'none' })
            }
          })
        },
        fail: () => {
          uni.showToast({ title: '生成图片失败', icon: 'none' })
        }
      })
    },
    downloadInH5(filePath) {
      try {
        const link = document.createElement('a')
        link.href = filePath
        link.download = `循途明信片_${this.postcardDate}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        this.saveToHistory(filePath)
        uni.showToast({ title: '已保存到下载目录', icon: 'success' })
      } catch (e) {
        console.error('下载明信片失败', e)
        uni.showToast({ title: '保存失败，请长按图片保存', icon: 'none' })
      }
    },
    saveToHistory(imagePath) {
      try {
        const history = uni.getStorageSync('postcard_history') || []
        // 只存可持久化的文件路径；H5 的 base64/blob 图片体积大，
        // 会撑爆 localStorage 并让 playSync 超过后端 64KB 上限导致整份明信片数据同步失败
        const isInlineImage = typeof imagePath === 'string' &&
          (imagePath.startsWith('data:') || imagePath.startsWith('blob:'))
        history.unshift({
          id: Date.now(),
          date: this.getWeekString(),
          image: isInlineImage ? '' : imagePath,
          timestamp: Date.now()
        })

        if (history.length > 10) {
          history.pop()
        }

        uni.setStorageSync('postcard_history', history)
        this.historyPostcards = history
        playSync.schedulePush('postcard')
      } catch (e) {
        console.error('保存明信片历史失败', e)
      }
    },
    weekRangeOf(offset) {
      const now = new Date()
      const day = now.getDay() || 7
      const monday = new Date(now)
      monday.setDate(now.getDate() - day + 1 - offset * 7)
      const sunday = new Date(monday)
      sunday.setDate(monday.getDate() + 6)
      const f = d =>
        `${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
      return `${f(monday)} — ${f(sunday)}`
    },
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) uni.navigateBack()
      else uni.switchTab({ url: '/pages/index/index' })
    },
    goGrowthTrack() {
      uni.navigateTo({ url: '/pages/growth-track/growth-track' })
    },
    goGallery() {
      uni.navigateTo({ url: '/pages/postcard-gallery/postcard-gallery' })
    }
  }
}
</script>

<style lang="scss" scoped>
/* 往期明信片 · 胶片版（1:1 对齐 循途FoloWay-往期明信片视觉稿.html） */
.xt-page.xt-postcard {
  background: #f6f3ec;
  background-image: none;
  color: #1f2c26;
}

.xt-page.xt-postcard .pc-scroll {
  padding: 0 18px 40px;
}

/* 顶部导航 */
.pc-nav {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
}

.pc-nav-ic {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
  color: #4c5a53;
}

.pc-nav-ic .ic {
  width: 17px;
  height: 17px;
}

.pc-nav-title {
  font-size: 14px;
  letter-spacing: 0.08em;
  color: #4c5a53;
}

/* 标题区 */
.pc-intro {
  padding: 14px 2px 20px;
}

.pc-intro-title {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 27px;
  letter-spacing: 0.04em;
  font-weight: 700;
  line-height: 1.3;
}

.pc-intro-sub {
  margin-top: 8px;
  font-size: 12px;
  color: #8c978f;
  letter-spacing: 0.02em;
}

.pc-intro-sub .hl {
  color: #3c6b55;
  font-weight: 600;
}
.pc-more {
  margin-top: 9px;
  font-size: 11px;
  font-weight: 600;
  color: #3c6b55;
  letter-spacing: 0.02em;
}

/* 明信片卡片 */
.pc-cards {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.pc-card {
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 8px 26px rgba(31, 44, 38, 0.08);
  border: 1px solid rgba(232, 226, 214, 0.9);
  animation: pc-rise 0.6s ease both;
}

.pc-card:nth-child(2) { animation-delay: 0.06s; }
.pc-card:nth-child(3) { animation-delay: 0.12s; }
.pc-card:nth-child(4) { animation-delay: 0.18s; }

@keyframes pc-rise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}

.pc-photo-wrap {
  position: relative;
  overflow: hidden;
  background: #dfd9cc;
  aspect-ratio: 16 / 9;
}

.pc-photo,
.pc-photo :deep(div),
.pc-photo :deep(img) {
  display: block;
  width: 100%;
  height: 100%;
}
.pc-photo :deep(div) {
  background-size: cover;
  background-position: center;
}
.pc-photo :deep(img) {
  object-fit: cover;
}

.pc-photo {
  /* 素材已裁掉水印边，按 16:9 完整画幅展示 */
  filter: saturate(1.06) contrast(1.01);
  transition: transform 0.8s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.pc-photo-wrap::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  box-shadow: inset 0 0 64px rgba(0, 0, 0, 0.1);
  pointer-events: none;
}

.pc-photo-wrap::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 46%;
  background: linear-gradient(to top, rgba(12, 20, 16, 0.48), rgba(12, 20, 16, 0.06) 55%, transparent);
  pointer-events: none;
}

.pc-badge {
  position: absolute;
  z-index: 2;
  left: 14px;
  top: 14px;
  font-size: 10.5px;
  letter-spacing: 0.06em;
  color: #22302a;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  padding: 5px 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.pc-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #3c6b55;
}

.pc-city {
  position: absolute;
  z-index: 2;
  left: 18px;
  bottom: 14px;
  color: #fff;
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 24px;
  letter-spacing: 0.06em;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
}

.pc-city .pc-city-en {
  display: block;
  font-family: inherit;
  font-size: 11px;
  letter-spacing: 0.18em;
  opacity: 0.82;
  margin-top: 3px;
}

.pc-content {
  padding: 15px 18px 16px;
}

.pc-quote {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 13.5px;
  line-height: 1.85;
  color: #4c5a53;
  letter-spacing: 0.01em;
}

.pc-meta {
  margin-top: 10px;
  font-size: 10.5px;
  color: #a6afa8;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.pc-sep {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #c9d0ca;
}

.pc-actions {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f1ece2;
  display: flex;
  align-items: center;
  gap: 18px;
}

.pc-act {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: #7e8a82;
}

.pc-act .ic {
  width: 14px;
  height: 14px;
}

.pc-act-right {
  margin-left: auto;
  color: #3c6b55;
  font-weight: 600;
}

/* 小卡片：城市名略小 */
.pc-mini .pc-city {
  font-size: 20px;
}

/* 结尾 */
.pc-end {
  margin: 30px 4px 0;
  text-align: center;
  font-size: 11px;
  color: #a9b2ac;
  letter-spacing: 0.06em;
  line-height: 1.9;
}

.pc-end .line {
  display: block;
  width: 26px;
  height: 1px;
  background: #dcd5c7;
  margin: 0 auto 14px;
}

/* 胶片颗粒：叠在页面最上层 */
.pc-grain {
  position: absolute;
  inset: 0;
  z-index: 60;
  pointer-events: none;
  opacity: 0.045;
  mix-blend-mode: multiply;
  background-size: 160px 160px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E");
}

.xt-page.xt-postcard .xt-export-canvas {
  position: absolute;
  left: -10000px;
  top: 0;
}

@media (prefers-reduced-motion: reduce) {
  .pc-card { animation: none; }
  .pc-photo { transition: none; }
}
</style>
