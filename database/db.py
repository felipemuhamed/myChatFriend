from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


Base = declarative_base()

class DatabaseConfig:
    def __init__(self):
        self.url = os.getenv("DATABASE_URL")
        self.engine = create_engine(self.url)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        self.base = Base

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()