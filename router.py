"""
Authentication API routes for PetroNexa.
Enforces server-controlled role initialization, email normalization, and secure session management.
"""

from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database import get_db, UserModel
from auth import UserCreate, UserResponse, Token
from security import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

logger = logging.getLogger("petronexa.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Default role enforced by server to prevent privilege escalation
DEFAULT_USER_ROLE = "drilling_engineer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Registers a new user account with normalized credentials and default authorization."""
    normalized_email = user_data.email.strip().lower()

    # Check for existing email registration
    result = await db.execute(select(UserModel).where(UserModel.email == normalized_email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # Derive or check unique username
    raw_username = user_data.username or normalized_email.split("@")[0]
    username = raw_username.strip()
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered."
        )

    # Force server-controlled role assignment to block admin role spoofing
    new_user = UserModel(
        email=normalized_email,
        username=username,
        hashed_password=get_password_hash(user_data.password),
        role=DEFAULT_USER_ROLE,
        company_name=user_data.company_name.strip() if user_data.company_name else None,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except SQLAlchemyError as err:
        await db.rollback()
        logger.error(f"Database error during user registration: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to a database error."
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """Authenticates user credentials and returns a Bearer JWT access token."""
    normalized_login_id = form_data.username.strip().lower()

    # Query user by normalized email
    result = await db.execute(select(UserModel).where(UserModel.email == normalized_login_id))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=token_expires
    )

    return {"access_token": token, "token_type": "bearer"}
