from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import academic_controller
from ..models import Student, Teacher
from ..utils.security import decode_access_token

router = APIRouter(prefix="/academic", tags=["Academics"])

@router.post("/mark-attendance")
def mark_attendance(
    request: Request,
    student_id: int = Form(...),
    class_id: int = Form(...),
    year: str = Form(...),
    teacher_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    teacher = _get_teacher(request, db)
    classroom = teacher.class_managed
    if not classroom or classroom.class_id != class_id or teacher.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    academic_controller.mark_attendance(db, student_id, class_id, year, teacher.teacher_id, status)
    return RedirectResponse(url="/teacher/dashboard", status_code=303)

@router.post("/update-marks")
def update_marks(
    request: Request,
    student_id: int = Form(...),
    year: str = Form(...),
    class_id: int = Form(...),
    eng: int = Form(0),
    kannada: int = Form(0),
    hindi: int = Form(0),
    math: int = Form(0),
    science: int = Form(0),
    social: int = Form(0),
    db: Session = Depends(get_db)
):
    teacher = _get_teacher(request, db)
    classroom = teacher.class_managed
    if not classroom or classroom.class_id != class_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")
    academic_controller.update_student_marks(db, student_id, year, class_id, {
        "eng": eng, "kannada": kannada, "hindi": hindi,
        "math": math, "science": science, "social": social
    }, teacher_id=teacher.teacher_id)
    return RedirectResponse(url="/teacher/dashboard", status_code=303)

@router.post("/create-ticket")
def raise_ticket(
    student_id: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    academic_controller.create_ticket(db, student_id, description)
    return RedirectResponse(url="/student/dashboard", status_code=303)

def _get_teacher(request: Request, db: Session):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("role") != "TEACHER":
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    teacher = db.query(Teacher).filter(Teacher.email == payload.get("sub")).first()
    if not teacher:
        raise HTTPException(status_code=401, detail="Teacher account not found")
    return teacher
