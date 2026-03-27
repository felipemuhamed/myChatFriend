from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database.db import Base
from typing import List, Optional



class MidiaInputSchema(BaseModel):
    media_id: str
    media_type: Optional[str] = None
    caption: Optional[str] = None
    permalink: Optional[str] = None
    thumbnail_url: Optional[str] = None
    media_url: Optional[str] = None


class AutomacaoCreateSchema(BaseModel):
    palavra_chave: str
    mensagem_resposta: str
    ig_account_id: str
    midias: List[MidiaInputSchema]


class AutomacaoEntity(Base):
    __tablename__ = "automacoes"

    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_meta.id", ondelete="CASCADE"), nullable=False)

    palavra_chave = Column(String, index=True, nullable=False)
    mensagem_resposta = Column(String, nullable=False)
    ativa = Column(Boolean, default=True, index=True)

    conta = relationship("ContaMetaEntity", back_populates="automacoes")

    automacao_midias = relationship(
        "AutomacaoMidiaEntity",
        back_populates="automacao",
        cascade="all, delete-orphan"
    )