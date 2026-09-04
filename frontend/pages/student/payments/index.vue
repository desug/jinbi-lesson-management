<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">{{ pageData.title }}</text>
      <text class="hero-desc">{{ pageData.description }}</text>
    </view>

    <view class="section-card">
      <empty-block
        title="二期开放"
        description="缴费记录、票据查看和到账确认功能将在后续版本开放。"
      />
    </view>
  </view>
</template>

<script>
import { getStudentPayments } from '@/api/student'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      pageData: {
        title: '缴费记录',
        description: '功能正在建设中。'
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
      const res = await getStudentPayments()
      this.pageData = res.data
    }
  }
}
</script>
