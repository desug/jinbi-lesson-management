<template>
  <view class="page-shell">
    <empty-block
      v-if="pageError"
      title="页面加载失败"
      :description="pageError"
      button-text="重新加载"
      @action="loadStudent"
    />

    <view v-else>
      <view class="hero-card">
        <text class="hero-title">课时调整</text>
        <text class="hero-desc">请为指定学员选择科目、调整方式、课时数量和备注，提交前会进行确认。</text>
      </view>

      <view class="section-card">
        <view class="form-item">
          <text class="form-label">学员姓名</text>
          <input :value="student.name" class="field-input" disabled />
        </view>

        <view class="form-item">
          <text class="form-label">当前班型</text>
          <input :value="student.classTypeText || '小班'" class="field-input" disabled />
        </view>

        <view class="form-item">
          <text class="form-label">调整科目</text>
          <picker :range="subjectOptions" @change="handleSubjectChange">
            <view class="selector-field">
              <text :class="form.subject ? '' : 'selector-field__placeholder'">{{ form.subject || '请选择调整科目' }}</text>
              <text>请选择</text>
            </view>
          </picker>
        </view>

        <view v-if="currentSubjectInfo.subjectName" class="subject-note">
          <view class="subject-note__grid">
            <view class="subject-note__item">
              <text class="subject-note__label">共计学时</text>
              <text class="subject-note__value">{{ currentSubjectInfo.totalHours }}</text>
            </view>
            <view class="subject-note__item">
              <text class="subject-note__label">剩余学时</text>
              <text :class="['subject-note__value', 'subject-note__value--strong', getRemainingHoursClass(currentSubjectInfo.remainingHours)]">
                {{ formatHours(currentSubjectInfo.remainingHours) }}
              </text>
            </view>
            <view class="subject-note__item">
              <text class="subject-note__label">已扣除</text>
              <text class="subject-note__value">{{ currentSubjectInfo.deductedHours }}</text>
            </view>
          </view>
          <text class="subject-note__desc">
            当前科目为“{{ currentSubjectInfo.subjectName }}”，请根据剩余课时合理执行加课时或扣课时。
          </text>
        </view>

        <view class="form-item">
          <text class="form-label">调整方式</text>
          <picker :range="changeTypeOptions" @change="handleTypeChange">
            <view class="selector-field">
              <text :class="form.changeType ? '' : 'selector-field__placeholder'">{{ form.changeType || '请选择调整方式' }}</text>
              <text>请选择</text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="form-label">课时数量</text>
          <input
            v-model="form.hours"
            class="field-input"
            type="number"
            maxlength="4"
            placeholder="请输入课时数量"
          />
        </view>

        <view v-if="form.changeType === '增加'" class="form-item">
          <text class="form-label">加课金额</text>
          <input
            v-model="form.amount"
            class="field-input"
            type="digit"
            maxlength="10"
            placeholder="请输入本次加课金额"
          />
        </view>

        <view class="form-item">
          <text class="form-label">记录日期</text>
          <input
            v-model="form.recordDate"
            class="field-input"
            maxlength="19"
            placeholder="YYYY-MM-DD HH:mm:ss"
          />
        </view>

        <view class="form-item">
          <text class="form-label">备注说明</text>
          <textarea
            v-model="form.remark"
            class="field-textarea"
            maxlength="60"
            placeholder="请输入备注说明"
          />
        </view>

        <view class="button-row">
          <view class="button-row__item">
            <button
              class="primary-btn"
              :loading="submitting || isConfirmingNegative"
              :disabled="submitting || isConfirmingNegative"
              @click="handleSubmit"
            >
              {{ submitting || isConfirmingNegative ? '提交中' : '确认提交' }}
            </button>
          </view>
          <view class="button-row__item">
            <button class="secondary-btn" @click="goDetail">返回详情</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { changeLesson, getAdminStudentDetail } from '@/api/admin'
import { extractBusinessError } from '@/utils/request'
import storage from '@/utils/storage'
import { ROLE, ROUTES } from '@/utils/constants'

const padNumber = function(value) {
  return value < 10 ? '0' + value : '' + value
}

const formatDateTimeInput = function(dateValue) {
  const date = dateValue || new Date()
  return (
    date.getFullYear() +
    '-' +
    padNumber(date.getMonth() + 1) +
    '-' +
    padNumber(date.getDate()) +
    ' ' +
    padNumber(date.getHours()) +
    ':' +
    padNumber(date.getMinutes()) +
    ':00'
  )
}

const createEmptySubject = function() {
  return {
    subjectName: '',
    totalHours: 0,
    remainingHours: 0,
    deductedHours: 0
  }
}

const NEGATIVE_HOURS_CONFIRM_CODE = 'NEGATIVE_HOURS_CONFIRM_REQUIRED'
const NEGATIVE_HOURS_MESSAGE = '尊敬的学员由于您未按时缴纳课时费，将无法为您提供课时服务'

export default {
  data: function() {
    return {
      studentId: '',
      defaultMode: '',
      pageError: '',
      submitting: false,
      isConfirmingNegative: false,
      student: {},
      subjectOptions: [],
      subjectList: [],
      changeTypeOptions: ['增加', '扣减'],
      form: {
        subject: '',
        changeType: '',
        hours: '',
        amount: '',
        recordDate: formatDateTimeInput(new Date()),
        remark: ''
      }
    }
  },
  computed: {
    currentSubjectInfo: function() {
      if (!this.form.subject) {
        return createEmptySubject()
      }

      return (
        this.subjectList.find(function(item) {
          return (item.subjectName || item.subject) === this.form.subject
        }, this) || createEmptySubject()
      )
    }
  },
  onLoad: function(options) {
    this.studentId = options.id || ''
    this.defaultMode = options.mode || ''
  },
  onShow: function() {
    if (!this.ensureAdminRole()) {
      return
    }
    this.loadStudent()
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
    loadStudent: async function() {
      let res

      try {
        res = await getAdminStudentDetail(this.studentId)
      } catch (error) {
        this.pageError = (error && error.message) || '学员数据加载失败'
        return
      }

      const student = res.data.profile

      if (!student) {
        this.pageError = '未找到对应学员'
        return
      }

      this.pageError = ''
      this.student = student
      this.subjectList = (res.data.subjects || []).map(function(item) {
        return Object.assign({}, item, {
          subjectName: item.subjectName || item.subject || '综合'
        })
      })
      if (!this.subjectList.length) {
        this.subjectList = [
          {
            subjectName: '综合',
            totalHours: 0,
            remainingHours: 0,
            deductedHours: 0
          }
        ]
      }
      this.subjectOptions = this.subjectList.map(function(item) {
        return item.subjectName
      })

      if (!this.form.subject && this.subjectOptions.length) {
        this.form.subject = this.subjectOptions[0]
      }

      if (!this.form.changeType) {
        this.form.changeType = this.defaultMode === '扣减' ? '扣减' : '增加'
      }
    },
    handleSubjectChange: function(event) {
      this.form.subject = this.subjectOptions[event.detail.value]
    },
    handleTypeChange: function(event) {
      this.form.changeType = this.changeTypeOptions[event.detail.value]
      if (this.form.changeType === '扣减') {
        this.form.amount = ''
      }
    },
    validateForm: function() {
      const hours = Number(this.form.hours || 0)
      const amountText = String(this.form.amount || '')

      if (!this.form.subject) {
        uni.showToast({
          title: '请选择调整科目',
          icon: 'none'
        })
        return false
      }

      if (!this.form.changeType) {
        uni.showToast({
          title: '请选择调整方式',
          icon: 'none'
        })
        return false
      }

      if (!/^\d+(\.\d+)?$/.test(this.form.hours) || hours <= 0) {
        uni.showToast({
          title: '请输入正确的课时数量',
          icon: 'none'
        })
        return false
      }

      if (this.form.changeType === '增加' && amountText && !/^\d+(\.\d+)?$/.test(amountText)) {
        uni.showToast({
          title: '请输入正确的加课金额',
          icon: 'none'
        })
        return false
      }

      return true
    },
    formatHours: function(value) {
      const numberValue = Number(value)
      if (!isFinite(numberValue)) {
        return '0'
      }
      return numberValue % 1 === 0 ? String(numberValue) : numberValue.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
    },
    getRemainingHoursClass: function(value) {
      const numberValue = Number(value)
      if (numberValue < 0) {
        return 'is-negative'
      }
      return numberValue === 0 ? 'is-zero' : ''
    },
    getNegativeHoursInfo: function(error) {
      const businessError = extractBusinessError(error) || {}
      const detail = businessError.detail && typeof businessError.detail === 'object' ? businessError.detail : {}
      const businessData = businessError.data && typeof businessError.data === 'object' ? businessError.data : {}
      const detailData = detail.data && typeof detail.data === 'object' ? detail.data : {}
      const data = Object.assign({}, businessError, detail, businessData, detailData)

      return {
        code: businessError.code || detail.code || businessData.code || (error && error.code) || '',
        message: businessError.message || detail.message || businessData.message || (error && error.message) || NEGATIVE_HOURS_MESSAGE,
        current: data.currentRemainingHours,
        deduct: data.deductHours,
        after: data.afterRemainingHours
      }
    },
    isNegativeHoursConfirmError: function(error) {
      return this.getNegativeHoursInfo(error).code === NEGATIVE_HOURS_CONFIRM_CODE
    },
    showNegativeHoursModal: function(error, originalPayload) {
      const info = this.getNegativeHoursInfo(error)
      const message = String(info.message || NEGATIVE_HOURS_MESSAGE).replace(/[。.]?$/, '。')
      const current = typeof info.current !== 'undefined' ? this.formatHours(info.current) : '-'
      const deduct = typeof info.deduct !== 'undefined' ? this.formatHours(info.deduct) : this.formatHours(originalPayload.hours)
      const after = typeof info.after !== 'undefined' ? this.formatHours(info.after) : '-'

      uni.showModal({
        title: '课时不足警告',
        content:
          message +
          '\n\n当前剩余 ' +
          current +
          ' 课时，本次扣除 ' +
          deduct +
          ' 课时，扣除后剩余 ' +
          after +
          ' 课时。是否仍然继续？',
        cancelText: '取消',
        confirmText: '仍然扣除',
        confirmColor: '#e5484d',
        success: async function(modalResult) {
          if (!modalResult.confirm || this.isConfirmingNegative) {
            return
          }
          await this.confirmNegativeDeduct(originalPayload)
        }.bind(this)
      })
    },
    resetFormAfterSuccess: function() {
      this.form.hours = ''
      this.form.amount = ''
      this.form.recordDate = formatDateTimeInput(new Date())
      this.form.remark = ''
    },
    buildLessonPayload: function() {
      const isDeduct = this.form.changeType === '扣减'
      return {
        studentId: this.studentId,
        subjectName: this.form.subject || '综合',
        changeType: this.form.changeType,
        hours: Number(this.form.hours),
        amount: isDeduct ? 0 : Number(this.form.amount || 0),
        recordDate: (this.form.recordDate || '').trim(),
        remark: (this.form.remark || (isDeduct ? '管理员手动扣课' : '管理员手动加课')).trim(),
        allowNegative: false
      }
    },
    handleLessonChangeSuccess: async function(response) {
      await this.loadStudent()
      this.resetFormAfterSuccess()

      uni.showToast({
        title: response.message || '操作成功',
        icon: 'none'
      })

      setTimeout(function() {
        uni.navigateBack({
          fail: function() {
            uni.reLaunch({
              url: ROUTES.ADMIN_STUDENT_DETAIL + '?id=' + this.studentId
            })
          }.bind(this)
        })
      }.bind(this), 400)
    },
    submitLessonChange: async function(payload) {
      try {
        const response = await changeLesson(payload)
        await this.handleLessonChangeSuccess(response)
      } catch (error) {
        if (this.isNegativeHoursConfirmError(error)) {
          this.submitting = false
          this.showNegativeHoursModal(error, payload)
          return
        }
        uni.showToast({
          title: (error && error.message) || '课时调整失败',
          icon: 'none'
        })
      } finally {
        this.submitting = false
      }
    },
    confirmNegativeDeduct: async function(originalPayload) {
      if (this.isConfirmingNegative) {
        return
      }

      this.isConfirmingNegative = true
      try {
        const response = await changeLesson(
          Object.assign({}, originalPayload, {
            allowNegative: true
          })
        )
        await this.handleLessonChangeSuccess(response)
      } catch (error) {
        uni.showToast({
          title: (error && error.message) || '扣课失败',
          icon: 'none'
        })
      } finally {
        this.isConfirmingNegative = false
      }
    },
    handleSubmit: function() {
      if (this.submitting || this.isConfirmingNegative || !this.validateForm()) {
        return
      }

      const payload = this.buildLessonPayload()

      const content =
        '确认对“' +
        this.student.name +
        '”执行“' +
        this.form.changeType +
        '”吗？\n科目：' +
        this.form.subject +
        '\n当前剩余：' +
        this.currentSubjectInfo.remainingHours +
        ' 学时\n本次数量：' +
        this.form.hours +
        ' 学时' +
        (this.form.changeType === '增加' ? '\n本次金额：' + this.form.amount + ' 元' : '') +
        '\n记录日期：' +
        (this.form.recordDate || '当前时间')

      this.submitting = true
      uni.showModal({
        title: '提交确认',
        content: content,
        confirmText: '确认提交',
        cancelText: '返回修改',
        success: async function(res) {
          if (!res.confirm) {
            this.submitting = false
            return
          }

          await this.submitLessonChange(payload)
        }.bind(this),
        fail: function() {
          this.submitting = false
        }.bind(this)
      })
    },
    goDetail: function() {
      uni.navigateBack({
        fail: function() {
          uni.reLaunch({
            url: ROUTES.ADMIN_STUDENT_DETAIL + '?id=' + this.studentId
          })
        }.bind(this)
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.subject-note {
  margin-bottom: 24rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f8fbff;
}

.subject-note__grid {
  display: flex;
  margin: 0 -8rpx;
}

.subject-note__item {
  flex: 1;
  margin: 0 8rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #ffffff;
}

.subject-note__label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.subject-note__value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  color: #1f2937;
}

.subject-note__value--strong {
  font-weight: 700;
  color: #2962ff;
}

.subject-note__value.is-negative {
  color: #e5484d;
}

.subject-note__value.is-zero {
  color: #64748b;
}

.subject-note__desc {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}
</style>
