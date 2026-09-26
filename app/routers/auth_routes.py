from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..api.controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
