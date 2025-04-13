from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.user import get_user_by_id, update_user
from app.dependencies import get_current_active_user, get_db
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
def read_users_me(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
) -> Any:
    """
    Get current user information.
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    user_in: UserUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Update current user information.
    """
    user = update_user(db, db_user=current_user, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Get a specific user by id.
    """
    user = get_user_by_id(db, user_id=user_id)
    if user == current_user:
        return user
    if not current_user.is_admin:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user