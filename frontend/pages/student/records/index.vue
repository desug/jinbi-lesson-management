<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="记录加载失败"
      :description="pageError"
      button-text="重新加载"
      @action="loadData"
    />

    <view v-else>
      <view class="hero-card">
        <text class="hero-title">课时变动记录</text>
        <text class="hero-desc">这里展示当前学员自己的全部课时变动记录，并提供各科课时汇总查看。</text>
        <view class="stat-grid">
          <view class="stat-card">
            <text class="stat-label">累计增加</text>
            <text class="stat-value">{{ summary.added }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-label">累计扣减</text>
            <text class="stat-value">{{ summary.deducted }}</text>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">课时记录</text>
          <text class="section-link">仅可查看本人数据</text>
        </view>
        <record-list
          :list="recordList"
          empty-title="暂无课时记录"
          empty-description="当前还没有课时变动记录。"
        />
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">科目课时汇总</text>
          <text class="section-link">查看当前课时情况</text>
        </view>
        <view v-if="subjectSummary.length" class="list-stack">
          <subject-hours-card
            v-for="item in subjectSummary"
            :key="item.subjectName || item.subject"
            :item="item"
          />
        </view>
        <empty-block
          v-else
          title="暂无课时汇总"
          description="当前还没有可展示的科目课时数据。"
        />
      </view>
    </view>
  </view>
</template>

<script>
import { getStudentRecords } from '@/api/student'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

export default {
  data: function() {
    return {
      pageError: '',
      summary: {
        added: 0,
        deducted: 0
      },
      recordList: [],
      subjectSummary: []
    }
  },
  onShow: function() {
    // onShow 每次页面显示都会执行；从别的页面回来时也能刷新最新课时。
    if (!this.ensureStudentRole()) {
      return
    }
    this.loadData()
  },
  methods: {
    ensureStudentRole: function() {
      // 学生页面只允许学生角色访问；如果当前不是学生，就回到学生登录页。
      if (storage.getRole() !== ROLE.STUDENT) {
        uni.reLaunch({
          url: ROUTES.LOGIN
        })
        return false
      }

      return true
    },
    loadData: async function() {
      // 页面只负责展示，数据获取和字段整理都放在 api/student.js 与 api/transform.js。
      this.pageError = ''

      try {
        const res = await getStudentRecords()
        // summary 是累计增加/扣减，recordList 是流水，subjectSummary 是各科余额。
        this.summary = res.data.summary
        this.recordList = res.data.list
        this.subjectSummary = res.data.subjectSummary || []
      } catch (error) {
        this.pageError = (error && error.message) || '课时记录加载失败'
      }
    }
  }
}
</script>
