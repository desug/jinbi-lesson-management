<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-title">图片查看</text>
      <text class="hero-desc">这里先展示图片占位卡片，后续可接入真实图片预览与查看能力。</text>
    </view>

    <view class="section-card">
      <view v-if="galleryList.length" class="list-stack">
        <view v-for="item in galleryList" :key="item.id" class="placeholder-card">
          <text class="section-title">{{ item.title }}</text>
          <text class="section-desc">{{ item.description }}</text>
        </view>
      </view>
      <empty-block
        v-else
        title="暂无图片内容"
        description="当前学员还没有可展示的图片内容。"
      />
    </view>
  </view>
</template>

<script>
import { getStudentGallery } from '@/api/student'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      galleryList: []
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
      const res = await getStudentGallery()
      this.galleryList = res.data.list || []
    }
  }
}
</script>
