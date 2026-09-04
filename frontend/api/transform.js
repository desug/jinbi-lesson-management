import { toCamelCaseDeep } from '@/utils/request'

const padNumber = function(value) {
  return value < 10 ? '0' + value : '' + value
}

const pickDefined = function() {
  for (let index = 0; index < arguments.length; index += 1) {
    if (typeof arguments[index] !== 'undefined' && arguments[index] !== null && arguments[index] !== '') {
      return arguments[index]
    }
  }
  return ''
}

const formatDateTime = function(value) {
  if (!value) {
    return ''
  }

  const textValue = String(value).replace('T', ' ')
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(textValue)) {
    return textValue.slice(0, 19)
  }

  const date = new Date(textValue.replace(/-/g, '/'))

  if (isNaN(date.getTime())) {
    return textValue.slice(0, 19)
  }

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
    ':' +
    padNumber(date.getSeconds())
  )
}

const formatHours = function(value) {
  const numberValue = Number(value || 0)
  if (!isFinite(numberValue)) {
    return '0'
  }
  return numberValue % 1 === 0 ? String(numberValue) : numberValue.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}

const formatMoney = function(value) {
  const numberValue = Number(value || 0)
  return '¥' + (isFinite(numberValue) ? numberValue : 0).toFixed(2)
}

export const normalizeClassType = function(classType) {
  const text = String(classType || '').replace(/\s/g, '').replace(/＋/g, '+')
  const lowerText = text.toLowerCase()

  if (!text) {
    return '小班'
  }
  if (text === 'VIP' || lowerText === 'vip' || text === '一对一') {
    return 'VIP'
  }
  if (text === '小班' || lowerText === 'small') {
    return '小班'
  }
  if (text === '小班+一对一' || lowerText === '小班+vip' || text === '小班一对一') {
    return '小班+一对一'
  }
  if (text === '一对二') {
    return '一对二'
  }
  return text
}

export const getClassTypeText = function(classType) {
  const normalizedType = normalizeClassType(classType)
  const labelMap = {
    'VIP': 'VIP',
    '小班': '小班',
    '小班+一对一': '小班+一对一（历史）',
    '一对二': '一对二'
  }
  return labelMap[normalizedType] || normalizedType || '未设置班型'
}

const buildSubjectStatus = function(remainingHours) {
  if (remainingHours < 0) {
    return '欠课时'
  }

  if (remainingHours === 0) {
    return '已用完'
  }

  if (remainingHours <= 5) {
    return '需关注'
  }

  return '正常'
}

export const normalizeSubject = function(item) {
  const source = toCamelCaseDeep(item || {})
  const subjectName = source.subjectName || source.subject || ''
  const totalHours = Number(source.totalHours || 0)
  const remainingHours = Number(source.remainingHours || 0)
  const deductedHours = Number(source.deductedHours || source.usedHours || 0)

  return Object.assign({}, source, {
    subjectName: subjectName,
    subject: subjectName,
    totalHours: totalHours,
    remainingHours: remainingHours,
    deductedHours: deductedHours,
    usedHours: deductedHours,
    statusText: buildSubjectStatus(remainingHours)
  })
}

export const normalizeSubjects = function(subjects) {
  return (subjects || []).map(function(item) {
    return normalizeSubject(item)
  })
}

export const summarizeSubjects = function(subjects) {
  const summary = normalizeSubjects(subjects).reduce(
    function(summary, item) {
      summary.totalHours += Number(item.totalHours || 0)
      summary.deductedHours += Number(item.deductedHours || 0)
      summary.remainingHours += Number(item.remainingHours || 0)
      return summary
    },
    {
      totalHours: 0,
      deductedHours: 0,
      usedHours: 0,
      remainingHours: 0
    }
  )

  summary.usedHours = summary.deductedHours
  return summary
}

export const normalizeStudentProfile = function(data) {
  const source = toCamelCaseDeep(data || {})
  const subjects = normalizeSubjects(source.subjects || [])
  const classType = normalizeClassType(source.classType)
  const school = source.school || source.schoolName || source.campus || ''

  return Object.assign({}, source, {
    // 后端可能返回 student_id；请求层转驼峰后是 studentId。统一保留两个字段，
    // 具体学员的详情、删除、课时和流水操作都以这条记录的 studentId 为准。
    id: source.id || source.studentId,
    studentId: source.studentId || source.id,
    name: source.name || '未设置姓名',
    parentName: source.parentName || '未设置',
    phone: source.phone || '',
    studentNo: source.studentNo || source.id || source.studentId || '',
    grade: source.grade || '未设置',
    school: school || '未设置学校',
    campus: source.campus || school || '未设置校区',
    adviser: source.adviser || '未设置顾问',
    avatar: source.avatar || '',
    classType: classType,
    classTypeText: source.classTypeText || getClassTypeText(classType),
    subjects: subjects
  })
}

export const normalizeRecord = function(item) {
  const source = toCamelCaseDeep(item || {})
  const subjectName = source.subjectName || source.subject || ''
  const rawChangeType = pickDefined(source.changeType, source.type, source.action)
  const isAdd = rawChangeType === 'add' || rawChangeType === '增加' || rawChangeType === '加课时'
  const changeTypeValue = isAdd ? 'add' : 'deduct'
  const displayChangeType = isAdd ? '增加' : '扣减'
  const changeTypeText = source.changeTypeText || (isAdd ? '加课时' : '扣课时')
  const hours = Number(pickDefined(source.hours, source.changeHours, source.changeHour, 0) || 0)
  const rawPaymentAmount = Number(pickDefined(source.amount, source.paymentAmount, 0) || 0)
  const paymentAmount = isFinite(rawPaymentAmount) ? rawPaymentAmount : 0
  const remainingHours = Number(pickDefined(source.remainingHours, source.remainHours, source.remaining, 0) || 0)
  const time = formatDateTime(pickDefined(source.recordDate, source.createdAt, source.time, source.created_at))
  const remarkText = source.remark || '-'
  const displayHours = pickDefined(source.displayHours, source.signedHours, '')
  const signedHoursText = displayHours
    ? String(displayHours) + (String(displayHours).indexOf('课时') > -1 ? '' : '课时')
    : (isAdd ? '+' : '-') + formatHours(hours) + '课时'
  const descriptionParts = []

  descriptionParts.push('金额：' + formatMoney(paymentAmount))
  descriptionParts.push('剩余课时：' + formatHours(remainingHours))
  descriptionParts.push('备注：' + remarkText)

  return Object.assign({}, source, {
    subjectName: subjectName,
    subject: subjectName,
    changeType: displayChangeType,
    changeTypeValue: changeTypeValue,
    changeTypeText: changeTypeText,
    hours: hours,
    displayHours: displayHours || (isAdd ? '+' : '-') + formatHours(hours),
    hoursText: signedHoursText,
    signedHoursText: signedHoursText,
    time: time,
    operatorName: source.operatorName || '系统',
    title: changeTypeText,
    description: descriptionParts.join(' / '),
    tagText: subjectName || '综合',
    paymentAmount: paymentAmount,
    amountValue: paymentAmount,
    amountText: formatMoney(paymentAmount),
    remainingHours: remainingHours,
    remainingHoursText: formatHours(remainingHours),
    remarkText: remarkText,
    amount: signedHoursText
  })
}

export const normalizeRecords = function(records) {
  return (records || [])
    .map(function(item, index) {
      return {
        index: index,
        record: normalizeRecord(item)
      }
    })
    .sort(function(left, right) {
      const leftTime = new Date(String(left.record.time || '').replace(/-/g, '/')).getTime()
      const rightTime = new Date(String(right.record.time || '').replace(/-/g, '/')).getTime()
      if (!isNaN(leftTime) && !isNaN(rightTime) && leftTime !== rightTime) {
        return rightTime - leftTime
      }
      return left.index - right.index
    })
    .map(function(item) {
      return item.record
    })
}

export const summarizeRecords = function(records) {
  return normalizeRecords(records).reduce(
    function(summary, item) {
      if (item.changeType === '增加') {
        summary.added += Number(item.hours || 0)
      } else {
        summary.deducted += Number(item.hours || 0)
      }
      return summary
    },
    {
      added: 0,
      deducted: 0
    }
  )
}

export const buildStudentHomeData = function(profile, records) {
  const normalizedProfile = normalizeStudentProfile(profile)
  const normalizedRecords = normalizeRecords(records)
  const summary = summarizeSubjects(normalizedProfile.subjects)

  return {
    welcome: '欢迎回来，' + normalizedProfile.name,
    profile: normalizedProfile,
    summary: summary,
    subjects: normalizedProfile.subjects,
    latestRecords: normalizedRecords.slice(0, 5)
  }
}

export const buildAdminStudentListData = function(studentList, params) {
  const query = String((params && params.keyword) || '').replace(/\s/g, '')
  const rawClassType = String((params && params.classType) || 'all')
  const classType = rawClassType === 'all' ? 'all' : normalizeClassType(rawClassType)
  const list = (studentList || [])
    .map(function(item) {
      const profile = normalizeStudentProfile(item)
      const summary = summarizeSubjects(profile.subjects)
      const subjectOverview = profile.subjects
        .map(function(subject) {
          return subject.subjectName + ' 剩余 ' + Number(subject.remainingHours || 0) + ' 学时'
        })
        .join('；')

      return Object.assign({}, profile, {
        totalHours: summary.totalHours,
        remainingHours: summary.remainingHours,
        deductedHours: summary.deductedHours,
        subjectNames: profile.subjects
          .map(function(subject) {
            return subject.subjectName
          })
          .join('、'),
        subjects: profile.subjects,
        subjectOverview: subjectOverview
      })
    })
    .filter(function(item) {
      const matchClassType = classType === 'all' || !classType ? true : item.classType === classType
      const matchKeyword = !query
        ? true
        : String(item.name || '').indexOf(query) > -1 ||
          String(item.phone || '').indexOf(query) > -1 ||
          String(item.studentNo || '').indexOf(query) > -1
      return matchClassType && matchKeyword
    })

  return {
    list: list,
    total: list.length
  }
}

export const buildAdminStudentDetailData = function(profile, records) {
  const normalizedProfile = normalizeStudentProfile(profile)
  const normalizedRecords = normalizeRecords(records || [])
  const summary = summarizeSubjects(normalizedProfile.subjects)

  return {
    profile: normalizedProfile,
    summary: summary,
    subjects: normalizedProfile.subjects,
    recentRecords: normalizedRecords.slice(0, 5)
  }
}

export const buildAdminHomeData = function(studentList) {
  const listData = buildAdminStudentListData(studentList, {})
  const warningCount = listData.list.filter(function(item) {
    return Number(item.remainingHours || 0) <= 5
  }).length

  return {
    summary: {
      studentCount: listData.total,
      warningCount: warningCount
    }
  }
}
