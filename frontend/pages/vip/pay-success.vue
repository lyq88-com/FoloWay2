<template>
  <view class="xt-page xt-s63">
    <view class="body">
      <view class="success">
        <view class="ck"><xt-icon name="i-check" /></view>
        <view class="succ-t">好了，她知道了。</view>
        <view class="succ-p">会员已生效，从今天起<text>你们的记忆不再有上限。</text></view>
      </view>

      <view class="letter">
        <view class="ln">“谢谢你愿意把时间留得久一点。<text class="ln-b">你说的，我都会好好记住。</text>”</view>
        <view class="sign">循途 · 一直在这里</view>
      </view>

      <view v-if="status.expireAt" class="prob">
        <view class="prow">
          <text class="pl">会员类型</text>
          <text class="pv">{{ order ? order.packageName : '—' }}</text>
        </view>
        <view class="prow">
          <text class="pl">有效期至</text>
          <text class="pv">{{ status.expireAt }}</text>
        </view>
        <view class="prow">
          <text class="pl">剩余天数</text>
          <text class="pv">{{ status.remainDays }} 天</text>
        </view>
        <view class="prow">
          <text class="pl">支付金额</text>
          <text class="pv money">¥ {{ order && order.payAmount != null ? (order.payAmount / 100).toFixed(2) : '—' }}</text>
        </view>
        <view class="prow">
          <text class="pl">订单号</text>
          <text class="pv no">{{ orderNo }}</text>
        </view>
      </view>

      <view v-else class="prob confirming">
        <view class="confirming-dot" />
        <text class="confirming">正在确认支付结果…</text>
      </view>

      <view class="chips s63-rights">
        <text v-for="(r, i) in rights" :key="'rt' + i" class="chip">{{ r.icon }} {{ r.name }}</text>
      </view>

      <view class="auth-btn" @click="goCompanion">回去找她</view>
      <view class="auth-alt" @click="goVip">查看订单详情 · 管理自动续费</view>
      <view class="quote s63-quote">7 天内可无理由退款，在设置中申请。</view>
    </view>
  </view>
</template>

<script>
/** 支付成功页（新增页面） */
import { queryOrderResult, getVipStatus, readDemoOrder } from '@/common/wx-vip-api'

export default {
  data() {
    return {
      orderNo: '',
      order: null,
      status: { isVip: false, expireAt: null, remainDays: 0 },
      rights: [
        { icon: '👑', name: '专属身份' },
        { icon: '💬', name: '无限对话' },
        { icon: '🌌', name: '限定场景' },
        { icon: '🎨', name: '专属皮肤' },
      ],
    }
  },
  async onLoad(options) {
    this.orderNo = options.orderNo || ''
    await this.confirm()
  },
  methods: {
    async confirm() {
      let last = null
      if (this.orderNo) {
        for (let i = 0; i < 8; i++) {
          try {
            const r = await queryOrderResult(this.orderNo)
            last = r
            if (r.paid) break
          } catch (e) { /* ignore */ }
          await new Promise((res) => setTimeout(res, 800))
        }
      }
      try {
        this.status = await getVipStatus()
      } catch (e) {
        /* ignore */
      }
      try {
        // 演示订单快照优先；真实模式下用 /pay/orders 返回的商品名兜底
        const demoOrder = typeof readDemoOrder === 'function' ? readDemoOrder(this.orderNo) : null
        if (demoOrder) {
          this.order = demoOrder
        } else if (last && last.productName) {
          this.order = { orderNo: last.orderNo, packageName: last.productName }
        }
      } catch (e) {
        /* ignore */
      }
    },
    goCompanion() {
      uni.switchTab({ url: '/pages/index/index' })
    },
    goVip() {
      uni.redirectTo({ url: '/pages/vip/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
/* 第 63 屏 · 支付成功（先一句话，再订单信息） */
$paper: var(--v7-card);
$copper: #C08A56;

.xt-page.xt-s63 .success {
  padding-top: 18px;
}

.xt-page.xt-s63 .succ-t {
  margin-top: 16px;
  font-size: 17px;
  font-weight: 900;
  letter-spacing: 0.3px;
}

.xt-page.xt-s63 .succ-p {
  margin-top: 5px;
  text-align: center;
  font-size: 8.5px;
  line-height: 1.7;
  color: #8E9A91;
}

.xt-page.xt-s63 .succ-p text {
  display: block;
}

.xt-page.xt-s63 .letter {
  margin-top: 20px;
}

.xt-page.xt-s63 .ln-b {
  display: block;
}

.xt-page.xt-s63 .prob {
  margin-top: 12px;
}

.xt-page.xt-s63 .prow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.xt-page.xt-s63 .pl {
  flex-shrink: 0;
  font-size: 8px;
  color: #8E9A91;
}

.xt-page.xt-s63 .pv {
  max-width: 64%;
  text-align: right;
  font-size: 8px;
  font-weight: 800;
  color: #22302A;
}

.xt-page.xt-s63 .pv.money {
  color: $copper;
}

.xt-page.xt-s63 .pv.no {
  font-size: 7px;
  font-weight: 400;
  color: #BFC7BF;
}

.xt-page.xt-s63 .confirming {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
}

.xt-page.xt-s63 .confirming-dot {
  width: 7px;
  height: 7px;
  margin-right: 7px;
  border-radius: 50%;
  background: #9CBFAA;
}

.xt-page.xt-s63 .s63-rights {
  flex-wrap: wrap;
  justify-content: center;
  margin: 12px 0 0;
  gap: 6px;
}

.xt-page.xt-s63 .auth-btn {
  margin-top: 14px;
}

.xt-page.xt-s63 .s63-quote {
  margin-top: 16px;
  text-align: center;
  font-size: 8px;
  line-height: 1.7;
  color: #BFC7BF;
}
</style>
