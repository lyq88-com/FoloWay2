<template>
  <view class="xt-page">
    <view class="body" style="padding:0">
      <view class="auth">
        <view class="brand">
          <view class="logo"><xt-icon name="i-spark" size="15" /></view>
          <text>循途</text>
        </view>

        <h2>别急，<br />先把密码找回来。</h2>
        <view class="lead">用注册时填写的手机号接收验证码，重置成功后即可用新密码登录。</view>

        <view class="field">
          <view class="lab">手机号</view>
          <input
            v-model="phone"
            class="val"
            type="number"
            maxlength="11"
            placeholder="请输入注册手机号"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">验证码</view>
          <view class="row2">
            <input
              v-model="code"
              class="val"
              type="number"
              maxlength="6"
              placeholder="6 位验证码"
              placeholder-style="color:#CFD6CE"
            />
            <text class="code" :class="{ disabled: counting }" @click="sendCode">{{ codeText }}</text>
          </view>
        </view>

        <view class="field">
          <view class="lab">新密码</view>
          <input
            v-model="password"
            class="val"
            password
            maxlength="32"
            placeholder="至少 8 位"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">确认新密码</view>
          <input
            v-model="confirmPassword"
            class="val"
            password
            maxlength="32"
            placeholder="请再次输入新密码"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="auth-btn" :class="{ disabled: isLoading }" @click="submit">
          <text v-if="!isLoading">重置密码</text>
          <text v-else>提交中…</text>
        </view>

        <view class="auth-alt" @click="goBack">返回登录</view>

        <view class="auth-foot">
          验证码 5 分钟内有效，仅可使用一次<br />循途 v1.0.0
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 找回密码页 - 短信验证码重置
 * 接口：POST /api/v1/auth/sms/send、POST /api/v1/auth/password/reset
 * 说明：开发渠道（SMS_PROVIDER=mock）会把演示验证码随响应返回，页面自动填入，方便本地联调。
 */
import authApi from '@/api/auth'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      phone: '',
      code: '',
      password: '',
      confirmPassword: '',
      isLoading: false,
      countdown: 0,
      timer: null
    }
  },
  computed: {
    counting() {
      return this.countdown > 0 || this.isLoading
    },
    codeText() {
      return this.countdown > 0 ? `${this.countdown}s 后重发` : '获取验证码'
    }
  },
  onUnload() {
    this.clearTimer()
  },
  methods: {
    clearTimer() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    startCountdown() {
      this.countdown = 60
      this.clearTimer()
      this.timer = setInterval(() => {
        this.countdown -= 1
        if (this.countdown <= 0) this.clearTimer()
      }, 1000)
    },
    async sendCode() {
      if (this.counting) return
      if (!/^1[3-9]\d{9}$/.test(this.phone.trim())) {
        return uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
      }
      this.isLoading = true
      try {
        const res = await authApi.sendSmsCode(this.phone.trim(), 'reset')
        // request 层 resolve 的是完整响应体 { code, message, data }
        if (!res || res.code !== 200) {
          return uni.showToast({ title: (res && res.message) || '发送失败', icon: 'none' })
        }
        this.startCountdown()
        const demoCode = res.data && res.data.demoCode
        if (demoCode) {
          // 仅开发渠道会返回 demoCode，自动填入便于本地联调
          this.code = String(demoCode)
          uni.showToast({ title: '演示验证码已填入', icon: 'none', duration: 1800 })
        } else {
          uni.showToast({ title: '验证码已发送', icon: 'success' })
        }
      } catch (e) {
        uni.showToast({ title: e.message || '发送失败', icon: 'none' })
      } finally {
        this.isLoading = false
      }
    },
    async submit() {
      if (this.isLoading) return
      const phone = this.phone.trim()
      const code = this.code.trim()
      if (!/^1[3-9]\d{9}$/.test(phone)) {
        return uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
      }
      if (!/^\d{4,8}$/.test(code)) {
        return uni.showToast({ title: '请输入验证码', icon: 'none' })
      }
      if (!this.password || this.password.length < 8) {
        return uni.showToast({ title: '新密码至少 8 位', icon: 'none' })
      }
      if (this.password !== this.confirmPassword) {
        return uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
      }

      this.isLoading = true
      try {
        const res = await authApi.resetPassword(phone, code, this.password)
        if (!res || res.code !== 200) {
          return uni.showToast({ title: (res && res.message) || '重置失败', icon: 'none', duration: 2500 })
        }
        uni.showToast({ title: '密码已重置，请登录', icon: 'success' })
        setTimeout(() => this.goBack(), 900)
      } catch (e) {
        uni.showToast({ title: e.message || '重置失败', icon: 'none' })
      } finally {
        this.isLoading = false
      }
    },
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) uni.navigateBack()
      else uni.reLaunch({ url: '/pages/login/login' })
    }
  }
}
</script>

<style lang="scss" scoped>
/* uni-input 包装层高度对齐设计稿 .val */
.xt-page .field .val {
  display: block;
  width: 100%;
  height: 15px;
}

/* 验证码按钮：可点区域与禁用态 */
.xt-page .field .code {
  flex-shrink: 0;
  padding: 4px 0 4px 10px;
  font-size: 8.5px;
}
.xt-page .field .code.disabled {
  color: #B5BDB6;
  pointer-events: none;
}

/* 提交中禁用重复点击 */
.xt-page .auth-btn.disabled {
  opacity: 0.72;
  pointer-events: none;
}
</style>
