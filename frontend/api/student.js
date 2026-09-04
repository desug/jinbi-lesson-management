//学生端API 封装学生资料，课时记录，首页数据等接口
import request from '@/utils/request'
import storage from '@/utils/storage'
import {
  getStudentAiMock,
  getStudentGalleryMock,
  getStudentPaymentsMock,
  getStudentProfileMock,
  getStudentRecordsMock
} from '@/mock/student'
import {
  buildStudentHomeData,
  normalizeRecords,
  normalizeStudentProfile,
  summarizeRecords
} from '@/api/transform'

export const getStudentProfile = async function() {
  const res = await request({
    url: '/student/profile',
    method: 'GET',
    mock: getStudentProfileMock
  })

  const profile = normalizeStudentProfile(res.data)
  storage.setStudentInfo(profile)
  storage.setUserInfo(profile)

  return Object.assign({}, res, {
    data: profile
  })
}

export const getStudentRecords = async function() {
  const res = await request({
    url: '/student/records',
    method: 'GET',
    mock: getStudentRecordsMock
  })

  const source = res.data || {}
  const sourceList = Array.isArray(source)
    ? source
    : Array.isArray(source.data)
      ? source.data
      : Array.isArray(source.list)
        ? source.list
        : []
  const list = normalizeRecords(sourceList)
  const cachedProfile = normalizeStudentProfile(storage.getStudentInfo() || storage.getUserInfo() || {})
  let subjectSummary = cachedProfile.subjects || []

  if (!subjectSummary.length) {
    try {
      const profileRes = await getStudentProfile()
      subjectSummary = profileRes.data.subjects || []
    } catch (error) {
      subjectSummary = []
    }
  }

  return Object.assign({}, res, {
    data: {
      summary: summarizeRecords(list),
      list: list,
      subjectSummary: subjectSummary
    }
  })
}

export const getStudentHome = async function() {
  const profileRes = await getStudentProfile()
  const recordsRes = await getStudentRecords()

  return {
    code: 0,
    message: '请求成功',
    data: buildStudentHomeData(profileRes.data, recordsRes.data.list)
  }
}

export const getStudentPayments = function() {
  return request({
    url: '/student/payments',
    method: 'GET',
    forceMock: true,
    mock: getStudentPaymentsMock
  })
}

export const getStudentAi = function() {
  return request({
    url: '/student/ai',
    method: 'GET',
    forceMock: true,
    mock: getStudentAiMock
  })
}

export const getStudentGallery = function() {
  return request({
    url: '/student/gallery',
    method: 'GET',
    forceMock: true,
    mock: getStudentGalleryMock
  })
}
