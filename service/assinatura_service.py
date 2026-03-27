from sqlalchemy.orm import Session

from models.assinatura import AssinaturaEntity
from models.conta_meta import ContaMetaEntity


class AssinaturaService:

    @staticmethod
    def get_by_conta_meta_id(db: Session, conta_meta_id: int):
        return (
            db.query(AssinaturaEntity)
            .filter(AssinaturaEntity.conta_meta_id == conta_meta_id)
            .first()
        )

    @staticmethod
    def create_default_if_not_exists(db: Session, conta_meta_id: int):
        assinatura = AssinaturaService.get_by_conta_meta_id(db, conta_meta_id)

        if assinatura:
            return assinatura

        conta = db.query(ContaMetaEntity).filter(ContaMetaEntity.id == conta_meta_id).first()
        if not conta:
            raise ValueError("Conta Meta não encontrada")

        assinatura = AssinaturaEntity(
            conta_meta_id=conta_meta_id,
            plano="free",
            status="active"
        )

        db.add(assinatura)
        db.commit()
        db.refresh(assinatura)

        return assinatura

    @staticmethod
    def update_plan(db: Session, conta_meta_id: int, novo_plano: str):
        assinatura = AssinaturaService.get_by_conta_meta_id(db, conta_meta_id)

        if not assinatura:
            conta = db.query(ContaMetaEntity).filter(ContaMetaEntity.id == conta_meta_id).first()
            if not conta:
                raise ValueError("Conta Meta não encontrada")

            assinatura = AssinaturaEntity(
                conta_meta_id=conta_meta_id,
                plano=novo_plano,
                status="active"
            )
            db.add(assinatura)
        else:
            assinatura.plano = novo_plano
            assinatura.status = "active"

        db.commit()
        db.refresh(assinatura)

        return assinatura