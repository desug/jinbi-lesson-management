import traceback

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.admin import (
    AdminCreateStudentRequest,
    AdminCreateStudentResponse,
    AdminDeleteStudentResponse,
    AdminGradeListResponse,
    AdminStudentListResponse,
    AdminUpgradeStudentGradeRequest,
    AdminUpgradeStudentGradeResponse,
)
from app.schemas.auth import TokenPayload
from app.schemas.lesson import AdminLessonRecordsResponse, LessonChangeRequest, LessonChangeResponse
from app.schemas.student import StudentProfileResponse
from app.services.admin_service import (
    INSUFFICIENT_HOURS_CODE,
    change_lesson_hours,
    create_student,
    delete_student,
    get_student_detail,
    list_grade_summaries,
    list_student_records_by_admin,
    list_students,
    list_students_by_grade,
    upgrade_student_grade,
)
from app.utils.deps import get_current_admin, get_db


# 这个 router 下所有接口都会自动带上 /admin 前缀，例如 /admin/students。
router = APIRouter(prefix="/admin", tags=["admin"])


def _raise_operation_failed(exc: Exception, message: str = "操作失败") -> None:
    """打印完整异常并按正确 HTTP 状态返回，避免 200 包装数据库失败。"""
    if isinstance(exc, HTTPException):
        raise exc
    traceback.print_exc()
    raise HTTPException(status_code=500, detail={"message": message, "detail": str(exc)}) from exc


@router.get("/grades", response_model=AdminGradeListResponse, summary="获取年级列表")
def admin_grades_endpoint(
    # Depends(get_current_admin) 会先解析 JWT，并确认当前用户角色是 admin。
    current_admin: TokenPayload = Depends(get_current_admin),
    # Depends(get_db) 为当前请求创建数据库 Session，用完后自动关闭。
    db: Session = Depends(get_db),
) -> AdminGradeListResponse:
    try:
        # 路由层不直接写数据库查询，交给 service 层处理业务逻辑。
        items = list_grade_summaries(db=db, current_admin=current_admin)
        return AdminGradeListResponse(success=True, data=items, items=items)
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "年级列表获取失败")


@router.get(
    "/grades/{grade}/students",
    response_model=AdminStudentListResponse,
    summary="获取某年级学生列表",
)
def admin_grade_students_endpoint(
    grade: str = Path(..., min_length=1, description="年级，例如：初一"),
    keyword: str | None = Query(default=None, description="按姓名、手机号或学号模糊搜索"),
    class_type: str | None = Query(default=None, alias="classType", description="班型：VIP / 小班 / 小班+一对一 / 一对二 / all"),
    class_type_snake: str | None = Query(default=None, alias="class_type", description="兼容 snake_case 班型参数"),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminStudentListResponse:
    # 前端有时传 classType，后端/脚本可能传 class_type，这里做兼容。
    selected_class_type = class_type or class_type_snake
    try:
        items = list_students_by_grade(
            db=db,
            current_admin=current_admin,
            grade=grade,
            keyword=keyword,
            class_type=selected_class_type,
        )
        return AdminStudentListResponse(items=items, total=len(items))
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学生列表获取失败")


@router.get("/students", response_model=AdminStudentListResponse, summary="获取学生列表")
def admin_students_endpoint(
    keyword: str | None = Query(default=None, description="按姓名、手机号或学号模糊搜索"),
    class_type: str | None = Query(default=None, alias="classType", description="班型：VIP / 小班 / 小班+一对一 / 一对二 / all"),
    class_type_snake: str | None = Query(default=None, alias="class_type", description="兼容 snake_case 班型参数"),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminStudentListResponse:
    selected_class_type = class_type or class_type_snake
    try:
        print("[admin students] keyword=", keyword, "classType=", selected_class_type)
        items = list_students(
            db=db,
            current_admin=current_admin,
            keyword=keyword,
            class_type=selected_class_type,
        )
        print("[admin students] count=", len(items))
        return AdminStudentListResponse(items=items, total=len(items))
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学生列表获取失败")


@router.post("/students", response_model=AdminCreateStudentResponse, summary="管理员新增学生")
def admin_create_student_endpoint(
    # payload 会先按 AdminCreateStudentRequest 做字段校验，例如姓名不能为空、课时不能为负。
    payload: AdminCreateStudentRequest,
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminCreateStudentResponse:
    try:
        # 新增学生会同时创建学生、默认科目、缴费记录、初始课时流水。
        return create_student(db=db, current_admin=current_admin, payload=payload)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"success": False, "message": str(exc.detail)}
        if "success" not in detail:
            detail["success"] = False
        if "message" not in detail:
            detail["message"] = "学生添加失败"
        return JSONResponse(status_code=exc.status_code, content=detail)
    except (SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学生添加失败")


@router.get(
    "/students/{student_id}",
    response_model=StudentProfileResponse,
    summary="获取学生详情",
)
def admin_student_detail_endpoint(
    student_id: int = Path(..., ge=1),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    try:
        # 管理员查看学生详情，返回结构复用学生资料 schema。
        return get_student_detail(db=db, current_admin=current_admin, student_id=student_id)
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学生详情获取失败")


@router.patch(
    "/students/{student_id}/grade",
    response_model=AdminUpgradeStudentGradeResponse,
    summary="管理员升级学员年级",
)
def admin_upgrade_student_grade_endpoint(
    payload: AdminUpgradeStudentGradeRequest,
    student_id: int = Path(..., ge=1),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminUpgradeStudentGradeResponse:
    try:
        # 年级升级只允许改到更高年级，具体限制在 service 层。
        return upgrade_student_grade(
            db=db,
            current_admin=current_admin,
            student_id=student_id,
            payload=payload,
        )
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学员年级升级失败")


@router.delete(
    "/students/{student_id}",
    response_model=AdminDeleteStudentResponse,
    summary="管理员删除学生",
)
def admin_delete_student_endpoint(
    student_id: int = Path(..., ge=1),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminDeleteStudentResponse:
    try:
        # 删除学生采用软删除：列表不再展示，但历史数据不会直接丢失。
        return delete_student(db=db, current_admin=current_admin, student_id=student_id)
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "学生删除失败")


@router.get(
    "/students/{student_id}/records",
    response_model=AdminLessonRecordsResponse,
    summary="获取某个学生全部课时记录",
)
def admin_student_records_endpoint(
    student_id: int = Path(..., ge=1),
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminLessonRecordsResponse:
    try:
        print("[records api] student_id =", student_id)
        records = list_student_records_by_admin(
            db=db,
            current_admin=current_admin,
            student_id=student_id,
        )
        print("[records api] count =", len(records))
        return AdminLessonRecordsResponse(success=True, data=records)
    except (HTTPException, SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "课时记录获取失败")


@router.post("/lesson/change", response_model=LessonChangeResponse, summary="管理员修改课时")
def admin_lesson_change_endpoint(
    # LessonChangeRequest 会校验 changeType、hours、amount、recordDate 等字段。
    payload: LessonChangeRequest,
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> LessonChangeResponse:
    try:
        # 课时调整是核心写操作：会改科目余额并新增课时流水，必要时还新增缴费记录。
        return change_lesson_hours(db=db, current_admin=current_admin, payload=payload)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        if detail.get("code") == INSUFFICIENT_HOURS_CODE:
            # 课时不足是业务错误，前端需要识别 code 并弹出专门提示，所以这里保留业务 code。
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "code": detail.get("code"),
                    "message": detail.get("message"),
                },
            )
        _raise_operation_failed(exc, "课时调整失败")
    except (SQLAlchemyError, Exception) as exc:
        _raise_operation_failed(exc, "课时调整失败")
