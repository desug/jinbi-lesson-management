<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="资料加载失败"
      :description="pageError"
      button-text="重新加载"
      @action="loadData"
    />

    <view v-else>
      <view class="hero-card">
        <text class="hero-title">我的资料</text>
        <text class="hero-desc">当前页面展示学员的基础信息，仅可查看本人数据。</text>
      </view>

      <view class="section-card">
        <view class="info-row">
          <text class="info-label">学员编号</text>
          <text class="info-value">{{ profile.id }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">学员姓名</text>
          <text class="info-value">{{ profile.name }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">家长姓名</text>
          <text class="info-value">{{ profile.parentName }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">联系电话</text>
          <text class="info-value">{{ profile.phone }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">年级</text>
          <text class="info-value">{{ profile.grade }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">所属校区</text>
          <text class="info-value">{{ profile.campus }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">专属顾问</text>
          <text class="info-value">{{ profile.adviser }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">学习科目</text>
          <text class="info-value">{{ subjectText }}</text>
        </view>
      </view>

      <view class="section-card">
        <view class="button-row">
          <view class="button-row__item">
            <button class="secondary-btn" @click="goPage(routes.STUDENT_HOME)">返回首页</button>
          </view>
          <view class="button-row__item">
            <button class="danger-btn" @click="handleLogout">退出登录</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { logout } from '@/api/auth'
import { getStudentProfile } from '@/api/student'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      routes: ROUTES,
      pageError: '',
      profile: {}
    }
  },
  computed: {
    subjectText: function() {
      return (this.profile.subjects || [])
        .map(function(item) {
          return item.subjectName || item.subject || item
        })
        .join('、')
    }
  },
  onShow: function() {
    if (!this.ensureStudentRole()) {
      return
    }
    this.loadData()
  },
  methods: {
    ensureStudentRole: function() {
      if (storage.getRole() !== ROLE.STUDENT) {
        uni.reLaunch({
          url: ROUTES.LOGIN
        })
        return false
      }

      return true
    },
    loadData: async function() {
      this.pageError = ''

      try {
        const res = await getStudentProfile()
        this.profile = res.data
      } catch (error) {
        this.pageError = (error && error.message) || '资料加载失败'
      }
    },
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    },
    handleLogout: function() {
      uni.showModal({
        title: '退出提示',
        content: '确认退出当前学员账号吗？',
        confirmText: '确认退出',
        cancelText: '继续查看',
        success: async function(res) {
          if (!res.confirm) {
            return
          }

          await logout()
          storage.clearAuth()
          uni.reLaunch({
            url: ROUTES.LOGIN
          })
        }
      })
    }
  }
}
</script>
