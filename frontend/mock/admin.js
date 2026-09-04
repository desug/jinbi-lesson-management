import {
  addAdminStudent,
  buildRecordItem,
  buildStudentProfile,
  getDatabase,
  getAdminStudentList,
  getStudentById,
  getStudentSummary,
  getSubjectCards,
  removeAdminStudent,
  updateAdminStudentGrade,
  updateStudentHours
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

export const getAdminHomeMock = function() {
  const list = getAdminStudentList('', 'all')
  const warningCount = list.filter(function(item) {
    return Number(item.remainingHours || 0) <= 5
  }).length

  return success({
    summary: {
      studentCount: list.length,
      warningCount: warningCount
    }
  })
}

export const createAdminStudentMock = function(payload) {
  return addAdminStudent(payload.data || {})
}

export const deleteAdminStudentMock = function(payload) {
  const match = String(payload.url || '').match(/\/admin\/students\/(.+)$/)
  return removeAdminStudent(match ? decodeURIComponent(match[1]) : '')
}

export const upgradeAdminStudentGradeMock = function(payload) {
  const match = String(payload.url || '').match(/\/admin\/students\/(.+)\/grade$/)
  return updateAdminStudentGrade(
    match ? decodeURIComponent(match[1]) : '',
    payload.data || {}
  )
}

export const getAdminStudentsMock = function(payload) {
  const data = payload.data || {}
  const list = getAdminStudentList(data.keyword, data.classType)
  return success({
    list: list,
    total: list.length
  })
}

export const getAdminGradesMock = function() {
  const database = getDatabase()
  const gradeMap = {}

  ;(database.students || []).forEach(function(student) {
    const grade = student.grade || '未分配'
    const summary = getStudentSummary(student)
    if (!gradeMap[grade]) {
      gradeMap[grade] = {
        grade: grade,
        studentCount: 0,
        vipCount: 0,
        smallCount: 0,
        smallVipCount: 0,
        oneToTwoCount: 0,
        totalRemainingHours: 0
      }
    }

    gradeMap[grade].studentCount += 1
    if (student.classType === 'VIP' || student.classType === 'vip') {
      gradeMap[grade].vipCount += 1
    } else if (student.classType === '小班' || student.classType === 'small') {
      gradeMap[grade].smallCount += 1
    } else if (student.classType === '小班+一对一') {
      gradeMap[grade].smallVipCount += 1
    } else if (student.classType === '一对二') {
      gradeMap[grade].oneToTwoCount += 1
    }
    gradeMap[grade].totalRemainingHours += Number(summary.remainingHours || 0)
  })

  return success({
    items: Object.keys(gradeMap).map(function(grade) {
      return gradeMap[grade]
    })
  })
}

export const getGradeStudentsMock = function(payload) {
  const data = payload.data || {}
  const match = String(payload.url || '').match(/\/admin\/grades\/(.+)\/students/)
  const grade = match ? decodeURIComponent(match[1]) : ''
  const list = getAdminStudentList(data.keyword, data.classType)
    .filter(function(student) {
      if (!grade) {
        return true
      }
      if (grade === '未分配') {
        return !student.grade || student.grade === '未分配'
      }
      return student.grade === grade
    })
    .sort(function(prev, next) {
      if (prev.classType !== next.classType) {
        return prev.classType === 'VIP' || prev.classType === 'vip' ? -1 : 1
      }
      return String(prev.name || '').localeCompare(String(next.name || ''), 'zh-Hans-CN')
    })

  return success({
    items: list,
    total: list.length
  })
}

export const getAdminStudentDetailMock = function(payload) {
  const data = payload.data || {}
  const student = getStudentById(data.id)

  if (!student) {
    return fail('未找到对应学员')
  }

  const summary = getStudentSummary(student)

  return success({
    profile: buildStudentProfile(student),
    summary: summary,
    subjects: getSubjectCards(student.subjects),
    recentRecords: (student.records || []).slice(0, 5).map(function(item) {
      return buildRecordItem(item)
    })
  })
}

export const adjustStudentHoursMock = function(payload) {
  const data = payload.data || {}
  return updateStudentHours(
    Object.assign({}, data, {
      subject: data.subjectName || data.subject,
      changeType: data.changeType === 'add' ? '增加' : data.changeType === 'deduct' ? '扣减' : data.changeType
    })
  )
}
