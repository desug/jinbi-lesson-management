<template>
  <view class="student-card" @click="handleClick">
    <view class="section-head">
      <view class="student-card__main">
        <text class="section-title">{{ student.name }}</text>
        <text class="student-card__meta">{{ student.grade }} ｜ {{ student.school || student.campus }}</text>
      </view>
      <text :class="['soft-tag', remainingHoursClass]">
        {{ Number(student.remainingHours) < 0 ? '欠课时 ' : '剩余 ' }}{{ student.remainingHours }} 课时
      </text>
    </view>

    <view class="info-row">
      <text class="info-label">联系电话</text>
      <text class="info-value">{{ student.phone }}</text>
    </view>

    <view class="info-row">
      <text class="info-label">班型</text>
      <view class="student-card__class-wrap">
        <class-type-tag :class-type="student.classType" />
      </view>
    </view>

    <view class="info-row">
      <text class="info-label">学习科目</text>
      <text class="info-value">{{ subjectText }}</text>
    </view>

    <view class="info-row">
      <text class="info-label">科目课时概览</text>
      <text class="info-value">{{ student.subjectOverview || '暂无课时信息' }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'StudentCard',
  props: {
    student: {
      type: Object,
      default: function() {
        return {}
      }
    }
  },
  computed: {
    remainingHoursClass: function() {
      const value = Number(this.student.remainingHours)
      if (value < 0) {
        return 'soft-tag--negative'
      }
      return value === 0 ? 'soft-tag--zero' : ''
    },
    subjectText: function() {
      const subjects = this.student.subjects

      if (Array.isArray(subjects)) {
        const text = subjects
          .map(function(item) {
            return item.subjectName || item.subject || ''
          })
          .filter(function(item) {
            return !!item
          })
          .join('、')

        return text || '暂无科目'
      }

      return this.student.subjectNames || subjects || '暂无科目'
    }
  },
  methods: {
    handleClick: function() {
      this.$emit('click', this.student)
    }
  }
}
</script>

<style lang="scss" scoped>
.student-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.05);
}

.student-card__main {
  max-width: calc(100% - 180rpx);
}

.student-card__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #64748b;
}

.student-card__class-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12rpx;
}

.student-card__class-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 104rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
}

.student-card__class-tag--small {
  color: #54657f;
  background: #f1f5f9;
}

.soft-tag--negative {
  color: #e5484d;
  background: #fff1f2;
}

.soft-tag--zero {
  color: #64748b;
  background: #f1f5f9;
}
</style>
