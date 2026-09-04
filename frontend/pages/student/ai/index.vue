<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">{{ pageData.title }}</text>
      <text class="hero-desc">{{ pageData.description }}</text>
    </view>

    <view class="section-card">
      <empty-block
        title="敬请期待"
        description="智能助手后续将支持学习建议、课时分析和沟通摘要。"
      />
    </view>
  </view>
</template>

<script>
import { getStudentAi } from '@/api/student'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      pageData: {
        title: '智能助手',
        description: '功能正在规划中。'
      }
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
      const res = await getStudentAi()
      this.pageData = res.data
    }
  }
}
</script>
