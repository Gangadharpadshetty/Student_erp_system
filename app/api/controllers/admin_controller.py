from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ...models import Student, Teacher, Class, SystemLog
from ...utils.security import hash_password
import datetime

def create_teacher(db: Session, name: str, email: str, password: str, phone: str, exp: int, subject: str):
    # Check if teacher already exists
    existing = db.query(Teacher).filter(Teacher.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Teacher with this email already exists")

    new_teacher = Teacher(
        name=name,
        email=email,
        password=hash_password(password),
        phone_no=phone,
        years_of_experience=exp,
        subject_specialization=subject
    )
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    # Log the action
    log_action(db, 1, "CREATE_TEACHER", f"Created teacher {name} with email {email}")

    return new_teacher

def create_student(db: Session, name: str, email: str, password: str, roll: int, year: str, class_id: int):
    if not 1 <= class_id <= 10:
        raise HTTPException(status_code=400, detail="Class ID must be between 1 and 10")

    # Check if student already exists
    existing = db.query(Student).filter(Student.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this email already exists")

    # Verify class exists
    classroom = db.query(Class).filter(Class.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class ID not found")

    new_student = Student(
        name=name,
        email=email,
        password=hash_password(password),
        roll_no=roll,
        year=year,
        class_id=class_id
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    log_action(db, 1, "CREATE_STUDENT", f"Created student {name} in class {class_id}")

    return new_student

def assign_class_teacher(db: Session, class_id: int, teacher_id: int):
    classroom = db.query(Class).filter(Class.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")

    classroom.class_teacher_id = teacher_id
    db.commit()

    log_action(db, 1, "ASSIGN_TEACHER", f"Assigned teacher {teacher_id} to class {class_id}")
    return classroom

def get_all_students(db: Session):
    return db.query(Student).all()

def get_all_teachers(db: Session):
    return db.query(Teacher).all()

def log_action(db: Session, user_id: int, action: str, details: str):
    log = SystemLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()
