<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">管理工作台</text>
      <text class="hero-desc">管理员可在这里查看学员概览，并进入学员列表进行搜索和课时调整。</text>
      <view class="stat-grid">
        <view class="stat-card">
          <text class="stat-label">学员总数</text>
          <text class="stat-value">{{ summary.studentCount }}</text>
        </view>
        <view class="stat-card">
          <text class="stat-label">需关注学员</text>
          <text class="stat-value">{{ summary.warningCount }}</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <button class="primary-btn" @click="goPage(routes.ADMIN_STUDENTS)">进入学员列表</button>
      <view class="placeholder-note">课时调整、查看记录等管理操作都从学员列表进入。</view>
    </view>
  </view>
</template>

<script>
import { getAdminHome } from '@/api/admin'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      routes: ROUTES,
      summary: {
        studentCount: 0,
        warningCount: 0
      }
    }
  },
  onShow: function() {
    if (!this.ensureAdminRole()) {
      return
    }
    this.loadData()
  },
  methods: {
    ensureAdminRole: function() {
      if (storage.getRole() !== ROLE.ADMIN) {
        uni.reLaunch({
          url: ROUTES.ADMIN_LOGIN
        })
        return false
      }

      return true
    },
    loadData: async function() {
      const res = await getAdminHome()
      this.summary = res.data.summary
    },
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    }
  }
}
</script>
