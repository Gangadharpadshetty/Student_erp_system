from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from .database import get_db
from .models import Class, Student, Teacher, SystemLog
from .api.controllers import auth_controller
from .utils.security import decode_access_token
from .routers import auth_routes, admin_routes, academic_routes, student_routes, teacher_routes

app = FastAPI(title="Student ERP System")

DASHBOARD_URLS = {
    "ADMIN": "/admin/dashboard",
    "TEACHER": "/teacher/dashboard",
    "STUDENT": "/student/dashboard",
}

# Setup Templates and Static Files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routes
app.include_router(auth_routes.router)
app.include_router(auth_routes.admin_registration_router)
app.include_router(admin_routes.router)
app.include_router(academic_routes.router)
app.include_router(student_routes.router)
app.include_router(teacher_routes.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db=Depends(get_db)):
    user = None
    dashboard_url = "/auth/login-page"
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload:
            role = payload.get("role")
            user = auth_controller.get_user_profile(db, payload.get("sub"), role)
            dashboard_url = DASHBOARD_URLS.get(role, "/auth/login-page")

    return templates.TemplateResponse(request, "home.html", {
        "user": user,
        "dashboard_url": dashboard_url,
    })

@app.get("/auth/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {
        "error": request.query_params.get("error"),
        "registered": request.query_params.get("registered"),
    })

# Temporary placeholder routes for dashboards
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dash(request: Request, db=Depends(get_db)):
    user = _get_session_user(request, db, "ADMIN")
    if not user:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    stats = {
        "total_students": db.query(Student).count(),
        "total_teachers": db.query(Teacher).count(),
        "avg_pass_rate": 0,
        "open_tickets": 0,
        "fees_collected": 0,
        "pass_rate": 0,
    }
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(10).all()
    return templates.TemplateResponse(request, "admin_dashboard.html", {
        "user": user,
        "stats": stats,
        "logs": logs,
        "classes": db.query(Class).order_by(Class.class_number).all(),
        "teachers": db.query(Teacher).order_by(Teacher.name).all(),
        "assignment_notice": "Class teacher assigned successfully." if request.query_params.get("assignment") == "success" else None,
    })

def _get_session_user(request: Request, db, expected_role: str):
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or payload.get("role") != expected_role:
        return None
    return auth_controller.get_user_profile(db, payload["sub"], expected_role)
