<template>
  <view class="xt-page xt-s56">
    <view class="body">
      <!-- 页头 -->
      <view class="chat-head" style="padding:2px 2px 12px">
        <navigator class="back" open-type="navigateBack"><xt-icon name="i-left" /></navigator>
        <view class="chat-meta">
          <view class="chat-name">编辑资料</view>
          <view class="chat-st">她会记住你写下的每一句</view>
        </view>
        <text class="icon-btn" style="font-size:8px;font-weight:800;color:var(--v7-green)" @click="saveProfile">保存</text>
      </view>

      <!-- 头像 -->
      <view style="display:flex;flex-direction:column;align-items:center;padding:6px 0 14px">
        <view style="position:relative;width:78px;height:78px" @click="changeAvatar">
          <image v-if="userForm.avatar" class="avatar-img" :src="userForm.avatar" mode="aspectFill" />
          <view v-else class="avatar-ph"><text class="avatar-t">{{ userInitial }}</text></view>
          <view class="avatar-edit"><xt-icon name="i-edit" size="11" /></view>
        </view>
        <text style="margin-top:8px;font-size:7.5px;color:#AEB6AE">{{ uploading ? '正在上传…' : '这个头像只有你自己能看到' }}</text>
      </view>

      <!-- 资料字段 -->
      <view class="field">
        <view class="lab">昵称</view>
        <input
          v-model="userForm.nickname"
          class="val"
          type="text"
          maxlength="20"
          placeholder="请输入昵称"
          placeholder-style="color:#CFD6CE"
        />
      </view>

      <view class="field">
        <view class="lab">一句话介绍自己</view>
        <textarea
          v-model="userForm.signature"
          class="val area"
          maxlength="100"
          placeholder="写下你的个性签名..."
          placeholder-style="color:#CFD6CE"
          :auto-height="true"
        />
      </view>

      <!-- ↓↓↓ 修改 ↓↓↓ 原来这里写死了 disabled，导致手机号永远填不进去；现改为可编辑 + 保存时校验 -->
      <view class="field">
        <view class="row2">
          <view style="flex:1">
            <view class="lab">手机号（选填）</view>
            <!-- 注意：不能用 type=number，H5 下会把 11 位手机号当数值处理，
                 出现精度/溢出问题（实测 13800138000 显示成 13800137728）。用 text + 保存时正则校验。 -->
            <input
              v-model="userForm.phone"
              class="val"
              type="text"
              maxlength="11"
              placeholder="请输入 11 位手机号"
              placeholder-style="color:#CFD6CE"
            />
          </view>
          <text class="code">仅用于找回</text>
        </view>
      </view>
      <!-- ↑↑↑ 修改 ↑↑↑ -->

      <view class="auth-btn" style="margin-top:12px" @click="saveProfile">保存</view>
    </view>
  </view>
</template>

<script>
import userApi from '@/api/user'
// ↓↓↓ 新增 ↓↓↓ 用它的 toStaticUrl 拼头像地址，避开后端硬编码的局域网 IP
import http from '@/common/request'
// ↑↑↑ 新增 ↑↑↑
import XtIcon from '@/components/xt-icon/xt-icon.vue'

const PHONE_RE = /^1[3-9]\d{9}$/

export default {
  components: { XtIcon },
  data() {
    return {
      // ↓↓↓ 新增 ↓↓↓ 上传中标记，防止连点
      uploading: false,
      // ↑↑↑ 新增 ↑↑↑
      userForm: {
        nickname: '',
        avatar: '',
        signature: '',
        phone: ''
      }
    }
  },
  computed: {
    userInitial() {
      const name = this.userForm.nickname || '用'
      return name.charAt(0)
    }
  },
  onShow() {
    this.loadUserInfo()
    // ↓↓↓ 新增 ↓↓↓ 以云端为准回填（手机号/签名存在库里，本地 store 可能是空的）
    this.fetchProfile()
    // ↑↑↑ 新增 ↑↑↑
  },
  methods: {
    loadUserInfo() {
      const storeUser = this.$store.state.userInfo || {}
      this.userForm = {
        nickname: storeUser.nickname || '',
        avatar: storeUser.avatar || '',
        signature: storeUser.signature || '',
        phone: storeUser.phone || ''
      }
    },

    // ↓↓↓ 新增 ↓↓↓ 拉取云端资料，失败静默沿用本地
    async fetchProfile() {
      try {
        const res = await userApi.getProfile()
        const d = (res && res.data) || res
        if (!d || d.is_guest) return
        this.userForm = {
          nickname: d.nickname || this.userForm.nickname || '',
          // 头像可能是相对路径（avatar/xxx.jpg）也可能是绝对 URL，统一过一遍
          avatar: http.toStaticUrl(d.avatar || ''),
          signature: d.signature || '',
          phone: d.phone || ''
        }
        this.$store.commit('setUserInfo', this.userForm)
      } catch (e) {
        console.warn('[profile-edit] 云端资料拉取失败，沿用本地缓存:', e && e.message)
      }
    },
    // ↑↑↑ 新增 ↑↑↑

    // ↓↓↓ 修改 ↓↓↓ 原来只把临时路径塞进表单（H5 是 blob: 地址，一刷新就没了，也从来没上传过服务器）
    // 现在：chooseImage → 上传 /user/avatar → 用返回的服务器地址
    changeAvatar() {
      if (this.uploading) return
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: async (res) => {
          const tempFilePath = res.tempFilePaths && res.tempFilePaths[0]
          if (!tempFilePath) {
            uni.showToast({ title: '选择图片失败', icon: 'none' })
            return
          }
          this.uploading = true
          uni.showLoading({ title: '上传中...', mask: true })
          try {
            const up = await userApi.uploadAvatar(tempFilePath)
            const d = (up && up.data) || up || {}
            // 优先用相对 path 自己拼前缀（H5 走 vite 代理），后端返回的 url 带硬编码局域网 IP，可能不通
            const url = http.toStaticUrl(d.path) || d.url || d.avatar || ''
            if (!url) throw new Error('上传返回地址为空')
            this.userForm.avatar = url
            // 头像接口已写库，这里同步 store 让其它页面立刻生效
            this.$store.commit('setUserInfo', { avatar: url })
            uni.hideLoading()
            uni.showToast({ title: '头像已更换', icon: 'success' })
          } catch (e) {
            uni.hideLoading()
            const msg = (e && e.message) || '头像上传失败'
            uni.showToast({ title: msg, icon: 'none', duration: 2500 })
          } finally {
            this.uploading = false
          }
        },
        fail: () => {
          uni.showToast({ title: '选择图片失败', icon: 'none' })
        }
      })
    },
    // ↑↑↑ 修改 ↑↑↑

    async saveProfile() {
      if (!this.userForm.nickname.trim()) {
        uni.showToast({ title: '请输入昵称', icon: 'none' })
        return
      }
      // ↓↓↓ 新增 ↓↓↓ 手机号校验（留空表示不填）
      const phone = (this.userForm.phone || '').trim()
      if (phone && !PHONE_RE.test(phone)) {
        uni.showToast({ title: '手机号格式不正确', icon: 'none' })
        return
      }
      // ↑↑↑ 新增 ↑↑↑
      uni.showLoading({ title: '保存中...' })
      try {
        const payload = {
          nickname: this.userForm.nickname.trim(),
          avatar: this.userForm.avatar || '',
          signature: this.userForm.signature || '',
          phone: phone
        }
        const res = await userApi.updateProfile(payload)
        const d = (res && res.data) || {}
        // ↓↓↓ 修改 ↓↓↓ 以服务端回传为准（后端会做手机号查重、签名截断等）
        this.$store.commit('setUserInfo', {
          nickname: d.nickname || payload.nickname,
          avatar: http.toStaticUrl(d.avatar || payload.avatar),
          signature: d.signature !== undefined && d.signature !== null ? d.signature : payload.signature,
          phone: d.phone !== undefined && d.phone !== null ? d.phone : payload.phone
        })
        // ↑↑↑ 修改 ↑↑↑
        uni.hideLoading()
        uni.showToast({ title: '保存成功', icon: 'success' })
        setTimeout(() => {
          uni.navigateBack()
        }, 1000)
      } catch (e) {
        uni.hideLoading()
        const errMsg = typeof e === 'object' ? (e.message || '保存失败') : '保存失败'
        uni.showToast({ title: errMsg, icon: 'none', duration: 2500 })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间 */
.xt-page.xt-s56 .body {
  padding-bottom: calc(24px + env(safe-area-inset-bottom));
}

/* 设计稿 img 尺寸同步到 uni-image 包装层 */
.xt-page.xt-s56 .avatar-img {
  display: block;
  width: 78px;
  height: 78px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 0 0 3px var(--v7-card), 0 12px 24px -16px rgba(62, 93, 74, 0.6);
}
.xt-page.xt-s56 .avatar-img :deep(div),
.xt-page.xt-s56 .avatar-img :deep(img) {
  width: 100%;
  height: 100%;
}
.xt-page.xt-s56 .avatar-img :deep(img) {
  object-fit: cover;
}

/* 未上传头像时的首字母兜底 */
.xt-page.xt-s56 .avatar-ph {
  width: 78px;
  height: 78px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #9CBFAA 0%, #3C5248 100%);
  box-shadow: 0 0 0 3px var(--v7-card), 0 12px 24px -16px rgba(62, 93, 74, 0.6);
}
.xt-page.xt-s56 .avatar-t {
  font-size: 26px;
  font-weight: 700;
  color: #F8F3E7;
}

.xt-page.xt-s56 .avatar-edit {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--v7-green);
  color: #ffffff;
  border: 2px solid var(--v7-card);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* uni-input 包装层尺寸对齐设计稿 .val */
.xt-page.xt-s56 .field .val {
  display: block;
  width: 100%;
  height: 15px;
}

/* 多行签名：改 textarea 后需要放开高度 */
.xt-page.xt-s56 .field .val.area {
  height: auto;
  min-height: 32px;
  padding-top: 2px;
  line-height: 1.6;
}
.xt-page.xt-s56 .field .val.area :deep(textarea) {
  height: auto;
  min-height: 32px;
  font-size: 10px;
  line-height: 1.6;
  color: #22302A;
  background: transparent;
}
</style>
