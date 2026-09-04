<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="详情加载失败"
      :description="pageError"
      button-text="重新加载"
      @action="loadData"
    />

    <view v-else>
      <view class="hero-card">
        <view class="hero-head">
          <text class="hero-title">{{ detail.profile.name }}</text>
          <view class="hero-class">
            <class-type-tag :class-type="detail.profile.classType" theme="light" />
          </view>
        </view>
        <text class="hero-desc">可查看学员资料、班型、各科课时情况和最近记录，并继续执行加课时或扣课时。</text>
        <view class="stat-grid">
          <view class="stat-card">
            <text class="stat-label">总课时</text>
            <text class="stat-value">{{ detail.summary.totalHours }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-label">已扣除</text>
            <text class="stat-value">{{ detail.summary.deductedHours }}</text>
          </view>
          <view class="stat-card">
            <text class="stat-label">剩余课时</text>
            <text :class="['stat-value', Number(detail.summary.remainingHours) < 0 ? 'stat-value--negative' : '']">
              {{ detail.summary.remainingHours }}
            </text>
          </view>
        </view>
      </view>

      <view class="section-card">
        <text class="section-title">学员基础信息</text>
        <view class="info-row">
          <text class="info-label">学员编号</text>
          <text class="info-value">{{ detail.profile.id }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">联系电话</text>
          <text class="info-value">{{ detail.profile.phone }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">年级</text>
          <text class="info-value">{{ detail.profile.grade }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">学校</text>
          <text class="info-value">{{ detail.profile.school || '-' }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">班型</text>
          <text class="info-value">{{ detail.profile.classTypeText || '-' }}</text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">各科课时情况</text>
          <text class="section-link" @click="goRecords">查看全部记录</text>
        </view>
        <view class="list-stack">
          <subject-hours-card
            v-for="item in detail.subjects"
            :key="item.subjectName || item.subject"
            :item="item"
          />
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <text class="section-title">最近记录</text>
          <text class="section-link" @click="goRecords">查看全部</text>
        </view>
        <view v-if="detail.recentRecords && detail.recentRecords.length" class="recent-record-list">
          <view
            v-for="item in detail.recentRecords"
            :key="item.id"
            :class="['recent-record-item', item.changeTypeValue === 'deduct' ? 'recent-record-item--deduct' : 'recent-record-item--add']"
          >
            <view class="recent-record-item__content">
              <view class="recent-record-item__main">
                <text :class="['recent-record-item__type', item.changeTypeValue === 'deduct' ? 'recent-record-item__type--deduct' : 'recent-record-item__type--add']">
                  {{ item.changeTypeText }}
                </text>
                <text :class="['recent-record-item__hours', item.changeTypeValue === 'deduct' ? 'recent-record-item__hours--deduct' : 'recent-record-item__hours--add']">
                  {{ item.hoursText }}
                </text>
              </view>
              <text :class="['recent-record-item__meta', Number(item.remainingHours) < 0 ? 'is-negative' : '']">
                剩余课时：{{ item.remainingHoursText || item.remainingHours || 0 }}
              </text>
              <text class="recent-record-item__meta">备注：{{ item.remarkText || '-' }}</text>
            </view>
            <text class="recent-record-item__time">{{ formatRecentTime(item.time) }}</text>
          </view>
        </view>
        <empty-block
          v-else
          title="暂无最近记录"
          description="当前学员还没有课时变动记录。"
        />
      </view>

      <view class="section-card">
        <view class="button-row">
          <view class="button-row__item">
            <button class="primary-btn" @click="goAdjust('增加')">加课时</button>
          </view>
          <view class="button-row__item">
            <button class="secondary-btn" @click="goAdjust('扣减')">扣课时</button>
          </view>
        </view>
        <view class="button-row" style="margin-top: 20rpx;">
          <view class="button-row__item">
            <button class="secondary-btn" @click="goRecords">查看全部记录</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getAdminStudentDetail, getAdminStudentRecords } from '@/api/admin'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

const createDefaultData = function() {
  return {
    profile: {},
    summary: {
      totalHours: 0,
      deductedHours: 0,
      remainingHours: 0
    },
    subjects: [],
    recentRecords: []
  }
}

export default {
  data: function() {
    return {
      studentId: '',
      pageError: '',
      detail: createDefaultData()
    }
  },
  onLoad: function(options) {
    const routeOptions = options || {}
    this.studentId = routeOptions.studentId || routeOptions.id || ''
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
      if (!this.studentId) {
        this.pageError = '未传入学员编号'
        return
      }

      this.pageError = ''

      try {
        const detailRes = await getAdminStudentDetail(this.studentId)
        const recordsRes = await getAdminStudentRecords(this.studentId)
        this.detail = Object.assign({}, detailRes.data, {
          recentRecords: recordsRes.data.list.slice(0, 5)
        })
      } catch (error) {
        this.pageError = (error && error.message) || '学员详情加载失败'
      }
    },
    formatRecentTime: function(value) {
      const text = String(value || '')
      return text.length >= 16 ? text.slice(0, 16) : text || '-'
    },
    goAdjust: function(mode) {
      uni.navigateTo({
        url: ROUTES.ADMIN_ADJUST_HOURS + '?id=' + this.studentId + '&mode=' + mode
      })
    },
    goRecords: function() {
      const studentId = this.studentId || (this.detail.profile && this.detail.profile.id)
      const studentName = encodeURIComponent((this.detail.profile && this.detail.profile.name) || '')
      uni.navigateTo({
        url: ROUTES.ADMIN_RECORDS + '?studentId=' + studentId + '&name=' + studentName
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

.hero-class {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12rpx;
}

.stat-value--negative {
  color: #ffb4ae;
}

.hero-class__text {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 104rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
}

.hero-class__text--small {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.18);
}

.recent-record-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.recent-record-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #f8fafc;
  border: 1rpx solid #e7eef8;
}

.recent-record-item__content {
  flex: 1;
  min-width: 0;
}

.recent-record-item--add {
  border-left: 6rpx solid #2962ff;
}

.recent-record-item--deduct {
  border-left: 6rpx solid #ef4444;
}

.recent-record-item__main {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.recent-record-item__meta {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.5;
  color: #64748b;
  word-break: break-all;
}

.recent-record-item__meta.is-negative {
  color: #e5484d;
  font-weight: 600;
}

.recent-record-item__type {
  flex: 0 0 auto;
  padding: 7rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 700;
  color: #ffffff;
}

.recent-record-item__type--add {
  background: #2962ff;
}

.recent-record-item__type--deduct {
  background: #ef4444;
}

.recent-record-item__hours {
  min-width: 0;
  font-size: 27rpx;
  line-height: 1.35;
  font-weight: 800;
}

.recent-record-item__hours--add {
  color: #2962ff;
}

.recent-record-item__hours--deduct {
  color: #ef4444;
}

.recent-record-item__time {
  flex: 0 0 auto;
  font-size: 23rpx;
  color: #64748b;
}
</style>
