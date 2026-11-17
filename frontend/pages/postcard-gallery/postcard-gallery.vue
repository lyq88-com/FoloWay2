<template>
  <view class="xt-page pg-page">
    <view class="body pg-body">
      <!-- 顶栏 -->
      <view class="pg-nav">
        <view class="pg-nav-ic" @click="goBack"><xt-icon name="i-left" :size="15" /></view>
        <view class="pg-nav-tx">
          <text class="t">明信片风景</text>
          <text class="s">点开可以看大图</text>
        </view>
        <view class="pg-nav-ic" @click="goCreate"><xt-icon name="i-plus" :size="15" /></view>
      </view>

      <!-- 标题区 -->
      <view class="pg-intro">
        <text class="pg-title">往期明信片</text>
        <view class="pg-sub">
          2026 · 已收集 <text class="hl">{{ cities.length }}</text> 张 · 来自 <text class="hl">{{ cities.length }}</text> 座城市
        </view>
      </view>

      <!-- 明信片卡片列表 -->
      <view class="pg-cards">
        <view
          v-for="(c, i) in cities"
          :key="c.city"
          class="pg-card"
          :class="{ 'pg-card--featured': i === 0 }"
        >
          <view class="pg-img" @click="preview(i)">
            <view class="pg-badge">
              <view class="dot"></view>
              <text>{{ i === 0 ? '本周 · 第 ' + (45) + ' 周' : '第 ' + (45 - i) + ' 周' }}</text>
            </view>
            <image class="pg-img-src" :src="c.img" mode="aspectFill" lazy-load />
            <view class="pg-shade"></view>
            <view class="pg-city">
              <text class="c">{{ c.city }}</text>
              <text class="e">{{ c.en }}</text>
            </view>
          </view>

          <view class="pg-card-body">
            <text class="pg-quote">"{{ quoteOf(c.city) }}"</text>
            <view class="pg-meta">
              <text>{{ metaOf(i).date }}</text>
              <view class="sep"></view>
              <text>与她相伴 7 天</text>
              <view class="sep"></view>
              <text>{{ metaOf(i).checkins }} 次打卡</text>
            </view>
            <view class="pg-actions">
              <view class="pg-act" @click="onFav(i)">
                <xt-icon name="i-heart" :size="13" />
                <text>收藏</text>
              </view>
              <view class="pg-act" @click="onPoster(i)">
                <xt-icon name="i-share" :size="13" />
                <text>生成海报</text>
              </view>
              <view class="pg-act pg-act--right" @click="preview(i)">
                <text>查看这一周</text>
                <xt-icon name="i-right" :size="11" />
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="pg-end">
        <view class="line"></view>
        <text>每一张，都是那一周你们一起走过的路</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 明信片风景图集 —— 浏览 static/images/postcard/ 下的全部风景照
 * 布局参考：往期明信片视觉稿（整行通栏卡片）
 */
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { POSTCARD_CITIES } from '@/common/postcard-cities'

const QUOTES = {
  '京都': '成功不是将来才有的，而是从决定去做的那一刻起，持续累积而成。',
  '上海': '慢一点也没关系，方向对了就好。',
  '大理': '风把云吹散的时候，忽然就不那么着急了。',
  '杭州': '早起的那天，湖面比想象中安静。',
  '重庆': '灯一层层亮起来的时候，忽然觉得日子也在往前走。',
  '成都': '下雨天最适合什么都不做，就坐着听雨。',
  '西安': '城墙上的风很大，把烦心事都吹散了。',
  '苏州': '园林里的水很静，像把时间也一起放慢了。',
  '青岛': '海雾散开的那一下，早起这件事突然就值了。',
  '厦门': '三角梅开得太认真，我都不好意思偷懒。',
  '哈尔滨': '零下的城市，每一扇窗户里都是暖的。',
  '长沙': '江边的风一吹，夜宵都变得理直气壮。',
  '泉州': '红砖被雨打得发亮，花串一路垂到肩头。',
  '洛阳': '灯一层层挂上去，夜色就软了下来。',
  '景德镇': '看匠人拉坯的时候，忽然明白慢是什么。',
  '阿勒泰': '草原上的风很干净，像被雪山洗过一遍。',
  '敦煌': '沙丘的影子拉得很长，一天就这样过去了。',
  '桂林': '山从雾里长出来，竹筏划开一整个清晨。',
  '南京': '梧桐叶落满石阶，秋天走得比谁都快。',
  '汕头': '骑楼的灯亮起来，像把旧时光重新点了一次。',
  '拉萨': '转经的人走得慢，时间在高原上也是慢的。',
  '喀什': '巷口的铜器敲了一下午，声音比阳光还亮。',
  '张家界': '云在脚下走，山像是从天上借来的。',
  '伊犁': '草原一眼望不到边，风把云影推得很远。',
  '婺源': '油菜花开满整座山坡，连空气都是甜的。',
  '平遥': '红灯笼挂在灰墙下，古城比想象中安静。',
  '霞浦': '退潮后的滩涂，被落日一条条照亮。',
  '扬州': '柳枝垂到水面上，春天被剪成一条条。'
}

export default {
  components: { XtIcon },
  data() {
    return {
      cities: POSTCARD_CITIES
    }
  },
  methods: {
    quoteOf(city) {
      return QUOTES[city] || '每一段路，都值得被好好记住。'
    },
    metaOf(i) {
      // 以第45周（本周）为基准往前推
      const weekNum = 45 - i
      const checkins = [18, 12, 9, 15, 11, 6, 14, 10, 8, 12, 16, 9, 13, 10, 7, 18, 9, 11, 14, 8, 12, 9, 17, 15, 10, 8, 13, 7][i] || 10
      // 计算日期范围（2026年，第45周为11.09-11.15）
      const baseMonday = new Date(2026, 10, 9) // 2026-11-09 周一
      const monday = new Date(baseMonday.getTime() - i * 7 * 86400000)
      const sunday = new Date(monday.getTime() + 6 * 86400000)
      const fmt = d => `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
      const dateStr = `${fmt(monday).slice(5)} — ${fmt(sunday).slice(5)}`
      return { date: dateStr, checkins }
    },
    preview(i) {
      const urls = this.cities.map(c => c.img)
      uni.previewImage({ urls, current: urls[i] || urls[0] })
    },
    onFav(i) {
      uni.showToast({ title: '已收藏', icon: 'success' })
    },
    onPoster(i) {
      uni.showToast({ title: '海报生成中…', icon: 'loading' })
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goCreate() {
      uni.switchTab({ url: '/pages/create/create' })
    }
  }
}
</script>

<style lang="scss" scoped>
.pg-page {
  background:
    radial-gradient(420px 300px at 88% -4%, rgba(196, 205, 189, 0.24), transparent 62%),
    radial-gradient(380px 320px at 4% 102%, rgba(228, 211, 187, 0.22), transparent 60%),
    #f8f4ec;
  color: #18231d;
}
.pg-body {
  padding-bottom: calc(36px + env(safe-area-inset-bottom));
}

/* 顶栏 */
.pg-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: calc(env(safe-area-inset-top) + 12px) 0 2px;
}
.pg-nav-ic {
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
.pg-nav-tx {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.pg-nav-tx .t {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
}
.pg-nav-tx .s {
  margin-top: 2px;
  font-size: 8.5px;
  color: #a2aaa3;
  letter-spacing: 0.3px;
}

/* 标题 */
.pg-intro {
  padding: 16px 2px 18px;
}
.pg-title {
  display: block;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.pg-sub {
  margin-top: 7px;
  font-size: 9.5px;
  color: #8c978f;
  letter-spacing: 0.3px;
}
.pg-sub .hl {
  color: #3c6b55;
  font-weight: 700;
}

/* 卡片列表 */
.pg-cards {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
/* 平板 / 桌面：双列排布，单张比例不变 */
@media (min-width: 760px) {
  .pg-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
}

/* 单张明信片卡片 */
.pg-card {
  background: #fffdfa;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(30, 42, 36, 0.07);
  box-shadow: 0 16px 32px -28px rgba(24, 35, 29, 0.6);
}

/* 图片区：按素材原始 16:9 等比缩放，窄屏不挤、宽屏不变形 */
.pg-img {
  position: relative;
  overflow: hidden;
  background: #dfd9cc;
  aspect-ratio: 16 / 9;
}
.pg-img-src {
  display: block;
  width: 100%;
  height: 100%;
}
.pg-img :deep(uni-image),
.pg-img :deep(uni-image > div),
.pg-img :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.pg-img :deep(uni-image > div) {
  background-size: cover;
  background-position: center;
}
.pg-img :deep(uni-image img) {
  object-fit: cover;
}
.pg-shade {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 46%;
  background: linear-gradient(to top, rgba(12, 20, 16, 0.5), rgba(12, 20, 16, 0.06) 55%, transparent);
  pointer-events: none;
}
.pg-badge {
  position: absolute;
  z-index: 2;
  left: 14px;
  top: 14px;
  font-size: 9.5px;
  letter-spacing: 0.06em;
  color: #22302a;
  background: rgba(255, 255, 255, 0.9);
  padding: 5px 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.pg-badge .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #3c6b55;
}
.pg-city {
  position: absolute;
  z-index: 2;
  left: 18px;
  bottom: 14px;
  color: #fff;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
  font-size: 22px;
  letter-spacing: 0.06em;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}
.pg-city .e {
  font-size: 10px;
  letter-spacing: 0.18em;
  opacity: 0.82;
  margin-top: 3px;
}

/* 卡片内容区 */
.pg-card-body {
  padding: 15px 18px 16px;
}
.pg-quote {
  display: block;
  font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
  font-size: 13px;
  line-height: 1.85;
  color: #4c5a53;
  letter-spacing: 0.01em;
}
.pg-meta {
  margin-top: 10px;
  font-size: 10px;
  color: #a6afa8;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pg-meta .sep {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #c9d0ca;
}
.pg-actions {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f1ece2;
  display: flex;
  align-items: center;
  gap: 18px;
}
.pg-act {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #7e8a82;
}
.pg-act--right {
  margin-left: auto;
  color: #3c6b55;
  font-weight: 600;
}

.pg-end {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 26px 0 10px;
  color: #a9b2ac;
  font-size: 8px;
  letter-spacing: 0.06em;
}
.pg-end .line {
  width: 40px;
  height: 1px;
  background: rgba(30, 42, 36, 0.12);
}
</style>
