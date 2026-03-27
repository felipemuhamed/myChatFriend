from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.db import Base

from core.enums import PlanoEnum, AssinaturaStatusEnum


class AssinaturaCreate(BaseModel):
    conta_meta_id: int
    plano: PlanoEnum = PlanoEnum.FREE


class AssinaturaUpdatePlano(BaseModel):
    plano: PlanoEnum


class AssinaturaResponse(BaseModel):
    id: int
    conta_meta_id: int
    plano: PlanoEnum
    status: AssinaturaStatusEnum
    started_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssinaturaEntity(Base):
    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, index=True)

    conta_meta_id = Column(
        Integer,
        ForeignKey("contas_meta.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    plano = Column(String, nullable=False, default="free")
    status = Column(String, nullable=False, default="active")

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    gateway_customer_id = Column(String, nullable=True)
    gateway_subscription_id = Column(String, nullable=True)

    conta_meta = relationship(
        "ContaMetaEntity",
        back_populates="assinatura"
    )