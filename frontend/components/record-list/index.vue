<template>
  <view>
    <empty-block
      v-if="!list.length"
      :title="emptyTitle"
      :description="emptyDescription"
    />

    <view v-else class="record-list">
      <view
        v-for="item in list"
        :key="item.id"
        :class="['record-list__item', item.changeTypeValue === 'deduct' ? 'record-list__item--deduct' : 'record-list__item--add']"
      >
        <view class="record-list__head">
          <view class="record-list__title-wrap">
            <text class="record-list__type">{{ item.changeTypeText || item.title }}</text>
            <text class="record-list__subject">{{ item.subjectName || item.subject || '综合' }}</text>
          </view>
          <text :class="['record-list__hours', item.changeTypeValue === 'deduct' ? 'record-list__hours--deduct' : '']">
            {{ item.hoursText || item.amount }}
          </text>
        </view>

        <view class="record-list__grid">
          <view class="record-list__field">
            <text class="record-list__label">金额</text>
            <text class="record-list__value">{{ item.amountText || '¥0.00' }}</text>
          </view>
          <view class="record-list__field">
            <text class="record-list__label">剩余课时</text>
            <text :class="['record-list__value', Number(item.remainingHours) < 0 ? 'is-negative' : '']">
              {{ item.remainingHoursText || item.remainingHours || 0 }}
            </text>
          </view>
        </view>

        <view class="record-list__line">
          <text class="record-list__label">时间</text>
          <text class="record-list__line-value">{{ item.time || '-' }}</text>
        </view>
        <view class="record-list__line">
          <text class="record-list__label">备注</text>
          <text class="record-list__line-value">{{ item.remarkText || '-' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'RecordList',
  props: {
    list: {
      type: Array,
      default: function() {
        return []
      }
    },
    emptyTitle: {
      type: String,
      default: '暂无记录'
    },
    emptyDescription: {
      type: String,
      default: '当前还没有记录。'
    }
  }
}
</script>

<style lang="scss" scoped>
.record-list__item {
  padding: 24rpx;
  margin-bottom: 20rpx;
  border-radius: 24rpx;
  background: #ffffff;
  border: 1rpx solid #e7eef8;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.05);
}

.record-list__item--add {
  border-left: 8rpx solid #2962ff;
}

.record-list__item--deduct {
  border-left: 8rpx solid #ef4444;
}

.record-list__item:last-child {
  margin-bottom: 0;
}

.record-list__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.record-list__title-wrap {
  flex: 1;
  min-width: 0;
}

.record-list__type {
  display: block;
  font-size: 31rpx;
  font-weight: 700;
  line-height: 1.35;
  color: #1f2937;
}

.record-list__subject {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  color: #64748b;
}

.record-list__hours {
  flex: 0 0 auto;
  min-width: 132rpx;
  padding: 10rpx 14rpx;
  border-radius: 18rpx;
  background: #eef4ff;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
  color: #2962ff;
}

.record-list__hours--deduct {
  color: #ef4444;
  background: #fff1f2;
}

.record-list__grid {
  display: flex;
  gap: 14rpx;
  margin-top: 20rpx;
}

.record-list__field {
  flex: 1;
  min-width: 0;
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.record-list__label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.record-list__value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  line-height: 1.35;
  color: #1f2937;
  word-break: break-all;
}

.record-list__value.is-negative {
  color: #e5484d;
}

.record-list__line {
  margin-top: 16rpx;
}

.record-list__line-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #475569;
  word-break: break-all;
}
</style>
