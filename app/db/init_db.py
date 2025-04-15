from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine


async def init_db() -> None:
    # Create tables if they don't exist
    # Create tables from the models
    Base.metadata.create_all(bind=engine)