<template>
  <view class="xt-page xt-s64">
    <view class="body doc">
      <view class="chat-head">
        <view class="back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="chat-meta">
          <view class="chat-name">关于 AI 陪伴</view>
          <view class="chat-st">最后更新 2026-11-01</view>
        </view>
        <view class="doc-mark"><xt-icon name="i-book" /></view>
      </view>

      <view class="mem-hero">
        <view class="t">请先读这三句</view>
        <view class="m">
          <text>一、循途是陪伴工具，不是医生。</text>
          <text>二、危机时刻，请优先联系真人。</text>
          <text>三、你的数据由你做主。</text>
        </view>
      </view>

      <view class="dh">一、循途是陪伴工具，不是医疗服务</view>
      <view class="dp">循途提供 AI 情绪陪伴、习惯养成与自我记录功能。AI 生成的内容不构成医学诊断、心理治疗建议或专业咨询意见。如果你正处在持续的情绪困扰中，请及时寻求精神科医生、心理咨询师等专业人士的帮助。</view>

      <view class="dh">二、危机时刻，请优先联系真人</view>
      <view class="dp">当你出现伤害自己的想法时，请立刻拨打 24 小时心理援助热线（如 400-161-9995），或联系你信任的人。AI 陪伴无法替代真人的帮助，我们也会在检测到相关信号时主动提醒你这些资源。</view>

      <view class="dh">三、内容安全约定</view>
      <view class="dp">请勿在动态、世界、剧本、评论中发布涉政敏感、色情低俗、暴力违禁、赌博诈骗或广告引流信息。系统会对提交内容与 AI 输出进行安全过滤，违规内容将被拦截。</view>

      <view class="dh">四、你的数据由你做主</view>
      <view class="dp">你可以在「设置」中随时导出个人数据，也可以申请注销账号（注销前系统会自动备份你的数据留档）。我们可以承诺：不向任何第三方出售你的个人数据。</view>

      <view class="dh">五、青少年保护</view>
      <view class="dp">开启「青少年模式」后，AI 主动消息、VIP 等付费入口将被限制，并提供使用时长提醒。监护人应协助未成年人合理使用本产品。</view>

      <view class="dh">六、演示版本说明</view>
      <view class="dp">当前版本为功能演示版本，AI 能力与支付流程均为演示实现，请勿进行真实交易。</view>

      <view class="hotline-card">
        <view class="hotline-head">
          <view class="hotline-icon"><xt-icon name="i-call" /></view>
          <view class="hotline-head-main">
            <view class="hotline-title">紧急求助资源</view>
            <view class="hotline-sub">24 小时 · 点击可直接拨打</view>
          </view>
        </view>
        <view class="hotline" @click="call('400-161-9995')">
          <text class="hotline-name">全国心理援助热线</text>
          <text class="hotline-phone">400-161-9995</text>
        </view>
        <view class="hotline" @click="call('010-82951332')">
          <text class="hotline-name">北京心理危机研究与干预中心</text>
          <text class="hotline-phone">010-82951332</text>
        </view>
      </view>

      <view class="auth-btn" @click="agree">我了解了</view>
      <view class="auth-alt" @click="goBack">返回上一页</view>
      <view class="quote s64-quote">完整条款请见《用户协议》与《隐私政策》</view>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    call(phone) {
      // #ifdef H5
      window.location.href = `tel:${phone}`
      // #endif
      // #ifndef H5
      uni.makePhoneCall({ phoneNumber: phone, fail: () => {} })
      // #endif
    },
    goBack() {
      uni.navigateBack({ fail: () => uni.reLaunch({ url: '/pages/index/index' }) })
    },
    agree() {
      try {
        uni.setStorageSync('disclaimer_agreed_at', String(Date.now()))
      } catch (e) { /* 静默 */ }
      uni.showToast({ title: '已记录，祝你使用愉快', icon: 'none' })
      setTimeout(() => this.goBack(), 600)
    }
  }
}
</script>

<style lang="scss" scoped>
/* 第 64 屏 · 免责声明（可读的中文，重点句加粗） */
.xt-page.xt-s64 .doc-mark {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8E9A91;
  background: #fff;
  box-shadow: 0 0 0 1px var(--v7-line);
}

.xt-page.xt-s64 .doc-mark .ic {
  width: 15px;
  height: 15px;
}

.xt-page.xt-s64 .mem-hero {
  margin-top: 8px;
}

.xt-page.xt-s64 .mem-hero .m text {
  display: block;
}

.xt-page.xt-s64 .dh {
  margin-top: 14px;
  font-size: 10.5px;
  font-weight: 800;
  color: #22302A;
}

.xt-page.xt-s64 .dp {
  margin-top: 5px;
  font-size: 8.5px;
  line-height: 1.85;
  color: #7C877E;
}

.xt-page.xt-s64 .hotline-card {
  margin-top: 14px;
  padding: 11px 12px 4px;
  border-radius: 15px;
  background: #FBF5EC;
  box-shadow: inset 0 0 0 1px rgba(192, 138, 86, 0.22);
}

.xt-page.xt-s64 .hotline-head {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.xt-page.xt-s64 .hotline-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #B57F4C;
}

.xt-page.xt-s64 .hotline-icon .ic {
  width: 13px;
  height: 13px;
}

.xt-page.xt-s64 .hotline-head-main {
  margin-left: 9px;
}

.xt-page.xt-s64 .hotline-title {
  font-size: 9px;
  font-weight: 900;
  color: #8A5D33;
}

.xt-page.xt-s64 .hotline-sub {
  margin-top: 2px;
  font-size: 7.5px;
  color: #B09272;
}

.xt-page.xt-s64 .hotline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-top: 1px solid rgba(192, 138, 86, 0.16);
}

.xt-page.xt-s64 .hotline-name {
  font-size: 8px;
  color: #6E563C;
}

.xt-page.xt-s64 .hotline-phone {
  font-size: 8px;
  font-weight: 800;
  color: #A9703F;
}

.xt-page.xt-s64 .auth-btn {
  margin-top: 14px;
}

.xt-page.xt-s64 .s64-quote {
  margin-top: 12px;
  text-align: center;
  font-size: 7.5px;
  line-height: 1.7;
  color: #BFC7BF;
}
</style>
