from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base
from datetime import timedelta, datetime
import secrets

# Rollenmodel als Python Enum
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    EDITOR = "editor"
    VIEWER = "viewer"

# Tussentabel voor de many-to-many relatie tussen gebruikers en toernooien
tournament_users = Table(
    "tournament_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("tournament_id", Integer, ForeignKey("tournaments.id"), primary_key=True),
    Column("role", String, default=UserRole.VIEWER),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    is_verified = Column(Boolean, default=False)  # Nieuwe kolom voor e-mailactivatie
    
    # Bestaande relaties ...
    verification_tokens = relationship("VerificationToken", back_populates="user")
    
    # Relatie met toernooien waar gebruiker deel van uitmaakt
    tournaments = relationship("Tournament", secondary=tournament_users, back_populates="users")
    # Toernooien die door deze gebruiker zijn aangemaakt
    created_tournaments = relationship("Tournament", back_populates="creator")

class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # Relatie met gebruikers die toegang hebben tot dit toernooi
    users = relationship("User", secondary=tournament_users, back_populates="tournaments")
    # Relatie met de gebruiker die dit toernooi heeft aangemaakt
    creator = relationship("User", back_populates="created_tournaments")

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    type = Column(String)  # "activation", "password_reset", etc.
    created_at = Column(DateTime, default=func.now())

    # Relatie met gebruiker
    user = relationship("User", back_populates="verification_tokens")

