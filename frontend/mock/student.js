import {
  buildRecordItem,
  buildStudentProfile,
  getCurrentStudent,
  getStudentSummary,
  getSubjectCards
} from '@/mock/database'

const success = function(data, message) {
  return {
    code: 0,
    message: message || '请求成功',
    data: data
  }
}

const fail = function(message) {
  return {
    code: 1,
    message: message || '请求失败',
    data: null
  }
}

export const getStudentHomeMock = function() {
  const student = getCurrentStudent()

  if (!student) {
    return fail('未获取到学员信息')
  }

  const summary = getStudentSummary(student)

  return success({
    welcome: '欢迎回来，' + student.name,
    profile: buildStudentProfile(student),
    summary: {
      totalHours: summary.totalHours,
      deductedHours: summary.deductedHours,
      usedHours: summary.deductedHours,
      remainingHours: summary.remainingHours
    },
    subjects: getSubjectCards(student.subjects),
    latestRecords: (student.records || []).slice(0, 5).map(function(item) {
      return buildRecordItem(item)
    })
  })
}

export const getStudentProfileMock = function() {
  const student = getCurrentStudent()
  return student ? success(buildStudentProfile(student)) : fail('未获取到学员资料')
}

export const getStudentRecordsMock = function() {
  const student = getCurrentStudent()

  if (!student) {
    return fail('未获取到课时记录')
  }

  const summary = (student.records || []).reduce(
    function(result, item) {
      if (item.changeType === '增加') {
        result.added += Number(item.hours || 0)
      } else {
        result.deducted += Number(item.hours || 0)
      }
      return result
    },
    {
      added: 0,
      deducted: 0
    }
  )

  return success({
    summary: summary,
    list: (student.records || []).map(function(item) {
      return buildRecordItem(item)
    }),
    subjectSummary: getSubjectCards(student.subjects)
  })
}

export const getStudentPaymentsMock = function() {
  return success({
    title: '缴费记录',
    description: '该功能将在二期开放，当前先保留页面入口。'
  })
}

export const getStudentAiMock = function() {
  return success({
    title: '智能助手',
    description: '智能助手功能正在规划中，敬请期待。'
  })
}

export const getStudentGalleryMock = function() {
  const student = getCurrentStudent()
  return success({
    list: student ? student.gallery || [] : []
  })
}
