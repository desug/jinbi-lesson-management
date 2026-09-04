//本文件夹 复用学生详情和记录接口，组装管理员查看某
import { getAdminStudentDetail, getAdminStudentRecords } from '@/api/admin'

export const getAdminRecords = async function(data) {
  const studentId = data && (data.studentId || data.id)
  const detailRes = await getAdminStudentDetail(studentId)
  const recordsRes = await getAdminStudentRecords(studentId)

  return {
    code: 0,
    message: '请求成功',
    data: {
      studentName: detailRes.data.profile.name,
      list: recordsRes.data.list
    }
  }
}
