<template>
  <view class="page-shell admin-students-page">
    <view class="hero-card">
      <text class="hero-title">学员管理</text>
      <text class="hero-desc">按年级组织学员，快速查看剩余课时，并手动加课时或扣课时。</text>
    </view>

    <view v-if="viewMode === 'grades'" class="section-card">
      <view class="section-head">
        <text class="section-title">年级列表</text>
        <view class="section-actions">
          <text class="section-link" @click="fetchGrades">刷新</text>
        </view>
      </view>

      <view v-if="gradeList.length" class="grade-grid">
        <view
          v-for="item in gradeList"
          :key="item.grade"
          class="grade-card"
          @click="selectGrade(item)"
        >
          <view class="grade-card__head">
            <text class="grade-card__name">{{ item.grade }}</text>
            <text class="soft-tag">共 {{ item.studentCount }} 人</text>
          </view>
          <text class="grade-card__line">
            VIP {{ item.vipCount }} 人 / 小班 {{ item.smallCount }} 人
          </text>
          <text class="grade-card__line">
            一对二 {{ item.oneToTwoCount || 0 }} 人
          </text>
          <text :class="['grade-card__hours', getRemainingHoursClass(item.totalRemainingHours)]">
            剩余课时总计 {{ formatHours(item.totalRemainingHours) }}
          </text>
        </view>
      </view>

      <empty-block
        v-else
        :title="gradeError ? '年级列表加载失败' : '暂无年级'"
        :description="gradeError || '当前暂无学员年级数据。'"
        button-text="重新加载"
        @action="fetchGrades"
      />
    </view>

    <view v-else>
      <view class="section-card">
        <view class="grade-toolbar">
          <view>
            <text class="section-title">{{ currentGrade }}学员列表</text>
            <text class="grade-toolbar__meta">{{ currentFilterLabel }}共 {{ total }} 人</text>
          </view>
          <view class="grade-toolbar__actions">
            <button v-if="isGradeStudentMode" class="mini-btn" @click="openCreateStudent">添加学生</button>
            <button class="mini-btn" @click="backToGrades">返回年级列表</button>
          </view>
        </view>

        <view class="filter-tabs">
          <view
            v-for="item in filterTabs"
            :key="item.value"
            :class="['filter-tab', classType === item.value ? 'filter-tab--active' : '']"
            @click="handleFilterChange(item.value)"
          >
            <text :class="['filter-tab__text', classType === item.value ? 'filter-tab__text--active' : '']">
              {{ item.label }}
            </text>
          </view>
        </view>

        <view class="form-item compact-form-item">
          <input
            v-model="keyword"
            class="field-input"
            maxlength="30"
            placeholder="姓名 / 手机号 / 学号"
            @confirm="handleSearch"
          />
        </view>

        <view class="button-row">
          <view class="button-row__item">
            <button class="primary-btn" @click="handleSearch">搜索</button>
          </view>
          <view class="button-row__item">
            <button class="secondary-btn" @click="resetSearch">清空条件</button>
          </view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <text class="section-title">AI 助手</text>
        <text class="section-link">智能课时查询</text>
      </view>
      <text class="section-desc">支持按自然语言查询学员班型、单科剩余课时和课时汇总。</text>

      <view class="form-item ai-input-row">
        <input
          v-model="aiQueryText"
          class="field-input"
          maxlength="80"
          placeholder="例如：演示学员01数学还剩多少课时"
          @confirm="handleAiQuery"
        />
      </view>

      <view class="button-row">
        <view class="button-row__item">
          <button class="primary-btn" @click="handleAiQuery">开始查询</button>
        </view>
      </view>

      <view class="ai-helper-list">
        <view
          v-for="item in aiExampleList"
          :key="item"
          class="ai-helper-item"
          @click="fillAiExample(item)"
        >
          <text class="ai-helper-item__text">{{ item }}</text>
        </view>
      </view>

      <view class="ai-result">
        <text class="ai-result__label">查询结果</text>
        <text :class="['ai-result__text', aiResultIsNegative ? 'is-negative' : '']">
          {{ aiResultText || '试试输入“演示学员01数学还剩多少课时”或“演示学员03课时汇总”。' }}
        </text>
      </view>
    </view>

    <view v-if="viewMode === 'students'" class="section-card">
        <view class="section-head">
          <text class="section-title">学生列表</text>
          <text class="section-link">{{ selectedGrade }}</text>
        </view>

        <view v-if="studentList.length" class="student-list">
          <view
            v-for="(student, studentIndex) in studentList"
            :key="student.id"
            class="student-card"
          >
            <view class="student-card__head">
              <view class="student-card__title-wrap">
                <text class="student-card__name">{{ student.name }}</text>
                <text :class="['class-tag', getClassTagClass(student.classType)]">
                  {{ getClassTypeLabel(student.classType) }}
                </text>
              </view>
              <view :class="['remaining-pill', getRemainingHoursClass(getStudentRemainingHours(student))]">
                <text class="remaining-pill__label">{{ Number(getStudentRemainingHours(student)) < 0 ? '欠课时' : '总剩余' }}</text>
                <text class="remaining-pill__value">{{ formatHours(getStudentRemainingHours(student)) }}</text>
              </view>
            </view>

            <view class="student-info-grid">
              <view class="student-info-item">
                <text class="student-info-label">手机号</text>
                <text class="student-info-value">{{ student.phone || '-' }}</text>
              </view>
              <view class="student-info-item">
                <text class="student-info-label">学号</text>
                <text class="student-info-value">{{ student.studentNo || '-' }}</text>
              </view>
              <view class="student-info-item">
                <text class="student-info-label">年级</text>
                <text class="student-info-value">{{ student.grade || currentGrade }}</text>
              </view>
              <view class="student-info-item">
                <text class="student-info-label">学校</text>
                <text class="student-info-value">{{ student.school || '-' }}</text>
              </view>
              <view class="student-info-item">
                <text class="student-info-label">班型</text>
                <text class="student-info-value">{{ getClassTypeLabel(student.classType) }}</text>
              </view>
            </view>

            <view class="subject-list">
              <view
                v-for="subject in student.subjects"
                :key="subject.subjectName"
                class="subject-row"
              >
                <text class="subject-row__name">{{ subject.subjectName }}</text>
                <text :class="['subject-row__text', getRemainingHoursClass(subject.remainingHours)]">
                  剩余 {{ formatHours(subject.remainingHours) }} / 总 {{ formatHours(subject.totalHours) }} / 已扣 {{ formatHours(subject.deductedHours) }}
                </text>
              </view>
              <text v-if="!student.subjects || !student.subjects.length" class="subject-empty">暂无科目课时</text>
            </view>

            <view class="student-actions">
              <button class="action-btn action-btn--plain" hover-stop-propagation @tap.stop="goDetailByIndex(studentIndex)">查看详情</button>
              <button class="action-btn action-btn--add" hover-stop-propagation @tap.stop="openAdjustByIndex(studentIndex, 'add')">加课时</button>
              <button class="action-btn action-btn--deduct" hover-stop-propagation @tap.stop="openAdjustByIndex(studentIndex, 'deduct')">扣课时</button>
              <button
                v-if="canUpgradeStudent(student)"
                class="action-btn action-btn--upgrade"
                hover-stop-propagation
                @tap.stop="openUpgradeGradeByIndex(studentIndex)"
              >
                升级年级
              </button>
              <button class="action-btn action-btn--delete" hover-stop-propagation @tap.stop="handleDeleteStudentByIndex(studentIndex)">删除</button>
            </view>
          </view>
        </view>

        <empty-block
          v-else
          :title="studentError ? '学生列表加载失败' : '暂无学员'"
          :description="studentError || emptyStudentDescription"
        />
      </view>

    <view
      v-if="createVisible"
      class="popup-mask"
      @click="closeCreateStudent"
      @touchmove.stop.prevent
    >
      <scroll-view scroll-y class="adjust-panel" @click.stop>
        <view class="adjust-panel__head">
          <text class="adjust-panel__title">添加学生</text>
          <text class="adjust-panel__close" @click="closeCreateStudent">关闭</text>
        </view>

        <view class="current-grade-note">
          <text class="current-grade-note__text">当前年级：{{ createForm.grade || currentGrade }}</text>
        </view>

        <view class="form-item">
          <text class="form-label">班型</text>
          <view class="class-type-choice-list">
            <view
              v-for="item in classTypeOptions"
              :key="item.value"
              :class="['class-type-choice', createForm.classType === item.value ? 'class-type-choice--active' : '']"
              @click="selectCreateClassType(item.value)"
            >
              <text :class="['class-type-choice__text', createForm.classType === item.value ? 'class-type-choice__text--active' : '']">
                {{ item.label }}
              </text>
            </view>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">姓名</text>
          <input
            v-model="createForm.name"
            class="field-input"
            maxlength="20"
            placeholder="请输入学生姓名"
          />
        </view>

        <view class="form-item">
          <text class="form-label">手机号</text>
          <input
            v-model="createForm.phone"
            class="field-input"
            type="number"
            maxlength="20"
            placeholder="请输入手机号"
          />
        </view>

        <view class="form-item">
          <text class="form-label">课时总数</text>
          <input
            v-model="createForm.totalHours"
            class="field-input"
            type="digit"
            maxlength="6"
            placeholder="请输入课时总数"
          />
        </view>

        <view class="form-item">
          <text class="form-label">总价</text>
          <input
            v-model="createForm.totalPrice"
            class="field-input"
            type="digit"
            maxlength="10"
            placeholder="请输入总价"
          />
        </view>

        <button class="submit-adjust-btn" :loading="creating" @click="submitCreateStudent">
          确认添加
        </button>
      </scroll-view>
    </view>

    <view
      v-if="upgradeVisible"
      class="popup-mask"
      @click="closeUpgradeGrade"
      @touchmove.stop.prevent
    >
      <scroll-view scroll-y class="adjust-panel" @click.stop>
        <view class="adjust-panel__head">
          <text class="adjust-panel__title">升级年级</text>
          <text class="adjust-panel__close" @click="closeUpgradeGrade">关闭</text>
        </view>

        <view class="current-grade-note">
          <text class="current-grade-note__text">当前年级：{{ upgradeCurrentGrade }}</text>
        </view>

        <view class="form-item">
          <text class="form-label">选择目标年级</text>
          <view class="grade-target-list">
            <view
              v-for="grade in upgradeTargetOptions"
              :key="grade"
              :class="['grade-target-item', upgradeTargetGrade === grade ? 'grade-target-item--active' : '']"
              @click="setUpgradeTargetGrade(grade)"
            >
              <text>{{ grade }}</text>
            </view>
          </view>
        </view>

        <button class="submit-adjust-btn" :loading="upgrading" @click="submitUpgradeGrade">
          确认升级
        </button>
      </scroll-view>
    </view>

    <view
      v-if="adjustVisible"
      class="popup-mask"
      @click="closeAdjust"
      @touchmove.stop.prevent
    >
      <scroll-view scroll-y class="adjust-panel" @click.stop>
        <view class="adjust-panel__head">
          <text class="adjust-panel__title">{{ adjustDialogTitle }}</text>
          <text class="adjust-panel__close" @click="closeAdjust">关闭</text>
        </view>

        <view class="form-item">
          <text class="form-label">学生姓名</text>
          <input :value="adjustStudent.name" class="field-input" disabled />
        </view>

        <view class="form-item">
          <text class="form-label">科目</text>
          <picker :range="subjectOptions" @change="handleSubjectChange">
            <view class="selector-field">
              <text :class="adjustForm.subjectName ? '' : 'selector-field__placeholder'">
                {{ adjustForm.subjectName || '请选择科目' }}
              </text>
              <text>请选择</text>
            </view>
          </picker>
        </view>

        <view v-if="currentSubjectInfo.subjectName" class="subject-note">
          <view class="subject-note__item">
            <text class="subject-note__label">当前剩余</text>
            <text :class="['subject-note__value', getRemainingHoursClass(currentSubjectInfo.remainingHours)]">
              {{ formatHours(currentSubjectInfo.remainingHours) }}
            </text>
          </view>
          <view class="subject-note__item">
            <text class="subject-note__label">总课时</text>
            <text class="subject-note__value">{{ formatHours(currentSubjectInfo.totalHours) }}</text>
          </view>
          <view class="subject-note__item">
            <text class="subject-note__label">已扣</text>
            <text class="subject-note__value">{{ formatHours(currentSubjectInfo.deductedHours) }}</text>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">操作类型</text>
          <view class="type-switch">
            <view
              :class="['type-switch__item', adjustForm.changeType === 'add' ? 'type-switch__item--add-active' : '']"
              @click="setAdjustType('add')"
            >
              <text>加课</text>
            </view>
            <view
              :class="['type-switch__item', adjustForm.changeType === 'deduct' ? 'type-switch__item--deduct-active' : '']"
              @click="setAdjustType('deduct')"
            >
              <text>扣课</text>
            </view>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">课时数</text>
          <input
            v-model="adjustForm.hours"
            class="field-input"
            type="digit"
            maxlength="5"
            placeholder="请输入课时数"
          />
        </view>

        <view v-if="adjustForm.changeType === 'add'" class="form-item">
          <text class="form-label">加课金额</text>
          <input
            v-model="adjustForm.amount"
            class="field-input"
            type="digit"
            maxlength="10"
            placeholder="请输入本次加课金额"
          />
        </view>

        <view class="form-item">
          <text class="form-label">记录日期</text>
          <input
            v-model="adjustForm.recordDate"
            class="field-input"
            maxlength="19"
            placeholder="YYYY-MM-DD HH:mm:ss"
          />
        </view>

        <view class="form-item">
          <text class="form-label">备注</text>
          <textarea
            v-model="adjustForm.remark"
            class="field-textarea"
            maxlength="80"
            placeholder="请输入备注"
          />
        </view>

        <button
          :class="['submit-adjust-btn', adjustForm.changeType === 'deduct' ? 'submit-adjust-btn--deduct' : '']"
          :loading="submitting || isConfirmingNegative"
          :disabled="submitting || isConfirmingNegative"
          @click="submitAdjust"
        >
          {{ adjustSubmitText }}
        </button>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { aiQuery, changeLesson, createAdminStudent, deleteAdminStudent, getAdminGrades, getGradeStudents, upgradeAdminStudentGrade } from '@/api/admin'
import { getAdminAiExampleList } from '@/utils/aiQuery'
import { CLASS_TYPE_OPTIONS, isCreateClassType } from '@/utils/classTypes'
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

const createStudentForm = function() {
  // 新增学生弹窗每次打开都用这个函数生成干净表单，避免上一次输入残留。
  return {
    name: '',
    phone: '',
    totalHours: '',
    totalPrice: '',
    grade: '',
    classType: ''
  }
}

const createAdjustForm = function(changeType, subjectName) {
  // 课时调整表单：changeType 为 add 表示加课，deduct 表示扣课。
  return {
    subjectName: subjectName || '',
    changeType: changeType || 'add',
    hours: '',
    amount: '',
    recordDate: formatDateTimeInput(new Date()),
    remark: ''
  }
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
const PHONE_CLASS_DUPLICATE_CODE = 'PHONE_CLASS_DUPLICATE'
const NEGATIVE_HOURS_MESSAGE = '尊敬的学员由于您未按时缴纳课时费，将无法为您提供课时服务'
const STUDENT_GRADE_ORDER = ['初一', '初二', '初三', '高一', '高二', '高三']
const DEFAULT_GRADE = '未分配'

export default {
  data: function() {
    return {
      // viewMode 控制当前是“年级列表”还是“某个年级的学生列表”。
      viewMode: 'grades',
      gradeList: [],
      gradeError: '',
      gradeRequestId: 0,
      selectedGrade: '',
      keyword: '',
      classType: 'all',
      total: 0,
      studentList: [],
      studentError: '',
      studentRequestId: 0,
      hasLoaded: false,
      aiQueryText: '',
      aiResultText: '',
      aiExampleList: getAdminAiExampleList(),
      // createVisible / adjustVisible / upgradeVisible 控制三个弹窗显示状态。
      createVisible: false,
      createForm: createStudentForm(),
      creating: false,
      adjustVisible: false,
      adjustStudent: {},
      subjectList: [],
      subjectOptions: [],
      adjustForm: createAdjustForm('add', ''),
      submitting: false,
      isConfirmingNegative: false,
      upgradeVisible: false,
      upgradeStudent: {},
      upgradeTargetGrade: '',
      upgrading: false,
      classTypeOptions: CLASS_TYPE_OPTIONS.map(function(item) {
        return Object.assign({}, item)
      }),
      filterTabs: [
        {
          label: '全部学员',
          value: 'all'
        },
        {
          label: 'VIP学员',
          value: 'VIP'
        },
        {
          label: '小班学员',
          value: '小班'
        },
        {
          label: '一对二',
          value: '一对二'
        }
      ]
    }
  },
  computed: {
    currentFilterLabel: function() {
      const current = this.filterTabs.find(function(item) {
        return item.value === this.classType
      }, this)
      return current ? current.label + '：' : '全部学员：'
    },
    activeGrade: function() {
      return (this.selectedGrade || '').trim()
    },
    isGradeStudentMode: function() {
      return this.viewMode === 'students' && !!this.activeGrade
    },
    currentGrade: function() {
      return this.isGradeStudentMode ? this.activeGrade : ''
    },
    upgradeCurrentGrade: function() {
      return this.getStudentGrade(this.upgradeStudent)
    },
    upgradeTargetOptions: function() {
      return this.getUpgradeTargetGrades(this.upgradeStudent)
    },
    emptyStudentDescription: function() {
      if (this.keyword) {
        return '请尝试更换姓名、手机号、学号或班型筛选条件后重新搜索。'
      }
      return '当前年级暂无符合条件的学员。'
    },
    adjustDialogTitle: function() {
      return this.adjustForm.changeType === 'deduct' ? '扣课时' : '加课时'
    },
    adjustSubmitText: function() {
      if (this.submitting || this.isConfirmingNegative) {
        return '提交中'
      }
      return this.adjustForm.changeType === 'deduct' ? '确认扣课' : '确认加课'
    },
    aiResultIsNegative: function() {
      return /-\d+(?:\.\d+)?\s*(?:课时|学时)/.test(String(this.aiResultText || ''))
    },
    currentSubjectInfo: function() {
      // 当前选中的科目信息，用于扣课前判断剩余课时是否足够。
      if (!this.adjustForm.subjectName) {
        return createEmptySubject()
      }

      return (
        this.subjectList.find(function(item) {
          return item.subjectName === this.adjustForm.subjectName
        }, this) || createEmptySubject()
      )
    }
  },
  onLoad: function() {
    // 首次进入页面先校验管理员身份，再加载年级列表。
    if (!this.ensureAdminRole()) {
      return
    }
    this.fetchGrades()
  },
  onShow: function() {
    // 从详情页/调整页返回时刷新当前视图，保证列表课时是最新的。
    if (!this.ensureAdminRole()) {
      return
    }
    if (!this.hasLoaded) {
      return
    }
    if (this.viewMode === 'grades') {
      this.fetchGrades()
    } else {
      this.fetchGradeStudents()
    }
  },
  methods: {
    ensureAdminRole: function() {
      // 管理员页面的第一道前端保护：不是 admin 角色就跳回管理员登录页。
      if (storage.getRole() !== ROLE.ADMIN) {
        uni.reLaunch({
          url: ROUTES.ADMIN_LOGIN
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
    getStudentRemainingHours: function(student) {
      if (student && typeof student.totalRemainingHours !== 'undefined' && student.totalRemainingHours !== null) {
        return student.totalRemainingHours
      }
      return student && typeof student.remainingHours !== 'undefined' ? student.remainingHours : 0
    },
    getClassTypeLabel: function(classType) {
      const labelMap = {
        'VIP': 'VIP',
        'vip': 'VIP',
        '小班': '小班',
        'small': '小班',
        '小班+一对一': '小班+一对一（历史）',
        '一对二': '一对二'
      }
      return labelMap[classType] || classType || '未设置班型'
    },
    getClassTagClass: function(classType) {
      if (classType === 'VIP' || classType === 'vip') {
        return 'class-tag--vip'
      }
      if (classType === '小班+一对一') {
        return 'class-tag--mixed'
      }
      if (classType === '一对二') {
        return 'class-tag--pair'
      }
      return 'class-tag--small'
    },
    selectCreateClassType: function(classType) {
      if (isCreateClassType(classType)) {
        this.createForm.classType = classType
      }
    },
    openCreateStudent: function() {
      // 新增学生必须先选年级，因为后端也要求 grade 不能为空。
      const grade = this.activeGrade
      if (!this.isGradeStudentMode || !grade) {
        uni.showToast({
          title: '请先选择年级后再添加学生',
          icon: 'none'
        })
        return
      }
      this.createForm = Object.assign(createStudentForm(), {
        grade: grade
      })
      this.createVisible = true
    },
    closeCreateStudent: function() {
      if (this.creating) {
        return
      }
      this.createVisible = false
      this.createForm = createStudentForm()
    },
    validateCreateForm: function() {
      // 提交前做必填和数字校验；后端仍会再校验一次，前端校验主要提升体验。
      const grade = String(this.createForm.grade || this.activeGrade || '').trim()
      if (!this.isGradeStudentMode || !grade) {
        uni.showToast({
          title: '请先选择年级后再添加学生',
          icon: 'none'
        })
        return false
      }
      this.createForm.grade = grade

      const name = (this.createForm.name || '').trim()
      const phone = (this.createForm.phone || '').trim()
      const totalHoursText = String(this.createForm.totalHours || '')
      const totalPriceText = String(this.createForm.totalPrice || '')
      const classType = String(this.createForm.classType || '').trim()

      if (!name) {
        uni.showToast({
          title: '请输入学生姓名',
          icon: 'none'
        })
        return false
      }

      if (!phone) {
        uni.showToast({
          title: '请输入手机号',
          icon: 'none'
        })
        return false
      }

      if (!classType) {
        uni.showToast({
          title: '请选择班型',
          icon: 'none'
        })
        return false
      }

      if (!isCreateClassType(classType)) {
        uni.showToast({
          title: '新增学生仅支持 VIP、小班、一对二班型',
          icon: 'none'
        })
        return false
      }

      if (!/^\d+(\.\d+)?$/.test(totalHoursText)) {
        uni.showToast({
          title: '请输入正确的课时总数',
          icon: 'none'
        })
        return false
      }

      if (!/^\d+(\.\d+)?$/.test(totalPriceText)) {
        uni.showToast({
          title: '请输入正确的总价',
          icon: 'none'
        })
        return false
      }

      return true
    },
    submitCreateStudent: async function() {
      // 调用后端新增学生接口；成功后刷新当前年级学生和年级汇总。
      if (this.creating || !this.validateCreateForm()) {
        return
      }

      const grade = String(this.createForm.grade || this.activeGrade || '').trim()
      const selectedClassType = String(this.createForm.classType || '').trim()
      this.creating = true

      try {
        const res = await createAdminStudent({
          name: (this.createForm.name || '').trim(),
          phone: (this.createForm.phone || '').trim(),
          totalHours: Number(this.createForm.totalHours || 0),
          totalPrice: Number(this.createForm.totalPrice || 0),
          grade: grade,
          classType: selectedClassType
        })
        this.creating = false
        this.closeCreateStudent()
        this.keyword = ''
        this.classType = selectedClassType
        this.selectedGrade = grade
        this.viewMode = 'students'
        await this.refreshCurrentGradeStudents()
        this.refreshGrades()
        uni.showToast({
          title: (res.data && res.data.message) || res.message || '学生添加成功',
          icon: 'none'
        })
      } catch (error) {
        const businessError = extractBusinessError(error) || {}
        const detail = businessError.detail && typeof businessError.detail === 'object' ? businessError.detail : {}
        const data = businessError.data && typeof businessError.data === 'object' ? businessError.data : {}
        const code = businessError.code || detail.code || data.code || (error && error.code) || ''
        uni.showToast({
          title:
            code === PHONE_CLASS_DUPLICATE_CODE
              ? '该手机号已经报名该班型，请勿重复添加'
              : (businessError.message || detail.message || data.message || (error && error.message) || '学生添加失败'),
          icon: 'none'
        })
      } finally {
        this.creating = false
      }
    },
    fetchGrades: async function() {
      // requestId 用来避免“慢请求覆盖快请求”：只有最后一次请求能更新页面。
      const requestId = this.gradeRequestId + 1
      this.gradeRequestId = requestId
      this.gradeError = ''

      try {
        const res = await getAdminGrades()
        if (requestId !== this.gradeRequestId) {
          return
        }
        const source = res.data || {}
        this.gradeList = Array.isArray(source.items) ? source.items : []
        this.hasLoaded = true
      } catch (error) {
        if (requestId !== this.gradeRequestId) {
          return
        }
        console.error('[admin grades fetch failed]', error)
        this.gradeList = []
        this.gradeError = (error && error.message) || '年级列表加载失败，请检查接口或后端服务。'
        uni.showToast({
          title: this.gradeError,
          icon: 'none'
        })
      }
    },
    selectGrade: function(item) {
      // 点击某个年级卡片后，切到学生列表视图并加载该年级学生。
      const grade = (item && item.grade ? item.grade : '').trim()
      if (!grade) {
        return
      }
      this.selectedGrade = grade
      this.keyword = ''
      this.classType = 'all'
      this.viewMode = 'students'
      this.fetchGradeStudents()
    },
    backToGrades: function() {
      this.viewMode = 'grades'
      this.selectedGrade = ''
      this.studentList = []
      this.total = 0
      this.fetchGrades()
    },
    fetchGradeStudents: async function() {
      // 根据当前年级、关键词、班型筛选学生列表。
      const grade = this.currentGrade
      if (!grade) {
        return
      }

      const requestId = this.studentRequestId + 1
      this.studentRequestId = requestId
      this.studentError = ''

      try {
        const res = await getGradeStudents(grade, {
          keyword: (this.keyword || '').trim(),
          classType: this.classType
        })
        if (requestId !== this.studentRequestId) {
          return
        }
        const source = res.data || {}
        this.studentList = Array.isArray(source.list) ? source.list : []
        this.total = Number(source.total || this.studentList.length)
        this.hasLoaded = true
      } catch (error) {
        if (requestId !== this.studentRequestId) {
          return
        }
        console.error('[admin grade students fetch failed]', error)
        this.studentList = []
        this.total = 0
        this.studentError = (error && error.message) || '学生列表加载失败，请检查接口或后端服务。'
        uni.showToast({
          title: this.studentError,
          icon: 'none'
        })
      }
    },
    refreshCurrentGradeStudents: function() {
      return this.fetchGradeStudents()
    },
    refreshGrades: function() {
      return this.fetchGrades()
    },
    handleSearch: function() {
      this.fetchGradeStudents()
    },
    handleFilterChange: function(value) {
      if (this.classType === value) {
        return
      }
      this.classType = value
      this.fetchGradeStudents()
    },
    resetSearch: function() {
      this.keyword = ''
      this.classType = 'all'
      this.fetchGradeStudents()
    },
    getStudentId: function(student) {
      return student && (student.studentId || student.id)
    },
    getStudentByIndex: function(studentIndex) {
      const index = Number(studentIndex)
      if (!isFinite(index) || index < 0 || index >= this.studentList.length) {
        return null
      }
      return this.studentList[index]
    },
    requireStudentId: function(student) {
      const studentId = this.getStudentId(student)
      if (studentId) {
        return studentId
      }

      uni.showToast({
        title: '学生数据缺少ID，请刷新后重试',
        icon: 'none'
      })
      return ''
    },
    goDetailByIndex: function(studentIndex) {
      this.goDetail(this.getStudentByIndex(studentIndex))
    },
    openAdjustByIndex: function(studentIndex, changeType) {
      this.openAdjust(this.getStudentByIndex(studentIndex), changeType)
    },
    openUpgradeGradeByIndex: function(studentIndex) {
      this.openUpgradeGrade(this.getStudentByIndex(studentIndex))
    },
    handleDeleteStudentByIndex: function(studentIndex) {
      this.handleDeleteStudent(this.getStudentByIndex(studentIndex))
    },
    goDetail: function(student) {
      const studentId = this.requireStudentId(student)
      if (!studentId) {
        return
      }
      uni.navigateTo({
        url: ROUTES.ADMIN_STUDENT_DETAIL + '?studentId=' + studentId
      })
    },
    handleDeleteStudent: function(student) {
      // 删除属于高风险操作，先弹确认框；后端实际做的是软删除。
      const studentId = this.requireStudentId(student)
      if (!studentId) {
        return
      }

      uni.showModal({
        title: '删除学生',
        content: '确定删除该学生吗？删除后将不再显示在学生列表中。',
        confirmText: '确认删除',
        cancelText: '取消',
        success: async function(res) {
          if (!res.confirm) {
            return
          }

          try {
            const response = await deleteAdminStudent(studentId)
            await this.refreshCurrentGradeStudents()
            this.refreshGrades()
            uni.showToast({
              title: (response.data && response.data.message) || response.message || '学生删除成功',
              icon: 'none'
            })
          } catch (error) {
            uni.showToast({
              title: (error && error.message) || '学生删除失败',
              icon: 'none'
            })
          }
        }.bind(this)
      })
    },
    getStudentGrade: function(student) {
      const sourceGrade = student && student.grade ? student.grade : this.currentGrade
      const grade = String(sourceGrade || '').trim()
      return grade || DEFAULT_GRADE
    },
    getUpgradeTargetGrades: function(student) {
      // 年级只能往后升级，例如初一可以到初二/初三/高中，不能降级。
      const currentGrade = this.getStudentGrade(student)
      if (!currentGrade || currentGrade === DEFAULT_GRADE) {
        return STUDENT_GRADE_ORDER.slice()
      }

      const currentIndex = STUDENT_GRADE_ORDER.indexOf(currentGrade)
      if (currentIndex < 0) {
        return STUDENT_GRADE_ORDER.slice()
      }

      return STUDENT_GRADE_ORDER.slice(currentIndex + 1)
    },
    canUpgradeStudent: function(student) {
      return this.getUpgradeTargetGrades(student).length > 0
    },
    openUpgradeGrade: function(student) {
      if (!this.requireStudentId(student)) {
        return
      }

      const targetOptions = this.getUpgradeTargetGrades(student)
      if (!targetOptions.length) {
        uni.showToast({
          title: '当前已是最高年级，无法继续升级',
          icon: 'none'
        })
        return
      }

      this.upgradeStudent = student
      this.upgradeTargetGrade = targetOptions[0]
      this.upgradeVisible = true
    },
    closeUpgradeGrade: function() {
      if (this.upgrading) {
        return
      }
      this.upgradeVisible = false
      this.upgradeStudent = {}
      this.upgradeTargetGrade = ''
    },
    setUpgradeTargetGrade: function(grade) {
      if (this.upgradeTargetOptions.indexOf(grade) < 0) {
        return
      }
      this.upgradeTargetGrade = grade
    },
    submitUpgradeGrade: async function() {
      // 年级升级成功后，当前列表里这个学生可能不再属于当前年级，所以要刷新列表。
      if (this.upgrading) {
        return
      }

      const studentId = this.getStudentId(this.upgradeStudent)
      const targetGrade = String(this.upgradeTargetGrade || '').trim()

      if (!studentId || !targetGrade) {
        uni.showToast({
          title: '请选择目标年级',
          icon: 'none'
        })
        return
      }

      this.upgrading = true

      try {
        const response = await upgradeAdminStudentGrade(studentId, targetGrade)
        this.studentList = this.studentList.filter(function(item) {
          return this.getStudentId(item) !== studentId
        }, this)
        this.total = Math.max(0, Number(this.total || 0) - 1)
        this.upgrading = false
        this.closeUpgradeGrade()
        await this.refreshCurrentGradeStudents()
        await this.refreshGrades()
        uni.showToast({
          title: (response.data && response.data.message) || response.message || '学员年级升级成功',
          icon: 'none'
        })
      } catch (error) {
        uni.showToast({
          title: (error && error.message) || '学员年级升级失败',
          icon: 'none'
        })
      } finally {
        this.upgrading = false
      }
    },
    openAdjust: function(student, changeType) {
      // 打开加课/扣课弹窗时，把学生的科目列表转成 picker 可用的选项。
      if (!this.requireStudentId(student)) {
        return
      }
      const subjects = Array.isArray(student.subjects) ? student.subjects : []
      if (!subjects.length) {
        uni.showToast({
          title: '该学员暂无可调整科目',
          icon: 'none'
        })
        return
      }

      this.adjustStudent = student
      this.subjectList = subjects.map(function(item) {
        return Object.assign({}, item, {
          subjectName: item.subjectName || item.subject || '综合'
        })
      })
      this.subjectOptions = this.subjectList.map(function(item) {
        return item.subjectName
      })
      this.adjustForm = createAdjustForm(changeType, this.subjectOptions[0])
      this.adjustVisible = true
    },
    closeAdjust: function() {
      if (this.submitting || this.isConfirmingNegative) {
        return
      }
      this.adjustVisible = false
      this.adjustStudent = {}
      this.subjectList = []
      this.subjectOptions = []
      this.adjustForm = createAdjustForm('add', '')
    },
    handleSubjectChange: function(event) {
      this.adjustForm.subjectName = this.subjectOptions[event.detail.value]
    },
    setAdjustType: function(changeType) {
      this.adjustForm.changeType = changeType
      if (changeType === 'deduct') {
        this.adjustForm.amount = ''
      }
    },
    validateAdjustForm: function() {
      // 这里只校验输入格式；余额是否允许扣成负数由线上后端统一判断。
      const hours = Number(this.adjustForm.hours || 0)
      const amountText = String(this.adjustForm.amount || '')

      if (!this.adjustForm.subjectName) {
        uni.showToast({
          title: '请选择科目',
          icon: 'none'
        })
        return false
      }

      if (!/^\d+(\.\d+)?$/.test(String(this.adjustForm.hours || '')) || hours <= 0) {
        uni.showToast({
          title: '请输入正确的课时数',
          icon: 'none'
        })
        return false
      }

      if (this.adjustForm.changeType === 'add' && amountText && !/^\d+(\.\d+)?$/.test(amountText)) {
        uni.showToast({
          title: '请输入正确的加课金额',
          icon: 'none'
        })
        return false
      }

      return true
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
    buildLessonPayload: function() {
      const isDeduct = this.adjustForm.changeType === 'deduct'
      return {
        studentId: this.getStudentId(this.adjustStudent),
        subjectName: this.adjustForm.subjectName || '综合',
        changeType: this.adjustForm.changeType,
        hours: Number(this.adjustForm.hours),
        amount: isDeduct ? 0 : Number(this.adjustForm.amount || 0),
        recordDate: (this.adjustForm.recordDate || '').trim(),
        remark: (this.adjustForm.remark || (isDeduct ? '管理员手动扣课' : '管理员手动加课')).trim(),
        allowNegative: false
      }
    },
    finishAdjustSuccess: async function(response) {
      this.adjustVisible = false
      this.adjustStudent = {}
      this.subjectList = []
      this.subjectOptions = []
      this.adjustForm = createAdjustForm('add', '')

      await Promise.all([this.refreshCurrentGradeStudents(), this.refreshGrades()])
      uni.showToast({
        title: response.message || '操作成功',
        icon: 'none'
      })
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
        await this.finishAdjustSuccess(response)
      } catch (error) {
        uni.showToast({
          title: (error && error.message) || '扣课失败',
          icon: 'none'
        })
      } finally {
        this.isConfirmingNegative = false
      }
    },
    submitAdjust: async function() {
      // 课时调整会影响科目余额、课时流水，后端用事务一次性处理。
      if (this.submitting || this.isConfirmingNegative || !this.validateAdjustForm()) {
        return
      }

      const payload = this.buildLessonPayload()
      this.submitting = true

      try {
        const response = await changeLesson(payload)
        await this.finishAdjustSuccess(response)
      } catch (error) {
        if (this.isNegativeHoursConfirmError(error)) {
          this.submitting = false
          this.showNegativeHoursModal(error, payload)
          return
        }
        const message = (error && error.message) || '课时调整失败'
        uni.showToast({
          title: message,
          icon: 'none'
        })
      } finally {
        this.submitting = false
      }
    },
    handleAiQuery: async function() {
      // 管理员自然语言查询，例如“演示学员01数学还剩多少课时”。
      const queryText = (this.aiQueryText || '').trim()

      if (!queryText) {
        uni.showToast({
          title: '请输入要查询的问题',
          icon: 'none'
        })
        return
      }

      try {
        const res = await aiQuery(queryText)
        this.aiResultText = (res.data && res.data.answer) || '未查询到结果，请换个问法再试。'
      } catch (error) {
        if (error && error.code === 401) {
          this.aiResultText = '登录已失效，请重新登录'
          return
        }

        if (error && (error.errMsg || /网络请求失败/.test(error.message || ''))) {
          uni.showToast({
            title: '网络请求失败，请检查后端服务',
            icon: 'none'
          })
          this.aiResultText = '网络请求失败，请检查后端服务'
          return
        }

        this.aiResultText = (error && error.message) || '查询失败，请稍后重试'
      }
    },
    fillAiExample: function(exampleText) {
      this.aiQueryText = exampleText
      this.handleAiQuery()
    }
  }
}
</script>

<style lang="scss" scoped>
.admin-students-page {
  padding-bottom: 140rpx;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 22rpx;
}

.grade-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8rpx -16rpx;
}

.grade-card {
  width: calc(50% - 16rpx);
  min-height: 230rpx;
  margin: 0 8rpx 16rpx;
  padding: 22rpx;
  border: 1rpx solid #e6eef9;
  border-radius: 22rpx;
  background: #f8fbff;
}

.grade-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.grade-card__name {
  font-size: 32rpx;
  font-weight: 700;
  color: #1f2937;
}

.grade-card__line,
.grade-card__hours {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: #64748b;
}

.grade-card__hours {
  font-weight: 600;
  color: #2962ff;
}

.grade-card__hours.is-negative {
  color: #e5484d;
}

.grade-card__hours.is-zero {
  color: #64748b;
}

.grade-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.grade-toolbar__actions {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.grade-toolbar__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #64748b;
}

.mini-btn {
  flex: 0 0 auto;
  min-width: 180rpx;
  min-height: 64rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #eef4ff;
  font-size: 24rpx;
  color: #2962ff;
}

.filter-tabs {
  display: flex;
  flex-wrap: wrap;
  margin: 22rpx -8rpx 0;
}

.filter-tab {
  margin: 0 8rpx 16rpx;
  padding: 14rpx 22rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
}

.filter-tab--active {
  background: linear-gradient(135deg, rgba(41, 98, 255, 0.12), rgba(109, 118, 188, 0.14));
}

.filter-tab__text {
  font-size: 24rpx;
  color: #5b6473;
}

.filter-tab__text--active {
  color: #4156c9;
  font-weight: 600;
}

.class-type-choice-list {
  display: flex;
  flex-wrap: wrap;
  margin: 12rpx -8rpx 0;
}

.class-type-choice {
  min-height: 64rpx;
  margin: 0 8rpx 16rpx;
  padding: 0 22rpx;
  border: 1rpx solid #dbe7f6;
  border-radius: 999rpx;
  background: #f8fbff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.class-type-choice--active {
  border-color: #2962ff;
  background: #2962ff;
  box-shadow: 0 8rpx 18rpx rgba(41, 98, 255, 0.18);
}

.class-type-choice__text {
  font-size: 24rpx;
  line-height: 1.2;
  color: #475569;
}

.class-type-choice__text--active {
  color: #ffffff;
  font-weight: 600;
}

.compact-form-item {
  margin-top: 2rpx;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.student-card {
  padding: 24rpx;
  border-radius: 24rpx;
  border: 1rpx solid #e7eef8;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.05);
}

.student-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.student-card__title-wrap {
  flex: 1;
  min-width: 0;
}

.student-card__name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1.35;
  color: #111827;
}

.class-tag {
  display: inline-flex;
  margin-top: 12rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
}

.class-tag--vip {
  color: #ffffff;
  background: #2962ff;
}

.class-tag--small {
  color: #475569;
  background: #eef2f7;
}

.class-tag--mixed {
  color: #7c2d12;
  background: #ffedd5;
}

.class-tag--pair {
  color: #0f766e;
  background: #ccfbf1;
}

.remaining-pill {
  min-width: 150rpx;
  padding: 14rpx 16rpx;
  border-radius: 18rpx;
  background: #f2f7ff;
  text-align: center;
}

.remaining-pill__label,
.remaining-pill__value {
  display: block;
}

.remaining-pill__label {
  font-size: 22rpx;
  color: #64748b;
}

.remaining-pill__value {
  margin-top: 6rpx;
  font-size: 36rpx;
  font-weight: 800;
  color: #2962ff;
}

.remaining-pill.is-negative {
  background: #fff1f2;
}

.remaining-pill.is-negative .remaining-pill__label,
.remaining-pill.is-negative .remaining-pill__value {
  color: #e5484d;
}

.remaining-pill.is-zero {
  background: #f1f5f9;
}

.remaining-pill.is-zero .remaining-pill__label,
.remaining-pill.is-zero .remaining-pill__value {
  color: #64748b;
}

.student-info-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 18rpx -8rpx 0;
}

.student-info-item {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 14rpx;
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.student-info-label,
.student-info-value {
  display: block;
}

.student-info-label {
  font-size: 22rpx;
  color: #64748b;
}

.student-info-value {
  margin-top: 8rpx;
  font-size: 25rpx;
  line-height: 1.35;
  color: #1f2937;
  word-break: break-all;
}

.subject-list {
  margin-top: 8rpx;
  padding: 16rpx 0 2rpx;
  border-top: 1rpx solid #eef2f7;
}

.subject-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  padding: 10rpx 0;
}

.subject-row__name {
  flex: 0 0 100rpx;
  font-size: 25rpx;
  font-weight: 600;
  color: #1f2937;
}

.subject-row__text {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.55;
  text-align: right;
  color: #475569;
}

.subject-row__text.is-negative {
  color: #e5484d;
  font-weight: 600;
}

.subject-empty {
  display: block;
  font-size: 24rpx;
  color: #94a3b8;
}

.student-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 20rpx;
}

.action-btn {
  flex: 1 1 calc(50% - 14rpx);
  min-height: 70rpx;
  padding: 0 12rpx;
  border-radius: 999rpx;
  font-size: 25rpx;
}

.action-btn--plain {
  color: #2962ff;
  background: #eef4ff;
}

.action-btn--add {
  color: #ffffff;
  background: linear-gradient(135deg, #2962ff 0%, #4d8dff 100%);
}

.action-btn--deduct {
  color: #ffffff;
  background: linear-gradient(135deg, #ef4444 0%, #fb7185 100%);
}

.action-btn--upgrade {
  color: #0f766e;
  background: #ecfdf5;
}

.action-btn--delete {
  color: #ef4444;
  background: #fff1f2;
}

.ai-input-row {
  margin-top: 18rpx;
}

.ai-helper-list {
  display: flex;
  flex-wrap: wrap;
  margin: 18rpx -8rpx 0;
}

.ai-helper-item {
  margin: 0 8rpx 16rpx;
  padding: 14rpx 20rpx;
  border-radius: 18rpx;
  background: #f8fbff;
}

.ai-helper-item__text {
  font-size: 24rpx;
  line-height: 1.6;
  color: #5b6473;
}

.ai-result {
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f8fafc;
}

.ai-result__label {
  display: block;
  font-size: 24rpx;
  color: #64748b;
}

.ai-result__text {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  line-height: 1.8;
  color: #1f2937;
}

.ai-result__text.is-negative {
  color: #e5484d;
}

.popup-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.42);
}

.adjust-panel {
  width: 100%;
  max-height: 86vh;
  padding: 30rpx 24rpx calc(40rpx + env(safe-area-inset-bottom));
  border-radius: 28rpx 28rpx 0 0;
  background: #ffffff;
}

.adjust-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.adjust-panel__title {
  font-size: 34rpx;
  font-weight: 700;
  color: #111827;
}

.adjust-panel__close {
  font-size: 26rpx;
  color: #2962ff;
}

.current-grade-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  padding: 20rpx 22rpx;
  border-radius: 18rpx;
  background: #f2f7ff;
}

.current-grade-note__text {
  font-size: 28rpx;
  font-weight: 700;
  color: #2962ff;
}

.grade-target-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.grade-target-item {
  min-width: 144rpx;
  min-height: 70rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 22rpx;
  border-radius: 999rpx;
  border: 1rpx solid #dbe7f6;
  background: #f8fafc;
  font-size: 26rpx;
  color: #475569;
}

.grade-target-item--active {
  border-color: #2962ff;
  color: #ffffff;
  background: #2962ff;
}

.subject-note {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.subject-note__item {
  flex: 1;
  padding: 18rpx 12rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  text-align: center;
}

.subject-note__label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.subject-note__value {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: #2962ff;
}

.subject-note__value.is-negative {
  color: #e5484d;
}

.subject-note__value.is-zero {
  color: #64748b;
}

.type-switch {
  display: flex;
  gap: 14rpx;
}

.type-switch__item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 78rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  font-size: 27rpx;
  color: #475569;
}

.type-switch__item--add-active {
  color: #ffffff;
  background: linear-gradient(135deg, #2962ff 0%, #4d8dff 100%);
}

.type-switch__item--deduct-active {
  color: #ffffff;
  background: linear-gradient(135deg, #ef4444 0%, #fb7185 100%);
}

.submit-adjust-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 86rpx;
  margin-top: 8rpx;
  border-radius: 999rpx;
  color: #ffffff;
  font-size: 28rpx;
  background: linear-gradient(135deg, #2962ff 0%, #4d8dff 100%);
}

.submit-adjust-btn--deduct {
  background: linear-gradient(135deg, #ef4444 0%, #fb7185 100%);
}
</style>
