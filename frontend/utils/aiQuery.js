import { getDatabase, getSubjectCards } from '@/mock/database'

const normalizeText = function(text) {
  return (text || '')
    .replace(/\s+/g, '')
    .replace(/[，。！？、；：,.!?;:“”"'‘’（）()]/g, '')
    .trim()
}

const getStudentList = function() {
  const database = getDatabase()

  return (database.students || []).map(function(student) {
    return {
      id: student.id,
      name: student.name,
      classType: student.classType,
      subjects: getSubjectCards(student.subjects || [])
    }
  })
}

const findStudentByName = function(queryText, studentList) {
  const matchedList = studentList
    .filter(function(student) {
      return queryText.indexOf(student.name) > -1
    })
    .sort(function(prev, next) {
      return next.name.length - prev.name.length
    })

  return matchedList.length ? matchedList[0] : null
}

const findSubjectByName = function(queryText, studentList) {
  const subjectMap = {}

  studentList.forEach(function(student) {
    ;(student.subjects || []).forEach(function(subject) {
      if (subject.subjectName) {
        subjectMap[subject.subjectName] = subject.subjectName
      }
    })
  })

  const subjectList = Object.keys(subjectMap).sort(function(prev, next) {
    return next.length - prev.length
  })

  return subjectList.find(function(subjectName) {
    return queryText.indexOf(subjectName) > -1
  }) || ''
}

const detectIntent = function(queryText) {
  if (/班型|VIP|小班|一对一|一对二/.test(queryText)) {
    return 'classType'
  }

  if (/所有科目|全部科目|课时情况|课时汇总|课时概况|课时明细/.test(queryText)) {
    return 'summary'
  }

  if (/还剩|剩余|还有多少|多少课时|多少学时|课时|学时/.test(queryText)) {
    return 'subjectHours'
  }

  return 'unknown'
}

const buildSubjectSummaryText = function(student) {
  const subjectText = (student.subjects || [])
    .map(function(subject) {
      return (
        subject.subjectName +
        '共 ' +
        subject.totalHours +
        ' 学时，已扣除 ' +
        subject.deductedHours +
        ' 学时，剩余 ' +
        subject.remainingHours +
        ' 学时'
      )
    })
    .join('；')

  return student.name + '当前课时情况：' + subjectText + '。'
}

export const getAdminAiExampleList = function() {
  return [
    '演示学员01数学还剩多少课时',
    '初三VIP有哪些学生',
    '高一一对二有哪些学生'
  ]
}

export const parseAdminAiQuery = function(queryText) {
  const normalizedText = normalizeText(queryText)
  const studentList = getStudentList()

  if (!normalizedText) {
    return '请输入想查询的问题，例如“演示学员01英语还剩多少课时”。'
  }

  const targetStudent = findStudentByName(normalizedText, studentList)

  if (!targetStudent) {
    return '未找到对应学员，请检查姓名后重试。'
  }

  const intent = detectIntent(normalizedText)

  if (intent === 'classType') {
    return targetStudent.name + '当前班型为' + (targetStudent.classType === 'vip' || targetStudent.classType === 'VIP' ? 'VIP班型' : targetStudent.classType || '小班') + '。'
  }

  if (intent === 'summary') {
    return buildSubjectSummaryText(targetStudent)
  }

  if (intent === 'subjectHours') {
    const subjectName = findSubjectByName(normalizedText, studentList)

    if (!subjectName) {
      return '已识别到学员姓名，但未识别到科目，请补充科目名称。'
    }

    const targetSubject = (targetStudent.subjects || []).find(function(subject) {
      return subject.subjectName === subjectName
    })

    if (!targetSubject) {
      return '已识别到学员姓名，但未找到该学员的对应科目，请检查后重试。'
    }

    return (
      targetStudent.name +
      '当前' +
      targetSubject.subjectName +
      '共 ' +
      targetSubject.totalHours +
      ' 学时，已扣除 ' +
      targetSubject.deductedHours +
      ' 学时，剩余 ' +
      targetSubject.remainingHours +
      ' 学时。'
    )
  }

  return '暂时无法理解这句话，请尝试输入“演示学员01英语还剩多少课时”。'
}
