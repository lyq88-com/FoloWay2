<template>
  <view
    class="character-sprite"
    :class="[animationClass, sizeClass, { 'is-blinking': isBlinking }]"
    :style="containerStyle"
  >
    <!-- 头像模式 -->
    <view v-if="mode === 'head'" class="sprite-head" v-html="headSVG" />
    <!-- 全身模式 -->
    <view v-else class="sprite-fullbody" v-html="fullBodySVG" />
    <!-- 走路影子 -->
    <view v-if="mode === 'fullbody' && showShadow" class="sprite-shadow" />
  </view>
</template>

<script>
import {
  getSpriteData,
  renderHeadSVG,
  renderFullBodySVG,
  renderBlinkSVG
} from '@/common/character-sprites.js'

export default {
  name: 'CharacterSprite',
  props: {
    // 角色ID
    characterId: { type: String, default: 'linxi' },
    // 渲染模式: 'head' | 'fullbody'
    mode: { type: String, default: 'head' },
    // 尺寸：'xs' | 'small' | 'medium' | 'large' | 'xlarge'
    size: { type: String, default: 'medium' },
    // 自定义宽度
    width: { type: Number, default: 0 },
    // 自定义高度
    height: { type: Number, default: 0 },
    // 动画类型
    animation: { type: String, default: 'float' },
    // 是否显示影子
    showShadow: { type: Boolean, default: false },
    // 是否显示光晕
    showGlow: { type: Boolean, default: true },
    // 眨眼间隔(ms)
    blinkInterval: { type: Number, default: 3000 },
    // 禁用眨眼
    disableBlink: { type: Boolean, default: false }
  },
  data() {
    return {
      isBlinking: false,
      blinkTimer: null,
      floatTimer: null,
      floatValue: 0
    }
  },
  computed: {
    spriteData() {
      return getSpriteData(this.characterId)
    },
    sizeMap() {
      return {
        xs: { head: 36, fullbody: { w: 64, h: 80 } },
        small: { head: 48, fullbody: { w: 80, h: 100 } },
        medium: { head: 64, fullbody: { w: 120, h: 150 } },
        large: { head: 90, fullbody: { w: 160, h: 200 } },
        xlarge: { head: 140, fullbody: { w: 240, h: 300 } }
      }
    },
    headSVG() {
      const s = this.sizeMap[this.size] || this.sizeMap.medium
      const actualSize = this.width || s.head
      if (this.isBlinking) {
        return renderBlinkSVG(this.spriteData, actualSize)
      }
      return renderHeadSVG(this.spriteData, { size: actualSize })
    },
    fullBodySVG() {
      const s = this.sizeMap[this.size] || this.sizeMap.medium
      const w = this.width || s.fullbody.w
      const h = this.height || s.fullbody.h
      return renderFullBodySVG(this.spriteData, {
        width: w,
        height: h,
        showGlow: this.showGlow
      })
    },
    animationClass() {
      return `anim-${this.animation || 'float'}`
    },
    sizeClass() {
      return `size-${this.size}`
    },
    containerStyle() {
      const style = {}
      if (this.mode === 'fullbody') {
        const s = this.sizeMap[this.size] || this.sizeMap.medium
        style.width = `${this.width || s.fullbody.w}px`
        style.height = `${this.height || s.fullbody.h}px`
      }
      return style
    }
  },
  mounted() {
    if (!this.disableBlink) {
      this.startBlinkAnimation()
    }
  },
  beforeDestroy() {
    this.stopBlinkAnimation()
  },
  methods: {
    startBlinkAnimation() {
      this.blinkTimer = setInterval(() => {
        this.isBlinking = true
        setTimeout(() => {
          this.isBlinking = false
        }, 180)
      }, this.blinkInterval)
    },
    stopBlinkAnimation() {
      if (this.blinkTimer) {
        clearInterval(this.blinkTimer)
        this.blinkTimer = null
      }
    }
  }
}
</script>

<style scoped>
.character-sprite {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.sprite-head,
.sprite-fullbody {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sprite-shadow {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 6px;
  background: radial-gradient(ellipse, rgba(0,0,0,0.15) 0%, transparent 70%);
  border-radius: 50%;
}

/* ====== 尺寸 ====== */
.size-xs .sprite-head { width: 36px; height: 36px; }
.size-small .sprite-head { width: 48px; height: 48px; }
.size-medium .sprite-head { width: 64px; height: 64px; }
.size-large .sprite-head { width: 90px; height: 90px; }
.size-xlarge .sprite-head { width: 140px; height: 140px; }

/* ====== 浮动动画 ====== */
.anim-float {
  animation: spriteFloat 3s ease-in-out infinite;
}

@keyframes spriteFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* ====== 弹跳动画 ====== */
.anim-bounce {
  animation: spriteBounce 0.6s ease;
}

@keyframes spriteBounce {
  0%, 100% { transform: translateY(0); }
  30% { transform: translateY(-12px); }
  50% { transform: translateY(0); }
  70% { transform: translateY(-6px); }
}

/* ====== 摆动动画 ====== */
.anim-sway {
  animation: spriteSway 4s ease-in-out infinite;
}

@keyframes spriteSway {
  0%, 100% { transform: rotate(0deg) translateY(0); }
  25% { transform: rotate(1.5deg) translateY(-2px); }
  75% { transform: rotate(-1.5deg) translateY(-2px); }
}

/* ====== 脉冲动画 ====== */
.anim-pulse {
  animation: spritePulse 1.5s ease-in-out infinite;
}

@keyframes spritePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}

/* ====== 行走动画 ====== */
.anim-walk {
  animation: spriteWalk 0.8s ease-in-out infinite;
}

@keyframes spriteWalk {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  15% { transform: translateY(-4px) rotate(-1.5deg); }
  30% { transform: translateY(0) rotate(0deg); }
  45% { transform: translateY(-4px) rotate(1.5deg); }
  60% { transform: translateY(0) rotate(0deg); }
  75% { transform: translateY(-2px) rotate(-0.5deg); }
  90% { transform: translateY(0) rotate(0deg); }
}

/* ====== 无动画 ====== */
.anim-none {
  animation: none;
}

/* ====== 眨眼过渡 ====== */
.character-sprite.is-blinking .sprite-head {
  transition: none;
}
</style>
