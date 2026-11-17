<template>
  <view class="xt-page xt-s62">
    <view class="body">
      <view class="vip-hero">
        <view class="vip-top">
          <view class="vip-brand">循 途 会 员</view>
          <view class="vip-state">{{ status.isVip ? '已开通' : '未开通' }}</view>
        </view>
        <view class="vip-eyebrow">时 间 之 外 的 陪 伴</view>
        <view class="vip-title">
          <text>让她记得更久，</text>
          <text>也让你被记得更久。</text>
        </view>
        <view class="vip-desc">会员不是解锁功能，是把你们的故事留得更完整一点。</view>
        <view class="vip-status">
          {{ status.isVip ? '有效期至 ' + status.expireAt + ' · 剩余 ' + status.remainDays + ' 天' : '开通后立即解锁下列全部权益' }}
        </view>
        <view v-if="status.isVip" class="vip-bar">
          <view class="vip-bar-in" :style="{ width: progressWidth }" />
        </view>
      </view>

      <view class="vip-main">
        <view class="cal-sec vip-sec">
          <text class="t">她会多做什么</text>
          <text class="s">{{ rights.length }} 项专属</text>
        </view>
        <view
          v-for="(r, i) in rights"
          :key="'r' + i"
          class="mem-item"
          :style="{ marginTop: i === 0 ? '0' : '7px' }"
        >
          <view class="mi" :class="['tint-green', 'tint-peach', 'tint-blue', 'tint-purple'][i % 4]">
            <xt-icon :name="['i-chat', 'i-world', 'i-brain', 'i-spark'][i % 4]" />
          </view>
          <view class="tx">
            <view class="t">{{ r.name }}</view>
          </view>
        </view>

        <view class="cal-sec vip-sec" style="margin-top: 14px">
          <text class="t">选择套餐</text>
          <text class="s">{{ packages.length }} 个方案</text>
        </view>
        <view
          v-for="item in packages"
          :key="item.id"
          class="plan"
          :class="{ on: selectedId === item.id }"
          @click="selectedId = item.id"
        >
          <text v-if="item.tag" class="tag2">{{ item.tag }}</text>
          <view class="n">{{ item.name }}</view>
          <view class="p">
            ¥ {{ item.price }}<text class="unit"> / {{ item.days }} 天</text>
          </view>
          <view class="d">{{ item.subTitle }}</view>
          <view v-for="(b, bi) in item.benefits" :key="'b' + bi" class="plan-b">· {{ b }}</view>
          <view v-if="item.originalPrice" class="d plan-save">
            原价 ¥{{ item.originalPrice }} · 省 ¥{{ (item.originalPrice - item.price).toFixed(1) }}
          </view>
        </view>

        <view class="auth-btn" @click="openPayPopup">
          {{ (status.isVip ? '立即续费' : '开始这段更长的陪伴') + ' · ¥' + currentPrice }}
        </view>
        <view class="vip-terms">自动续费，可随时在设置中关闭</view>
        <view class="vip-terms">《会员服务协议》 · 《自动续费规则》</view>
        <view class="quote vip-quote">会员一经开通不支持退款 · 支付由微信支付提供担保</view>
        <view class="vip-demo">演示版本 · 支付流程为模拟实现，不会产生真实扣款</view>
      </view>
    </view>

    <!-- 支付确认弹窗 -->
    <view v-if="payPopup" class="mask" @click="payPopup = false">
      <view class="pay-sheet" @click.stop>
        <text class="sheet-title">确认订单</text>
        <view class="sheet-row">
          <text class="sheet-label">商品</text>
          <text class="sheet-value">{{ currentPackage.name }}</text>
        </view>
        <view class="sheet-row">
          <text class="sheet-label">会员时长</text>
          <text class="sheet-value">{{ currentPackage.days }} 天</text>
        </view>
        <view class="sheet-row">
          <text class="sheet-label">支付方式</text>
          <text class="sheet-value">微信支付</text>
        </view>
        <view class="sheet-amount">
          <text class="sheet-amount-symbol">¥</text>
          <text class="sheet-amount-num">{{ currentPrice }}</text>
        </view>
        <button class="sheet-btn" :loading="paying" @click="doCreateOrder">确认支付</button>
        <button class="sheet-cancel" @click="payPopup = false">暂不支付</button>
      </view>
    </view>

    <!-- 演示模式：模拟支付收银台（接真实支付后自动消失） -->
    <view v-if="demoCashier" class="mask" @click.stop>
      <view class="cashier" @click.stop>
        <text class="cashier-title">微信支付（演示）</text>
        <text class="cashier-sub">真实环境此处由微信收银台接管</text>
        <view class="cashier-amount">
          <text class="cashier-amount-symbol">¥</text>
          <text class="cashier-amount-num">{{ currentPrice }}</text>
        </view>
        <text class="cashier-order">{{ currentOrderNo }}</text>
        <button class="cashier-btn" @click="onPayResult(true)">模拟支付成功</button>
        <button class="cashier-btn ghost" @click="onPayResult(false)">模拟取消支付</button>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * VIP 会员购买页（新增页面，独立挂载）
 * 演示模式下可完整跑通：选套餐 → 下单 → 模拟支付 → 成功页 → VIP 状态更新
 */
import {
  getVipPackages,
  createVipOrder,
  queryOrderResult,
  getVipStatus,
  simulatePayResult,
  getMpAuthUrl,
  isWechatBrowser,
  WX_VIP_CONFIG,
} from '@/common/wx-vip-api'

export default {
  data() {
    return {
      packages: [],
      selectedId: null,
      status: { isVip: false, expireAt: null, remainDays: 0 },
      payPopup: false,
      demoCashier: false,
      paying: false,
      currentOrderNo: '',
      rights: [
        { icon: '💬', name: '无限对话' },
        { icon: '🌌', name: '限定场景' },
        { icon: '📊', name: '深度报告' },
        { icon: '🎨', name: '专属皮肤' },
      ],
    }
  },
  computed: {
    currentPackage() {
      return this.packages.find((p) => p.id === this.selectedId) || {}
    },
    currentPrice() {
      return this.currentPackage.price != null ? this.currentPackage.price.toFixed(2) : '0.00'
    },
    progressWidth() {
      // 按 365 天为一个满周期做视觉进度
      const pct = Math.min(100, Math.max(2, (this.status.remainDays / 365) * 100))
      return pct.toFixed(1) + '%'
    },
  },
  onLoad() {
    this.loadPackages()
    this.loadStatus()
  },
  onShow() {
    // ↓↓↓ 安全合规批次：青少年模式下拦截 VIP 页（付费入口） ↓↓↓
    try {
      if (uni.getStorageSync('pref_teen_mode') === 'true') {
        uni.showModal({
          title: '青少年模式',
          content: '当前处于青少年模式，VIP等付费入口已限制使用。',
          showCancel: false,
          confirmText: '知道了',
          success: () => uni.navigateBack({ fail: () => uni.reLaunch({ url: '/pages/index/index' }) })
        })
        return
      }
    } catch (e) { /* 静默 */ }
    // ↑↑↑ 新增结束 ↑↑↑
    this.loadStatus()
  },
  methods: {
    async loadPackages() {
      try {
        this.packages = await getVipPackages()
        if (this.packages.length) this.selectedId = this.packages[1] ? this.packages[1].id : this.packages[0].id
      } catch (e) {
        uni.showToast({ title: (e && e.msg) || '套餐加载失败', icon: 'none' })
      }
    },
    async loadStatus() {
      try {
        this.status = await getVipStatus()
      } catch (e) {
        /* 未登录时静默 */
      }
    },

    openPayPopup() {
      if (this.paying) return
      if (!this.currentPackage.id) return uni.showToast({ title: '请选择套餐', icon: 'none' })
      this.payPopup = true
    },

    async doCreateOrder() {
      if (this.paying) return
      this.paying = true
      try {
        const res = await createVipOrder(this.currentPackage.id)
        this.currentOrderNo = res.orderNo
        this.payPopup = false
        this.paying = false

        // mock 渠道（后端 provider=mock）返回 demo=true：打开模拟收银台，
        // 支付结果由 /pay/orders/{no}/mock-pay 落到服务端
        if (res.demo || WX_VIP_CONFIG.vipUseMock) {
          this.demoCashier = true
          return
        }
        if (res.wechatParams) {
          this.invokeJsapiPay(res.wechatParams)
        } else if (res.mwebUrl) {
          this.invokeMwebPay(res.mwebUrl)
        } else {
          throw { code: 4002, msg: '未获取到支付参数' }
        }
      } catch (e) {
        this.paying = false
        this.handlePayError(e)
      }
    },

    /** JSAPI：仅微信内置浏览器可用 */
    invokeJsapiPay(params) {
      // #ifdef H5
      if (!isWechatBrowser()) return uni.showToast({ title: '请在微信客户端中打开以完成支付', icon: 'none' })
      if (typeof WeixinJSBridge === 'undefined') return uni.showToast({ title: '微信支付初始化失败', icon: 'none' })
      const vm = this
      WeixinJSBridge.invoke(
        'getBrandWCPayRequest',
        {
          appId: params.appId,
          timeStamp: params.timeStamp,
          nonceStr: params.nonceStr,
          package: params.package,
          signType: params.signType,
          paySign: params.paySign,
        },
        (r) => {
          if (r.err_msg === 'get_brand_wcpay_request:ok') vm.afterClientPayOk()
          else if (r.err_msg === 'get_brand_wcpay_request:cancel') uni.showToast({ title: '支付已取消', icon: 'none' })
          else uni.showToast({ title: '支付失败', icon: 'none' })
        }
      )
      // #endif
      // #ifndef H5
      uni.showToast({ title: '请在微信内置浏览器中完成支付', icon: 'none' })
      // #endif
    },

    /** MWEB：外部浏览器跳转微信支付中间页 */
    invokeMwebPay(mwebUrl) {
      // #ifdef H5
      const back = encodeURIComponent(
        window.location.origin + window.location.pathname + '#/pages/vip/pay-success?orderNo=' + this.currentOrderNo
      )
      window.location.href = mwebUrl + (mwebUrl.indexOf('?') > -1 ? '&' : '?') + 'redirect_url=' + back
      // #endif
      // #ifndef H5
      plus.runtime.openURL(mwebUrl)
      // #endif
    },

    async afterClientPayOk() {
      uni.showLoading({ title: '确认支付结果…' })
      let paid = false
      for (let i = 0; i < 10; i++) {
        try {
          const r = await queryOrderResult(this.currentOrderNo)
          if (r.paid) { paid = true; break }
        } catch (e) { /* 忽略单次失败 */ }
        await new Promise((r) => setTimeout(r, 1000))
      }
      uni.hideLoading()
      if (paid) uni.redirectTo({ url: '/pages/vip/pay-success?orderNo=' + this.currentOrderNo })
      else {
        uni.showToast({ title: '支付结果确认中，请稍后查看', icon: 'none' })
        this.loadStatus()
      }
    },

    /** 演示收银台回调 */
    async onPayResult(success) {
      this.demoCashier = false
      try {
        const r = await simulatePayResult(this.currentOrderNo, success)
        if (!success || !r.paid) return uni.showToast({ title: '支付已取消', icon: 'none' })
        uni.redirectTo({ url: '/pages/vip/pay-success?orderNo=' + this.currentOrderNo })
      } catch (e) {
        uni.showToast({ title: (e && e.msg) || '支付失败', icon: 'none' })
      }
    },

    handlePayError(e) {
      const code = e && e.code
      const msg = (e && e.msg) || '支付失败，请稍后重试'
      if (code === 401) {
        return uni.showModal({
          title: '登录已过期',
          content: '请重新登录后继续支付',
          success: (r) => { if (r.confirm) uni.navigateTo({ url: '/pages/login/login' }) },
        })
      }
      if (code === 4001) {
        return uni.showModal({
          title: '需要支付授权',
          content: '首次使用微信支付，需要完成一次微信授权',
          success: async (r) => {
            if (!r.confirm) return
            try {
              const res = await getMpAuthUrl()
              // #ifdef H5
              window.location.href = res.authUrl
              // #endif
            } catch (err) {
              uni.showToast({ title: '获取授权地址失败', icon: 'none' })
            }
          },
        })
      }
      uni.showToast({ title: msg, icon: 'none', duration: 2500 })
    },
  },
}
</script>

<style lang="scss" scoped>
/* 第 62 屏 · VIP 会员（深色整屏头部 + 价格先行） */
$paper: var(--v7-card);
$ink: var(--v7-green);
$copper: #C08A56;

.xt-page.xt-s62 .body {
  padding: 0;
}

.xt-page.xt-s62 .vip-hero {
  padding: calc(env(safe-area-inset-top) + 16px) 20px 22px;
  background: linear-gradient(165deg, #404E48 0%, #27302C 56%, #202A25 100%);
  color: #F0E5DB;
}

.xt-page.xt-s62 .vip-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.xt-page.xt-s62 .vip-brand {
  font-size: 7.5px;
  letter-spacing: 2px;
  color: rgba(243, 231, 216, 0.6);
}

.xt-page.xt-s62 .vip-state {
  font-size: 7px;
  letter-spacing: 0.6px;
  padding: 4px 9px;
  border-radius: 999px;
  color: #D3BFAA;
  background: rgba(243, 231, 216, 0.12);
}

.xt-page.xt-s62 .vip-eyebrow {
  margin-top: 26px;
  font-size: 8px;
  letter-spacing: 2.4px;
  color: #D3BFAA;
}

.xt-page.xt-s62 .vip-title {
  margin-top: 10px;
  font-size: 23px;
  font-weight: 900;
  line-height: 1.4;
  letter-spacing: 0.4px;
}

.xt-page.xt-s62 .vip-title text {
  display: block;
}

.xt-page.xt-s62 .vip-desc {
  margin-top: 9px;
  width: 82%;
  font-size: 8.5px;
  line-height: 1.85;
  color: rgba(243, 231, 216, 0.6);
}

.xt-page.xt-s62 .vip-status {
  margin-top: 12px;
  font-size: 7.5px;
  letter-spacing: 0.4px;
  color: rgba(243, 231, 216, 0.46);
}

.xt-page.xt-s62 .vip-bar {
  margin-top: 9px;
  height: 3px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(243, 231, 216, 0.14);
}

.xt-page.xt-s62 .vip-bar-in {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #D3BFAA, #F0E5DB);
  transition: width 0.4s ease;
}

.xt-page.xt-s62 .vip-main {
  padding: 14px 18px 26px;
}

.xt-page.xt-s62 .vip-sec {
  margin: 0 0 2px;
}

.xt-page.xt-s62 .plan .unit {
  font-size: 8px;
  font-weight: 400;
  color: #AEB6AE;
}

.xt-page.xt-s62 .plan-b {
  margin-top: 4px;
  font-size: 7.5px;
  color: #8E9A91;
}

.xt-page.xt-s62 .plan-save {
  color: $copper;
}

.xt-page.xt-s62 .vip-terms {
  margin-top: 8px;
  text-align: center;
  font-size: 7px;
  line-height: 1.7;
  color: #BFC7BF;
}

.xt-page.xt-s62 .vip-quote {
  margin-top: 12px;
  text-align: center;
  font-size: 7.5px;
  line-height: 1.7;
  color: #BFC7BF;
}

.xt-page.xt-s62 .vip-demo {
  margin-top: 16px;
  text-align: center;
  font-size: 7px;
  color: #C9D0C9;
}

/* 支付确认 / 演示收银台 */
.xt-page.xt-s62 .mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 200;
  background: rgba(31, 42, 37, 0.45);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.xt-page.xt-s62 .pay-sheet {
  width: 100%;
  max-width: 392px;
  padding: 22px 20px calc(env(safe-area-inset-bottom) + 20px);
  box-sizing: border-box;
  background: $paper;
  border-radius: 22px 22px 0 0;
}

.xt-page.xt-s62 .sheet-title {
  display: block;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 900;
  color: #22302A;
}

.xt-page.xt-s62 .sheet-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(46, 86, 67, 0.07);
}

.xt-page.xt-s62 .sheet-label {
  font-size: 9px;
  color: #8E9A91;
}

.xt-page.xt-s62 .sheet-value {
  font-size: 9px;
  font-weight: 700;
  color: #22302A;
}

.xt-page.xt-s62 .sheet-amount {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin: 16px 0 18px;
  color: $copper;
}

.xt-page.xt-s62 .sheet-amount-symbol {
  font-size: 12px;
  font-weight: 800;
}

.xt-page.xt-s62 .sheet-amount-num {
  font-size: 30px;
  font-weight: 900;
}

.xt-page.xt-s62 .sheet-btn {
  height: 44px;
  line-height: 44px;
  border: none;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  color: $paper;
  background: linear-gradient(135deg, var(--v7-green), $ink);
  box-shadow: 0 14px 26px -16px rgba(110, 143, 123, 0.9);
}

.xt-page.xt-s62 .sheet-btn::after,
.xt-page.xt-s62 .sheet-cancel::after,
.xt-page.xt-s62 .cashier-btn::after {
  border: none;
}

.xt-page.xt-s62 .sheet-cancel {
  height: 40px;
  line-height: 40px;
  margin-top: 4px;
  border: none;
  background: transparent;
  font-size: 10px;
  color: #8E9A91;
}

.xt-page.xt-s62 .cashier {
  width: 100%;
  max-width: 392px;
  padding: 24px 20px calc(env(safe-area-inset-bottom) + 22px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: $paper;
  border-radius: 22px 22px 0 0;
}

.xt-page.xt-s62 .cashier-title {
  font-size: 14px;
  font-weight: 900;
  color: #22302A;
}

.xt-page.xt-s62 .cashier-sub {
  margin-top: 4px;
  font-size: 8px;
  color: #A2AAA3;
}

.xt-page.xt-s62 .cashier-amount {
  display: flex;
  align-items: baseline;
  margin: 14px 0 4px;
  color: $copper;
}

.xt-page.xt-s62 .cashier-amount-symbol {
  font-size: 12px;
  font-weight: 800;
}

.xt-page.xt-s62 .cashier-amount-num {
  font-size: 32px;
  font-weight: 900;
}

.xt-page.xt-s62 .cashier-order {
  margin-bottom: 16px;
  font-size: 7.5px;
  color: #BFC7BF;
}

.xt-page.xt-s62 .cashier-btn {
  width: 100%;
  height: 44px;
  line-height: 44px;
  margin-bottom: 8px;
  border: none;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: $paper;
  background: linear-gradient(135deg, var(--v7-green), $ink);
}

.xt-page.xt-s62 .cashier-btn.ghost {
  background: transparent;
  color: #8E9A91;
  font-weight: 400;
}
</style>
