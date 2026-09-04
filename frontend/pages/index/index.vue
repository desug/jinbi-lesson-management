<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">补课机构课时管理</text>
      <text class="hero-desc">请选择当前身份进入对应端口，后续所有功能都在这套现有项目中继续维护。</text>
    </view>

    <view class="section-card">
      <text class="section-title">角色选择</text>
      <view class="button-row">
        <view class="button-row__item">
          <button class="primary-btn" @click="goPage(routes.LOGIN)">学员端</button>
        </view>
        <view class="button-row__item">
          <button class="secondary-btn" @click="goPage(routes.ADMIN_LOGIN)">管理员端</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      routes: ROUTES
    }
  },
  methods: {
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    }
  }
}
</script>
