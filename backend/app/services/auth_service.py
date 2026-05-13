from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import bad_request, unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    new_jti,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest


def signup(db: Session, data: SignupRequest) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise bad_request("Email already registered")
    user = User(
        name=data.name,
        email=str(data.email),
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, data: LoginRequest) -> tuple[str, str]:
    user = db.query(User).filter(User.email == str(data.email)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise unauthorized("Invalid email or password")
    access = create_access_token(str(user.id), {"email": user.email})
    jti = new_jti()
    refresh = create_refresh_token(str(user.id), jti)
    exp = datetime.now(timezone.utc)
    exp_refresh = exp + timedelta(days=settings.refresh_token_expire_days)
    row = RefreshToken(user_id=user.id, jti=jti, expires_at=exp_refresh, revoked=False)
    db.add(row)
    db.commit()
    return access, refresh


def refresh_tokens(db: Session, refresh_token: str) -> tuple[str, str]:
    from app.core.security import safe_decode

    payload = safe_decode(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise unauthorized("Invalid refresh token")
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise unauthorized()
    row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not row or row.revoked or row.expires_at < datetime.now(timezone.utc):
        raise unauthorized("Refresh token expired or revoked")
    user = db.get(User, int(sub))
    if not user:
        raise unauthorized()
    access = create_access_token(str(user.id), {"email": user.email})
    new_jti_val = new_jti()
    new_refresh = create_refresh_token(str(user.id), new_jti_val)
    row.revoked = True
    exp_refresh = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(user_id=user.id, jti=new_jti_val, expires_at=exp_refresh, revoked=False)
    )
    db.commit()
    return access, new_refresh
