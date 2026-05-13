from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import unauthorized
from app.core.security import safe_decode
from app.models.user import User
from app.schemas.common import PaginationParams

security_scheme = HTTPBearer(auto_error=False)


def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
) -> User:
    if creds is None or not creds.credentials:
        raise unauthorized()
    payload = safe_decode(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise unauthorized("Invalid or expired token")
    sub = payload.get("sub")
    if not sub:
        raise unauthorized()
    user = db.get(User, int(sub))
    if not user:
        raise unauthorized("User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
