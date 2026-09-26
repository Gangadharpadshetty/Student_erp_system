from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import academic_controller
from ..utils.security import decode_access_token
import datetime

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/dashboard", response_class=HTMLResponse)
async def student_dash(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    payload = decode_access_token(token)
    if not payload or payload["role"] != "STUDENT":
        return RedirectResponse(url="/auth/login-page", status_code=303)

    # Fetch Student Profile
    from ..api.controllers.auth_controller import get_user_profile
    user = get_user_profile(db, payload["sub"], "STUDENT")
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    # Fetch the latest report
    reports = academic_controller.get_student_report(db, user["student_id"])
    report = max(reports, key=lambda item: item.report_id) if reports else None

    return templates.TemplateResponse(request, "student_report.html", {
        "user": user,
        "report": report,
        "current_date": datetime.date.today().strftime("%B %d, %Y")
    })

@router.post("/raise-ticket")
async def raise_ticket(
    request: Request,
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    payload = decode_access_token(token)

    ticket = academic_controller.create_ticket(db, payload["id"], description)
    return {"message": "Ticket raised successfully", "ticket_id": ticket.ticket_id}
