<template>
  <view class="xt-page xt-s21">
    <view class="body" style="padding:0">
      <view class="auth">
        <view class="brand">
          <view class="logo"><xt-icon name="i-spark" size="15" /></view>
          <text>循途</text>
        </view>

        <h2>先让 TA 认识你。</h2>
        <view class="lead">不需要完美的人设，你怎么称呼自己都可以。</view>

        <view class="field">
          <view class="lab">昵称</view>
          <input
            v-model="username"
            class="val"
            type="text"
            maxlength="50"
            placeholder="请输入用户名（2-50 字符）"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">邮箱</view>
          <input
            v-model="email"
            class="val"
            type="text"
            maxlength="100"
            placeholder="请输入邮箱"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">手机号（选填）</view>
          <input
            v-model="phone"
            class="val"
            type="number"
            maxlength="11"
            placeholder="填写后可用手机号登录"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">密码</view>
          <input
            v-model="password"
            class="val"
            password
            maxlength="50"
            placeholder="请输入密码（至少 8 位）"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="field">
          <view class="lab">确认密码</view>
          <input
            v-model="confirmPassword"
            class="val"
            password
            maxlength="50"
            placeholder="请再次输入密码"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="agree-row" @click="agreed = !agreed">
          <view class="checkbox" :class="{ checked: agreed }">
            <text v-if="agreed" class="check-mark">✓</text>
          </view>
          <text class="agree-text">我已阅读并同意《用户协议》和《隐私政策》</text>
        </view>

        <view class="auth-btn" :class="{ disabled: isLoading }" @click="handleRegister">
          <text v-if="!isLoading">创建账号</text>
          <text v-else>注册中…</text>
        </view>

        <view class="auth-alt" @click="goBack">已有账号？去登录</view>

        <view class="auth-foot">
          注册即表示同意《用户协议》与《隐私政策》<br />我们会先带你做一次 8 题的小测试
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 注册页 - 调用 FastAPI /api/v1/auth/register-username
 * 注册成功后自动跳回登录页
 */
import authApi from '@/api/auth'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      username: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      agreed: false,
      isLoading: false,
    }
  },
  methods: {
    async handleRegister() {
      const username = this.username.trim()
      const email = this.email.trim()
      const phone = this.phone.trim()
      const password = this.password

      // 校验
      if (!username || username.length < 2 || username.length > 50) {
        return uni.showToast({ title: '用户名需 2-50 字符', icon: 'none' })
      }
      if (!email || !/^[\w.+\-]+@[\w\-]+\.[\w.\-]+$/.test(email)) {
        return uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
      }
      if (phone && !/^1\d{10}$/.test(phone)) {
        return uni.showToast({ title: '手机号格式不正确', icon: 'none' })
      }
      if (!password || password.length < 8) {
        return uni.showToast({ title: '密码至少 8 位', icon: 'none' })
      }
      if (password !== this.confirmPassword) {
        return uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
      }
      if (!this.agreed) {
        return uni.showToast({ title: '请先同意用户协议', icon: 'none' })
      }

      this.isLoading = true
      try {
        const res = await authApi.register({ username, password, email, phone })
        const data = res.data || res
        if (data.access_token || data.user?.id) {
          uni.showToast({ title: '注册成功，请登录', icon: 'success' })
          setTimeout(() => uni.navigateBack(), 800)
        } else {
          uni.showToast({ title: data.message || '注册失败', icon: 'none' })
        }
      } catch (e) {
        uni.showToast({ title: e.message || '注册失败', icon: 'none' })
      } finally {
        this.isLoading = false
      }
    },

    goBack() {
      uni.navigateBack()
    },
  },
}
</script>

<style lang="scss" scoped>
/* uni-input 包装层高度对齐设计稿 .val */
.xt-page.xt-s21 .field .val {
  display: block;
  width: 100%;
  height: 15px;
}

/* 设计稿无协议勾选样式，表单校验必需，补最小结构样式 */
.xt-page.xt-s21 .agree-row {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 12px;
}
.xt-page.xt-s21 .checkbox {
  width: 14px;
  height: 14px;
  margin-top: 1px;
  border-radius: 4px;
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1px var(--v7-line);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.xt-page.xt-s21 .checkbox.checked {
  background: var(--v7-green);
  box-shadow: inset 0 0 0 1px var(--v7-green);
}
.xt-page.xt-s21 .check-mark {
  font-size: 8px;
  font-weight: 700;
  color: #F8F3E7;
}
.xt-page.xt-s21 .agree-text {
  flex: 1;
  font-size: 8px;
  line-height: 1.6;
  color: #6A776E;
}

/* 提交中禁用重复点击 */
.xt-page.xt-s21 .auth-btn.disabled {
  opacity: 0.72;
  pointer-events: none;
}
</style>
