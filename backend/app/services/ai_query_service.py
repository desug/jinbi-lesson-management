from __future__ import annotations

import json
import re
import traceback
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.lesson_record import LessonRecord
from app.models.student import Student
from app.models.student_subject import StudentSubject
from app.schemas.ai import AiQueryResponse, ParsedAiQuery
from app.schemas.auth import TokenPayload
from app.services.class_types import (
    CLASS_TYPES,
    class_type_db_values,
    class_type_label,
    detect_class_type_in_text,
    normalize_class_type,
)
from app.services.common import parse_token_subject_id


MODEL_INTENTS = {
    "subject_hours",
    "all_subjects_summary",
    "class_type",
    "lesson_records",
    "list_by_class_type",
    "low_remaining_hours",
    "total_hours",
    "deducted_hours",
    "unknown",
}

AI_QUERY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {
            "type": "string",
            "enum": sorted(MODEL_INTENTS),
        },
        "student_name": {"type": "string"},
        "phone": {"type": "string"},
        "grade": {"type": "string"},
        "subject_name": {"type": "string"},
        "class_type": {"type": "string"},
        "threshold": {
            "anyOf": [
                {"type": "number"},
                {"type": "null"},
            ]
        },
    },
    "required": [
        "intent",
        "student_name",
        "phone",
        "grade",
        "subject_name",
        "class_type",
        "threshold",
    ],
}

SYSTEM_PROMPT = """
你是补课机构课时管理系统的管理员查询意图解析器。
只把用户问题解析成 JSON，不回答业务结果，不生成 SQL，不修改任何数据。
只能选择以下 intent：
subject_hours, all_subjects_summary, class_type, lesson_records,
list_by_class_type, low_remaining_hours, total_hours, deducted_hours, unknown。
字段含义：
- student_name：学生姓名；没有则为空字符串
- phone：手机号；没有则为空字符串
- grade：年级，例如 初一、初二、初三、高一、高二、高三；没有则为空字符串
- subject_name：科目名，例如 数学、英语；没有则为空字符串
- class_type：班型，只能归一为 VIP、小班、小班+一对一、一对二；用户说“一对一”时归一为 VIP；没有则为空字符串
- threshold：低课时阈值；没有则为 null
请只返回 JSON 对象，不要输出 Markdown、解释或多余文本。
""".strip()

PUNCTUATION_RE = re.compile(r"[\s，。！？、；：,.!?;:“”\"'‘’（）()\[\]【】]+")
PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
COMMON_SUBJECT_NAMES = ["数学", "英语", "语文", "物理", "化学", "生物", "历史", "地理", "政治"]
GRADE_NAMES = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级", "初一", "初二", "初三", "高一", "高二", "高三", "未分配"]


def _active_student_filter():
    return or_(Student.is_deleted.is_(False), Student.is_deleted.is_(None))


def answer_ai_query(
    db: Session,
    current_admin: TokenPayload,
    query: str,
) -> AiQueryResponse:
    parse_token_subject_id(current_admin)

    query_text = (query or "").strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请输入要查询的问题",
        )

    try:
        local_parsed = _parse_query_with_rules(db, query_text)
        llm_parsed = None
        if local_parsed.intent == "unknown":
            llm_parsed = _parse_query_with_deepseek(query_text)
        parsed = _merge_parsed_query(llm_parsed, local_parsed)
        print("[ai query] query=", query_text)
        print("[ai query] parsed=", parsed.model_dump())
        response = _execute_parsed_query(
            db=db,
            parsed=parsed,
            ai_configured=bool(settings.deepseek_api_key.strip()),
        )
        print("[ai query] answer=", response.answer)
        return response
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "AI 查询数据库失败，请稍后重试", "detail": str(exc)},
        ) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "AI 查询失败，请稍后重试", "detail": str(exc)},
        ) from exc


def _parse_query_with_deepseek(query_text: str) -> ParsedAiQuery | None:
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=(settings.deepseek_base_url or "https://api.deepseek.com").rstrip("/"),
            timeout=8.0,
            max_retries=0,
        )
        completion = client.chat.completions.create(
            model=settings.deepseek_model or "deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query_text},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content if completion.choices else ""
        return _parsed_query_from_json(content or "")
    except Exception:
        return None


def _parsed_query_from_json(content: str) -> ParsedAiQuery | None:
    content_text = (content or "").strip()
    if content_text.startswith("```"):
        content_text = re.sub(r"^```(?:json)?", "", content_text, flags=re.IGNORECASE).strip()
        content_text = re.sub(r"```$", "", content_text).strip()

    try:
        payload = json.loads(content_text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    payload["threshold"] = _to_decimal_or_none(payload.get("threshold"))
    try:
        return _normalize_parsed_query(ParsedAiQuery.model_validate(payload))
    except ValidationError:
        return None


def _parse_query_with_rules(db: Session, query_text: str) -> ParsedAiQuery:
    normalized_text = _normalize_query_text(query_text)
    phone = _extract_phone(query_text)
    grade = _detect_grade(normalized_text)
    student_name = _match_student_name(db, normalized_text)
    subject_name = _match_subject_name(db, normalized_text)
    class_type = _detect_class_type(query_text)
    if not student_name and not phone and not class_type:
        student_name = _infer_student_name_candidate(normalized_text, subject_name)
    threshold = _detect_threshold(query_text)
    intent = _detect_intent(normalized_text, student_name, phone, subject_name, class_type, grade)

    return ParsedAiQuery(
        intent=intent,
        student_name=student_name,
        phone=phone,
        grade=grade,
        subject_name=subject_name,
        class_type=class_type,
        threshold=threshold,
    )


def _merge_parsed_query(
    llm_parsed: ParsedAiQuery | None,
    local_parsed: ParsedAiQuery,
) -> ParsedAiQuery:
    if llm_parsed is None:
        return local_parsed

    llm_parsed = _normalize_parsed_query(llm_parsed)
    local_parsed = _normalize_parsed_query(local_parsed)

    intent = llm_parsed.intent
    if intent == "unknown":
        intent = local_parsed.intent
    elif local_parsed.intent in {
        "low_remaining_hours",
        "list_by_class_type",
        "total_hours",
        "deducted_hours",
        "lesson_records",
        "all_subjects_summary",
    } and intent in {"unknown", "subject_hours", "class_type"}:
        intent = local_parsed.intent

    return ParsedAiQuery(
        intent=intent,
        student_name=local_parsed.student_name or llm_parsed.student_name,
        phone=local_parsed.phone or llm_parsed.phone,
        grade=local_parsed.grade or llm_parsed.grade,
        subject_name=local_parsed.subject_name or llm_parsed.subject_name,
        class_type=local_parsed.class_type or llm_parsed.class_type,
        threshold=llm_parsed.threshold if llm_parsed.threshold is not None else local_parsed.threshold,
    )


def _normalize_parsed_query(parsed: ParsedAiQuery) -> ParsedAiQuery:
    intent = parsed.intent if parsed.intent in MODEL_INTENTS else "unknown"
    phone_match = _extract_phone(parsed.phone)
    return ParsedAiQuery(
        intent=intent,
        student_name=(parsed.student_name or "").strip(),
        phone=phone_match,
        grade=_normalize_grade(parsed.grade),
        subject_name=(parsed.subject_name or "").strip(),
        class_type=_normalize_class_type(parsed.class_type),
        threshold=_to_decimal_or_none(parsed.threshold),
    )


def _execute_parsed_query(
    db: Session,
    parsed: ParsedAiQuery,
    ai_configured: bool,
) -> AiQueryResponse:
    if parsed.intent == "list_by_class_type" or (
        parsed.intent == "class_type" and parsed.class_type and not (parsed.student_name or parsed.phone)
    ):
        return _handle_list_by_class_type(db, parsed)

    if parsed.intent == "low_remaining_hours":
        return _handle_low_remaining_hours(db, parsed)

    if parsed.intent == "unknown":
        return _unknown_response(ai_configured)

    student = _find_student(db, parsed)
    if student is None:
        return _unknown_student_response(parsed)

    if parsed.intent == "subject_hours":
        if not parsed.subject_name:
            return _handle_all_subjects_summary(student)
        return _handle_subject_hours(student, parsed.subject_name)

    if parsed.intent == "all_subjects_summary":
        return _handle_all_subjects_summary(student)

    if parsed.intent == "class_type":
        return _handle_class_type(student)

    if parsed.intent == "lesson_records":
        return _handle_lesson_records(db, student)

    if parsed.intent == "total_hours":
        return _handle_total_hours(student, parsed.subject_name)

    if parsed.intent == "deducted_hours":
        return _handle_deducted_hours(student, parsed.subject_name)

    return _unknown_response(ai_configured)


def _normalize_query_text(query_text: str) -> str:
    return PUNCTUATION_RE.sub("", query_text or "")


def _extract_phone(text: str) -> str:
    match = PHONE_RE.search(text or "")
    return match.group(1) if match else ""


def _match_student_name(db: Session, normalized_text: str) -> str:
    names = db.scalars(
        select(Student.name).where(_active_student_filter()).order_by(Student.name.desc())
    ).all()
    matched_names = [name for name in names if name and name in normalized_text]
    matched_names.sort(key=len, reverse=True)
    return matched_names[0] if matched_names else ""


def _match_subject_name(db: Session, normalized_text: str) -> str:
    subject_names = db.scalars(
        select(StudentSubject.subject_name)
        .join(Student, Student.id == StudentSubject.student_id)
        .where(_active_student_filter())
        .distinct()
    ).all()
    matched_subjects = [name for name in subject_names if name and name in normalized_text]
    matched_subjects.sort(key=len, reverse=True)
    if matched_subjects:
        return matched_subjects[0]

    common_matches = [name for name in COMMON_SUBJECT_NAMES if name in normalized_text]
    common_matches.sort(key=len, reverse=True)
    return common_matches[0] if common_matches else ""


def _infer_student_name_candidate(normalized_text: str, subject_name: str) -> str:
    candidate = normalized_text or ""
    if not candidate:
        return ""

    if subject_name:
        candidate = candidate.replace(subject_name, "")

    candidate = re.sub(
        r"还剩|剩余|还有多少|剩多少|多少课时|多少学时|课时汇总|各科汇总|"
        r"课时情况|课时概况|课时明细|课时|学时|总学时|总课时|"
        r"是什么班型|什么班型|班型|记录|流水|明细|最近|"
        r"请问|查询|查看|一下|多少|吗|呢|的|他|她",
        "",
        candidate,
    )
    candidate = re.sub(r"\d+(?:\.\d+)?", "", candidate)
    candidate = candidate.strip()

    if re.fullmatch(r"[\u4e00-\u9fa5]{2,6}", candidate):
        return candidate
    return ""


def _detect_class_type(text: str) -> str:
    return detect_class_type_in_text(text)


def _normalize_grade(value: str) -> str:
    text = (value or "").strip()
    return text if text in GRADE_NAMES else ""


def _detect_grade(normalized_text: str) -> str:
    matches = [grade for grade in GRADE_NAMES if grade and grade in (normalized_text or "")]
    matches.sort(key=len, reverse=True)
    return matches[0] if matches else ""


def _detect_threshold(text: str) -> Decimal | None:
    threshold_text = PHONE_RE.sub("", text or "")
    number_match = re.search(r"(?:少于|低于|不足|小于)\s*(\d+(?:\.\d+)?)", threshold_text)
    if not number_match:
        number_match = re.search(r"(\d+(?:\.\d+)?)", threshold_text)
    if number_match:
        return _to_decimal_or_none(number_match.group(1))

    for phrase, value in {
        "二十": Decimal("20"),
        "十五": Decimal("15"),
        "十二": Decimal("12"),
        "十": Decimal("10"),
        "八": Decimal("8"),
        "五": Decimal("5"),
    }.items():
        if phrase in (text or ""):
            return value
    return None


def _detect_intent(
    normalized_text: str,
    student_name: str,
    phone: str,
    subject_name: str,
    class_type: str,
    grade: str,
) -> str:
    has_student = bool(student_name or phone)

    if re.search(r"少于|低于|不足|小于", normalized_text):
        return "low_remaining_hours"

    if class_type and re.search(r"哪些|哪几个|名单|列表|有谁|有哪些|学员|学生", normalized_text) and not has_student:
        return "list_by_class_type"

    if re.search(r"记录|流水|明细|最近", normalized_text):
        return "lesson_records"

    if re.search(r"班型|类型", normalized_text):
        if class_type and not has_student:
            return "list_by_class_type"
        return "class_type"

    if re.search(r"汇总|全部|各科|所有|概况|情况", normalized_text):
        return "all_subjects_summary"

    if re.search(r"总课时|总学时|一共|总共|共有|买了多少|购买", normalized_text):
        return "total_hours"

    if re.search(r"已扣|扣了|扣除|消耗|已经上了|用了多少", normalized_text):
        return "deducted_hours"

    if re.search(r"剩余|还剩|剩多少|还有多少|多少课时|多少学时", normalized_text):
        return "subject_hours" if subject_name else "all_subjects_summary"

    if class_type and grade and not has_student:
        return "list_by_class_type"

    if class_type and not has_student:
        return "list_by_class_type"

    if has_student:
        return "all_subjects_summary"

    return "unknown"


def _normalize_class_type(value: str) -> str:
    return normalize_class_type(value) or detect_class_type_in_text(value)


def _to_decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _find_student(db: Session, parsed: ParsedAiQuery) -> Student | None:
    stmt = select(Student).options(selectinload(Student.subjects)).where(_active_student_filter())

    if parsed.phone:
        student = db.scalar(stmt.where(Student.phone == parsed.phone))
        if student is not None:
            return student

    student_name = (parsed.student_name or "").strip()
    if not student_name:
        return None

    student = db.scalar(stmt.where(Student.name == student_name))
    if student is not None:
        return student

    candidates = db.scalars(stmt.where(Student.name.like(f"%{student_name}%"))).all()
    if candidates:
        return sorted(candidates, key=lambda item: len(item.name))[0]

    return None


def _find_subject(student: Student, subject_name: str) -> StudentSubject | None:
    normalized_subject = (subject_name or "").strip()
    if not normalized_subject:
        return None

    for subject in student.subjects:
        if subject.subject_name == normalized_subject:
            return subject

    for subject in student.subjects:
        if normalized_subject in subject.subject_name or subject.subject_name in normalized_subject:
            return subject

    return None


def _unknown_response(ai_configured: bool) -> AiQueryResponse:
    if ai_configured:
        answer = "暂时无法理解这个问题，请尝试输入学生姓名、手机号、科目或班型，例如“演示学员01数学还剩多少课时”或“初三一对一有哪些学生”。"
    else:
        answer = (
            "AI 服务未配置，当前已使用本地规则解析；暂时无法理解这个问题。"
            "请在后端 .env 中填写 DEEPSEEK_API_KEY，或尝试输入“演示学员01数学还剩多少课时”。"
        )
    return AiQueryResponse(answer=answer, intent="unknown", data={})


def _unknown_student_response(parsed: ParsedAiQuery) -> AiQueryResponse:
    if parsed.phone:
        answer = f"没有找到手机号“{parsed.phone}”对应的学生，请检查姓名或手机号。"
    elif parsed.student_name:
        answer = f"没有找到叫“{parsed.student_name}”的学生，请检查姓名或手机号。"
    else:
        answer = "请提供要查询的学生姓名或手机号。"
    return AiQueryResponse(answer=answer, intent="unknown_student", data={})


def _unknown_subject_response(student: Student, subject_name: str) -> AiQueryResponse:
    if subject_name:
        answer = f"找到了学生{student.name}，但没有找到他的{subject_name}课时记录。"
    else:
        answer = f"找到了学生{student.name}，但未识别到要查询的科目。"
    return AiQueryResponse(answer=answer, intent="unknown_subject", data={})


def _class_type_label(class_type: str) -> str:
    return class_type_label(class_type)


def _format_hours(value: Any) -> str:
    decimal_value = _to_decimal_or_none(value) or Decimal("0")
    if decimal_value == decimal_value.to_integral_value():
        return str(int(decimal_value))
    return format(decimal_value.normalize(), "f")


def _json_number(value: Any) -> int | float:
    decimal_value = _to_decimal_or_none(value) or Decimal("0")
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    return float(decimal_value)


def _student_base_payload(student: Student) -> dict[str, Any]:
    return {
        "studentId": student.id,
        "studentName": student.name,
        "phone": student.phone,
        "studentNo": student.student_no,
        "grade": student.grade,
        "school": student.school,
        "classType": student.class_type,
    }


def _subject_payload(subject: StudentSubject) -> dict[str, Any]:
    return {
        "subjectName": subject.subject_name,
        "totalHours": _json_number(subject.total_hours),
        "remainingHours": _json_number(subject.remaining_hours),
        "deductedHours": _json_number(subject.deducted_hours),
    }


def _student_subject_payload(student: Student, subject: StudentSubject) -> dict[str, Any]:
    payload = _student_base_payload(student)
    payload.update(_subject_payload(subject))
    return payload


def _handle_subject_hours(student: Student, subject_name: str) -> AiQueryResponse:
    subject = _find_subject(student, subject_name)
    if subject is None:
        return _unknown_subject_response(student, subject_name)

    answer = (
        f"{student.name}{subject.subject_name}当前总学时 {_format_hours(subject.total_hours)}，"
        f"已扣除 {_format_hours(subject.deducted_hours)}，"
        f"剩余 {_format_hours(subject.remaining_hours)} 学时。"
    )
    return AiQueryResponse(
        answer=answer,
        intent="subject_hours",
        data=_student_subject_payload(student, subject),
    )


def _handle_all_subjects_summary(student: Student) -> AiQueryResponse:
    subjects = sorted(student.subjects, key=lambda item: item.id)
    if not subjects:
        return AiQueryResponse(
            answer=f"{student.name}暂无课时记录。",
            intent="all_subjects_summary",
            data={**_student_base_payload(student), "subjects": []},
        )

    subject_text = "，".join(
        f"{subject.subject_name}剩余 {_format_hours(subject.remaining_hours)} / 总 {_format_hours(subject.total_hours)}"
        for subject in subjects
    )
    total_hours = sum((subject.total_hours for subject in subjects), Decimal("0"))
    remaining_hours = sum((subject.remaining_hours for subject in subjects), Decimal("0"))
    deducted_hours = sum((subject.deducted_hours for subject in subjects), Decimal("0"))
    data = {
        **_student_base_payload(student),
        "totalHours": _json_number(total_hours),
        "remainingHours": _json_number(remaining_hours),
        "deductedHours": _json_number(deducted_hours),
        "subjects": [_subject_payload(subject) for subject in subjects],
    }
    return AiQueryResponse(
        answer=f"{student.name}当前课时汇总：{subject_text}。",
        intent="all_subjects_summary",
        data=data,
    )


def _handle_class_type(student: Student) -> AiQueryResponse:
    label = _class_type_label(student.class_type)
    return AiQueryResponse(
        answer=f"{student.name}当前班型是 {label}。",
        intent="class_type",
        data=_student_base_payload(student),
    )


def _handle_lesson_records(db: Session, student: Student) -> AiQueryResponse:
    records = db.scalars(
        select(LessonRecord)
        .where(LessonRecord.student_id == student.id)
        .order_by(LessonRecord.record_date.desc(), LessonRecord.id.desc())
        .limit(10)
    ).all()

    if not records:
        return AiQueryResponse(
            answer=f"{student.name}暂无课时记录。",
            intent="lesson_records",
            data={**_student_base_payload(student), "records": []},
        )

    record_payloads = []
    answer_parts = []
    for record in records:
        change_label = "加课" if record.change_type == "add" else "扣课"
        record_datetime = record.record_date or record.created_at
        created_at = record_datetime.strftime("%Y-%m-%d %H:%M:%S") if record_datetime else ""
        answer_parts.append(
            f"{created_at} {record.subject_name}{change_label}{_format_hours(record.hours)}学时"
        )
        record_payloads.append(
            {
                "studentId": student.id,
                "studentName": student.name,
                "subjectName": record.subject_name,
                "changeType": record.change_type,
                "hours": _json_number(record.hours),
                "amount": _json_number(record.amount),
                "remainingHours": _json_number(record.remaining_hours),
                "operatorName": record.operator_name,
                "remark": record.remark or "",
                "createdAt": created_at,
                "recordDate": created_at,
            }
        )

    return AiQueryResponse(
        answer=f"{student.name}最近 {len(records)} 条课时记录：" + "；".join(answer_parts) + "。",
        intent="lesson_records",
        data={**_student_base_payload(student), "records": record_payloads},
    )


def _handle_total_hours(student: Student, subject_name: str) -> AiQueryResponse:
    if subject_name:
        subject = _find_subject(student, subject_name)
        if subject is None:
            return _unknown_subject_response(student, subject_name)
        return AiQueryResponse(
            answer=f"{student.name}{subject.subject_name}当前总学时 {_format_hours(subject.total_hours)}。",
            intent="total_hours",
            data=_student_subject_payload(student, subject),
        )

    subjects = sorted(student.subjects, key=lambda item: item.id)
    total_hours = sum((subject.total_hours for subject in subjects), Decimal("0"))
    return AiQueryResponse(
        answer=f"{student.name}当前全部科目总学时 {_format_hours(total_hours)}。",
        intent="total_hours",
        data={
            **_student_base_payload(student),
            "totalHours": _json_number(total_hours),
            "subjects": [_subject_payload(subject) for subject in subjects],
        },
    )


def _handle_deducted_hours(student: Student, subject_name: str) -> AiQueryResponse:
    if subject_name:
        subject = _find_subject(student, subject_name)
        if subject is None:
            return _unknown_subject_response(student, subject_name)
        return AiQueryResponse(
            answer=f"{student.name}{subject.subject_name}已扣除 {_format_hours(subject.deducted_hours)} 学时。",
            intent="deducted_hours",
            data=_student_subject_payload(student, subject),
        )

    subjects = sorted(student.subjects, key=lambda item: item.id)
    deducted_hours = sum((subject.deducted_hours for subject in subjects), Decimal("0"))
    return AiQueryResponse(
        answer=f"{student.name}当前全部科目已扣除 {_format_hours(deducted_hours)} 学时。",
        intent="deducted_hours",
        data={
            **_student_base_payload(student),
            "deductedHours": _json_number(deducted_hours),
            "subjects": [_subject_payload(subject) for subject in subjects],
        },
    )


def _handle_list_by_class_type(db: Session, parsed: ParsedAiQuery) -> AiQueryResponse:
    class_type = parsed.class_type
    if class_type not in CLASS_TYPES:
        return AiQueryResponse(
            answer="请说明要查询 VIP、小班、小班+一对一，还是一对二学员。",
            intent="unknown",
            data={},
        )

    stmt = select(Student).where(
        Student.class_type.in_(class_type_db_values(class_type)),
        _active_student_filter(),
    )
    if parsed.grade:
        stmt = stmt.where(Student.grade == parsed.grade)

    students = db.scalars(
        stmt.order_by(Student.id.asc())
    ).all()
    label = _class_type_label(class_type)
    scope = f"{parsed.grade} " if parsed.grade else "当前 "
    data = {
        "grade": parsed.grade,
        "classType": class_type,
        "students": [_student_base_payload(student) for student in students],
    }
    if not students:
        return AiQueryResponse(
            answer=f"{scope}没有 {label}。",
            intent="list_by_class_type",
            data=data,
        )

    names = "、".join(student.name for student in students)
    return AiQueryResponse(
        answer=f"{scope}{label}有：{names}。",
        intent="list_by_class_type",
        data=data,
    )


def _handle_low_remaining_hours(db: Session, parsed: ParsedAiQuery) -> AiQueryResponse:
    subject_name = (parsed.subject_name or "").strip()
    if not subject_name:
        return AiQueryResponse(
            answer="请指定要查询的科目，例如“哪些学生数学剩余课时少于 10”。",
            intent="unknown_subject",
            data={},
        )

    threshold = parsed.threshold or Decimal("10")
    subject_exists = db.scalar(
        select(StudentSubject.id)
        .join(Student, Student.id == StudentSubject.student_id)
        .where(StudentSubject.subject_name == subject_name, _active_student_filter())
        .limit(1)
    )
    if subject_exists is None:
        return AiQueryResponse(
            answer=f"没有找到{subject_name}科目的课时记录。",
            intent="unknown_subject",
            data={},
        )

    rows = db.execute(
        select(Student, StudentSubject)
        .join(StudentSubject, StudentSubject.student_id == Student.id)
        .where(
            _active_student_filter(),
            StudentSubject.subject_name == subject_name,
            StudentSubject.remaining_hours < threshold,
        )
        .order_by(StudentSubject.remaining_hours.asc(), Student.id.asc())
    ).all()

    student_items = [
        {
            **_student_base_payload(student),
            **_subject_payload(subject),
        }
        for student, subject in rows
    ]
    data = {
        "subjectName": subject_name,
        "threshold": _json_number(threshold),
        "students": student_items,
    }
    if not rows:
        return AiQueryResponse(
            answer=f"没有找到{subject_name}剩余课时少于 {_format_hours(threshold)} 的学生。",
            intent="low_remaining_hours",
            data=data,
        )

    names = "，".join(
        f"{student.name}剩余 {_format_hours(subject.remaining_hours)} 学时"
        for student, subject in rows
    )
    return AiQueryResponse(
        answer=f"{subject_name}剩余课时少于 {_format_hours(threshold)} 的学生有：{names}。",
        intent="low_remaining_hours",
        data=data,
    )
