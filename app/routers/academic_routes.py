from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import academic_controller

router = APIRouter(prefix="/academic", tags=["Academics"])

@router.post("/mark-attendance")
def mark_attendance(
    student_id: int = Form(...),
    class_id: int = Form(...),
    year: str = Form(...),
    teacher_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    academic_controller.mark_attendance(db, student_id, class_id, year, teacher_id, status)
    return RedirectResponse(url="/teacher/dashboard", status_code=303)

@router.post("/update-marks")
def update_marks(
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
    academic_controller.update_student_marks(db, student_id, year, class_id, {
        "eng": eng, "kannada": kannada, "hindi": hindi,
        "math": math, "science": science, "social": social
    })
    return RedirectResponse(url="/teacher/dashboard", status_code=303)

@router.post("/create-ticket")
def raise_ticket(
    student_id: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    academic_controller.create_ticket(db, student_id, description)
    return RedirectResponse(url="/student/dashboard", status_code=303)
