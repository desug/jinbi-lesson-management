import { getAdminByAccount, getStudentByPhone } from '@/mock/database'

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

export const studentLoginMock = function(payload) {
  const data = payload.data || {}
  const isVipEntry = data.loginEntry === 'vip'
  const student = getStudentByPhone(data.phone, isVipEntry ? 'vip' : '')

  if (!student) {
    return fail(isVipEntry ? '未找到对应的 VIP 学员，请确认手机号' : '未找到对应学员，请确认手机号')
  }

  return success(
    {
      token: 'student-token-' + student.id,
      role: 'student',
      userInfo: {
        id: student.id,
        name: student.name,
        phone: student.phone,
        grade: student.grade,
        campus: student.campus,
        classType: student.classType,
        classTypeText: student.classType === 'vip' ? 'VIP' : '小班'
      }
    },
    '登录成功'
  )
}

export const adminLoginMock = function(payload) {
  const data = payload.data || {}
  const admin = getAdminByAccount(data.account, data.password)

  if (!admin) {
    return fail('账号或密码不正确')
  }

  return success(
    {
      token: 'admin-token-' + admin.id,
      role: 'admin',
      userInfo: {
        id: admin.id,
        name: admin.name,
        campus: admin.campus,
        position: admin.position
      }
    },
    '登录成功'
  )
}

export const logoutMock = function() {
  return success({}, '退出成功')
}
