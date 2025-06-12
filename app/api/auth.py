from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.security import create_access_token, get_password_hash
from ..config import settings
from ..db.database import get_db
from ..db.models import User
from ..schemas.user import User as UserSchema, UserCreate, Token
from .deps import authenticate_user
from ..core.email import send_activation_email, send_password_reset_email
from ..core.token import create_verification_token, verify_token

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrecte email of wachtwoord")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactieve gebruiker")
    elif not user.is_verified:
        raise HTTPException(status_code=400, detail="E-mailadres is nog niet geverifieerd")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserSchema)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Registreer een nieuwe gebruiker en stuur een activatie-email
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Een gebruiker met dit e-mailadres bestaat al.",
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_superuser=False,
        is_active=True,  # Actief, maar nog niet geverifieerd
        is_verified=False,  # E-mail nog niet geverifieerd
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Maak een activatietoken aan en stuur een e-mail
    token = create_verification_token(db, user.id, "activation")
    send_activation_email(user.email, token)
    
    return user


@router.get("/activate")
def activate_user(token: str, db: Session = Depends(get_db)) -> Any:
    """
    Activeer een gebruikersaccount met een token
    """
    user = verify_token(db, token, "activation")
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Ongeldige of verlopen activatielink.",
        )
    
    # Markeer de gebruiker als geverifieerd
    user.is_verified = True
    db.add(user)
    db.commit()
    
    return {"msg": "Account succesvol geactiveerd!"}


@router.post("/password-recovery/{email}")
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    """
    Password recovery
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="De gebruiker met dit e-mailadres bestaat niet in het systeem.",
        )
    
    # Genereer een wachtwoordreset token en stuur een e-mail
    token = create_verification_token(db, user.id, "password_reset", timedelta(hours=1))
    send_password_reset_email(user.email, token)
    
    return {"msg": "Wachtwoord herstel e-mail is verzonden"}

@router.post("/reset-password")
def reset_password(
    token: str, new_password: str, db: Session = Depends(get_db)
) -> Any:
    """
    Reset het wachtwoord met een token
    """
    user = verify_token(db, token, "password_reset")
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Ongeldige of verlopen reset link.",
        )
    
    # Update het wachtwoord
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    
    return {"msg": "Wachtwoord succesvol bijgewerkt"}