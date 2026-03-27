from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.db import Base


from sqlalchemy import UniqueConstraint

class MidiaInstagramEntity(Base):
    __tablename__ = "midias_instagram"

    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas_meta.id", ondelete="CASCADE"), nullable=False, index=True)

    media_id = Column(String, nullable=False, index=True)
    media_type = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    permalink = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    media_url = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("conta_id", "media_id", name="uq_conta_media"),
    )

    conta = relationship("ContaMetaEntity", back_populates="midias")
    automacao_midias = relationship("AutomacaoMidiaEntity", back_populates="midia")