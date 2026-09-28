from sqlalchemy.orm import Session
from fastapi import HTTPException
from ...models import Academics, Attendance, Class, Report, Teacher, Ticket, Student
import datetime

def mark_attendance(db: Session, student_id: int, class_id: int, year: str, teacher_id: int, status: str):
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    classroom = db.query(Class).filter(
        Class.class_id == class_id,
        Class.class_teacher_id == teacher_id,
    ).first()
    if not classroom:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.class_id == class_id,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your class")
    if status not in {"Present", "Absent"}:
        raise HTTPException(status_code=422, detail="Attendance status must be Present or Absent")

    today = datetime.date.today()
    existing = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.class_id == class_id,
        Attendance.date == today
    ).first()

    if existing:
        existing.status = status
    else:
        attendance = Attendance(
            student_id=student_id,
            class_id=class_id,
            year=year,
            teacher_id=teacher_id,
            date=today,
            status=status
        )
        db.add(attendance)

    db.commit()
    return {"status": "success"}

def update_student_marks(
    db: Session,
    student_id: int,
    year: str,
    class_id: int,
    marks_data: dict,
    teacher_id: int | None = None,
):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.class_id != class_id:
        raise HTTPException(status_code=400, detail="Class does not match the student's class")
    if teacher_id is not None:
        classroom = db.query(Class).filter(
            Class.class_id == class_id,
            Class.class_teacher_id == teacher_id,
        ).first()
        if not classroom:
            raise HTTPException(status_code=403, detail="You are not assigned to this class")
    if any(mark < 0 or mark > 100 for mark in marks_data.values()):
        raise HTTPException(status_code=422, detail="Marks must be between 0 and 100")

    # Calculate total and percentage
    total_marks = sum(marks_data.values())
    percentage = (total_marks / (len(marks_data) * 100)) * 100
    status = "PASS" if percentage >= 35 else "FAIL"

    report = db.query(Report).filter(
        Report.student_id == student_id,
        Report.year == year
    ).first()

    if not report:
        report = Report(student_id=student_id, year=year, class_id=class_id)
        db.add(report)

    report.eng_marks = marks_data.get("eng", 0)
    report.kannada_marks = marks_data.get("kannada", 0)
    report.hindi_marks = marks_data.get("hindi", 0)
    report.math_marks = marks_data.get("math", 0)
    report.science_marks = marks_data.get("science", 0)
    report.social_science_marks = marks_data.get("social", 0)
    report.overall_percentage = percentage
    report.result_status = status

    db.commit()
    return report

def save_academic_summary(
    db: Session,
    year: str,
    class_id: int,
    total_students: int,
    fees_collected: float,
    teacher_salaries: float,
    students_passed: int,
    distinctions: int,
):
    classroom = db.query(Class).filter(Class.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if students_passed > total_students or distinctions > students_passed:
        raise HTTPException(
            status_code=422,
            detail="Passed students cannot exceed enrollment, and distinctions cannot exceed passed students",
        )

    record = db.query(Academics).filter(
        Academics.class_id == class_id,
        Academics.year == year,
    ).first()
    if not record:
        record = Academics(class_id=class_id, year=year)
        db.add(record)

    record.total_students = total_students
    record.fees_collected = fees_collected
    record.teacher_salaries = teacher_salaries
    record.students_passed = students_passed
    record.distinctions = distinctions
    db.commit()
    db.refresh(record)
    return record

def get_student_report(db: Session, student_id: int):
    return db.query(Report).filter(Report.student_id == student_id).all()

def get_student_attendance(db: Session, student_id: int):
    return db.query(Attendance).filter(Attendance.student_id == student_id).all()

def create_ticket(db: Session, student_id: int, description: str):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not description.strip():
        raise HTTPException(status_code=422, detail="Ticket description is required")
    ticket = Ticket(student_id=student_id, issue_description=description)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def resolve_ticket(db: Session, ticket_id: int):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "Resolved"
    db.commit()
    return ticket
