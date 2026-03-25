from database.db import DatabaseConfig
from pydantic import BaseModel

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import  relationship

db_config = DatabaseConfig()
Base = db_config.base

class AutomacaoCreate(BaseModel):
    palavra_chave: str
    mensagem_resposta: str
    conta_instagram_id: str


class AutomacaoCreateSchema(BaseModel):
    palavra_chave: str
    mensagem_resposta: str
    ig_account_id: str


class AutomacaoEntity(Base):
    __tablename__ = "automacoes"

    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_meta.id"))
    palavra_chave = Column(String, index=True)
    mensagem_resposta = Column(String)
    
    # NOVA FLAG DE CONTROLE
    ativa = Column(Boolean, default=True, index=True)

    conta = relationship("ContaMetaEntity", back_populates="automacoes")