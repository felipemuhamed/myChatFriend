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

class ContaMetaCreateRequest(BaseModel):
    user_id: str
    ig_account_id: str
    long_lived_token: str

class ContaMetaEntity(Base):
    __tablename__ = "contas_meta"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    ig_account_id = Column(String, unique=True, index=True, nullable=False)
    long_lived_token = Column(String, nullable=False)

    assinatura = relationship(
        "AssinaturaEntity",
        back_populates="conta_meta",
        uselist=False,
        cascade="all, delete-orphan"
    )

    automacoes = relationship(
        "AutomacaoEntity",
        back_populates="conta",
        cascade="all, delete-orphan"
    )

    midias = relationship(
        "MidiaInstagramEntity",
        back_populates="conta",
        cascade="all, delete-orphan"
    )