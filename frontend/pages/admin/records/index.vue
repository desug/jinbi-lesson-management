<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="记录加载失败"
      :description="pageError"
      :button-text="studentId ? '重新加载' : ''"
      @action="loadData"
    />

    <view v-else>
      <view class="hero-card">
        <text class="hero-title">{{ studentName }}的全部记录</text>
        <text class="hero-desc">这里展示指定学生的完整课时变动历史，便于管理员查看调整结果。</text>
      </view>

      <view class="record-section">
        <view v-if="records.length" class="record-list">
          <view
            v-for="item in records"
            :key="item.id"
            :class="['record-card', item.changeTypeValue === 'deduct' ? 'record-card--deduct' : 'record-card--add']"
          >
            <view class="record-card__head">
              <view class="record-card__title-wrap">
                <text :class="['record-card__tag', item.changeTypeValue === 'deduct' ? 'record-card__tag--deduct' : 'record-card__tag--add']">
                  {{ item.changeTypeText }}
                </text>
                <text class="record-card__subject">{{ item.subjectName || '综合' }}</text>
              </view>
              <text :class="['record-card__hours', item.changeTypeValue === 'deduct' ? 'record-card__hours--deduct' : 'record-card__hours--add']">
                {{ item.hoursText }}
              </text>
            </view>

            <view class="record-card__grid">
              <view class="record-card__field">
                <text class="record-card__label">金额</text>
                <text class="record-card__value">{{ item.amountText || '¥0.00' }}</text>
              </view>
              <view class="record-card__field">
                <text class="record-card__label">剩余课时</text>
                <text :class="['record-card__value', Number(item.remainingHours) < 0 ? 'is-negative' : '']">
                  {{ item.remainingHoursText || item.remainingHours || 0 }}
                </text>
              </view>
            </view>

            <view class="record-card__line">
              <text class="record-card__label">时间</text>
              <text class="record-card__line-value">{{ item.time || '-' }}</text>
            </view>
            <view class="record-card__line">
              <text class="record-card__label">备注</text>
              <text class="record-card__line-value">{{ item.remarkText || '-' }}</text>
            </view>
          </view>
        </view>

        <empty-block
          v-else
          title="暂无课时记录"
          description="当前学员还没有课时变动记录。"
        />
      </view>
    </view>
  </view>
</template>

<script>
import { getAdminStudentDetail } from '@/api/admin'
import { normalizeRecords } from '@/api/transform'
import request from '@/utils/request'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

const pickRecordsFromResponse = function(res) {
  let list = []

  if (Array.isArray(res)) {
    list = res
  } else if (res && Array.isArray(res.data)) {
    list = res.data
  } else if (res && res.data && Array.isArray(res.data.data)) {
    list = res.data.data
  } else if (res && res.success && Array.isArray(res.data)) {
    list = res.data
  } else if (res && res.data && Array.isArray(res.data.list)) {
    list = res.data.list
  } else if (res && res.data && res.data.data && Array.isArray(res.data.data.list)) {
    list = res.data.data.list
  }

  return list
}

export default {
  data: function() {
    return {
      studentId: '',
      pageError: '',
      studentName: '当前学员',
      records: [],
      hasLoaded: false,
      loading: false
    }
  },
  onLoad: function(options) {
    const routeOptions = options || {}
    console.log('[records page options]', routeOptions)
    this.studentId = routeOptions.studentId || routeOptions.id || ''
    this.studentName = this.decodeRouteText(routeOptions.name || routeOptions.studentName || '') || '当前学员'
    if (!this.studentId) {
      this.pageError = '缺少学生ID，无法加载课时记录'
      return
    }
    if (this.ensureAdminRole()) {
      this.loadData()
    }
  },
  onShow: function() {
    if (!this.ensureAdminRole()) {
      return
    }
    if (this.hasLoaded) {
      this.loadData()
    }
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
    decodeRouteText: function(value) {
      try {
        return decodeURIComponent(value || '')
      } catch (error) {
        return value || ''
      }
    },
    loadData: async function() {
      if (this.loading) {
        return
      }
      if (!this.studentId) {
        this.pageError = '缺少学生ID，无法加载课时记录'
        return
      }

      this.pageError = ''
      this.loading = true

      try {
        const res = await request({
          url: '/admin/students/' + this.studentId + '/records',
          method: 'GET'
        })
        console.log('[records api response]', res)

        const list = pickRecordsFromResponse(res)
        this.records = normalizeRecords(list)
        if (this.records.length && (!this.studentName || this.studentName === '当前学员')) {
          this.studentName = this.records[0].studentName || this.studentName
        }
        if (!this.records.length && (!this.studentName || this.studentName === '当前学员')) {
          this.loadStudentName()
        }
        this.hasLoaded = true
      } catch (error) {
        this.pageError = (error && error.message) || '记录加载失败'
      } finally {
        this.loading = false
      }
    },
    loadStudentName: async function() {
      try {
        const detailRes = await getAdminStudentDetail(this.studentId)
        const profile = detailRes && detailRes.data && detailRes.data.profile
        if (profile && profile.name) {
          this.studentName = profile.name
        }
      } catch (error) {
        console.warn('[records student name load failed]', error)
      }
    }
  },
  onPullDownRefresh: function() {
    this.loadData().finally(function() {
      uni.stopPullDownRefresh()
    })
  }
}
</script>

<style lang="scss" scoped>
.record-section {
  margin-bottom: 24rpx;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.record-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #ffffff;
  border: 1rpx solid #e7eef8;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.05);
}

.record-card--add {
  border-left: 8rpx solid #2962ff;
}

.record-card--deduct {
  border-left: 8rpx solid #ef4444;
}

.record-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.record-card__title-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
}

.record-card__tag {
  flex: 0 0 auto;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 700;
}

.record-card__tag--add {
  color: #ffffff;
  background: #2962ff;
}

.record-card__tag--deduct {
  color: #ffffff;
  background: #ef4444;
}

.record-card__subject {
  min-width: 0;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.35;
  color: #1f2937;
}

.record-card__hours {
  flex: 0 0 auto;
  min-width: 136rpx;
  padding: 10rpx 14rpx;
  border-radius: 18rpx;
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.25;
  text-align: center;
}

.record-card__hours--add {
  color: #2962ff;
  background: #eef4ff;
}

.record-card__hours--deduct {
  color: #ef4444;
  background: #fff1f2;
}

.record-card__grid {
  display: flex;
  gap: 14rpx;
  margin-top: 20rpx;
}

.record-card__field {
  flex: 1;
  min-width: 0;
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.record-card__label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.record-card__value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.35;
  color: #1f2937;
  word-break: break-all;
}

.record-card__value.is-negative {
  color: #e5484d;
}

.record-card__line {
  margin-top: 16rpx;
}

.record-card__line-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #475569;
  word-break: break-all;
}
</style>
