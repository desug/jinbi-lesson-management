import { buildRecordItem, getStudentById } from '@/mock/database'

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

export const getAdminRecordsMock = function(payload) {
  const data = payload.data || {}
  const student = getStudentById(data.id)

  if (!student) {
    return fail('未找到学员记录')
  }

  return success({
    studentName: student.name,
    list: (student.records || []).map(function(item) {
      return buildRecordItem(item)
    })
  })
}
