<template>
  <view class="xt-page xt-s31">
    <view class="body">
      <view class="wk-head">
        <view class="wk-head-l">
          <view class="icon-btn wk-back" @click="goBack"><xt-icon name="i-left" /></view>
          <view>
            <view class="wk-title">环球行走</view>
            <view class="wk-sub">{{ rangeLabel }}和她走了 {{ rangeStepsDisplay }} 步</view>
          </view>
        </view>
        <view class="wk-actions">
          <view class="icon-btn wk-archive" @click="goGrowthTrack"><xt-icon name="i-archive" /></view>
          <view class="wk-seg">
            <span :class="{ on: range === 'today' }" @click="range = 'today'">今天</span>
            <span :class="{ on: range === 'week' }" @click="range = 'week'">本周</span>
          </view>
        </view>
      </view>

      <view class="v7-map-frame">
        <walk-map compact />
      </view>

      <view class="wk-hero">
        <view class="wk-hrow">
          <view class="wk-loc">
            <xt-icon name="i-world" />
            <b>第 {{ passedNodesCount }} 站 · {{ currentStage.name }}</b>
            <span>· {{ totalCheckins }} 次打卡</span>
          </view>
          <view class="wk-streak"><i></i>连续 {{ streakDays }} 天</view>
        </view>
        <view class="wk-num">
          <b>{{ rangeStepsDisplay }}</b>
          <em>步 · {{ rangeLabel }}累计</em>
          <span>{{ stageProgress }}%</span>
        </view>
        <view class="wk-track">
          <view class="wk-ends">
            <span>出发 · 起点</span>
            <span>{{ currentStage.name }} · 前方一站</span>
          </view>
          <view class="wk-line">
            <i class="wk-fill" :style="{ width: stageProgress + '%' }"></i>
            <span class="wk-av">
              <image v-if="companionPhoto" :src="companionPhoto" mode="aspectFill" />
              <view v-else class="wk-fb"><text>{{ companionEmoji }}</text></view>
            </span>
          </view>
        </view>
        <view class="wk-foot">
          <span><b>{{ totalCheckins }}</b> 次到站</span>
          <span class="dot"></span>
          <span>约 {{ Math.round(totalSteps / 110) }} 分钟</span>
          <span class="wk-her"><i></i>她也在走 · {{ totalStepsDisplay }} 步</span>
        </view>
      </view>

      <!-- 旅程站点：从 flower 页合并 -->
      <view class="wk-route">
        <view class="wk-rhead">
          <b>旅程 <i>{{ passedNodesCount }}</i> / {{ totalNodesCount }} 站</b>
          <span>{{ currentStage.name }} · {{ totalStepsDisplay }} 步</span>
        </view>
        <view class="wk-stops">
          <view
            v-for="(s, i) in routeStops"
            :key="'st' + i"
            class="wk-stop"
            :class="{ done: s.done, now: s.now }"
          >
            <b>{{ s.short }}</b>
            <span>{{ s.label }}</span>
          </view>
        </view>
      </view>

      <view class="wk-card">
        <view class="wk-chead">
          <b>{{ rangeLabel }}步数</b>
          <span>{{ rangeStepsDisplay }} 步 · 与她同行</span>
        </view>
        <view class="wk-bars">
          <view
            v-for="(b, i) in weeklyBars"
            :key="'wb' + i"
            class="wk-b"
            :class="{ on: b.on }"
          >
            <i :style="{ height: b.height + '%' }"></i>
          </view>
        </view>
        <view class="wk-days">
          <span v-for="(d, i) in weekDayLabels" :key="'wd' + i" :class="{ on: weeklyBars[i].on }">{{ d }}</span>
        </view>
      </view>

      <!-- 同行纪念：从 flower 页合并 -->
      <view class="wk-shot">
        <view class="wk-shot-ph">
          <image v-if="companionHero" :src="companionHero" mode="aspectFill" />
          <view v-else class="wk-fb wk-fb-lg"><text>{{ companionEmoji }}</text></view>
          <view class="wk-shot-badge"><i></i>{{ currentStage.name }} · 第 {{ passedNodesCount }} 站</view>
        </view>
        <view class="wk-shot-cap">
          <text class="cap-l">同行纪念 · 她留给你的话</text>
          <text class="cap-q">「{{ companionVoice }}」</text>
          <text class="cap-n">{{ currentCharacterName }} · 与你同行</text>
        </view>
      </view>

      <view class="wk-stats">
        <view class="wk-stat">
          <b>{{ (totalSteps * 0.0007).toFixed(1) }}</b><em>km</em><span>今日距离</span>
        </view>
        <view class="wk-stat">
          <b>{{ Math.round(totalSteps / 110) }}</b><em>min</em><span>户外时间</span>
        </view>
        <view class="wk-stat">
          <b>{{ Math.round(totalSteps * 0.04) }}</b><em>kcal</em><span>消耗</span>
        </view>
      </view>

      <view class="wk-recent">
        <view class="wk-rc" v-for="stop in recentStops" :key="stop.key">
          <b>{{ stop.mark }}</b>
          <view>
            <em>{{ stop.name }}</em>
            <span>{{ stop.meta }}</span>
          </view>
        </view>
      </view>

      <view class="wk-note">
        <span>{{ rangeLabel }}已经走了 <b>{{ rangeSegments }}</b> 段路</span>
        <span>她在每一段都留了一句话</span>
      </view>

      <!-- 明信片入口：从 flower 页合并 -->
      <view class="wk-post" @click="goPostcard">
        <view class="wk-post-ico"><xt-icon name="i-archive" /></view>
        <view class="wk-post-tx">
          <view class="wk-post-t">她寄回的明信片</view>
          <view class="wk-post-d">沿途共 {{ recentHistory.length }} 张 · 去翻看这一路的风景</view>
        </view>
        <view class="wk-post-ar"><xt-icon name="i-right" /></view>
      </view>

      <view class="wk-cta">
        <span class="wk-btn" @click="goChat">继续旅程</span>
        <span class="wk-ghost" @click="goGrowthTrack">成长足迹</span>
      </view>
    </view>
  </view>
</template>

<script>
import WalkMap from '@/components/walk-map/walk-map.vue'
import { getAllCharacters, getAllCustomCharacters, getCharacterById } from '@/common/ai-characters'
import { getActivePartnerId, getPartnerAvatar, getPartnerPhoto, findPartner } from '@/common/ai-partner'

export default {
  components: { WalkMap },
  data() {
    return {
      refreshTimer: null,
      scrollAnchor: '',
      // 今天 / 本周 切换（原来两个 tab 没有点击事件）
      range: 'today'
    }
  },
  computed: {
    // === 今天 / 本周 真实聚合：数据源 walkHistory，步数权重与 store 一致 ===
    walkEntries() {
      const history = this.$store.getters.walkHistory || []
      const weight = { habit: 1, emotion: 0.3, meditation: 0.5 }
      return history.map(h => ({
        date: String(h.date || ''),
        steps: weight[h.type] !== undefined ? weight[h.type] : 0
      }))
    },
    todayKey() {
      return this.dayKey(new Date())
    },
    weekStartKey() {
      const d = new Date()
      d.setDate(d.getDate() - ((d.getDay() + 6) % 7))
      return this.dayKey(d)
    },
    todaySteps() {
      return this.sumSteps(e => e.date === this.todayKey)
    },
    weekSteps() {
      return this.sumSteps(e => e.date >= this.weekStartKey)
    },
    rangeLabel() {
      return this.range === 'week' ? '本周' : '今天'
    },
    rangeSteps() {
      return this.range === 'week' ? this.weekSteps : this.todaySteps
    },
    rangeStepsDisplay() {
      const s = this.rangeSteps
      return s % 1 === 0 ? s.toFixed(0) : s.toFixed(1)
    },
    rangeSegments() {
      return this.walkEntries.filter(e => (
        this.range === 'week' ? e.date >= this.weekStartKey : e.date === this.todayKey
      )).length
    },
    weekDayLabels() {
      return ['一', '二', '三', '四', '五', '六', '日']
    },
    // 最近 7 天真实步数柱状图（原来写死 [52, 74, ...]）
    weeklyBars() {
      const now = new Date()
      const days = []
      for (let i = 0; i < 7; i++) {
        const d = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        d.setDate(d.getDate() - ((now.getDay() + 6) % 7) + i)
        days.push({
          date: this.dayKey(d),
          steps: this.sumSteps(e => e.date === this.dayKey(d)),
          on: i === ((now.getDay() + 6) % 7)
        })
      }
      const max = Math.max(1, ...days.map(x => x.steps))
      return days.map(x => ({
        ...x,
        height: x.steps ? Math.max(10, Math.round(x.steps / max * 100)) : 6
      }))
    },
    currentCharacterId() {
      return getActivePartnerId()
    },
    currentCharacterName() {
      const c = findPartner(this.currentCharacterId)
      return c ? c.name : 'AI伙伴'
    },
    companionEmoji() {
      const c = findPartner(this.currentCharacterId)
      return (c && c.avatar) || '🌿'
    },
    streakDays() {
      return this.$store.state.streakDays || 0
    },
    totalCheckins() {
      return this.$store.getters.totalCheckins
    },
    totalSteps() {
      return this.$store.state.walkMap.totalSteps || 0
    },
    totalStepsDisplay() {
      const s = this.totalSteps
      return s % 1 === 0 ? s.toFixed(0) : s.toFixed(1)
    },
    currentStage() {
      return this.$store.getters.currentStage
    },
    stageProgress() {
      return this.$store.getters.stageProgress
    },
    stageMaxLabel() {
      const next = this.currentStage.nextThreshold
      if (next === null || next === Infinity) return '∞'
      return next
    },
    currentDestination() {
      return this.currentStage.name || '起点'
    },
    stageCardBg() {
      const t = this.currentStage.theme
      return `linear-gradient(135deg, ${t.skyTop} 0%, ${t.skyBottom} 100%)`
    },
    stageProgressGradient() {
      const t = this.currentStage.theme
      return `linear-gradient(90deg, ${t.pathColor} 0%, ${t.accent} 100%)`
    },
    stageNodes() {
      return this.currentStage.nodes || []
    },
    totalNodesCount() {
      return this.stageNodes.length
    },
    passedNodesCount() {
      if (!this.stageNodes.length) return 0
      const progress = this.stageProgress
      const passed = Math.floor((progress / 100) * this.stageNodes.length)
      return Math.min(passed, this.stageNodes.length)
    },
    routeStops() {
      const passed = this.passedNodesCount
      return this.stageNodes.map((node, idx) => ({
        label: node.label || '',
        short: (node.label || '·').slice(0, 1),
        done: idx < passed,
        now: idx === passed
      }))
    },
    companionPhoto() {
      return getPartnerAvatar(this.currentCharacterId) || ''
    },
    // 同行纪念使用 3:4 完整立绘；地图小头像使用脸部特写
    companionHero() {
      return getPartnerPhoto(this.currentCharacterId) || ''
    },
    companionList() {
      const fixed = getAllCharacters().slice(0, 12)
      const custom = getAllCustomCharacters()
      return [...fixed, ...custom]
    },
    recentHistory() {
      const history = this.$store.getters.walkHistory || []
      return [...history].reverse().slice(0, 10)
    },
    recentStops() {
      const list = this.recentHistory.slice(0, 3)
      if (!list.length) {
        return [
          { key: 'd1', mark: '起', name: '起点', meta: '出发 · 等待第一步' },
          { key: 'd2', mark: '今', name: '今天', meta: '刚刚 · 继续走' },
          { key: 'd3', mark: '明', name: '下一站', meta: '还差几次打卡' }
        ]
      }
      return list.map((log, i) => ({
        key: 'log' + i,
        mark: log.date ? log.date.slice(-2) : '·',
        name: this.getTypeName(log.type),
        meta: (log.date || '') + (log.time ? ' · ' + log.time : '')
      }))
    },
    companionVoice() {
      // 根据当前进度生成鼓励语
      const progress = this.stageProgress
      const stage = this.currentStage
      const voices = [
        `每一步都在靠近${stage.name}的终点，你的坚持很了不起`,
        `已经走了${this.totalStepsDisplay}步了，${stage.name}的风景正等着你`,
        `连续${this.streakDays}天的坚持，旅途因你而精彩`,
        `${stage.name}的旅程还在继续，一起走下去吧`,
        `每一次打卡都是旅途中的风景，继续前行`
      ]
      const idx = Math.floor(progress / 20) % voices.length
      return voices[idx]
    },
    voiceCardStyle() {
      const t = this.currentStage.theme
      return {
        background: `linear-gradient(135deg, ${t.skyTop}15 0%, ${t.accent}10 100%)`,
        borderColor: t.accent + '30'
      }
    },
    voiceAvatarStyle() {
      const c = getCharacterById(this.currentCharacterId)
      if (c && c.colors) {
        return {
          background: `linear-gradient(135deg, ${c.colors.primary}, ${c.colors.accent})`
        }
      }
      return {}
    }
  },
  onShow() {
    this.startAutoRefresh()
  },
  onHide() {
    this.stopAutoRefresh()
  },
  onUnload() {
    this.stopAutoRefresh()
  },
  methods: {
    dayKey(d) {
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    },
    sumSteps(pred) {
      return this.walkEntries.filter(pred).reduce((sum, e) => sum + e.steps, 0)
    },
    goBack() {
      // 自定义导航栏后没有原生返回键；直接打开本页（无页面栈）时回退到发现页
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/discover/discover' }) })
    },
    goChat() {
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    goGrowthTrack() {
      uni.navigateTo({ url: '/pages/growth-track/growth-track' })
    },
    goPostcard() {
      uni.navigateTo({ url: '/pages/postcard/postcard' })
    },
    refreshStatus() {
      uni.showToast({ title: '已刷新', icon: 'success', duration: 1000 })
    },
    switchCompanion(companion) {
      this.$store.commit('setAiConfig', {
        avatarType: companion.id,
        name: companion.name
      })
      uni.showToast({
        title: `${companion.name}加入旅程`,
        icon: 'none',
        duration: 1500
      })
    },
    getTypeName(type) {
      const map = {
        habit: '习惯打卡',
        emotion: '情绪记录',
        meditation: '正念放松'
      }
      return map[type] || '行走'
    },
    getTypeIcon(type) {
      const map = {
        habit: '✓',
        emotion: '♡',
        meditation: '◐'
      }
      return map[type] || '·'
    },
    isNodePassed(idx) {
      const progress = this.stageProgress
      const nodeProgress = (idx / this.stageNodes.length) * 100
      return progress > nodeProgress
    },
    isNodeActive(idx) {
      const progress = this.stageProgress
      const nodeProgress = (idx / this.stageNodes.length) * 100
      const nextNodeProgress = ((idx + 1) / this.stageNodes.length) * 100
      return progress >= nodeProgress && progress < nextNodeProgress
    },
    milestoneStyle(idx) {
      const t = this.currentStage.theme
      if (this.isNodePassed(idx)) {
        return { background: `linear-gradient(135deg, ${t.accent}, ${t.pathColor})` }
      }
      if (this.isNodeActive(idx)) {
        return {
          background: `linear-gradient(135deg, ${t.skyTop}, ${t.skyBottom})`,
          boxShadow: `0 0 20rpx ${t.accent}80`
        }
      }
      return { background: '#F0F0F0' }
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {}, 30000)
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 设计稿 img 尺寸同步到 uni-image 包装层 */
.xt-page.xt-s31 .wk-av uni-image {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s31 .wk-tip uni-image {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: block;
  flex-shrink: 0;
}
.xt-page.xt-s31 .wk-shot-ph uni-image,
.xt-page.xt-s31 .wk-shot-ph :deep(uni-image > div),
.xt-page.xt-s31 .wk-shot-ph :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s31 .wk-shot-ph :deep(uni-image img) {
  object-fit: cover;
}

/* 无立绘伙伴回退 */
.xt-page.xt-s31 .wk-fb {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  font-size: 12px;
  line-height: 1;
  border-radius: inherit;
}
.xt-page.xt-s31 .wk-fb-lg { font-size: 42px; }

/* ===== 从 flower 合并：顶部成长足迹入口 ===== */
.xt-page.xt-s31 .wk-actions {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}
.xt-page.xt-s31 .wk-archive {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.92);
}
.xt-page.xt-s31 .wk-archive .ic {
  width: 13px;
  height: 13px;
}

/* ===== 旅程站点 ===== */
.xt-page.xt-s31 .wk-route {
  margin-top: 12px;
  padding: 13px 13px 12px;
  border-radius: 18px;
  background: #FFFDFA;
  box-shadow: 0 14px 30px -28px rgba(34, 48, 42, 0.6), inset 0 0 0 1px rgba(30, 42, 36, 0.08);
}
.xt-page.xt-s31 .wk-rhead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.xt-page.xt-s31 .wk-rhead b {
  font-size: 10px;
  font-weight: 900;
  color: #3A463F;
}
.xt-page.xt-s31 .wk-rhead b i {
  font-style: normal;
  color: #A9763F;
}
.xt-page.xt-s31 .wk-rhead span {
  font-size: 7.5px;
  color: #AEB6AE;
}
.xt-page.xt-s31 .wk-stops {
  display: flex;
  justify-content: space-between;
  margin-top: 11px;
}
.xt-page.xt-s31 .wk-stop {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.xt-page.xt-s31 .wk-stop b {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  font-weight: 900;
  color: #B4BDB5;
  background: #F1F2EA;
  box-shadow: inset 0 0 0 1px rgba(34, 48, 42, 0.06);
}
.xt-page.xt-s31 .wk-stop span {
  font-size: 6.5px;
  color: #B4BDB5;
  white-space: nowrap;
}
.xt-page.xt-s31 .wk-stop.done b {
  color: #FFFDFA;
  background: linear-gradient(135deg, #44705A, #24493A);
}
.xt-page.xt-s31 .wk-stop.done span { color: #6A776E; }
.xt-page.xt-s31 .wk-stop.now b {
  color: #3A463F;
  background: #EFE3CF;
  box-shadow: 0 0 0 2px rgba(178, 121, 63, 0.26);
}
.xt-page.xt-s31 .wk-stop.now span {
  color: #A9763F;
  font-weight: 800;
}

/* ===== 同行纪念（拍立得） ===== */
.xt-page.xt-s31 .wk-shot {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 8px;
  border-radius: 18px;
  background: #FFFDFA;
  box-shadow: 0 18px 34px -30px rgba(34, 48, 42, 0.7), inset 0 0 0 1px rgba(30, 42, 36, 0.08);
}
.xt-page.xt-s31 .wk-shot-ph {
  position: relative;
  width: 118px;
  height: 157px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
  background: #EFE9DE;
}
.xt-page.xt-s31 .wk-shot-badge {
  position: absolute;
  left: 6px;
  bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 6.2px;
  font-weight: 800;
  letter-spacing: 0.2px;
  color: #FFFDFA;
  background: rgba(20, 32, 26, 0.55);
}
.xt-page.xt-s31 .wk-shot-badge i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #E8C08C;
}
.xt-page.xt-s31 .wk-shot-cap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 4px;
}
.xt-page.xt-s31 .cap-l {
  display: block;
  margin-bottom: 7px;
  font-size: 6.5px;
  font-weight: 800;
  letter-spacing: 0.6px;
  color: #A9763F;
}
.xt-page.xt-s31 .cap-q {
  display: block;
  font-size: 9px;
  line-height: 1.75;
  color: #4B5A51;
}
.xt-page.xt-s31 .cap-n {
  display: block;
  margin-top: 7px;
  font-size: 7px;
  letter-spacing: 0.3px;
  color: #AEB6AE;
}

/* ===== 明信片入口 ===== */
.xt-page.xt-s31 .wk-post {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 11px 12px;
  border-radius: 16px;
  background: #FFFDFA;
  box-shadow: 0 14px 28px -30px rgba(34, 48, 42, 0.7), inset 0 0 0 1px rgba(30, 42, 36, 0.08);
}
.xt-page.xt-s31 .wk-post-ico {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #A9763F;
  background: #F1ECE2;
}
.xt-page.xt-s31 .wk-post-ico .ic { width: 14px; height: 14px; }
.xt-page.xt-s31 .wk-post-tx { flex: 1; min-width: 0; }
.xt-page.xt-s31 .wk-post-t {
  font-size: 10px;
  font-weight: 900;
  color: #3A463F;
}
.xt-page.xt-s31 .wk-post-d {
  margin-top: 2px;
  font-size: 7.5px;
  color: #AEB6AE;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.xt-page.xt-s31 .wk-post-ar {
  flex-shrink: 0;
  color: #CFD6CE;
}
.xt-page.xt-s31 .wk-post-ar .ic { width: 12px; height: 12px; }
/* 自定义导航栏后，返回按钮与标题同排，避免与原生标题栏重复 */
.xt-page.xt-s31 .wk-head-l {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 1;
  min-width: 0;
}
.xt-page.xt-s31 .wk-back {
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.92);
  flex-shrink: 0;
}
.xt-page.xt-s31 .wk-back .ic {
  width: 14px;
  height: 14px;
}

/* 顶部地点风景：纸感相框包住紧凑地图 */
.v7-map-frame {
  margin: 4px 0 12px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--v7-line, rgba(30, 42, 36, 0.1));
  background: var(--v7-card, #FFFDFA);
  box-shadow: 0 6px 18px rgba(34, 48, 42, 0.06);
}

/* 给鲜艳的场景蒙一层薄纸色，和 V7 纸感统一 */
.v7-map-frame :deep(.map-scene)::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(248, 244, 236, 0.14);
  pointer-events: none;
  z-index: 30;
}
</style>
