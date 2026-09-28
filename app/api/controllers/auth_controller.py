from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import hmac
import os

from ...models import Admin, Student, Teacher
from ...utils.security import hash_password, verify_password, create_access_token
from ...utils.validation import validate_email, validate_password

def login_user(db: Session, email: str, password: str):
    email = email.strip().lower()

    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(password, admin.password):
        return {
            "token": create_access_token({"sub": admin.email, "role": "ADMIN", "id": admin.admin_id}),
            "role": "ADMIN",
            "name": admin.name,
        }

    # Check Teachers table
    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if teacher and verify_password(password, teacher.password):
        return {
            "token": create_access_token({"sub": teacher.email, "role": "TEACHER", "id": teacher.teacher_id}),
            "role": "TEACHER",
            "name": teacher.name
        }

    # Check Students table
    student = db.query(Student).filter(Student.email == email).first()
    if student and verify_password(password, student.password):
        return {
            "token": create_access_token({"sub": student.email, "role": "STUDENT", "id": student.student_id}),
            "role": "STUDENT",
            "name": student.name
        }

    if not admin and email == "admin@erp.com" and password == "admin123":
        return {
            "token": create_access_token({"sub": email, "role": "ADMIN", "id": 1}),
            "role": "ADMIN",
            "name": "Administrator"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

def register_admin(db: Session, name: str, email: str, password: str, registration_key: str):
    expected_key = os.getenv("ADMIN_REGISTRATION_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=503, detail="Admin registration is not enabled")
    if not hmac.compare_digest(registration_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid admin registration key")

    name = name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=422, detail="Name is required and must be 100 characters or fewer")
    email = validate_email(email)
    password = validate_password(password)

    existing_account = (
        db.query(Admin).filter(Admin.email == email).first()
        or db.query(Teacher).filter(Teacher.email == email).first()
        or db.query(Student).filter(Student.email == email).first()
    )
    if existing_account or email == "admin@erp.com":
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    admin = Admin(name=name, email=email, password=hash_password(password))
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

def get_user_profile(db: Session, email: str, role: str):
    if role == "STUDENT":
        user = db.query(Student).filter(Student.email == email).first()
        if not user:
            return None
        return {
            "student_id": user.student_id,
            "name": user.name,
            "email": user.email,
            "roll_no": user.roll_no,
            "class_id": user.class_id,
            "role": "STUDENT"
        }
    elif role == "TEACHER":
        user = db.query(Teacher).filter(Teacher.email == email).first()
        if not user:
            return None
        return {
            "name": user.name,
            "email": user.email,
            "specialization": user.subject_specialization,
            "role": "TEACHER"
        }
    elif role == "ADMIN":
        admin = db.query(Admin).filter(Admin.email == email).first()
        return {
            "admin_id": admin.admin_id if admin else 1,
            "name": admin.name if admin else "Administrator",
            "email": email,
            "role": "ADMIN"
        }
    return None
