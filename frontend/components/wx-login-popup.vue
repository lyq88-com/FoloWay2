<template>
  <view v-if="innerVisible" class="wx-mask" @click="onMaskClick">
    <view class="wx-dialog" @click.stop>
      <!-- 头部 -->
      <view class="wx-head">
        <text class="wx-title">微信扫码登录</text>
        <text class="wx-close" @click="close">×</text>
      </view>

      <!-- 二维码区 -->
      <view class="qr-box">
        <image v-if="qrImage" class="qr-img" :src="qrImage" mode="aspectFit" />
        <view v-else class="qr-empty">
          <view v-if="loading" class="qr-spin" />
          <text class="qr-empty-txt">{{ loading ? '二维码生成中…' : '点击重试' }}</text>
        </view>

        <view v-if="state === 'EXPIRED' || state === 'FAILED'" class="qr-cover" @click="refresh">
          <text class="qr-cover-title">{{ failTitle }}</text>
          <text class="qr-cover-sub">点击刷新二维码</text>
        </view>
      </view>

      <!-- 提示 -->
      <view class="wx-tip">
        <text class="wx-tip-main">{{ tip }}</text>
        <text class="wx-tip-sub">请使用微信扫描二维码，并在手机上点击「确认登录」</text>
      </view>

      <!-- 演示模式：真实环境不走这里 -->
      <view v-if="isDemo" class="demo-area">
        <view class="demo-badge"><text class="demo-badge-txt">演示模式</text></view>
        <button class="demo-btn" @click="onSimulateScan">模拟已扫码</button>
      </view>

      <!-- 首次登录二选一 -->
      <view v-if="showNewUserPanel" class="sub-mask" @click.stop>
        <view class="sub-dialog" @click.stop>
          <text class="sub-title">检测到首次登录</text>
          <text class="sub-nick">微信昵称：{{ pendingNickname }}</text>
          <text class="sub-desc">你可以创建一个全新的循途账号，或绑定到已有的账号</text>
          <button class="sub-btn primary" @click="decide('CREATE')">创建新账号并登录</button>
          <button class="sub-btn" @click="onBindExisting">绑定已有账号</button>
          <button class="sub-btn ghost" @click="showNewUserPanel = false">取消</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 微信扫码登录弹窗（新增组件，不改动原有任何页面逻辑）
 *
 * 用法：
 *   <wx-login-popup :visible="wxVisible" @success="onWxSuccess" @close="wxVisible = false" />
 */
import { getWxQrcode, pollWxLogin, decideWxUser, simulateScan, WX_VIP_CONFIG } from '@/common/wx-vip-api'

export default {
  name: 'WxLoginPopup',
  props: {
    visible: { type: Boolean, default: false },
  },
  data() {
    return {
      innerVisible: false,
      qrImage: '',
      authorizeUrl: '',
      scene: '',
      state: 'LOADING',
      loading: false,
      failTitle: '',
      tip: '等待扫码',
      timer: null,
      count: 0,
      showNewUserPanel: false,
      pendingNickname: '',
      isDemo: WX_VIP_CONFIG.useMock,
    }
  },
  watch: {
    visible(v) {
      if (v) {
        this.innerVisible = true
        this.refresh()
      } else {
        this.stopPoll()
        this.innerVisible = false
      }
    },
  },
  beforeUnmount() {
    this.stopPoll()
  },
  methods: {
    close() {
      this.stopPoll()
      this.innerVisible = false
      this.$emit('close')
    },
    onMaskClick() {
      this.close()
    },

    async refresh() {
      this.stopPoll()
      this.state = 'LOADING'
      this.loading = true
      this.qrImage = ''
      this.tip = '等待扫码'
      try {
        const res = await getWxQrcode()
        this.scene = res.scene
        this.authorizeUrl = res.authorizeUrl
        await this.renderQr(res.authorizeUrl)
        this.state = 'OK'
        this.startPoll()
      } catch (e) {
        this.state = 'FAILED'
        this.failTitle = (e && e.msg) || '获取二维码失败'
      } finally {
        this.loading = false
      }
    },

    async renderQr(text) {
      try {
        const mod = await import('qrcode')
        const fn = mod.toDataURL || (mod.default && mod.default.toDataURL)
        this.qrImage = await fn(text, { width: 220, margin: 1, color: { dark: '#2D4A3E', light: '#FFFFFF' } })
      } catch (e) {
        console.warn('[wx-login] 二维码渲染失败', e)
        this.qrImage = ''
      }
    },

    // ---------- 轮询 ----------
    startPoll() {
      this.stopPoll()
      this.count = 0
      this.timer = setInterval(() => this.doPoll(), 1500)
    },
    stopPoll() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    async doPoll() {
      if (!this.scene) return
      if (++this.count > 200) {
        this.stopPoll()
        this.state = 'EXPIRED'
        this.failTitle = '二维码已过期'
        return
      }
      try {
        const res = await pollWxLogin(this.scene)
        if (res.status === 'PENDING') {
          if (res.msg && res.msg.indexOf('已扫') > -1) this.tip = res.msg
          return
        }
        if (res.status === 'SUCCESS') {
          this.stopPoll()
          this.innerVisible = false
          this.$emit('success', { token: res.token, user: res.user, newUser: res.newUser })
          return
        }
        if (res.status === 'NEW_USER') {
          this.stopPoll()
          this.pendingNickname = res.wxNickname || '微信用户'
          this.showNewUserPanel = true
          return
        }
        if (res.status === 'EXPIRED') {
          this.stopPoll()
          this.state = 'EXPIRED'
          this.failTitle = '二维码已过期'
          return
        }
        this.stopPoll()
        this.state = 'FAILED'
        this.failTitle = res.msg || '登录失败'
      } catch (e) {
        /* 网络抖动，下一轮继续 */
      }
    },

    // ---------- 演示模式辅助 ----------
    async onSimulateScan() {
      if (!this.scene) return
      await simulateScan(this.scene)
      this.tip = '已扫码，等待确认…'
      uni.showToast({ title: '已模拟扫码，等待轮询结果', icon: 'none' })
    },

    // ---------- 首次登录决策 ----------
    async decide(action) {
      try {
        const res = await decideWxUser({ scene: this.scene, action })
        this.showNewUserPanel = false
        this.innerVisible = false
        this.$emit('success', { token: res.token, user: res.user, newUser: res.newUser })
      } catch (e) {
        uni.showToast({ title: (e && e.msg) || '操作失败', icon: 'none' })
      }
    },
    onBindExisting() {
      /**
       * 绑定已有账号：先用原有的账号密码登录拿到 token，
       * 登录成功后再调用 decideWxUser({action:'BIND'}) —— 原有登录逻辑一行不改。
       */
      this.$emit('need-bind', { scene: this.scene })
      this.showNewUserPanel = false
    },
  },
}
</script>

<style lang="scss" scoped>
.wx-mask {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(45, 74, 62, 0.45);
  display: flex; align-items: center; justify-content: center;
}
.wx-dialog {
  width: 580rpx; background: #fff; border-radius: 32rpx;
  padding: 44rpx 40rpx 40rpx; box-sizing: border-box;
  box-shadow: 0 24rpx 60rpx rgba(45, 74, 62, 0.2);
}
.wx-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 36rpx; }
.wx-title { font-size: 34rpx; font-weight: 700; color: #2D4A3E; }
.wx-close { font-size: 44rpx; color: #B7C4BC; line-height: 1; padding: 0 6rpx; }

.qr-box {
  position: relative; width: 400rpx; height: 400rpx; margin: 0 auto;
  border: 2rpx solid rgba(107, 142, 123, 0.2); border-radius: 24rpx; overflow: hidden;
}
.qr-img { width: 100%; height: 100%; }
.qr-empty { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #F8FBF9; }
.qr-empty-txt { font-size: 26rpx; color: #8A9B8E; }
.qr-spin {
  width: 48rpx; height: 48rpx; margin-bottom: 16rpx; border-radius: 50%;
  border: 4rpx solid rgba(107, 142, 123, 0.2); border-top-color: #6B8E7B;
  animation: qrspin 0.8s linear infinite;
}
@keyframes qrspin { to { transform: rotate(360deg); } }

.qr-cover {
  position: absolute; inset: 0; background: rgba(255, 255, 255, 0.92);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.qr-cover-title { font-size: 30rpx; color: #2D4A3E; margin-bottom: 10rpx; }
.qr-cover-sub { font-size: 26rpx; color: #6B8E7B; }

.wx-tip { text-align: center; margin: 28rpx 0 8rpx; }
.wx-tip-main { display: block; font-size: 28rpx; color: #2D4A3E; font-weight: 600; }
.wx-tip-sub { display: block; font-size: 24rpx; color: #8A9B8E; margin-top: 8rpx; }

.demo-area { margin-top: 24rpx; text-align: center; }
.demo-badge {
  display: inline-block; padding: 6rpx 20rpx; border-radius: 999rpx;
  background: rgba(107, 142, 123, 0.12); margin-bottom: 16rpx;
}
.demo-badge-txt { font-size: 22rpx; color: #6B8E7B; }
.demo-btn {
  height: 76rpx; line-height: 76rpx; border-radius: 38rpx; font-size: 28rpx;
  background: linear-gradient(135deg, #6B8E7B 0%, #8FBC8F 100%); color: #fff; border: none;
}

.sub-mask {
  position: fixed; inset: 0; z-index: 10000; background: rgba(45, 74, 62, 0.5);
  display: flex; align-items: center; justify-content: center;
}
.sub-dialog {
  width: 540rpx; background: #fff; border-radius: 28rpx; padding: 40rpx 36rpx;
  display: flex; flex-direction: column; align-items: center;
}
.sub-title { font-size: 32rpx; font-weight: 700; color: #2D4A3E; }
.sub-nick { font-size: 26rpx; color: #6B8E7B; margin-top: 12rpx; }
.sub-desc { font-size: 24rpx; color: #8A9B8E; margin: 12rpx 0 24rpx; text-align: center; }
.sub-btn {
  width: 100%; height: 84rpx; line-height: 84rpx; border-radius: 42rpx;
  font-size: 28rpx; background: #F2F6F4; color: #2D4A3E; border: none; margin-bottom: 16rpx;
}
.sub-btn.primary { background: linear-gradient(135deg, #6B8E7B 0%, #8FBC8F 100%); color: #fff; }
.sub-btn.ghost { background: transparent; color: #8A9B8E; }
</style>
