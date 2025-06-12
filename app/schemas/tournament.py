from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime
from ..db.models import UserRole

class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(TournamentBase):
    pass

class TournamentInDBBase(TournamentBase):
    id: int
    created_at: datetime
    creator_id: int
    
    class Config:
        from_attributes = True

class Tournament(TournamentInDBBase):
    pass

class TournamentWithUsers(Tournament):
    users: List[Dict] = []  # Lijst van gebruikers met hun rollen

class TournamentUserUpdate(BaseModel):
    user_id: int
    role: UserRole