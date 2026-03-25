from database.db import DatabaseConfig
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.db import Base


class MetaTokenUpdate(BaseModel):
    long_lived_token: str
    conta_instagram_id: str

class MetaTokenUpdateSchema(BaseModel):
    ig_account_id: str
    long_lived_token: str

class ContaMetaEntity(Base):
    __tablename__ = "contas_meta"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) 
    ig_account_id = Column(String, unique=True, index=True) 
    long_lived_token = Column(String) 

    automacoes = relationship("AutomacaoEntity", back_populates="conta")