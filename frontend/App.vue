<script>
export default {
  onLaunch: function() {},
  onShow: function() {},
  onHide: function() {}
}
</script>

<style lang="scss">
page {
  min-height: 100%;
  background-color: #f5f7fb;
  color: #1f2937;
  font-size: 28rpx;
}

view,
text,
button,
input,
textarea {
  box-sizing: border-box;
}

button {
  padding: 0;
  border: 0;
  background-color: transparent;
}

button::after {
  border: 0;
}

.page-shell {
  min-height: 100vh;
  padding: 28rpx 24rpx 40rpx;
  background:
    radial-gradient(circle at top right, rgba(34, 104, 255, 0.14), transparent 38%),
    linear-gradient(180deg, #f7f9fc 0%, #eef3fb 100%);
}

.hero-card,
.section-card,
.placeholder-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.06);
}

.hero-card {
  margin-bottom: 24rpx;
  background: linear-gradient(135deg, rgba(41, 98, 255, 0.96), rgba(87, 160, 255, 0.9));
}

.section-card,
.placeholder-card {
  margin-bottom: 24rpx;
}

.hero-title {
  display: block;
  font-size: 38rpx;
  font-weight: 600;
  line-height: 1.45;
  color: #ffffff;
}

.hero-desc {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  line-height: 1.4;
  color: #1f2937;
}

.section-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}

.section-link {
  font-size: 24rpx;
  color: #2962ff;
}

.stat-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10rpx;
}

.stat-card {
  width: calc(50% - 20rpx);
  margin: 10rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.16);
}

.stat-label {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.82);
}

.stat-value {
  display: block;
  margin-top: 12rpx;
  font-size: 38rpx;
  font-weight: 700;
  color: #ffffff;
}

.info-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #eef2f7;
}

.info-row:last-child {
  border-bottom: 0;
}

.info-label {
  font-size: 24rpx;
  color: #64748b;
}

.info-value {
  max-width: 68%;
  font-size: 26rpx;
  line-height: 1.7;
  text-align: right;
  color: #1f2937;
}

.button-row {
  display: flex;
  margin: 0 -10rpx;
}

.button-row__item {
  flex: 1;
  margin: 0 10rpx;
}

.primary-btn,
.secondary-btn,
.danger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 84rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  font-size: 28rpx;
  line-height: 1;
}

.primary-btn {
  color: #ffffff;
  background: linear-gradient(135deg, #2962ff 0%, #4d8dff 100%);
}

.secondary-btn {
  color: #2962ff;
  background: #eef4ff;
}

.danger-btn {
  color: #ffffff;
  background: linear-gradient(135deg, #ff5a5f 0%, #ff7b74 100%);
}

.quick-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10rpx -20rpx;
}

.quick-item {
  width: calc(50% - 20rpx);
  margin: 0 10rpx 20rpx;
  padding: 26rpx 22rpx;
  border-radius: 22rpx;
  background: #f8fbff;
}

.quick-item__label {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #1f2937;
}

.quick-item__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.list-stack > view,
.list-stack > empty-block,
.list-stack > subject-hours-card,
.list-stack > student-card,
.list-stack > record-list {
  display: block;
  margin-bottom: 20rpx;
}

.list-stack > view:last-child,
.list-stack > empty-block:last-child,
.list-stack > subject-hours-card:last-child,
.list-stack > student-card:last-child,
.list-stack > record-list:last-child {
  margin-bottom: 0;
}

.form-item {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 24rpx;
  color: #475569;
}

.field-input,
.field-textarea,
.selector-field {
  width: 100%;
  padding: 22rpx 24rpx;
  border-radius: 18rpx;
  border: 1rpx solid #d8e0ec;
  background: #ffffff;
  font-size: 28rpx;
  color: #1f2937;
}

.field-input[disabled] {
  color: #64748b;
  background: #f8fafc;
}

.field-textarea {
  min-height: 180rpx;
}

.selector-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.selector-field__placeholder {
  color: #94a3b8;
}

.soft-tag {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #eef4ff;
  font-size: 22rpx;
  color: #2962ff;
}

.placeholder-note {
  margin-top: 16rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #f8fafc;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}
</style>
