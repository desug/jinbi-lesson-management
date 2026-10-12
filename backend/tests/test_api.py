from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import create_access_token
from app.models.lesson_record import LessonRecord
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_subject import StudentSubject


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def lesson_payload(student, **values):
    return {"studentId": student.id, "subjectName": "数学",
            "changeType": "add", "hours": 2, "amount": 100, **values}


def test_health_and_openapi(client):
    assert client.get("/health").json()["ok"] is True
    schema = client.get("/openapi.json").json()
    assert "/admin/lesson/change" in schema["paths"]
    assert "/student/payments" not in schema["paths"]


@pytest.mark.parametrize("path", ["/admin/students", "/student/profile"])
def test_missing_auth_is_401(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.json()["success"] is False
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("expired", [False, True])
def test_invalid_or_expired_token_is_rejected(client, expired):
    token = create_access_token("1", "student", timedelta(seconds=-1)) if expired else "invalid.jwt"
    assert client.get("/student/profile", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_wrong_admin_password(client, accounts):
    assert client.post("/auth/admin-login", json={"username": "test_admin", "password": "wrong"}).status_code == 401


def test_student_cannot_access_admin(client, student_headers):
    assert client.get("/admin/students", headers=student_headers).status_code == 403


def test_admin_cannot_use_student_endpoint(client, admin_headers):
    assert client.get("/student/profile", headers=admin_headers).status_code == 403


def test_student_profile_is_scoped_to_token(client, accounts, student_headers):
    profile = client.get("/student/profile", headers=student_headers).json()
    assert profile["id"] == accounts[1].id
    assert profile["phone"] != accounts[2].phone
    assert Decimal(str(profile["totalRemainingHours"])) == 10


def test_student_records_do_not_leak_other_students(client, db, accounts, admin_headers, student_headers):
    for student in accounts[1:]:
        assert client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(student)).status_code == 200
    records = client.get("/student/records", headers=student_headers).json()
    assert len(records) == 1
    assert {item["studentId"] for item in records} == {accounts[1].id}


def test_create_student_writes_four_related_entities(client, db, admin_headers):
    response = client.post("/admin/students", headers=admin_headers, json={
        "name": "新演示学员", "phone": "13900009993", "grade": "初一", "classType": "VIP",
        "totalHours": 8, "totalPrice": 800})
    assert response.status_code == 200
    student_id = response.json()["data"]["id"]
    assert db.get(Student, student_id).name == "新演示学员"
    for model in (StudentSubject, LessonRecord, Payment):
        assert db.scalar(select(func.count()).select_from(model).where(model.student_id == student_id)) == 1


def test_duplicate_phone_does_not_write_data(client, db, accounts, admin_headers):
    before = [count(db, model) for model in (Student, StudentSubject, Payment, LessonRecord)]
    response = client.post("/admin/students", headers=admin_headers, json={
        "name": "重复学员", "phone": accounts[1].phone, "grade": "初一", "classType": "VIP",
        "totalHours": 8, "totalPrice": 800})
    assert response.status_code == 400
    assert [count(db, model) for model in (Student, StudentSubject, Payment, LessonRecord)] == before


def test_add_and_deduct_preserve_balance_and_ledger(client, db, accounts, admin_headers):
    student = accounts[1]
    response = client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(student, hours="2.25"))
    assert response.status_code == 200
    assert count(db, Payment) == 1
    response = client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(student, changeType="deduct", hours="1.5", amount=0))
    assert response.status_code == 200
    subject = db.scalar(select(StudentSubject).where(StudentSubject.student_id == student.id))
    assert subject.total_hours == Decimal("12.25")
    assert subject.deducted_hours == Decimal("1.50")
    assert subject.remaining_hours == Decimal("10.75")
    assert subject.total_hours == subject.deducted_hours + subject.remaining_hours
    assert count(db, LessonRecord) == 2
    assert count(db, Payment) == 1
    assert Decimal(str(response.json()["record"]["remainingHours"])) == subject.remaining_hours


def test_insufficient_hours_roll_back_without_ledger(client, db, accounts, admin_headers):
    response = client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(accounts[1], changeType="deduct", hours=11, amount=0))
    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_HOURS"
    assert count(db, LessonRecord) == 0
    assert accounts[1].subjects[0].remaining_hours == 10


@pytest.mark.parametrize("hours", [0, -1])
def test_non_positive_hours_are_422(client, db, accounts, admin_headers, hours):
    response = client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(accounts[1], hours=hours))
    assert response.status_code == 422
    assert count(db, LessonRecord) == 0


def test_commit_failure_rolls_back_balance_payment_and_record(client, db, accounts, admin_headers, monkeypatch):
    student_id = accounts[1].id
    def fail_commit():
        raise SQLAlchemyError("injected test failure")
    monkeypatch.setattr(db, "commit", fail_commit)
    response = client.post("/admin/lesson/change", headers=admin_headers,
                           json=lesson_payload(accounts[1]))
    assert response.status_code == 500
    assert count(db, LessonRecord) == 0
    assert count(db, Payment) == 0
    subject = db.scalar(select(StudentSubject).where(StudentSubject.student_id == student_id))
    assert subject.remaining_hours == 10


def test_grade_can_only_move_forward(client, accounts, admin_headers):
    path = f"/admin/students/{accounts[1].id}/grade"
    assert client.patch(path, headers=admin_headers, json={"targetGrade": "初二"}).status_code == 200
    assert client.patch(path, headers=admin_headers, json={"targetGrade": "初一"}).status_code == 400


def test_soft_delete_hides_login_but_preserves_ledger(client, db, accounts, admin_headers):
    student = accounts[1]
    client.post("/admin/lesson/change", headers=admin_headers, json=lesson_payload(student))
    assert client.delete(f"/admin/students/{student.id}", headers=admin_headers).status_code == 200
    assert db.get(Student, student.id).is_deleted is True
    assert count(db, LessonRecord) == 1
    assert client.post("/auth/student-login", json={"phone": student.phone}).status_code == 404
    items = client.get("/admin/students", headers=admin_headers).json()["items"]
    assert student.id not in {item["id"] for item in items}


def test_rule_based_ai_is_read_only(client, db, accounts, admin_headers):
    before = count(db, LessonRecord)
    response = client.post("/admin/ai-query", headers=admin_headers,
                           json={"query": "演示学员甲数学还剩多少课时"})
    assert response.status_code == 200
    assert response.json()["intent"] == "subject_hours"
    assert "10" in response.json()["answer"]
    assert count(db, LessonRecord) == before
    assert accounts[1].subjects[0].remaining_hours == 10
