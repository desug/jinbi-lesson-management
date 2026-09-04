<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">{{ pageTitle }}</text>
      <text class="hero-desc">{{ pageDesc }}</text>
    </view>

    <view class="section-card">
      <text class="section-title">登录入口</text>
      <text class="section-desc">请选择当前入口。VIP班型入口仅用于 VIP 学员登录学生端。</text>

      <view class="login-entry-grid">
        <view
          :class="['login-entry', currentMode === 'student' ? 'login-entry--active' : '']"
          @click="switchMode('student')"
        >
          <text class="login-entry__title">学生登录</text>
          <text class="login-entry__desc">适用于普通学员和全部学员登录</text>
        </view>

        <view
          :class="[
            'login-entry',
            'login-entry--vip',
            currentMode === 'vip' ? 'login-entry--vip-active' : ''
          ]"
          @click="switchMode('vip')"
        >
          <text class="login-entry__title">VIP班型登录</text>
          <text class="login-entry__desc">仅支持 VIP 学员手机号进入学生端</text>
        </view>
      </view>

      <button class="secondary-btn login-entry-admin" @click="goPage(routes.ADMIN_LOGIN)">管理员登录</button>
    </view>

    <view class="section-card">
      <text class="section-title">登录信息</text>

      <view class="form-item">
        <text class="form-label">手机号码</text>
        <input
          v-model="form.phone"
          class="field-input"
          type="number"
          maxlength="11"
          placeholder="请输入绑定手机号"
        />
      </view>

      <view class="form-item">
        <text class="form-label">验证码</text>
        <input
          v-model="form.code"
          class="field-input"
          type="number"
          maxlength="4"
          placeholder="请输入四位验证码"
        />
      </view>

      <button :class="['primary-btn', currentMode === 'vip' ? 'primary-btn--vip' : '']" :loading="loading" @click="handleLogin">
        {{ submitText }}
      </button>
      <view :class="['placeholder-note', currentMode === 'vip' ? 'placeholder-note--vip' : '']">{{ demoText }}</view>
    </view>

    <view class="section-card">
      <text class="section-title">辅助入口</text>
      <view class="button-row">
        <view class="button-row__item">
          <button class="secondary-btn" @click="goPage(routes.INDEX)">角色选择</button>
        </view>
        <view class="button-row__item">
          <button class="secondary-btn" @click="switchMode('student')">恢复学生登录</button>
        </view>
      </view>
    </view>

    <view v-if="enrollmentVisible" class="enrollment-mask" @touchmove.stop.prevent>
      <view class="enrollment-dialog">
        <text class="enrollment-dialog__title">请选择班型</text>
        <text class="enrollment-dialog__desc">该手机号对应多条学员记录，请选择本次要查看的班型。</text>

        <scroll-view scroll-y class="enrollment-list">
          <view
            v-for="item in enrollmentOptions"
            :key="item.selectionKey"
            :class="['enrollment-option', selectedEnrollmentKey === item.selectionKey ? 'enrollment-option--active' : '']"
            @click="selectEnrollment(item)"
          >
            <text class="enrollment-option__name">{{ item.name }}｜{{ item.grade }}｜{{ item.classType }}</text>
            <text v-if="item.studentId" class="enrollment-option__id">学员 ID：{{ item.studentId }}</text>
          </view>
        </scroll-view>

        <view class="enrollment-actions">
          <button class="enrollment-btn enrollment-btn--cancel" :disabled="selectingEnrollment" @click="cancelEnrollment">
            取消
          </button>
          <button
            class="enrollment-btn enrollment-btn--confirm"
            :loading="selectingEnrollment"
            :disabled="selectingEnrollment || !selectedEnrollmentKey"
            @click="confirmEnrollment"
          >
            确认进入
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { studentLogin } from '@/api/auth'
import { extractBusinessError } from '@/utils/request'
import storage from '@/utils/storage'
import { ROUTES } from '@/utils/constants'

const INTERNAL_TEST_CODE = '1234'
const MULTIPLE_ENROLLMENTS_CODE = 'MULTIPLE_ENROLLMENTS'

const getErrorCandidates = function(error) {
  const businessError = extractBusinessError(error) || {}
  return [
    businessError,
    businessError.detail,
    businessError.detail && businessError.detail.data,
    businessError.data,
    businessError.data && businessError.data.detail,
    businessError.data && businessError.data.data,
    businessError.response && businessError.response.data,
    businessError.response && businessError.response.data && businessError.response.data.detail,
    businessError.response &&
      businessError.response.data &&
      businessError.response.data.detail &&
      businessError.response.data.detail.data,
    businessError.response && businessError.response.data && businessError.response.data.data,
    error
  ].filter(function(item) {
    return item && typeof item === 'object'
  })
}

const getBusinessErrorCode = function(error) {
  const candidates = getErrorCandidates(error)
  for (let index = 0; index < candidates.length; index += 1) {
    if (candidates[index].code) {
      return candidates[index].code
    }
  }
  return ''
}

const getEnrollmentStudents = function(error) {
  const candidates = getErrorCandidates(error)
  const listKeys = ['students', 'enrollments', 'options', 'list']
  for (let index = 0; index < candidates.length; index += 1) {
    for (let keyIndex = 0; keyIndex < listKeys.length; keyIndex += 1) {
      const list = candidates[index][listKeys[keyIndex]]
      if (Array.isArray(list)) {
        return list
      }
    }
  }
  return []
}

const normalizeEnrollmentOptions = function(students) {
  return (students || []).map(function(item, index) {
    const source = item || {}
    const studentId = source.studentId || source.student_id || source.id || ''
    const classType = source.classType || source.class_type || source.classTypeText || '未设置班型'
    return {
      studentId: studentId,
      name: source.name || source.studentName || '未设置姓名',
      grade: source.grade || '未设置年级',
      classType: classType,
      selectionKey: studentId ? 'student:' + studentId : 'class:' + classType + ':' + index
    }
  })
}

export default {
  data: function() {
    return {
      routes: ROUTES,
      loading: false,
      enrollmentVisible: false,
      enrollmentOptions: [],
      selectedEnrollmentKey: '',
      pendingLoginPhone: '',
      selectingEnrollment: false,
      currentMode: 'student',
      form: {
        phone: '19900000004',
        code: '1234'
      }
    }
  },
  computed: {
    // computed 会根据 currentMode 自动刷新页面文字，不需要手动 setData。
    pageTitle: function() {
      return this.currentMode === 'vip' ? 'VIP班型登录' : '学生登录'
    },
    pageDesc: function() {
      return this.currentMode === 'vip'
        ? '请输入已绑定的 VIP 学员手机号登录学生端，进入后查看个人课时数据。'
        : '请输入绑定手机号登录，登录后只能查看本人的课时数据。'
    },
    submitText: function() {
      return this.currentMode === 'vip' ? '登录并进入学生首页' : '登录并进入首页'
    },
    demoText: function() {
      return this.currentMode === 'vip'
        ? 'VIP 演示手机号可直接使用：19900000004、19900000006、19900000008。'
        : '演示手机号可直接使用：19900000004 ~ 19900000011。'
    }
  },
  methods: {
    switchMode: function(mode) {
      // 学生登录和 VIP 登录共用一个接口，区别是 VIP 模式登录后会额外检查班型。
      this.cancelEnrollment()
      this.currentMode = mode

      if (mode === 'vip') {
        this.form.phone = '19900000004'
      } else if (!this.form.phone) {
        this.form.phone = '19900000005'
      }

      this.form.code = '1234'
    },
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    },
    validateForm: function() {
      // 前端先做基础校验，可以减少无效请求，也能给用户更快反馈。
      const phone = String(this.form.phone || '').trim()
      const code = String(this.form.code || '').trim()

      if (!phone) {
        uni.showToast({
          title: '请输入手机号',
          icon: 'none'
        })
        return false
      }

      if (!/^\d{11}$/.test(phone)) {
        uni.showToast({
          title: '请输入正确手机号',
          icon: 'none'
        })
        return false
      }

      if (!code) {
        uni.showToast({
          title: '请输入验证码',
          icon: 'none'
        })
        return false
      }

      if (code !== INTERNAL_TEST_CODE) {
        uni.showToast({
          title: '验证码错误，内部测试验证码为 1234',
          icon: 'none'
        })
        return false
      }

      return true
    },
    handleLogin: async function() {
      // 防重复点击：loading 为 true 时直接 return，避免连续发多次登录请求。
      if (this.loading || !this.validateForm()) {
        return
      }

      this.loading = true

      try {
        // 真正的登录请求在 api/auth.js 里，那里会保存 token 和用户信息。
        const res = await studentLogin({
          phone: String(this.form.phone || '').trim()
        })
        this.finishLogin(res)
      } catch (error) {
        if (getBusinessErrorCode(error) === MULTIPLE_ENROLLMENTS_CODE) {
          const options = normalizeEnrollmentOptions(getEnrollmentStudents(error))
          if (!options.length) {
            uni.showToast({
              title: '未获取到可选班型，请稍后重试',
              icon: 'none'
            })
            return
          }
          this.pendingLoginPhone = String(this.form.phone || '').trim()
          this.enrollmentOptions = options
          this.selectedEnrollmentKey = ''
          this.enrollmentVisible = true
          return
        }
        uni.showToast({
          title: (error && error.message) || '登录失败，请稍后重试',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    finishLogin: function(res) {
      const student = res && res.data && res.data.student ? res.data.student : {}
      if (this.currentMode === 'vip' && student.classType !== 'VIP') {
        // VIP 入口只允许 VIP 学员进入；普通学员误进时清理登录态。
        storage.clearAuth()
        uni.showToast({
          title: '当前所选记录不是 VIP 学员，请切换学生登录入口',
          icon: 'none'
        })
        return false
      }

      this.enrollmentVisible = false
      this.enrollmentOptions = []
      this.selectedEnrollmentKey = ''
      this.pendingLoginPhone = ''
      uni.showToast({
        title: '登录成功',
        icon: 'none'
      })

      setTimeout(function() {
        // reLaunch 会关闭当前登录页，防止用户返回到登录页造成状态混乱。
        uni.reLaunch({
          url: ROUTES.STUDENT_HOME
        })
      }, 300)
      return true
    },
    selectEnrollment: function(item) {
      if (!this.selectingEnrollment && item) {
        this.selectedEnrollmentKey = item.selectionKey
      }
    },
    cancelEnrollment: function() {
      if (this.selectingEnrollment) {
        return
      }
      this.enrollmentVisible = false
      this.enrollmentOptions = []
      this.selectedEnrollmentKey = ''
      this.pendingLoginPhone = ''
    },
    confirmEnrollment: async function() {
      if (this.selectingEnrollment || !this.selectedEnrollmentKey) {
        return
      }
      const selected = this.enrollmentOptions.find(function(item) {
        return item.selectionKey === this.selectedEnrollmentKey
      }, this)
      if (!selected) {
        return
      }

      this.selectingEnrollment = true
      try {
        const payload = {
          phone: this.pendingLoginPhone
        }
        if (selected.studentId) {
          payload.studentId = selected.studentId
        } else {
          payload.classType = selected.classType
        }
        const res = await studentLogin(payload)
        this.finishLogin(res)
      } catch (error) {
        uni.showToast({
          title: (error && error.message) || '进入所选班型失败，请重试',
          icon: 'none'
        })
      } finally {
        this.selectingEnrollment = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.login-entry-grid {
  display: flex;
  margin: 20rpx -10rpx 24rpx;
}

.login-entry {
  flex: 1;
  margin: 0 10rpx;
  padding: 24rpx 22rpx;
  border-radius: 22rpx;
  border: 1rpx solid #dbe6ff;
  background: #f8fbff;
}

.login-entry--active {
  border-color: #7ea6ff;
  background: #eef4ff;
  box-shadow: 0 10rpx 24rpx rgba(41, 98, 255, 0.08);
}

.login-entry--vip {
  border-color: rgba(119, 122, 178, 0.18);
  background: linear-gradient(180deg, rgba(245, 244, 252, 1), rgba(239, 240, 248, 1));
}

.login-entry--vip-active {
  border-color: rgba(109, 118, 188, 0.4);
  box-shadow: 0 12rpx 26rpx rgba(109, 118, 188, 0.1);
}

.login-entry__title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #1f2937;
}

.login-entry__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.login-entry-admin {
  margin-top: 4rpx;
}

.primary-btn--vip {
  background: linear-gradient(135deg, #6b73b7 0%, #8b92cb 100%);
}

.placeholder-note--vip {
  background: rgba(109, 118, 188, 0.08);
  color: #5f689e;
}

.enrollment-mask {
  position: fixed;
  z-index: 1000;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(15, 23, 42, 0.48);
}

.enrollment-dialog {
  width: 100%;
  max-height: 78vh;
  padding: 36rpx 32rpx 30rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 24rpx 64rpx rgba(30, 64, 175, 0.18);
}

.enrollment-dialog__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #1e3a8a;
}

.enrollment-dialog__desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #64748b;
}

.enrollment-list {
  max-height: 48vh;
  margin-top: 24rpx;
}

.enrollment-option {
  margin-top: 16rpx;
  padding: 24rpx;
  border: 2rpx solid #dbeafe;
  border-radius: 20rpx;
  background: #f8fbff;
}

.enrollment-option--active {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.12);
}

.enrollment-option__name,
.enrollment-option__id {
  display: block;
}

.enrollment-option__name {
  font-size: 28rpx;
  font-weight: 600;
  color: #1e293b;
}

.enrollment-option__id {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.enrollment-actions {
  display: flex;
  margin: 30rpx -8rpx 0;
}

.enrollment-btn {
  flex: 1;
  margin: 0 8rpx;
  border-radius: 18rpx;
  font-size: 26rpx;
}

.enrollment-btn--cancel {
  color: #475569;
  background: #f1f5f9;
}

.enrollment-btn--confirm {
  color: #ffffff;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
}
</style>
