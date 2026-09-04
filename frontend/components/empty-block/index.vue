<template>
  <view class="empty-block">
    <text class="empty-block__title">{{ title }}</text>
    <text class="empty-block__desc">{{ description }}</text>
    <button v-if="buttonText" class="secondary-btn empty-block__btn" @click="handleClick">{{ buttonText }}</button>
  </view>
</template>

<script>
export default {
  name: 'EmptyBlock',
  props: {
    title: {
      type: String,
      default: '暂无内容'
    },
    description: {
      type: String,
      default: '当前还没有可展示的数据。'
    },
    buttonText: {
      type: String,
      default: ''
    }
  },
  methods: {
    handleClick: function() {
      this.$emit('action')
    }
  }
}
</script>

<style lang="scss" scoped>
.empty-block {
  padding: 36rpx 24rpx;
  border-radius: 24rpx;
  text-align: center;
  background: #f8fafc;
}

.empty-block__title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2937;
}

.empty-block__desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}

.empty-block__btn {
  margin-top: 24rpx;
  border: 0;
}
</style>
