<template>
  <view class="xt-page xt-s20">
    <view class="body" style="padding:0">
      <view class="auth">
        <view class="brand">
          <view class="logo"><xt-icon name="i-spark" size="15" /></view>
          <text>循途</text>
        </view>

        <h2>回到她身边，<br />今天也有人在等你。</h2>
        <view class="lead">用账号密码登录，继续你们未完成的对话和习惯。</view>

        <view class="field">
          <view class="lab">用户名 / 手机号</view>
          <input
            v-model="username"
            class="val"
            type="text"
            maxlength="50"
            placeholder="请输入用户名或手机号"
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
            placeholder="请输入密码"
            placeholder-style="color:#CFD6CE"
          />
        </view>

        <view class="auth-btn" :class="{ disabled: isLoading }" @click="handleLogin">
          <text v-if="!isLoading">登 录</text>
          <text v-else>登录中…</text>
        </view>

        <view class="auth-alt" @click="goRecover">忘记密码？</view>

        <view class="auth-3rd">
          <view class="third" @click="wxVisible = true">微信</view>
          <view class="third">Apple</view>
          <view class="third">游客体验</view>
        </view>

        <!-- 保留注册入口 -->
        <view class="auth-alt" @click="goRegister">还没有账号？立即注册</view>

        <view class="auth-foot">
          登录即表示同意《用户协议》与《隐私政策》<br />循途 v1.0.0
        </view>
      </view>
    </view>

    <!-- 微信扫码登录（保留原有入口与回调） -->
    <wx-login-popup
      :visible="wxVisible"
      @close="wxVisible = false"
      @success="onWxLoginSuccess"
    />

    <!-- 登录后立即展示的新手引导（首次登录，完成/跳过后再进入下一步） -->
    <GuideOnboarding :visible="showGuide" :account="guideAccount" @finish="onGuideFinish" />
  </view>
</template>

<script>
/**
 * 登录页 - 调用 FastAPI /api/v1/auth/login-username（用户名或手机号均可）
 * 登录成功后：token 存 store（自动持久化到 uni.storage），跳转首页
 */
import authApi from '@/api/auth'
import { fetchQuizResultFromCloud } from '@/common/personality-quiz'
import economy from '@/common/economy'
import playSync from '@/common/play-sync'
// ↓↓↓ 新增 ↓↓↓
import WxLoginPopup from '@/components/wx-login-popup.vue'
import GuideOnboarding from '@/components/guide-onboarding.vue'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
// ↑↑↑ 新增结束 ↑↑↑

export default {
  // ↓↓↓ 新增 ↓↓↓
  components: { WxLoginPopup, GuideOnboarding, XtIcon },
  // ↑↑↑ 新增结束 ↑↑↑
  data() {
    return {
      username: '',
      password: '',
      isLoading: false,
      // ↓↓↓ 新增 ↓↓↓
      wxVisible: false,
      // 新手引导：登录成功后立即展示，关闭后再跳转
      showGuide: false,
      pendingUrl: '',
      guideAccount: '',
      // ↑↑↑ 新增结束 ↑↑↑
    }
  },
  methods: {
    async handleLogin() {
      const username = this.username.trim()
      const password = this.password
      if (!username) return uni.showToast({ title: '请输入用户名或手机号', icon: 'none' })
      if (!password) return uni.showToast({ title: '请输入密码', icon: 'none' })
      if (password.length < 8) return uni.showToast({ title: '密码至少 8 位', icon: 'none' })

      this.isLoading = true
      try {
        const res = await authApi.login(username, password)
        const data = res.data || res
        if (!data.access_token) {
          return uni.showToast({ title: data.message || '登录失败', icon: 'none' })
        }

        // 1. token 入 store（store 会自动持久化到 uni.storage）
        this.$store.commit('setToken', data.access_token)
        // 1.1 登录账号入 store：优先用真实 username（手机号登录时也归一为 username），
        //     保证 quiz_completed_<account> / guide_onboarding_done_<account> 等本地键稳定
        const accountKey = (data.user && (data.user.username || data.user.phone)) || username
        this.$store.commit('setUsername', accountKey)
        // 2. 用户信息入 store
        if (data.user) {
          this.$store.commit('setUserInfo', {
            nickname: data.user.nickname || data.user.username || '',
            avatar: '',
            phone: data.user.phone || '',
            registerTime: '',
          })
        }

        uni.showToast({ title: '登录成功', icon: 'success' })

        // ↓↓↓ 新增：先从云端拉回该账号的测评结果（换设备/清缓存后靠它恢复） ↓↓↓
        try {
          const cloudResult = await fetchQuizResultFromCloud()
          if (cloudResult) {
            this.$store.commit('setPersonalityResult', cloudResult)
            this.$store.commit('setQuizCompleted', true)
          }
        } catch (e) {
          console.warn('云端测评结果拉取失败(按本地标记继续):', e && e.message)
        }
        // ↑↑↑ 新增结束 ↑↑↑

        // ↓↓↓ 新增：拉回该账号云端的金币/礼物/扭蛋券/账单（换设备不再清零） ↓↓↓
        try {
          await economy.pullFromCloud()
        } catch (e) {
          console.warn('云端经济数据拉取失败(按本地数据继续):', e && e.message)
        }
        // ↑↑↑ 新增结束 ↑↑↑

        // ↓↓↓ 新增：拉回盲盒 / 碎片 / 明信片玩法数据 ↓↓↓
        try {
          await playSync.pullAll()
        } catch (e) {
          console.warn('云端玩法数据拉取失败(按本地数据继续):', e && e.message)
        }
        // ↑↑↑ 新增结束 ↑↑↑

        setTimeout(() => {
          // 测评完成标记按账号区分：该账号没做过测评就走性格测试，做完直接进「陪伴」首页
          const quizDone = uni.getStorageSync('quiz_completed_' + username) === 'true'
          this.redirectAfterLogin(quizDone ? '/pages/index/index' : '/pages/personality-quiz/personality-quiz', username)
        }, 800)
      } catch (e) {
        uni.showToast({ title: e.message || '登录失败', icon: 'none' })
      } finally {
        this.isLoading = false
      }
    },

    goRegister() {
      uni.navigateTo({ url: '/pages/login/register' })
    },

    /** 忘记密码：短信验证码重置 */
    goRecover() {
      uni.navigateTo({ url: '/pages/login/recover' })
    },

    // ↓↓↓ 新增：微信登录成功处理（与账号密码登录的产物保持一致） ↓↓↓
    onWxLoginSuccess({ token, user }) {
      this.wxVisible = false
      if (token) this.$store.commit('setToken', token)
      if (user) {
        this.$store.commit('setUserInfo', {
          nickname: user.nickname || '微信用户',
          avatar: user.avatar || '',
          phone: '',
          registerTime: '',
        })
      }
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        this.redirectAfterLogin('/pages/index/index')
      }, 800)
    },
    // ↑↑↑ 新增结束 ↑↑↑

    // 登录成功后：首次登录先弹新手引导，引导关闭/跳过后再进入目标页
    // account：账号标识，与 quiz_completed_<username> 同规则，保证引导也是按账号隔离
    redirectAfterLogin(url, account = '') {
      this.guideAccount = account
      const key = account ? ('guide_onboarding_done_' + account) : 'guide_onboarding_done'
      let guideDone = false
      try {
        guideDone = uni.getStorageSync(key) === 'true'
      } catch (e) { /* 静默 */ }
      if (guideDone) {
        uni.reLaunch({ url })
        return
      }
      this.pendingUrl = url
      this.showGuide = true
    },
    onGuideFinish() {
      this.showGuide = false
      const url = this.pendingUrl
      this.pendingUrl = ''
      if (url) uni.reLaunch({ url })
    },
  },
}
</script>

<style lang="scss" scoped>
/* uni-input 包装层高度对齐设计稿 .val */
.xt-page.xt-s20 .field .val {
  display: block;
  width: 100%;
  height: 15px;
}

/* 设计稿 .auth-3rd span 改用 view 承载，补等价规则 */
.xt-page.xt-s20 .auth-3rd .third {
  flex: 1;
  padding: 9px 0;
  border-radius: 12px;
  text-align: center;
  font-size: 8.5px;
  color: #6A776E;
  background: #fff;
  box-shadow: 0 0 0 1px var(--v7-line);
}

/* 提交中禁用重复点击 */
.xt-page.xt-s20 .auth-btn.disabled {
  opacity: 0.72;
  pointer-events: none;
}
</style>
