from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import admin_controller
from ..api.controllers import academic_controller
from ..models import Academics, Report, Student, Ticket, Class, Teacher
from ..utils.security import decode_access_token

templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("role") != "ADMIN":
        raise HTTPException(status_code=401, detail="Admin authentication required")

router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(require_admin)]
)

@router.post("/create-teacher")
def add_teacher(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    exp: int = Form(...),
    subject: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_controller.create_teacher(db, name, email, password, phone, exp, subject)
    return JSONResponse({"message": "Teacher created successfully"})

@router.post("/create-student")
def add_student(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    roll: int = Form(...),
    year: str = Form(...),
    class_id: int = Form(..., ge=1, le=10),
    db: Session = Depends(get_db)
):
    admin_controller.create_student(db, name, email, password, roll, year, class_id)
    return JSONResponse({"message": "Student created successfully"})

@router.post("/assign-teacher")
def assign_teacher(
    class_id: int = Form(..., ge=1, le=10),
    teacher_id: int = Form(..., gt=0),
    db: Session = Depends(get_db)
):
    admin_controller.assign_class_teacher(db, class_id, teacher_id)
    return RedirectResponse(url="/admin/dashboard?assignment=success", status_code=303)

@router.get("/students")
def list_students(db: Session = Depends(get_db)):
    return admin_controller.get_all_students(db)

@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db)):
    return admin_controller.get_all_teachers(db)

@router.get("/users")
def manage_users(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "admin_users.html", {
        "user": _get_admin_user(request, db),
        "students": db.query(Student).order_by(Student.name).all(),
        "teachers": db.query(Teacher).order_by(Teacher.name).all(),
    })

@router.get("/academics")
def academic_control(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "admin_academics.html", {
        "user": _get_admin_user(request, db),
        "notice": request.query_params.get("notice"),
        "students": db.query(Student).order_by(Student.class_id, Student.roll_no).all(),
        "classes": db.query(Class).order_by(Class.class_id).all(),
        "reports": db.query(Report).order_by(Report.year.desc(), Report.report_id.desc()).all(),
        "academic_records": db.query(Academics).order_by(Academics.year.desc(), Academics.class_id).all(),
    })

@router.post("/academic-reports")
def save_report_marks(
    student_id: int = Form(...),
    year: str = Form(...),
    eng: int = Form(..., ge=0, le=100),
    kannada: int = Form(..., ge=0, le=100),
    hindi: int = Form(..., ge=0, le=100),
    math: int = Form(..., ge=0, le=100),
    science: int = Form(..., ge=0, le=100),
    social: int = Form(..., ge=0, le=100),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    report = academic_controller.update_student_marks(db, student_id, year, student.class_id, {
        "eng": eng,
        "kannada": kannada,
        "hindi": hindi,
        "math": math,
        "science": science,
        "social": social,
    })
    return JSONResponse({
        "message": "Student report saved successfully",
        "report_id": report.report_id,
        "percentage": report.overall_percentage,
        "result": report.result_status,
    })

@router.post("/academic-records")
def save_academic_record(
    year: str = Form(...),
    class_id: int = Form(..., ge=1, le=10),
    total_students: int = Form(..., ge=0),
    fees_collected: float = Form(..., ge=0),
    teacher_salaries: float = Form(..., ge=0),
    students_passed: int = Form(..., ge=0),
    distinctions: int = Form(..., ge=0),
    db: Session = Depends(get_db),
):
    record = academic_controller.save_academic_summary(
        db, year, class_id, total_students, fees_collected, teacher_salaries,
        students_passed, distinctions,
    )
    return JSONResponse({
        "message": "Academic summary saved successfully",
        "academic_id": record.academic_id,
    })

@router.get("/tickets")
def ticket_center(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "admin_tickets.html", {
        "user": _get_admin_user(request, db),
        "notice": request.query_params.get("notice"),
        "students": db.query(Student).order_by(Student.name).all(),
        "tickets": db.query(Ticket).order_by(Ticket.created_at.desc()).all(),
    })

@router.post("/tickets/create")
def add_ticket(
    student_id: int = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    ticket = academic_controller.create_ticket(db, student_id, description)
    return JSONResponse({"message": "Ticket created successfully", "ticket_id": ticket.ticket_id})

@router.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: int, db: Session = Depends(get_db)):
    academic_controller.resolve_ticket(db, ticket_id)
    return JSONResponse({"message": "Ticket marked as resolved"})

def _get_admin_user(request: Request, db: Session):
    payload = decode_access_token(request.cookies.get("access_token"))
    from ..api.controllers.auth_controller import get_user_profile
    return get_user_profile(db, payload["sub"], "ADMIN")
