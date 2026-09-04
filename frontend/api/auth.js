//此文件 页面登录后调用这里，成功后保存token和用户信息，再跳转到对应首页
import request from '@/utils/request'
import storage from '@/utils/storage'
import { ROLE } from '@/utils/constants'
import { adminLoginMock, logoutMock, studentLoginMock } from '@/mock/auth'
import { normalizeStudentProfile } from '@/api/transform'

const saveLoginState = function(token, userType, info) {
  uni.setStorageSync('token', token || '')
  uni.setStorageSync('userType', userType || '')
  storage.setToken(token)
  storage.setUserType(userType)
  storage.setRole(userType)
  storage.setUserInfo(info)

  if (userType === ROLE.ADMIN) {
    storage.setAdminInfo(info)
  } else {
    storage.setStudentInfo(info)
  }
}

export const studentLogin = async function(phoneOrPayload) {
  const payload =
    typeof phoneOrPayload === 'object'
      ? phoneOrPayload || {}
      : {
          phone: phoneOrPayload
        }

  const res = await request({
    url: '/auth/student-login',
    method: 'POST',
    data: {
      phone: payload.phone,
      // 多班型二次登录优先传 studentId；保留 classType 仅兼容后端的旧约定。
      studentId: payload.studentId || payload.id,
      classType: payload.classType
    },
    showLoading: true,
    loadingText: '登录中',
    mock: studentLoginMock
  })

  const responseData = res.data || {}
  const loginData = responseData.data && responseData.data.token ? responseData.data : responseData
  const token = loginData.token
  const student = normalizeStudentProfile(loginData.user || loginData.student || {})

  if (!token) {
    throw Object.assign({}, res, {
      message: res.message || '登录响应缺少 token，请稍后重试'
    })
  }
  const data = {
    token: token,
    userType: ROLE.STUDENT,
    role: ROLE.STUDENT,
    student: student,
    userInfo: student
  }

  saveLoginState(token, ROLE.STUDENT, student)

  return Object.assign({}, res, {
    data: data
  })
}

export const adminLogin = async function(usernameOrPayload, password) {
  const payload =
    typeof usernameOrPayload === 'object'
      ? usernameOrPayload || {}
      : {
          username: usernameOrPayload,
          password: password
        }

  const res = await request({
    url: '/auth/admin-login',
    method: 'POST',
    data: {
      username: payload.username || payload.account,
      password: payload.password
    },
    showLoading: true,
    loadingText: '登录中',
    mock: adminLoginMock
  })

  const token = res.data.token
  const admin = res.data.admin || {}
  const data = {
    token: token,
    userType: ROLE.ADMIN,
    role: ROLE.ADMIN,
    admin: admin,
    userInfo: admin
  }

  saveLoginState(token, ROLE.ADMIN, admin)

  return Object.assign({}, res, {
    data: data
  })
}

export const logout = function() {
  storage.clearAuth()

  return request({
    url: '/auth/logout',
    method: 'POST',
    forceMock: true,
    mock: logoutMock
  })
}
