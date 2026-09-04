//本文件作用为请求封装（所有接口都走这里)
import config from '@/config'
import { ROLE, ROUTES, STORAGE_KEYS } from '@/utils/constants'

// 真机调试时最常见的问题不是代码错，而是手机访问不到电脑后端，所以这里把排查项集中写成错误提示。
const NETWORK_ERROR_MESSAGE =
  '网络请求失败，请检查：\n' +
  '1. 后端是否启动\n' +
  '2. baseURL 是否为电脑局域网 IP\n' +
  '3. 手机和电脑是否在同一 Wi-Fi\n' +
  '4. 后端是否使用 --host 0.0.0.0 启动\n' +
  '5. Windows 防火墙是否放行 8000 端口'

const isObject = function(value) {
  return Object.prototype.toString.call(value) === '[object Object]'
}

const isSensitiveLogKey = function(key) {
  const normalizedKey = String(key || '').toLowerCase()
  return (
    normalizedKey.indexOf('password') > -1 ||
    normalizedKey === 'authorization' ||
    normalizedKey === 'token' ||
    /token$/.test(normalizedKey)
  )
}

const sanitizeLogString = function(value) {
  return String(value || '')
    .replace(/("?(?:password|token|accessToken|refreshToken|authorization)"?\s*[:=]\s*)"?[^",\s}]+"?/gi, '$1"***"')
    .replace(/Bearer\s+[A-Za-z0-9._~+\/-]+/gi, 'Bearer ***')
}

// 仅用于控制台日志。返回新对象，不会修改真正发送给后端的请求数据。
export const sanitizeRequestData = function(value) {
  if (Array.isArray(value)) {
    return value.map(function(item) {
      return sanitizeRequestData(item)
    })
  }

  if (!isObject(value)) {
    return typeof value === 'string' ? sanitizeLogString(value) : value
  }

  return Object.keys(value).reduce(function(result, key) {
    result[key] = isSensitiveLogKey(key) ? '***' : sanitizeRequestData(value[key])
    return result
  }, {})
}

const toCamelKey = function(key) {
  return key.replace(/_([a-z])/g, function(_, letter) {
    return letter.toUpperCase()
  })
}

export const toCamelCaseDeep = function(value) {
  if (Array.isArray(value)) {
    return value.map(function(item) {
      return toCamelCaseDeep(item)
    })
  }

  if (!isObject(value)) {
    return value
  }

  return Object.keys(value).reduce(function(result, key) {
    // 后端通常返回 snake_case，例如 student_id；前端页面更习惯用 camelCase，例如 studentId。
    result[toCamelKey(key)] = toCamelCaseDeep(value[key])
    return result
  }, {})
}

const normalizeResponse = function(response) {
  // 统一响应格式：不管后端直接返回数组、对象，还是返回带 code 的对象，页面最终都按 res.data 使用。
  const camelResponse = toCamelCaseDeep(response)

  if (camelResponse && typeof camelResponse.code !== 'undefined') {
    return camelResponse
  }

  return {
    code: 0,
    message: '请求成功',
    data: camelResponse
  }
}

const buildUrl = function(url) {
  if (/^https?:\/\//.test(url)) {
    // 如果传进来已经是完整地址，就不再拼 baseURL。
    return url
  }

  const baseURL = (config.baseURL || '').replace(/\/$/, '')
  const path = (url || '').charAt(0) === '/' ? url : '/' + (url || '')
  return baseURL + path
}

const buildQueryString = function(data) {
  if (!isObject(data)) {
    return ''
  }

  return Object.keys(data)
    .filter(function(key) {
      const value = data[key]
      return value !== '' && value !== null && typeof value !== 'undefined'
    })
    .map(function(key) {
      return encodeURIComponent(key) + '=' + encodeURIComponent(String(data[key]))
    })
    .join('&')
}

const buildLogUrl = function(url, method, data) {
  if (method !== 'GET') {
    return url
  }

  const queryString = buildQueryString(data)
  if (!queryString) {
    return url
  }

  return url + (url.indexOf('?') > -1 ? '&' : '?') + queryString
}

const logRequestFailure = function(info) {
  console.error('[request failed]', {
    method: info.method,
    url: info.url,
    data: sanitizeRequestData(info.data),
    statusCode: info.statusCode,
    response: sanitizeRequestData(info.response),
    errMsg: sanitizeLogString(info.errMsg)
  })
}

const getBusinessCode = function(responseData) {
  if (!responseData) {
    return ''
  }
  if (typeof responseData.code !== 'undefined') {
    return responseData.code
  }
  if (responseData.detail && typeof responseData.detail.code !== 'undefined') {
    return responseData.detail.code
  }
  if (responseData.data && typeof responseData.data.code !== 'undefined') {
    return responseData.data.code
  }
  return ''
}

const shouldDeferBusinessToast = function(code) {
  return (
    code === 'PHONE_CLASS_DUPLICATE' ||
    code === 'MULTIPLE_ENROLLMENTS' ||
    code === 'INSUFFICIENT_HOURS' ||
    code === 'NEGATIVE_HOURS_CONFIRM_REQUIRED'
  )
}

const isBusinessFailure = function(response) {
  if (!response) {
    return false
  }
  if (response.success === false) {
    return true
  }
  const code = getBusinessCode(response)
  return (
    response.success !== true &&
    typeof code === 'string' &&
    !!code &&
    code !== '0' &&
    code !== 'OK' &&
    code !== 'SUCCESS'
  )
}

const parseBusinessErrorText = function(value) {
  if (typeof value !== 'string' || !value.trim()) {
    return null
  }

  try {
    return JSON.parse(value)
  } catch (error) {
    return null
  }
}

// 兼容 uni.request reject、完整 response、后端 JSON 以及 errMsg 中的 JSON。
export const extractBusinessError = function(error) {
  const parsedErrMsg = parseBusinessErrorText(error && error.errMsg)
  const parsedError = parseBusinessErrorText(error)
  const candidates = [
    error && error.response && error.response.data,
    error && error.response,
    error && error.data,
    parsedErrMsg,
    error && error.errMsg,
    parsedError,
    error
  ]

  for (let index = 0; index < candidates.length; index += 1) {
    const candidate = candidates[index]
    if (!candidate) {
      continue
    }
    if (
      typeof candidate.code !== 'undefined' ||
      (candidate.detail && typeof candidate.detail.code !== 'undefined') ||
      (candidate.data && typeof candidate.data.code !== 'undefined')
    ) {
      return candidate
    }
  }

  return candidates.find(function(candidate) {
    return !!candidate
  }) || {}
}

const getToken = function() {
  // 兼容新旧缓存 key，避免以前登录过的用户因为 key 改名而直接失效。
  return uni.getStorageSync('token') || uni.getStorageSync(STORAGE_KEYS.TOKEN) || uni.getStorageSync('jinbi_clean_token') || ''
}

const getLoginRoute = function() {
  // token 失效时，根据当前角色跳回学生登录页或管理员登录页。
  const userType = uni.getStorageSync(STORAGE_KEYS.USER_TYPE) || uni.getStorageSync('jinbi_clean_role') || ''
  return userType === ROLE.ADMIN ? ROUTES.ADMIN_LOGIN : ROUTES.LOGIN
}

const clearAuthStorage = function() {
  ;[
    STORAGE_KEYS.TOKEN,
    STORAGE_KEYS.USER_TYPE,
    STORAGE_KEYS.USER_INFO,
    STORAGE_KEYS.ADMIN_INFO,
    STORAGE_KEYS.STUDENT_INFO,
    'jinbi_clean_token',
    'jinbi_clean_role'
  ].forEach(function(key) {
    uni.removeStorageSync(key)
  })
}

const getErrorMessage = function(statusCode, responseData) {
  if (statusCode === 401) {
    return '登录已失效，请重新登录'
  }

  if (statusCode === 403) {
    return '无管理员权限'
  }

  if (statusCode >= 500) {
    return '服务器内部错误，请稍后重试'
  }

  if (responseData && typeof responseData.detail === 'string') {
    return responseData.detail
  }

  if (responseData && responseData.message) {
    return responseData.message
  }

  if (responseData && responseData.detail && responseData.detail.message) {
    return responseData.detail.message
  }

  if (statusCode === 400) {
    return '请求参数错误'
  }

  if (statusCode === 422) {
    return '参数校验失败'
  }

  return '请求失败'
}

const handleHttpError = function(statusCode, responseData) {
  // 后端 HTTP 状态码不是 2xx 时，会进入这里统一转成前端能理解的错误对象。
  const normalizedData = toCamelCaseDeep(responseData)
  const businessCode = getBusinessCode(normalizedData)
  const message = getErrorMessage(statusCode, normalizedData)
  const loginRoute = statusCode === 401 ? getLoginRoute() : ''
  const detailData = normalizedData && isObject(normalizedData.detail) ? normalizedData.detail : {}
  const errorData = Object.assign({}, normalizedData || {}, detailData)
  const shouldDeferToBusiness = (statusCode === 409 && !!businessCode) || shouldDeferBusinessToast(businessCode)

  if (!shouldDeferToBusiness) {
    uni.showToast({
      title: message,
      icon: 'none'
    })
  }

  if (statusCode === 401) {
    // 401 表示登录失效：清理本地 token，再重新进入登录页。
    clearAuthStorage()
    setTimeout(function() {
      uni.reLaunch({
        url: loginRoute
      })
    }, 500)
  }

  return {
    code: businessCode || statusCode,
    statusCode: statusCode,
    httpStatusCode: statusCode,
    message: message,
    data: errorData,
    response: {
      statusCode: statusCode,
      data: normalizedData
    },
    errMsg: message
  }
}

const showNetworkFailTip = function() {
  uni.showToast({
    title: '网络请求失败，请检查后端服务',
    icon: 'none'
  })
}

const runMockRequest = function(requestOptions, showLoading) {
  // mock 请求用于没有后端时演示页面，返回结构也会走 normalizeResponse，保证页面不用区分真假接口。
  return new Promise(function(resolve, reject) {
    setTimeout(function() {
      try {
        const response = normalizeResponse(
          requestOptions.mock({
            data: requestOptions.data || {},
            method: requestOptions.method || 'GET',
            url: requestOptions.url || ''
          })
        )

        if (showLoading) {
          uni.hideLoading()
        }

        if (response.code !== 0) {
          logRequestFailure({
            method: requestOptions.method || 'GET',
            url: requestOptions.url || '',
            data: requestOptions.data || {},
            statusCode: response.code,
            response: response,
            errMsg: response.message || 'mock request failed'
          })
          const businessCode = getBusinessCode(response)
          if (!shouldDeferBusinessToast(businessCode)) {
            uni.showToast({
              title: response.message || '请求失败',
              icon: 'none'
            })
          }
          reject(response)
          return
        }

        resolve(response)
      } catch (error) {
        if (showLoading) {
          uni.hideLoading()
        }

        uni.showToast({
          title: '请求处理失败',
          icon: 'none'
        })
        reject(error)
      }
    }, 180)
  })
}

export default function request(options) {
  // 项目里所有真实接口最终都会调用这个函数，相当于前端的“请求总闸门”。
  const requestOptions = options || {}
  const method = (requestOptions.method || 'GET').toUpperCase()
  const showLoading = !!requestOptions.showLoading
  const loadingText = requestOptions.loadingText || '加载中'
  const shouldUseMock = !!requestOptions.forceMock || (config.useMock && typeof requestOptions.mock === 'function')

  if (showLoading) {
    uni.showLoading({
      title: loadingText,
      mask: true
    })
  }

  if (shouldUseMock && typeof requestOptions.mock === 'function') {
    return runMockRequest(requestOptions, showLoading)
  }

  const token = getToken()
  const header = Object.assign(
    {
      'Content-Type': 'application/json'
    },
    requestOptions.header || {}
  )

  if (token) {
    // 后端 FastAPI 用 Bearer Token 校验登录态，所以这里把 token 放进 Authorization 请求头。
    header.Authorization = 'Bearer ' + token
  }

  const requestUrl = buildUrl(requestOptions.url || '')
  const requestData = requestOptions.data || {}
  const finalRequestUrl = method === 'GET' ? buildLogUrl(requestUrl, method, requestData) : requestUrl
  const logUrl = method === 'GET' ? buildLogUrl(requestUrl, method, sanitizeRequestData(requestData)) : requestUrl
  const finalRequestData = method === 'GET' ? {} : requestData

  // GET 参数拼到 URL 上，POST/PATCH/DELETE 参数放到 body 里。
  console.log('[request]', method, logUrl, sanitizeRequestData(requestData))
  console.log('[request token exists]', !!token)

  return new Promise(function(resolve, reject) {
    uni.request({
      url: finalRequestUrl,
      method: method,
      data: finalRequestData,
      header: header,
      timeout: requestOptions.timeout || config.requestTimeout,
      success: function(res) {
        if (showLoading) {
          uni.hideLoading()
        }

        const statusCode = res.statusCode || 0
        console.log('[response]', statusCode, sanitizeRequestData(res.data))

        if (statusCode >= 200 && statusCode < 300) {
          // 部分后端会用 HTTP 200 返回 success:false 的业务错误，这类响应也必须进入 catch。
          const normalizedResponse = normalizeResponse(res.data)
          if (isBusinessFailure(normalizedResponse)) {
            const businessCode = getBusinessCode(normalizedResponse)
            if (!shouldDeferBusinessToast(businessCode)) {
              uni.showToast({
                title: normalizedResponse.message || '请求失败',
                icon: 'none'
              })
            }
            reject(normalizedResponse)
            return
          }
          resolve(normalizedResponse)
          return
        }

        logRequestFailure({
          method: method,
          url: logUrl,
          data: requestData,
          statusCode: statusCode,
          response: res.data,
          errMsg: res.errMsg || ''
        })
        reject(handleHttpError(statusCode, res.data))
      },
      fail: function(error) {
        if (showLoading) {
          uni.hideLoading()
        }

        logRequestFailure({
          method: method,
          url: logUrl,
          data: requestData,
          statusCode: 0,
          response: error,
          errMsg: error && error.errMsg
        })

        showNetworkFailTip()

        reject({
          code: 0,
          message: NETWORK_ERROR_MESSAGE,
          url: logUrl,
          method: method,
          statusCode: 0,
          response: error,
          hasToken: !!token,
          errMsg: error && error.errMsg,
          data: error
        })
      }
    })
  })
}
