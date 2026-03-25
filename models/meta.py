from database.db import DatabaseConfig
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import  relationship

db_config = DatabaseConfig()
Base = db_config.base

class MetaTokenUpdate(BaseModel):
    long_lived_token: str
    conta_instagram_id: str

class MetaTokenUpdateSchema(BaseModel):
    ig_account_id: str
    long_lived_token: str

class ContaMetaEntity(Base):
    __tablename__ = "contas_meta"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # O ID gerado pelo Keycloak
    ig_account_id = Column(String, unique=True, index=True) # ID do Instagram do cliente
    long_lived_token = Column(String) # O Token para o bot usar

    # Relacionamento: Uma conta pode ter várias automações
    automacoes = relationship("AutomacaoEntity", back_populates="conta")