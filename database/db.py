from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "postgresql://saas_user:senha_super_secreta_123@db:5432/saas_automacao"

class DatabaseConfig:
    """Classe responsável por gerenciar a conexão com o PostgreSQL"""
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.base = declarative_base()

    def get_db(self):
        db = self.session_local()
        try:
            yield db
        finally:
            db.close()