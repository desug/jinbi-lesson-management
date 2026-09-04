import storage from '@/utils/storage'
import { ROLE, STORAGE_KEYS } from '@/utils/constants'

const cloneData = function(data) {
  return JSON.parse(JSON.stringify(data))
}

const padNumber = function(value) {
  return value < 10 ? '0' + value : '' + value
}

const formatTime = function(date) {
  return (
    date.getFullYear() +
    '-' +
    padNumber(date.getMonth() + 1) +
    '-' +
    padNumber(date.getDate()) +
    ' ' +
    padNumber(date.getHours()) +
    ':' +
    padNumber(date.getMinutes())
  )
}

const createTime = function(dayOffset, hour, minute) {
  const date = new Date()
  date.setDate(date.getDate() + dayOffset)
  date.setHours(typeof hour === 'number' ? hour : 9)
  date.setMinutes(typeof minute === 'number' ? minute : 0)
  date.setSeconds(0)
  date.setMilliseconds(0)
  return formatTime(date)
}

const normalizeClassType = function(classType) {
  const text = String(classType || '').replace(/\s/g, '').replace(/＋/g, '+')
  const lowerText = text.toLowerCase()
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
  return text || '小班'
}

const getClassTypeText = function(classType) {
  const normalizedType = normalizeClassType(classType)
  const labels = {
    'VIP': 'VIP',
    '小班': '小班',
    '小班+一对一': '小班+一对一',
    '一对二': '一对二'
  }
  return labels[normalizedType] || normalizedType || '未设置班型'
}

const CREATE_CLASS_TYPES = ['VIP', '小班', '小班+一对一', '一对二']

const normalizeCreateClassType = function(classType) {
  const text = String(classType || '').replace(/\s/g, '').replace(/＋/g, '+')
  return CREATE_CLASS_TYPES.indexOf(text) > -1 ? text : ''
}

const UPGRADE_GRADE_ORDER = ['初一', '初二', '初三', '高一', '高二', '高三']
const DEFAULT_GRADE = '未分配'

const buildSubjectStatus = function(remainingHours) {
  if (remainingHours <= 0) {
    return '已用完'
  }

  if (remainingHours <= 5) {
    return '需关注'
  }

  return '正常'
}

const createSubject = function(subjectName, totalHours, remainingHours, deductedHours) {
  return {
    subjectName: subjectName,
    totalHours: totalHours,
    remainingHours: remainingHours,
    deductedHours: deductedHours
  }
}

const normalizeSubject = function(item) {
  const subjectName = item.subjectName || item.subject || ''
  const remainingHours = Number(item.remainingHours || 0)
  let deductedHours = typeof item.deductedHours !== 'undefined' ? Number(item.deductedHours) : Number(item.usedHours || 0)
  let totalHours = Number(item.totalHours || 0)

  if (deductedHours < 0) {
    deductedHours = 0
  }

  if (totalHours < remainingHours + deductedHours) {
    totalHours = remainingHours + deductedHours
  }

  return {
    subjectName: subjectName,
    subject: subjectName,
    totalHours: totalHours,
    remainingHours: remainingHours,
    deductedHours: deductedHours,
    usedHours: deductedHours
  }
}

const normalizeRecord = function(item) {
  const subjectName = item.subjectName || item.subject || ''

  return {
    id: item.id || 'R' + Date.now(),
    subjectName: subjectName,
    subject: subjectName,
    changeType: item.changeType === '增加' ? '增加' : '扣减',
    hours: Number(item.hours || 0),
    amount: Number(item.amount || 0),
    remainingHours: typeof item.remainingHours !== 'undefined' ? Number(item.remainingHours || 0) : null,
    time: item.time || formatTime(new Date()),
    recordDate: item.recordDate || item.time || formatTime(new Date()),
    remark: item.remark || '',
    operatorName: item.operatorName || '系统'
  }
}

const normalizeGallery = function(item, index) {
  return {
    id: item.id || 'G' + (index + 1),
    title: item.title || '图片预览',
    description: item.description || '用于展示学员图片内容的占位卡片'
  }
}

const normalizeStudent = function(item, index) {
  return {
    id: item.id || 'S' + padNumber(index + 1),
    studentNo: item.studentNo || item.student_no || item.id || 'S' + padNumber(index + 1),
    name: item.name || '学员' + (index + 1),
    parentName: item.parentName || '家长',
    phone: item.phone || '',
    grade: item.grade || '未分配',
    school: item.school || item.campus || '未设置学校',
    campus: item.campus || item.school || '未设置校区',
    adviser: item.adviser || '未设置顾问',
    classType: normalizeClassType(item.classType),
    subjects: (item.subjects || []).map(function(subjectItem) {
      return normalizeSubject(subjectItem)
    }),
    records: (item.records || []).map(function(recordItem) {
      return normalizeRecord(recordItem)
    }),
    gallery: (item.gallery || []).map(function(galleryItem, galleryIndex) {
      return normalizeGallery(galleryItem, galleryIndex)
    })
  }
}

const normalizeAdmin = function(item, index) {
  let account = item.account || ''

  if (!account || account === 'admin') {
    account = index === 0 ? '校区主管' : '教务老师' + (index + 1)
  }

  return {
    id: item.id || 'A' + padNumber(index + 1),
    account: account,
    password: item.password || 'demo-only-password',
    name: item.name || '管理员' + (index + 1),
    campus: item.campus || '演示资料03',
    position: item.position || '教务主管'
  }
}

const normalizeDatabase = function(database) {
  return {
    students: (database.students || []).map(function(studentItem, index) {
      return normalizeStudent(studentItem, index)
    }),
    admins: (database.admins || []).map(function(adminItem, index) {
      return normalizeAdmin(adminItem, index)
    })
  }
}

const createDefaultDatabase = function() {
  // Completely synthetic fixture. No real students, payments or phone contacts.
  return normalizeDatabase({
    students: [1, 2, 3].map(function(index) {
      return {
        id: 'DEMO' + index,
        studentNo: 'DEMO00' + index,
        name: '演示学员0' + index,
        parentName: '演示家长0' + index,
        phone: '1990000000' + index,
        grade: '初一',
        campus: '演示校区',
        adviser: '演示教师',
        classType: index === 1 ? 'vip' : 'small',
        subjects: [createSubject('数学', 20, 18, 2)],
        records: [{id: 'DEMORECORD' + index, subject: '数学', changeType: '扣减',
          hours: 2, amount: 0, time: createTime(-1, 10, 0),
          remark: '虚构演示课时记录', operatorName: '演示教师'}],
        gallery: []
      }
    }),
    admins: [{id: 'DEMOADMIN', account: '演示管理员', name: '演示教师',
      campus: '演示校区', position: '演示管理员', password: 'demo-only-password'}]
  })
}

export const getDatabase = function() {
  const cached = uni.getStorageSync(STORAGE_KEYS.MOCK_DATABASE)

  if (cached && cached.students && cached.admins) {
    const normalizedData = normalizeDatabase(cached)
    uni.setStorageSync(STORAGE_KEYS.MOCK_DATABASE, cloneData(normalizedData))
    return normalizedData
  }

  const initialData = createDefaultDatabase()
  uni.setStorageSync(STORAGE_KEYS.MOCK_DATABASE, cloneData(initialData))
  return initialData
}

export const saveDatabase = function(database) {
  const normalizedData = normalizeDatabase(database)
  uni.setStorageSync(STORAGE_KEYS.MOCK_DATABASE, cloneData(normalizedData))
}

export const getCurrentStudent = function() {
  const role = storage.getRole()
  const userInfo = storage.getUserInfo()
  const database = getDatabase()

  if (role === ROLE.STUDENT && userInfo && userInfo.id) {
    const target = database.students.find(function(item) {
      return item.id === userInfo.id
    })

    if (target) {
      return cloneData(target)
    }
  }

  return database.students.length ? cloneData(database.students[0]) : null
}

export const getStudentByPhone = function(phone, classType) {
  const database = getDatabase()
  const target = database.students.find(function(item) {
    if (item.phone !== phone) {
      return false
    }

    if (classType === 'vip' || classType === 'VIP') {
      return item.classType === 'VIP' || item.classType === 'vip'
    }

    return true
  })

  return target ? cloneData(target) : null
}

export const getStudentById = function(studentId) {
  const database = getDatabase()
  const target = database.students.find(function(item) {
    return item.id === studentId
  })
  return target ? cloneData(target) : null
}

export const getAdminByAccount = function(account, password) {
  const database = getDatabase()
  const target = database.admins.find(function(item) {
    return item.account === account && item.password === password
  })
  return target ? cloneData(target) : null
}

export const getSubjectCards = function(subjects) {
  return (subjects || []).map(function(item) {
    const normalizedItem = normalizeSubject(item)
    return {
      subjectName: normalizedItem.subjectName,
      subject: normalizedItem.subjectName,
      totalHours: Number(normalizedItem.totalHours || 0),
      remainingHours: Number(normalizedItem.remainingHours || 0),
      deductedHours: Number(normalizedItem.deductedHours || 0),
      usedHours: Number(normalizedItem.deductedHours || 0),
      statusText: buildSubjectStatus(Number(normalizedItem.remainingHours || 0))
    }
  })
}

export const getStudentSummary = function(student) {
  const result = (student.subjects || []).reduce(
    function(summary, item) {
      const normalizedItem = normalizeSubject(item)
      summary.totalHours += Number(normalizedItem.totalHours || 0)
      summary.deductedHours += Number(normalizedItem.deductedHours || 0)
      summary.remainingHours += Number(normalizedItem.remainingHours || 0)
      return summary
    },
    {
      totalHours: 0,
      deductedHours: 0,
      remainingHours: 0
    }
  )

  result.usedHours = result.deductedHours
  return result
}

export const buildRecordItem = function(record) {
  const subjectName = record.subjectName || record.subject || ''

  return {
    id: record.id,
    subjectName: subjectName,
    subject: subjectName,
    title: subjectName + (record.changeType === '增加' ? '课时增加' : '课时扣减'),
    time: record.time,
    description: record.remark ? '备注：' + record.remark : '操作人：' + (record.operatorName || '系统'),
    tagText: record.changeType === '增加' ? '已增加' : '已扣减',
    amount: (record.changeType === '增加' ? '+' : '-') + record.hours + ' 课时'
  }
}

export const buildStudentProfile = function(student) {
  return {
    id: student.id,
    name: student.name,
    parentName: student.parentName,
    phone: student.phone,
    studentNo: student.studentNo,
    grade: student.grade,
    school: student.school,
    campus: student.campus,
    adviser: student.adviser,
    classType: student.classType,
    classTypeText: getClassTypeText(student.classType),
    subjects: (student.subjects || []).map(function(item) {
      return item.subjectName || item.subject
    })
  }
}

export const getAdminStudentList = function(keyword, classType) {
  const database = getDatabase()
  const query = (keyword || '').replace(/\s/g, '')
  const currentClassType = classType && classType !== 'all' ? normalizeClassType(classType) : 'all'

  return database.students
    .map(function(item) {
      const summary = getStudentSummary(item)
      const subjectOverview = item.subjects
        .map(function(subjectItem) {
          const subjectName = subjectItem.subjectName || subjectItem.subject
          return subjectName + ' 剩余 ' + Number(subjectItem.remainingHours || 0) + ' 学时'
        })
        .join('；')

      return {
        id: item.id,
        name: item.name,
        phone: item.phone,
        studentNo: item.studentNo,
        grade: item.grade,
        school: item.school,
        campus: item.campus,
        classType: item.classType,
        classTypeText: getClassTypeText(item.classType),
        remainingHours: summary.remainingHours,
        deductedHours: summary.deductedHours,
        subjects: item.subjects
          .map(function(subjectItem) {
            return subjectItem.subjectName || subjectItem.subject
          })
          .join('、'),
        subjectOverview: subjectOverview
      }
    })
    .filter(function(item) {
      const matchClassType =
        currentClassType === 'all' || !currentClassType ? true : item.classType === currentClassType
      const matchKeyword = !query ? true : item.name.indexOf(query) > -1 || item.phone.indexOf(query) > -1

      if (!matchClassType) {
        return false
      }

      if (!query) {
        return true
      }

      return matchKeyword
    })
}

export const updateStudentHours = function(payload) {
  const database = getDatabase()
  const studentIndex = database.students.findIndex(function(item) {
    return item.id === payload.studentId
  })

  if (studentIndex === -1) {
    return {
      code: 1,
      message: '未找到对应学员'
    }
  }

  const student = database.students[studentIndex]
  const subjectIndex = student.subjects.findIndex(function(item) {
    return (item.subjectName || item.subject) === payload.subject
  })

  if (subjectIndex === -1) {
    return {
      code: 1,
      message: '未找到对应科目'
    }
  }

  const subject = student.subjects[subjectIndex]
  const hours = Number(payload.hours || 0)

  if (hours <= 0) {
    return {
      code: 1,
      message: '请输入正确的课时数量'
    }
  }

  if (payload.changeType === '扣减' && Number(subject.remainingHours || 0) < hours) {
    return {
      code: 1,
      message: '剩余课时不足，无法扣减'
    }
  }

  if (payload.changeType === '增加') {
    subject.totalHours = Number(subject.totalHours || 0) + hours
    subject.remainingHours = Number(subject.remainingHours || 0) + hours
  } else {
    subject.deductedHours = Number(subject.deductedHours || 0) + hours
    subject.remainingHours = Number(subject.remainingHours || 0) - hours
  }

  subject.subject = subject.subjectName || subject.subject
  subject.usedHours = Number(subject.deductedHours || 0)

  const newRecord = {
    id: 'R' + Date.now(),
    subjectName: subject.subjectName || payload.subject,
    subject: subject.subjectName || payload.subject,
    changeType: payload.changeType,
    hours: hours,
    amount: payload.changeType === '增加' ? Number(payload.amount || 0) : 0,
    remainingHours: Number(subject.remainingHours || 0),
    time: payload.recordDate || formatTime(new Date()),
    recordDate: payload.recordDate || formatTime(new Date()),
    remark: payload.remark,
    operatorName: payload.operatorName || '管理员'
  }

  student.records = [newRecord].concat(student.records || [])
  saveDatabase(database)

  return {
    code: 0,
    message: payload.changeType === '增加' ? '加课时成功' : '扣课时成功',
    data: {
      record: buildRecordItem(newRecord)
    }
  }
}

export const addAdminStudent = function(payload) {
  const database = getDatabase()
  const phone = String(payload.phone || '').trim()
  const existed = database.students.find(function(item) {
    return item.phone === phone
  })

  if (existed) {
    return {
      code: 1,
      message: '手机号已存在，请更换手机号'
    }
  }

  const totalHours = Number(payload.totalHours || 0)
  const totalPrice = Number(payload.totalPrice || 0)
  const grade = String(payload.grade || '').trim()
  const rawClassType = String(payload.classType || '').trim()
  const classType = normalizeCreateClassType(rawClassType)

  if (!grade) {
    return {
      code: 1,
      message: '请先选择年级后再添加学生'
    }
  }

  if (!rawClassType) {
    return {
      code: 1,
      message: '请选择班型'
    }
  }

  if (!classType) {
    return {
      code: 1,
      message: '班型不合法'
    }
  }

  const id = 'S' + Date.now()
  const studentNo = 'S' + new Date().getFullYear() + String(database.students.length + 1).padStart(4, '0')
  const recordTime = formatTime(new Date())
  const newRecord = {
    id: 'R' + Date.now(),
    subjectName: '综合',
    subject: '综合',
    changeType: '增加',
    hours: totalHours,
    amount: totalPrice,
    remainingHours: totalHours,
    time: recordTime,
    recordDate: recordTime,
    remark: '新建学生初始化课时',
    operatorName: '管理员'
  }
  const student = normalizeStudent(
    {
      id: id,
      studentNo: studentNo,
      name: String(payload.name || '').trim(),
      phone: phone,
      grade: grade,
      classType: classType,
      subjects: [createSubject('综合', totalHours, totalHours, 0)],
      records: [newRecord]
    },
    database.students.length
  )

  database.students.unshift(student)
  saveDatabase(database)

  return {
    code: 0,
    message: '学生添加成功',
    data: {
      id: student.id,
      name: student.name,
      phone: student.phone,
      studentNo: student.studentNo,
      classType: student.classType,
      grade: student.grade,
      totalHours: totalHours,
      remainingHours: totalHours,
      totalPrice: totalPrice
    }
  }
}

export const updateAdminStudentGrade = function(studentId, payload) {
  const database = getDatabase()
  const student = database.students.find(function(item) {
    return String(item.id) === String(studentId)
  })
  const targetGrade = String((payload && payload.targetGrade) || '').trim()

  if (!student) {
    return {
      code: 1,
      message: '未找到该学员'
    }
  }

  if (!targetGrade) {
    return {
      code: 1,
      message: '请选择目标年级'
    }
  }

  const targetIndex = UPGRADE_GRADE_ORDER.indexOf(targetGrade)
  const oldGrade = String(student.grade || DEFAULT_GRADE).trim() || DEFAULT_GRADE
  const oldIndex = UPGRADE_GRADE_ORDER.indexOf(oldGrade)

  if (targetIndex < 0 || (oldIndex >= 0 && targetIndex <= oldIndex)) {
    return {
      code: 1,
      message: '目标年级必须高于当前年级'
    }
  }

  student.grade = targetGrade
  saveDatabase(database)

  return {
    code: 0,
    message: '学员年级升级成功',
    data: {
      id: student.id,
      name: student.name,
      oldGrade: oldGrade,
      newGrade: targetGrade
    }
  }
}

export const removeAdminStudent = function(studentId) {
  const database = getDatabase()
  const beforeCount = database.students.length
  database.students = database.students.filter(function(item) {
    return item.id !== studentId
  })

  if (database.students.length === beforeCount) {
    return {
      code: 1,
      message: '未找到该学员'
    }
  }

  saveDatabase(database)
  return {
    code: 0,
    message: '学生删除成功',
    data: {
      id: studentId,
      isDeleted: true
    }
  }
}
