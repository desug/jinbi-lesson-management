<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">管理员登录</text>
      <text class="hero-desc">请输入管理员账号和密码进入管理端，可搜索学员并调整课时。</text>
    </view>

    <view class="section-card">
      <text class="section-title">登录信息</text>

      <view class="form-item">
        <text class="form-label">管理员账号</text>
        <input
          v-model="form.account"
          class="field-input"
          maxlength="20"
          placeholder="请输入管理员账号"
        />
      </view>

      <view class="form-item">
        <text class="form-label">登录密码</text>
        <view class="password-field">
          <input
            v-model="form.password"
            class="field-input password-input"
            type="text"
            :password="!showPassword"
            maxlength="32"
            placeholder="请输入管理员密码"
            confirm-type="done"
            @confirm="handleLogin"
          />
          <view class="password-toggle" @tap.stop="togglePassword">
            <text>{{ showPassword ? '隐藏' : '显示' }}</text>
          </view>
        </view>
        <view v-if="form.password" class="password-count">已输入 {{ form.password.length }} 位</view>
      </view>

      <button class="primary-btn" :loading="loading" :disabled="loading" @click="handleLogin">
        {{ loading ? '登录中' : '登录并进入工作台' }}
      </button>
    </view>

    <view class="section-card">
      <text class="section-title">其他入口</text>
      <view class="button-row">
        <view class="button-row__item">
          <button class="secondary-btn" @click="goPage(routes.LOGIN)">学员登录</button>
        </view>
        <view class="button-row__item">
          <button class="secondary-btn" @click="goPage(routes.INDEX)">角色选择</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { adminLogin } from '@/api/auth'
import { ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      routes: ROUTES,
      loading: false,
      showPassword: false,
      form: {
        account: 'admin',
        password: ''
      }
    }
  },
  onShow: function() {
    // 每次重新进入管理员登录页都清空密码，账号预填沿用原设计。
    this.form.password = ''
    this.showPassword = false
  },
  methods: {
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    },
    togglePassword: function() {
      this.showPassword = !this.showPassword
    },
    validateForm: function() {
      if (!this.form.account) {
        uni.showToast({
          title: '请输入管理员账号',
          icon: 'none'
        })
        return false
      }

      if (!this.form.password || this.form.password.length < 6) {
        uni.showToast({
          title: '请输入不少于六位的登录密码',
          icon: 'none'
        })
        return false
      }

      return true
    },
    handleLogin: async function() {
      if (this.loading || !this.validateForm()) {
        return
      }

      this.loading = true

      try {
        await adminLogin(this.form.account, this.form.password)
        this.form.password = ''
        this.showPassword = false

        uni.showToast({
          title: '登录成功',
          icon: 'none'
        })

        setTimeout(function() {
          uni.reLaunch({
            url: ROUTES.ADMIN_HOME
          })
        }, 300)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.password-field {
  position: relative;
}

.password-input {
  padding-right: 132rpx;
}

.password-toggle {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 100%;
  min-height: 82rpx;
  font-size: 25rpx;
  color: #2962ff;
}

.password-count {
  margin-top: 12rpx;
  font-size: 23rpx;
  color: #64748b;
}
</style>
