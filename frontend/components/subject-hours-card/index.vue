<template>
  <view class="subject-card">
    <view class="section-head">
      <text class="section-title">{{ subjectName }}</text>
      <text :class="['soft-tag', isNegative ? 'soft-tag--negative' : '']">{{ statusText }}</text>
    </view>

    <view class="subject-card__grid">
      <view class="subject-card__item">
        <text class="subject-card__label">共计学时</text>
        <text class="subject-card__value">{{ item.totalHours }}</text>
      </view>
      <view class="subject-card__item">
        <text class="subject-card__label">剩余学时</text>
        <text :class="['subject-card__value', 'subject-card__value--strong', remainingHoursClass]">
          {{ remainingHours }}
        </text>
      </view>
      <view class="subject-card__item">
        <text class="subject-card__label">扣除学时</text>
        <text class="subject-card__value">{{ deductedHours }}</text>
      </view>
    </view>

    <text class="subject-card__summary">
      {{ subjectName }}：共 {{ item.totalHours }} 学时，剩余 {{ remainingHours }} 学时，已扣除 {{ deductedHours }} 学时
    </text>
  </view>
</template>

<script>
export default {
  name: 'SubjectHoursCard',
  props: {
    item: {
      type: Object,
      default: function() {
        return {}
      }
    }
  },
  computed: {
    subjectName: function() {
      return this.item.subjectName || this.item.subject || '未设置科目'
    },
    remainingHours: function() {
      const value = Number(this.item.remainingHours)
      return isFinite(value) ? value : 0
    },
    isNegative: function() {
      return this.remainingHours < 0
    },
    remainingHoursClass: function() {
      if (this.isNegative) {
        return 'is-negative'
      }
      return this.remainingHours === 0 ? 'is-zero' : ''
    },
    statusText: function() {
      return this.isNegative ? '欠课时' : this.item.statusText || (this.remainingHours === 0 ? '已用完' : '正常')
    },
    deductedHours: function() {
      return Number(typeof this.item.deductedHours !== 'undefined' ? this.item.deductedHours : this.item.usedHours || 0)
    }
  }
}
</script>

<style lang="scss" scoped>
.subject-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.05);
}

.subject-card__grid {
  display: flex;
  margin: 0 -8rpx;
}

.subject-card__item {
  flex: 1;
  margin: 0 8rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.subject-card__label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.subject-card__value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  color: #1f2937;
}

.subject-card__value--strong {
  font-weight: 700;
  color: #2962ff;
}

.subject-card__value--strong.is-negative {
  color: #e5484d;
}

.subject-card__value--strong.is-zero {
  color: #64748b;
}

.soft-tag--negative {
  color: #e5484d;
  background: #fff1f2;
}

.subject-card__summary {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}
</style>
