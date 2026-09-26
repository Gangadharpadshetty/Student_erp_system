from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ...models import Student, Teacher, Report
from ...utils.security import verify_password, create_access_token

def login_user(db: Session, email: str, password: str):
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

    # For simplicity, Admin is handled similarly or via a specific admin check
    # In a real app, we'd have a dedicated Admin table or role in a Users table.
    # We will implement Admin check here based on a specific email for now.
    if email == "admin@erp.com" and password == "admin123": # Temporary hardcoded for first boot
        return {
            "token": create_access_token({"sub": email, "role": "ADMIN", "id": 1}),
            "role": "ADMIN",
            "name": "Administrator"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

def get_user_profile(db: Session, email: str, role: str):
    if role == "STUDENT":
        user = db.query(Student).filter(Student.email == email).first()
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
        return {
            "name": user.name,
            "email": user.email,
            "specialization": user.subject_specialization,
            "role": "TEACHER"
        }
    elif role == "ADMIN":
        return {
            "name": "Administrator",
            "email": email,
            "role": "ADMIN"
        }
    return None
