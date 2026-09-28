import os

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["Authentication"])
admin_registration_router = APIRouter(prefix="/admin", tags=["Administration"])
templates = Jinja2Templates(directory="app/templates")


@admin_registration_router.get("/register", response_class=HTMLResponse)
def admin_registration_page(request: Request):
    return templates.TemplateResponse(request, "admin_register.html", {
        "error": request.query_params.get("error"),
        "registration_enabled": bool(os.getenv("ADMIN_REGISTRATION_KEY")),
    })


@admin_registration_router.post("/register", response_class=HTMLResponse)
def register_admin(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    registration_key: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        auth_controller.register_admin(db, name, email, password, registration_key)
    except HTTPException as exc:
        return templates.TemplateResponse(request, "admin_register.html", {
            "error": exc.detail,
            "registration_enabled": bool(os.getenv("ADMIN_REGISTRATION_KEY")),
        }, status_code=exc.status_code)
    return RedirectResponse(url="/auth/login-page?registered=1", status_code=303)

@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        result = auth_controller.login_user(db, email, password)
    except HTTPException:
        return RedirectResponse(url="/auth/login-page?error=Invalid+email+or+password", status_code=303)

    redirect_response = RedirectResponse(url="/", status_code=303)
    redirect_response.set_cookie(
        key="access_token",
        value=result["token"],
        httponly=True,
        samesite="lax",
        path="/",
    )
    return redirect_response

@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from ..utils.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    profile = auth_controller.get_user_profile(db, payload["sub"], payload["role"])
    return profile

@router.api_route("/logout", methods=["GET", "POST"])
def logout():
    redirect_response = RedirectResponse(url="/", status_code=303)
    redirect_response.delete_cookie("access_token", path="/")
    return redirect_response
