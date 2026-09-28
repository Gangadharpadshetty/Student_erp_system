from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import academic_controller
from ..models import Student, Ticket
from ..utils.security import decode_access_token
import datetime

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/report", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def student_dash(request: Request, db: Session = Depends(get_db)):
    user = _get_student_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    # Fetch the latest report
    reports = academic_controller.get_student_report(db, user["student_id"])
    report = max(reports, key=lambda item: item.report_id) if reports else None

    return templates.TemplateResponse(request, "student_report.html", {
        "user": user,
        "report": report,
        "notice": request.query_params.get("notice"),
        "current_date": datetime.date.today().strftime("%B %d, %Y")
    })

@router.get("/attendance", response_class=HTMLResponse)
async def student_attendance(request: Request, db: Session = Depends(get_db)):
    user = _get_student_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    attendance_records = academic_controller.get_student_attendance(db, user["student_id"])
    attendance_records.sort(key=lambda record: record.date or datetime.date.min, reverse=True)
    return templates.TemplateResponse(request, "student_attendance.html", {
        "user": user,
        "attendance_records": attendance_records,
        "current_date": datetime.date.today().strftime("%B %d, %Y"),
    })

@router.get("/tickets", response_class=HTMLResponse)
async def student_tickets(request: Request, db: Session = Depends(get_db)):
    user = _get_student_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    tickets = db.query(Ticket).filter(
        Ticket.student_id == user["student_id"]
    ).order_by(Ticket.created_at.desc()).all()
    return templates.TemplateResponse(request, "student_tickets.html", {
        "user": user,
        "tickets": tickets,
        "notice": request.query_params.get("notice"),
        "current_date": datetime.date.today().strftime("%B %d, %Y"),
    })

@router.post("/raise-ticket")
def raise_ticket(
    request: Request,
    description: str = Form(...),
    return_to: str = Form("/student/tickets"),
    db: Session = Depends(get_db),
):
    user = _get_student_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    academic_controller.create_ticket(db, user["student_id"], description)
    destination = return_to if return_to in {"/student/tickets", "/student/report", "/student/dashboard"} else "/student/tickets"
    return RedirectResponse(url=f"{destination}?notice=ticket-created", status_code=303)

def _get_student_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("role") != "STUDENT":
        return None

    from ..api.controllers.auth_controller import get_user_profile
    student = db.query(Student).filter(Student.email == payload.get("sub")).first()
    if not student:
        return None
    return get_user_profile(db, student.email, "STUDENT")
