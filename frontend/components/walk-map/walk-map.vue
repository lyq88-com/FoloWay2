<template>
  <view class="walk-map-container" :class="{ compact: compact }" @click="onMapTap">
    <!-- 地图场景 -->
    <view class="map-scene" :style="sceneStyle">
      <!-- 天空层 -->
      <view class="sky-layer" :style="skyStyle">
        <!-- 太阳/月亮 -->
        <view v-if="showCelestial" class="celestial-body" :class="celestialType" :style="celestialStyle">
          <view class="celestial-glow"></view>
          <view class="celestial-core"></view>
        </view>
        <!-- 云朵 - CSS形状 -->
        <view v-if="currentStage.scene.clouds > 0" class="cloud-layer">
          <view
            v-for="n in currentStage.scene.clouds"
            :key="'cloud-' + n"
            class="cloud"
            :class="'cloud-' + n"
            :style="cloudStyle(n)"
          >
            <view class="cloud-body cloud-part-1"></view>
            <view class="cloud-body cloud-part-2"></view>
            <view class="cloud-body cloud-part-3"></view>
          </view>
        </view>
        <!-- 星星 -->
        <view v-if="currentStage.scene.stars" class="star-layer">
          <view
            v-for="n in 15"
            :key="'star-' + n"
            class="star"
            :style="starStyle(n)"
          >✦</view>
        </view>
        <!-- 极光 -->
        <view v-if="currentStage.scene.aurora" class="aurora-layer">
          <view class="aurora-band aurora-1"></view>
          <view class="aurora-band aurora-2"></view>
          <view class="aurora-band aurora-3"></view>
        </view>
        <!-- 萤火虫 -->
        <view v-if="currentStage.scene.fireflies" class="firefly-layer">
          <view
            v-for="n in 8"
            :key="'firefly-' + n"
            class="firefly"
            :style="fireflyStyle(n)"
          ></view>
        </view>
      </view>

      <!-- 山脉层 -->
      <view v-if="currentStage.scene.mountains > 0" class="mountain-layer">
        <view
          v-for="n in currentStage.scene.mountains"
          :key="'mountain-' + n"
          class="mountain"
          :class="'mountain-' + n"
          :style="mountainStyle(n)"
        ></view>
        <!-- 雪山顶 -->
        <view v-if="currentStage.scene.snow" class="snow-cap-layer">
          <view
            v-for="n in currentStage.scene.mountains"
            :key="'snowcap-' + n"
            class="snow-cap"
            :style="snowCapStyle(n)"
          ></view>
        </view>
      </view>

      <!-- 地面层 -->
      <view class="ground-layer" :style="groundStyle">
        <!-- 地面渐变叠加 -->
        <view class="ground-overlay" :style="groundOverlayStyle"></view>
        <!-- 树木 -->
        <view v-if="currentStage.scene.trees > 0" class="tree-layer">
          <view
            v-for="n in currentStage.scene.trees"
            :key="'tree-' + n"
            class="tree"
            :style="treeStyle(n)"
          >
            <text class="tree-emoji">{{ treeEmoji }}</text>
          </view>
        </view>
        <!-- 花朵 -->
        <view v-if="currentStage.scene.flowers" class="flower-layer">
          <view
            v-for="n in 6"
            :key="'flower-' + n"
            class="flower"
            :style="flowerStyle(n)"
          >
            <text class="flower-emoji">{{ flowerEmoji }}</text>
          </view>
        </view>
        <!-- 水面波纹 -->
        <view v-if="currentStage.scene.water" class="water-layer">
          <view class="wave wave-1"></view>
          <view class="wave wave-2"></view>
          <view class="wave wave-3"></view>
          <view class="wave wave-4"></view>
        </view>
      </view>

      <!-- 路径层 -->
      <view class="path-layer">
        <!-- 路径线 - 虚线 -->
        <view class="path-line-bg" :style="{ borderColor: 'rgba(' + hexToRgb(currentStage.theme.pathColor) + ', 0.15)' }"></view>
        <view class="path-line" :style="{ backgroundImage: 'repeating-linear-gradient(90deg, ' + currentStage.theme.pathColor + ' 0, ' + currentStage.theme.pathColor + ' 16rpx, transparent 16rpx, transparent 32rpx)' }"></view>
        <!-- 路径节点 -->
        <view
          v-for="(node, idx) in currentStage.nodes"
          :key="'node-' + idx"
          class="path-node"
          :class="{ active: isNodeActive(idx), passed: isNodePassed(idx) }"
          :style="nodeStyle(idx)"
        >
          <view class="node-pulse" v-if="isNodeActive(idx)" :style="{ borderColor: currentStage.theme.accent }"></view>
          <view class="node-circle" :style="nodeCircleStyle(idx)">
            <text class="node-icon">{{ node.icon }}</text>
          </view>
          <text class="node-label" :style="{ color: nodeLabelColor }">{{ node.label }}</text>
        </view>
      </view>

      <!-- AI角色 + 对话气泡 -->
      <view class="ai-walker" :style="walkerStyle">
        <!-- 火花轨迹 -->
        <view class="sparkle-trail">
          <view class="sparkle sparkle-1"></view>
          <view class="sparkle sparkle-2"></view>
          <view class="sparkle sparkle-3"></view>
        </view>
        <!-- 对话气泡 -->
        <view v-if="showDialogue" class="dialogue-bubble" :style="bubbleStyle" @click.stop="changeDialogue">
          <view class="bubble-tail" :style="{ borderTopColor: bubbleBgColor }"></view>
          <text class="dialogue-text">{{ dialogueText }}</text>
          <view class="bubble-dots">
            <view class="bubble-dot"></view>
            <view class="bubble-dot"></view>
            <view class="bubble-dot"></view>
          </view>
        </view>
        <!-- AI角色立绘头像（轻治愈潮流插画风，支持自定义角色） -->
        <view class="walker-avatar" :style="avatarBgStyle" @click.stop="goChat">
          <view class="avatar-ring"></view>
          <view class="walker-sprite-wrap">
            <CharacterHead :characterId="characterId" size="small" :disableBlink="false" />
          </view>
          <view class="walker-shadow"></view>
          <view class="chat-hint-dot">
            <text class="chat-hint-icon">💬</text>
          </view>
        </view>
        <!-- 角色名 -->
        <text v-if="!compact" class="walker-name" :style="{ color: currentStage.theme.accent }">{{ aiName }}</text>
      </view>
    </view>

    <!-- 关卡信息条 -->
    <view class="stage-info-bar" :style="infoBarStyle">
      <view class="stage-info-left">
        <view class="stage-icon-wrap" :style="stageIconBgStyle">
          <text class="stage-icon-big">{{ currentStage.icon }}</text>
        </view>
        <view class="stage-info-text">
          <text class="stage-name-text">{{ currentStage.name }}</text>
          <text class="stage-sub-text">{{ currentStage.subtitle }}</text>
        </view>
      </view>
      <view class="stage-info-right">
        <text class="checkpoint-text" :style="{ color: currentStage.theme.accent }">{{ totalCheckins }}<text class="checkpoint-sep">/</text><text class="checkpoint-max">{{ stageMaxLabel }}</text></text>
        <text class="checkpoint-label">累计打卡</text>
      </view>
    </view>

    <!-- 关卡进度条 -->
    <view class="progress-bar-wrap" :style="progressWrapStyle">
      <view class="progress-bar-track" :style="progressTrackStyle">
        <view class="progress-bar-fill" :style="progressFillStyle"></view>
        <view class="progress-shimmer" v-if="stageProgress > 0 && stageProgress < 100"></view>
      </view>
      <view class="progress-percent-wrap">
        <text class="progress-percent" :style="{ color: currentStage.theme.accent }">{{ stageProgress }}%</text>
      </view>
    </view>

    <!-- 关卡导航点 -->
    <view class="stage-nav-dots" :style="navDotsStyle">
      <view
        v-for="stage in allStages"
        :key="'stage-dot-' + stage.id"
        class="stage-dot"
        :class="{
          current: stage.id === currentStage.id,
          unlocked: stage.id <= currentStage.id,
          locked: stage.id > currentStage.id
        }"
      >
        <view class="stage-dot-circle" :style="stageDotCircleStyle(stage)">
          <text class="stage-dot-icon">{{ stage.icon }}</text>
        </view>
        <text class="stage-dot-label" v-if="!compact">{{ stage.name }}</text>
      </view>
    </view>

    <!-- 底部入口 -->
    <view v-if="!compact" class="map-footer-entry" :style="footerStyle" @click.stop="goGrowthTrack">
      <text class="footer-entry-text">查看成长足迹</text>
      <text class="footer-entry-arrow">›</text>
    </view>

    <!-- 通关徽章 -->
    <view v-if="unlockedEnding" class="ending-badge">
      <text class="ending-icon">🏆</text>
      <text class="ending-text">全程通关</text>
    </view>

    <!-- 地图 AI 互动弹窗 -->
    <ai-interaction-modal
      :visible="showMapAIModal"
      type="success"
      :characterId="characterId"
      :message="mapAIModalMessage"
      :loading="mapAIModalLoading"
      :stats="{ stageName: currentStage?.name, totalCheckins }"
      @close="closeMapAIModal"
      @chat="goChat"
      @primary="closeMapAIModal"
    />
  </view>
</template>

<script>
import { MAP_STAGES, getRandomLocationDialogue, getEndingQuote } from '@/common/walk-map-config.js'
import { getCharacterById } from '@/common/ai-characters'
import CharacterHead from '@/components/character-sprite/character-head.vue'
import AIInteractionModal from '@/components/ai-interaction-modal/ai-interaction-modal.vue'
import aiService from '@/common/ai-service.js'

export default {
  name: 'WalkMap',
  components: { CharacterHead, AIInteractionModal },
  props: {
    compact: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      dialogueIndex: 0,
      showDialogue: true,
      allStages: MAP_STAGES,
      // AI地图联动
      showMapAIModal: false,
      mapAIModalMessage: '',
      mapAIModalLoading: false,
      lastStageId: null
    }
  },
  watch: {
    // 监听关卡变化，触发AI互动
    currentStage: {
      handler(newStage, oldStage) {
        if (newStage && newStage.id !== this.lastStageId && this.lastStageId !== null) {
          this.triggerMapAIInteraction(newStage)
        }
        this.lastStageId = newStage?.id
      },
      immediate: false
    }
  },
  computed: {
    totalCheckins() {
      return this.$store.getters.totalCheckins
    },
    currentStage() {
      return this.$store.getters.currentStage
    },
    stageProgress() {
      return this.$store.getters.stageProgress
    },
    unlockedEnding() {
      return this.$store.getters.unlockedEnding
    },
    stageMaxLabel() {
      const next = this.currentStage.nextThreshold
      if (next === Infinity) return '∞'
      return next
    },
    characterId() {
      return this.$store.state.aiConfig.avatarType || 'linxi'
    },
    aiCharacter() {
      return getCharacterById(this.characterId) || getCharacterById('linxi')
    },
    aiAvatar() {
      return this.aiCharacter.avatar || '🌿'
    },
    aiName() {
      return this.$store.state.aiConfig.name || this.aiCharacter.name || 'AI伙伴'
    },
    dialogueText() {
      if (this.unlockedEnding) {
        const ending = getEndingQuote(this.characterId)
        if (ending) return ending
      }
      const dialogues = getRandomLocationDialogue(this.characterId, this.currentStage.id)
      return dialogues
    },
    showCelestial() {
      // 所有场景都显示太阳或月亮
      return true
    },
    celestialType() {
      // 雪山和星空场景用月亮，其他用太阳
      if (this.currentStage.id === 3) return 'moon'
      if (this.currentStage.id === 4) return 'moon'
      return 'sun'
    },
    celestialStyle() {
      const positions = [
        { top: '10%', right: '15%' },
        { top: '8%', right: '20%' },
        { top: '12%', right: '10%' },
        { top: '15%', right: '18%' },
        { top: '8%', right: '25%' },
        { top: '12%', right: '15%' }
      ]
      const pos = positions[this.currentStage.id] || positions[0]
      return {
        top: pos.top,
        right: pos.right
      }
    },
    sceneStyle() {
      return {
        borderRadius: this.compact ? '24rpx 24rpx 0 0' : '32rpx 32rpx 0 0'
      }
    },
    skyStyle() {
      return {
        background: `linear-gradient(180deg, ${this.currentStage.theme.skyTop} 0%, ${this.currentStage.theme.skyBottom} 100%)`
      }
    },
    groundStyle() {
      return {
        background: `linear-gradient(180deg, ${this.currentStage.theme.groundTop} 0%, ${this.currentStage.theme.groundBottom} 100%)`
      }
    },
    groundOverlayStyle() {
      // 地面纹理叠加
      return {
        background: `radial-gradient(ellipse at 50% 100%, rgba(255,255,255,0.15) 0%, transparent 60%)`
      }
    },
    walkerStyle() {
      const progress = this.stageProgress
      const left = 5 + (progress / 100) * 87
      return {
        left: left + '%'
      }
    },
    bubbleStyle() {
      return {
        background: 'rgba(255, 255, 255, 0.96)',
        borderColor: 'rgba(' + this.hexToRgb(this.currentStage.theme.accent) + ', 0.3)'
      }
    },
    bubbleBgColor() {
      return 'rgba(255, 255, 255, 0.96)'
    },
    avatarBgStyle() {
      const colors = this.aiCharacter.colors
      if (colors) {
        return {
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
          boxShadow: '0 8rpx 24rpx ' + (colors.glow || 'rgba(0,0,0,0.2)')
        }
      }
      return {}
    },
    nodeLabelColor() {
      const stageId = this.currentStage.id
      if (stageId === 3 || stageId === 4) return 'rgba(255,255,255,0.9)'
      return 'rgba(0,0,0,0.55)'
    },
    treeEmoji() {
      const trees = ['🌲', '🌳', '🌴', '🎄']
      return trees[this.currentStage.id % trees.length]
    },
    flowerEmoji() {
      const flowers = ['🌼', '🌸', '🌺', '🌷']
      return flowers[this.currentStage.id % flowers.length]
    },
    infoBarStyle() {
      return {
        background: `linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(248,251,249,0.98) 100%)`
      }
    },
    progressWrapStyle() {
      return {
        background: `linear-gradient(135deg, rgba(248,251,249,0.98) 0%, rgba(255,255,255,0.98) 100%)`
      }
    },
    progressTrackStyle() {
      return {
        background: 'rgba(' + this.hexToRgb(this.currentStage.theme.pathColor) + ', 0.15)'
      }
    },
    progressFillStyle() {
      return {
        width: this.stageProgress + '%',
        background: `linear-gradient(90deg, ${this.currentStage.theme.pathColor} 0%, ${this.currentStage.theme.accent} 100%)`
      }
    },
    stageIconBgStyle() {
      return {
        background: `linear-gradient(135deg, ${this.currentStage.theme.skyTop} 0%, ${this.currentStage.theme.skyBottom} 100%)`,
        boxShadow: `0 4rpx 16rpx rgba(0,0,0,0.12)`
      }
    },
    navDotsStyle() {
      return {
        background: 'rgba(255,255,255,0.98)'
      }
    },
    footerStyle() {
      return {
        background: `linear-gradient(135deg, rgba(${this.hexToRgb(this.currentStage.theme.accent)}, 0.08) 0%, rgba(${this.hexToRgb(this.currentStage.theme.pathColor)}, 0.05) 100%)`
      }
    },
    stageDotCircleStyle() {
      return (stage) => {
        if (stage.id <= this.currentStage.id) {
          return {
            background: `linear-gradient(135deg, ${stage.theme.skyTop} 0%, ${stage.theme.accent} 100%)`,
            boxShadow: '0 4rpx 12rpx rgba(0,0,0,0.1)'
          }
        }
        return {
          background: 'rgba(0,0,0,0.06)'
        }
      }
    },
    nodeCircleStyle() {
      return (idx) => {
        const isPassed = this.isNodePassed(idx)
        const isActive = this.isNodeActive(idx)
        if (isActive) {
          return {
            background: `linear-gradient(135deg, ${this.currentStage.theme.accent} 0%, ${this.currentStage.theme.pathColor} 100%)`,
            borderColor: 'rgba(255,255,255,0.8)',
            boxShadow: `0 0 20rpx rgba(${this.hexToRgb(this.currentStage.theme.accent)}, 0.6)`
          }
        }
        if (isPassed) {
          return {
            background: `linear-gradient(135deg, ${this.currentStage.theme.accent} 0%, ${this.currentStage.theme.accent} 100%)`,
            borderColor: 'rgba(255,255,255,0.6)'
          }
        }
        return {
          background: 'rgba(255,255,255,0.5)',
          borderColor: 'rgba(255,255,255,0.3)'
        }
      }
    }
  },
  watch: {
    'currentStage.id'() {
      this.dialogueIndex = 0
      this.showDialogue = true
    }
  },
  methods: {
    // AI 地图联动方法
    async triggerMapAIInteraction(stage) {
      if (!stage) return
      
      this.mapAIModalLoading = true
      this.showMapAIModal = true
      
      try {
        const response = await aiService.onMapStageUnlock(
          stage.name,
          stage.id
        )
        this.mapAIModalMessage = response || `恭喜抵达${stage.name}！`
      } catch (e) {
        console.error('地图AI互动失败:', e)
        this.mapAIModalMessage = `新的一站：${stage.name}，一起继续前行~`
      } finally {
        this.mapAIModalLoading = false
      }
    },
    closeMapAIModal() {
      this.showMapAIModal = false
      this.mapAIModalMessage = ''
    },
    async triggerCheckinAI() {
      // 打卡触发地图AI
      try {
        const response = await aiService.onCheckinSuccess({
          name: '当前习惯',
          type: 'habit'
        })
        // 更新对话气泡内容
        this.dialogueText = response
      } catch (e) {
        console.error('打卡地图AI失败:', e)
      }
    },
    onMapTap() {
      if (this.compact) {
        this.goGrowthTrack()
      }
    },
    goChat() {
      // 点击AI伙伴直接唤起聊天窗口
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    goGrowthTrack() {
      uni.navigateTo({
        url: '/pages/growth-track/growth-track'
      })
    },
    changeDialogue() {
      this.dialogueIndex++
      this.showDialogue = !this.showDialogue
      this.$nextTick(() => {
        this.showDialogue = true
      })
    },
    isNodeActive(idx) {
      const node = this.currentStage.nodes[idx]
      if (!node) return false
      const total = this.totalCheckins
      const nextNode = this.currentStage.nodes[idx + 1]
      if (!nextNode) return total >= node.atStep
      return total >= node.atStep && total < nextNode.atStep
    },
    isNodePassed(idx) {
      const node = this.currentStage.nodes[idx]
      if (!node) return false
      return this.totalCheckins >= node.atStep
    },
    nodeStyle(idx) {
      const total = this.currentStage.nodes.length
      const percent = (idx / (total - 1)) * 100
      return {
        left: percent + '%'
      }
    },
    cloudStyle(n) {
      const positions = [
        { top: '8%', left: '12%', scale: 1 },
        { top: '14%', left: '58%', scale: 0.75 },
        { top: '5%', left: '82%', scale: 0.6 }
      ]
      const pos = positions[(n - 1) % positions.length]
      return {
        top: pos.top,
        left: pos.left,
        transform: `scale(${pos.scale})`
      }
    },
    starStyle(n) {
      const seed = (n * 37) % 100
      const top = (seed % 40) + 2
      const left = (seed * 7) % 95 + 2
      const delay = (n % 6) * 0.5
      const size = (n % 3) + 1
      return {
        top: top + '%',
        left: left + '%',
        fontSize: (12 + size * 4) + 'rpx',
        animationDelay: delay + 's'
      }
    },
    fireflyStyle(n) {
      const seed = (n * 53) % 100
      const top = 20 + (seed % 50)
      const left = 5 + (seed * 3) % 90
      const delay = (n * 0.7) % 4
      return {
        top: top + '%',
        left: left + '%',
        animationDelay: delay + 's'
      }
    },
    mountainStyle(n) {
      const positions = [
        { left: '0%', width: '40%', height: '60%', opacity: 0.5 },
        { left: '25%', width: '50%', height: '85%', opacity: 0.75 },
        { left: '55%', width: '45%', height: '55%', opacity: 0.4 }
      ]
      const pos = positions[(n - 1) % positions.length]
      return {
        left: pos.left,
        width: pos.width,
        height: pos.height,
        opacity: pos.opacity,
        background: this.currentStage.theme.groundBottom
      }
    },
    snowCapStyle(n) {
      const positions = [
        { left: '0%', width: '40%' },
        { left: '25%', width: '50%' },
        { left: '55%', width: '45%' }
      ]
      const pos = positions[(n - 1) % positions.length]
      return {
        left: pos.left,
        width: pos.width
      }
    },
    treeStyle(n) {
      const positions = [
        { bottom: '5%', left: '8%', scale: 0.7 },
        { bottom: '3%', left: '30%', scale: 0.9 },
        { bottom: '8%', left: '55%', scale: 0.6 },
        { bottom: '2%', left: '75%', scale: 0.8 },
        { bottom: '6%', left: '90%', scale: 0.5 }
      ]
      const pos = positions[(n - 1) % positions.length]
      return {
        bottom: pos.bottom,
        left: pos.left,
        transform: `scale(${pos.scale})`
      }
    },
    flowerStyle(n) {
      const seed = (n * 29) % 100
      const bottom = 2 + (seed % 8)
      const left = 8 + (n - 1) * 15 + (seed % 5)
      return {
        bottom: bottom + '%',
        left: left + '%',
        transform: `scale(${0.7 + (seed % 4) * 0.15})`
      }
    },
    hexToRgb(hex) {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      if (!result) return '0,0,0'
      return `${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)}`
    }
  }
}
</script>

<style lang="scss" scoped>
.walk-map-container {
  position: relative;
  border-radius: 32rpx;
  overflow: hidden;
  box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.1);

  &.compact {
    border-radius: 24rpx;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.08);
  }
}

/* === 场景区域 === */
.map-scene {
  position: relative;
  width: 100%;
  height: 540rpx;
  overflow: hidden;

  .compact & {
    height: 400rpx;
  }
}

/* === 天空层 === */
.sky-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 42%;
  overflow: hidden;
}

/* === 太阳/月亮 === */
.celestial-body {
  position: absolute;
  width: 80rpx;
  height: 80rpx;
  z-index: 5;
}

.celestial-glow {
  position: absolute;
  top: -20rpx;
  left: -20rpx;
  right: -20rpx;
  bottom: -20rpx;
  border-radius: 50%;
}

.sun .celestial-glow {
  background: radial-gradient(circle, rgba(255, 230, 0, 0.3) 0%, transparent 70%);
  animation: sun-pulse 4s ease-in-out infinite;
}

.moon .celestial-glow {
  background: radial-gradient(circle, rgba(200, 220, 255, 0.25) 0%, transparent 70%);
  animation: moon-pulse 6s ease-in-out infinite;
}

.celestial-core {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
}

.sun .celestial-core {
  background: radial-gradient(circle at 35% 35%, #FFF9C4 0%, #FFD54F 50%, #FFB300 100%);
  box-shadow: 0 0 40rpx rgba(255, 200, 0, 0.5);
}

.moon .celestial-core {
  background: radial-gradient(circle at 35% 35%, #F5F5F5 0%, #E0E0E0 60%, #BDBDBD 100%);
  box-shadow: 0 0 30rpx rgba(200, 220, 255, 0.4);
}

@keyframes sun-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

@keyframes moon-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
}

/* === 云朵 - CSS形状 === */
.cloud-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.cloud {
  position: absolute;
  width: 100rpx;
  height: 40rpx;
}

.cloud-body {
  position: absolute;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 50%;
  filter: blur(3rpx);
}

.cloud-part-1 {
  width: 60rpx;
  height: 60rpx;
  top: -10rpx;
  left: 0;
}

.cloud-part-2 {
  width: 80rpx;
  height: 80rpx;
  top: -25rpx;
  left: 25rpx;
}

.cloud-part-3 {
  width: 50rpx;
  height: 50rpx;
  top: -5rpx;
  left: 60rpx;
}

.cloud-1 {
  animation: cloud-drift-1 25s ease-in-out infinite;
}
.cloud-2 {
  animation: cloud-drift-2 30s ease-in-out infinite;
}
.cloud-3 {
  animation: cloud-drift-1 35s ease-in-out infinite;
}

@keyframes cloud-drift-1 {
  0%, 100% { transform: translateX(0) scale(var(--s, 1)); }
  50% { transform: translateX(30rpx) scale(var(--s, 1)); }
}

@keyframes cloud-drift-2 {
  0%, 100% { transform: translateX(0) scale(var(--s, 1)); }
  50% { transform: translateX(-20rpx) scale(var(--s, 1)); }
}

/* === 星星层 === */
.star-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.star {
  position: absolute;
  color: #FFD93D;
  text-shadow: 0 0 8rpx rgba(255, 217, 61, 0.6);
  animation: twinkle 2s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* === 极光层 === */
.aurora-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.aurora-band {
  position: absolute;
  width: 200%;
  height: 120rpx;
  border-radius: 50%;
  filter: blur(24rpx);
  opacity: 0.35;
}

.aurora-1 {
  top: 8%;
  left: -50%;
  background: linear-gradient(90deg, #00F5D4, #9B5DE5, #00BBF9);
  animation: aurora-flow 8s ease-in-out infinite;
}

.aurora-2 {
  top: 22%;
  left: -30%;
  background: linear-gradient(90deg, #F15BB5, #00F5D4, #9B5DE5);
  animation: aurora-flow 12s ease-in-out infinite reverse;
}

.aurora-3 {
  top: 35%;
  left: -40%;
  background: linear-gradient(90deg, #00BBF9, #F15BB5, #00F5D4);
  animation: aurora-flow 10s ease-in-out infinite;
  animation-delay: -3s;
}

@keyframes aurora-flow {
  0%, 100% { transform: translateX(0) translateY(0); }
  33% { transform: translateX(80rpx) translateY(-10rpx); }
  66% { transform: translateX(-40rpx) translateY(10rpx); }
}

/* === 萤火虫 === */
.firefly-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.firefly {
  position: absolute;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #FFEB3B;
  box-shadow: 0 0 12rpx rgba(255, 235, 59, 0.8);
  animation: firefly-float 5s ease-in-out infinite;
}

@keyframes firefly-float {
  0%, 100% { opacity: 0; transform: translate(0, 0) scale(0.5); }
  25% { opacity: 1; transform: translate(20rpx, -15rpx) scale(1); }
  50% { opacity: 0.6; transform: translate(40rpx, 5rpx) scale(0.8); }
  75% { opacity: 1; transform: translate(20rpx, -10rpx) scale(1.1); }
}

/* === 山脉层 === */
.mountain-layer {
  position: absolute;
  bottom: 38%;
  left: 0;
  right: 0;
  height: 42%;
}

.mountain {
  position: absolute;
  bottom: 0;
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  border-radius: 8rpx;
}

.snow-cap-layer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100%;
}

.snow-cap {
  position: absolute;
  bottom: 0;
  height: 35%;
  background: linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.3) 100%);
  clip-path: polygon(50% 0%, 30% 100%, 70% 100%);
  opacity: 0.7;
}

/* === 地面层 === */
.ground-layer {
  position: absolute;
  top: 58%;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.ground-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.tree-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.tree {
  position: absolute;
}

.tree-emoji {
  font-size: 56rpx;
  display: block;
  filter: drop-shadow(0 4rpx 8rpx rgba(0,0,0,0.1));
}

.flower-layer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30%;
}

.flower {
  position: absolute;
}

.flower-emoji {
  font-size: 32rpx;
  display: block;
  filter: drop-shadow(0 2rpx 4rpx rgba(0,0,0,0.08));
}

/* === 水面 === */
.water-layer {
  position: absolute;
  top: 25%;
  left: 0;
  right: 0;
  bottom: 0;
}

.wave {
  position: absolute;
  left: -50%;
  right: -50%;
  height: 4rpx;
  border-radius: 50%;
  opacity: 0.3;
  animation: wave-flow 4s ease-in-out infinite;
}

.wave-1 { top: 20%; background: rgba(255, 255, 255, 0.6); animation-delay: 0s; }
.wave-2 { top: 45%; background: rgba(255, 255, 255, 0.4); animation-delay: 1s; }
.wave-3 { top: 65%; background: rgba(255, 255, 255, 0.3); animation-delay: 2s; }
.wave-4 { top: 85%; background: rgba(255, 255, 255, 0.2); animation-delay: 3s; }

@keyframes wave-flow {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(60rpx); }
}

/* === 路径层 === */
.path-layer {
  position: absolute;
  top: 46%;
  left: 0;
  right: 0;
  height: 130rpx;
}

.path-line-bg {
  position: absolute;
  top: 50%;
  left: 5%;
  right: 5%;
  height: 16rpx;
  border-radius: 8rpx;
  border: 2rpx solid;
  transform: translateY(-50%);
  opacity: 0.5;
}

.path-line {
  position: absolute;
  top: 50%;
  left: 5%;
  right: 5%;
  height: 6rpx;
  border-radius: 3rpx;
  opacity: 0.6;
  transform: translateY(-50%);
}

.path-node {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.node-pulse {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  border: 3rpx solid;
  animation: node-pulse-ring 2s ease-out infinite;
}

@keyframes node-pulse-ring {
  0% { width: 56rpx; height: 56rpx; opacity: 1; }
  100% { width: 120rpx; height: 120rpx; opacity: 0; }
}

.node-circle {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.path-node.active .node-circle {
  width: 72rpx;
  height: 72rpx;
  border-color: rgba(255, 255, 255, 0.9);
}

.path-node.passed .node-circle {
  border-color: rgba(255, 255, 255, 0.5);
}

.node-icon {
  font-size: 28rpx;
}

.path-node.active .node-icon {
  font-size: 36rpx;
}

.node-label {
  font-size: 20rpx;
  margin-top: 8rpx;
  white-space: nowrap;
  opacity: 0.85;
  font-weight: 500;
}

/* === AI角色 === */
.ai-walker {
  position: absolute;
  top: 36%;
  transition: left 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateX(-50%);
}

.sparkle-trail {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60rpx;
  height: 40rpx;
}

.sparkle {
  position: absolute;
  width: 6rpx;
  height: 6rpx;
  border-radius: 50%;
  background: #FFD93D;
  box-shadow: 0 0 8rpx rgba(255, 217, 61, 0.8);
  animation: sparkle-rise 2s ease-in-out infinite;
}

.sparkle-1 { left: 10%; animation-delay: 0s; }
.sparkle-2 { left: 50%; animation-delay: 0.5s; }
.sparkle-3 { left: 80%; animation-delay: 1s; }

@keyframes sparkle-rise {
  0% { opacity: 0; transform: translateY(0) scale(0); }
  30% { opacity: 1; transform: translateY(-15rpx) scale(1); }
  100% { opacity: 0; transform: translateY(-35rpx) scale(0.3); }
}

.walker-avatar {
  width: 84rpx;
  height: 84rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: walker-bob 2.5s ease-in-out infinite;
}

.avatar-ring {
  position: absolute;
  top: -6rpx;
  left: -6rpx;
  right: -6rpx;
  bottom: -6rpx;
  border-radius: 50%;
  border: 3rpx solid rgba(255, 255, 255, 0.3);
  animation: ring-rotate 4s linear infinite;
}

@keyframes ring-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.walker-emoji {
  font-size: 46rpx;
  position: relative;
  z-index: 2;
}

/* 立绘头像容器（轻治愈潮流插画风） */
.walker-sprite-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.3);
}

/* 聊天提示点 */
.chat-hint-dot {
  position: absolute;
  top: -6rpx;
  right: -6rpx;
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3;
  animation: chat-hint-pulse 2s ease-in-out infinite;
}

.chat-hint-icon {
  font-size: 20rpx;
}

@keyframes chat-hint-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.85; }
}

.walker-shadow {
  position: absolute;
  bottom: -8rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 50rpx;
  height: 8rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.15);
  animation: shadow-pulse 2.5s ease-in-out infinite;
}

@keyframes walker-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-14rpx); }
}

@keyframes shadow-pulse {
  0%, 100% { width: 50rpx; opacity: 0.15; }
  50% { width: 38rpx; opacity: 0.28; }
}

.walker-name {
  font-size: 22rpx;
  margin-top: 8rpx;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
  white-space: nowrap;
  font-weight: 600;
}

/* === 对话气泡 === */
.dialogue-bubble {
  position: absolute;
  bottom: 105rpx;
  left: 50%;
  transform: translateX(-50%);
  max-width: 420rpx;
  min-width: 260rpx;
  padding: 22rpx 28rpx;
  border-radius: 24rpx;
  border: 2rpx solid;
  animation: bubble-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bubble-tail {
  position: absolute;
  bottom: -16rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 12rpx solid transparent;
  border-right: 12rpx solid transparent;
  border-top: 16rpx solid rgba(255, 255, 255, 0.96);
}

.dialogue-text {
  font-size: 24rpx;
  color: #333;
  line-height: 1.6;
  text-align: center;
  display: block;
}

.bubble-dots {
  display: flex;
  justify-content: center;
  gap: 6rpx;
  margin-top: 10rpx;
}

.bubble-dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.15);
  animation: dot-bounce 1.4s ease-in-out infinite;
}

.bubble-dot:nth-child(2) { animation-delay: 0.2s; }
.bubble-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 60%, 100% { transform: scale(1); opacity: 0.3; }
  30% { transform: scale(1.3); opacity: 1; }
}

@keyframes bubble-pop {
  0% { opacity: 0; transform: translateX(-50%) scale(0.5) translateY(20rpx); }
  100% { opacity: 1; transform: translateX(-50%) scale(1) translateY(0); }
}

/* === 关卡信息条 === */
.stage-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 28rpx 16rpx;
}

.stage-info-left {
  display: flex;
  align-items: center;
}

.stage-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 18rpx;
}

.stage-icon-big {
  font-size: 40rpx;
}

.stage-info-text {
  display: flex;
  flex-direction: column;
}

.stage-name-text {
  font-size: 32rpx;
  font-weight: 700;
  color: #2D4A3E;
  letter-spacing: -0.5rpx;
}

.stage-sub-text {
  font-size: 22rpx;
  color: #8A9B8E;
  margin-top: 4rpx;
}

.stage-info-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.checkpoint-text {
  font-size: 36rpx;
  font-weight: 700;
  display: flex;
  align-items: baseline;
}

.checkpoint-sep {
  font-size: 28rpx;
  opacity: 0.5;
  margin: 0 2rpx;
}

.checkpoint-max {
  font-size: 28rpx;
  opacity: 0.7;
}

.checkpoint-label {
  font-size: 20rpx;
  color: #aaa;
  margin-top: 2rpx;
}

/* === 进度条 === */
.progress-bar-wrap {
  display: flex;
  align-items: center;
  padding: 0 28rpx 18rpx;
  gap: 16rpx;
}

.progress-bar-track {
  flex: 1;
  height: 14rpx;
  border-radius: 7rpx;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 7rpx;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  z-index: 1;
}

.progress-shimmer {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 40rpx;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%);
  animation: shimmer-move 2s linear infinite;
  z-index: 2;
}

@keyframes shimmer-move {
  0% { left: -40rpx; }
  100% { left: 100%; }
}

.progress-percent-wrap {
  min-width: 70rpx;
  text-align: right;
}

.progress-percent {
  font-size: 26rpx;
  font-weight: 700;
}

/* === 关卡导航点 === */
.stage-nav-dots {
  display: flex;
  align-items: flex-start;
  justify-content: space-around;
  padding: 16rpx 16rpx 20rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.04);
}

.stage-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.35;
  transition: all 0.3s ease;
}

.stage-dot.unlocked {
  opacity: 0.65;
}

.stage-dot.current {
  opacity: 1;
  transform: scale(1.15);
}

.stage-dot-circle {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stage-dot-icon {
  font-size: 24rpx;
}

.stage-dot.current .stage-dot-circle {
  filter: drop-shadow(0 4rpx 8rpx rgba(0, 0, 0, 0.15));
}

.stage-dot-label {
  font-size: 18rpx;
  color: #999;
  margin-top: 6rpx;
  white-space: nowrap;
}

.stage-dot.current .stage-dot-label {
  color: #2D4A3E;
  font-weight: 600;
}

/* === 底部入口 === */
.map-footer-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.04);
}

.footer-entry-text {
  font-size: 26rpx;
  color: #6B8E7B;
  font-weight: 600;
}

.footer-entry-arrow {
  font-size: 32rpx;
  color: #6B8E7B;
  margin-left: 8rpx;
}

/* === 通关徽章 === */
.ending-badge {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  display: flex;
  align-items: center;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  box-shadow: 0 4rpx 12rpx rgba(255, 165, 0, 0.4);
  z-index: 20;
  animation: badge-glow 2s ease-in-out infinite;
}

.ending-icon {
  font-size: 28rpx;
  margin-right: 6rpx;
}

.ending-text {
  font-size: 22rpx;
  font-weight: 700;
  color: #fff;
}

@keyframes badge-glow {
  0%, 100% { box-shadow: 0 4rpx 12rpx rgba(255, 165, 0, 0.4); }
  50% { box-shadow: 0 4rpx 24rpx rgba(255, 165, 0, 0.7); }
}
</style>
