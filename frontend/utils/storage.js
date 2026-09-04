//此文件用于登录态缓存封装(把token，用户角色，学生信息，管理员信息统一封装，避免页面直接操作storage)
import { STORAGE_KEYS } from '@/utils/constants'

const setItem = function(key, value) {
  uni.setStorageSync(key, value)
}

const getItem = function(key, defaultValue) {
  const value = uni.getStorageSync(key)
  return value === '' || typeof value === 'undefined' ? defaultValue : value
}

const removeItem = function(key) {
  uni.removeStorageSync(key)
}

const removeLegacyAuth = function() {
  removeItem('jinbi_clean_token')
  removeItem('jinbi_clean_role')
}

const storage = {
  setToken: function(token) {
    setItem(STORAGE_KEYS.TOKEN, token || '')
  },
  getToken: function() {
    return getItem(STORAGE_KEYS.TOKEN, '') || getItem('jinbi_clean_token', '')
  },
  setUserType: function(userType) {
    setItem(STORAGE_KEYS.USER_TYPE, userType || '')
  },
  getUserType: function() {
    return getItem(STORAGE_KEYS.USER_TYPE, '') || getItem('jinbi_clean_role', '')
  },
  setRole: function(role) {
    this.setUserType(role)
  },
  getRole: function() {
    return this.getUserType()
  },
  setUserInfo: function(userInfo) {
    setItem(STORAGE_KEYS.USER_INFO, userInfo || {})
  },
  getUserInfo: function() {
    return getItem(STORAGE_KEYS.USER_INFO, {})
  },
  setAdminInfo: function(admin) {
    setItem(STORAGE_KEYS.ADMIN_INFO, admin || {})
  },
  getAdminInfo: function() {
    return getItem(STORAGE_KEYS.ADMIN_INFO, {})
  },
  setStudentInfo: function(student) {
    setItem(STORAGE_KEYS.STUDENT_INFO, student || {})
  },
  getStudentInfo: function() {
    return getItem(STORAGE_KEYS.STUDENT_INFO, {})
  },
  clearAuth: function() {
    removeItem(STORAGE_KEYS.TOKEN)
    removeItem(STORAGE_KEYS.ROLE)
    removeItem(STORAGE_KEYS.USER_TYPE)
    removeItem(STORAGE_KEYS.USER_INFO)
    removeItem(STORAGE_KEYS.ADMIN_INFO)
    removeItem(STORAGE_KEYS.STUDENT_INFO)
    removeLegacyAuth()
  }
}

export default storage
