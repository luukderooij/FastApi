import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..db.models import VerificationToken, User

def create_verification_token(db: Session, user_id: int, token_type: str, expires_in: timedelta = timedelta(hours=24)) -> str:
    """
    Maak een nieuw verificatietoken voor een gebruiker
    """
    # Verwijder eventuele bestaande tokens van hetzelfde type
    db.query(VerificationToken).filter(
        VerificationToken.user_id == user_id, 
        VerificationToken.type == token_type
    ).delete()
    
    # Genereer een nieuw token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + expires_in
    
    # Sla het nieuwe token op
    db_token = VerificationToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
        type=token_type
    )
    
    db.add(db_token)
    db.commit()
    
    return token

def verify_token(db: Session, token: str, token_type: str) -> User:
    """
    Valideer een token en geef de bijbehorende gebruiker terug
    """
    # Zoek het token in de database
    db_token = db.query(VerificationToken).filter(
        VerificationToken.token == token,
        VerificationToken.type == token_type
    ).first()
    
    # Controleer of het token bestaat en niet verlopen is
    if not db_token or db_token.expires_at < datetime.utcnow():
        return None
    
    # Haal de gebruiker op
    user = db.query(User).filter(User.id == db_token.user_id).first()
    
    # Verwijder het token (gebruiken en direct verwijderen)
    db.delete(db_token)
    db.commit()
    
    return user