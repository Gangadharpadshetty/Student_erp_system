import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models import Academics, Student, Teacher, Class, Report, SystemLog, Ticket
from app.utils.security import create_access_token

# Setup Test Database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    client.cookies.set(
        "access_token",
        create_access_token({"sub": "admin@erp.com", "role": "ADMIN", "id": 1})
    )
    try:
        yield session
    finally:
        app.dependency_overrides.clear()
        client.cookies.delete("access_token")
        session.close()

def test_login_redirects_to_home(db_session):
    client.cookies.delete("access_token")
    response = client.post(
        "/auth/login",
        data={"email": "admin@erp.com", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies


def test_home_stays_visible_when_logged_in(db_session):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert "Go to your workspace" in response.text
    assert "Log out" in response.text

def test_role_dashboards_render_with_role_profiles(db_session):
    school_class = Class(class_id=1, class_number=1)
    student = Student(
        name="Dashboard Student",
        email="dashboard@student.com",
        password="hashed",
        roll_no=3,
        year="2026-2027",
        class_id=1,
    )
    teacher = Teacher(
        name="Dashboard Teacher",
        email="dashboard@teacher.com",
        password="hashed",
        phone_no="555-0101",
        years_of_experience=4,
        subject_specialization="Math",
    )
    db_session.add_all([school_class, student, teacher])
    db_session.commit()

    client.cookies.set("access_token", create_access_token({
        "sub": student.email, "role": "STUDENT", "id": student.student_id,
    }))
    student_response = client.get("/student/dashboard", follow_redirects=False)
    assert student_response.status_code == 200
    assert "Dashboard Student" in student_response.text
    assert "Your report is not ready yet" in student_response.text

    client.cookies.set("access_token", create_access_token({
        "sub": teacher.email, "role": "TEACHER", "id": teacher.teacher_id,
    }))
    teacher_response = client.get("/teacher/dashboard", follow_redirects=False)
    assert teacher_response.status_code == 200
    assert "Dashboard Teacher" in teacher_response.text
    assert "Mark attendance" in teacher_response.text

    client.cookies.set("access_token", create_access_token({
        "sub": "admin@erp.com", "role": "ADMIN", "id": 1,
    }))
    admin_response = client.get("/admin/dashboard", follow_redirects=False)
    assert admin_response.status_code == 200
    assert "Administrator" in admin_response.text
    assert "System Administration" in admin_response.text

def test_student_dashboard_redirects_for_invalid_role(db_session):
    client.cookies.set("access_token", create_access_token({
        "sub": "admin@erp.com", "role": "ADMIN", "id": 1,
    }))
    response = client.get("/student/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login-page"


# --- Test Cases ---

def test_admin_create_student(db_session):
    """Test if Admin can successfully create a student"""
    # Create a class first
    school_class = Class(class_id=1, class_number=10)
    db_session.add(school_class)
    db_session.commit()

    # Simulate Admin request
    response = client.post(
        "/admin/create-student",
        data={
            "name": "Test Student",
            "email": "test@student.com",
            "password": "password123",
            "roll": 1,
            "year": "2024",
            "class_id": 1
        }
    )

    assert response.status_code == 200
    assert response.history == []
    assert "created successfully" in response.json()["message"]

    # Verify in DB
    student = db_session.query(Student).filter(Student.email == "test@student.com").first()
    assert student is not None
    assert student.name == "Test Student"

@pytest.mark.parametrize("class_id", [0, 11])
def test_create_student_rejects_class_outside_range(db_session, class_id):
    response = client.post(
        "/admin/create-student",
        data={
            "name": "Out of Range",
            "email": f"range{class_id}@student.com",
            "password": "password123",
            "roll": 1,
            "year": "2024",
            "class_id": class_id
        }
    )

    assert response.status_code == 422
    assert response.history == []

def test_pass_fail_logic(db_session):
    """Test the grading logic (Pass if >= 35%)"""
    from app.api.controllers import academic_controller

    # Setup a student
    student = Student(student_id=2, name="Grade Test", email="grade@test.com", roll_no=2, year="2024", class_id=1)
    db_session.add(student)
    db_session.commit()

    # Scenario 1: Failing marks
    fail_marks = {"eng": 10, "kannada": 10, "hindi": 10, "math": 10, "science": 10, "social": 10}
    report_fail = academic_controller.update_student_marks(db_session, 2, "2024", 1, fail_marks)
    assert report_fail.result_status == "FAIL"

    # Scenario 2: Passing marks
    pass_marks = {"eng": 50, "kannada": 50, "hindi": 50, "math": 50, "science": 50, "social": 50}
    report_pass = academic_controller.update_student_marks(db_session, 2, "2024", 1, pass_marks)
    assert report_pass.result_status == "PASS"

def test_unauthorized_access():
    """Test that unauthorized users cannot access admin routes"""
    # No cookie set, should return 401 or redirect
    response = client.get("/admin/students")
    # Since our current routes aren't yet wrapped in a role-dependency,
    # this is a reminder to implement the Role Dependency in the final push.
    assert response.status_code in [401, 303, 403]

def test_system_logging(db_session):
    """Test if admin actions are logged in SystemLog table"""
    from app.api.controllers import admin_controller

    # Setup Class
    school_class = Class(class_id=1, class_number=10)
    db_session.add(school_class)
    db_session.commit()

    # Action: Create Teacher
    admin_controller.create_teacher(
        db_session, "Mr. Smith", "smith@school.com", "pass123", "12345", 5, "Math"
    )

    # Verify log exists
    log = db_session.query(SystemLog).filter(SystemLog.action == "CREATE_TEACHER").first()
    assert log is not None
    assert "Created teacher Mr. Smith" in log.details

def test_admin_academic_and_ticket_pages_render(db_session):
    response = client.get("/admin/academics")
    assert response.status_code == 200
    assert "Student marks and report" in response.text
    assert "Academic summary records" in response.text

    response = client.get("/admin/tickets")
    assert response.status_code == 200
    assert "Create a support ticket" in response.text

def test_admin_manage_users_shows_available_profiles_without_passwords(db_session):
    db_session.add(Class(class_id=1, class_number=1))
    student = Student(
        name="Profile Student",
        email="profile@student.com",
        password="student-secret-hash",
        roll_no=7,
        year="2026-2027",
        class_id=1,
    )
    teacher = Teacher(
        name="Profile Teacher",
        email="profile@teacher.com",
        password="teacher-secret-hash",
        phone_no="555-0100",
        years_of_experience=6,
        subject_specialization="Science",
    )
    db_session.add_all([student, teacher])
    db_session.commit()

    response = client.get("/admin/users")
    assert response.status_code == 200
    assert "Profile Student" in response.text
    assert "profile@student.com" in response.text
    assert "Roll number" in response.text
    assert "Profile Teacher" in response.text
    assert "profile@teacher.com" in response.text
    assert "Science" in response.text
    assert "student-secret-hash" not in response.text
    assert "teacher-secret-hash" not in response.text

def test_admin_can_save_student_report_and_academic_summary(db_session):
    school_class = Class(class_id=1, class_number=1)
    student = Student(
        name="Academic Test Student",
        email="academic@student.com",
        password="hashed",
        roll_no=1,
        year="2026-2027",
        class_id=1,
    )
    db_session.add_all([school_class, student])
    db_session.commit()

    report_response = client.post("/admin/academic-reports", data={
        "student_id": student.student_id,
        "year": "2026-2027",
        "eng": 80,
        "kannada": 80,
        "hindi": 80,
        "math": 80,
        "science": 80,
        "social": 80,
    })
    assert report_response.status_code == 200
    assert report_response.json()["result"] == "PASS"
    assert db_session.query(Report).filter_by(student_id=student.student_id).count() == 1

    academic_response = client.post("/admin/academic-records", data={
        "year": "2026-2027",
        "class_id": 1,
        "total_students": 1,
        "fees_collected": 2500,
        "teacher_salaries": 1000,
        "students_passed": 1,
        "distinctions": 1,
    })
    assert academic_response.status_code == 200
    assert db_session.query(Academics).filter_by(class_id=1, year="2026-2027").count() == 1

def test_admin_can_create_and_resolve_ticket(db_session):
    db_session.add(Class(class_id=1, class_number=1))
    student = Student(
        name="Ticket Test Student",
        email="ticket@student.com",
        password="hashed",
        roll_no=1,
        year="2026-2027",
        class_id=1,
    )
    db_session.add(student)
    db_session.commit()

    create_response = client.post("/admin/tickets/create", data={
        "student_id": student.student_id,
        "description": "Needs help with enrollment",
    })
    assert create_response.status_code == 200
    ticket_id = create_response.json()["ticket_id"]
    assert db_session.query(Ticket).filter_by(ticket_id=ticket_id).one().status == "Open"

    resolve_response = client.post(f"/admin/tickets/{ticket_id}/resolve")
    assert resolve_response.status_code == 200
    assert db_session.query(Ticket).filter_by(ticket_id=ticket_id).one().status == "Resolved"
