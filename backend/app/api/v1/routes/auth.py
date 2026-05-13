from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.limiter import limiter
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse, WsTokenResponse
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter()


@router.post("/signup", response_model=UserOut)
@limiter.limit("5/minute")
def signup_route(request: Request, data: SignupRequest, db: Session = Depends(get_db)):
    user = auth_service.signup(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login_route(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    access, refresh = auth_service.login(db, data)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh_route(data: RefreshRequest, db: Session = Depends(get_db)):
    access, refresh = auth_service.refresh_tokens(db, data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.get("/ws-token", response_model=WsTokenResponse)
def ws_token(user: CurrentUser):
    from app.core.config import settings

    token = create_access_token(str(user.id), {"email": user.email})
    return WsTokenResponse(token=token, expires_in=settings.access_token_expire_minutes * 60)
