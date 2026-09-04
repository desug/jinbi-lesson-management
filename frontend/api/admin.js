//本文件为管理员端API 封装学生列表，年纪列表，创建学生，删除学生，加口课时，AI查询等管理员功能
import request from '@/utils/request'
import {
  adjustStudentHoursMock,
  createAdminStudentMock,
  deleteAdminStudentMock,
  upgradeAdminStudentGradeMock
} from '@/mock/admin'
import {
  buildAdminHomeData,
  buildAdminStudentDetailData,
  buildAdminStudentListData,
  normalizeRecords
} from '@/api/transform'
import { isCreateClassType } from '@/utils/classTypes'

const pickStudentItems = function(data) {
  const source = data || {}
  if (Array.isArray(source)) {
    return source
  }
  if (Array.isArray(source.items)) {
    return source.items
  }
  if (Array.isArray(source.list)) {
    return source.list
  }
  return []
}

const pickStudentTotal = function(data, listLength) {
  const source = data || {}
  if (typeof source.total !== 'undefined') {
    return Number(source.total || 0)
  }
  return listLength
}

const pickRecordList = function(res) {
  const source = (res && res.data) || {}
  if (Array.isArray(res)) {
    return res
  }
  if (res && Array.isArray(res.data)) {
    return res.data
  }
  if (res && res.data && Array.isArray(res.data.data)) {
    return res.data.data
  }
  if (res && res.success && Array.isArray(res.data)) {
    return res.data
  }
  if (Array.isArray(source)) {
    return source
  }
  if (Array.isArray(source.list)) {
    return source.list
  }
  if (source.data && Array.isArray(source.data.list)) {
    return source.data.list
  }
  return []
}

export const getAdminStudents = async function(params) {
  const query = params || {}
  const res = await request({
    url: '/admin/students',
    method: 'GET',
    data: query
  })

  const sourceList = pickStudentItems(res.data)
  const listData = buildAdminStudentListData(sourceList, query)

  return Object.assign({}, res, {
    data: Object.assign({}, listData, {
      total: pickStudentTotal(res.data, listData.list.length)
    })
  })
}

export const getAdminGrades = async function() {
  const res = await request({
    url: '/admin/grades',
    method: 'GET'
  })

  const source = res.data || {}
  const items = Array.isArray(source.items) ? source.items : Array.isArray(source.list) ? source.list : []

  return Object.assign({}, res, {
    data: {
      items: items,
      list: items
    }
  })
}

export const getGradeStudents = async function(grade, params) {
  const query = params || {}
  const res = await request({
    url: '/admin/grades/' + encodeURIComponent(grade) + '/students',
    method: 'GET',
    data: query
  })

  const sourceList = pickStudentItems(res.data)
  const listData = buildAdminStudentListData(sourceList, query)

  return Object.assign({}, res, {
    data: Object.assign({}, listData, {
      items: listData.list,
      total: pickStudentTotal(res.data, listData.list.length)
    })
  })
}

export const getAdminHome = async function() {
  const studentsRes = await request({
    url: '/admin/students',
    method: 'GET'
  })
  const sourceList = pickStudentItems(studentsRes.data)

  return {
    code: 0,
    message: '请求成功',
    data: buildAdminHomeData(sourceList)
  }
}

export const createAdminStudent = async function(data) {
  const payload = data || {}
  if (!isCreateClassType(payload.classType)) {
    throw {
      code: 'INVALID_CLASS_TYPE',
      message: '新增学生仅支持 VIP、小班、一对二班型'
    }
  }
  return request({
    url: '/admin/students',
    method: 'POST',
    data: {
      name: payload.name,
      phone: payload.phone,
      totalHours: payload.totalHours,
      totalPrice: payload.totalPrice,
      grade: payload.grade,
      classType: payload.classType
    },
    showLoading: true,
    loadingText: '提交中',
    mock: createAdminStudentMock
  })
}

export const deleteAdminStudent = async function(studentId) {
  return request({
    url: '/admin/students/' + studentId,
    method: 'DELETE',
    showLoading: true,
    loadingText: '删除中',
    mock: deleteAdminStudentMock
  })
}

export const upgradeAdminStudentGrade = async function(studentId, targetGrade) {
  return request({
    url: '/admin/students/' + studentId + '/grade',
    method: 'PATCH',
    data: {
      targetGrade: targetGrade
    },
    showLoading: true,
    loadingText: '升级中',
    mock: upgradeAdminStudentGradeMock
  })
}

export const getAdminStudentDetail = async function(studentIdOrPayload) {
  const studentId =
    typeof studentIdOrPayload === 'object'
      ? studentIdOrPayload.studentId || studentIdOrPayload.id
      : studentIdOrPayload
  const res = await request({
    url: '/admin/students/' + studentId,
    method: 'GET',
    data: {
      id: studentId
    }
  })

  const profile = res.data.profile || res.data

  return Object.assign({}, res, {
    data: buildAdminStudentDetailData(profile, res.data.recentRecords || [])
  })
}

export const getAdminStudentRecords = async function(studentId) {
  const res = await request({
    url: '/admin/students/' + studentId + '/records',
    method: 'GET'
  })

  const sourceList = pickRecordList(res)
  const list = normalizeRecords(sourceList)

  return Object.assign({}, res, {
    data: {
      list: list,
      total: list.length
    }
  })
}

export const changeLesson = async function(data) {
  const payload = data || {}
  const changeType = payload.changeType === '增加' || payload.changeType === 'add' ? 'add' : 'deduct'
  const res = await request({
    url: '/admin/lesson/change',
    method: 'POST',
    data: {
      studentId: payload.studentId,
      subjectName: payload.subjectName || payload.subject || '综合',
      changeType: changeType,
      hours: payload.hours,
      amount: Number(payload.amount || 0),
      recordDate: payload.recordDate,
      remark: payload.remark,
      allowNegative: payload.allowNegative === true
    },
    showLoading: true,
    loadingText: '提交中',
    mock: adjustStudentHoursMock
  })

  // 兼容请求层把业务 JSON（或完整 response）直接 resolve 的情况，避免把确认警告误判成扣课成功。
  const businessResponse = res && res.data && res.data.code === 'NEGATIVE_HOURS_CONFIRM_REQUIRED' ? res.data : res
  if (businessResponse && businessResponse.code === 'NEGATIVE_HOURS_CONFIRM_REQUIRED') {
    throw Object.assign({}, businessResponse, {
      response: {
        data: businessResponse
      }
    })
  }

  return Object.assign({}, res, {
    message: (res.data && res.data.message) || res.message || (changeType === 'add' ? '加课时成功' : '扣课时成功')
  })
}

export const adjustStudentHours = function(data) {
  return changeLesson(data)
}

export const aiQuery = async function(query) {
  const res = await request({
    url: '/admin/ai-query',
    method: 'POST',
    data: {
      query: query
    },
    showLoading: true,
    loadingText: '正在查询...'
  })

  if (res.data && res.data.data) {
    console.log('[admin ai query data]', res.data.data)
  }

  return res
}

export const queryAdminAi = aiQuery
