from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
