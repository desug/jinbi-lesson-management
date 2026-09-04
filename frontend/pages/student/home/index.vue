<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="页面加载失败"
      :description="pageError"
      button-text="重新加载"
      @action="loadData"
    />

    <view v-else>
      <view class="hero-card">
        <view class="hero-head">
          <text class="hero-title">{{ homeData.welcome }}</text>
          <class-type-tag :class-type="homeData.profile.classType" theme="light" />
        </view>
        <text class="hero-desc">这里可查看学员个人信息、各科课时明细和最近五条课时记录。</text>
        <view class="stat-grid">
          <view class="stat-card">
            <text class="stat-label">总课时</text>
            <text class="stat-value">{{ homeData.summary.totalHours }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-label">已扣除</text>
            <text class="stat-value">{{ homeData.summary.deductedHours }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-label">剩余课时</text>
            <text :class="['stat-value', Number(homeData.summary.remainingHours) < 0 ? 'stat-value--negative' : '']">
              {{ homeData.summary.remainingHours }}
            </text>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">个人信息</text>
          <text class="section-link" @click="goPage(routes.STUDENT_PROFILE)">查看资料</text>
        </view>
        <view class="info-row">
          <text class="info-label">学员姓名</text>
          <text class="info-value">{{ homeData.profile.name }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">学员编号</text>
          <text class="info-value">{{ homeData.profile.id }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">联系电话</text>
          <text class="info-value">{{ homeData.profile.phone }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">所属校区</text>
          <text class="info-value">{{ homeData.profile.campus }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">当前班型</text>
          <text class="info-value">{{ homeData.profile.classTypeText || '未设置班型' }}</text>
        </view>
      </view>

      <view class="section-card">
        <text class="section-title">快捷入口</text>
        <view class="quick-grid">
          <view class="quick-item" @click="goPage(routes.STUDENT_RECORDS)">
            <text class="quick-item__label">课时记录</text>
            <text class="quick-item__desc">查看全部课时变动记录</text>
          </view>
          <view class="quick-item" @click="goPage(routes.STUDENT_PAYMENTS)">
            <text class="quick-item__label">缴费记录</text>
            <text class="quick-item__desc">二期开放，当前仅保留入口</text>
          </view>
          <view class="quick-item" @click="goPage(routes.STUDENT_AI)">
            <text class="quick-item__label">智能助手</text>
            <text class="quick-item__desc">敬请期待，后续开放</text>
          </view>
          <view class="quick-item" @click="goPage(routes.STUDENT_GALLERY)">
            <text class="quick-item__label">图片查看</text>
            <text class="quick-item__desc">查看图片占位卡片</text>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">科目课时明细</text>
          <text class="section-link" @click="goPage(routes.STUDENT_RECORDS)">查看记录</text>
        </view>
        <view class="list-stack">
          <subject-hours-card
            v-for="item in homeData.subjects"
            :key="item.subjectName || item.subject"
            :item="item"
          />
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">最近五条记录</text>
          <text class="section-link" @click="goPage(routes.STUDENT_RECORDS)">查看全部</text>
        </view>
        <record-list
          :list="homeData.latestRecords"
          empty-title="暂无课时记录"
          empty-description="当前还没有课时变动记录。"
        />
      </view>
    </view>
  </view>
</template>

<script>
import { getStudentProfile, getStudentRecords } from '@/api/student'
import { buildStudentHomeData } from '@/api/transform'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

const createDefaultData = function() {
  return {
    welcome: '欢迎回来',
    profile: {},
    summary: {
      totalHours: 0,
      deductedHours: 0,
      remainingHours: 0
    },
    subjects: [],
    latestRecords: []
  }
}

export default {
  data: function() {
    return {
      routes: ROUTES,
      pageError: '',
      homeData: createDefaultData()
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
        const profileRes = await getStudentProfile()
        const recordsRes = await getStudentRecords()
        this.homeData = buildStudentHomeData(profileRes.data, recordsRes.data.list)
      } catch (error) {
        this.pageError = (error && error.message) || '首页数据加载失败'
      }
    },
    goPage: function(url) {
      uni.navigateTo({
        url: url
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.hero-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.stat-value--negative {
  color: #ffb4ae;
}
</style>
