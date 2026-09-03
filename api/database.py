from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.config import config

engine = create_engine(config.get_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
