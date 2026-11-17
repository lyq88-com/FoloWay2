<template>
  <view class="loading-skeleton">
    <view v-for="n in rows" :key="n" class="skeleton-row" :style="rowStyle(n)">
      <view class="skeleton-block shimmer" :style="blockStyle(n)"></view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'LoadingSkeleton',
  props: {
    rows: { type: Number, default: 3 },
    type: { type: String, default: 'card' }
  },
  methods: {
    rowStyle(n) {
      if (this.type === 'card') {
        return { marginBottom: '20rpx' }
      }
      return {}
    },
    blockStyle(n) {
      if (this.type === 'card') {
        return { height: '120rpx', borderRadius: '24rpx' }
      }
      if (this.type === 'text') {
        const widths = ['100%', '80%', '60%']
        return {
          height: '32rpx',
          width: widths[(n - 1) % 3],
          borderRadius: '8rpx',
          marginBottom: '16rpx'
        }
      }
      return {}
    }
  }
}
</script>

<style lang="scss" scoped>
.loading-skeleton {
  width: 100%;
}
.skeleton-row {
  width: 100%;
}
.skeleton-block {
  width: 100%;
  background: #EFEFEF;
}
.shimmer {
  background: linear-gradient(90deg, #EFEFEF 25%, #F5F5F5 50%, #EFEFEF 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
