from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.exceptions import bad_request
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.patch("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == str(data.email)).first():
            raise bad_request("Email already in use")
        user.email = str(data.email)
    if data.name is not None:
        user.name = data.name
    db.commit()
    db.refresh(user)
    return user
