"""Disposable test data; the application's normal database is never used."""
import os

# Set every connection and credential setting before importing the application.
# dotenv uses override=False, so an existing backend/.env cannot replace these.
os.environ.update({
    "APP_ENV": "test", "DEBUG": "false", "DATABASE_ECHO": "false",
    "MYSQL_HOST": "127.0.0.1", "MYSQL_PORT": "1",
    "MYSQL_USER": "unused_test_user", "MYSQL_PASSWORD": "unused_test_password",
    "MYSQL_DB": "unused_test_database", "MYSQL_CHARSET": "utf8mb4",
    "JWT_SECRET_KEY": "isolated-test-signing-key-not-for-deployment",
    "JWT_ALGORITHM": "HS256", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "DEEPSEEK_API_KEY": "", "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
    "DEEPSEEK_MODEL": "deepseek-chat",
})

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.security import get_password_hash
from app.main import app
from app.models.admin import Admin
from app.models.student import Student
from app.models.student_subject import StudentSubject
from app.utils.deps import get_db


@pytest.fixture(scope="session")
def mysql_engine():
    value = os.getenv("JINBI_TEST_DATABASE_URL", "")
    if not value:
        yield None
        return
    url = make_url(value)
    if (url.drivername != "mysql+pymysql" or url.database != "lesson_test"
            or url.host not in {"127.0.0.1", "localhost"}):
        raise pytest.UsageError("Tests only accept local mysql+pymysql / lesson_test")
    engine = create_engine(url, pool_pre_ping=True)
    if "alembic_version" not in inspect(engine).get_table_names():
        raise pytest.UsageError("Run alembic upgrade head on the isolated test database first")
    yield engine
    engine.dispose()


@pytest.fixture
def db(mysql_engine):
    if mysql_engine is not None:
        # Service commits release savepoints; the outer transaction is rolled back.
        with mysql_engine.connect() as connection:
            outer = connection.begin()
            with Session(connection, join_transaction_mode="create_savepoint",
                         expire_on_commit=False) as session:
                yield session
            outer.rollback()
    else:
        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(engine)
        with Session(engine, expire_on_commit=False) as session:
            yield session
        engine.dispose()


@pytest.fixture
def client(db):
    def isolated_db():
        yield db
    app.dependency_overrides[get_db] = isolated_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def admin_password_hash():
    return get_password_hash("test-only-password")


@pytest.fixture
def accounts(db, admin_password_hash):
    admin = Admin(username="test_admin", password_hash=admin_password_hash, role="admin")
    student = Student(name="演示学员甲", phone="13900009991", student_no="TEST-001",
                      grade="初一", class_type="VIP", status="normal", avatar="")
    other = Student(name="演示学员乙", phone="13900009992", student_no="TEST-002",
                    grade="初二", class_type="小班", status="normal", avatar="")
    student.subjects = [StudentSubject(subject_name="数学", total_hours=10,
                                      remaining_hours=10, deducted_hours=0)]
    other.subjects = [StudentSubject(subject_name="数学", total_hours=20,
                                    remaining_hours=20, deducted_hours=0)]
    db.add_all([admin, student, other])
    db.commit()
    return admin, student, other


@pytest.fixture
def admin_headers(client, accounts):
    response = client.post("/auth/admin-login", json={
        "username": "test_admin", "password": "test-only-password"})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["token"]}


@pytest.fixture
def student_headers(client, accounts):
    response = client.post("/auth/student-login", json={"phone": accounts[1].phone})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["token"]}
