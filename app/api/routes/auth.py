from datetime import timedelta
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_email, get_user_by_username
from app.dependencies import get_db
from app.schemas.token import Token
from app.schemas.user import User, UserCreate

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=User)
def register(
    user_in: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new user.
    """
    # Check if username exists
    user = get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email exists
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = create_user(db, user_in=user_in)
    return user


@router.post("/login", response_model=Token)
def login(
    db: Annotated[Session, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Any:
    """
    Get access token for future authenticated requests.
    """
    user = authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }