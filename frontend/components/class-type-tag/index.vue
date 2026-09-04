<template>
  <view v-if="showTag" :class="['class-type-tag', 'class-type-tag--' + theme, className]">
    <text class="class-type-tag__text">{{ label }}</text>
  </view>
</template>

<script>
export default {
  name: 'ClassTypeTag',
  props: {
    classType: {
      type: String,
      default: ''
    },
    theme: {
      type: String,
      default: 'plain'
    }
  },
  computed: {
    normalizedType: function() {
      const text = String(this.classType || '').replace(/\s/g, '').replace(/＋/g, '+')
      const lowerText = text.toLowerCase()
      if (text === 'VIP' || lowerText === 'vip' || text === '一对一') {
        return 'VIP'
      }
      if (text === '小班' || lowerText === 'small') {
        return '小班'
      }
      if (text === '小班+一对一' || lowerText === '小班+vip' || text === '小班一对一') {
        return '小班+一对一'
      }
      if (text === '一对二') {
        return '一对二'
      }
      return text
    },
    showTag: function() {
      return !!this.normalizedType
    },
    label: function() {
      const labels = {
        'VIP': 'VIP',
        '小班': '小班',
        '小班+一对一': '小班+一对一（历史）',
        '一对二': '一对二'
      }
      return labels[this.normalizedType] || this.normalizedType
    },
    className: function() {
      if (this.normalizedType === 'VIP') {
        return 'class-type-tag--vip'
      }
      if (this.normalizedType === '小班+一对一') {
        return 'class-type-tag--mixed'
      }
      if (this.normalizedType === '一对二') {
        return 'class-type-tag--pair'
      }
      return 'class-type-tag--small'
    }
  }
}
</script>

<style lang="scss" scoped>
.class-type-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 120rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  border: 1rpx solid transparent;
}

.class-type-tag--plain {
  background: rgba(109, 118, 188, 0.12);
  border-color: rgba(109, 118, 188, 0.18);
}

.class-type-tag--light {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.24);
}

.class-type-tag__text {
  font-size: 22rpx;
  line-height: 1.2;
  color: #ffffff;
}

.class-type-tag--plain .class-type-tag__text {
  color: #6571bd;
}

.class-type-tag--small.class-type-tag--plain {
  background: #eef2f7;
  border-color: #e2e8f0;
}

.class-type-tag--small.class-type-tag--plain .class-type-tag__text {
  color: #475569;
}

.class-type-tag--mixed.class-type-tag--plain {
  background: #ffedd5;
  border-color: #fed7aa;
}

.class-type-tag--mixed.class-type-tag--plain .class-type-tag__text {
  color: #7c2d12;
}

.class-type-tag--pair.class-type-tag--plain {
  background: #ccfbf1;
  border-color: #99f6e4;
}

.class-type-tag--pair.class-type-tag--plain .class-type-tag__text {
  color: #0f766e;
}
</style>
