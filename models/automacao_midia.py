from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.db import Base


class AutomacaoMidiaEntity(Base):
    __tablename__ = "automacao_midias"

    id = Column(Integer, primary_key=True, index=True)
    automacao_id = Column(Integer, ForeignKey("automacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    midia_id = Column(Integer, ForeignKey("midias_instagram.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("automacao_id", "midia_id", name="uq_automacao_midia"),
    )

    automacao = relationship("AutomacaoEntity", back_populates="automacao_midias")
    midia = relationship("MidiaInstagramEntity", back_populates="automacao_midias")