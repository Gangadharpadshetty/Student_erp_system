import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..api.controllers import academic_controller
from ..database import get_db
from ..models import Attendance, Report, Student, Teacher
from ..utils.security import decode_access_token

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/teacher", tags=["Teacher"])


def _get_teacher(request: Request, db: Session):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("role") != "TEACHER":
        return None
    return db.query(Teacher).filter(Teacher.email == payload.get("sub")).first()


@router.get("/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    teacher = _get_teacher(request, db)
    if not teacher:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    classroom = teacher.class_managed
    students = []
    reports = []
    attendance_records = []
    if classroom:
        students = db.query(Student).filter(
            Student.class_id == classroom.class_id
        ).order_by(Student.roll_no, Student.name).all()
        reports = db.query(Report).join(Student).filter(
            Student.class_id == classroom.class_id
        ).order_by(Report.year.desc(), Student.roll_no).all()
        attendance_records = db.query(Attendance).filter(
            Attendance.class_id == classroom.class_id,
            Attendance.date == datetime.date.today(),
        ).all()

    attendance_by_student = {record.student_id: record for record in attendance_records}
    return templates.TemplateResponse(request, "teacher.html", {
        "user": {
            "name": teacher.name,
            "email": teacher.email,
            "role": "TEACHER",
        },
        "teacher": teacher,
        "classroom": classroom,
        "students": students,
        "reports": reports,
        "attendance_by_student": attendance_by_student,
        "current_date": datetime.date.today().strftime("%B %d, %Y"),
    })


@router.post("/attendance")
def save_attendance(
    request: Request,
    student_id: int = Form(..., gt=0),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    teacher = _get_teacher(request, db)
    if not teacher:
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    classroom = teacher.class_managed
    if not classroom:
        raise HTTPException(status_code=403, detail="You are not assigned to a class")
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.class_id == classroom.class_id,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your class")

    academic_controller.mark_attendance(
        db,
        student.student_id,
        classroom.class_id,
        student.year or str(datetime.date.today().year),
        teacher.teacher_id,
        status,
    )
    return JSONResponse({"message": f"Attendance saved for {student.name}", "status": status})


@router.post("/marks")
def save_marks(
    request: Request,
    student_id: int = Form(..., gt=0),
    year: str = Form(..., min_length=4, max_length=20),
    eng: int = Form(..., ge=0, le=100),
    kannada: int = Form(..., ge=0, le=100),
    hindi: int = Form(..., ge=0, le=100),
    math: int = Form(..., ge=0, le=100),
    science: int = Form(..., ge=0, le=100),
    social: int = Form(..., ge=0, le=100),
    db: Session = Depends(get_db),
):
    teacher = _get_teacher(request, db)
    if not teacher:
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    classroom = teacher.class_managed
    if not classroom:
        raise HTTPException(status_code=403, detail="You are not assigned to a class")

    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.class_id == classroom.class_id,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your class")

    report = academic_controller.update_student_marks(
        db,
        student.student_id,
        year,
        classroom.class_id,
        {
            "eng": eng,
            "kannada": kannada,
            "hindi": hindi,
            "math": math,
            "science": science,
            "social": social,
        },
        teacher_id=teacher.teacher_id,
    )
    return JSONResponse({
        "message": f"Report saved for {student.name}",
        "percentage": report.overall_percentage,
        "result": report.result_status,
    })
