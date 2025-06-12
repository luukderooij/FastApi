from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db.database import get_db
from ..db.models import Tournament, User, tournament_users, UserRole
from ..schemas.tournament import (
    Tournament as TournamentSchema,
    TournamentCreate,
    TournamentUpdate,
    TournamentWithUsers,
    TournamentUserUpdate
)
from .deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[TournamentSchema])
def read_tournaments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve tournaments
    """
    # Haal alle toernooien op waar de huidige gebruiker toegang toe heeft
    tournaments = db.query(Tournament).join(
        tournament_users, Tournament.id == tournament_users.c.tournament_id
    ).filter(
        tournament_users.c.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return tournaments

@router.post("/", response_model=TournamentSchema)
def create_tournament(
    *,
    db: Session = Depends(get_db),
    tournament_in: TournamentCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new tournament
    """
    tournament = Tournament(
        name=tournament_in.name,
        description=tournament_in.description,
        creator_id=current_user.id,
    )
    db.add(tournament)
    db.commit()
    
    # Voeg de maker toe als admin
    statement = tournament_users.insert().values(
        user_id=current_user.id,
        tournament_id=tournament.id,
        role=UserRole.ADMIN
    )
    db.execute(statement)
    db.commit()
    
    db.refresh(tournament)
    return tournament

@router.get("/{tournament_id}", response_model=TournamentWithUsers)
def read_tournament(
    *,
    db: Session = Depends(get_db),
    tournament_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get specific tournament by ID
    """
    # Controleer of het toernooi bestaat en of de gebruiker toegang heeft
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Toernooi niet gevonden")
    
    # Controleer of de gebruiker toegang heeft tot dit toernooi
    user_role = db.query(tournament_users).filter(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == current_user.id
        )
    ).first()
    
    if not user_role:
        raise HTTPException(status_code=403, detail="Geen toegang tot dit toernooi")
    
    # Haal alle gebruikers op met hun rollen voor dit toernooi
    tournament_data = TournamentWithUsers.model_validate(tournament)
    users_with_roles = db.query(
        User.id, User.email, tournament_users.c.role
    ).join(
        tournament_users, User.id == tournament_users.c.user_id
    ).filter(
        tournament_users.c.tournament_id == tournament_id
    ).all()
    
    tournament_data.users = [
        {"id": user.id, "email": user.email, "role": user.role}
        for user in users_with_roles
    ]
    
    return tournament_data

@router.put("/{tournament_id}", response_model=TournamentSchema)
def update_tournament(
    *,
    db: Session = Depends(get_db),
    tournament_id: int,
    tournament_in: TournamentUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a tournament
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Toernooi niet gevonden")
    
    # Controleer of de gebruiker admin of creator is
    user_role = db.query(tournament_users.c.role).filter(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == current_user.id
        )
    ).scalar()
    
    if user_role not in [UserRole.ADMIN, UserRole.MODERATOR] and tournament.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om dit toernooi te bewerken")
    
    # Update toernooi gegevens
    if tournament_in.name is not None:
        tournament.name = tournament_in.name
    if tournament_in.description is not None:
        tournament.description = tournament_in.description
    
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament

@router.post("/{tournament_id}/users", response_model=TournamentWithUsers)
def add_user_to_tournament(
    *,
    db: Session = Depends(get_db),
    tournament_id: int,
    user_update: TournamentUserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Add a user to a tournament with a specific role
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Toernooi niet gevonden")
    
    # Controleer of de huidige gebruiker admin of creator is
    user_role = db.query(tournament_users.c.role).filter(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == current_user.id
        )
    ).scalar()
    
    if user_role != UserRole.ADMIN and tournament.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om gebruikers toe te voegen")
    
    # Controleer of de toe te voegen gebruiker bestaat
    user_to_add = db.query(User).filter(User.id == user_update.user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    # Controleer of de gebruiker al toegevoegd is
    existing_role = db.query(tournament_users).filter(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == user_update.user_id
        )
    ).first()
    
    if existing_role:
        # Update de bestaande rol
        statement = tournament_users.update().where(
            and_(
                tournament_users.c.tournament_id == tournament_id,
                tournament_users.c.user_id == user_update.user_id
            )
        ).values(role=user_update.role)
        db.execute(statement)
    else:
        # Voeg de gebruiker toe met de opgegeven rol
        statement = tournament_users.insert().values(
            user_id=user_update.user_id,
            tournament_id=tournament_id,
            role=user_update.role
        )
        db.execute(statement)
    
    db.commit()
    
    # Geef het bijgewerkte toernooi terug met gebruikersinformatie
    return read_tournament(db=db, tournament_id=tournament_id, current_user=current_user)

@router.delete("/{tournament_id}/users/{user_id}")
def remove_user_from_tournament(
    *,
    db: Session = Depends(get_db),
    tournament_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove a user from a tournament
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Toernooi niet gevonden")
    
    # Controleer of de huidige gebruiker admin of creator is
    user_role = db.query(tournament_users.c.role).filter(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == current_user.id
        )
    ).scalar()
    
    if user_role != UserRole.ADMIN and tournament.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Onvoldoende rechten om gebruikers te verwijderen")
    
    # Verwijder de gebruiker van het toernooi
    statement = tournament_users.delete().where(
        and_(
            tournament_users.c.tournament_id == tournament_id,
            tournament_users.c.user_id == user_id
        )
    )
    db.execute(statement)
    db.commit()
    
    return {"msg": "Gebruiker is verwijderd uit het toernooi"}