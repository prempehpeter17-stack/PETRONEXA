"""Authentication schemas and JWT dependency helpers for PetroNexa."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal, UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    username: str | None = Field(default=None, max_length=80)
    company_name: str | None = Field(default=None, max_length=150)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    company_name: str | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret,
            algorithms=[settings.jwt_algorithm],
        )
        email = payload.get("sub")
        if not email:
            raise credentials_error
    except (JWTError, ValueError, TypeError):
        raise credentials_error

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserModel).where(UserModel.email == str(email).strip().lower())
        )
        user = result.scalars().first()
        if user is None:
            raise credentials_error
        return user
