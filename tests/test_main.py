import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models import Admin, Academics, Attendance, Student, Teacher, Class, Report, SystemLog, Ticket
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

def test_admin_registration_is_available_at_admin_endpoint(db_session):
    response = client.get("/admin/register")
    assert response.status_code == 200
    assert "Register an admin" in response.text
    assert 'action="/admin/register"' in response.text

def test_admin_registration_requires_server_key(db_session, monkeypatch):
    monkeypatch.delenv("ADMIN_REGISTRATION_KEY", raising=False)
    response = client.post("/admin/register", data={
        "name": "New Admin",
        "email": "new-admin@example.com",
        "password": "securepass123",
        "registration_key": "anything",
    })
    assert response.status_code == 503
    assert "Admin registration is not enabled" in response.text
    assert db_session.query(Admin).count() == 0

def test_admin_registration_creates_login_account(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_REGISTRATION_KEY", "one-time-registration-secret")
    response = client.post("/admin/register", data={
        "name": "New Admin",
        "email": "NEW-ADMIN@example.com",
        "password": "securepass123",
        "registration_key": "one-time-registration-secret",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login-page?registered=1"
    admin = db_session.query(Admin).filter_by(email="new-admin@example.com").one()
    assert admin.name == "New Admin"
    assert admin.password != "securepass123"

    login_response = client.post("/auth/login", data={
        "email": admin.email,
        "password": "securepass123",
    }, follow_redirects=False)
    assert login_response.status_code == 303
    assert "access_token" in login_response.cookies


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

def test_assigned_teacher_can_record_attendance_and_marks(db_session):
    teacher = Teacher(
        name="Class Teacher",
        email="class-teacher@example.com",
        password="hashed",
        phone_no="5551234567",
        subject_specialization="Math",
    )
    db_session.add(teacher)
    db_session.flush()
    classroom = Class(class_id=1, class_number=1, class_teacher_id=teacher.teacher_id)
    student = Student(
        name="Roster Student",
        email="roster@student.com",
        password="hashed",
        roll_no=1,
        year="2026-2027",
        class_id=1,
    )
    db_session.add_all([classroom, student])
    db_session.commit()
    client.cookies.set("access_token", create_access_token({
        "sub": teacher.email, "role": "TEACHER", "id": teacher.teacher_id,
    }))

    dashboard_response = client.get("/teacher/dashboard")
    assert dashboard_response.status_code == 200
    assert "Roster Student" in dashboard_response.text
    assert 'action="/teacher/attendance"' in dashboard_response.text
    assert 'action="/teacher/marks"' in dashboard_response.text

    attendance_response = client.post("/teacher/attendance", data={
        "student_id": student.student_id,
        "status": "Present",
    })
    assert attendance_response.status_code == 200
    attendance = db_session.query(Attendance).filter_by(student_id=student.student_id).one()
    assert attendance.status == "Present"
    assert attendance.teacher_id == teacher.teacher_id
    assert attendance.class_id == classroom.class_id

    marks_response = client.post("/teacher/marks", data={
        "student_id": student.student_id,
        "year": "2026-2027",
        "eng": 80,
        "kannada": 80,
        "hindi": 80,
        "math": 80,
        "science": 80,
        "social": 80,
    })
    assert marks_response.status_code == 200
    assert marks_response.json()["result"] == "PASS"
    assert db_session.query(Report).filter_by(student_id=student.student_id).count() == 1

def test_teacher_cannot_write_for_unassigned_class(db_session):
    teacher = Teacher(
        name="Unassigned Teacher",
        email="unassigned@example.com",
        password="hashed",
    )
    db_session.add(teacher)
    db_session.flush()
    db_session.add(Class(class_id=1, class_number=1))
    student = Student(
        name="Other Class Student",
        email="other-class@student.com",
        password="hashed",
        roll_no=1,
        year="2026-2027",
        class_id=1,
    )
    db_session.add(student)
    db_session.commit()
    client.cookies.set("access_token", create_access_token({
        "sub": teacher.email, "role": "TEACHER", "id": teacher.teacher_id,
    }))

    response = client.post("/teacher/attendance", data={
        "student_id": student.student_id,
        "status": "Present",
    })
    assert response.status_code == 403
    assert db_session.query(Attendance).count() == 0

def test_student_report_and_attendance_pages_render_own_records(db_session):
    db_session.add(Class(class_id=1, class_number=1))
    student = Student(
        name="Student Records",
        email="records@student.com",
        password="hashed",
        roll_no=4,
        year="2026-2027",
        class_id=1,
    )
    db_session.add(student)
    db_session.commit()
    db_session.add(Report(
        year="2026-2027",
        student_id=student.student_id,
        class_id=1,
        eng_marks=85,
        kannada_marks=80,
        hindi_marks=75,
        math_marks=90,
        science_marks=88,
        social_science_marks=82,
        overall_percentage=83.33,
        result_status="PASS",
    ))
    db_session.add(Attendance(
        student_id=student.student_id,
        class_id=1,
        year="2026-2027",
        teacher_id=1,
        status="Present",
    ))
    db_session.commit()
    client.cookies.set("access_token", create_access_token({
        "sub": student.email, "role": "STUDENT", "id": student.student_id,
    }))

    report_response = client.get("/student/report", follow_redirects=False)
    assert report_response.status_code == 200
    assert "Official Marksheet - 2026-2027" in report_response.text
    assert "83.33%" in report_response.text

    attendance_response = client.get("/student/attendance", follow_redirects=False)
    assert attendance_response.status_code == 200
    assert "My Attendance" in attendance_response.text
    assert "Present" in attendance_response.text
    assert "2026-2027" in attendance_response.text

def test_student_attendance_requires_student_login(db_session):
    client.cookies.set("access_token", create_access_token({
        "sub": "admin@erp.com", "role": "ADMIN", "id": 1,
    }))
    response = client.get("/student/attendance", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login-page"

def test_student_can_raise_ticket_and_view_confirmation(db_session):
    db_session.add(Class(class_id=1, class_number=1))
    student = Student(
        name="Ticket Owner",
        email="ticket-owner@student.com",
        password="hashed",
        roll_no=8,
        year="2026-2027",
        class_id=1,
    )
    db_session.add(student)
    db_session.commit()
    client.cookies.set("access_token", create_access_token({
        "sub": student.email, "role": "STUDENT", "id": student.student_id,
    }))

    response = client.post("/student/raise-ticket", data={
        "description": "Please review my attendance",
        "return_to": "/student/report",
        "student_id": 9999,
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/student/report?notice=ticket-created"

    ticket = db_session.query(Ticket).one()
    assert ticket.student_id == student.student_id
    assert ticket.issue_description == "Please review my attendance"

    report_response = client.get(response.headers["location"])
    assert report_response.status_code == 200
    assert "Your support ticket was submitted successfully." in report_response.text

    tickets_response = client.get("/student/tickets")
    assert tickets_response.status_code == 200
    assert "Please review my attendance" in tickets_response.text
    assert "My tickets" in tickets_response.text

def test_student_raise_ticket_requires_student_login(db_session):
    client.cookies.set("access_token", create_access_token({
        "sub": "admin@erp.com", "role": "ADMIN", "id": 1,
    }))
    response = client.post("/student/raise-ticket", data={
        "description": "This should not be accepted",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login-page"
    assert db_session.query(Ticket).count() == 0


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

@pytest.mark.parametrize(("email", "password"), [
    ("not-an-email", "securepass123"),
    ("valid@student.com", "short"),
])
def test_student_registration_rejects_invalid_email_or_password(db_session, email, password):
    db_session.add(Class(class_id=1, class_number=1))
    db_session.commit()
    response = client.post("/admin/create-student", data={
        "name": "Invalid Account",
        "email": email,
        "password": password,
        "roll": 2,
        "year": "2026-2027",
        "class_id": 1,
    })
    assert response.status_code == 422

def test_teacher_registration_rejects_invalid_phone(db_session):
    response = client.post("/admin/create-teacher", data={
        "name": "Invalid Phone",
        "email": "teacher@example.com",
        "password": "securepass123",
        "phone": "call-me",
        "exp": 2,
        "subject": "Science",
    })
    assert response.status_code == 422

def test_admin_can_assign_teacher_to_class(db_session):
    classroom = Class(class_id=1, class_number=1)
    teacher = Teacher(
        name="Assigned Teacher",
        email="assigned@example.com",
        password="hashed",
        phone_no="5551234567",
        subject_specialization="Math",
    )
    db_session.add_all([classroom, teacher])
    db_session.commit()

    response = client.post("/admin/assign-teacher", data={
        "class_id": 1,
        "teacher_id": teacher.teacher_id,
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard?assignment=success"
    assert db_session.query(Class).filter_by(class_id=1).one().class_teacher_id == teacher.teacher_id

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
        db_session, "Mr. Smith", "smith@school.com", "pass12345", "1234567", 5, "Math"
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
